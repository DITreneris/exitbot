"""
Base LLM client with error handling and resilience features
"""
import time
import logging
import random
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

from exitbot.app.llm.cache import cached_llm_response
from exitbot.app.core.logging import get_logger

logger = get_logger("exitbot.app.llm.base")

class CircuitBreaker:
    """
    Circuit breaker pattern implementation to prevent repeated calls to failing services
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_time: int = 60):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Number of failures before circuit opens
            recovery_time: Time in seconds before attempting to close circuit
        """
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.failure_count = 0
        self.last_failure_time = 0
        self.is_open = False
    
    def record_failure(self):
        """Record a failure and open circuit if threshold is reached"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def record_success(self):
        """Record a success and reset failure count"""
        self.failure_count = 0
        self.is_open = False
    
    def can_execute(self) -> bool:
        """
        Check if request can be executed
        
        Returns:
            bool: True if circuit is closed or half-open (allowing test requests)
        """
        # If circuit is closed, allow execution
        if not self.is_open:
            return True
        
        # If circuit is open but recovery time has elapsed, allow a test request
        elapsed_time = time.time() - self.last_failure_time
        if elapsed_time >= self.recovery_time:
            logger.info("Circuit breaker allowing test request after recovery time")
            return True
        
        logger.warning(f"Circuit breaker is open, blocking request for {self.recovery_time - elapsed_time:.1f}s more")
        return False

class BaseLLMClient(ABC):
    """Base class for LLM clients with error handling and resilience"""
    
    def __init__(self, 
                 max_retries: int = 3, 
                 timeout: int = 30,
                 circuit_breaker: Optional[CircuitBreaker] = None):
        """
        Initialize base LLM client
        
        Args:
            max_retries: Maximum number of retries for failed requests
            timeout: Timeout in seconds for requests
            circuit_breaker: CircuitBreaker instance or None to use default
        """
        self.max_retries = max_retries
        self.timeout = timeout
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
    
    @abstractmethod
    def _send_request(self, prompt: str) -> Dict[str, Any]:
        """
        Send request to LLM API
        
        Args:
            prompt: The prompt to send
            
        Returns:
            Dict containing the response
        """
        pass
    
    def _format_prompt(self, prompt: str, context: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Format prompt with optional context messages
        
        Args:
            prompt: The main prompt
            context: Optional list of context messages
            
        Returns:
            Formatted prompt string
        """
        if not context:
            return prompt
        
        formatted_context = "\n".join([f"{msg.get('role', 'system')}: {msg.get('content', '')}" 
                                      for msg in context if msg.get('content')])
        return f"{formatted_context}\n\nuser: {prompt}"
    
    @cached_llm_response
    def generate_response(self, 
                          prompt: str, 
                          context: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Generate response with error handling and retries
        
        Args:
            prompt: The prompt to send
            context: Optional conversation context
            
        Returns:
            Dict containing the response and metadata
        """
        # Check if circuit breaker allows the request
        if not self.circuit_breaker.can_execute():
            return {
                "response": "I'm having trouble connecting to my knowledge base. Please try again in a minute.",
                "error": "Circuit breaker open",
                "duration": 0
            }
        
        # Format prompt with context if provided
        formatted_prompt = self._format_prompt(prompt, context)
        
        # Initialize variables
        start_time = time.time()
        retry_count = 0
        backoff_time = 1
        
        # Attempt request with exponential backoff
        while retry_count <= self.max_retries:
            try:
                response = self._send_request(formatted_prompt)
                duration = time.time() - start_time
                
                # Record success in circuit breaker ONLY if request succeeded
                self.circuit_breaker.record_success()
                
                # Add duration to response
                response["duration"] = duration
                return response
                
            except Exception as e:
                last_exception = e # Store the last exception
                retry_count += 1
                
                if retry_count > self.max_retries:
                    self.circuit_breaker.record_failure() 
                    logger.error(f"Failed to generate response after {self.max_retries} retries: {last_exception}")
                    
                    return {
                        "response": "I'm having trouble connecting to my knowledge base. Please try again later.",
                        "error": str(last_exception),
                        "duration": time.time() - start_time
                    }
                
                # Calculate backoff with jitter
                jitter = random.uniform(0, 0.5)
                sleep_time = backoff_time + jitter
                logger.warning(f"Request failed: {last_exception}. Retrying in {sleep_time:.1f}s (attempt {retry_count}/{self.max_retries})")
                
                # Wait before retrying
                time.sleep(sleep_time)
                
                # Exponential backoff
                backoff_time *= 2
        
        # Fallback return if loop finishes unexpectedly (e.g., max_retries < 0)
        # Also record failure here as a safeguard
        self.circuit_breaker.record_failure()
        final_error = last_exception if 'last_exception' in locals() else "Unknown error after retries"
        logger.error(f"generate_response loop finished unexpectedly. Error: {final_error}")
        return { 
            "response": "I encountered an unexpected issue. Please try again later.",
            "error": str(final_error),
            "duration": time.time() - start_time
        }

    @abstractmethod
    def analyze_sentiment(self, text: str) -> float:
        """
        Analyze sentiment of text
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment score between -1.0 (negative) and 1.0 (positive)
        """
        pass 
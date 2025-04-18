"""
Groq LLM client implementation
"""
import os
import requests
import logging
from typing import Dict, Any, Optional, List

from exitbot.app.llm.client_base import BaseLLMClient
from exitbot.app.core.config import settings
from exitbot.app.core.logging import get_logger

logger = get_logger("exitbot.app.llm.groq_client")

class GroqClient(BaseLLMClient):
    """
    Client for Groq LLM API with resilience and error handling
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 model: Optional[str] = None,
                 max_retries: int = 3,
                 timeout: int = 30):
        """
        Initialize Groq client
        
        Args:
            api_key: Groq API key (default: from settings)
            model: Model name (default: from settings)
            max_retries: Maximum number of retries for failed requests
            timeout: Timeout in seconds for requests
        """
        super().__init__(max_retries=max_retries, timeout=timeout)
        
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        
        if not self.api_key:
            logger.warning("No Groq API key provided. Functionality will be limited.")
    
    def _send_request(self, prompt: str) -> Dict[str, Any]:
        """
        Send request to Groq API
        
        Args:
            prompt: Prompt to send to API
            
        Returns:
            Dict containing the response
        """
        if not self.api_key:
            raise ValueError("Groq API key is required")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Prepare messages for chat completion
        messages = [{"role": "user", "content": prompt}]
        
        # Prepare data payload
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024
        }
        
        try:
            # Send request to Groq API
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            
            # Check for errors
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            
            if "choices" not in response_data or not response_data["choices"]:
                raise ValueError("Invalid response from Groq API")
            
            # Extract content from response
            content = response_data["choices"][0]["message"]["content"]
            
            return {"response": content}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending request to Groq API: {str(e)}")
            raise
    
    def analyze_sentiment(self, text: str) -> float:
        """
        Analyze sentiment of text using Groq API
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment score between -1.0 (negative) and 1.0 (positive)
        """
        prompt = f"""
        Analyze the sentiment of the following text and return ONLY a float value between -1.0 (negative) and 1.0 (positive):
        
        Text: {text}
        
        Return only the float value and nothing else.
        """
        
        try:
            result = self.generate_response(prompt=prompt)
            
            # Extract response and try to convert to float
            response_text = result.get("response", "0.0")
            
            # Clean and convert to float
            response_text = response_text.strip()
            
            # Attempt to parse a float from the response
            try:
                sentiment_score = float(response_text)
            except ValueError:
                # If conversion fails, try to extract a number from the text
                import re
                float_matches = re.findall(r'-?\d+\.\d+', response_text)
                if float_matches:
                    sentiment_score = float(float_matches[0])
                else:
                    logger.warning(f"Could not extract sentiment value from response: {response_text}")
                    sentiment_score = 0.0  # Default to neutral
            
            # Ensure the value is within the specified range
            return max(min(sentiment_score, 1.0), -1.0)
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return 0.0  # Neutral sentiment as fallback

# Create a singleton instance
groq_client = GroqClient() 
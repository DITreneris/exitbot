"""
Ollama LLM client implementation
"""
import json
import logging
import requests
from typing import Dict, Any, Optional, List

try:
    # Try package-level imports first (for app running as a module)
    from exitbot.app.llm.client_base import BaseLLMClient
    from exitbot.app.core.config import settings
except ImportError:
    # Fall back to relative imports (for direct script execution)
    from app.llm.client_base import BaseLLMClient
    from app.core.config import settings

logger = logging.getLogger(__name__)

class OllamaClient(BaseLLMClient):
    """
    Client for Ollama local LLM API with resilience and error handling
    """
    
    def __init__(self, 
                 host: Optional[str] = None,
                 model: Optional[str] = None,
                 max_retries: int = 3,
                 timeout: int = 60):
        """
        Initialize Ollama client
        
        Args:
            host: Ollama host URL (default: from settings)
            model: Model name (default: from settings)
            max_retries: Maximum number of retries for failed requests
            timeout: Timeout in seconds for requests
        """
        super().__init__(max_retries=max_retries, timeout=timeout)
        
        self.host = host or settings.OLLAMA_HOST or "http://localhost:11434"
        self.model = model or settings.OLLAMA_MODEL or "llama2"
        
        # Ensure host has proper format
        if not self.host.startswith(("http://", "https://")):
            self.host = f"http://{self.host}"
        
        # Remove trailing slash if present
        self.host = self.host.rstrip("/")
        
        logger.info(f"Ollama client initialized with host: {self.host}, model: {self.model}")
    
    def _send_request(self, prompt: str) -> Dict[str, Any]:
        """
        Send request to Ollama API
        
        Args:
            prompt: Prompt to send to API
            
        Returns:
            Dict containing the response
        """
        api_url = f"{self.host}/api/generate"
        
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        
        # Send request to Ollama API
        response = requests.post(
            api_url,
            json=data,
            timeout=self.timeout
        )
        
        # Check for errors
        response.raise_for_status()
        
        # Parse response
        response_data = response.json()
        
        if "response" not in response_data:
            raise ValueError("Invalid response from Ollama API")
        
        return {
            "response": response_data["response"]
        }
    
    def analyze_sentiment(self, text: str) -> float:
        """
        Analyze sentiment of text using Ollama API
        
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
            result = self.generate_response(prompt)
            
            # Extract response and try to convert to float
            response_text = result.get("response", "0.0")
            
            # Clean and convert to float
            response_text = response_text.strip()
            
            # Handle potential text around the float value
            # Look for floating point patterns
            import re
            float_matches = re.findall(r'-?\d+\.\d+', response_text)
            if float_matches:
                response_text = float_matches[0]
            
            sentiment_score = float(response_text)
            
            # Ensure the value is within the specified range
            return max(min(sentiment_score, 1.0), -1.0)
            
        except (ValueError, KeyError) as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return 0.0  # Neutral sentiment as fallback

# Create a singleton instance
ollama_client = OllamaClient() 
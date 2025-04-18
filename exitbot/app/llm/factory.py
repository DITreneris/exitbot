from typing import Dict, Any, Union, Optional

from exitbot.app.core.config import settings
from exitbot.app.core.logging import get_logger
from exitbot.app.llm.mock_client import MockLLMClient
from exitbot.app.llm.groq_client import GroqClient

logger = get_logger("llm.factory")

class LLMClientFactory:
    """Factory for creating LLM clients"""
    
    @staticmethod
    def create_client():
        """
        Create and return an LLM client based on configuration
        
        Returns:
            LLM client instance (GroqClient or MockLLMClient for testing)
        """
        provider = settings.LLM_PROVIDER.lower()
        
        # If TESTING is True, always return MockLLMClient
        # if settings.TESTING:
        #     logger.info("Using Mock LLM client because TESTING=True")
        #     return MockLLMClient()

        if provider == "groq" and settings.GROQ_API_KEY:
            logger.info(f"Using Groq LLM provider with model {settings.GROQ_MODEL}")
            return GroqClient(
                api_key=settings.GROQ_API_KEY,
                model=settings.GROQ_MODEL
            )
        else:
            logger.info("Using Mock LLM client for testing")
            return MockLLMClient()

# Create a singleton instance of the appropriate client
llm_client = LLMClientFactory.create_client() 
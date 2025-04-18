import os
import pytest
from unittest.mock import patch, MagicMock
import importlib

from exitbot.app.llm.groq_client import GroqClient
# from exitbot.app.llm.ollama_client import OllamaClient # Commented out
from exitbot.app.llm.factory import LLMClientFactory
from exitbot.app.core.config import settings

# Mock responses
MOCK_OLLAMA_RESPONSE = {"response": "This is a test response from Ollama"}
MOCK_GROQ_RESPONSE = {"choices": [{"message": {"content": "This is a test response from Groq"}}]}

class TestLLMClients:
    
    # @patch('exitbot.app.llm.ollama_client.ollama.generate')
    # def test_ollama_client(self, mock_generate):
    #     """Test that the Ollama client works correctly"""
    #     # Setup mock
    #     mock_generate.return_value = MOCK_OLLAMA_RESPONSE
        
    #     # Create client
    #     client = OllamaClient(model="test-model")
        
    #     # Test response generation
    #     response = client.generate_response("This is a test prompt")
        
    #     # Verify correct response
    #     assert response == MOCK_OLLAMA_RESPONSE
    #     assert mock_generate.called
    #     assert mock_generate.call_args[1]["model"] == "test-model"
    #     assert mock_generate.call_args[1]["prompt"] == "This is a test prompt"
    
    @patch('exitbot.app.llm.groq_client.requests.post')
    def test_groq_client(self, mock_post):
        """Test that the Groq client works correctly"""
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_GROQ_RESPONSE
        mock_post.return_value = mock_response
        
        # Create client
        client = GroqClient(api_key="test-key", model="test-model")
        
        # Test response generation
        response = client.generate_response("This is a test prompt")
        
        # Verify correct response
        assert response["response"] == "This is a test response from Groq"
        assert mock_post.called
        assert "Bearer test-key" in mock_post.call_args[1]["headers"]["Authorization"]
        
        # Check that the data includes the model and prompt
        data = mock_post.call_args[1]["json"]
        assert data["model"] == "test-model"
        assert data["messages"][0]["content"] == "This is a test prompt"
    
    @patch('exitbot.app.llm.factory.settings') # Patch settings *in the factory module*
    @patch('exitbot.app.llm.factory.GroqClient') # Patch GroqClient class used by factory
    def test_llm_factory_groq(self, mock_groq_class, mock_factory_settings):
        """Test that the factory creates Groq client when configured"""
        # Configure the mocked settings object (imported within the factory module)
        mock_factory_settings.LLM_PROVIDER = "groq"
        mock_factory_settings.GROQ_API_KEY = "test-key"
        mock_factory_settings.GROQ_MODEL = "test-model"

        # No reload needed if we patch the correct settings object

        # Mock the instance returned when GroqClient is called
        mock_groq_instance = MagicMock()
        mock_groq_class.return_value = mock_groq_instance

        # Call the factory's static method
        client = LLMClientFactory.create_client()

        # Verify GroqClient was called (instantiated) with correct args
        mock_groq_class.assert_called_once_with(
            api_key="test-key",
            model="test-model"
        )
        # Verify the factory returned the instance created by the mock class
        assert client == mock_groq_instance

        # Additional test cases can be added for other providers or fallback logic
        # mock_groq.assert_called_with(
        #     api_key="test-key",
        #     model="test-model"
        # )
        # mock_ollama.assert_not_called() # Removed assertion 
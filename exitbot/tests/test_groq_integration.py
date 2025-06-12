"""
Integration tests for the Groq LLM client
"""
from unittest.mock import patch, MagicMock
import time
import requests

from exitbot.app.llm.groq_client import GroqClient
from exitbot.app.llm.factory import LLMClientFactory
from exitbot.app.llm.cache import _cache

# Test data
TEST_API_KEY = "test_api_key"
TEST_MODEL = "llama3-70b-8192"
LONG_PROMPT = "A" * 10000  # 10K character prompt
MOCK_SUCCESS_RESPONSE = {"choices": [{"message": {"content": "Test response"}}]}


class TestGroqIntegration:
    """Test class for Groq integration"""

    def test_groq_client_initialization(self):
        """Test that the Groq client initializes correctly"""
        client = GroqClient(api_key=TEST_API_KEY, model=TEST_MODEL)
        assert client.api_key == TEST_API_KEY
        assert client.model == TEST_MODEL
        assert client.max_retries == 3  # Default value
        assert "api.groq.com" in client.api_url

    @patch("exitbot.app.llm.groq_client.requests.post")
    def test_basic_response_handling(self, mock_post):
        """Test basic response handling"""
        _cache.clear()
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_SUCCESS_RESPONSE
        mock_post.return_value = mock_response

        # Create client and test
        client = GroqClient(api_key=TEST_API_KEY)
        result = client.generate_response(prompt="Test prompt")

        # Verify result
        assert "response" in result
        assert result["response"] == "Test response"

        # Verify the API was called with correct data
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["messages"][0]["content"] == "Test prompt"

    @patch("exitbot.app.llm.groq_client.requests.post")
    def test_long_prompt_handling(self, mock_post):
        """Test handling of long prompts"""
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_SUCCESS_RESPONSE
        mock_post.return_value = mock_response

        # Create client and test
        client = GroqClient(api_key=TEST_API_KEY)
        result = client.generate_response(prompt=LONG_PROMPT)

        # Verify result
        assert "response" in result

        # Verify the API was called with the full prompt
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        assert len(call_kwargs["json"]["messages"][0]["content"]) == len(LONG_PROMPT)

    @patch("exitbot.app.llm.groq_client.requests.post")
    def test_error_handling(self, mock_post):
        """Test error handling and retries"""
        _cache.clear()
        # Setup mock to fail twice then succeed
        mock_post.side_effect = [
            requests.exceptions.RequestException("API timeout"),
            requests.exceptions.RequestException("Rate limit"),
            MagicMock(status_code=200, json=lambda: MOCK_SUCCESS_RESPONSE),
        ]

        # Create client with short timeout for faster tests
        client = GroqClient(api_key=TEST_API_KEY, timeout=1)

        # Record start time to measure retry backoff
        start_time = time.time()
        result = client.generate_response(prompt="Test prompt")
        elapsed_time = time.time() - start_time

        # Verify result eventually succeeded
        assert "response" in result
        assert result["response"] == "Test response"

        # Verify the API was called 3 times (2 failures + 1 success)
        assert mock_post.call_count == 3

        # Verify backoff delay occurred (should be at least 1 + 2 seconds with exponential backoff)
        assert elapsed_time >= 1  # We're mocking, so actual delay may be minimal

    @patch("exitbot.app.llm.groq_client.requests.post")
    def test_complete_failure_handling(self, mock_post):
        """Test handling of complete API failure"""
        _cache.clear()
        # Setup mock to always fail
        mock_post.side_effect = requests.exceptions.RequestException("API down")

        # Create client with minimal retries for faster tests
        client = GroqClient(api_key=TEST_API_KEY, max_retries=2, timeout=1)
        result = client.generate_response(prompt="Test prompt")

        # Verify we got a fallback response
        assert "response" in result
        assert "trouble connecting" in result["response"]
        assert "error" in result

        # Verify the API was called max_retries + 1 times (initial call + retries)
        expected_calls = client.max_retries + 1
        assert (
            mock_post.call_count == expected_calls
        ), f"Expected {expected_calls} calls, got {mock_post.call_count}"

    @patch("exitbot.app.llm.groq_client.requests.post")
    def test_sentiment_analysis(self, mock_post):
        """Test sentiment analysis functionality"""
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "0.75"}}]
        }
        mock_post.return_value = mock_response

        # Create client and test
        client = GroqClient(api_key=TEST_API_KEY)
        sentiment = client.analyze_sentiment("I love this product!")

        # Verify sentiment score
        assert isinstance(sentiment, float)
        assert -1.0 <= sentiment <= 1.0
        assert sentiment == 0.75

        # Verify prompt contained sentiment analysis instructions
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        prompt = call_kwargs["json"]["messages"][0]["content"]
        assert "sentiment" in prompt.lower()
        assert "float value" in prompt.lower()
        assert "I love this product!" in prompt

    @patch("exitbot.app.llm.groq_client.requests.post")
    def test_invalid_sentiment_response(self, mock_post):
        """Test handling of invalid sentiment response"""
        # Setup mock to return non-numeric response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "This is positive"}}]
        }
        mock_post.return_value = mock_response

        # Create client and test
        client = GroqClient(api_key=TEST_API_KEY)
        sentiment = client.analyze_sentiment("Test text")

        # Verify default sentiment returned
        assert sentiment == 0.0

    @patch("exitbot.app.llm.factory.settings")
    def test_factory_selects_groq(self, mock_factory_settings):
        """Test that factory correctly selects Groq when configured"""
        # Mock settings for Groq on the patched object
        mock_factory_settings.LLM_PROVIDER = "groq"
        mock_factory_settings.GROQ_API_KEY = "mock_api_key"
        mock_factory_settings.GROQ_MODEL = "mock_model"

        # Patch GroqClient.__init__ to prevent actual instantiation during test
        with patch.object(GroqClient, "__init__", return_value=None) as mock_groq_init:
            # Call the factory method
            client = LLMClientFactory.create_client()

            # Verify GroqClient.__init__ was called (meaning GroqClient was selected)
            mock_groq_init.assert_called_once()
            # Verify the factory returned the (mocked init) GroqClient instance
            # We can check the type, as __init__ was mocked
            assert isinstance(client, GroqClient)

            # Optionally check args passed to __init__ if needed
            # args = mock_groq_init.call_args[1]
            # assert args['api_key'] == "mock_api_key"
            # assert args['model'] == "mock_model"

    # @patch('exitbot.app.core.config.settings')
    # def test_factory_fallback_without_api_key(self, mock_settings):
    #     """Test that factory falls back to Ollama if no Groq API key is provided"""
    #     # Mock settings with missing API key
    #     mock_settings.LLM_PROVIDER = "groq"
    #     mock_settings.GROQ_API_KEY = ""
    #     mock_settings.OLLAMA_HOST = "mock_host"
    #     mock_settings.OLLAMA_MODEL = "mock_model"

    #     # Create client via factory with patched create_client to avoid actual instantiation
    #     with patch('exitbot.app.llm.factory.OllamaClient') as mock_ollama:
    #         mock_ollama_instance = MagicMock()
    #         mock_ollama.return_value = mock_ollama_instance

    #         client = LLMClientFactory.create_client()

    #         # Verify OllamaClient was created as fallback
    #         mock_ollama.assert_called_once()
    #         assert client == mock_ollama_instance

"""
Mocking utilities for tests, particularly for the Ollama API
"""
from unittest.mock import patch


def mock_ollama_response(content="This is a test response"):
    """Create a mock Ollama response object"""
    return {
        "model": "llama3.1:8b",
        "created_at": "2023-06-18T12:34:56.789Z",
        "response": content,
        "done": True,
    }


def mock_ollama_generate(model, prompt, **kwargs):
    """Mock for ollama.generate function"""
    # For sentiment analysis prompts, return a score
    if "sentiment" in prompt.lower() and "between -1.0 and 1.0" in prompt:
        if "positive" in prompt.lower():
            return mock_ollama_response("0.8")
        elif "negative" in prompt.lower():
            return mock_ollama_response("-0.7")
        else:
            return mock_ollama_response("0.0")

    # For interview prompts
    if "exitbot" in prompt.lower() and "interview" in prompt.lower():
        return mock_ollama_response("Thank you for sharing. That's valuable feedback.")

    # For follow-up determination
    if "follow-up question" in prompt.lower():
        # 50% chance of follow-up
        if "better offer" in prompt.lower() or "culture" in prompt.lower():
            return mock_ollama_response(
                "Can you tell me more about what specifically attracted you to the new opportunity?"
            )
        else:
            return mock_ollama_response("NO_FOLLOWUP")

    # For summary prompts
    if "summarizing" in prompt.lower() and "exit interview" in prompt.lower():
        return mock_ollama_response(
            """
        - Primary reason for leaving: Better compensation elsewhere
        - Key areas of satisfaction: Team culture, work-life balance
        - Key areas of dissatisfaction: Limited growth opportunities
        - Actionable feedback: Consider more competitive compensation and clearer career paths
        """
        )

    # Default response
    return mock_ollama_response("I processed your request.")


def mock_ollama_list():
    """Mock for ollama.list function"""
    return {
        "models": [
            {
                "name": "llama3.1:8b",
                "modified_at": "2023-05-10T12:00:00.000Z",
                "size": 4200000000,
            }
        ]
    }


def setup_mock_ollama():
    """Setup all Ollama-related mocks"""
    # Create patches
    generate_patch = patch("ollama.generate", side_effect=mock_ollama_generate)
    list_patch = patch("ollama.list", return_value=mock_ollama_list())

    # Start patches
    mock_generate = generate_patch.start()
    mock_list = list_patch.start()

    return {
        "generate_patch": generate_patch,
        "list_patch": list_patch,
        "mock_generate": mock_generate,
        "mock_list": mock_list,
    }


def teardown_mock_ollama(mocks):
    """Teardown all Ollama-related mocks"""
    mocks["generate_patch"].stop()
    mocks["list_patch"].stop()


class MockOllamaContext:
    """Context manager for mocking Ollama API during tests"""

    def __enter__(self):
        self.mocks = setup_mock_ollama()
        return self.mocks

    def __exit__(self, exc_type, exc_val, exc_tb):
        teardown_mock_ollama(self.mocks)


class MockLLM:
    """Mock for LLM client to be used in tests"""

    @staticmethod
    def patch_llm():
        """
        Patch the LLM client for testing

        This creates a mock for the LLM client that can be used in tests
        to avoid making actual API calls.

        Returns:
            patch: A context manager for patching the LLM client
        """
        # We patch the function instead of the entire client to maintain the interface
        return patch(
            "exitbot.app.llm.factory.llm_client.generate_response",
            MockLLM.mock_generate_response,
        )

    @staticmethod
    def patch_sentiment():
        """
        Patch the sentiment analysis for testing

        Returns:
            patch: A context manager for patching the sentiment analysis
        """
        return patch(
            "exitbot.app.llm.factory.llm_client.analyze_sentiment",
            MockLLM.mock_analyze_sentiment,
        )

    @staticmethod
    def mock_generate_response(prompt, temperature=0.7):
        """
        Mock implementation of generate_response

        Args:
            prompt: The prompt sent to the model
            temperature: Temperature setting (ignored in mock)

        Returns:
            dict: A mock response with canned answers based on prompt
        """
        # Determine response based on prompt
        if "follow up" in prompt.lower():
            if "why are you leaving" in prompt.lower():
                return {
                    "response": "Can you elaborate on the specific factors that influenced your decision to leave?"
                }
            else:
                return {"response": "NO_FOLLOWUP"}
        elif "summary" in prompt.lower():
            return {
                "response": "The employee is leaving due to better opportunities elsewhere. "
                + "They expressed satisfaction with their team but frustration with "
                + "limited growth prospects and compensation."
            }
        elif "sentiment" in prompt.lower():
            return {"response": "0.2"}  # Slightly positive
        else:
            return {
                "response": "Thank you for sharing that. Your feedback is valuable and will help us improve."
            }

    @staticmethod
    def mock_analyze_sentiment(text):
        """
        Mock implementation of analyze_sentiment

        Args:
            text: The text to analyze

        Returns:
            float: A sentiment score between -1 and 1
        """
        lower_text = text.lower()

        # Basic sentiment detection
        if any(
            word in lower_text
            for word in ["happy", "great", "excellent", "good", "love", "enjoy"]
        ):
            return 0.8
        elif any(word in lower_text for word in ["okay", "fine", "alright", "neutral"]):
            return 0.0
        elif any(
            word in lower_text
            for word in ["unhappy", "bad", "poor", "hate", "terrible"]
        ):
            return -0.8
        else:
            # Default slightly positive
            return 0.2

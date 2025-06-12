"""
Simple test script to verify Groq integration is working.
"""
import os
import time
import pathlib
from dotenv import load_dotenv
from exitbot.app.core.config import settings

# Try to load from .env files in various locations
load_dotenv()  # Default location
load_dotenv(dotenv_path=pathlib.Path(__file__).parent / ".env")  # In exitbot folder
load_dotenv(dotenv_path=pathlib.Path(__file__).parent.parent / ".env")  # In root folder

# Get API key from environment or use the one from .env
GROQ_API_KEY = "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"
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

# Set provider to Groq for testing
os.environ["LLM_PROVIDER"] = "groq"

# Print current environment settings for debug
print(f"Using LLM provider: {os.environ.get('LLM_PROVIDER')}")
print(f"Groq API key exists: {'Yes' if GROQ_API_KEY else 'No'}")
print(f"Groq model: {settings.GROQ_MODEL}")


def test_groq_simple():
    """Simple test of Groq API connection"""

    # Run a simple test with explicit API key
    from exitbot.app.llm.groq_client import GroqClient

    client = GroqClient(
        api_key=GROQ_API_KEY, model=settings.GROQ_MODEL or "llama3-70b-8192"
    )

    # Test the client
    start_time = time.time()
    response = client.generate_response("What is the capital of France?")
    elapsed = time.time() - start_time

    print(f"Response time: {elapsed:.2f} seconds")
    print(f"Response: {response['response']}")

    assert "Paris" in response["response"]
    assert elapsed < 10.0  # Might be slower with the larger model


if __name__ == "__main__":
    test_groq_simple()

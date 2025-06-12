"""
Direct test script to verify Groq API is working without dependencies on other modules.
"""
# Remove unused time
# import time
import requests
import pytest

# Groq API key
API_KEY = "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"
MODEL = "llama3-8b-8192"


def test_groq_api():
    """Test the Groq API directly"""
    print(f"Testing Groq API with model: {MODEL}")

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Say hello in one word"}],
        "temperature": 0.7,
    }

    api_url = "https://api.groq.com/openai/v1/chat/completions"

    try:
        print("Sending request to Groq API...")
        response = requests.post(api_url, headers=headers, json=data, timeout=30)

        response.raise_for_status()
        result = response.json()

        print("\nAPI Response:")
        print(f"Status code: {response.status_code}")

        response_text = result["choices"][0]["message"]["content"]
        print(f"Response: {response_text}")

        assert response.status_code == 200
        assert response_text is not None and response_text != ""
    except Exception as e:
        print(f"An error occurred: {e}")
        if hasattr(e, "response") and e.response:
            try:
                print(f"Response content: {e.response.text}")
            except Exception as inner_e:
                print(f"Could not print response details: {inner_e}")
        pytest.fail(f"Groq API test failed with error: {str(e)}")


if __name__ == "__main__":
    test_groq_api()

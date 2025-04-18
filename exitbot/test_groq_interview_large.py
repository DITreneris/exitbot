"""
Test script to verify Groq API works with an exit interview scenario using the larger model.
"""
import time
import requests
import json
import pytest
import sys

# Groq API key
API_KEY = "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"
MODEL = "llama3-70b-8192"  # Using the larger model

def test_exit_interview_scenario():
    """Test the Groq API with an exit interview scenario"""
    print(f"Testing Groq API for exit interview with model: {MODEL}")
    
    # Create a prompt that simulates our interview system
    interview_prompt = """
    You are ExitBot, an AI assistant designed to conduct exit interviews with departing employees.
    Your goal is to gather feedback in a conversational, empathetic manner.
    
    Current employee: John Smith
    Current question: "What are your main reasons for leaving the company?"
    Employee response: "I've received a better offer from another company with higher pay and more opportunities for growth."
    
    Please respond to the employee's answer in a professional and empathetic way. 
    Ask a relevant follow-up question to gather more specific details about their reasons for leaving.
    """
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": interview_prompt}],
        "temperature": 0.7,
    }
    
    api_url = "https://api.groq.com/openai/v1/chat/completions"
    
    try:
        print("Sending interview prompt to Groq API...")
        start_time = time.time()
        
        response = requests.post(
            api_url,
            headers=headers,
            json=data,
            timeout=30
        )
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        response.raise_for_status()
        result = response.json()
        
        print("\nAPI Response:")
        print(f"Status code: {response.status_code}")
        print(f"Response time: {elapsed_time:.2f} seconds")
        
        response_text = result["choices"][0]["message"]["content"]
        print(f"\nBot response: \n{response_text}")
        
        assert response.status_code == 200
        assert response_text is not None and response_text != ""
    except Exception as e:
        print(f"Error: {str(e)}")
        if hasattr(e, 'response') and e.response:
            try:
                print(f"Response status code: {e.response.status_code}")
                print(f"Response content: {e.response.text}")
            except:
                print("Could not print response details.")
        
        if 'pytest' in sys.modules:
             pytest.fail(f"Groq interview (large model) test failed with error: {str(e)}")
        else:
             print("\nTest finished with error (running standalone).")

if __name__ == "__main__":
    test_exit_interview_scenario() 
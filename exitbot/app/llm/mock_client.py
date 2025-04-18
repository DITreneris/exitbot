"""
Mock LLM client for testing
"""
from typing import Dict, Any, Optional, List
import time
import random

class MockLLMClient:
    """
    Simple mock client for testing that returns canned responses
    """
    
    def __init__(self):
        """Initialize mock client"""
        self.responses = {
            "why leaving": "Thank you for sharing that information. It's understandable that you're looking for new growth opportunities. Could you share more about what specific growth aspects you feel were missing in your current role?",
            "satisfied role": "I appreciate your candid feedback about your role satisfaction. It sounds like you had a mix of positive and challenging experiences. What aspects of your role did you find most fulfilling?",
            "feedback manager": "Thank you for your feedback regarding your manager and team. It's valuable to hear both the strengths and areas for improvement. Is there anything specific you think could be done to improve team communication?",
            "improve organization": "Thank you for these insightful suggestions about improving the organization. Your perspective as someone who has worked here is incredibly valuable. Which of these improvements do you think would have the biggest positive impact?"
        }
        
    def generate_response(self, prompt: str, context: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Generate a mock response
        
        Args:
            prompt: The prompt text
            context: Optional conversation context (ignored)
            
        Returns:
            Dict with response text
        """
        # Add a small delay to simulate processing
        time.sleep(0.5)
        
        # Try to match the prompt with one of our canned responses
        response_text = "Thank you for sharing your thoughts. Your feedback is valuable to us as we work to improve our workplace environment."
        
        # Look for keywords in the prompt
        for keyword, resp in self.responses.items():
            if keyword.lower() in prompt.lower():
                response_text = resp
                break
        
        return {
            "response": response_text,
            "duration": 0.5
        }
    
    def analyze_sentiment(self, text: str) -> float:
        """
        Analyze sentiment of text (mocked)
        
        Args:
            text: Text to analyze
            
        Returns:
            Mock sentiment score between -1.0 and 1.0
        """
        # For testing, generate a random sentiment with bias towards positive
        # unless there are negative words
        sentiment = random.uniform(0.0, 0.7)  # Default slightly positive
        
        negative_words = ["bad", "poor", "terrible", "difficult", "issue", "problem",
                         "frustrating", "disappointing", "unhappy", "quit", "leave"]
        positive_words = ["good", "great", "excellent", "awesome", "happy", "satisfied",
                         "enjoyed", "positive", "helpful", "learn", "growth"]
        
        # Check for negative and positive words
        for word in negative_words:
            if word in text.lower():
                sentiment -= random.uniform(0.2, 0.5)
                
        for word in positive_words:
            if word in text.lower():
                sentiment += random.uniform(0.1, 0.4)
        
        # Ensure it's within bounds
        return max(min(sentiment, 1.0), -1.0) 
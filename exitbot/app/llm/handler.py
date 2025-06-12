"""
LLM Handler for ExitBot - Manages interactions with the LLM API
"""

import os
import logging
import requests
import json
import datetime
from typing import Dict, Any, List, Optional
from .prompts import (
    SYSTEM_PROMPT_INTERVIEW,
    SYSTEM_PROMPT_ANALYSIS,
    SYSTEM_PROMPT_FOLLOW_UP,
)

logger = logging.getLogger(__name__)


class LLMHandler:
    """
    Handles all interactions with the Language Model API
    """

    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None):
        """
        Initialize the LLM handler with API credentials

        Args:
            api_key: API key for the LLM service
            api_url: URL endpoint for the LLM service
        """
        self.api_key = api_key or os.environ.get("LLM_API_KEY", "")
        self.api_url = api_url or os.environ.get(
            "LLM_API_URL", "https://api.openai.com/v1/chat/completions"
        )

        if not self.api_key:
            logger.warning(
                "No LLM API key provided. LLM functionality will be limited."
            )

    def _make_api_request(
        self, messages: List[Dict[str, str]], temperature: float = 0.7
    ) -> Optional[str]:
        """
        Make a request to the LLM API

        Args:
            messages: List of message dictionaries (role, content)
            temperature: Creativity parameter (0.0-1.0)

        Returns:
            Response text from LLM or None if request failed
        """
        if not self.api_key:
            logger.error("Cannot make API request: No API key configured")
            return None

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": "gpt-4",  # Can be configurable in the future
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 1000,
        }

        try:
            response = requests.post(
                self.api_url, headers=headers, data=json.dumps(payload), timeout=30
            )
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return None
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Error parsing API response: {str(e)}")
            return None

    def generate_follow_up_question(
        self, conversation_history: List[Dict[str, str]]
    ) -> Optional[str]:
        """
        Generate a follow-up question based on the conversation history

        Args:
            conversation_history: List of previous messages in the conversation

        Returns:
            Follow-up question text or None if generation failed
        """
        messages = [{"role": "system", "content": SYSTEM_PROMPT_FOLLOW_UP}]

        # Add conversation history
        messages.extend(conversation_history)

        return self._make_api_request(messages, temperature=0.7)

    def conduct_interview(
        self, user_input: str, conversation_history: List[Dict[str, str]]
    ) -> Optional[str]:
        """
        Generate the next interview response based on user input and conversation history

        Args:
            user_input: The latest input from the user
            conversation_history: Previous messages in the conversation

        Returns:
            Response text from the interviewer bot
        """
        messages = [{"role": "system", "content": SYSTEM_PROMPT_INTERVIEW}]

        # Add conversation history
        messages.extend(conversation_history)

        # Add the latest user input
        messages.append({"role": "user", "content": user_input})

        return self._make_api_request(messages, temperature=0.8)

    def analyze_interview(
        self, conversation_history: List[Dict[str, str]]
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze the completed interview and generate insights

        Args:
            conversation_history: Full conversation history from the interview

        Returns:
            Dictionary containing analysis results or None if analysis failed
        """
        messages = [{"role": "system", "content": SYSTEM_PROMPT_ANALYSIS}]

        # Add conversation history
        messages.extend(conversation_history)

        # Request analysis
        analysis_text = self._make_api_request(messages, temperature=0.3)

        if not analysis_text:
            return None

        # For now, return the raw analysis text
        # In the future, we could parse this into a structured format
        return {
            "raw_analysis": analysis_text,
            "interview_length": len(conversation_history),
            "timestamp": datetime.datetime.now().isoformat(),
        }

    def get_fallback_response(self) -> str:
        """
        Provide a fallback response when API calls fail

        Returns:
            A generic response to continue the conversation
        """
        fallback_responses = [
            "I appreciate your thoughts on this. Could you tell me more about your experience?",
            "Thank you for sharing. What other aspects of your work would you like to discuss?",
            "That's helpful feedback. Is there anything else you'd like to add about your time here?",
            "I understand. Could you elaborate on how this affected your work experience?",
        ]

        import random

        return random.choice(fallback_responses)

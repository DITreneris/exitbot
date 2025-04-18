import re
import pytest
from playwright.sync_api import Page, expect

# Basic URL for the Streamlit app - adjust if needed
APP_URL = "http://localhost:8501" 

def test_employee_app_login_and_first_message(page: Page):
    """
    Tests the employee login flow and sending the first message.
    Assumes the backend API is running and responsive.
    """
    page.goto(APP_URL)

    # --- Login Form ---
    # Use placeholders as selectors, assuming no specific test IDs
    email_input = page.locator('input[placeholder="your.email@company.com"]')
    name_input = page.locator('input[placeholder="John Doe"]')
    # Updated selector: Locate button directly by text
    start_button = page.locator('button:has-text("Start Interview")')

    # Wait for elements to be visible to avoid race conditions
    expect(email_input).to_be_visible(timeout=15000) # Increased timeout for initial load
    expect(name_input).to_be_visible()
    expect(start_button).to_be_visible()

    # Fill and submit the form
    email_input.fill("test.employee@example.com")
    name_input.fill("Test Employee")
    start_button.click()
    page.pause() # Re-enable pause after click

    # --- Interview Interface ---
    # Wait for the first bot message to appear
    # --- Updated: Simplify selector and increase timeout ---
    # Bot messages have the class 'bot-message' 
    # first_bot_message = page.locator('div.bot-message:has-text("ExitBot:")').first # Original selector
    first_bot_message = page.locator('div.bot-message').first # Simplified selector
    # Also wait for the text area for the response
    response_area = page.locator('textarea[placeholder^="Type your response"]') # Placeholder starts with "Type your response"
    # Updated selector: Locate button directly by text
    send_button = page.locator('button:has-text("Send")')
    
    # Wait for the interface elements to appear after login/session creation
    # This implicitly waits for the API calls in the login handler to complete

    # --- PAUSE FOR DEBUGGING (After rerun) ---
    # page.pause() # Removing pause
    
    # Increased timeout significantly
    expect(first_bot_message).to_be_visible(timeout=40000) 
    expect(response_area).to_be_visible()
    expect(send_button).to_be_visible()

    # Verify the first bot message has some content
    expect(first_bot_message).not_to_be_empty() 
    
    # --- Send First Message ---
    user_response_text = "This is my first response."
    response_area.fill(user_response_text)
    send_button.click()

    # --- Verify Message Sent ---
    # Wait for the user's message to appear in the chat history
    # User messages have class 'user-message' and contain 'You:'
    user_message_in_chat = page.locator(f'div.user-message:has-text("{user_response_text}")')
    
    # Wait for the user message AND potentially the *next* bot message/question
    # This waits for the send_message API call to complete
    expect(user_message_in_chat).to_be_visible(timeout=20000) # Allow time for send + LLM response

    # Optional: Wait for the *next* bot message as well
    # This assumes the bot always replies immediately.
    # next_bot_message = page.locator('div.bot-message:has-text("ExitBot:")').nth(1) # Second bot message
    # expect(next_bot_message).to_be_visible(timeout=20000)

    print("Employee app E2E test: Login and first message successful.") 
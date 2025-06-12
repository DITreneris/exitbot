"""
Enhanced Chat Interface Component for Employee App

This module provides a modern, animated chat interface for the employee exit interview experience.
"""

import streamlit as st
import time
from typing import List, Dict, Any, Optional, Callable

def render_chat_interface(
    messages: List[Dict[str, Any]],
    on_message_submit: Callable[[str], None],
    current_question_number: Optional[int] = None,
    total_questions: Optional[int] = None,
    is_complete: bool = False,
    is_thinking: bool = False
):
    """
    Renders an enhanced chat interface with animations and typing indicators
    
    Parameters:
    - messages: List of message dictionaries with 'role' and 'content'
    - on_message_submit: Callback function to handle message submission
    - current_question_number: Optional current question number for progress tracking
    - total_questions: Optional total questions for progress tracking
    - is_complete: Boolean indicating if the interview is complete
    - is_thinking: Boolean indicating if the system is "thinking" (typing animation)
    
    Returns:
    - None
    """
    
    # Main chat container with enhanced styling
    st.markdown(
        """
        <div class="chat-interface-header">
            <div class="chat-bot-identity">
                <div class="chat-bot-avatar">🤖</div>
                <div class="chat-bot-name">ExitBot Assistant</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    chat_container = st.container()
    
    with chat_container:
        # Show progress bar if we have question number info
        if current_question_number is not None and total_questions is not None and total_questions > 0:
            progress = current_question_number / total_questions
            
            # Enhanced progress display
            st.markdown(
                f"""
                <div class="progress-container">
                    <div class="progress-bar-wrapper">
                        <div class="progress-bar" style="width: {int(progress * 100)}%"></div>
                    </div>
                    <div class="question-progress">
                        <span class="question-counter">Question {current_question_number} of {total_questions}</span>
                        <span class="progress-percentage">{int(progress * 100)}% Complete</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    
        # Messages container with enhanced styling
        st.markdown('<div class="messages-container">', unsafe_allow_html=True)
        
        messages_container = st.container()
        
        with messages_container:
            # Display welcome message if no messages yet
            if not messages:
                st.markdown(
                    """
                    <div class="message bot-message welcome-message animate-fade-in">
                        <div class="message-content">
                            👋 Welcome to your exit interview! I'm here to gather your feedback about your experience. 
                            Please answer honestly - your responses will help improve the workplace for current and future employees.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            # Render all existing messages
            for idx, message in enumerate(messages):
                # Determine if this is from the bot or the user
                is_bot = message["role"] == "assistant"
                
                # Add animation class for newest messages
                animate_class = "animate-fade-in" if idx >= len(messages) - 2 else ""
                
                # Render the message with improved styling
                if is_bot:
                    st.markdown(
                        f"""
                        <div class="message bot-message {animate_class}">
                            <div class="message-avatar">🤖</div>
                            <div class="message-bubble">
                                <div class="message-content">{message["content"]}</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"""
                        <div class="message user-message {animate_class}">
                            <div class="message-bubble">
                                <div class="message-content">{message["content"]}</div>
                            </div>
                            <div class="message-avatar">👤</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                # Tiny delay for animation effect
                if idx >= len(messages) - 2 and idx < len(messages) - 1:
                    time.sleep(0.1)
            
            # Show typing indicator if the system is "thinking"
            if is_thinking:
                st.markdown(
                    """
                    <div class="message bot-message typing-message">
                        <div class="message-avatar">🤖</div>
                        <div class="message-bubble">
                            <div class="typing-animation">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close messages-container
    
    # Input area - only show if the interview is not complete
    if not is_complete:
        st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
        
        # Use columns to create a chat-like input with button
        col1, col2 = st.columns([5, 1])
        
        with col1:
            # Enhanced text input
            user_input = st.text_input(
                "Your response",
                key="chat_input",
                placeholder="Type your response here and press Enter or Send...",
                label_visibility="collapsed",
                disabled=is_thinking  # Disable input while "thinking"
            )
        
        with col2:
            # Submit button with better styling
            send_button = st.button(
                "Send",
                key="send_button",
                use_container_width=True,
                disabled=is_thinking or not user_input.strip()  # Disable if thinking or empty
            )
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close chat-input-container
        
        # Add helpful hint text for users
        if not any(msg["role"] == "user" for msg in messages):
            st.markdown(
                """
                <div class="chat-hint">
                    <span>💡 Tip:</span> Be candid and specific in your answers to provide the most helpful feedback.
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # Handle message submission
        if send_button and user_input.strip():
            # Call the provided callback
            on_message_submit(user_input)
            
            # Clear the input
            st.session_state["chat_input"] = ""
        
        # Allow pressing Enter to submit
        if user_input and st.session_state.get("chat_input_prev") != user_input:
            st.session_state["chat_input_prev"] = user_input
            
            # Check if Enter was likely just pressed (input present and not changed by our reset)
            if user_input.strip() and "chat_input" in st.session_state and st.session_state["chat_input"] == user_input:
                on_message_submit(user_input)
                st.session_state["chat_input"] = ""


# Helper function for the parent component to use
def create_typing_effect(message_placeholder, message_text, delay=0.03):
    """
    Creates a typing effect within a Streamlit placeholder
    
    Parameters:
    - message_placeholder: Streamlit empty placeholder
    - message_text: Full text to display
    - delay: Delay between characters in seconds
    
    Returns:
    - None
    """
    full_message = ""
    
    # Don't actually animate in test environments or if delay is 0
    if delay <= 0:
        message_placeholder.markdown(message_text, unsafe_allow_html=True)
        return
    
    for char in message_text:
        full_message += char
        message_placeholder.markdown(full_message + "▌", unsafe_allow_html=True)
        time.sleep(delay)
    
    # Final message without cursor
    message_placeholder.markdown(full_message, unsafe_allow_html=True) 
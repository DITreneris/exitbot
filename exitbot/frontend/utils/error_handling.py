"""
Error handling utilities for the ExitBot HR app.
Centralizes error display and handling logic.
"""

import logging
import streamlit as st


def display_api_error(error_details, context="Error"):
    """
    Display API error messages using Streamlit components.
    
    Args:
        error_details (dict): Error details from the API response
        context (str): Context message to prefix the error
        
    Returns:
        None
    """
    if error_details:
        message = error_details.get("detail", "An unknown error occurred.")
        logging.warning(
            f"{context}: {message} (Raw: {error_details.get('raw_text')})"
        )  # Log raw details
        st.error(f"{context}: {message}")
    else:
        # This case should ideally not happen if called correctly
        logging.error("display_api_error called with None or empty error_details")
        st.error(
            "An unexpected UI error occurred while trying to display an API error."
        )


def display_empty_state(message, icon="📊", action_button=None):
    """
    Display a friendly empty state message when no data is available.
    
    Args:
        message (str): Main message to display in the empty state
        icon (str): Emoji or icon to display
        action_button (str, optional): Text for the action button
        
    Returns:
        bool: True if action button was clicked, False otherwise
    """
    st.markdown(
        f"""
        <div class="dashboard-empty-state">
            <div class="empty-state-icon">{icon}</div>
            <h2>{message}</h2>
            <p>This might be because:</p>
            <ul>
                <li>The server is still starting up</li>
                <li>There are no records in the selected date range</li>
                <li>Your connection to the data service was interrupted</li>
            </ul>
            <div class="empty-state-action">
                <p>You can try adjusting filters or refreshing the page.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    button_clicked = False
    if action_button:
        button_clicked = st.button(action_button, use_container_width=True)
    
    return button_clicked 
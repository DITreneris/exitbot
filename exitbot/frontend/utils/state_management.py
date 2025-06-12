"""
State management utilities for the ExitBot HR app.
Provides functions for consistent session state initialization and management.
"""

import streamlit as st
from datetime import datetime, timedelta
import extra_streamlit_components as stx


def initialize_session_state():
    """
    Initialize all required session state variables with default values.
    This ensures all components can rely on these variables existing.
    
    Returns:
        None
    """
    # Authentication state
    if "token" not in st.session_state:
        st.session_state.token = None
    
    # Navigation state
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "Dashboard"
    
    # Interview selection state
    if "selected_interview" not in st.session_state:
        st.session_state.selected_interview = None
    
    # Date range for filters
    if "date_range" not in st.session_state:
        st.session_state.date_range = (
            (datetime.now() - timedelta(days=30)).date(),
            datetime.now().date(),
        )
    
    # Search and filter state
    if "search_query" not in st.session_state:
        st.session_state.search_query = ""
    
    if "department_filter" not in st.session_state:
        st.session_state.department_filter = "All"
    
    if "status_filter" not in st.session_state:
        st.session_state.status_filter = "All"


def get_token():
    """
    Get the authentication token from session state.
    
    Returns:
        str: Authentication token or None if not authenticated
    """
    return st.session_state.token


def set_token(token):
    """
    Set the authentication token in session state.
    
    Args:
        token (str): Authentication token
        
    Returns:
        None
    """
    st.session_state.token = token


def clear_token():
    """
    Clear the authentication token from session state.
    
    Returns:
        None
    """
    st.session_state.token = None


def is_authenticated():
    """
    Check if the user is authenticated.
    
    Returns:
        bool: True if authenticated, False otherwise
    """
    return st.session_state.token is not None


def set_active_tab(tab_name):
    """
    Set the active tab in the navigation.
    
    Args:
        tab_name (str): Name of the active tab
        
    Returns:
        None
    """
    st.session_state.active_tab = tab_name


def get_active_tab():
    """
    Get the currently active tab.
    
    Returns:
        str: Name of the active tab
    """
    return st.session_state.active_tab


def set_date_range(start_date, end_date):
    """
    Set the date range for filters.
    
    Args:
        start_date (date): Start date
        end_date (date): End date
        
    Returns:
        None
    """
    st.session_state.date_range = (start_date, end_date)


def get_date_range():
    """
    Get the current date range from session state.
    
    Returns:
        tuple: (start_date, end_date)
    """
    return st.session_state.date_range


def set_selected_interview(interview_id):
    """
    Set the selected interview ID.
    
    Args:
        interview_id (str): ID of the selected interview
        
    Returns:
        None
    """
    st.session_state.selected_interview = interview_id


def get_selected_interview():
    """
    Get the currently selected interview ID.
    
    Returns:
        str: ID of the selected interview or None
    """
    return st.session_state.selected_interview


# Configure a cookie manager instance
def get_cookie_manager():
    """
    Get or create a cookie manager instance.
    
    Returns:
        CookieManager: Cookie manager instance
    """
    # Use a unique key to avoid conflicts with other Streamlit apps
    return stx.CookieManager(key="__hr_app_cookie_manager") 
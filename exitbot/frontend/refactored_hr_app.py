"""
ExitBot HR Dashboard - Main app with modular architecture
"""

import streamlit as st
from datetime import datetime, timedelta, date
import logging
import sys
import os

# Add parent directory to path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Set up page configuration (MUST BE THE FIRST STREAMLIT COMMAND)
st.set_page_config(
    page_title="ExitBot - HR Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",  # This will collapse the sidebar by default
)

# Import API functions
from exitbot.frontend.api_client import login, get_user_profile

# Import utilities
from exitbot.frontend.utils import (
    initialize_session_state,
    get_token,
    set_token,
    clear_token,
    is_authenticated,
    set_active_tab,
    get_active_tab,
    get_cookie_manager,
    display_api_error
)

# Import design system and components
from exitbot.frontend.components.design_system import get_base_css, get_hr_app_css
from exitbot.frontend.components.login import render_login

# Import page components
from exitbot.frontend.pages import (
    render_dashboard, 
    render_interviews, 
    render_reports,
    render_settings
)

# Apply custom styling from the design system
st.markdown(
    get_base_css() + get_hr_app_css() + """
    <style>
    /* Completely hide the default Streamlit sidebar */
    section[data-testid="stSidebar"] {
        display: none !important;
        width: 0px !important;
        height: 0px !important;
        position: absolute !important;
        top: 0px !important;
        left: 0px !important;
        overflow: hidden !important;
        visibility: hidden !important;
        z-index: -1 !important;
    }

    /* Remove the expand sidebar icon */
    .st-emotion-cache-1olp933 {
        display: none !important;
    }

    /* Fix main container width */
    .st-emotion-cache-18ni7ap {
        width: 100% !important;
        margin-left: 0px !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize session state
initialize_session_state()

# Set up cookie manager
cookies = get_cookie_manager()


def render_navigation():
    """Render the main navigation bar with modern design"""
    tabs = [
        {"name": "Dashboard", "icon": "📊"},
        {"name": "Interviews", "icon": "🗣️"},
        {"name": "Reports", "icon": "📈"},
        {"name": "Settings", "icon": "⚙️"}
    ]
    active_tab = get_active_tab()
    nav_html = ""
    for tab in tabs:
        is_active = "active" if tab["name"] == active_tab else ""
        nav_html += (
            f'<form style="margin:0;display:inline;" action="#" method="post">'
            f'<button class="nav-item {is_active}" name="nav_{tab["name"]}" type="submit">{tab["icon"]} {tab["name"]}</button>'
            f'</form>'
        )
    st.markdown(
        f'''
        <style>
        .custom-navbar {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 2rem;
            background: linear-gradient(90deg, #1E40AF 60%, #2563EB 100%);
            border-radius: 16px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 12px -2px rgba(30,64,175,0.08);
            padding: 0.5rem 0.5rem 0.5rem 0.5rem;
        }}
        .custom-navbar .nav-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 1.15rem;
            font-weight: 600;
            color: #DBEAFE;
            background: transparent;
            border: none;
            border-radius: 10px;
            padding: 0.6rem 1.5rem;
            cursor: pointer;
            transition: background 0.2s, color 0.2s, box-shadow 0.2s;
        }}
        .custom-navbar .nav-item.active {{
            background: #fff;
            color: #1E40AF;
            box-shadow: 0 2px 8px 0 rgba(30,64,175,0.10);
        }}
        .custom-navbar .nav-item:hover:not(.active) {{
            background: #2563EB;
            color: #fff;
        }}
        </style>
        <div class="custom-navbar">
            {nav_html}
        </div>
        ''',
        unsafe_allow_html=True
    )
    # Handle navigation
    for tab in tabs:
        if st.session_state.get(f"nav_{tab['name']}"):
            set_active_tab(tab['name'])
            st.rerun()
    # Set session state for navigation
    for tab in tabs:
        st.session_state[f"nav_{tab['name']}"] = False


def render_user_profile(token):
    """Render user profile in header"""
    profile, error = get_user_profile(token)
    
    if error:
        return
    
    name = profile.get("name", "User")
    
    # Add custom CSS for user profile
    st.markdown(
        """
        <style>
        .user-profile {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 10px;
            padding: 10px;
        }
        .user-avatar {
            width: 32px;
            height: 32px;
            background-color: #1E40AF;
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }
        .user-name {
            font-size: 14px;
            font-weight: 500;
            color: #1F2937;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Render user info and logout option
    col1, col2 = st.columns([10, 2])
    
    with col2:
        st.markdown(
            f"""
            <div class="user-profile">
                <div class="user-avatar">{name[0].upper()}</div>
                <div class="user-name">{name}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        if st.button("Logout", key="logout"):
            # Clear token from session state
            clear_token()
            # Clear token from cookies
            cookies.delete("auth_token")
            st.rerun()


def main():
    # Get token from session state or cookies
    token = get_token()
    
    # If no token in session but token in cookies, restore it
    if not token:
        try:
            cookie_token = cookies.get("auth_token")  # Use auth_token instead of token
            if cookie_token:
                set_token(cookie_token)
                token = cookie_token
                st.success("Welcome back! Logged in using saved credentials.")
        except Exception as e:
            logging.error(f"Error retrieving token from cookie: {str(e)}")
            # Continue without the cookie
    
    # Show login screen if not authenticated
    if not token:
        login_successful = render_login(login, cookies)
        if login_successful:
            # The token has already been set in the session state by render_login
            # Just get it and set it in cookies too
            token = get_token()
            try:
                expiration_date = datetime.now() + timedelta(days=7)
                cookies.set("auth_token", token, expires_at=expiration_date)
            except Exception as e:
                logging.error(f"Error saving token to cookie: {str(e)}")
                # Continue anyway as we have token in session state
            st.rerun()
        return
    
    # Show the authenticated UI
    render_user_profile(token)
    render_navigation()
    
    # Render the active page based on the tab
    active_tab = get_active_tab()
    
    if active_tab == "Dashboard":
        render_dashboard(token)
    elif active_tab == "Interviews":
        render_interviews(token)
    elif active_tab == "Reports":
        render_reports(token)
    elif active_tab == "Settings":
        render_settings(token)


if __name__ == "__main__":
    main() 
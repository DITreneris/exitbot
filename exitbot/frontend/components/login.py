"""
Enhanced Login Component for the HR Dashboard

This module provides an enhanced login experience with improved UI/UX based on the design system.
"""

import streamlit as st
from datetime import datetime, timedelta
import logging
import extra_streamlit_components as stx

# Import the design system
from exitbot.frontend.components.design_system import PRIMARY_600

def render_login(login_function, cookie_manager):
    """
    Render an enhanced login form with better UX
    
    Args:
        login_function: Function to call for login API
        cookie_manager: Cookie manager instance for storing token
    
    Returns:
        bool: True if login successful, False otherwise
    """
    # Center-aligned container with max width
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Brand header with app logo and title 
        st.markdown(
            """
            <div class="login-card">
                <div class="brand-header">
                    <div class="app-logo">📊</div>
                    <h1>ExitBot HR Dashboard</h1>
                    <p class="subtitle">Employee exit interview management system</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Welcome text in a separate markdown block with its own style
        st.markdown(
            """
            <style>
            .welcome-text {
                text-align: center;
                color: #4B5563;
                margin-bottom: 24px;
                font-size: 16px;
            }
            </style>
            <div class="welcome-text">
                Sign in to access exit interview data, reports, and settings.
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Login form with enhanced styling
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input(
                "Email",
                placeholder="your.email@company.com",
                help="Enter the email address associated with your HR account"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="••••••••",
                help="Enter your password"
            )
            
            remember_me = st.checkbox("Remember me for 30 days", value=True)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                submitted = st.form_submit_button("Sign In", use_container_width=True)
            with col2:
                st.markdown('<div style="height: 37px;"></div>', unsafe_allow_html=True)
                st.markdown('<a href="#" style="line-height: 37px;">Forgot password?</a>', unsafe_allow_html=True)
                
        if submitted:
            if not email or not password:
                st.warning("Please enter both email and password.")
                return False
                
            # Show loading spinner
            with st.spinner("Signing in..."):
                try:
                    result, error = login_function(email, password)
                    
                    if error:
                        error_msg = error.get('detail', 'Invalid email or password')
                        st.error(f"Login failed: {error_msg}")
                        return False
                        
                    if result:
                        # Store token in session state (result is the token itself, not a dict)
                        st.session_state.token = result
                        
                        # If remember me, store in cookie (expires in 30 days)
                        if remember_me:
                            try:
                                expiration_date = datetime.now() + timedelta(days=30)
                                cookie_manager.set(
                                    cookie='auth_token',
                                    val=result,
                                    expires_at=expiration_date  # Pass datetime object instead of seconds
                                )
                            except Exception as e:
                                st.warning(f"Could not save cookie for automatic login. Error: {str(e)}")
                                # Continue anyway since we have token in session
                            
                        return True
                    else:
                        st.error("Login failed: Unable to authenticate")
                        return False
                except Exception as e:
                    st.error(f"Login error: {str(e)}")
                    logging.error(f"Unexpected login error: {str(e)}")
                    return False
                    
        # Additional helpful information
        st.markdown(
            """
            <div class="login-help">
                <p>Need an account? Contact your system administrator.</p>
                <p>Experiencing issues? <a href="#">Get help</a></p>
            </div>
            """,
            unsafe_allow_html=True
        )
            
    return False


def _display_api_error(error_details, context="Error"):
    """Display API error messages consistently"""
    if error_details:
        message = error_details.get("detail", "An unknown error occurred.")
        logging.warning(
            f"{context}: {message} (Raw: {error_details.get('raw_text')})"
        )
        st.error(f"{context}: {message}")
    else:
        logging.error("display_api_error called with None or empty error_details")
        st.error(
            "An unexpected error occurred while trying to process your request."
        ) 
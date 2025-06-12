"""
Settings page component for the ExitBot HR app.
"""

import streamlit as st

from exitbot.frontend.utils import (
    display_api_error,
    display_empty_state,
    load_settings_data
)
from exitbot.frontend.api_client import (
    update_system_config,
    update_question,
    create_question,
    delete_question
)


def render_profile_settings(profile_data):
    """
    Render user profile settings section.
    
    Args:
        profile_data (dict): User profile data
        
    Returns:
        bool: True if settings were updated, False otherwise
    """
    st.markdown("## Profile Settings")
    
    # Extract profile data with defaults
    name = profile_data.get("name", "")
    email = profile_data.get("email", "")
    role = profile_data.get("role", "HR Manager")
    
    # Show form for editing profile
    with st.form(key="profile_form"):
        # Name field
        new_name = st.text_input("Name", value=name)
        
        # Email field
        new_email = st.text_input("Email", value=email)
        
        # Role selection
        new_role = st.selectbox(
            "Role",
            options=["HR Manager", "HR Specialist", "Department Manager", "Administrator"],
            index=["HR Manager", "HR Specialist", "Department Manager", "Administrator"].index(role) 
                if role in ["HR Manager", "HR Specialist", "Department Manager", "Administrator"] else 0
        )
        
        # Notification preferences
        notifications = st.multiselect(
            "Email Notifications",
            options=[
                "New Exit Interview", 
                "Completed Exit Interview", 
                "Weekly Report Summary"
            ],
            default=profile_data.get("notifications", ["Completed Exit Interview"])
        )
        
        # Submit button
        submitted = st.form_submit_button("Save Profile Settings", use_container_width=True)
        
        if submitted:
            # Here we would call the API to update the profile
            # In a real implementation, we would use an API call
            st.success("Profile settings saved successfully!")
            return True
    
    return False


def render_system_settings(system_config, token):
    """
    Render system configuration settings section.
    
    Args:
        system_config (dict): System configuration data
        token (str): Authentication token
        
    Returns:
        bool: True if settings were updated, False otherwise
    """
    st.markdown("## System Settings")
    
    # Extract config values with defaults
    interview_expiry_days = system_config.get("interview_expiry_days", 14)
    auto_reminders_enabled = system_config.get("auto_reminders_enabled", True)
    reminder_days = system_config.get("reminder_days", 3)
    sentiment_analysis_enabled = system_config.get("sentiment_analysis_enabled", True)
    anonymize_reports = system_config.get("anonymize_reports", False)
    language = system_config.get("language", "en")
    
    # Settings form
    with st.form(key="system_settings_form"):
        # Interview expiry setting
        new_expiry_days = st.number_input(
            "Interview Expiry (days)",
            min_value=1,
            max_value=60,
            value=interview_expiry_days,
            help="Number of days before an interview link expires"
        )
        
        # Auto reminders toggle
        new_auto_reminders = st.checkbox(
            "Enable Automatic Reminders",
            value=auto_reminders_enabled,
            help="Send automatic reminders for incomplete interviews"
        )
        
        # Reminder days (only shown if auto reminders enabled)
        new_reminder_days = 3
        if new_auto_reminders:
            new_reminder_days = st.number_input(
                "Reminder Days Before Expiry",
                min_value=1,
                max_value=10,
                value=reminder_days,
                help="Days before expiry to send a reminder"
            )
        
        # Sentiment analysis toggle
        new_sentiment_analysis = st.checkbox(
            "Enable Sentiment Analysis",
            value=sentiment_analysis_enabled,
            help="Automatically analyze sentiment in exit interviews"
        )
        
        # Anonymize reports toggle
        new_anonymize_reports = st.checkbox(
            "Anonymize Reports by Default",
            value=anonymize_reports,
            help="Remove identifiable information from reports by default"
        )
        
        # Language selection
        new_language = st.selectbox(
            "Default Language",
            options=["en", "es", "fr", "de", "zh"],
            index=["en", "es", "fr", "de", "zh"].index(language) if language in ["en", "es", "fr", "de", "zh"] else 0,
            help="Default language for exit interviews"
        )
        
        # Submit button
        submitted = st.form_submit_button("Save System Settings", use_container_width=True)
        
        if submitted:
            # Prepare the updated config
            updated_config = {
                "interview_expiry_days": new_expiry_days,
                "auto_reminders_enabled": new_auto_reminders,
                "reminder_days": new_reminder_days,
                "sentiment_analysis_enabled": new_sentiment_analysis,
                "anonymize_reports": new_anonymize_reports,
                "language": new_language
            }
            
            # Call API to update system config
            result, error = update_system_config(token, updated_config)
            
            if error:
                display_api_error(error, "Failed to save system settings")
            else:
                st.success("System settings saved successfully!")
                return True
    
    return False


def render_question_management(questions_data, token):
    """
    Render question template management section.
    
    Args:
        questions_data (list): List of question templates
        token (str): Authentication token
        
    Returns:
        bool: True if questions were updated, False otherwise
    """
    st.markdown("## Interview Questions")
    
    # Initialize session state for editing
    if "editing_question" not in st.session_state:
        st.session_state.editing_question = None
    
    if "adding_question" not in st.session_state:
        st.session_state.adding_question = False
    
    # Button to add new question
    if not st.session_state.adding_question and st.session_state.editing_question is None:
        if st.button("+ Add New Question", use_container_width=True):
            st.session_state.adding_question = True
            st.rerun()
    
    # Form to add new question
    if st.session_state.adding_question:
        with st.form(key="add_question_form"):
            st.markdown("### Add New Question")
            
            question_text = st.text_area("Question Text", value="")
            
            question_type = st.selectbox(
                "Question Type",
                options=["text", "multiple_choice", "rating"],
                index=0
            )
            
            # Options for multiple choice questions
            options = []
            if question_type == "multiple_choice":
                option_text = st.text_area(
                    "Options (one per line)",
                    value="",
                    help="Enter each option on a new line"
                )
                options = [opt.strip() for opt in option_text.split("\n") if opt.strip()]
            
            # Category selection
            category = st.selectbox(
                "Category",
                options=[
                    "Experience", 
                    "Management", 
                    "Compensation", 
                    "Work Environment", 
                    "Career Growth", 
                    "Other"
                ]
            )
            
            # Required toggle
            required = st.checkbox("Required Question", value=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                cancel = st.form_submit_button("Cancel", use_container_width=True)
                
            with col2:
                submit = st.form_submit_button("Add Question", use_container_width=True)
            
            if cancel:
                st.session_state.adding_question = False
                st.rerun()
            
            if submit:
                # Create new question object
                new_question = {
                    "text": question_text,
                    "type": question_type,
                    "required": required,
                    "category": category
                }
                
                if question_type == "multiple_choice":
                    new_question["options"] = options
                
                # Call API to create question
                result, error = create_question(token, new_question)
                
                if error:
                    display_api_error(error, "Failed to create question")
                else:
                    st.success("Question created successfully!")
                    st.session_state.adding_question = False
                    return True
    
    # Display existing questions
    if questions_data:
        # Show questions by category
        categories = {}
        for question in questions_data:
            category = question.get("category", "Other")
            if category not in categories:
                categories[category] = []
            categories[category].append(question)
        
        # Tabs for each category
        if categories:
            tabs = st.tabs(list(categories.keys()))
            
            for i, (category, questions) in enumerate(categories.items()):
                with tabs[i]:
                    for question in questions:
                        question_id = question.get("id", "")
                        text = question.get("text", "")
                        q_type = question.get("type", "text")
                        
                        # Check if this question is being edited
                        if st.session_state.editing_question == question_id:
                            with st.form(key=f"edit_question_{question_id}"):
                                st.markdown(f"### Edit Question")
                                
                                new_text = st.text_area("Question Text", value=text)
                                
                                # Type can't be changed after creation
                                st.text(f"Type: {q_type.replace('_', ' ').title()}")
                                
                                # Options for multiple choice
                                options = []
                                if q_type == "multiple_choice":
                                    current_options = question.get("options", [])
                                    option_text = st.text_area(
                                        "Options (one per line)",
                                        value="\n".join(current_options),
                                        help="Enter each option on a new line"
                                    )
                                    options = [opt.strip() for opt in option_text.split("\n") if opt.strip()]
                                
                                # Required toggle
                                required = st.checkbox("Required Question", value=question.get("required", True))
                                
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    cancel = st.form_submit_button("Cancel", use_container_width=True)
                                    
                                with col2:
                                    submit = st.form_submit_button("Save Changes", use_container_width=True)
                                
                                if cancel:
                                    st.session_state.editing_question = None
                                    st.rerun()
                                
                                if submit:
                                    # Create updated question object
                                    updated_question = {
                                        "id": question_id,
                                        "text": new_text,
                                        "type": q_type,
                                        "required": required,
                                        "category": category
                                    }
                                    
                                    if q_type == "multiple_choice":
                                        updated_question["options"] = options
                                    
                                    # Call API to update question
                                    result, error = update_question(token, question_id, updated_question)
                                    
                                    if error:
                                        display_api_error(error, "Failed to update question")
                                    else:
                                        st.success("Question updated successfully!")
                                        st.session_state.editing_question = None
                                        return True
                        else:
                            # Display question card with edit/delete buttons
                            col1, col2 = st.columns([10, 2])
                            
                            with col1:
                                st.markdown(f"**{text}**")
                                st.markdown(f"Type: {q_type.replace('_', ' ').title()}")
                                
                                if q_type == "multiple_choice":
                                    options = question.get("options", [])
                                    if options:
                                        st.markdown("Options:")
                                        for option in options:
                                            st.markdown(f"- {option}")
                                
                                if question.get("required", False):
                                    st.markdown("**Required**")
                            
                            with col2:
                                # Edit button
                                if st.button("Edit", key=f"edit_{question_id}"):
                                    st.session_state.editing_question = question_id
                                    st.rerun()
                                
                                # Delete button
                                if st.button("Delete", key=f"delete_{question_id}"):
                                    # Confirm deletion
                                    if st.button(f"Confirm Delete", key=f"confirm_{question_id}"):
                                        # Call API to delete question
                                        result, error = delete_question(token, question_id)
                                        
                                        if error:
                                            display_api_error(error, "Failed to delete question")
                                        else:
                                            st.success("Question deleted successfully!")
                                            return True
                            
                            # Add separator
                            st.markdown("---")
    else:
        st.info("No question templates found. Add your first question to get started.")


def render_settings(token):
    """
    Render the settings page with profile, system, and question management.
    
    Args:
        token (str): Authentication token
        
    Returns:
        None
    """
    st.markdown(
        """
        <div class="settings-header">
            <h1>Settings</h1>
            <div class="settings-subtitle">
                Manage your profile, system configuration, and interview questions.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Load settings data
    settings_data, error = load_settings_data(token)
    
    if error:
        display_api_error(error, "Failed to load settings")
        return
    
    # Extract settings components
    profile_data = settings_data.get("user_profile", {})
    system_config = settings_data.get("system_config", {})
    questions_data = settings_data.get("questions", [])
    
    # Create tabs for different settings sections
    profile_tab, system_tab, questions_tab = st.tabs([
        "Profile", "System Configuration", "Interview Questions"
    ])
    
    # Render profile settings tab
    with profile_tab:
        if render_profile_settings(profile_data):
            st.rerun()
    
    # Render system settings tab
    with system_tab:
        if render_system_settings(system_config, token):
            st.rerun()
    
    # Render question management tab
    with questions_tab:
        if render_question_management(questions_data, token):
            st.rerun() 
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime, timedelta, date
import extra_streamlit_components as stx # Import for cookie manager
import logging # Import logging

# Page configuration (MUST BE THE FIRST STREAMLIT COMMAND)
st.set_page_config(
    page_title="ExitBot - HR Dashboard",
    page_icon="📊",
    layout="wide",
)

# Import API functions from the new client module
from exitbot.frontend.api_client import (
    login,
    get_all_interviews,
    get_interview_details,
    get_interview_summary,
    get_summary_stats,
    get_department_breakdown,
    export_data,
    get_questions,     # <-- Import new question functions
    create_question,
    update_question,
    delete_question,
    get_system_config, # <-- Import new config functions
    update_system_config 
)

# Initialize Cookie Manager - key should be unique for the app
# Using double underscore might help avoid clashes if deploying multiple apps
cookies = stx.CookieManager(key="__hr_app_cookie_manager")

# Custom styling
st.markdown("""
<style>
.dashboard-title {
    font-size: 2.5rem;
    font-weight: bold;
}
.card {
    border-radius: 5px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    padding: 1rem;
    margin-bottom: 1rem;
}
.metric-card {
    text-align: center;
    font-size: 1.2rem;
}
.metric-value {
    font-size: 2rem;
    font-weight: bold;
}
.info-text {
    font-size: 0.8rem;
    color: #888;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "token" not in st.session_state:
    st.session_state.token = None # Default if no cookie either
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Dashboard"
if "selected_interview" not in st.session_state:
    st.session_state.selected_interview = None
if "date_range" not in st.session_state:
    st.session_state.date_range = (
        (datetime.now() - timedelta(days=30)).date(),
        datetime.now().date()
    )

# --- Helper Functions ---
def display_api_error(error_details, context="Error"):
    """Display API error messages using Streamlit components."""
    if error_details:
        message = error_details.get('detail', "An unknown error occurred.")
        logging.warning(f"{context}: {message} (Raw: {error_details.get('raw_text')})") # Log raw details
        st.error(f"{context}: {message}")
    else:
        # This case should ideally not happen if called correctly
        logging.error("display_api_error called with None or empty error_details")
        st.error("An unexpected UI error occurred while trying to display an API error.")

# --- UI Components ---
def render_login():
    """Render login form"""
    st.markdown('<div class="dashboard-title">ExitBot HR Dashboard</div>', unsafe_allow_html=True)
    st.write("Please login to access the HR dashboard.")
    
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="admin@example.com")
        password = st.text_input("Password", type="password")
        
        submit = st.form_submit_button("Login")
        
        if submit:
            if not email or not password:
                st.error("Please provide email and password")
            else:
                # Call the imported login function
                token, error = login(email, password)
                if error:
                    display_api_error(error, "Login failed")
                elif token:
                    st.session_state.token = token
                    # Persist token in cookie
                    expires_at = datetime.now() + timedelta(days=7)
                    cookies.set('auth_token', token, expires_at=expires_at)
                    st.success("Login successful!")
                    st.rerun()
                else:
                    # Should not happen if login() returns correctly
                    st.error("Login returned unexpected result.")

def render_dashboard(token):
    """Render main dashboard"""
    # Sidebar navigation
    with st.sidebar:
        st.title("ExitBot")
        selected = st.radio(
            "Navigation",
            ["Dashboard", "Interviews", "Reports", "Settings"],
            key="navigation"
        )
        st.session_state.active_tab = selected
        
        # Date range selector for filtering
        st.subheader("Date Range")
        start_date, end_date = st.date_input(
            "Select date range",
            value=st.session_state.date_range,
            min_value=date(2020, 1, 1),
            max_value=datetime.now().date(),
        )
        st.session_state.date_range = (start_date, end_date)
        
        # Logout button
        if st.button("Logout"):
            # --- Flag that logout is requested ---
            st.session_state.logout_requested = True 
            # Clear session state token
            st.session_state.token = None
            # Clear cache potentially? Caching is handled by TTL now.
            st.rerun()
    
    # Main content area - Calls use the imported API functions
    if st.session_state.active_tab == "Dashboard":
        render_dashboard_tab(token, st.session_state.date_range[0], st.session_state.date_range[1])
    elif st.session_state.active_tab == "Interviews":
        render_interviews_tab(token)
    elif st.session_state.active_tab == "Reports":
        render_reports_tab(token, st.session_state.date_range[0], st.session_state.date_range[1])
    elif st.session_state.active_tab == "Settings":
        render_settings_tab(token)

def render_dashboard_tab(token, start_date, end_date):
    """Render dashboard overview tab"""
    st.title("Dashboard")
    st.write(f"Overview of exit interviews from {start_date} to {end_date}")
    
    # Fetch summary stats
    stats, error = get_summary_stats(token, start_date, end_date)
    if error:
        display_api_error(error, "Could not load dashboard statistics")
        # Optionally return or display minimal dashboard
        return 

    if stats:
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(
                f"""
                <div class="card metric-card">
                    <div>Total Interviews</div>
                    <div class="metric-value">{stats['total_interviews']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        with col2:
            st.markdown(
                f"""
                <div class="card metric-card">
                    <div>Completed</div>
                    <div class="metric-value">{stats.get('interviews_by_status', {}).get('completed', 0)}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        with col3:
            st.markdown(
                f"""
                <div class="card metric-card">
                    <div>In Progress</div>
                    <div class="metric-value">{stats.get('interviews_by_status', {}).get('in_progress', 0)}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        with col4:
            sentiment = stats['average_sentiment']
            sentiment_value = f"{sentiment:.2f}" if sentiment is not None else "N/A"
            st.markdown(
                f"""
                <div class="card metric-card">
                    <div>Avg. Sentiment</div>
                    <div class="metric-value">{sentiment_value}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # Display exit reasons chart
        st.subheader("Top Exit Reasons")
        if stats.get('top_exit_reasons'): # Use .get for safety
            reasons_df = pd.DataFrame(stats['top_exit_reasons'])
            fig = px.bar(
                reasons_df,
                x='reason',
                y='count',
                labels={'reason': 'Reason', 'count': 'Count'},
                title='Top Reasons for Leaving'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No exit reasons data available.")
        
        # --- TEMPORARY DEBUG: Comment out Department Breakdown --- 
        # departments_data, error = get_department_breakdown(token, start_date, end_date)
        # if error:
        #      display_api_error(error, "Could not load department breakdown")
        # elif departments_data and departments_data.get('departments'):
        #     st.subheader("Department Breakdown")
        #     dept_df = pd.DataFrame(departments_data['departments'])
            
        #     col1, col2 = st.columns([3, 2])
            
        #     with col1:
        #         # Department interview counts
        #         fig = px.bar(
        #             dept_df,
        #             x='department',
        #             y='interview_count',
        #             labels={'department': 'Department', 'interview_count': 'Exit Interviews'},
        #             title='Exit Interviews by Department'
        #         )
        #         st.plotly_chart(fig, use_container_width=True)
            
        #     with col2:
        #         # Department sentiment
        #         if 'sentiment_score' in dept_df.columns:
        #             # Create a sentiment gauge for each department
        #             for i, row in dept_df.iterrows():
        #                 dept = row['department']
        #                 sentiment = row['sentiment_score'] if row['sentiment_score'] is not None else 0
                        
        #                 fig = go.Figure(go.Indicator(
        #                     mode="gauge+number",
        #                     value=sentiment,
        #                     domain={'x': [0, 1], 'y': [0, 1]},
        #                     title={'text': f"{dept} Sentiment"},
        #                     gauge={
        #                         'axis': {'range': [-1, 1]},
        #                         'bar': {'color': "darkblue"},
        #                         'steps': [
        #                             {'range': [-1, -0.5], 'color': "red"},
        #                             {'range': [-0.5, 0], 'color': "orange"},
        #                             {'range': [0, 0.5], 'color': "lightgreen"},
        #                             {'range': [0.5, 1], 'color': "green"}
        #                         ],
        #                     }
        #                 ))
        #                 fig.update_layout(height=200)
        #                 st.plotly_chart(fig, use_container_width=True)
        # --- END TEMPORARY DEBUG ---

    else:
        st.warning("No dashboard data available for the selected period.") # Keep this if stats is None/empty but no error

def render_interviews_tab(token):
    """Render interviews list and details tab"""
    st.title("Exit Interviews")
    
    # Fetch interviews
    interviews_list, error = get_all_interviews(token)
    if error:
        display_api_error(error, "Could not load interviews")
        return

    if interviews_list:
        # Convert to DataFrame for display
        interviews_df = pd.DataFrame(interviews_list)
        
        if not interviews_df.empty:
            # Add formatting
            interviews_df['created_at'] = pd.to_datetime(interviews_df['created_at']).dt.date
            interviews_df['status'] = interviews_df['status'].apply(
                lambda x: f"<span style='color: {'green' if x == 'completed' else 'orange'};'>{x}</span>"
            )
            
            # Display as table
            st.write("### All Exit Interviews")
            
            # Add filter options
            col1, col2 = st.columns(2)
            with col1:
                status_filter = st.multiselect(
                    "Filter by status",
                    options=["completed", "in_progress"],
                    default=["completed", "in_progress"]
                )
            
            # Apply filters
            filtered_df = interviews_df
            if status_filter:
                # Need to filter on the original values, not the HTML formatted ones
                filtered_df = interviews_df[interviews_df['status'].str.contains('|'.join(status_filter))]
            
            # Display table with clickable rows
            st.dataframe(
                filtered_df[['id', 'employee_id', 'created_at', 'status']],
                column_config={
                    "id": "Interview ID",
                    "employee_id": "Employee ID",
                    "created_at": "Date",
                    "status": "Status"
                },
                use_container_width=True,
                hide_index=True
            )
            
            # Interview selection
            selected_id = st.selectbox(
                "Select interview to view details",
                options=filtered_df['id'].tolist(),
                format_func=lambda x: f"Interview #{x}"
            )
            
            if selected_id:
                st.session_state.selected_interview = selected_id
                
        else:
            st.info("No interviews found in the system.")
    else:
        st.warning("Could not load interviews. Please check your connection.")
    
    # Display interview details if selected
    if st.session_state.selected_interview:
        st.write(f"### Interview #{st.session_state.selected_interview} Details")
        
        interview_details, error = get_interview_details(token, st.session_state.selected_interview)
        if error:
            display_api_error(error, f"Could not load details for interview {st.session_state.selected_interview}")
        elif interview_details:
            # Employee info
            st.write(f"**Status:** {interview_details['status']}")
            st.write(f"**Employee ID:** {interview_details['employee_id']}")
            st.write(f"**Date:** {interview_details['created_at']}")
            
            # Summary section
            with st.expander("Interview Summary", expanded=True):
                summary, error = get_interview_summary(token, st.session_state.selected_interview)
                if error:
                    display_api_error(error, f"Could not load summary for interview {st.session_state.selected_interview}")
                    st.markdown("Summary could not be loaded.")
                else:
                    st.markdown(summary) # Display summary or "Not available" message from API client
            
            # Responses
            if 'responses' in interview_details and interview_details['responses']:
                st.write("### Responses")
                
                for i, response in enumerate(interview_details['responses']):
                    with st.expander(f"Question {i+1}", expanded=i==0):
                        st.write(f"**Question:** {response.get('question_text', 'Unknown')}")
                        st.write(f"**Employee:** {response.get('employee_message', 'No response')}")
                        st.write(f"**Bot:** {response.get('bot_response', 'No response')}")
                        
                        # Display sentiment if available
                        sentiment = response.get('sentiment')
                        if sentiment is not None:
                            sentiment_val = float(sentiment)
                            color = "red" if sentiment_val < -0.3 else "orange" if sentiment_val < 0.3 else "green"
                            st.markdown(f"**Sentiment:** <span style='color:{color};'>{sentiment_val:.2f}</span>", unsafe_allow_html=True)
            else:
                st.info("No responses recorded for this interview.")
        else:
            st.warning("No details found for the selected interview.") # If details are None but no error

def render_reports_tab(token, start_date, end_date):
    """Render reports and data export tab"""
    st.title("Reports & Exports")
    
    # Date range for reports
    col1, col2 = st.columns(2)
    with col1:
        report_start_date = st.date_input("Report start date", value=start_date)
    with col2:
        report_end_date = st.date_input("Report end date", value=end_date)
    
    # Report tabs
    report_tab = st.radio(
        "Report Type",
        ["Summary Statistics", "Department Analysis", "Export Data"],
        horizontal=True
    )
    
    if report_tab == "Summary Statistics":
        stats, error = get_summary_stats(token, report_start_date, report_end_date)
        if error:
            display_api_error(error, "Could not load summary statistics")
        elif stats:
            st.write("### Exit Interview Statistics")
            st.write(f"Period: {report_start_date} to {report_end_date}")
            
            st.metric("Total Interviews", stats['total_interviews'])
            st.metric("Completion Rate", f"{stats['completed_interviews'] / max(1, stats['total_interviews']):.0%}")
            
            if stats['average_sentiment'] is not None:
                sentiment_val = float(stats['average_sentiment'])
                st.metric("Average Sentiment", f"{sentiment_val:.2f}")
                
                # Interpret sentiment
                if sentiment_val < -0.3:
                    st.error("Overall negative sentiment detected. Consider reviewing exit interview details.")
                elif sentiment_val < 0.3:
                    st.warning("Neutral sentiment detected.")
                else:
                    st.success("Overall positive sentiment detected.")
            
            # Exit reasons chart
            if stats['top_exit_reasons']:
                reasons_df = pd.DataFrame(stats['top_exit_reasons'])
                fig = px.pie(
                    reasons_df,
                    values='count',
                    names='reason',
                    title='Top Reasons for Leaving'
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No statistics data available for the selected period.")
            
    elif report_tab == "Department Analysis":
        departments_data, error = get_department_breakdown(token, report_start_date, report_end_date)
        if error:
            display_api_error(error, "Could not load department analysis")
        elif departments_data and departments_data.get('departments'):
            st.write("### Department Analysis")
            st.write(f"Period: {report_start_date} to {report_end_date}")
            
            dept_df = pd.DataFrame(departments_data['departments'])
            
            # Department interview counts
            fig = px.bar(
                dept_df,
                x='department',
                y='interview_count',
                labels={'department': 'Department', 'interview_count': 'Exit Interviews'},
                title='Exit Interviews by Department'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Department sentiment comparison
            if 'sentiment_score' in dept_df.columns:
                sentiment_df = dept_df.dropna(subset=['sentiment_score'])
                if not sentiment_df.empty:
                    fig = px.bar(
                        sentiment_df,
                        x='department',
                        y='sentiment_score',
                        labels={'department': 'Department', 'sentiment_score': 'Sentiment Score'},
                        title='Sentiment Analysis by Department',
                        color='sentiment_score',
                        color_continuous_scale=['red', 'yellow', 'green'],
                        range_color=[-1, 1]
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Findings
                    max_dept = sentiment_df.loc[sentiment_df['sentiment_score'].idxmax()]
                    min_dept = sentiment_df.loc[sentiment_df['sentiment_score'].idxmin()]
                    
                    st.write("### Key Findings")
                    st.write(f"**Highest Sentiment:** {max_dept['department']} ({max_dept['sentiment_score']:.2f})")
                    st.write(f"**Lowest Sentiment:** {min_dept['department']} ({min_dept['sentiment_score']:.2f})")
                    
                    if max_dept['sentiment_score'] - min_dept['sentiment_score'] > 0.5:
                        st.warning("Significant sentiment variation between departments detected.")
        else:
            st.warning("No department data available for the selected period.")
            
    elif report_tab == "Export Data":
        st.write("### Export Exit Interview Data")
        
        # Export settings
        export_format = st.selectbox("Export format", ["JSON", "CSV"], index=0)
        department_filter = st.text_input("Filter by department (optional)")
        
        if st.button("Generate Export"):
            with st.spinner("Generating export..."):
                export_content, error = export_data(
                    token,
                    format=export_format.lower(),
                    start_date=report_start_date,
                    end_date=report_end_date,
                    department=department_filter if department_filter else None
                )
                
                if error:
                    display_api_error(error, "Failed to generate export data")
                elif export_content:
                    # Convert to appropriate format
                    if export_format == "JSON":
                        export_str = json.dumps(export_content, indent=2)
                        mime = "application/json"
                        file_ext = "json"
                    else:  # CSV
                        # Flatten the data for CSV export
                        flat_data = []
                        for interview in export_content:
                            for response in interview.get('responses', []):
                                flat_data.append({
                                    'interview_id': interview['id'],
                                    'employee_id': interview['employee_id'],
                                    'department': interview.get('department'),
                                    'status': interview['status'],
                                    'question': response.get('question'),
                                    'employee_response': response.get('employee_message'),
                                    'sentiment': response.get('sentiment'),
                                })
                                
                        export_df = pd.DataFrame(flat_data)
                        export_str = export_df.to_csv(index=False)
                        mime = "text/csv"
                        file_ext = "csv"
                    
                    # Provide download link
                    filename = f"exitbot_export_{report_start_date}_{report_end_date}.{file_ext}"
                    st.download_button(
                        label=f"Download {export_format}",
                        data=export_str,
                        file_name=filename,
                        mime=mime
                    )
                else:
                    st.error("Export generation returned no content.") # If content is None/empty but no error

def render_settings_tab(token):
    """Render settings tab with Question Management and System Preferences"""
    st.title("Settings")
    
    tab1, tab2, tab3 = st.tabs(["Question Management", "System Preferences", "About"])

    with tab1:
        st.subheader("Manage Interview Questions")
        
        # Fetch questions
        questions, error = get_questions(token)
        if error:
            display_api_error(error, "Could not load questions")
            # Prevent rest of the tab from rendering if questions can't be loaded
            return 

        # --- Add New Question Form ---
        with st.form("new_question_form", clear_on_submit=True):
            new_question_text = st.text_area("Enter new question text:", height=100)
            submitted = st.form_submit_button("Add Question")
            if submitted and new_question_text:
                result, error = create_question(token, new_question_text)
                if error:
                    display_api_error(error, "Failed to add question")
                elif result:
                    st.success(f"Question added (ID: {result.get('id', 'N/A')})")
                    # Rerun needed to refresh the list from cache potentially
                    st.rerun()
                else:
                     st.error("Failed to add question (unexpected result).") # Should be caught by error handling ideally
            elif submitted:
                st.warning("Please enter text for the new question.")
        
        st.divider()
        
        # --- Display Existing Questions ---
        if questions:
            st.write("**Current Questions:**")
            
            # Use columns for better layout
            col_text, col_active, col_actions = st.columns([4, 1, 1])
            col_text.write("**Question Text**")
            col_active.write("**Active**")
            col_actions.write("**Actions**")

            for q in questions:
                q_id = q.get('id')
                q_text = q.get('text', 'N/A')
                q_active = q.get('is_active', False)
                
                col1, col2, col3 = st.columns([4, 1, 1])
                
                with col1:
                    # Allow editing text directly (might be complex to manage state)
                    # Alternative: Button to open an edit modal/form
                    # For simplicity, let's just display it for now.
                    st.write(q_text)
                
                with col2:
                    # Toggle for activation status
                    new_active_state = st.toggle("Active", value=q_active, key=f"active_toggle_{q_id}")
                    if new_active_state != q_active:
                        if f"update_active_{q_id}" not in st.session_state:
                            st.session_state[f"update_active_{q_id}"] = new_active_state
                            update_result, error = update_question(token, q_id, is_active=new_active_state)
                            del st.session_state[f"update_active_{q_id}"] # Clear flag regardless of outcome
                            if error:
                                display_api_error(error, f"Failed to update status for question {q_id}")
                                st.session_state[f"active_toggle_{q_id}"] = q_active # Revert visual state
                            else:
                                st.success(f"Question {q_id} status updated.")
                            # Rerun needed to reflect change visually and clear cache potentially
                            st.rerun()
                                
                with col3:
                    # Delete button
                    if st.button("Delete", key=f"del_btn_{q_id}"):
                        delete_result, error = delete_question(token, q_id)
                        if error:
                            display_api_error(error, f"Failed to delete question {q_id}")
                        elif delete_result: # Should be True on success (or None if error)
                            st.success(f"Question {q_id} deleted.")
                            st.rerun() # Refresh list
                        # else: # No explicit action if delete_result is False/None without error (shouldn't happen)

                st.divider()
                    
        else: # This case now means questions list is empty, not necessarily an error
            st.info("No questions found. Add some using the form above.")

    with tab2: # System Preferences
        st.subheader("System Preferences")
        
        config, error = get_system_config(token)
        
        if error:
            display_api_error(error, "Could not load system configuration")
        elif config:
            # Use form for batch updates
            with st.form("system_config_form"):
                st.write("Configure system-wide settings.")
                
                # Example settings (replace with actual config keys)
                llm_model = st.selectbox(
                    "LLM Model for Summaries/Analysis", 
                    options=["ollama/llama2", "ollama/mistral", "placeholder/gpt-4"], # Example options
                    index=["ollama/llama2", "ollama/mistral", "placeholder/gpt-4"].index(config.get("llm_model", "ollama/llama2"))
                )
                
                sentiment_pos = st.slider(
                    "Positive Sentiment Threshold", 
                    min_value=0.0, max_value=1.0, 
                    value=float(config.get("sentiment_threshold_positive", 0.3)), 
                    step=0.05
                )
                
                sentiment_neg = st.slider(
                    "Negative Sentiment Threshold", 
                    min_value=-1.0, max_value=0.0, 
                    value=float(config.get("sentiment_threshold_negative", -0.3)), 
                    step=0.05
                )
                
                report_format = st.selectbox(
                    "Default Report Format",
                    options=["json", "csv"], # Example options
                    index=["json", "csv"].index(config.get("default_report_format", "json"))
                )
                
                # Submit button for the form
                submitted = st.form_submit_button("Save Preferences")
                if submitted:
                    new_config_data = {
                        "llm_model": llm_model,
                        "sentiment_threshold_positive": sentiment_pos,
                        "sentiment_threshold_negative": sentiment_neg,
                        "default_report_format": report_format
                        # Add other settings as needed
                    }
                    updated_config, update_error = update_system_config(token, new_config_data)
                    if update_error:
                        display_api_error(update_error, "Failed to save preferences")
                    else:
                        st.success("Preferences saved successfully!")
                        # Rerun might be needed if get_system_config cache needs refreshing
                        # The placeholder update function clears it, but real API might differ
                        st.rerun()
                        
        else:
             st.warning("System configuration could not be loaded or is empty.")

    with tab3:
        st.write("### About ExitBot")
        st.write("""
        ExitBot is an HR exit interview bot that conducts structured exit interviews with departing employees,
        collects feedback, and generates reports for HR using Ollama for local LLM inference.
        
        Version: 0.1.0
        """)

# Main App Logic
def main():
    # --- Handle logout request first ---
    if st.session_state.get('logout_requested', False):
        try:
            cookies.delete('auth_token')
        except KeyError:
            # Cookie might already be deleted or wasn't set
            pass
        # Ensure token is cleared JUST IN CASE it was re-read before this point
        st.session_state.token = None 
        st.session_state.logout_requested = False # Reset flag
        # No need to rerun here, the rest of the script will execute and 
        # the token being None will lead to the login page.
        
    # --- Attempt to load token from cookie at the start ---
    # This needs to run on every script run to potentially load the state
    if not st.session_state.token: # Only try loading from cookie if not already logged in this session
        auth_token_from_cookie = cookies.get('auth_token')
        if auth_token_from_cookie:
            st.session_state.token = auth_token_from_cookie
            # Optional: Add a check here to verify the token with the backend (e.g., a '/me' endpoint)
            # If verification fails, delete the cookie and set st.session_state.token = None

    # Check if user is logged in
    if st.session_state.token:
        render_dashboard(st.session_state.token)
    else:
        render_login()

if __name__ == "__main__":
    main() 
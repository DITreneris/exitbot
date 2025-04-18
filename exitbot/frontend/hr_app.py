import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from datetime import datetime, timedelta, date

# API connection settings
API_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="ExitBot - HR Dashboard",
    page_icon="📊",
    layout="wide",
)

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
    st.session_state.token = None
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Dashboard"
if "selected_interview" not in st.session_state:
    st.session_state.selected_interview = None
if "date_range" not in st.session_state:
    st.session_state.date_range = (
        (datetime.now() - timedelta(days=30)).date(),
        datetime.now().date()
    )

# Authentication functions
def login(email, password):
    """Login to the API"""
    try:
        response = requests.post(
            f"{API_URL}/api/auth/login",
            data={"username": email, "password": password}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            st.error(f"Login failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to server: {str(e)}")
        return None

# API functions
def get_all_interviews(token, skip=0, limit=100):
    """Fetch all interviews from API"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_URL}/api/interviews?skip={skip}&limit={limit}",
            headers=headers
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.warning(f"Failed to fetch interviews: {response.text}")
            return []
    except Exception as e:
        st.error(f"Error connecting to server: {str(e)}")
        return []

def get_interview_details(token, interview_id):
    """Fetch details for a specific interview"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_URL}/api/interviews/{interview_id}",
            headers=headers
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.warning(f"Failed to fetch interview details: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to server: {str(e)}")
        return None

def get_interview_summary(token, interview_id):
    """Fetch summary for a specific interview"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_URL}/api/reports/interview/{interview_id}/summary",
            headers=headers
        )
        if response.status_code == 200:
            return response.text
        else:
            st.warning(f"Failed to fetch interview summary: {response.text}")
            return "Summary not available."
    except Exception as e:
        st.error(f"Error connecting to server: {str(e)}")
        return "Error generating summary."

def get_summary_stats(token, start_date=None, end_date=None):
    """Fetch summary statistics"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        params = {}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
            
        response = requests.get(
            f"{API_URL}/api/reports/summary",
            headers=headers,
            params=params
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.warning(f"Failed to fetch summary stats: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to server: {str(e)}")
        return None

def get_department_breakdown(token, start_date=None, end_date=None):
    """Fetch department breakdown"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        params = {}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
            
        response = requests.get(
            f"{API_URL}/api/reports/by-department",
            headers=headers,
            params=params
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.warning(f"Failed to fetch department breakdown: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to server: {str(e)}")
        return None

def export_data(token, format="json", start_date=None, end_date=None, department=None):
    """Export interview data"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        params = {"format": format}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        if department:
            params["department"] = department
            
        response = requests.get(
            f"{API_URL}/api/reports/export",
            headers=headers,
            params=params
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.warning(f"Failed to export data: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to server: {str(e)}")
        return None

# UI Components
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
                token = login(email, password)
                if token:
                    st.session_state.token = token
                    st.success("Login successful!")
                    st.rerun()

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
            st.session_state.token = None
            st.rerun()
    
    # Main content area
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
    stats = get_summary_stats(token, start_date, end_date)
    
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
                    <div class="metric-value">{stats['completed_interviews']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        with col3:
            st.markdown(
                f"""
                <div class="card metric-card">
                    <div>In Progress</div>
                    <div class="metric-value">{stats['in_progress_interviews']}</div>
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
        if stats['top_exit_reasons']:
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
        
        # Department breakdown
        departments = get_department_breakdown(token, start_date, end_date)
        if departments and departments['departments']:
            st.subheader("Department Breakdown")
            dept_df = pd.DataFrame(departments['departments'])
            
            col1, col2 = st.columns([3, 2])
            
            with col1:
                # Department interview counts
                fig = px.bar(
                    dept_df,
                    x='department',
                    y='interview_count',
                    labels={'department': 'Department', 'interview_count': 'Exit Interviews'},
                    title='Exit Interviews by Department'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Department sentiment
                if 'sentiment_score' in dept_df.columns:
                    # Create a sentiment gauge for each department
                    for i, row in dept_df.iterrows():
                        dept = row['department']
                        sentiment = row['sentiment_score'] if row['sentiment_score'] is not None else 0
                        
                        fig = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=sentiment,
                            domain={'x': [0, 1], 'y': [0, 1]},
                            title={'text': f"{dept} Sentiment"},
                            gauge={
                                'axis': {'range': [-1, 1]},
                                'bar': {'color': "darkblue"},
                                'steps': [
                                    {'range': [-1, -0.5], 'color': "red"},
                                    {'range': [-0.5, 0], 'color': "orange"},
                                    {'range': [0, 0.5], 'color': "lightgreen"},
                                    {'range': [0.5, 1], 'color': "green"}
                                ],
                            }
                        ))
                        fig.update_layout(height=200)
                        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Could not load dashboard data. Please check your connection.")

def render_interviews_tab(token):
    """Render interviews list and details tab"""
    st.title("Exit Interviews")
    
    # Interview listing
    interviews = get_all_interviews(token)
    
    if interviews:
        # Convert to DataFrame for display
        interviews_df = pd.DataFrame(interviews)
        
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
        
        interview = get_interview_details(token, st.session_state.selected_interview)
        
        if interview:
            # Employee info
            st.write(f"**Status:** {interview['status']}")
            st.write(f"**Employee ID:** {interview['employee_id']}")
            st.write(f"**Date:** {interview['created_at']}")
            
            # Summary section
            with st.expander("Interview Summary", expanded=True):
                summary = get_interview_summary(token, st.session_state.selected_interview)
                st.markdown(summary)
            
            # Responses
            if 'responses' in interview and interview['responses']:
                st.write("### Responses")
                
                for i, response in enumerate(interview['responses']):
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
            st.warning("Could not load interview details.")

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
        stats = get_summary_stats(token, report_start_date, report_end_date)
        
        if stats:
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
            st.warning("Could not load statistics for the selected period.")
            
    elif report_tab == "Department Analysis":
        departments = get_department_breakdown(token, report_start_date, report_end_date)
        
        if departments and departments['departments']:
            st.write("### Department Analysis")
            st.write(f"Period: {report_start_date} to {report_end_date}")
            
            dept_df = pd.DataFrame(departments['departments'])
            
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
            st.warning("Could not load department data for the selected period.")
            
    elif report_tab == "Export Data":
        st.write("### Export Exit Interview Data")
        
        # Export settings
        export_format = st.selectbox("Export format", ["JSON", "CSV"], index=0)
        department_filter = st.text_input("Filter by department (optional)")
        
        if st.button("Generate Export"):
            with st.spinner("Generating export..."):
                data = export_data(
                    token,
                    format=export_format.lower(),
                    start_date=report_start_date,
                    end_date=report_end_date,
                    department=department_filter if department_filter else None
                )
                
                if data:
                    # Convert to appropriate format
                    if export_format == "JSON":
                        export_str = json.dumps(data, indent=2)
                        mime = "application/json"
                        file_ext = "json"
                    else:  # CSV
                        # Flatten the data for CSV export
                        flat_data = []
                        for interview in data:
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
                    st.error("Failed to generate export data.")

def render_settings_tab(token):
    """Render settings and configuration tab"""
    st.title("Settings")
    
    st.write("### System Configuration")
    
    # Display system info (placeholder for future settings)
    st.info("This section will allow customization of the ExitBot configuration.")
    
    # TODO: Add settings for:
    # - Question management
    # - User management
    # - System preferences
    
    st.write("### About ExitBot")
    st.write("""
    ExitBot is an HR exit interview bot that conducts structured exit interviews with departing employees,
    collects feedback, and generates reports for HR using Ollama for local LLM inference.
    
    Version: 0.1.0
    """)

# Main App Logic
def main():
    if not st.session_state.token:
        render_login()
    else:
        render_dashboard(st.session_state.token)

if __name__ == "__main__":
    main() 
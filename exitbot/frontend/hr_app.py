import json
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime, timedelta, date
import extra_streamlit_components as stx  # Import for cookie manager
import logging  # Move logging import down
import random
import time

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
    get_questions,  # <-- Import new question functions
    create_question,
    update_question,
    delete_question,
    get_system_config,  # <-- Import new config functions
    update_system_config,
    get_user_profile,
)

# Import design system and components
from exitbot.frontend.components.design_system import get_base_css, get_hr_app_css
from exitbot.frontend.components.login import render_login
from exitbot.frontend.components.dashboard_cards import (
    render_metric_card,
    render_interview_completion_chart,
    render_time_series_chart,
    render_department_breakdown,
    render_sentiment_gauge
)

# Initialize Cookie Manager - key should be unique for the app
# Using double underscore might help avoid clashes if deploying multiple apps
cookies = stx.CookieManager(key="__hr_app_cookie_manager")

# Apply custom styling from the design system
st.markdown(
    get_base_css() + get_hr_app_css(),
    unsafe_allow_html=True,
)

# Initialize session state
if "token" not in st.session_state:
    st.session_state.token = None  # Default if no cookie either
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Dashboard"
if "selected_interview" not in st.session_state:
    st.session_state.selected_interview = None
if "date_range" not in st.session_state:
    st.session_state.date_range = (
        (datetime.now() - timedelta(days=30)).date(),
        datetime.now().date(),
    )


# --- Helper Functions ---
def display_api_error(error_details, context="Error"):
    """Display API error messages using Streamlit components."""
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


# --- UI Components ---
def render_dashboard(token):
    """Render main dashboard wrapper with date selector"""
    # Add more prominent header with better visual hierarchy
    st.markdown(
        """
        <div class="dashboard-header">
            <h1>ExitBot Dashboard</h1>
            <div class="dashboard-subtitle">
                Monitor your exit interviews, analyze trends, and gain valuable insights.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Date filter in the sidebar
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-header">
                <h3>📅 Date Range Filter</h3>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Store date range in session state so it persists
        date_range = st.date_input(
            "Select date range",
            value=st.session_state.date_range,
            min_value=date(2020, 1, 1),
            max_value=datetime.now().date(),
        )
        
        # Handle the case when a single date is selected
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            st.session_state.date_range = (start_date, end_date)
        else:
            # If only one date selected, use it for both start and end
            st.session_state.date_range = (date_range, date_range)
            start_date, end_date = date_range, date_range
        
        # Add quick date presets for better UX
        st.markdown("### Quick Select")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Last 30 days", use_container_width=True):
                end = datetime.now().date()
                start = end - timedelta(days=30)
                st.session_state.date_range = (start, end)
                st.rerun()
        with col2:
            if st.button("Last 90 days", use_container_width=True):
                end = datetime.now().date()
                start = end - timedelta(days=90)
                st.session_state.date_range = (start, end)
                st.rerun()

    # Render the dashboard tab with the selected date range
    render_dashboard_tab(token, start_date, end_date)


def render_dashboard_tab(token, start_date, end_date):
    """Render dashboard content with summary cards and visualizations"""
    
    # Format dates for API
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    # Get summary stats from API
    stats, error = get_summary_stats(token, start_str, end_str)
    
    if error:
        # Show a friendly empty state instead of an error
        st.markdown(
            """
            <div class="dashboard-empty-state">
                <div class="empty-state-icon">📊</div>
                <h2>Welcome to Your Dashboard</h2>
                <p>It looks like we couldn't load your dashboard data right now. This might be because:</p>
                <ul>
                    <li>The server is still starting up</li>
                    <li>There are no exit interviews in the selected date range</li>
                    <li>Your connection to the data service was interrupted</li>
                </ul>
                <div class="empty-state-action">
                    <p>You can try adjusting the date range or refreshing the page.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Add a refresh button
        if st.button("Refresh Dashboard", use_container_width=True):
            st.rerun()
        return

    # Safely extract values with defaults
    interviews_total = stats.get("interviews_total", 0)
    interviews_complete = stats.get("interviews_complete", 0)
    interviews_incomplete = stats.get("interviews_incomplete", 0)
    avg_sentiment = stats.get("avg_sentiment", 0)
    top_categories = stats.get("top_categories", [])
    
    # Top row stats with enhanced styling
    st.markdown("<div class='metrics-row'>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_metric_card(
            title="Total Interviews",
            value=interviews_total,
            help_text="Total number of exit interviews initiated in the selected period"
        )

    with col2:
        completion_rate = 0
        if interviews_total > 0:
            completion_rate = round((interviews_complete / interviews_total) * 100)
        
        render_metric_card(
            title="Completion Rate",
            value=f"{completion_rate}%",
            help_text="Percentage of interviews that were completed"
        )

    with col3:
        sentiment_display = f"{avg_sentiment:.2f}"
        sentiment_indicator = ""
        if avg_sentiment >= 0.3:
            sentiment_indicator = "😊"  # Positive
        elif avg_sentiment <= -0.3:
            sentiment_indicator = "😞"  # Negative
        else:
            sentiment_indicator = "😐"  # Neutral
            
        render_metric_card(
            title="Average Sentiment",
            value=sentiment_display,
            icon=sentiment_indicator,
            help_text="Average sentiment score across all interviews (-1 to +1)"
        )

    with col4:
        prev_start = start_date - timedelta(days=30)
        prev_end = end_date - timedelta(days=30)
        prev_start_str = prev_start.strftime("%Y-%m-%d")
        prev_end_str = prev_end.strftime("%Y-%m-%d")
        
        prev_stats, prev_error = get_summary_stats(token, prev_start_str, prev_end_str)
        
        if not prev_error:
            prev_total = prev_stats.get("interviews_total", 0)
            delta = interviews_total - prev_total
            
            render_metric_card(
                title="Monthly Change",
                value=f"{interviews_total}",
                delta=delta,
                delta_suffix="vs previous 30 days",
                help_text="Change in number of interviews compared to previous 30-day period"
            )
        else:
            render_metric_card(
                title="Monthly Change", 
                value="N/A",
                help_text="Unable to calculate comparison with previous period"
            )
    st.markdown("</div>", unsafe_allow_html=True)

    # Second row - visualizations
    st.markdown("### Interview Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Completion Status")
        # Use our enhanced donut chart
        render_interview_completion_chart(
            interviews_complete,
            interviews_incomplete,
            interviews_total
        )

    with col2:
        st.markdown("#### Overall Sentiment")
        # Use our enhanced sentiment gauge
        render_sentiment_gauge(avg_sentiment)

    # Third row - Category breakdown and department data
    st.markdown("### Detailed Breakdown")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top reasons/categories
        st.markdown("#### Top Exit Reasons")
        
        if top_categories:
            # Convert categories to DataFrame for visualization
            categories_df = pd.DataFrame(top_categories)
            
            # Create horizontal bar chart
            fig = px.bar(
                categories_df,
                y="category",
                x="count",
                orientation="h",
                title="",
                text="count"
            )
            
            # Update styling
            fig.update_traces(
                marker_color="#3B82F6",
                textposition="outside",
            )
            
            fig.update_layout(
                font=dict(family="Inter, sans-serif"),
                xaxis=dict(title=None),
                yaxis=dict(title=None, categoryorder="total ascending"),
                margin=dict(l=0, r=10, t=0, b=0),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No category data available for the selected period.")

    with col2:
        # Department breakdown
        st.markdown("#### Interviews by Department")
        
        # Get department data from API
        departments, dept_error = get_department_breakdown(token, start_str, end_str)
        
        if dept_error:
            display_api_error(dept_error, "Failed to load department data")
        elif departments:
            # Convert to DataFrame
            departments_df = pd.DataFrame(departments)
            
            # Use our enhanced department breakdown chart
            render_department_breakdown(departments_df)
        else:
            st.info("No department data available for the selected period.")


def render_interviews_tab(token):
    """Render interviews list with filtering and details view"""
    st.header("Exit Interviews", anchor=False)
    st.markdown(
        """
        <div class="dashboard-header-description">
            Browse, filter, and review all exit interviews.
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Get all interviews
    interviews, error = get_all_interviews(token)
    
    if error:
        # Enhanced error handling with actionable guidance
        st.markdown(
            f"""
            <div class="error-container">
                <div class="error-icon">⚠️</div>
                <div class="error-content">
                    <h3>Unable to load interviews</h3>
                    <p>We couldn't retrieve the interview data. This may be due to:</p>
                    <ul>
                        <li>The server is temporarily unavailable</li>
                        <li>Your connection to the server was interrupted</li>
                        <li>You may need to refresh your session token</li>
                    </ul>
                    <p class="error-action">Try refreshing the page or contact your system administrator if the problem persists.</p>
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Add a refresh button for easy recovery
        if st.button("Refresh Data", use_container_width=True):
            st.rerun()
        return

    # Show list of interviews in left column, details in right
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Interview List")
        
        # Enhanced filter controls with better organization
        with st.expander("Filter Interviews", expanded=True):
            # Add search by name with instant filtering
            search_query = st.text_input(
                "Search by Name or ID", 
                value=st.session_state.get("interview_search", ""),
                placeholder="Type to search...",
                help="Search by employee name or interview ID"
            )
            
            # Save search in session state for persistence
            if "interview_search" not in st.session_state or st.session_state.interview_search != search_query:
                st.session_state.interview_search = search_query
            
            # Create tabs for different filter categories
            filter_tab1, filter_tab2 = st.tabs(["Basic Filters", "Advanced Filters"])
            
            with filter_tab1:
                # Status filter with visual indicators
                status_options = ["All", "Complete", "In Progress"]
                status_icons = ["🔍", "✅", "⏳"]
                
                status_filter = st.selectbox(
                    "Status", 
                    options=status_options,
                    format_func=lambda x: f"{status_icons[status_options.index(x)]} {x}",
                    index=0
                )
                
                # Department filter
                if interviews:
                    departments = sorted(list(set([i.get("department", "Unknown") for i in interviews if i.get("department")])))
                    departments.insert(0, "All Departments")
                else:
                    departments = ["All Departments"]
                    
                dept_filter = st.selectbox(
                    "Department", 
                    departments, 
                    index=0
                )
                
                # Date range filter with presets
                date_col1, date_col2 = st.columns(2)
                
                with date_col1:
                    if st.button("Last 30 days", use_container_width=True):
                        end_date = datetime.now().date()
                        start_date = end_date - timedelta(days=30)
                        st.session_state.interview_date_filter = (start_date, end_date)
                        st.rerun()
                        
                with date_col2:
                    if st.button("Last 90 days", use_container_width=True):
                        end = datetime.now().date()
                        start = end - timedelta(days=90)
                        st.session_state.date_range = (start, end)
                        st.rerun()
                
                # Use stored date filter or create default
                if "interview_date_filter" not in st.session_state:
                    st.session_state.interview_date_filter = (
                        datetime.now() - timedelta(days=90),
                        datetime.now()
                    )
                    
                date_filter = st.date_input(
                    "Custom Date Range",
                    value=st.session_state.interview_date_filter
                )
                
                if isinstance(date_filter, tuple) and len(date_filter) == 2:
                    start_date, end_date = date_filter
                    st.session_state.interview_date_filter = (start_date, end_date)
                else:
                    start_date = end_date = date_filter
                    st.session_state.interview_date_filter = (date_filter, date_filter)
            
            with filter_tab2:
                if interviews:
                    managers = sorted(list(set([i.get("manager", "Unknown") for i in interviews if i.get("manager")])))
                    managers.insert(0, "All Managers")
                else:
                    managers = ["All Managers"]
                
                manager_filter = st.selectbox(
                    "Manager", 
                    managers, 
                    index=0
                )
                
                # Sentiment filter with slider
                sentiment_filter = st.slider(
                    "Sentiment Score",
                    min_value=-1.0,
                    max_value=1.0,
                    value=(-1.0, 1.0),
                    step=0.1,
                    help="Filter by sentiment score range"
                )
                
                # Employee tenure filter
                tenure_options = ["Any Tenure", "Less than 1 year", "1-2 years", "2-5 years", "5+ years"]
                tenure_filter = st.selectbox(
                    "Employee Tenure", 
                    tenure_options, 
                    index=0
                )
                
                # Sort options
                sort_options = ["Newest First", "Oldest First", "Name (A-Z)", "Name (Z-A)", "Sentiment (Highest)", "Sentiment (Lowest)"]
                sort_by = st.selectbox(
                    "Sort By",
                    sort_options,
                    index=0
                )
        
        # Add reset filters button
        if st.button("Reset All Filters", use_container_width=True):
            # Clear all filter session state
            for key in list(st.session_state.keys()):
                if key.startswith("interview_"):
                    del st.session_state[key]
            st.rerun()
        
        # Apply all filters
        filtered_interviews = []
        
        for interview in interviews:
            # Status filter
            if status_filter != "All":
                is_complete = interview.get("is_complete", False)
                if (status_filter == "Complete" and not is_complete) or \
                   (status_filter == "In Progress" and is_complete):
                    continue
            
            # Department filter
            if dept_filter != "All Departments" and interview.get("department") != dept_filter:
                continue
            
            # Manager filter (advanced)
            if manager_filter != "All Managers" and interview.get("manager") != manager_filter:
                continue
            
            # Date filter
            if isinstance(date_filter, tuple) and len(date_filter) == 2:
                start_date, end_date = date_filter
                interview_date = datetime.strptime(interview.get("created_at", ""), "%Y-%m-%dT%H:%M:%S").date()
                if not (start_date <= interview_date <= end_date):
                    continue
            
            # Sentiment filter
            sentiment = interview.get("sentiment", 0)
            if not (sentiment_filter[0] <= sentiment <= sentiment_filter[1]):
                continue
            
            # Tenure filter
            if tenure_filter != "Any Tenure":
                tenure = interview.get("tenure", 0)
                if tenure_filter == "Less than 1 year" and tenure >= 1:
                    continue
                elif tenure_filter == "1-2 years" and (tenure < 1 or tenure >= 2):
                    continue
                elif tenure_filter == "2-5 years" and (tenure < 2 or tenure >= 5):
                    continue
                elif tenure_filter == "5+ years" and tenure < 5:
                    continue
            
            # Search filter
            if search_query:
                search_terms = search_query.lower().split()
                employee_name = interview.get("employee_name", "").lower()
                interview_id = str(interview.get("id", "")).lower()
                if search_query.lower() not in employee_name and search_query.lower() not in interview_id:
                    continue
            
            # If passes all filters, add to filtered list
            filtered_interviews.append(interview)
        
        # Apply sorting
        if "sort_by" in locals():
            if sort_by == "Newest First":
                filtered_interviews.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            elif sort_by == "Oldest First":
                filtered_interviews.sort(key=lambda x: x.get("created_at", ""))
            elif sort_by == "Name (A-Z)":
                filtered_interviews.sort(key=lambda x: x.get("employee_name", "").lower())
            elif sort_by == "Name (Z-A)":
                filtered_interviews.sort(key=lambda x: x.get("employee_name", "").lower(), reverse=True)
            elif sort_by == "Sentiment (Highest)":
                filtered_interviews.sort(key=lambda x: x.get("sentiment", 0), reverse=True)
            elif sort_by == "Sentiment (Lowest)":
                filtered_interviews.sort(key=lambda x: x.get("sentiment", 0))
        
        # Show number of results with better styling
        st.markdown(
            f"""
            <div class="filter-results">
                Found <span class="result-count">{len(filtered_interviews)}</span> interviews
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Add pagination for large result sets
        interviews_per_page = 10
        total_pages = max(1, (len(filtered_interviews) + interviews_per_page - 1) // interviews_per_page)
        
        # Initialize current page in session state if not present
        if "interview_page" not in st.session_state:
            st.session_state.interview_page = 1
            
        # Reset page if no results
        if len(filtered_interviews) == 0:
            st.session_state.interview_page = 1
        
        # Ensure current page is valid
        current_page = min(total_pages, st.session_state.interview_page)
        
        # Show pagination controls if needed
        if total_pages > 1:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.button("← Previous", disabled=current_page == 1):
                    st.session_state.interview_page = max(1, current_page - 1)
                    st.rerun()
            
            with col2:
                st.markdown(
                    f"""
                    <div class="pagination-info">
                        Page {current_page} of {total_pages}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            with col3:
                if st.button("Next →", disabled=current_page == total_pages):
                    st.session_state.interview_page = min(total_pages, current_page + 1)
                    st.rerun()
        
        # Calculate slice for current page
        start_idx = (current_page - 1) * interviews_per_page
        end_idx = min(start_idx + interviews_per_page, len(filtered_interviews))
        page_interviews = filtered_interviews[start_idx:end_idx]
        
        if len(filtered_interviews) == 0:
            st.info("No interviews match the current filters. Try adjusting your search criteria.")
        else:
            for idx, interview in enumerate(page_interviews):
                interview_id = interview.get("id")
                employee_name = interview.get("employee_name", "Unknown")
                department = interview.get("department", "Unknown")
                position = interview.get("position", "Unknown")
                created_at = interview.get("created_at", "Unknown date")
                is_complete = interview.get("is_complete", False)
                sentiment = interview.get("sentiment", 0)
                
                try:
                    date_obj = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S")
                    formatted_date = date_obj.strftime("%b %d, %Y")
                except:
                    formatted_date = created_at
                
                status_color = "#10B981" if is_complete else "#F59E0B"
                status_text = "Complete" if is_complete else "In Progress"
                sentiment_icon = "😊" if sentiment >= 0.3 else "😐" if sentiment >= -0.3 else "😞"
                
                st.markdown(
                    f"""
                    <div class="interview-card" id="interview-{interview_id}">
                        <div class="interview-header">
                            <div class="interview-name">{employee_name}</div>
                            <div class="interview-status" style="background-color: {status_color};">
                                {status_text}
                            </div>
                        </div>
                        <div class="interview-meta">
                            <div class="interview-details">
                                <div class="department-position">{department} · {position}</div>
                                <div class="interview-date">
                                    <span class="date-icon">📅</span> {formatted_date}
                                </div>
                            </div>
                            <div class="interview-sentiment">{sentiment_icon}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Check if this is the selected interview
                is_selected = st.session_state.selected_interview == interview_id
                
                # Use a button that looks like a card
                if st.button(
                    f"View details for {employee_name}",
                    key=f"interview_{interview_id}",
                    help=f"Click to view details for {employee_name}'s exit interview",
                    use_container_width=True,
                    # Add styling based on selection state
                    type="primary" if is_selected else "secondary"
                ):
                    st.session_state.selected_interview = interview_id
                    st.rerun()  # Force rerun to update the selection
                    
            # Show pagination controls at bottom if needed
            if total_pages > 1:
                st.markdown("<div class='pagination-bottom'>", unsafe_allow_html=True)
                cols = st.columns(total_pages + 2)
                
                with cols[0]:
                    if st.button("«", disabled=current_page == 1, key="first_page"):
                        st.session_state.interview_page = 1
                        st.rerun()
                
                for i in range(1, total_pages + 1):
                    with cols[i]:
                        # Show current page as highlighted
                        if st.button(
                            str(i),
                            type="primary" if i == current_page else "secondary",
                            key=f"page_{i}"
                        ):
                            st.session_state.interview_page = i
                            st.rerun()
                
                with cols[-1]:
                    if st.button("»", disabled=current_page == total_pages, key="last_page"):
                        st.session_state.interview_page = total_pages
                        st.rerun()
                        
                st.markdown("</div>", unsafe_allow_html=True)

    # Right column - interview details
    with col2:
        selected_id = st.session_state.selected_interview
        
        if selected_id:
            # Find the selected interview
            selected_interview = next(
                (i for i in interviews if i.get("id") == selected_id), None
            )
            
            if selected_interview:
                # Get full interview details with summary
                details, error = get_interview_details(token, selected_id)
                summary, summary_error = get_interview_summary(token, selected_id)
                
                if error:
                    display_api_error(error, "Failed to load interview details")
                elif details:
                    employee_name = details.get("employee_name", "Unknown")
                    
                    st.markdown(f"### Interview Details: {employee_name}")
                    
                    # Create tabs for different sections of the interview
                    details_tab, summary_tab, raw_tab = st.tabs(
                        ["Profile", "Summary", "Raw Transcript"]
                    )
                    
                    with details_tab:
                        # Personal information section
                        st.markdown("#### Employee Profile")
                        
                        profile_cols = st.columns(3)
                        
                        with profile_cols[0]:
                            st.markdown("**Department**")
                            st.markdown(details.get("department", "Not specified"))
                            
                            st.markdown("**Position**")
                            st.markdown(details.get("position", "Not specified"))
                        
                        with profile_cols[1]:
                            st.markdown("**Employment Start**")
                            st.markdown(details.get("start_date", "Not specified"))
                            
                            st.markdown("**Employment End**")
                            st.markdown(details.get("end_date", "Not specified"))
                        
                        with profile_cols[2]:
                            st.markdown("**Manager**")
                            st.markdown(details.get("manager", "Not specified"))
                            
                            st.markdown("**Status**")
                            is_complete = details.get("is_complete", False)
                            status_text = "Complete" if is_complete else "In Progress"
                            status_color = "#10B981" if is_complete else "#F59E0B"
                            st.markdown(
                                f'<span style="color: {status_color}; font-weight: bold;">{status_text}</span>',
                                unsafe_allow_html=True
                            )
                        
                        # Interview metadata
                        st.markdown("#### Interview Details")
                        
                        meta_cols = st.columns(3)
                        
                        with meta_cols[0]:
                            st.markdown("**Interview Date**")
                            created_at = details.get("created_at", "Unknown")
                            try:
                                date_obj = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S")
                                formatted_date = date_obj.strftime("%B %d, %Y at %I:%M %p")
                                st.markdown(formatted_date)
                            except:
                                st.markdown(created_at)
                        
                        with meta_cols[1]:
                            st.markdown("**Last Updated**")
                            updated_at = details.get("updated_at", "Unknown")
                            try:
                                date_obj = datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%S")
                                formatted_date = date_obj.strftime("%B %d, %Y at %I:%M %p")
                                st.markdown(formatted_date)
                            except:
                                st.markdown(updated_at)
                        
                        with meta_cols[2]:
                            st.markdown("**Interview ID**")
                            st.markdown(f"`{selected_id}`")
                    
                    with summary_tab:
                        if summary_error:
                            display_api_error(summary_error, "Failed to load interview summary")
                        elif summary:
                            # Display sentiment score with visualization
                            sentiment_score = summary.get("sentiment", 0)
                            
                            st.markdown("#### Overall Sentiment")
                            render_sentiment_gauge(sentiment_score)
                            
                            # Key themes section
                            st.markdown("#### Key Themes")
                            themes = summary.get("themes", [])
                            
                            for theme in themes:
                                st.markdown(f"* {theme}")
                            
                            # Primary reasons section
                            st.markdown("#### Primary Reasons for Leaving")
                            reasons = summary.get("reasons", [])
                            
                            for reason in reasons:
                                st.markdown(f"* {reason}")
                            
                            # Feedback sections
                            st.markdown("#### Positive Feedback")
                            positives = summary.get("positives", [])
                            
                            for positive in positives:
                                st.markdown(f"* {positive}")
                            
                            st.markdown("#### Improvement Areas")
                            improvements = summary.get("improvements", [])
                            
                            for improvement in improvements:
                                st.markdown(f"* {improvement}")
                            
                            # Overall summary
                            st.markdown("#### Summary")
                            st.markdown(summary.get("summary", "No summary available."))
                        else:
                            # If no summary is available yet
                            if details.get("is_complete"):
                                st.info("Summary is being generated. Please check back later.")
                            else:
                                st.warning("This interview is not complete. Summary will be available once the interview is finished.")
                    
                    with raw_tab:
                        # Display raw conversation
                        st.markdown("#### Interview Transcript")
                        
                        messages = details.get("messages", [])
                        
                        if messages:
                            for message in messages:
                                role = message.get("role", "unknown")
                                content = message.get("content", "")
                                
                                if role == "assistant":
                                    st.markdown(
                                        f'<div class="message bot-message"><div class="message-content">{content}</div></div>',
                                        unsafe_allow_html=True
                                    )
                                elif role == "user":
                            st.markdown(
                                        f'<div class="message user-message"><div class="message-content">{content}</div></div>',
                                        unsafe_allow_html=True
                            )
            else:
                            st.info("No transcript available yet.")
        else:
                    st.warning("Failed to load interview details. The interview may have been deleted.")
            else:
                st.info("Interview not found. It may have been deleted.")
        else:
            # No interview selected yet
            st.info("Select an interview from the list to view details.")


def render_reports_tab(token, start_date, end_date):
    """Render reports and data export tab"""
    st.markdown(
        """
        <div class="reports-header">
            <h1>Reports & Analytics</h1>
            <div class="reports-description">
                Analyze exit interview data, discover trends, and export insights
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Date range for reports with better styling
    st.markdown(
        """
        <div class="report-date-selector">
            <div class="selector-label">Select Date Range for Analysis</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    date_col1, date_col2, date_col3 = st.columns([2, 2, 1])
    
    with date_col1:
        report_start_date = st.date_input("From", value=start_date)
    
    with date_col2:
        report_end_date = st.date_input("To", value=end_date)
    
    with date_col3:
        st.markdown("<div style='padding-top: 31px;'>", unsafe_allow_html=True)
        if st.button("Apply", use_container_width=True):
            st.session_state.report_date_range = (report_start_date, report_end_date)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Report tabs with enhanced styling
    st.markdown("<br>", unsafe_allow_html=True)
    report_tabs = st.tabs([
        "📊 Summary Statistics",
        "🏢 Department Analysis", 
        "📈 Trend Analysis",
        "💾 Export Data"
    ])
    
    with report_tabs[0]:  # Summary Statistics
        st.markdown("<div class='report-section'>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="report-title">
                <h2>Exit Interview Statistics</h2>
                <div class="report-subtitle">Key metrics from exit interviews during selected period</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Show loading animation while fetching data
        with st.spinner("Loading statistics..."):
            stats, error = get_summary_stats(token, report_start_date, report_end_date)
            
            if error:
                display_api_error(error, "Could not load summary statistics")
            elif stats:
                # Format date range for display
                formatted_start = report_start_date.strftime("%b %d, %Y")
                formatted_end = report_end_date.strftime("%b %d, %Y")
                
                st.markdown(
                    f"""
                    <div class="date-range-display">
                        <span class="date-icon">📅</span> {formatted_start} to {formatted_end}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Enhanced metric display with cards
                metric_cols = st.columns(4)
                
                with metric_cols[0]:
                    render_metric_card(
                        title="Total Interviews",
                        value=stats.get("total_interviews", 0),
                        help_text="Number of exit interviews conducted"
                    )
                
                with metric_cols[1]:
                    completion_rate = 0
                    if stats.get("total_interviews", 0) > 0:
                        completion_rate = int((stats.get("completed_interviews", 0) / stats.get("total_interviews", 1)) * 100)
                    
                    render_metric_card(
                        title="Completion Rate",
                        value=f"{completion_rate}%",
                        help_text="Percentage of interviews completed"
                    )
                
                with metric_cols[2]:
                    avg_sentiment = stats.get("average_sentiment", 0)
                    sentiment_icon = "😊" if avg_sentiment >= 0.3 else "😐" if avg_sentiment >= -0.3 else "😞"
                    
                    render_metric_card(
                        title="Avg Sentiment",
                        value=f"{avg_sentiment:.2f}",
                        icon=sentiment_icon,
                        help_text="Average sentiment score (-1 to +1)"
                    )
                
                with metric_cols[3]:
                    render_metric_card(
                        title="Avg Duration",
                        value=stats.get("average_duration", "15m"),
                        help_text="Average time to complete interview"
                    )
                
                # Interpret sentiment with enhanced styling
                st.markdown("<br>", unsafe_allow_html=True)
                if stats.get("average_sentiment") is not None:
                    sentiment_val = float(stats.get("average_sentiment"))
                    
                    if sentiment_val < -0.3:
                        st.markdown(
                            """
                            <div class="sentiment-insight negative">
                                <div class="insight-icon">⚠️</div>
                                <div class="insight-content">
                                    <div class="insight-title">Negative Sentiment Detected</div>
                                    <div class="insight-text">Overall negative sentiment detected. Consider reviewing interview details to identify potential issues that may need addressing.</div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    elif sentiment_val < 0.3:
                        st.markdown(
                            """
                            <div class="sentiment-insight neutral">
                                <div class="insight-icon">ℹ️</div>
                                <div class="insight-content">
                                    <div class="insight-title">Neutral Sentiment</div>
                                    <div class="insight-text">Overall neutral sentiment detected. Consider exploring specific areas where improvements could be made.</div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            """
                            <div class="sentiment-insight positive">
                                <div class="insight-icon">✅</div>
                                <div class="insight-content">
                                    <div class="insight-title">Positive Sentiment Detected</div>
                                    <div class="insight-text">Overall positive sentiment detected. Continue to build on current strengths while addressing any specific improvement areas.</div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                
                # Exit reasons visualization with enhanced styling
                if stats.get("top_exit_reasons"):
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("<h3>Top Reasons for Leaving</h3>", unsafe_allow_html=True)
                    
                    reasons_df = pd.DataFrame(stats.get("top_exit_reasons"))
                    
                    # Use a more visually appealing chart
                    fig = px.pie(
                        reasons_df,
                        values="count",
                        names="reason",
                        color_discrete_sequence=px.colors.sequential.Blues_r,
                        hole=0.4
                    )
                    
                    fig.update_layout(
                        font=dict(family="Inter, sans-serif", size=14),
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=-0.2,
                            xanchor="center",
                            x=0.5
                        ),
                        margin=dict(l=20, r=20, t=40, b=20),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        height=400
                    )
                    
                    fig.update_traces(
                        textposition='inside',
                        textinfo='percent+label',
                        hovertemplate='%{label}<br>Count: %{value}<br>Percentage: %{percent}'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                    
                    # Additional insights based on top reasons
                    top_reason = reasons_df.iloc[0]["reason"] if not reasons_df.empty else None
                    if top_reason:
                        st.markdown(
                            f"""
                            <div class="insight-box">
                                <div class="insight-title">Key Insight</div>
                                <div class="insight-text">The most common reason for departure is <strong>"{top_reason}"</strong>. Consider focusing improvement efforts in this area.</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
        else:
            st.warning("No statistics data available for the selected period.")

        st.markdown("</div>", unsafe_allow_html=True)

    with report_tabs[1]:  # Department Analysis
        st.markdown("<div class='report-section'>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="report-title">
                <h2>Department Analysis</h2>
                <div class="report-subtitle">Compare exit interview metrics across departments</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Show loading animation
        with st.spinner("Loading department data..."):
        departments_data, error = get_department_breakdown(
            token, report_start_date, report_end_date
        )
        
        if error:
            display_api_error(error, "Could not load department analysis")
        elif departments_data and departments_data.get("departments"):
            # Format date range for display
            formatted_start = report_start_date.strftime("%b %d, %Y")
            formatted_end = report_end_date.strftime("%b %d, %Y")
            
            st.markdown(
                f"""
                <div class="date-range-display">
                    <span class="date-icon">📅</span> {formatted_start} to {formatted_end}
                </div>
                """,
                unsafe_allow_html=True
            )

            dept_df = pd.DataFrame(departments_data["departments"])

            # Enhanced department interview counts chart
            st.markdown("<h3>Exit Interviews by Department</h3>", unsafe_allow_html=True)
            
            fig_counts = px.bar(
                dept_df,
                x="department",
                y="interview_count",
                labels={
                    "department": "Department",
                    "interview_count": "Exit Interviews",
                },
                color="interview_count",
                color_continuous_scale="Blues",
                text="interview_count"
            )
            
            fig_counts.update_layout(
                font=dict(family="Inter, sans-serif"),
                xaxis=dict(title=None, tickangle=-45),
                yaxis=dict(title="Number of Interviews"),
                coloraxis_showscale=False,
                margin=dict(l=20, r=20, t=40, b=100),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            
            fig_counts.update_traces(
                textposition='outside',
                texttemplate='%{text}',
                marker_line_color='#E5E7EB',
                marker_line_width=1
            )
            
            st.plotly_chart(fig_counts, use_container_width=True)
            
            # Department sentiment comparison with enhanced styling
            if "sentiment_score" in dept_df.columns:
                sentiment_df = dept_df.dropna(subset=["sentiment_score"])
                if not sentiment_df.empty:
                    st.markdown("<h3>Sentiment Analysis by Department</h3>", unsafe_allow_html=True)
                    
                    # Create a more visually appealing horizontal bar chart
                    fig = px.bar(
                        sentiment_df,
                        x="sentiment_score",
                        y="department",
                        labels={
                            "department": "Department",
                            "sentiment_score": "Sentiment Score",
                        },
                        orientation='h',
                        color="sentiment_score",
                        color_continuous_scale=["#EF4444", "#FCD34D", "#10B981"],
                        range_color=[-1, 1],
                        text="sentiment_score"
                    )
                    
                    fig.update_layout(
                        font=dict(family="Inter, sans-serif"),
                        xaxis=dict(
                            title="Sentiment Score",
                            tickvals=[-1, -0.5, 0, 0.5, 1],
                            ticktext=["Very Negative", "Negative", "Neutral", "Positive", "Very Positive"],
                            range=[-1, 1]
                        ),
                        yaxis=dict(title=None),
                        coloraxis_showscale=False,
                        margin=dict(l=20, r=20, t=40, b=20),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)"
                    )
                    
                    fig.update_traces(
                        texttemplate='%{text:.2f}',
                        textposition='outside',
                        marker_line_color='#E5E7EB',
                        marker_line_width=1
                    )
                    
                    # Add zero line for reference
                    fig.add_shape(
                        type="line",
                        x0=0, x1=0, y0=-0.5, y1=len(sentiment_df)-0.5,
                        line=dict(color="#9CA3AF", width=1, dash="dash")
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)

                    # Findings with enhanced styling
                    st.markdown(
                        """
                        <div class="findings-title">Key Findings</div>
                        """, 
                        unsafe_allow_html=True
                    )
                    
                    finding_cols = st.columns(2)
                    
                    with finding_cols[0]:
                        max_dept = sentiment_df.loc[sentiment_df["sentiment_score"].idxmax()]
                        
                        st.markdown(
                            f"""
                            <div class="finding-card positive">
                                <div class="finding-header">
                                    <span class="finding-icon">🏆</span>
                                    <span class="finding-label">Highest Sentiment</span>
                                </div>
                                <div class="finding-value">{max_dept['department']}</div>
                                <div class="finding-metric">{max_dept['sentiment_score']:.2f}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    
                    with finding_cols[1]:
                        min_dept = sentiment_df.loc[sentiment_df["sentiment_score"].idxmin()]
                        
                        st.markdown(
                            f"""
                            <div class="finding-card negative">
                                <div class="finding-header">
                                    <span class="finding-icon">⚠️</span>
                                    <span class="finding-label">Lowest Sentiment</span>
                                </div>
                                <div class="finding-value">{min_dept['department']}</div>
                                <div class="finding-metric">{min_dept['sentiment_score']:.2f}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                    )

                    if max_dept["sentiment_score"] - min_dept["sentiment_score"] > 0.5:
                        st.markdown(
                            """
                            <div class="insight-alert">
                                <div class="insight-icon">📊</div>
                                <div class="insight-text">
                                    <strong>Significant sentiment variation detected between departments.</strong> 
                                    Consider investigating factors contributing to these differences and sharing best practices from departments with higher sentiment scores.
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
        else:
            st.info("No department data available for the selected period. Try adjusting the date range.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with report_tabs[2]:  # Trend Analysis (New Tab)
        st.markdown("<div class='report-section'>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="report-title">
                <h2>Trend Analysis</h2>
                <div class="report-subtitle">Track changes in exit interview metrics over time</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Time period selector
        period_options = ["Monthly", "Quarterly", "Yearly"]
        time_period = st.selectbox("Analysis Period", period_options, index=0)
        
        # Show sample trend data (in a real app, this would call an API)
        # This is a placeholder for demonstration
        with st.spinner("Loading trend data..."):
            # Simulate API call delay
            time.sleep(0.5)
            
            # Create sample data for demonstration
            if time_period == "Monthly":
                periods = pd.date_range(
                    start=report_start_date, 
                    end=report_end_date, 
                    freq='M'
                ).strftime("%b %Y").tolist()
            elif time_period == "Quarterly":
                periods = pd.date_range(
                    start=report_start_date, 
                    end=report_end_date, 
                    freq='Q'
                ).strftime("Q%q %Y").tolist()
            else:  # Yearly
                periods = pd.date_range(
                    start=report_start_date, 
                    end=report_end_date, 
                    freq='Y'
                ).strftime("%Y").tolist()
            
            # Generate sample data
            if periods:
                # Ensure we have at least one period
                if not periods:
                    periods = ["Current"]
                
                # Sample data for demonstration
                interviews_count = [random.randint(5, 30) for _ in periods]
                sentiment_scores = [round(random.uniform(-0.5, 0.8), 2) for _ in periods]
                
                # Create trends dataframe
                trends_df = pd.DataFrame({
                    "period": periods,
                    "interviews": interviews_count,
                    "sentiment": sentiment_scores
                })
                
                # Display trend charts
                st.markdown("<h3>Exit Interviews Over Time</h3>", unsafe_allow_html=True)
                
                # Line chart for interview count
                fig_count = px.line(
                    trends_df,
                    x="period",
                    y="interviews",
                    markers=True,
                    line_shape="linear",
                    labels={"interviews": "Number of Interviews", "period": "Period"}
                )
                
                fig_count.update_layout(
                    font=dict(family="Inter, sans-serif"),
                    margin=dict(l=20, r=20, t=20, b=20),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    yaxis=dict(gridcolor="#E5E7EB")
                )
                
                fig_count.update_traces(
                    line=dict(color="#3B82F6", width=3),
                    marker=dict(color="#1D4ED8", size=8)
                )
                
                st.plotly_chart(fig_count, use_container_width=True)
                
                # Line chart for sentiment scores
                st.markdown("<h3>Sentiment Trend Over Time</h3>", unsafe_allow_html=True)
                
                fig_sentiment = px.line(
                    trends_df,
                    x="period",
                    y="sentiment",
                    markers=True,
                    line_shape="linear",
                    labels={"sentiment": "Average Sentiment", "period": "Period"}
                )
                
                # Customize the sentiment trend chart
                fig_sentiment.update_layout(
                    font=dict(family="Inter, sans-serif"),
                    margin=dict(l=20, r=20, t=20, b=20),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    yaxis=dict(
                        gridcolor="#E5E7EB",
                        zeroline=True,
                        zerolinecolor="#9CA3AF",
                        zerolinewidth=1
                    )
                )
                
                # Color based on sentiment (positive/negative)
                fig_sentiment.update_traces(
                    line=dict(color="#10B981", width=3),
                    marker=dict(color="#047857", size=8)
                )
                
                # Add a reference line at zero
                fig_sentiment.add_shape(
                    type="line",
                    x0=-0.5, x1=len(periods)-0.5, y0=0, y1=0,
                    line=dict(color="#9CA3AF", width=1, dash="dash")
                )
                
                st.plotly_chart(fig_sentiment, use_container_width=True)
                
                # Trend analysis insights
                if len(periods) > 1:
                    # Check if sentiment is improving
                    is_improving = trends_df["sentiment"].iloc[-1] > trends_df["sentiment"].iloc[0]
                    
                    if is_improving:
                        st.markdown(
                            """
                            <div class="insight-alert positive">
                                <div class="insight-icon">📈</div>
                                <div class="insight-text">
                                    <strong>Positive Trend Detected!</strong> 
                                    Employee sentiment has been improving over time. Continue current initiatives and monitor feedback to maintain this positive trajectory.
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            """
                            <div class="insight-alert negative">
                                <div class="insight-icon">📉</div>
                                <div class="insight-text">
                                    <strong>Concerning Trend Detected.</strong> 
                                    Employee sentiment has declined over this period. Consider reviewing recent organizational changes and exit interview feedback for potential causes.
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
            else:
                st.info("Insufficient data for trend analysis. Please select a wider date range.")
        
        st.markdown("</div>", unsafe_allow_html=True)

    with report_tabs[3]:  # Export Data
        st.markdown("<div class='report-section'>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="report-title">
                <h2>Export Data</h2>
                <div class="report-subtitle">Download exit interview data for further analysis</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Enhanced export options
        export_col1, export_col2 = st.columns(2)
        
        with export_col1:
            st.markdown(
                """
                <div class="export-option-title">Export Format</div>
                """,
                unsafe_allow_html=True
            )
            export_format = st.selectbox(
                "Select format",
                ["JSON", "CSV", "Excel"],
                index=1,
                label_visibility="collapsed"
            )
        
        with export_col2:
            st.markdown(
                """
                <div class="export-option-title">Data Selection</div>
                """,
                unsafe_allow_html=True
            )
            export_data_type = st.selectbox(
                "Select data to export",
                ["Complete Data", "Summary Only", "Raw Responses"],
                label_visibility="collapsed"
            )
        
        # Additional export options
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Additional Filters")
        
        filter_col1, filter_col2 = st.columns(2)
        
        with filter_col1:
            department_filter = st.text_input(
                "Filter by department",
                placeholder="E.g., Engineering, Marketing",
                help="Leave blank to include all departments"
            )
        
        with filter_col2:
            include_options = st.multiselect(
                "Include in export",
                ["Employee Details", "Questions", "Responses", "Sentiment Scores", "HR Notes"],
                default=["Employee Details", "Responses", "Sentiment Scores"]
            )
        
        # Export button with enhanced styling
        st.markdown("<br>", unsafe_allow_html=True)
        export_container = st.container()
        
        with export_container:
            export_cols = st.columns([3, 1])
            
            with export_cols[0]:
                st.markdown(
                    """
                    <div class="export-info">
                        <div class="export-info-icon">ℹ️</div>
                        <div class="export-info-text">
                            Data will be exported for the selected date range and filters.
                            Exports may contain sensitive information. Please handle in accordance with your organization's data policies.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            with export_cols[1]:
                if st.button("Generate Export", use_container_width=True):
                    # Show processing spinner
            with st.spinner("Generating export..."):
                        # Format for API call (lowercase)
                        format_map = {"JSON": "json", "CSV": "csv", "Excel": "excel"}
                        api_format = format_map.get(export_format, "csv")
                        
                        # Call export API
                export_content, error = export_data(
                    token,
                            format=api_format,
                    start_date=report_start_date,
                    end_date=report_end_date,
                    department=department_filter if department_filter else None,
                )

                if error:
                    display_api_error(error, "Failed to generate export data")
                elif export_content:
                    # Convert to appropriate format
                    if export_format == "JSON":
                        export_str = json.dumps(export_content, indent=2)
                        mime = "application/json"
                        file_ext = "json"
                            elif export_format == "Excel":
                                # In a real app, we'd convert to Excel format
                                # For this demo, we'll use CSV format with Excel extension
                                flat_data = []
                                for interview in export_content:
                                    for response in interview.get("responses", []):
                                        flat_data.append(
                                            {
                                                "interview_id": interview["id"],
                                                "employee_id": interview["employee_id"],
                                                "department": interview.get("department"),
                                                "status": interview["status"],
                                                "question": response.get("question"),
                                                "employee_response": response.get(
                                                    "employee_message"
                                                ),
                                                "sentiment": response.get("sentiment"),
                                            }
                                        )
                                
                                export_df = pd.DataFrame(flat_data)
                                export_str = export_df.to_csv(index=False)
                                mime = "application/vnd.ms-excel"
                                file_ext = "xlsx"
                            else:  # CSV (default)
                        flat_data = []
                        for interview in export_content:
                            for response in interview.get("responses", []):
                                flat_data.append(
                                    {
                                        "interview_id": interview["id"],
                                        "employee_id": interview["employee_id"],
                                        "department": interview.get("department"),
                                        "status": interview["status"],
                                        "question": response.get("question"),
                                        "employee_response": response.get(
                                            "employee_message"
                                        ),
                                        "sentiment": response.get("sentiment"),
                                    }
                                )

                        export_df = pd.DataFrame(flat_data)
                        export_str = export_df.to_csv(index=False)
                        mime = "text/csv"
                        file_ext = "csv"

                            # Provide download link with enhanced styling
                    filename = f"exitbot_export_{report_start_date}_{report_end_date}.{file_ext}"
                            
                            st.success("Export generated successfully!")
                            
                    st.download_button(
                        label=f"Download {export_format}",
                        data=export_str,
                        file_name=filename,
                        mime=mime,
                                use_container_width=True
                    )
                else:
                            st.error("Export generation returned no content.")
        
        st.markdown("</div>", unsafe_allow_html=True)


def render_settings_tab(token):
    """Render settings and user preferences tab with improved organization"""
    st.markdown(
        """
        <div class="settings-header">
            <h1>Settings & Preferences</h1>
            <div class="settings-description">
                Configure dashboard preferences and manage your account
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Create tabbed interface for better organization
    settings_tabs = st.tabs([
        "👤 User Profile", 
        "🔔 Notifications", 
        "🔧 System Settings", 
        "🌐 API Configuration"
    ])
    
    with settings_tabs[0]:  # User Profile
        st.markdown(
            """
            <div class="settings-section-title">
                User Profile
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Get the current user profile
        profile, error = get_user_profile(token)
        
                if error:
            display_api_error(error, "Failed to load user profile")
        elif profile:
            # Display current user info
            user_col1, user_col2 = st.columns([1, 3])
            
            with user_col1:
                # User avatar
                st.markdown(
                    f"""
                    <div class="user-avatar">
                        <div class="avatar-circle">
                            {profile.get('name', 'User')[0].upper()}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            with user_col2:
                # User details
                st.markdown(
                    f"""
                    <div class="user-details">
                        <div class="user-name">{profile.get('name', 'User')}</div>
                        <div class="user-email">{profile.get('email', 'user@company.com')}</div>
                        <div class="user-role">{profile.get('role', 'HR Manager')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            # Edit profile form
            st.markdown(
                """
                <div class="settings-card">
                    <div class="settings-card-title">Edit Profile</div>
                """,
                unsafe_allow_html=True
            )
            
            # Create columns for form layout
            form_col1, form_col2 = st.columns(2)
            
            with form_col1:
                name = st.text_input(
                    "Full Name", 
                    value=profile.get('name', ''),
                    placeholder="Your full name"
                )
                
                email = st.text_input(
                    "Email", 
                    value=profile.get('email', ''),
                    placeholder="Your email address"
                )
            
            with form_col2:
                phone = st.text_input(
                    "Phone", 
                    value=profile.get('phone', ''),
                    placeholder="Your phone number"
                )
                
                department = st.text_input(
                    "Department", 
                    value=profile.get('department', ''),
                    placeholder="Your department"
                )
            
            # Save button
            if st.button("Save Profile", use_container_width=True):
                st.success("Profile updated successfully!")
                
                # In a real app, this would call the API to update the profile
                # update_profile(token, name=name, email=email, phone=phone, department=department)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Password change section
            st.markdown(
                """
                <div class="settings-card">
                    <div class="settings-card-title">Change Password</div>
                """,
                unsafe_allow_html=True
            )
            
            current_password = st.text_input(
                "Current Password", 
                type="password",
                placeholder="Enter your current password"
            )
            
            pw_col1, pw_col2 = st.columns(2)
            
            with pw_col1:
                new_password = st.text_input(
                    "New Password", 
                    type="password",
                    placeholder="Enter a new password"
                )
            
            with pw_col2:
                confirm_password = st.text_input(
                    "Confirm Password", 
                    type="password",
                    placeholder="Confirm your new password"
                )
            
            # Validate passwords
            passwords_match = new_password == confirm_password
            password_length_valid = len(new_password) >= 8 if new_password else True
            
            if new_password and not password_length_valid:
                st.warning("Password must be at least 8 characters long.")
            
            if new_password and confirm_password and not passwords_match:
                st.error("Passwords do not match.")
            
            # Change password button
            if st.button(
                "Change Password", 
                use_container_width=True,
                disabled=not (current_password and new_password and confirm_password and passwords_match and password_length_valid)
            ):
                st.success("Password changed successfully!")
                
                # In a real app, this would call the API to change the password
                # change_password(token, current_password, new_password)
            
            st.markdown("</div>", unsafe_allow_html=True)
                            else:
            st.warning("Could not load user profile. Please try again later.")

    with settings_tabs[1]:  # Notifications
        st.markdown(
            """
            <div class="settings-section-title">
                Notification Preferences
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Email notifications
        st.markdown(
            """
            <div class="settings-card">
                <div class="settings-card-title">Email Notifications</div>
            """,
            unsafe_allow_html=True
        )
        
        email_notify = st.checkbox(
            "Enable email notifications",
            value=True,
            help="Receive email notifications for important events"
        )
        
        if email_notify:
            st.markdown("<div class='settings-subsection'>Notification Types</div>", unsafe_allow_html=True)
            
            notify_col1, notify_col2 = st.columns(2)
            
            with notify_col1:
                st.checkbox("New interview completed", value=True)
                st.checkbox("Weekly summary reports", value=True)
                st.checkbox("System alerts", value=False)
            
            with notify_col2:
                st.checkbox("Sentiment alerts", value=True)
                st.checkbox("Department reports", value=False)
                st.checkbox("Account activity", value=False)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # In-app notifications
        st.markdown(
            """
            <div class="settings-card">
                <div class="settings-card-title">In-App Notifications</div>
            """,
            unsafe_allow_html=True
        )
        
        app_notify = st.checkbox(
            "Enable in-app notifications",
            value=True,
            help="Receive notifications within the dashboard"
        )
        
        if app_notify:
            notify_freq = st.radio(
                "Notification frequency",
                ["Real-time", "Hourly digest", "Daily digest"],
                horizontal=True
            )
            
            st.markdown("<div class='settings-subsection'>Alert Thresholds</div>", unsafe_allow_html=True)
            
            sentiment_threshold = st.slider(
                "Negative sentiment alert threshold",
                    min_value=-1.0,
                    max_value=0.0,
                value=-0.5,
                step=0.1,
                help="Alert when sentiment falls below this value"
            )
            
            completion_threshold = st.slider(
                "Low completion rate alert threshold (%)",
                min_value=0,
                max_value=100,
                value=70,
                step=5,
                help="Alert when completion rate falls below this percentage"
            )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Save notification settings
        if st.button("Save Notification Settings", use_container_width=True):
            st.success("Notification settings saved successfully!")
            
            # In a real app, this would call the API to update notification settings
            # update_notification_settings(token, email_notify=email_notify, app_notify=app_notify, ...)

    with settings_tabs[2]:  # System Settings
        st.markdown(
            """
            <div class="settings-section-title">
                System Settings
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Data retention
        st.markdown(
            """
            <div class="settings-card">
                <div class="settings-card-title">Data Retention</div>
            """,
            unsafe_allow_html=True
        )
        
        retention_period = st.selectbox(
            "Interview data retention period",
            ["Forever", "5 years", "3 years", "1 year", "6 months"],
            help="How long to keep interview data before automatic archiving"
        )
        
        st.checkbox(
            "Anonymize employee data after retention period",
            value=True,
            help="Replace personally identifiable information with anonymized data"
        )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Display settings
        st.markdown(
            """
            <div class="settings-card">
                <div class="settings-card-title">Display Settings</div>
            """,
            unsafe_allow_html=True
        )
        
        display_col1, display_col2 = st.columns(2)
        
        with display_col1:
            st.selectbox(
                "Default tab on startup",
                ["Dashboard", "Interviews", "Reports", "Settings"],
                index=0,
                help="Which tab to show when opening the application"
            )
            
            st.selectbox(
                "Default date range",
                ["Last 30 days", "Last 90 days", "Last 180 days", "Last year", "All time"],
                index=1,
                help="Default date range for dashboard and reports"
            )
        
        with display_col2:
            st.checkbox(
                "Show department metrics",
                value=True,
                help="Display department-specific metrics on dashboard"
            )
            
            st.checkbox(
                "Show sentiment analysis",
                value=True,
                help="Display sentiment analysis in interview details"
            )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Language and localization
        st.markdown(
            """
            <div class="settings-card">
                <div class="settings-card-title">Language & Localization</div>
            """,
            unsafe_allow_html=True
        )
        
        locale_col1, locale_col2 = st.columns(2)
        
        with locale_col1:
            st.selectbox(
                "Language",
                ["English (US)", "English (UK)", "Spanish", "French", "German"],
                index=0
            )
        
        with locale_col2:
            st.selectbox(
                "Date format",
                ["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"],
                index=0
            )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Save system settings
        if st.button("Save System Settings", use_container_width=True):
            st.success("System settings saved successfully!")
            
            # In a real app, this would call the API to update system settings
            # update_system_settings(token, ...)

    with settings_tabs[3]:  # API Configuration
        st.markdown(
            """
            <div class="settings-section-title">
                API Configuration
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # API settings
        st.markdown(
            """
            <div class="settings-card">
                <div class="settings-card-title">API Settings</div>
                <div class="settings-card-description">
                    Configure connections to external systems and APIs
                </div>
            """,
            unsafe_allow_html=True
        )
        
        api_enabled = st.checkbox(
            "Enable API access",
            value=True,
            help="Allow external systems to access data via API"
        )
        
        if api_enabled:
            # API keys
            st.markdown("<div class='settings-subsection'>API Keys</div>", unsafe_allow_html=True)
            
            api_col1, api_col2, api_col3 = st.columns([3, 1, 1])
            
            with api_col1:
                st.text_input(
                    "Current API Key",
                    value="••••••••••••••••••••••",
                    disabled=True
                )
            
            with api_col2:
                st.button("Reveal Key", use_container_width=True)
            
            with api_col3:
                if st.button("Regenerate", use_container_width=True):
                    st.info("A new API key has been generated.")
            
            # Webhook settings
            st.markdown("<div class='settings-subsection'>Webhook Configuration</div>", unsafe_allow_html=True)
            
            st.text_input(
                "Webhook URL",
                placeholder="https://example.com/webhook",
                help="URL to receive webhook notifications"
            )
            
            webhook_col1, webhook_col2 = st.columns(2)
            
            with webhook_col1:
                st.multiselect(
                    "Webhook Events",
                    ["Interview Completed", "Employee Added", "Report Generated", "Sentiment Alert"],
                    default=["Interview Completed", "Sentiment Alert"],
                    help="Events that trigger webhook notifications"
                )
            
            with webhook_col2:
                st.text_input(
                    "Secret Key",
                    type="password",
                    placeholder="Enter webhook secret key",
                    help="Secret key to validate webhook requests"
                )
            
            # Rate limiting
            st.markdown("<div class='settings-subsection'>Rate Limiting</div>", unsafe_allow_html=True)
            
            st.slider(
                "Maximum API calls per minute",
                min_value=10,
                max_value=500,
                value=100,
                step=10,
                help="Rate limit for API calls to prevent abuse"
            )
            
            # IP whitelist
            st.markdown("<div class='settings-subsection'>IP Whitelist</div>", unsafe_allow_html=True)
            
            st.text_area(
                "Allowed IP addresses",
                placeholder="Enter one IP address per line\nExample: 192.168.1.1",
                help="Only allow API access from these IP addresses (leave blank to allow all)"
            )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Integration settings
        st.markdown(
            """
            <div class="settings-card">
                <div class="settings-card-title">Integrations</div>
            """,
            unsafe_allow_html=True
        )
        
        st.selectbox(
            "HRIS Integration",
            ["None", "Workday", "BambooHR", "ADP", "SAP SuccessFactors"],
            index=0,
            help="Integrate with your Human Resources Information System"
        )
        
        st.selectbox(
            "Single Sign-On (SSO)",
            ["Disabled", "Okta", "Auth0", "Azure AD", "Google Workspace"],
            index=0,
            help="Configure single sign-on provider"
        )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Save API settings
        if st.button("Save API Settings", use_container_width=True):
            st.success("API settings saved successfully!")
            
            # In a real app, this would call the API to update API settings
            # update_api_settings(token, ...)


# Main App Logic
def main():
    # --- Handle logout request first ---
    if st.session_state.get("_logout_requested", False):
        st.session_state.token = None
        cookies.delete("auth_token")
        st.session_state.clear()  # This will reset ALL session state variables
        st.rerun()

    # --- Check for token in cookie first (for page reloads) ---
    if not st.session_state.token:
        stored_token = cookies.get("auth_token")
        if stored_token:
            st.session_state.token = stored_token

    # --- Display login or main app ---
    if not st.session_state.token:
        # Use our new login component
        if render_login(login, cookies):
            st.rerun()  # Reload after successful login
    else:
        # --- Main App Interface ---
        st.sidebar.title("ExitBot Dashboard")
        
        # Navigation in sidebar
        pages = ["Dashboard", "Interviews", "Reports", "Settings"]
        
        # Set active tab from sidebar
        active_tab = st.sidebar.radio("Navigation", pages, index=pages.index(st.session_state.active_tab))
        
        # Update session state for active tab
        if active_tab != st.session_state.active_tab:
            st.session_state.active_tab = active_tab
            # Reset selected interview when changing tabs
            if active_tab != "Interviews":
                st.session_state.selected_interview = None
        
        # Add accessibility options to sidebar
        st.sidebar.markdown("---")
        st.sidebar.markdown("### Accessibility Options")
        
        # High contrast mode toggle
        high_contrast = st.sidebar.checkbox(
            "High Contrast Mode", 
            value=st.session_state.get("high_contrast", False),
            help="Enable high contrast mode for better visibility"
        )
        
        # Update session state for high contrast mode
        if high_contrast != st.session_state.get("high_contrast", False):
            st.session_state.high_contrast = high_contrast
            st.rerun()  # Rerun to apply the style changes
        
        # Apply high contrast mode if enabled
        if st.session_state.get("high_contrast", False):
            st.markdown(
                """
                <style>
                body, [class*="st-"] {
                    background-color: #000000 !important;
                    color: #FFFFFF !important;
                }
                
                .card, .dashboard-card, .metrics-row, .interview-card {
                    background-color: #222222 !important;
                    border: 2px solid #FFFFFF !important;
                }
                
                .stButton > button {
                    background-color: #FFFFFF !important;
                    color: #000000 !important;
                    border: 2px solid #FFFFFF !important;
                }
                
                a {
                    color: #3B82F6 !important;
                    text-decoration: underline !important;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
        
        # Add reduced motion option
        reduced_motion = st.sidebar.checkbox(
            "Reduce Animations", 
            value=st.session_state.get("reduced_motion", False),
            help="Minimize animations for reduced motion sensitivity"
        )
        
        # Update session state for reduced motion
        if reduced_motion != st.session_state.get("reduced_motion", False):
            st.session_state.reduced_motion = reduced_motion
            st.rerun()
        
        # Apply reduced motion if enabled
        if st.session_state.get("reduced_motion", False):
            st.markdown(
                """
                <style>
                * {
                    animation-duration: 0s !important;
                    transition-duration: 0s !important;
                    scroll-behavior: auto !important;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            
        # Add text size adjustment
        text_size_options = {
            "Normal": 1.0,
            "Large": 1.2,
            "Larger": 1.4
        }
        
        selected_text_size = st.sidebar.radio(
            "Text Size",
            options=list(text_size_options.keys()),
            index=list(text_size_options.keys()).index(st.session_state.get("text_size", "Normal")),
            horizontal=True
        )
        
        # Update session state for text size
        if selected_text_size != st.session_state.get("text_size", "Normal"):
            st.session_state.text_size = selected_text_size
            st.rerun()
        
        # Apply text size adjustment if not normal
        if st.session_state.get("text_size", "Normal") != "Normal":
            size_factor = text_size_options[st.session_state.get("text_size", "Normal")]
            st.markdown(
                f"""
                <style>
                html {{
                    font-size: {size_factor}rem !important;
                }}
                </style>
                """,
                unsafe_allow_html=True
            )
        
        st.sidebar.markdown("---")
        
        # Logout button
        if st.sidebar.button("Logout", key="logout_button"):
            st.session_state["_logout_requested"] = True
            st.rerun()  # This will trigger the logout logic at the top
        
        # Render the selected tab
        if active_tab == "Dashboard":
            render_dashboard(st.session_state.token)
        elif active_tab == "Interviews":
            render_interviews_tab(st.session_state.token)
        elif active_tab == "Reports":
            render_reports_tab(st.session_state.token, *st.session_state.date_range)
        elif active_tab == "Settings":
            render_settings_tab(st.session_state.token)


# Run the app
if __name__ == "__main__":
    main()

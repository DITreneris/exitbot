"""
Interviews page component for the ExitBot HR app.
"""

import streamlit as st
from datetime import datetime, timedelta

from exitbot.frontend.utils import (
    display_api_error,
    display_empty_state,
    format_date,
    load_interview_data,
    load_interview_details,
    get_date_range,
    set_selected_interview,
    get_selected_interview
)


def render_interview_filters():
    """
    Render interview list filters.
    
    Returns:
        tuple: (search_query, department, status, use_date_range)
    """
    st.markdown(
        """
        <div class="filter-container">
            <div class="filter-header">
                <h3>Filter Interviews</h3>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Text search for employee name/ID
    search_query = st.text_input("Search employee name or ID", 
                                key="interview_search")
    
    # Create two columns for filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Department dropdown
        department = st.selectbox(
            "Department",
            options=["All", "Engineering", "Marketing", "Sales", "HR", "Finance"],
            key="department_filter"
        )
    
    with col2:
        # Status dropdown
        status = st.selectbox(
            "Status",
            options=["All", "completed", "in_progress", "not_started"],
            key="status_filter"
        )
    
    with col3:
        # Date range toggle
        use_date_range = st.checkbox("Filter by date range", value=False,
                                    key="use_date_range")
    
    return search_query, department, status, use_date_range


def render_interview_list(token, search_query=None, department=None, status=None, 
                         start_date=None, end_date=None):
    """
    Render the list of interviews with pagination.
    
    Args:
        token (str): Authentication token
        search_query (str, optional): Search query for employee name/id
        department (str, optional): Department filter
        status (str, optional): Status filter
        start_date (str, optional): Start date filter
        end_date (str, optional): End date filter
        
    Returns:
        None
    """
    # Default to page 1 if not in session state
    if "interview_page" not in st.session_state:
        st.session_state.interview_page = 1
    
    # Page size
    page_size = 10
    
    # Load interviews with pagination
    interviews, error = load_interview_data(
        token,
        search_query=search_query,
        department=department,
        status=status,
        start_date=start_date,
        end_date=end_date,
        page=st.session_state.interview_page,
        limit=page_size
    )
    
    if error:
        display_api_error(error, "Failed to load interviews")
        return
    
    # Handle empty data
    items = interviews.get("items", [])
    if not items:
        display_empty_state("No Interviews Found", "🔍")
        return
    
    # Display total count
    total = interviews.get("total", 0)
    st.markdown(f"**{total} interviews found**")
    
    # Render interviews as cards
    st.markdown(
        """
        <div class="interview-list">
        """,
        unsafe_allow_html=True
    )
    
    # Get currently selected interview
    selected_interview = get_selected_interview()
    
    for interview in items:
        interview_id = interview.get("id")
        name = interview.get("employee_name", "Unknown Employee")
        dept = interview.get("department", "Unknown Department")
        date_str = format_date(interview.get("date"))
        status = interview.get("status", "unknown")
        
        # Choose color based on status
        status_color = {
            "completed": "success",
            "in_progress": "warning",
            "not_started": "neutral"
        }.get(status, "neutral")
        
        # Choose emoji based on status
        status_emoji = {
            "completed": "✅",
            "in_progress": "⏳",
            "not_started": "🔄"
        }.get(status, "❓")
        
        is_selected = selected_interview == interview_id
        
        col1, col2 = st.columns([10, 2])
        with col1:
            st.markdown(
                f"""
                <div class="interview-card {'selected' if is_selected else ''}">
                    <div class="interview-card-details">
                        <div class="interview-name">{name}</div>
                        <div class="interview-meta">
                            <span class="department">{dept}</span>
                            <span class="separator">•</span>
                            <span class="date">{date_str}</span>
                        </div>
                    </div>
                    <div class="interview-status {status_color}">
                        <span class="status-icon">{status_emoji}</span>
                        <span class="status-text">{status.replace('_', ' ').title()}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col2:
            if st.button("View", key=f"view_{interview_id}"):
                set_selected_interview(interview_id)
                st.rerun()
    
    st.markdown(
        """
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Pagination controls
    total_pages = (total + page_size - 1) // page_size
    
    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            if st.button("◀ Previous", 
                        disabled=st.session_state.interview_page <= 1):
                st.session_state.interview_page -= 1
                st.rerun()
        
        with col2:
            st.markdown(
                f"""
                <div class="pagination-info">
                    Page {st.session_state.interview_page} of {total_pages}
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col3:
            if st.button("Next ▶", 
                        disabled=st.session_state.interview_page >= total_pages):
                st.session_state.interview_page += 1
                st.rerun()


def render_interview_details(token, interview_id):
    """
    Render details for a specific interview.
    
    Args:
        token (str): Authentication token
        interview_id (str): ID of the interview to display
        
    Returns:
        None
    """
    # Load interview details
    details, error = load_interview_details(token, interview_id)
    
    if error:
        display_api_error(error, "Failed to load interview details")
        return
    
    # Back button
    if st.button("← Back to List"):
        set_selected_interview(None)
        st.rerun()
    
    # Extract interview data
    name = details.get("employee_name", "Unknown Employee")
    employee_id = details.get("employee_id", "N/A")
    dept = details.get("department", "Unknown Department")
    position = details.get("position", "Unknown Position")
    manager = details.get("manager", "Unknown Manager")
    date_str = format_date(details.get("date"))
    status = details.get("status", "unknown")
    
    # Header with interview information
    st.markdown(
        f"""
        <div class="interview-details-header">
            <h2>{name}</h2>
            <div class="interview-meta-details">
                <span>ID: {employee_id}</span>
                <span class="separator">•</span>
                <span>Department: {dept}</span>
                <span class="separator">•</span>
                <span>Position: {position}</span>
            </div>
            <div class="interview-meta-details">
                <span>Manager: {manager}</span>
                <span class="separator">•</span>
                <span>Date: {date_str}</span>
                <span class="separator">•</span>
                <span class="status-{status}">{status.replace('_', ' ').title()}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Show summary if completed
    if status == "completed" and "summary" in details:
        summary = details["summary"]
        
        # Overall experience
        st.markdown("### Overall Experience")
        sentiment = summary.get("sentiment", {})
        sentiment_score = sentiment.get("score", 0)
        
        # Render sentiment score with color
        sentiment_color = "green" if sentiment_score >= 4 else "orange" if sentiment_score >= 2.5 else "red"
        st.markdown(
            f"""
            <div class="sentiment-score" style="color: {sentiment_color}">
                {sentiment_score:.1f}/5
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Key points from the interview
        st.markdown("### Key Points")
        key_points = summary.get("key_points", [])
        for point in key_points:
            st.markdown(f"- {point}")
        
        # Reasons for leaving
        st.markdown("### Primary Reasons for Leaving")
        reasons = summary.get("reasons", [])
        for reason in reasons:
            category = reason.get("category", "Other")
            details = reason.get("details", "No details provided")
            st.markdown(
                f"""
                <div class="reason-item">
                    <div class="reason-category">{category}</div>
                    <div class="reason-details">{details}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # Recommendations
        st.markdown("### Recommendations")
        recommendations = summary.get("recommendations", [])
        for rec in recommendations:
            st.markdown(f"- {rec}")
    
    elif status == "in_progress":
        st.markdown(
            """
            <div class="interview-in-progress">
                <div class="progress-icon">⏳</div>
                <div class="progress-message">
                    <h3>Interview in Progress</h3>
                    <p>The employee is currently taking this exit interview.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    else:  # not_started
        st.markdown(
            """
            <div class="interview-not-started">
                <div class="not-started-icon">🔄</div>
                <div class="not-started-message">
                    <h3>Interview Not Started</h3>
                    <p>The employee has not yet begun this exit interview.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


def render_interviews(token):
    """
    Render the interviews page with list and details views.
    
    Args:
        token (str): Authentication token
        
    Returns:
        None
    """
    st.markdown(
        """
        <div class="interviews-header">
            <h1>Exit Interviews</h1>
            <div class="interviews-subtitle">
                View and analyze employee exit interviews.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Get selected interview if any
    selected_interview = get_selected_interview()
    
    # If viewing details, show full width details page
    if selected_interview:
        render_interview_details(token, selected_interview)
        return
    
    # Otherwise show the list view with filters
    # Get filter values
    search_query, department, status, use_date_range = render_interview_filters()
    
    # Get date range if enabled
    start_date, end_date = None, None
    if use_date_range:
        start_date, end_date = get_date_range()
        start_date = start_date.strftime("%Y-%m-%d")
        end_date = end_date.strftime("%Y-%m-%d")
    
    # Display the list of interviews
    render_interview_list(
        token, 
        search_query=search_query, 
        department=department, 
        status=status,
        start_date=start_date, 
        end_date=end_date
    )

    st.markdown(
        """
        <style>
        .interview-list {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        .interview-card {
            background: #fff;
            border-radius: 16px;
            box-shadow: 0 4px 12px -2px rgba(30,64,175,0.06);
            padding: 1.5rem 1.5rem 1.5rem 1.5rem;
            margin-bottom: 0.5rem;
            transition: box-shadow 0.2s, transform 0.2s;
            font-size: 1.15rem;
        }
        .interview-card.selected {
            border: 2px solid #2563EB;
            box-shadow: 0 6px 16px -2px rgba(30,64,175,0.12);
        }
        .interview-name {
            font-size: 1.35rem;
            font-weight: 700;
            color: #1E40AF;
            margin-bottom: 0.25rem;
        }
        .interview-meta {
            font-size: 1.05rem;
            color: #6B7280;
            font-weight: 500;
        }
        .interview-status {
            font-size: 1.1rem;
            font-weight: 600;
            border-radius: 8px;
            padding: 0.3rem 0.8rem;
            margin-top: 0.5rem;
            display: inline-block;
        }
        .interview-status.success {
            background: #D1FAE5;
            color: #047857;
        }
        .interview-status.warning {
            background: #FEF3C7;
            color: #B45309;
        }
        .interview-status.neutral {
            background: #F3F4F6;
            color: #6B7280;
        }
        .filter-header h3 {
            font-size: 1.35rem;
            font-weight: 700;
            color: #1E40AF;
            margin-bottom: 0.5rem;
        }
        .pagination-info {
            font-size: 1.1rem;
            font-weight: 600;
            color: #1E40AF;
            margin-top: 0.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    ) 
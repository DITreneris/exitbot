"""
Dashboard page component for the ExitBot HR app.
"""

import streamlit as st
from datetime import datetime, timedelta, date
import pandas as pd

from exitbot.frontend.utils import (
    display_api_error,
    display_empty_state,
    format_date,
    load_dashboard_data,
    get_date_range,
    set_date_range
)
from exitbot.frontend.components.dashboard_cards import (
    render_metric_card,
    render_interview_completion_chart,
    render_time_series_chart,
    render_department_breakdown,
    render_sentiment_gauge
)


def format_completion_rate(completed, total):
    """
    Format the completion rate as a percentage
    
    Args:
        completed (int): Number of completed interviews
        total (int): Total number of interviews
        
    Returns:
        str: Formatted percentage
    """
    if total == 0:
        return "0%"
    
    rate = (completed / total) * 100
    return f"{int(rate)}%"


def render_dashboard(token):
    """
    Render the dashboard page with metrics and visualizations.
    
    Args:
        token (str): Authentication token
        
    Returns:
        None
    """
    # Add page header with better visual hierarchy
    st.markdown(
        """
        <style>
        .dashboard-hero {
            background-color: #1E40AF;
            color: white;
            padding: 18px 32px 18px 32px;
            border-radius: 16px;
            margin-bottom: 24px;
            background-image: linear-gradient(to right, #1E40AF, #2563EB);
            box-shadow: 0 4px 12px -2px rgba(30,64,175,0.10);
            display: flex;
            flex-direction: column;
            align-items: flex-start;
        }
        .dashboard-hero h1 {
            color: white;
            font-size: 2.8rem;
            margin-bottom: 6px;
            font-weight: 800;
            letter-spacing: -1px;
            line-height: 1.1;
            background: none !important;
            padding: 0 !important;
            box-shadow: none !important;
        }
        .dashboard-subtitle {
            color: #DBEAFE;
            font-size: 1.25rem;
            max-width: 800px;
            font-weight: 500;
            margin-bottom: 0;
        }
        .dashboard-stats-row {
            background-color: white;
            border-radius: 16px;
            padding: 28px 24px 28px 24px;
            box-shadow: 0 4px 12px -2px rgba(30,64,175,0.06);
            margin-bottom: 28px;
            display: flex;
            gap: 2rem;
        }
        .metric-card .metric-value {
            font-size: 2.5rem !important;
            font-weight: 800 !important;
            color: #1E40AF !important;
            margin-bottom: 0.5rem;
        }
        .metric-card .metric-title {
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            color: #374151 !important;
        }
        .metric-card .metric-delta {
            font-size: 1.1rem !important;
            font-weight: 600 !important;
        }
        .metric-card .metric-delta-suffix {
            font-size: 0.95rem !important;
        }
        .section-gap {
            height: 32px;
        }
        .chart-container {
            background-color: white;
            border-radius: 16px;
            padding: 28px 24px 28px 24px;
            box-shadow: 0 4px 12px -2px rgba(30,64,175,0.06);
            margin-bottom: 28px;
        }
        .chart-header h3 {
            font-size: 1.35rem;
            font-weight: 700;
            color: #1E40AF;
        }
        .activity-item {
            display: flex;
            padding: 12px 0;
            border-bottom: 1px solid #F3F4F6;
        }
        .activity-icon {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 12px;
        }
        .activity-icon.completed {
            background-color: rgba(16, 185, 129, 0.1);
            color: #10B981;
        }
        .activity-icon.pending {
            background-color: rgba(245, 158, 11, 0.1);
            color: #F59E0B;
        }
        .activity-details {
            flex: 1;
        }
        .activity-name {
            font-weight: 600;
            color: #1F2937;
        }
        .activity-meta {
            color: #6B7280;
            font-size: 0.9rem;
            display: flex;
            justify-content: space-between;
        }
        </style>
        
        <div class="dashboard-hero">
            <h1>ExitBot Dashboard</h1>
            <div class="dashboard-subtitle">
                Monitor your exit interviews, analyze trends, and gain valuable insights to improve employee retention.
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
        
        # Get date range from session state
        start_date, end_date = get_date_range()
        
        # Store date range in session state so it persists
        date_range = st.date_input(
            "Select date range",
            value=(start_date, end_date),
            min_value=date(2020, 1, 1),
            max_value=datetime.now().date(),
        )
        
        # Handle the case when a single date is selected
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            set_date_range(start_date, end_date)
        else:
            # If only one date selected, use it for both start and end
            set_date_range(date_range, date_range)
            start_date, end_date = date_range, date_range
        
        # Add quick date presets for better UX
        st.markdown("### Quick Select")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Last 30 days", use_container_width=True):
                end = datetime.now().date()
                start = end - timedelta(days=30)
                set_date_range(start, end)
                st.rerun()
        with col2:
            if st.button("Last 90 days", use_container_width=True):
                end = datetime.now().date()
                start = end - timedelta(days=90)
                set_date_range(start, end)
                st.rerun()

    # Format dates for API
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    # Load dashboard data
    dashboard_data, error = load_dashboard_data(token, start_str, end_str)
    
    if error or not dashboard_data:
        # Create placeholder data for development
        dashboard_data = {
            "summary_stats": {
                "interviews_total": 45,
                "interviews_complete": 32,
                "interviews_incomplete": 13,
                "avg_sentiment": 0.65,
                "top_categories": [
                    {"category": "Career Growth", "count": 12},
                    {"category": "Compensation", "count": 8},
                    {"category": "Work-Life Balance", "count": 6},
                    {"category": "Management", "count": 5},
                    {"category": "Company Culture", "count": 4}
                ]
            },
            "department_breakdown": {
                "Engineering": 15,
                "Sales": 10,
                "Marketing": 8,
                "HR": 5,
                "Finance": 4,
                "Product": 3
            },
            "recent_interviews": [
                {
                    "employee_name": "John Smith",
                    "department": "Engineering",
                    "date": "2023-05-10",
                    "status": "completed"
                },
                {
                    "employee_name": "Jane Doe",
                    "department": "Marketing",
                    "date": "2023-05-08",
                    "status": "completed"
                },
                {
                    "employee_name": "Michael Johnson",
                    "department": "Sales",
                    "date": "2023-05-05",
                    "status": "pending"
                }
            ]
        }
        
        # Show a message that we're using demo data
        st.warning("Showing demo data. Connect to API for real data.")
    
    # Extract data from dashboard_data
    stats = dashboard_data["summary_stats"]
    department_data = dashboard_data["department_breakdown"]
    recent_interviews = dashboard_data["recent_interviews"]
    
    # Safely extract values with defaults
    interviews_total = stats.get("interviews_total", 0)
    interviews_complete = stats.get("interviews_complete", 0)
    interviews_incomplete = stats.get("interviews_incomplete", 0)
    avg_sentiment = stats.get("avg_sentiment", 0)
    top_categories = stats.get("top_categories", [])
    
    # Top row stats with enhanced styling
    st.markdown("<div class='dashboard-stats-row'>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_metric_card(
            title="Total Exit Interviews",
            value=interviews_total,
            delta="+5%",
            delta_suffix="vs. previous period",
            icon="📋"
        )

    with col2:
        completion_rate = format_completion_rate(interviews_complete, interviews_total)
        render_metric_card(
            title="Completion Rate",
            value=completion_rate,
            delta="+2%",
            delta_suffix="vs. previous period",
            icon="✅"
        )

    with col3:
        render_metric_card(
            title="Average Sentiment",
            value=f"{avg_sentiment:.1f}",
            delta="-0.3",
            delta_suffix="vs. previous period",
            icon="😊"
        )

    with col4:
        render_metric_card(
            title="Incomplete Interviews",
            value=interviews_incomplete,
            delta="+2",
            delta_suffix="requiring attention",
            icon="⏳"
        )
    st.markdown("</div>", unsafe_allow_html=True)

    # Middle row: Charts
    st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            <div class='chart-container'>
                <div class='chart-header'>
                    <h3>Interview Completion</h3>
                </div>
            """,
            unsafe_allow_html=True
        )
        render_interview_completion_chart(interviews_complete, interviews_incomplete, interviews_total)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown(
            """
            <div class='chart-container'>
                <div class='chart-header'>
                    <h3>Sentiment Analysis</h3>
                </div>
            """,
            unsafe_allow_html=True
        )
        render_sentiment_gauge(avg_sentiment)
        st.markdown("</div>", unsafe_allow_html=True)

    # Bottom row: Department Breakdown and Top Departure Reasons
    st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            <div class='chart-container'>
                <div class='chart-header'>
                    <h3>Department Breakdown</h3>
                </div>
            """,
            unsafe_allow_html=True
        )
        
        # Create a DataFrame for the department data if it's a dict or list
        if isinstance(department_data, (dict, list)):
            if isinstance(department_data, dict):
                # Transform dict to dataframe
                df = pd.DataFrame({
                    'department': list(department_data.keys()),
                    'count': list(department_data.values())
                })
            else:
                # Assuming it's a list of dicts with 'department' and 'count' keys
                df = pd.DataFrame(department_data)
        else:
            # If it's already a DataFrame, use it directly
            df = department_data
            
        # Render department breakdown
        render_department_breakdown(df)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown(
            """
            <div class='chart-container'>
                <div class='chart-header'>
                    <h3>Top Exit Reasons</h3>
                </div>
            """,
            unsafe_allow_html=True
        )
        # Extract top categories for chart visualization
        categories = [item["category"] for item in top_categories]
        values = [item["count"] for item in top_categories]
        
        # Create a DataFrame for the chart
        df = pd.DataFrame({
            'Category': categories,
            'Count': values
        })
        
        # Pass the correct parameters to the function
        render_time_series_chart(
            data=df, 
            title="Top Exit Reasons", 
            x_column='Category', 
            y_column='Count'
        )
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Recent activity feed
    st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class='chart-container'>
            <div class='chart-header'>
                <h3>Recent Activity</h3>
            </div>
        """,
        unsafe_allow_html=True
    )
    
    # Display recent interviews in a nice list
    if recent_interviews:
        for interview in recent_interviews:
            status = interview.get("status", "unknown")
            status_emoji = "✅" if status == "completed" else "⏳"
            name = interview.get("employee_name", "Unknown Employee")
            dept = interview.get("department", "Unknown Department")
            date_str = format_date(interview.get("date", ""))
            
            st.markdown(
                f"""
                <div class="activity-item">
                    <div class="activity-icon {status}">{status_emoji}</div>
                    <div class="activity-details">
                        <div class="activity-title">{name} - {dept}</div>
                        <div class="activity-date">{date_str}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.markdown(
            """
            <div class="empty-activity">
                <p>No recent interviews found in the selected date range.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown("</div>", unsafe_allow_html=True) 
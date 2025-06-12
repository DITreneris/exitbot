"""
Reports page component for the ExitBot HR app.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

from exitbot.frontend.utils import (
    display_api_error,
    display_empty_state,
    format_date,
    format_percentage,
    load_report_data,
    get_date_range,
    set_date_range
)
from exitbot.frontend.api_client import export_data


def render_report_filters():
    """
    Render report filters in the sidebar.
    
    Returns:
        tuple: (start_date, end_date, selected_departments)
    """
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-header">
                <h3>📅 Report Options</h3>
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
            if st.button("Last 30 days", use_container_width=True, key="reports_30d"):
                end = datetime.now().date()
                start = end - timedelta(days=30)
                set_date_range(start, end)
                st.rerun()
        with col2:
            if st.button("Last 90 days", use_container_width=True, key="reports_90d"):
                end = datetime.now().date()
                start = end - timedelta(days=90)
                set_date_range(start, end)
                st.rerun()
        
        # Department multi-select
        st.markdown("### Departments")
        
        # Initialize departments in session state if not present
        if "selected_departments" not in st.session_state:
            st.session_state.selected_departments = []
        
        # Department options
        department_options = [
            "Engineering", 
            "Marketing", 
            "Sales", 
            "Human Resources", 
            "Finance", 
            "Operations"
        ]
        
        selected_departments = st.multiselect(
            "Select departments",
            options=department_options,
            default=st.session_state.selected_departments,
            key="report_departments"
        )
        
        # Store in session state
        st.session_state.selected_departments = selected_departments
        
        # Reset button for filters
        if st.button("Reset Filters", use_container_width=True):
            end = datetime.now().date()
            start = end - timedelta(days=30)
            set_date_range(start, end)
            st.session_state.selected_departments = []
            st.rerun()
    
    return start_date, end_date, selected_departments


def render_summary_statistics(stats):
    """
    Render summary statistics section.
    
    Args:
        stats (dict): Summary statistics data
        
    Returns:
        None
    """
    st.markdown("## Summary Statistics")
    
    # Create metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Interviews", 
            value=stats.get("interviews_total", 0),
            delta=stats.get("interviews_total_delta", "N/A")
        )
    
    with col2:
        st.metric(
            "Completion Rate", 
            value=format_percentage(
                stats.get("interviews_complete", 0) / 
                max(stats.get("interviews_total", 1), 1)
            ),
            delta=stats.get("completion_rate_delta", "N/A")
        )
    
    with col3:
        st.metric(
            "Average Sentiment", 
            value=f"{stats.get('avg_sentiment', 0):.1f}/5",
            delta=stats.get("avg_sentiment_delta", "N/A")
        )
    
    with col4:
        top_reason = "None"
        top_categories = stats.get("top_categories", [])
        if top_categories:
            top_reason = top_categories[0].get("category", "None")
        
        st.metric(
            "Top Exit Reason", 
            value=top_reason
        )


def render_department_analysis(department_data, selected_departments=None):
    """
    Render department analysis section.
    
    Args:
        department_data (dict): Department breakdown data
        selected_departments (list, optional): List of selected departments to highlight
        
    Returns:
        None
    """
    st.markdown("## Department Analysis")
    
    # Extract data for charting
    departments = []
    completion_rates = []
    sentiment_scores = []
    total_counts = []
    
    # Process department data
    for dept in department_data:
        dept_name = dept.get("department", "Unknown")
        
        # Skip if not in selected departments (when filter is active)
        if selected_departments and dept_name not in selected_departments:
            continue
            
        departments.append(dept_name)
        
        # Calculate completion rate
        total = dept.get("total", 0)
        completed = dept.get("completed", 0)
        completion_rate = completed / max(total, 1)
        completion_rates.append(completion_rate)
        
        # Get sentiment score
        sentiment = dept.get("sentiment", 0)
        sentiment_scores.append(sentiment)
        
        # Get total count
        total_counts.append(total)
    
    # Render data in tabs
    tab1, tab2, tab3 = st.tabs(["Completion Rates", "Sentiment Scores", "Exit Volume"])
    
    with tab1:
        if not departments:
            st.info("No department data available for the selected filters.")
        else:
            # Create a DataFrame for the completion rates
            df = pd.DataFrame({
                "Department": departments,
                "Completion Rate": [rate * 100 for rate in completion_rates]
            })
            
            # Sort by completion rate
            df = df.sort_values("Completion Rate", ascending=False)
            
            # Create the bar chart
            st.bar_chart(
                df.set_index("Department"),
                use_container_width=True
            )
    
    with tab2:
        if not departments:
            st.info("No department data available for the selected filters.")
        else:
            # Create a DataFrame for sentiment scores
            df = pd.DataFrame({
                "Department": departments,
                "Sentiment Score": sentiment_scores
            })
            
            # Sort by sentiment score
            df = df.sort_values("Sentiment Score", ascending=False)
            
            # Create the bar chart
            st.bar_chart(
                df.set_index("Department"),
                use_container_width=True
            )
    
    with tab3:
        if not departments:
            st.info("No department data available for the selected filters.")
        else:
            # Create a DataFrame for exit volume
            df = pd.DataFrame({
                "Department": departments,
                "Exit Interviews": total_counts
            })
            
            # Sort by count
            df = df.sort_values("Exit Interviews", ascending=False)
            
            # Create the bar chart
            st.bar_chart(
                df.set_index("Department"),
                use_container_width=True
            )


def render_trend_analysis(report_data):
    """
    Render trend analysis section.
    
    Args:
        report_data (dict): Combined report data
        
    Returns:
        None
    """
    st.markdown("## Trend Analysis")
    
    # Get trend data from the report
    # Normally this would come from the API, but we'll simulate it for now
    # In a real implementation, you'd request time-series data from the API
    
    # Simulate trend data
    st.info("Trend analysis data is being collected. Check back soon for insights into exit patterns over time.")
    
    # Placeholder for future implementation
    st.markdown("""
    Coming soon:
    - Monthly exit rates over time
    - Sentiment trends by department
    - Seasonality analysis
    - Correlation with company events
    """)


def render_export_options(token, start_date, end_date, selected_departments=None):
    """
    Render export options section.
    
    Args:
        token (str): Authentication token
        start_date (date): Start date for export
        end_date (date): End date for export
        selected_departments (list, optional): List of selected departments to export
        
    Returns:
        None
    """
    st.markdown("## Export Data")
    
    # Format dates for API
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    # Create export options
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Format")
        export_format = st.radio(
            "Choose export format",
            options=["CSV", "Excel", "JSON"],
            index=0,
            key="export_format"
        )
    
    with col2:
        st.markdown("### Options")
        include_summaries = st.checkbox("Include interview summaries", value=True, key="include_summaries")
        anonymize_data = st.checkbox("Anonymize personal data", value=False, key="anonymize_data")
    
    # Export button
    if st.button("Export Data", use_container_width=True, type="primary"):
        with st.spinner("Preparing export..."):
            # Call the export API
            export_data_result, error = export_data(
                token, 
                start_date=start_str,
                end_date=end_str,
                departments=selected_departments if selected_departments else None,
                format=export_format.lower(),
                include_summaries=include_summaries,
                anonymize=anonymize_data
            )
            
            if error:
                display_api_error(error, "Export Failed")
            else:
                # Normally, the API would return a download URL or file data
                # For demonstration, we'll just show success
                st.success("Export successful! The file will download automatically.")
                
                # In a real implementation, you'd provide a download link or
                # trigger a download with st.download_button


def render_reports(token):
    """
    Render the reports page with data visualization and export options.
    
    Args:
        token (str): Authentication token
        
    Returns:
        None
    """
    st.markdown(
        """
        <style>
        .report-section {
            background: #fff;
            border-radius: 16px;
            box-shadow: 0 4px 12px -2px rgba(30,64,175,0.06);
            padding: 2rem 2rem 2rem 2rem;
            margin-bottom: 2rem;
        }
        .report-header h2, .report-header h3 {
            font-size: 1.35rem;
            font-weight: 700;
            color: #1E40AF;
            margin-bottom: 0.5rem;
        }
        .summary-metric {
            font-size: 2.2rem;
            font-weight: 800;
            color: #1E40AF;
            margin-bottom: 0.25rem;
        }
        .summary-label {
            font-size: 1.1rem;
            font-weight: 600;
            color: #374151;
        }
        .summary-delta {
            font-size: 1.1rem;
            font-weight: 600;
        }
        .summary-delta-suffix {
            font-size: 0.95rem;
        }
        .department-table th, .department-table td {
            font-size: 1.05rem;
            padding: 0.6rem 1rem;
        }
        .trend-chart-container {
            background: #fff;
            border-radius: 16px;
            box-shadow: 0 4px 12px -2px rgba(30,64,175,0.06);
            padding: 1.5rem 1.5rem 1.5rem 1.5rem;
            margin-bottom: 1.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown(
        """
        <div class="reports-header">
            <h1>Exit Interview Reports</h1>
            <div class="reports-subtitle">
                Analyze trends and export data from exit interviews.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Render filters in sidebar and get values
    start_date, end_date, selected_departments = render_report_filters()
    
    # Format dates for API
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    # Load report data
    report_data, error = load_report_data(
        token, 
        start_str, 
        end_str, 
        departments=selected_departments if selected_departments else None
    )
    
    if error:
        # Show a friendly empty state instead of an error
        if display_empty_state("No Report Data Available", "📊", "Refresh Reports"):
            st.rerun()
        return
    
    # Extract data from report_data
    stats = report_data["summary_stats"]
    department_data = report_data["department_data"]
    
    # Render report sections
    render_summary_statistics(stats)
    render_department_analysis(department_data, selected_departments)
    render_trend_analysis(report_data)
    render_export_options(token, start_date, end_date, selected_departments) 
"""
Data loading utilities for the ExitBot HR app.
Standardizes API interactions and error handling.
"""

from exitbot.frontend.api_client import (
    get_all_interviews,
    get_interview_details,
    get_interview_summary,
    get_summary_stats,
    get_department_breakdown,
    export_data,
    get_questions,
    create_question,
    update_question,
    delete_question,
    get_system_config,
    update_system_config,
    get_user_profile,
)


def load_dashboard_data(token, start_date, end_date):
    """
    Load all data needed for the dashboard.
    
    Args:
        token (str): Authentication token
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        
    Returns:
        tuple: (dashboard_data, error)
            dashboard_data (dict): Combined dashboard data or None if error
            error (dict): Error details or None if successful
    """
    # Get summary statistics
    stats, error = get_summary_stats(token, start_date, end_date)
    if error:
        return None, error
    
    # Get department breakdown
    department_data, error = get_department_breakdown(token, start_date, end_date)
    if error:
        return None, error
    
    # Get recent interviews for activity feed
    interviews, error = get_all_interviews(
        token, 
        start_date=start_date,
        end_date=end_date,
        limit=5,  # Just need a few for the dashboard
        sort_by="date",
        sort_order="desc"
    )
    if error:
        return None, error
    
    # Combine all data into a single dashboard data object
    dashboard_data = {
        "summary_stats": stats,
        "department_breakdown": department_data,
        "recent_interviews": interviews.get("items", [])
    }
    
    return dashboard_data, None


def load_interview_data(token, search_query=None, department=None, status=None, 
                       start_date=None, end_date=None, page=1, limit=10):
    """
    Load interview data with filters.
    
    Args:
        token (str): Authentication token
        search_query (str, optional): Search query for employee name/id
        department (str, optional): Department filter
        status (str, optional): Status filter
        start_date (str, optional): Start date filter
        end_date (str, optional): End date filter
        page (int): Page number for pagination
        limit (int): Number of items per page
        
    Returns:
        tuple: (interview_data, error)
            interview_data (dict): Interview data with pagination or None if error
            error (dict): Error details or None if successful
    """
    # Calculate offset for pagination
    offset = (page - 1) * limit
    
    # Handle "All" department filter
    if department == "All":
        department = None
    
    # Handle "All" status filter
    if status == "All":
        status = None
    
    # Call API with filters
    interviews, error = get_all_interviews(
        token,
        search=search_query,
        department=department, 
        status=status,
        start_date=start_date,
        end_date=end_date,
        offset=offset,
        limit=limit
    )
    
    return interviews, error


def load_interview_details(token, interview_id):
    """
    Load details for a specific interview.
    
    Args:
        token (str): Authentication token
        interview_id (str): ID of the interview
        
    Returns:
        tuple: (interview_details, error)
            interview_details (dict): Interview details or None if error
            error (dict): Error details or None if successful
    """
    # Get basic interview data
    details, error = get_interview_details(token, interview_id)
    if error:
        return None, error
    
    # Get interview summary if available
    if details.get("status") == "completed":
        summary, error = get_interview_summary(token, interview_id)
        if not error:
            details["summary"] = summary
    
    return details, None


def load_report_data(token, start_date, end_date, departments=None):
    """
    Load data for reports.
    
    Args:
        token (str): Authentication token
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        departments (list, optional): List of departments to include
        
    Returns:
        tuple: (report_data, error)
            report_data (dict): Combined report data or None if error
            error (dict): Error details or None if successful
    """
    # Get summary statistics
    stats, error = get_summary_stats(token, start_date, end_date)
    if error:
        return None, error
    
    # Get department breakdown
    department_data, error = get_department_breakdown(
        token, 
        start_date, 
        end_date,
        departments=departments
    )
    if error:
        return None, error
    
    # Combine into report data
    report_data = {
        "summary_stats": stats,
        "department_data": department_data
    }
    
    return report_data, None


def load_settings_data(token):
    """
    Load settings data.
    
    Args:
        token (str): Authentication token
        
    Returns:
        tuple: (settings_data, error)
            settings_data (dict): Combined settings data or None if error
            error (dict): Error details or None if successful
    """
    # Get system configuration
    config, error = get_system_config(token)
    if error:
        return None, error
    
    # Get user profile
    profile, error = get_user_profile(token)
    if error:
        return None, error
    
    # Get question templates
    questions, error = get_questions(token)
    if error:
        return None, error
    
    # Combine into settings data
    settings_data = {
        "system_config": config,
        "user_profile": profile,
        "questions": questions
    }
    
    return settings_data, None 
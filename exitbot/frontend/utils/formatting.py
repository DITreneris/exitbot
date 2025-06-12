"""
Formatting utilities for the ExitBot HR app.
Provides consistent formatting for dates, percentages, and metrics.
"""

from datetime import datetime, timedelta, date


def format_date(date_obj, include_time=False):
    """
    Format a date consistently throughout the app.
    
    Args:
        date_obj (date or datetime): Date to format
        include_time (bool): Whether to include time in the output
        
    Returns:
        str: Formatted date string
    """
    if not date_obj:
        return "N/A"
    
    if isinstance(date_obj, str):
        try:
            if "T" in date_obj:  # ISO format with time
                date_obj = datetime.fromisoformat(date_obj.replace("Z", "+00:00"))
            else:
                date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
        except ValueError:
            return date_obj  # Return original if parsing fails
    
    if include_time and isinstance(date_obj, datetime):
        return date_obj.strftime("%b %d, %Y %I:%M %p")
    else:
        if isinstance(date_obj, datetime):
            date_obj = date_obj.date()
        return date_obj.strftime("%b %d, %Y")


def format_percentage(value, decimal_places=1):
    """
    Format a value as a percentage with specified decimal places.
    
    Args:
        value (float): Value to format (0.1 = 10%)
        decimal_places (int): Number of decimal places to include
        
    Returns:
        str: Formatted percentage string with % symbol
    """
    if value is None:
        return "N/A"
    
    try:
        value_float = float(value)
        return f"{value_float * 100:.{decimal_places}f}%"
    except (ValueError, TypeError):
        return str(value)


def format_completion_rate(completed, total):
    """
    Calculate and format the completion rate as a percentage.
    
    Args:
        completed (int): Number of completed items
        total (int): Total number of items
        
    Returns:
        str: Formatted completion rate as percentage
    """
    if not total:
        return "0%"
    
    completion_rate = completed / total
    return format_percentage(completion_rate)


def get_date_presets():
    """
    Return common date range presets for filters.
    
    Returns:
        dict: Dictionary of preset date ranges
    """
    today = date.today()
    return {
        "Last 7 days": (today - timedelta(days=7), today),
        "Last 30 days": (today - timedelta(days=30), today),
        "Last 90 days": (today - timedelta(days=90), today),
        "This year": (date(today.year, 1, 1), today),
        "Last year": (
            date(today.year - 1, 1, 1), 
            date(today.year - 1, 12, 31)
        ),
    } 
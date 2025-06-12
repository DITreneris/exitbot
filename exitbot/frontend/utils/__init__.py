"""
Utility functions for the ExitBot HR app.
"""

import sys
import os

# Add parent directory to path to make imports work
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from exitbot.frontend.utils.error_handling import display_api_error, display_empty_state
from exitbot.frontend.utils.formatting import (
    format_date, 
    format_percentage, 
    format_completion_rate,
    get_date_presets
)
from exitbot.frontend.utils.state_management import (
    initialize_session_state,
    get_token,
    set_token,
    clear_token,
    is_authenticated,
    set_active_tab,
    get_active_tab,
    set_date_range,
    get_date_range,
    set_selected_interview,
    get_selected_interview,
    get_cookie_manager
)
from exitbot.frontend.utils.data_loading import (
    load_dashboard_data,
    load_interview_data,
    load_interview_details,
    load_report_data,
    load_settings_data
)

__all__ = [
    # Error handling
    'display_api_error',
    'display_empty_state',
    
    # Formatting
    'format_date',
    'format_percentage',
    'format_completion_rate',
    'get_date_presets',
    
    # State management
    'initialize_session_state',
    'get_token',
    'set_token',
    'clear_token',
    'is_authenticated',
    'set_active_tab',
    'get_active_tab',
    'set_date_range',
    'get_date_range',
    'set_selected_interview',
    'get_selected_interview',
    'get_cookie_manager',
    
    # Data loading
    'load_dashboard_data',
    'load_interview_data',
    'load_interview_details',
    'load_report_data',
    'load_settings_data'
] 
"""
UI Components Package for ExitBot

This package contains reusable UI components based on the design system.
"""

# Import all components for easy access
from exitbot.frontend.components.design_system import (
    get_base_css, 
    get_hr_app_css, 
    get_employee_app_css
)
from exitbot.frontend.components.login import render_login
from exitbot.frontend.components.welcome import render_welcome, render_completion
from exitbot.frontend.components.chat_interface import render_chat_interface, create_typing_effect
from exitbot.frontend.components.dashboard_cards import (
    render_metric_card,
    render_interview_completion_chart,
    render_time_series_chart,
    render_department_breakdown,
    render_sentiment_gauge
) 
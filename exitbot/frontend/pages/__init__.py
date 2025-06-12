"""
Page-level components for the ExitBot HR app.
"""

import sys
import os

# Add parent directory to path to make imports work
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from exitbot.frontend.pages.dashboard import render_dashboard
from exitbot.frontend.pages.interviews import render_interviews
from exitbot.frontend.pages.reports import render_reports
from exitbot.frontend.pages.settings import render_settings

__all__ = [
    'render_dashboard',
    'render_interviews',
    'render_reports',
    'render_settings'
] 
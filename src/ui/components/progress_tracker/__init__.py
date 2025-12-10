"""
Progress Tracker component for Vulcan.

Tracks user progress through demo module completion tasks:
- Data indexing
- Query validation
- Tool deployment
- Agent deployment
"""

from .header import render_progress_header
from .service import ProgressTrackingService, get_progress_service

__all__ = [
    "render_progress_header",
    "ProgressTrackingService",
    "get_progress_service",
]

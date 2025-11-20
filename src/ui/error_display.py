"""
Error display utilities for Streamlit UI

Provides consistent, user-friendly error messages across the application.
"""

import streamlit as st
import logging
from src.exceptions import VulcanException

logger = logging.getLogger(__name__)


def display_error(error: Exception, title: str = "Error", show_technical_details: bool = True):
    """
    Display an error in the Streamlit UI with user-friendly formatting
    
    Args:
        error: The exception to display
        title: Title for the error message
        show_technical_details: Whether to show technical details in an expander
    """
    # Display title
    st.error(f"🚨 {title}")
    
    # Check if it's one of our custom exceptions
    if isinstance(error, VulcanException):
        # Use the formatted display message
        st.markdown(error.get_display_message())
        
        # Log the full error
        logger.error(f"{title}: {error.user_message}", exc_info=True)
        
    else:
        # Generic error display
        error_msg = str(error)
        st.markdown(f"**Error:** {error_msg}")
        
        if show_technical_details:
            with st.expander("📋 Technical Details"):
                st.code(error_msg)
                st.caption("Check the application logs for more information.")
        
        logger.error(f"{title}: {error_msg}", exc_info=True)


def display_warning(message: str, title: str = "Warning"):
    """
    Display a warning message in the Streamlit UI
    
    Args:
        message: The warning message to display
        title: Title for the warning
    """
    st.warning(f"⚠️ **{title}**")
    st.markdown(message)
    logger.warning(f"{title}: {message}")


def display_success(message: str, title: str = "Success"):
    """
    Display a success message in the Streamlit UI
    
    Args:
        message: The success message to display
        title: Title for the success message
    """
    st.success(f"✅ **{title}**")
    st.markdown(message)
    logger.info(f"{title}: {message}")


def display_info(message: str, title: str = None):
    """
    Display an info message in the Streamlit UI
    
    Args:
        message: The info message to display
        title: Optional title for the info message
    """
    if title:
        st.info(f"ℹ️ **{title}**")
        st.markdown(message)
    else:
        st.info(message)
    
    logger.info(f"{title or 'Info'}: {message}")


def wrap_with_error_handling(func, error_title: str = "Operation Failed"):
    """
    Decorator/wrapper to add error handling to a function
    
    Args:
        func: Function to wrap
        error_title: Title to use for error display
        
    Returns:
        Result of function or None if error occurs
    """
    try:
        return func()
    except Exception as e:
        display_error(e, title=error_title)
        return None


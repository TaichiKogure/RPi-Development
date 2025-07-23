"""
Helper Module for Web Interface

This module contains utility functions for the web interface.
"""

import logging
import datetime

# Configure logging
logger = logging.getLogger(__name__)

def format_timestamp(timestamp, format_str="%Y-%m-%d %H:%M:%S"):
    """
    Format a timestamp for display.
    
    Args:
        timestamp (str or datetime): The timestamp to format
        format_str (str, optional): The format string to use. Defaults to "%Y-%m-%d %H:%M:%S".
        
    Returns:
        str: The formatted timestamp
    """
    try:
        if isinstance(timestamp, str):
            # Try to parse the timestamp
            dt = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            return dt.strftime(format_str)
        elif isinstance(timestamp, datetime.datetime):
            return timestamp.strftime(format_str)
        else:
            return str(timestamp)
    except Exception as e:
        logger.error(f"Error formatting timestamp: {e}")
        return str(timestamp)

def format_value(value, precision=2, unit=""):
    """
    Format a value for display.
    
    Args:
        value (float or str): The value to format
        precision (int, optional): The number of decimal places. Defaults to 2.
        unit (str, optional): The unit to append. Defaults to "".
        
    Returns:
        str: The formatted value
    """
    try:
        if value is None:
            return "-"
        
        if isinstance(value, (int, float)):
            # Format as number with specified precision
            formatted = f"{value:.{precision}f}"
            # Remove trailing zeros after decimal point
            if "." in formatted:
                formatted = formatted.rstrip("0").rstrip(".")
            
            # Add unit if specified
            if unit:
                formatted += f" {unit}"
            
            return formatted
        else:
            # Return as string
            return str(value)
    except Exception as e:
        logger.error(f"Error formatting value: {e}")
        return str(value)
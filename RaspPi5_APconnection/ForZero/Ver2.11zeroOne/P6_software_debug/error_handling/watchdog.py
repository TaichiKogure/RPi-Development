#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simplified Watchdog for Raspberry Pi Pico 2W - Debug Version 4.19
Version: 4.19.0-debug

This module provides a simplified interface to the P6_watchdog_debug module.
It's intended to be imported by main.py on the Pico 2W.
"""

from P6_watchdog_debug import Watchdog, handle_error, log_error, sync_all_files, reset_device, safe_reset, init_error_log

# These functions are provided for backwards compatibility
def init_watchdog(timeout_ms=8000):
    """Initialize the watchdog timer.
    
    Args:
        timeout_ms (int): Timeout in milliseconds before reset
        
    Returns:
        Watchdog: Watchdog object
    """
    return Watchdog(timeout_ms=timeout_ms)

def feed_watchdog(watchdog):
    """Feed the watchdog to prevent reset.
    
    Args:
        watchdog (Watchdog): Watchdog object
    """
    watchdog.feed()

def handle_exception(error, context=None):
    """Handle an exception.
    
    Args:
        error (Exception): The error that occurred
        context (dict): Additional context information
    """
    handle_error(error, context)

def initialize_error_log():
    """Initialize the error log file.
    
    Returns:
        bool: True if successful, False otherwise
    """
    return init_error_log()
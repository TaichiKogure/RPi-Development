#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi Pico 2W Watchdog and Error Handling - Solo Version 4.44
Version: 4.44.0-solo

This module provides watchdog and error handling functionality for the
Raspberry Pi Pico 2W (P3) environmental monitoring system.

Features:
- Hardware watchdog timer to automatically reset on system freeze
- Error logging to file
- Safe file synchronization to prevent data corruption
- Configurable error handling behavior

Usage:
    This file should be imported by main.py on the Pico 2W.
"""

import time
import machine
import os
import sys
import gc

# Constants
ERROR_LOG_FILE = "/error_log_p3_solo44.txt"  # Changed from P2 to P3
MAX_LOG_SIZE = 10240  # 10KB max log file size
LOG_TO_FILE = True    # Set to True to log to file instead of printing

class Watchdog:
    """Hardware watchdog timer to automatically reset the device if it freezes."""
    
    def __init__(self, timeout_ms=8000):
        """Initialize the watchdog timer.
        
        Args:
            timeout_ms (int): Timeout in milliseconds before reset
        """
        self.wdt = machine.WDT(timeout=timeout_ms)
        self.last_feed = time.time()
        self.timeout_ms = timeout_ms
        print(f"Watchdog initialized with {timeout_ms}ms timeout")
    
    def feed(self):
        """Feed the watchdog to prevent reset."""
        self.wdt.feed()
        self.last_feed = time.time()
    
    def get_time_since_feed(self):
        """Get time since last feed in seconds."""
        return time.time() - self.last_feed
    
    def is_close_to_timeout(self, margin_percent=20):
        """Check if we're close to watchdog timeout.
        
        Args:
            margin_percent (int): Percentage of timeout to consider as "close"
            
        Returns:
            bool: True if close to timeout, False otherwise
        """
        time_since_feed = self.get_time_since_feed() * 1000  # Convert to ms
        margin = self.timeout_ms * margin_percent / 100
        return time_since_feed > (self.timeout_ms - margin)

def handle_error(error, context=None):
    """Handle an error by logging it to file.
    
    Args:
        error (Exception): The error that occurred
        context (dict): Additional context information
    """
    try:
        # Force garbage collection to free memory
        gc.collect()
        
        # Format error message
        error_msg = f"[ERROR] {time.time()}: {type(error).__name__}: {str(error)}"
        if context:
            context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
            error_msg += f" | Context: {context_str}"
        
        # Print error to console
        print(error_msg)
        
        # Log to file if enabled
        if LOG_TO_FILE:
            try:
                # Check if log file exists and is too large
                try:
                    stat = os.stat(ERROR_LOG_FILE)
                    if stat[6] > MAX_LOG_SIZE:
                        # Truncate file if too large
                        with open(ERROR_LOG_FILE, "w") as f:
                            f.write(f"Log truncated at {time.time()} due to size limit\n")
                except:
                    # File doesn't exist or can't be accessed
                    pass
                
                # Append error to log file
                with open(ERROR_LOG_FILE, "a") as f:
                    f.write(error_msg + "\n")
                
                # Sync file system to ensure error is written
                sync_all_files()
            except Exception as e:
                # If file logging fails, print to console
                print(f"Error logging to file: {e}")
        
    except Exception as e:
        # If error handling fails, print to console
        print(f"Error during error handling: {e}")

def sync_all_files():
    """Sync all files to prevent data corruption."""
    try:
        os.sync()
    except:
        # os.sync() might not be available on all MicroPython ports
        pass

def reset_device(reason="Unknown", delay=3):
    """Reset the device safely.
    
    Args:
        reason (str): Reason for reset
        delay (int): Delay in seconds before reset
    """
    print(f"Performing safe device reset: {reason}")
    print(f"Resetting in {delay} seconds...")
    
    # Log reset reason if logging is enabled
    if LOG_TO_FILE:
        try:
            with open(ERROR_LOG_FILE, "a") as f:
                f.write(f"RESET: {reason} at {time.time()}\n")
        except:
            pass
    
    # Sync files before reset
    sync_all_files()
    
    # Wait a moment for any pending operations
    for i in range(delay):
        print(f"{delay-i} seconds until reset...")
        time.sleep(1)
        # Allow background processing during delay
        machine.idle()
    
    # Final message before reset
    print("RESETTING NOW")
    
    # Reset the device
    machine.reset()

def safe_execution(func, args=None, kwargs=None, error_context=None, max_retries=3):
    """Execute a function safely with error handling and retries.
    
    Args:
        func (function): Function to execute
        args (tuple): Positional arguments for the function
        kwargs (dict): Keyword arguments for the function
        error_context (dict): Context information for error handling
        max_retries (int): Maximum number of retry attempts
        
    Returns:
        The return value of the function, or None if all retries fail
    """
    if args is None:
        args = ()
    if kwargs is None:
        kwargs = {}
    if error_context is None:
        error_context = {"function": func.__name__}
    
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            handle_error(e, {**error_context, "attempt": attempt + 1})
            if attempt < max_retries - 1:
                print(f"Retrying {func.__name__} ({attempt + 1}/{max_retries})...")
                time.sleep(1)  # Wait before retry
                # Allow background processing during delay
                machine.idle()
    
    return None
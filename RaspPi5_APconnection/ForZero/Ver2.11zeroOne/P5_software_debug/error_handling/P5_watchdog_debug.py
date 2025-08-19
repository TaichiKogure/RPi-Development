#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi Pico 2W Watchdog and Error Handling - Debug Version 4.19
Version: 4.19.0-debug

This module provides watchdog and error handling functionality for the
Raspberry Pi Pico 2W (P5) environmental monitoring system.

Features:
- Hardware watchdog timer to automatically reset on system freeze
- Error logging to file
- Safe file synchronization to prevent data corruption
- Configurable error handling behavior
- Improved error handling for Thonny compatibility

Usage:
    This file should be imported by main.py on the Pico 2W.
"""

import time
import machine
import os
import sys
import gc

# Constants
ERROR_LOG_FILE = "/error_log_p5_solo.txt"  # Error log file path
MAX_LOG_SIZE = 10240  # 10KB max log file size
LOG_TO_FILE = False   # Set to True to log to file instead of printing

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
        print(f"Error in error handler: {e}")

def log_error(error, context=None, log_file=ERROR_LOG_FILE, log_to_file=LOG_TO_FILE):
    """Log an error to file and console.
    
    Args:
        error (Exception): The error that occurred
        context (dict): Additional context information
        log_file (str): Path to log file
        log_to_file (bool): Whether to log to file
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
        if log_to_file:
            try:
                # Check if log file exists and is too large
                try:
                    stat = os.stat(log_file)
                    if stat[6] > MAX_LOG_SIZE:
                        # Truncate file if too large
                        with open(log_file, "w") as f:
                            f.write(f"Log truncated at {time.time()} due to size limit\n")
                except:
                    # File doesn't exist or can't be accessed
                    pass
                
                # Append error to log file
                with open(log_file, "a") as f:
                    f.write(error_msg + "\n")
                
                # Sync file system to ensure error is written
                sync_all_files()
            except Exception as e:
                # If file logging fails, print to console
                print(f"Error logging to file: {e}")
        
    except Exception as e:
        # If error handling fails, print to console
        print(f"Error in error handler: {e}")

def sync_all_files():
    """Sync all files to ensure they're written to flash."""
    try:
        os.sync()
    except:
        # os.sync() might not be available on all MicroPython ports
        pass

def reset_device(delay=3, reason="Unknown"):
    """Reset the device with a delay.
    
    Args:
        delay (int): Delay in seconds before reset
        reason (str): Reason for reset
    """
    print(f"Resetting device in {delay} seconds. Reason: {reason}")
    
    # Ensure all pending writes are flushed
    sync_all_files()
    
    # Wait for the specified delay
    for i in range(delay, 0, -1):
        print(f"Resetting in {i}...")
        time.sleep(1)
    
    # Reset the device
    print("Performing reset now...")
    machine.reset()

def safe_reset(delay=3, reason="Unknown"):
    """Safely reset the device with a delay.
    
    Args:
        delay (int): Delay in seconds before reset
        reason (str): Reason for reset
    """
    # Log the reset
    if LOG_TO_FILE:
        try:
            with open(ERROR_LOG_FILE, "a") as f:
                f.write(f"[RESET] {time.time()}: {reason}\n")
            
            # Sync file system to ensure log is written
            sync_all_files()
        except:
            # If logging fails, continue with reset
            pass
    
    # Reset the device
    reset_device(delay, reason)

def init_error_log():
    """Initialize the error log file."""
    if LOG_TO_FILE:
        try:
            with open(ERROR_LOG_FILE, "w") as f:
                f.write(f"Error log initialized at {time.time()}\n")
            
            # Sync file system to ensure log is written
            sync_all_files()
            
            print(f"Error log initialized: {ERROR_LOG_FILE}")
            return True
        except Exception as e:
            print(f"Failed to initialize error log: {e}")
            return False
    
    return True
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi Pico 2W Watchdog and Error Handling - Debug Version 4.25
Version: 4.25.0-debug

This module provides watchdog and error handling functionality for the
Raspberry Pi Pico 2W (P4) environmental monitoring system.

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
ERROR_LOG_FILE = "/error_log_p4_solo.txt"
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
    
    def disable(self):
        """Disable the watchdog (if possible).
        
        Note: On some platforms, once enabled, the watchdog cannot be disabled.
        """
        try:
            # This is a no-op on platforms where WDT can't be disabled
            # But we include it for future compatibility
            print("Attempting to disable watchdog (may not be supported)")
        except:
            print("Failed to disable watchdog (not supported)")

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
        # Last resort error handling
        print(f"Error in error handler: {e}")

def sync_all_files():
    """Sync all files to prevent data corruption."""
    try:
        os.sync()
    except:
        # os.sync() not available on all platforms
        pass

def reset_device(reason="Unknown", delay=3):
    """Reset the device after logging the reason and waiting for a delay.
    
    Args:
        reason (str): Reason for reset
        delay (int): Delay in seconds before reset
    """
    try:
        # Format reset message
        reset_msg = f"[RESET] {time.time()}: {reason}"
        
        # Print reset message to console
        print(reset_msg)
        
        # Log to file if enabled
        if LOG_TO_FILE:
            try:
                with open(ERROR_LOG_FILE, "a") as f:
                    f.write(reset_msg + "\n")
                
                # Sync file system to ensure message is written
                sync_all_files()
            except:
                # If file logging fails, just continue
                pass
        
        # Wait for delay
        print(f"Resetting in {delay} seconds...")
        time.sleep(delay)
        
        # Reset device
        machine.reset()
    except Exception as e:
        # Last resort error handling
        print(f"Error in reset_device: {e}")
        
        # Force reset
        machine.reset()

def monitor_memory(threshold_percent=90, action="log"):
    """Monitor memory usage and take action if it exceeds threshold.
    
    Args:
        threshold_percent (int): Percentage of memory usage to trigger action
        action (str): Action to take ("log", "gc", or "reset")
        
    Returns:
        dict: Memory usage information
    """
    try:
        # Force garbage collection
        gc.collect()
        
        # Get memory usage
        free_mem = gc.mem_free()
        allocated_mem = gc.mem_alloc()
        total_mem = free_mem + allocated_mem
        mem_percent = (allocated_mem / total_mem) * 100
        
        # Create memory info dict
        mem_info = {
            "free": free_mem,
            "allocated": allocated_mem,
            "total": total_mem,
            "percent": mem_percent
        }
        
        # Check if memory usage exceeds threshold
        if mem_percent > threshold_percent:
            # Format memory message
            mem_msg = f"[MEMORY] {time.time()}: Memory usage {mem_percent:.1f}% exceeds threshold {threshold_percent}%"
            
            # Print memory message to console
            print(mem_msg)
            
            # Log to file if enabled
            if LOG_TO_FILE:
                try:
                    with open(ERROR_LOG_FILE, "a") as f:
                        f.write(mem_msg + "\n")
                    
                    # Sync file system to ensure message is written
                    sync_all_files()
                except:
                    # If file logging fails, just continue
                    pass
            
            # Take action based on action parameter
            if action == "gc":
                # Force garbage collection
                gc.collect()
            elif action == "reset":
                # Reset device
                reset_device(reason=f"Memory usage {mem_percent:.1f}% exceeds threshold {threshold_percent}%")
        
        return mem_info
    except Exception as e:
        # Last resort error handling
        print(f"Error in monitor_memory: {e}")
        
        # Return empty dict
        return {}
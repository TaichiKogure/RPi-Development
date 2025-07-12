#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi Pico 2W Watchdog and Error Handling - Debug Version 4.18
Version: 4.18.0-debug

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
ERROR_LOG_FILE = "/error_log_p3_solo.txt"
MAX_LOG_SIZE = 10240  # 10KB max log file size

class Watchdog:
    """Hardware watchdog timer to automatically reset the device if it freezes."""
    
    def __init__(self, timeout_ms=8000):
        """Initialize the watchdog timer.
        
        Args:
            timeout_ms (int): Timeout in milliseconds before reset
        """
        self.wdt = machine.WDT(timeout=timeout_ms)
        self.last_feed = time.time()
        print(f"Watchdog initialized with {timeout_ms}ms timeout")
    
    def feed(self):
        """Feed the watchdog to prevent reset."""
        self.wdt.feed()
        self.last_feed = time.time()
    
    def get_time_since_feed(self):
        """Get time since last feed in seconds."""
        return time.time() - self.last_feed

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
        # If error handling fails, print to console
        print(f"Error during error handling: {e}")

def sync_all_files():
    """Sync all files to prevent data corruption."""
    try:
        os.sync()
    except:
        # os.sync() might not be available on all MicroPython ports
        pass

def reset_device():
    """Reset the device safely."""
    print("Performing safe device reset...")
    
    # Sync files before reset
    sync_all_files()
    
    # Wait a moment for any pending operations
    time.sleep(1)
    
    # Reset the device
    machine.reset()

# Example usage
if __name__ == "__main__":
    try:
        print("=== P3 Watchdog Debug Test (Ver 4.18.0) ===")
        
        # Initialize watchdog
        watchdog = Watchdog(timeout_ms=8000)
        
        # Test error handling
        try:
            print("Testing error handling...")
            raise ValueError("Test error")
        except Exception as e:
            handle_error(e, {"phase": "test", "test_id": 1})
        
        # Feed watchdog in a loop
        print("Feeding watchdog in a loop...")
        for i in range(10):
            print(f"Feed {i+1}/10")
            watchdog.feed()
            time.sleep(0.5)
        
        print("Test complete!")
        
    except Exception as e:
        print(f"Error: {e}")
        handle_error(e, {"phase": "main"})
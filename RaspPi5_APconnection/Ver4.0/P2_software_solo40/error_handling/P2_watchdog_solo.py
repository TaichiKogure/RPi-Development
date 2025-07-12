# -*- coding: utf-8 -*-
"""
Watchdog and Error Handling for Raspberry Pi Pico 2W - Solo Version 4.0.0
Version: 4.0.0-solo

This module provides watchdog and error handling functionality for the Raspberry Pi Pico 2W,
ensuring that the device can recover from errors and continue operating without manual intervention.

Features:
- Hardware watchdog timer to reset the device if it hangs
- Error logging to help diagnose issues
- Automatic restart on critical errors
- Configurable error handling strategies
- LED status indicators for error conditions
- Improved log file handling to prevent data loss during reset
- Safe reset procedure to ensure logs are properly saved
- Enhanced sync_all_files function for more reliable data persistence

Requirements:
- MicroPython for Raspberry Pi Pico W
- machine library

Usage:
    import P2_watchdog_solo
    # Initialize watchdog with 8-second timeout
    wdt = P2_watchdog_solo.Watchdog(timeout_ms=8000)
    
    # In main loop
    try:
        # Your code here
        wdt.feed()  # Feed the watchdog to prevent reset
    except Exception as e:
        P2_watchdog_solo.handle_error(e)
"""

import time
import machine
from machine import Pin, WDT
import micropython
import sys
import os
import gc

# Allocate memory for emergency exception buffer
micropython.alloc_emergency_exception_buf(100)

# Status LED
LED_PIN = 25  # Onboard LED on Pico W

# Error codes
ERROR_CODES = {
    "SENSOR_ERROR": 1,
    "WIFI_ERROR": 2,
    "MEMORY_ERROR": 3,
    "TIMEOUT_ERROR": 4,
    "CO2_SENSOR_ERROR": 5,  # New error code for CO2 sensor
    "UNKNOWN_ERROR": 9
}

class Watchdog:
    """Class to manage the hardware watchdog timer."""
    
    def __init__(self, timeout_ms=8000, led_pin=LED_PIN):
        """Initialize the watchdog timer.
        
        Args:
            timeout_ms (int): Watchdog timeout in milliseconds
            led_pin (int): LED pin number for status indication
        """
        self.led = Pin(led_pin, Pin.OUT)
        self.led.off()
        
        # Initialize hardware watchdog
        try:
            self.wdt = WDT(timeout=timeout_ms)
            self.enabled = True
            print(f"Watchdog initialized with {timeout_ms}ms timeout")
        except Exception as e:
            self.enabled = False
            print(f"Failed to initialize watchdog: {e}")
    
    def feed(self):
        """Feed the watchdog to prevent reset."""
        if self.enabled:
            self.wdt.feed()
    
    def blink_led(self, count=1, duration=0.1):
        """Blink the LED to indicate activity.
        
        Args:
            count (int): Number of blinks
            duration (float): Duration of each blink in seconds
        """
        for _ in range(count):
            self.led.on()
            time.sleep(duration)
            self.led.off()
            time.sleep(duration)

def sync_all_files():
    """Ensure all file operations are completed and synced to flash.
    
    This function attempts to ensure that all pending file operations
    are completed before a reset by forcing a garbage collection and
    syncing the filesystem if possible.
    
    Returns:
        bool: True if sync operations were successful, False otherwise
    """
    try:
        print("Starting file sync process...")
        
        # Force garbage collection to free up memory and close any
        # resources that might be pending collection
        gc.collect()
        print("Garbage collection completed")
        
        # Try to sync the filesystem if the function exists
        # (not all MicroPython ports have this)
        if hasattr(os, 'sync'):
            os.sync()
            print("Filesystem synced using os.sync()")
        else:
            print("os.sync not available, using alternative methods")
            
            # Alternative approach: write a small file to force a sync
            try:
                # First, try to close any open files
                for i in range(3):  # Standard file descriptors
                    try:
                        os.close(i)
                    except:
                        pass
                
                # Write a sync marker file
                with open("/sync_marker.txt", "w") as f:
                    f.write(f"sync_{time.time()}")
                    # Explicitly flush the file
                    if hasattr(f, 'flush'):
                        f.flush()
                
                # Read it back to ensure write completed
                with open("/sync_marker.txt", "r") as f:
                    f.read()
                
                print("Sync marker file written and read back")
            except Exception as e:
                print(f"Sync marker file operation failed: {e}")
        
        # Small delay to allow any pending flash operations to complete
        print("Waiting for flash operations to complete...")
        time.sleep(1.0)  # Increased from 0.5 to 1.0 seconds
        print("File sync process completed")
        return True
    
    except Exception as e:
        print(f"Error during sync_all_files: {e}")
        return False

class ErrorLogger:
    """Class to log errors for later analysis."""
    
    def __init__(self, log_file="/error_log_solo.txt", max_logs=20):  # Increased from 10 to 20
        """Initialize the error logger.
        
        Args:
            log_file (str): Path to the log file
            max_logs (int): Maximum number of error logs to keep
        """
        self.log_file = log_file
        self.max_logs = max_logs
    
    def log_error(self, error_type, error_message, additional_info=None):
        """Log an error to the file.
        
        Args:
            error_type (str): Type of error
            error_message (str): Error message
            additional_info (dict): Additional information about the error
            
        Returns:
            bool: True if error was successfully logged, False otherwise
        """
        try:
            # Create timestamp
            timestamp = time.localtime()
            time_str = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
                timestamp[0], timestamp[1], timestamp[2],
                timestamp[3], timestamp[4], timestamp[5]
            )
            
            # Format error message
            log_entry = f"[{time_str}] {error_type}: {error_message}"
            if additional_info:
                log_entry += f" | {additional_info}"
            
            # Read existing logs
            logs = []
            try:
                with open(self.log_file, "r") as f:
                    logs = f.readlines()
            except:
                # File doesn't exist or other error, start with empty log
                pass
            
            # Add new log and limit to max_logs
            logs.append(log_entry + "\n")
            if len(logs) > self.max_logs:
                logs = logs[-self.max_logs:]
            
            # Write logs back to file with explicit flush
            with open(self.log_file, "w") as f:
                f.writelines(logs)
                # Explicitly flush to ensure data is written
                if hasattr(f, 'flush'):
                    f.flush()
            
            # Force sync to ensure data is saved to flash
            sync_all_files()
            
            print(f"Error logged: {log_entry}")
            return True
        
        except Exception as e:
            print(f"Failed to log error: {e}")
            return False

class ErrorHandler:
    """Class to handle errors and determine recovery actions."""
    
    def __init__(self, logger=None, led_pin=LED_PIN):
        """Initialize the error handler.
        
        Args:
            logger (ErrorLogger): Logger to record errors
            led_pin (int): LED pin number for error indication
        """
        self.logger = logger or ErrorLogger()
        self.led = Pin(led_pin, Pin.OUT)
        self.led.off()
        self.error_count = {}
        self.last_error_time = {}
        self.reset_threshold = 5  # Number of errors before reset
        self.error_window = 300  # Time window in seconds for counting errors
    
    def _classify_error(self, error):
        """Classify the error type.
        
        Args:
            error (Exception): The error to classify
            
        Returns:
            str: Error type
        """
        error_str = str(error).lower()
        
        if "mhz19c" in error_str or "co2" in error_str:
            return "CO2_SENSOR_ERROR"
        elif "sensor" in error_str or "i2c" in error_str or "bme680" in error_str:
            return "SENSOR_ERROR"
        elif "wifi" in error_str or "socket" in error_str or "network" in error_str or "connection" in error_str:
            return "WIFI_ERROR"
        elif "memory" in error_str or "allocation" in error_str:
            return "MEMORY_ERROR"
        elif "timeout" in error_str:
            return "TIMEOUT_ERROR"
        else:
            return "UNKNOWN_ERROR"
    
    def _should_reset(self, error_type):
        """Determine if the device should be reset based on error frequency.
        
        Args:
            error_type (str): Type of error
            
        Returns:
            bool: True if device should be reset, False otherwise
        """
        current_time = time.time()
        
        # Initialize counters if this is the first error of this type
        if error_type not in self.error_count:
            self.error_count[error_type] = 0
            self.last_error_time[error_type] = current_time
        
        # Reset counter if outside the error window
        if current_time - self.last_error_time[error_type] > self.error_window:
            self.error_count[error_type] = 0
        
        # Increment counter and update time
        self.error_count[error_type] += 1
        self.last_error_time[error_type] = current_time
        
        # Check if threshold is exceeded
        return self.error_count[error_type] >= self.reset_threshold
    
    def handle_error(self, error, additional_info=None):
        """Handle an error and determine recovery action.
        
        Args:
            error (Exception): The error to handle
            additional_info (dict): Additional information about the error
            
        Returns:
            str: Action taken ("logged", "reset")
        """
        # Classify error
        error_type = self._classify_error(error)
        error_code = ERROR_CODES.get(error_type, ERROR_CODES["UNKNOWN_ERROR"])
        
        # Log error
        self.logger.log_error(error_type, str(error), additional_info)
        
        # Indicate error with LED
        self._blink_error_code(error_code)
        
        # Check if we should reset
        if self._should_reset(error_type):
            print(f"Too many {error_type} errors. Resetting device...")
            time.sleep(1)
            return self.reset_device(delay=15)  # Increased from 1 to 15 seconds
        
        return "logged"
    
    def _blink_error_code(self, code):
        """Blink the LED to indicate error code.
        
        Args:
            code (int): Error code to blink
        """
        # Turn off LED
        self.led.off()
        time.sleep(0.5)
        
        # Blink code
        for _ in range(code):
            self.led.on()
            time.sleep(0.2)
            self.led.off()
            time.sleep(0.2)
        
        time.sleep(0.5)
    
    def reset_device(self, delay=15):  # Increased from 1 to 15 seconds
        """Reset the device safely, ensuring logs are saved.
        
        Args:
            delay (int): Delay in seconds before reset
            
        Returns:
            str: Action taken ("reset")
        """
        print(f"Preparing to reset device in {delay} seconds...")
        
        # Log the reset event
        self.logger.log_error("SYSTEM", "Device reset requested", {"reason": "Too many errors", "delay": delay})
        
        # Rapid blink to indicate imminent reset
        for _ in range(5):
            self.led.on()
            time.sleep(0.1)
            self.led.off()
            time.sleep(0.1)
        
        # Print countdown
        for i in range(delay, 0, -1):
            if i % 5 == 0 or i <= 3:  # Print at 5-second intervals and final 3 seconds
                print(f"{i} seconds until reset...")
            
            # Blink LED during countdown (slow pattern)
            if i % 2 == 0:
                self.led.on()
            else:
                self.led.off()
                
            time.sleep(1)
        
        # Ensure all files are synced before reset
        print("Syncing files before reset...")
        sync_all_files()
        
        # Final confirmation and reset
        print("Reset now!")
        
        # One final long blink to indicate reset
        self.led.on()
        time.sleep(0.5)
        self.led.off()
        
        # Small delay to ensure LED state is visible
        time.sleep(0.2)
        
        # Reset the device
        machine.reset()
        
        # This will never be reached due to reset
        return "reset"

# Global instances
error_logger = ErrorLogger()
error_handler = ErrorHandler(error_logger)

def handle_error(error, additional_info=None):
    """Global function to handle errors.
    
    Args:
        error (Exception): The error to handle
        additional_info (dict): Additional information about the error
        
    Returns:
        str: Action taken ("logged", "reset")
    """
    return error_handler.handle_error(error, additional_info)

# Example usage
if __name__ == "__main__":
    try:
        # Initialize watchdog
        wdt = Watchdog(timeout_ms=8000)
        
        print("Testing watchdog and error handling (Solo Version 4.0.0)...")
        
        # Test error handling
        try:
            # Simulate an error
            raise ValueError("Test error")
        except Exception as e:
            handle_error(e, {"test": True})
        
        # Main loop
        count = 0
        while True:
            # Feed the watchdog
            wdt.feed()
            
            # Blink LED to show activity
            wdt.blink_led(1, 0.1)
            
            # Simulate occasional errors
            count += 1
            if count % 10 == 0:
                error_types = ["SENSOR_ERROR", "WIFI_ERROR", "CO2_SENSOR_ERROR", "UNKNOWN_ERROR"]
                error_type = error_types[count % len(error_types)]
                try:
                    raise Exception(f"Simulated {error_type}")
                except Exception as e:
                    handle_error(e)
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("Test stopped by user")
    except Exception as e:
        print(f"Unexpected error: {e}")
        handle_error(e)
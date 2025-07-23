# -*- coding: utf-8 -*-
"""
Watchdog and Error Handling for Raspberry Pi Pico 2W - Solo Version 3
Version: 3.0.0-solo

This module provides watchdog and error handling functionality for the Raspberry Pi Pico 2W,
ensuring that the device can recover from errors and continue operating without manual intervention.

Features:
- Hardware watchdog timer to reset the device if it hangs
- Error logging to help diagnose issues
- Automatic restart on critical errors
- Configurable error handling strategies
- LED status indicators for error conditions

Requirements:
- MicroPython for Raspberry Pi Pico W
- machine library

Usage:
    import watchdog_solo
    # Initialize watchdog with 8-second timeout
    wdt = watchdog_solo.Watchdog(timeout_ms=8000)
    
    # In main loop
    try:
        # Your code here
        wdt.feed()  # Feed the watchdog to prevent reset
    except Exception as e:
        watchdog_solo.handle_error(e)
"""

import time
import machine
from machine import Pin, WDT
import micropython
import sys
import os

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

class ErrorLogger:
    """Class to log errors for later analysis."""
    
    def __init__(self, log_file="/error_log_solo.txt", max_logs=10):
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
            try:
                with open(self.log_file, "r") as f:
                    logs = f.readlines()
            except:
                logs = []
            
            # Add new log and limit to max_logs
            logs.append(log_entry + "\n")
            if len(logs) > self.max_logs:
                logs = logs[-self.max_logs:]
            
            # Write logs back to file
            with open(self.log_file, "w") as f:
                f.writelines(logs)
            
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
        
        if "sensor" in error_str or "i2c" in error_str or "bme680" in error_str:
            return "SENSOR_ERROR"
        elif "wifi" in error_str or "socket" in error_str or "network" in error_str:
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
            return self.reset_device()
        
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
    
    def reset_device(self, delay=1):
        """Reset the device.
        
        Args:
            delay (int): Delay in seconds before reset
            
        Returns:
            str: Action taken ("reset")
        """
        print(f"Resetting device in {delay} seconds...")
        
        # Rapid blink to indicate imminent reset
        for _ in range(5):
            self.led.on()
            time.sleep(0.1)
            self.led.off()
            time.sleep(0.1)
        
        time.sleep(delay)
        machine.reset()
        return "reset"  # This will never be reached due to reset

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
        
        print("Testing watchdog and error handling (Solo Version 3)...")
        
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
                error_type = ["SENSOR_ERROR", "WIFI_ERROR", "UNKNOWN_ERROR"][count % 3]
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
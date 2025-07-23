# -*- coding: utf-8 -*-
"""
Watchdog and Error Handling for Raspberry Pi Pico 2W (P3) - Debug Version 4.15
Version: 4.15.0-debug

This module provides watchdog and error handling functionality for the Raspberry Pi Pico 2W (P3),
ensuring that the device can recover from errors and continue operating without manual intervention.

Features:
- Enhanced debugging for error handling and watchdog
- Configurable watchdog timeout and reset behavior
- Detailed error logging with multiple verbosity levels
- Safe reset procedure with configurable delay
- Improved file synchronization to prevent data loss
- LED status indicators for different error types
- Ability to disable automatic reset for debugging
- Detailed error statistics and diagnostics

Requirements:
- MicroPython for Raspberry Pi Pico W
- machine library

Usage:
    import P3_watchdog_debug
    # Initialize watchdog with 8-second timeout
    wdt = P3_watchdog_debug.Watchdog(timeout_ms=8000, auto_reset=True)
    
    # In main loop
    try:
        # Your code here
        wdt.feed()  # Feed the watchdog to prevent reset
    except Exception as e:
        P3_watchdog_debug.handle_error(e, auto_reset=False)  # Disable auto-reset for debugging
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

# Debug levels
DEBUG_NONE = 0    # No debug output
DEBUG_BASIC = 1   # Basic error information
DEBUG_DETAILED = 2  # Detailed error information
DEBUG_VERBOSE = 3  # Very verbose output including all error details

# Error codes
ERROR_CODES = {
    "SENSOR_ERROR": 1,
    "WIFI_ERROR": 2,
    "MEMORY_ERROR": 3,
    "TIMEOUT_ERROR": 4,
    "CO2_SENSOR_ERROR": 5,
    "I2C_ERROR": 6,
    "UART_ERROR": 7,
    "FILE_ERROR": 8,
    "UNKNOWN_ERROR": 9
}

class Watchdog:
    """Class to manage the hardware watchdog timer with enhanced debugging."""
    
    def __init__(self, timeout_ms=8000, led_pin=LED_PIN, debug_level=DEBUG_BASIC, auto_reset=True):
        """Initialize the watchdog timer.
        
        Args:
            timeout_ms (int): Watchdog timeout in milliseconds
            led_pin (int): LED pin number for status indication
            debug_level (int): Level of debug output (0-3)
            auto_reset (bool): Whether to automatically reset on watchdog timeout
        """
        self.led = Pin(led_pin, Pin.OUT)
        self.led.off()
        self.timeout_ms = timeout_ms
        self.feed_count = 0
        self.last_feed_time = time.time()
        self.debug_level = debug_level
        self.auto_reset = auto_reset
        self.wdt = None
        
        # Initialize hardware watchdog if auto_reset is enabled
        if self.auto_reset:
            try:
                self.wdt = WDT(timeout=timeout_ms)
                self.enabled = True
                self._debug_print(f"Watchdog initialized with {timeout_ms}ms timeout", DEBUG_BASIC)
                
                # Blink LED to indicate watchdog is active
                self.blink_led(3, 0.1)
            except Exception as e:
                self.enabled = False
                self._debug_print(f"Failed to initialize watchdog: {e}", DEBUG_BASIC)
        else:
            self.enabled = False
            self._debug_print("Watchdog disabled (auto_reset=False)", DEBUG_BASIC)
    
    def _debug_print(self, message, level=DEBUG_BASIC):
        """Print debug message if debug level is high enough.
        
        Args:
            message (str): Message to print
            level (int): Minimum debug level required to print this message
        """
        if self.debug_level >= level:
            print(f"[Watchdog Debug] {message}")
    
    def set_debug_level(self, level):
        """Set the debug level.
        
        Args:
            level (int): Debug level (0-3)
        """
        self.debug_level = level
        self._debug_print(f"Debug level set to {level}", DEBUG_BASIC)
    
    def set_auto_reset(self, auto_reset):
        """Set whether to automatically reset on watchdog timeout.
        
        Args:
            auto_reset (bool): Whether to auto-reset
        """
        # If changing from disabled to enabled, need to initialize watchdog
        if auto_reset and not self.auto_reset:
            try:
                self.wdt = WDT(timeout=self.timeout_ms)
                self.enabled = True
                self._debug_print(f"Watchdog enabled with {self.timeout_ms}ms timeout", DEBUG_BASIC)
                
                # Blink LED to indicate watchdog is active
                self.blink_led(3, 0.1)
            except Exception as e:
                self.enabled = False
                self._debug_print(f"Failed to initialize watchdog: {e}", DEBUG_BASIC)
        
        # If changing from enabled to disabled, can't disable hardware watchdog
        # but we can stop feeding it (which will cause a reset)
        elif not auto_reset and self.auto_reset:
            self._debug_print("Warning: Cannot disable hardware watchdog once enabled. Will stop feeding it.", DEBUG_BASIC)
        
        self.auto_reset = auto_reset
        self._debug_print(f"Auto-reset set to {auto_reset}", DEBUG_BASIC)
    
    def feed(self):
        """Feed the watchdog to prevent reset."""
        if self.enabled and self.wdt:
            self.wdt.feed()
            self.feed_count += 1
            self.last_feed_time = time.time()
            
            # Occasionally log feed count
            if self.feed_count % 100 == 0:
                self._debug_print(f"Watchdog fed {self.feed_count} times", DEBUG_DETAILED)
    
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
    
    def get_status(self):
        """Get the status of the watchdog.
        
        Returns:
            dict: Watchdog status information
        """
        return {
            "enabled": self.enabled,
            "auto_reset": self.auto_reset,
            "timeout_ms": self.timeout_ms,
            "feed_count": self.feed_count,
            "last_feed_time": self.last_feed_time,
            "time_since_last_feed": time.time() - self.last_feed_time,
            "debug_level": self.debug_level
        }

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
                with open("/sync_marker_p3_debug.txt", "w") as f:
                    f.write(f"sync_{time.time()}")
                    # Explicitly flush the file
                    if hasattr(f, 'flush'):
                        f.flush()
                
                # Read it back to ensure write completed
                with open("/sync_marker_p3_debug.txt", "r") as f:
                    f.read()
                
                print("Sync marker file written and read back")
            except Exception as e:
                print(f"Sync marker file operation failed: {e}")
        
        # Small delay to allow any pending flash operations to complete
        print("Waiting for flash operations to complete...")
        time.sleep(2.0)
        print("File sync process completed")
        return True
    
    except Exception as e:
        print(f"Error during sync_all_files: {e}")
        return False

class ErrorLogger:
    """Class to log errors for later analysis with enhanced debugging."""
    
    def __init__(self, log_file="/error_log_p3_debug.txt", max_logs=50, debug_level=DEBUG_BASIC):
        """Initialize the error logger.
        
        Args:
            log_file (str): Path to the log file
            max_logs (int): Maximum number of error logs to keep
            debug_level (int): Level of debug output (0-3)
        """
        self.log_file = log_file
        self.max_logs = max_logs
        self.log_count = 0
        self.debug_level = debug_level
        
        # Create log file if it doesn't exist
        try:
            with open(self.log_file, "a") as f:
                pass
            self._debug_print(f"Error log file initialized: {self.log_file}", DEBUG_BASIC)
        except Exception as e:
            self._debug_print(f"Failed to initialize error log file: {e}", DEBUG_BASIC)
    
    def _debug_print(self, message, level=DEBUG_BASIC):
        """Print debug message if debug level is high enough.
        
        Args:
            message (str): Message to print
            level (int): Minimum debug level required to print this message
        """
        if self.debug_level >= level:
            print(f"[Error Logger Debug] {message}")
    
    def set_debug_level(self, level):
        """Set the debug level.
        
        Args:
            level (int): Debug level (0-3)
        """
        self.debug_level = level
        self._debug_print(f"Debug level set to {level}", DEBUG_BASIC)
    
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
            
            self._debug_print(f"Logging error: {log_entry}", DEBUG_DETAILED)
            
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
            
            self.log_count += 1
            self._debug_print(f"Error logged successfully (total: {self.log_count})", DEBUG_BASIC)
            return True
        
        except Exception as e:
            self._debug_print(f"Failed to log error: {e}", DEBUG_BASIC)
            return False
    
    def get_logs(self, max_count=None):
        """Get the most recent error logs.
        
        Args:
            max_count (int): Maximum number of logs to return
            
        Returns:
            list: List of log entries
        """
        try:
            with open(self.log_file, "r") as f:
                logs = f.readlines()
            
            if max_count is not None and max_count > 0:
                return logs[-max_count:]
            return logs
        except Exception as e:
            self._debug_print(f"Failed to read logs: {e}", DEBUG_BASIC)
            return []
    
    def clear_logs(self):
        """Clear all error logs.
        
        Returns:
            bool: True if logs were successfully cleared, False otherwise
        """
        try:
            with open(self.log_file, "w") as f:
                pass
            self._debug_print("Error logs cleared", DEBUG_BASIC)
            return True
        except Exception as e:
            self._debug_print(f"Failed to clear logs: {e}", DEBUG_BASIC)
            return False

class ErrorHandler:
    """Class to handle errors and determine recovery actions with enhanced debugging."""
    
    def __init__(self, logger=None, led_pin=LED_PIN, debug_level=DEBUG_BASIC, auto_reset=True):
        """Initialize the error handler.
        
        Args:
            logger (ErrorLogger): Logger to record errors
            led_pin (int): LED pin number for error indication
            debug_level (int): Level of debug output (0-3)
            auto_reset (bool): Whether to automatically reset on critical errors
        """
        self.logger = logger or ErrorLogger(debug_level=debug_level)
        self.led = Pin(led_pin, Pin.OUT)
        self.led.off()
        self.error_count = {}
        self.last_error_time = {}
        self.reset_threshold = 5  # Number of errors before reset
        self.error_window = 300  # Time window in seconds for counting errors
        self.total_errors = 0
        self.debug_level = debug_level
        self.auto_reset = auto_reset
    
    def _debug_print(self, message, level=DEBUG_BASIC):
        """Print debug message if debug level is high enough.
        
        Args:
            message (str): Message to print
            level (int): Minimum debug level required to print this message
        """
        if self.debug_level >= level:
            print(f"[Error Handler Debug] {message}")
    
    def set_debug_level(self, level):
        """Set the debug level.
        
        Args:
            level (int): Debug level (0-3)
        """
        self.debug_level = level
        self.logger.set_debug_level(level)
        self._debug_print(f"Debug level set to {level}", DEBUG_BASIC)
    
    def set_auto_reset(self, auto_reset):
        """Set whether to automatically reset on critical errors.
        
        Args:
            auto_reset (bool): Whether to auto-reset
        """
        self.auto_reset = auto_reset
        self._debug_print(f"Auto-reset set to {auto_reset}", DEBUG_BASIC)
    
    def set_reset_threshold(self, threshold):
        """Set the number of errors before reset.
        
        Args:
            threshold (int): Number of errors before reset
        """
        self.reset_threshold = threshold
        self._debug_print(f"Reset threshold set to {threshold}", DEBUG_BASIC)
    
    def set_error_window(self, window):
        """Set the time window in seconds for counting errors.
        
        Args:
            window (int): Time window in seconds
        """
        self.error_window = window
        self._debug_print(f"Error window set to {window} seconds", DEBUG_BASIC)
    
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
        elif "i2c" in error_str:
            return "I2C_ERROR"
        elif "uart" in error_str:
            return "UART_ERROR"
        elif "sensor" in error_str or "bme680" in error_str:
            return "SENSOR_ERROR"
        elif "wifi" in error_str or "socket" in error_str or "network" in error_str or "connection" in error_str:
            return "WIFI_ERROR"
        elif "memory" in error_str or "allocation" in error_str:
            return "MEMORY_ERROR"
        elif "timeout" in error_str:
            return "TIMEOUT_ERROR"
        elif "file" in error_str or "open" in error_str or "read" in error_str or "write" in error_str:
            return "FILE_ERROR"
        else:
            return "UNKNOWN_ERROR"
    
    def _should_reset(self, error_type):
        """Determine if the device should be reset based on error frequency.
        
        Args:
            error_type (str): Type of error
            
        Returns:
            bool: True if device should be reset, False otherwise
        """
        # If auto-reset is disabled, never reset
        if not self.auto_reset:
            self._debug_print(f"Auto-reset disabled, not resetting for {error_type}", DEBUG_DETAILED)
            return False
        
        current_time = time.time()
        
        # Initialize counters if this is the first error of this type
        if error_type not in self.error_count:
            self.error_count[error_type] = 0
            self.last_error_time[error_type] = current_time
        
        # Reset counter if outside the error window
        if current_time - self.last_error_time[error_type] > self.error_window:
            self._debug_print(f"Error window expired for {error_type}, resetting counter", DEBUG_DETAILED)
            self.error_count[error_type] = 0
        
        # Increment counter and update time
        self.error_count[error_type] += 1
        self.last_error_time[error_type] = current_time
        self.total_errors += 1
        
        # Check if threshold is exceeded
        should_reset = self.error_count[error_type] >= self.reset_threshold
        if should_reset:
            self._debug_print(f"Reset threshold ({self.reset_threshold}) exceeded for {error_type}", DEBUG_BASIC)
        else:
            self._debug_print(f"Error count for {error_type}: {self.error_count[error_type]}/{self.reset_threshold}", DEBUG_DETAILED)
        
        return should_reset
    
    def handle_error(self, error, additional_info=None, auto_reset=None):
        """Handle an error and determine recovery action.
        
        Args:
            error (Exception): The error to handle
            additional_info (dict): Additional information about the error
            auto_reset (bool): Override the instance auto_reset setting for this error
            
        Returns:
            str: Action taken ("logged", "reset")
        """
        # Apply override if provided
        if auto_reset is not None:
            old_auto_reset = self.auto_reset
            self.set_auto_reset(auto_reset)
        
        # Classify error
        error_type = self._classify_error(error)
        error_code = ERROR_CODES.get(error_type, ERROR_CODES["UNKNOWN_ERROR"])
        
        self._debug_print(f"Handling error: {error_type} - {error}", DEBUG_BASIC)
        
        # Add error count to additional info
        if additional_info is None:
            additional_info = {}
        
        additional_info["total_errors"] = self.total_errors + 1
        additional_info["error_type"] = error_type
        additional_info["error_code"] = error_code
        
        # Log error
        self.logger.log_error(error_type, str(error), additional_info)
        
        # Indicate error with LED
        self._blink_error_code(error_code)
        
        # Check if we should reset
        if self._should_reset(error_type):
            self._debug_print(f"Too many {error_type} errors. Resetting device...", DEBUG_BASIC)
            time.sleep(1)
            
            # Restore override if provided
            if auto_reset is not None:
                self.set_auto_reset(old_auto_reset)
                
            return self.reset_device(delay=20, reason=f"Too many {error_type} errors")
        
        # Restore override if provided
        if auto_reset is not None:
            self.set_auto_reset(old_auto_reset)
            
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
    
    def reset_device(self, delay=20, reason="Unknown"):
        """Reset the device safely, ensuring logs are saved.
        
        Args:
            delay (int): Delay in seconds before reset
            reason (str): Reason for reset
            
        Returns:
            str: Action taken ("reset" or "reset_skipped")
        """
        self._debug_print(f"Preparing to reset device in {delay} seconds. Reason: {reason}", DEBUG_BASIC)
        
        # Check if auto-reset is enabled
        if not self.auto_reset:
            self._debug_print("Auto-reset disabled, skipping reset", DEBUG_BASIC)
            
            # Log the skipped reset
            self.logger.log_error("SYSTEM", "Device reset skipped (auto-reset disabled)", {"reason": reason})
            
            # Blink LED to indicate reset was skipped
            for _ in range(3):
                self.led.on()
                time.sleep(0.5)
                self.led.off()
                time.sleep(0.5)
                
            return "reset_skipped"
        
        # Log the reset event
        self.logger.log_error("SYSTEM", "Device reset requested", {"reason": reason, "delay": delay})
        
        # Rapid blink to indicate imminent reset
        for _ in range(5):
            self.led.on()
            time.sleep(0.1)
            self.led.off()
            time.sleep(0.1)
        
        # Print countdown
        for i in range(delay, 0, -1):
            if i % 5 == 0 or i <= 3:  # Print at 5-second intervals and final 3 seconds
                self._debug_print(f"{i} seconds until reset...", DEBUG_BASIC)
            
            # Blink LED during countdown (slow pattern)
            if i % 2 == 0:
                self.led.on()
            else:
                self.led.off()
                
            time.sleep(1)
        
        # Ensure all files are synced before reset
        self._debug_print("Syncing files before reset...", DEBUG_BASIC)
        sync_all_files()
        
        # Final confirmation and reset
        self._debug_print("Reset now!", DEBUG_BASIC)
        
        # One final long blink to indicate reset
        self.led.on()
        time.sleep(0.5)
        self.led.off()
        
        # Small delay to ensure LED state is visible and all output is sent
        time.sleep(0.5)
        
        # Reset the device
        machine.reset()
        
        # This will never be reached due to reset
        return "reset"
    
    def get_error_stats(self):
        """Get statistics about errors.
        
        Returns:
            dict: Error statistics
        """
        return {
            "total_errors": self.total_errors,
            "error_counts": self.error_count,
            "last_error_times": self.last_error_time,
            "reset_threshold": self.reset_threshold,
            "error_window": self.error_window,
            "auto_reset": self.auto_reset,
            "debug_level": self.debug_level
        }

# Global instances with debug settings
error_logger = ErrorLogger(debug_level=DEBUG_BASIC)
error_handler = ErrorHandler(error_logger, debug_level=DEBUG_BASIC, auto_reset=True)

def set_debug_level(level):
    """Set the debug level for all components.
    
    Args:
        level (int): Debug level (0-3)
    """
    global error_logger, error_handler
    error_logger.set_debug_level(level)
    error_handler.set_debug_level(level)
    print(f"Global debug level set to {level}")

def set_auto_reset(auto_reset):
    """Set whether to automatically reset on critical errors.
    
    Args:
        auto_reset (bool): Whether to auto-reset
    """
    global error_handler
    error_handler.set_auto_reset(auto_reset)
    print(f"Global auto-reset set to {auto_reset}")

def handle_error(error, additional_info=None, auto_reset=None):
    """Global function to handle errors.
    
    Args:
        error (Exception): The error to handle
        additional_info (dict): Additional information about the error
        auto_reset (bool): Override the auto-reset setting for this error
        
    Returns:
        str: Action taken ("logged", "reset", "reset_skipped")
    """
    return error_handler.handle_error(error, additional_info, auto_reset)

def safe_reset(delay=20, reason="Manual reset", force=False):
    """Safely reset the device, ensuring logs are saved.
    
    Args:
        delay (int): Delay in seconds before reset
        reason (str): Reason for reset
        force (bool): Force reset even if auto-reset is disabled
        
    Returns:
        str: Action taken ("reset", "reset_skipped")
    """
    global error_handler
    
    # If force is True, temporarily enable auto-reset
    if force and not error_handler.auto_reset:
        old_auto_reset = error_handler.auto_reset
        error_handler.set_auto_reset(True)
        result = error_handler.reset_device(delay=delay, reason=reason)
        error_handler.set_auto_reset(old_auto_reset)
        return result
    else:
        return error_handler.reset_device(delay=delay, reason=reason)

def get_error_logs(max_count=10):
    """Get the most recent error logs.
    
    Args:
        max_count (int): Maximum number of logs to return
        
    Returns:
        list: List of log entries
    """
    return error_logger.get_logs(max_count)

def clear_error_logs():
    """Clear all error logs.
    
    Returns:
        bool: True if logs were successfully cleared, False otherwise
    """
    return error_logger.clear_logs()

def get_error_stats():
    """Get statistics about errors.
    
    Returns:
        dict: Error statistics
    """
    return error_handler.get_error_stats()

# Example usage
if __name__ == "__main__":
    try:
        # Set debug level
        set_debug_level(DEBUG_DETAILED)
        
        # Disable auto-reset for testing
        set_auto_reset(False)
        
        # Initialize watchdog
        wdt = Watchdog(timeout_ms=8000, debug_level=DEBUG_DETAILED, auto_reset=False)
        
        print("Testing watchdog and error handling (P3 Debug Version 4.15.0)...")
        
        # Test error handling
        try:
            # Simulate an error
            raise ValueError("Test error")
        except Exception as e:
            handle_error(e, {"test": True})
        
        # Print error logs
        print("\nError logs:")
        logs = get_error_logs(5)
        for log in logs:
            print(log.strip())
        
        # Print error stats
        print("\nError statistics:")
        stats = get_error_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")
        
        # Test different auto-reset settings
        print("\nTesting auto-reset settings:")
        
        # Test with auto-reset disabled
        try:
            raise TimeoutError("Test timeout error")
        except Exception as e:
            result = handle_error(e, {"auto_reset_test": False}, auto_reset=False)
            print(f"Result with auto_reset=False: {result}")
        
        # Test with auto-reset enabled but below threshold
        try:
            raise ConnectionError("Test connection error")
        except Exception as e:
            result = handle_error(e, {"auto_reset_test": True}, auto_reset=True)
            print(f"Result with auto_reset=True (below threshold): {result}")
        
        # Test safe_reset with force=True
        print("\nTesting safe_reset with force=True (will reset if not intercepted)...")
        print("Intercepting reset for demonstration...")
        # safe_reset(delay=5, reason="Test forced reset", force=True)
        
        # Main loop
        count = 0
        print("\nStarting main loop. Press Ctrl+C to stop.")
        while True:
            # Feed the watchdog
            wdt.feed()
            
            # Blink LED to show activity
            wdt.blink_led(1, 0.1)
            
            # Simulate occasional errors
            count += 1
            if count % 10 == 0:
                error_types = ["SENSOR_ERROR", "WIFI_ERROR", "CO2_SENSOR_ERROR", "I2C_ERROR", "UNKNOWN_ERROR"]
                error_type = error_types[count % len(error_types)]
                try:
                    raise Exception(f"Simulated {error_type}")
                except Exception as e:
                    handle_error(e, auto_reset=False)  # Disable auto-reset for testing
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("Test stopped by user")
    except Exception as e:
        print(f"Unexpected error: {e}")
        handle_error(e, auto_reset=False)  # Disable auto-reset for testing
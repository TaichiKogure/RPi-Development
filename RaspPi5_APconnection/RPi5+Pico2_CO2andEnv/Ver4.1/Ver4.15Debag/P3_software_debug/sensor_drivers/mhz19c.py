#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MH-Z19C CO2 Sensor Driver for Raspberry Pi Pico W
Version 1.1.0 (Enhanced for Ver4.15 Debug)

This module provides a driver for the MH-Z19C CO2 sensor connected to a Raspberry Pi Pico W.
The sensor uses UART communication and requires a 30-second warmup period before readings.

Enhancements in this version:
- Improved error handling and recovery
- Better logging for troubleshooting
- Retry mechanism for failed readings
- Graceful handling of communication errors
- Status tracking for sensor health
- Enhanced debugging capabilities

Pin connections:
- VCC (red) -> VBUS (5V, pin 40)
- GND (black) -> GND (pin 38)
- TX (green) -> GP9 (pin 12)
- RX (blue) -> GP8 (pin 11)
"""

import time
import struct
import gc
from machine import UART, Pin

# Debug levels
DEBUG_NONE = 0    # No debug output
DEBUG_BASIC = 1   # Basic information
DEBUG_DETAILED = 2  # Detailed information
DEBUG_VERBOSE = 3  # Very verbose output

class MHZ19C:
    """Driver for MH-Z19C CO2 sensor with enhanced debugging."""

    def __init__(self, uart_id=1, tx_pin=8, rx_pin=9, baudrate=9600, debug_level=DEBUG_BASIC):
        """Initialize the MH-Z19C sensor.

        Args:
            uart_id (int): UART ID to use (default: 1)
            tx_pin (int): TX pin number (default: 8, connected to RX of sensor)
            rx_pin (int): RX pin number (default: 9, connected to TX of sensor)
            baudrate (int): Baud rate (default: 9600)
            debug_level (int): Level of debug output (0-3)
        """
        try:
            self.uart = UART(uart_id, baudrate=baudrate, tx=Pin(tx_pin), rx=Pin(rx_pin))
            self.warmup_time = 30  # seconds
            self.warmup_start = time.time()
            self.is_warmed_up = False
            self.last_read_time = 0
            self.last_co2_value = 0
            self.error_count = 0
            self.max_errors = 5
            self.read_count = 0
            self.successful_reads = 0
            self.debug_level = debug_level
            
            self._debug_print(f"MH-Z19C initialized on UART{uart_id} (TX: GP{tx_pin}, RX: GP{rx_pin})", DEBUG_BASIC)
            self._debug_print(f"Warming up for {self.warmup_time} seconds...", DEBUG_BASIC)
            
            # Flush any data in the UART buffer
            while self.uart.any():
                self.uart.read()
                
        except Exception as e:
            print(f"Error initializing MH-Z19C: {e}")
            raise

    def _debug_print(self, message, level=DEBUG_BASIC):
        """Print debug message if debug level is high enough.
        
        Args:
            message (str): Message to print
            level (int): Minimum debug level required to print this message
        """
        if self.debug_level >= level:
            print(f"[MH-Z19C Debug] {message}")

    def set_debug_level(self, level):
        """Set the debug level.
        
        Args:
            level (int): Debug level (0-3)
        """
        self.debug_level = level
        self._debug_print(f"Debug level set to {level}", DEBUG_BASIC)

    def _calculate_checksum(self, packet):
        """Calculate checksum for command packet."""
        try:
            checksum = 0
            for byte in packet[1:8]:
                checksum += byte
            checksum = ~checksum & 0xFF
            checksum += 1
            return checksum
        except Exception as e:
            self._debug_print(f"Error calculating checksum: {e}", DEBUG_BASIC)
            return 0

    def _verify_checksum(self, response):
        """Verify checksum of response packet."""
        try:
            if len(response) < 9:
                self._debug_print(f"Response too short: {len(response)} bytes", DEBUG_BASIC)
                return False

            checksum = 0
            for byte in response[1:8]:
                checksum += byte
            checksum = ~checksum & 0xFF
            checksum += 1

            if checksum != response[8]:
                self._debug_print(f"Checksum mismatch: calculated {checksum}, received {response[8]}", DEBUG_BASIC)
                
            return checksum == response[8]
        except Exception as e:
            self._debug_print(f"Error verifying checksum: {e}", DEBUG_BASIC)
            return False

    def _send_command(self, command, data=None, retries=3):
        """Send command to sensor and read response with retry.

        Args:
            command (int): Command byte
            data (list): Optional data bytes (default: None)
            retries (int): Number of retry attempts (default: 3)

        Returns:
            bytes: Response from sensor or None if error
        """
        if data is None:
            data = [0, 0, 0, 0, 0]

        # Force garbage collection before UART operation
        gc.collect()
        
        for attempt in range(retries):
            try:
                # Create command packet
                packet = bytearray([0xFF, 0x01, command] + data)
                packet.append(self._calculate_checksum(packet))
                
                self._debug_print(f"Sending command 0x{command:02x}, attempt {attempt+1}/{retries}", DEBUG_DETAILED)
                self._debug_print(f"Command packet: {[hex(b) for b in packet]}", DEBUG_VERBOSE)
                
                # Flush any existing data
                while self.uart.any():
                    self.uart.read()
                
                # Send command
                self.uart.write(packet)
                
                # Wait for response with timeout
                start_time = time.time()
                timeout = 1.0  # 1 second timeout
                
                # Wait for data to be available
                while not self.uart.any() and time.time() - start_time < timeout:
                    time.sleep(0.01)
                
                # Check if we have data
                if self.uart.any():
                    # Read response
                    response = self.uart.read(9)
                    
                    self._debug_print(f"Response received: {[hex(b) for b in response] if response else 'None'}", DEBUG_VERBOSE)
                    
                    if response and len(response) == 9 and response[0] == 0xFF and response[1] == 0x86:
                        if self._verify_checksum(response):
                            if attempt > 0:
                                self._debug_print(f"Command 0x{command:02x} succeeded on attempt {attempt+1}", DEBUG_BASIC)
                            return response
                        else:
                            self._debug_print(f"Attempt {attempt+1}: Checksum error", DEBUG_BASIC)
                    else:
                        self._debug_print(f"Attempt {attempt+1}: Invalid response: {response if response else 'None'}", DEBUG_BASIC)
                else:
                    self._debug_print(f"Attempt {attempt+1}: No response within timeout", DEBUG_BASIC)
                
                # Wait before retry
                if attempt < retries - 1:
                    wait_time = 0.2 * (attempt + 1)  # Progressive backoff
                    self._debug_print(f"Waiting {wait_time:.1f}s before retry", DEBUG_DETAILED)
                    time.sleep(wait_time)
            
            except Exception as e:
                self._debug_print(f"Error sending command (attempt {attempt+1}): {e}", DEBUG_BASIC)
            
        # All retries failed
        self.error_count += 1
        self._debug_print(f"Command 0x{command:02x} failed after {retries} attempts. Total errors: {self.error_count}", DEBUG_BASIC)
        return None

    def read_co2(self, retries=3):
        """Read CO2 concentration from sensor.

        Args:
            retries (int): Number of retry attempts (default: 3)

        Returns:
            int: CO2 concentration in ppm or 0 if error
        """
        # Check if sensor is warmed up
        current_time = time.time()
        if not self.is_warmed_up:
            if current_time - self.warmup_start >= self.warmup_time:
                self.is_warmed_up = True
                self._debug_print("MH-Z19C warmup complete", DEBUG_BASIC)
            else:
                remaining = self.warmup_time - (current_time - self.warmup_start)
                self._debug_print(f"MH-Z19C still warming up ({remaining:.1f} seconds remaining)", DEBUG_BASIC)
                return 0

        # Limit read frequency to once per second
        if current_time - self.last_read_time < 1:
            return self.last_co2_value

        # Increment read count
        self.read_count += 1
        
        self._debug_print(f"Reading CO2 (attempt {self.read_count})", DEBUG_DETAILED)
        
        # Send read command
        response = self._send_command(0x86, retries=retries)

        if response:
            try:
                # Extract CO2 value (high byte, low byte)
                co2 = (response[2] << 8) | response[3]
                
                self._debug_print(f"Raw CO2 reading: {co2} ppm", DEBUG_DETAILED)
                
                # Validate reading (typical range 400-5000 ppm)
                if co2 < 0 or co2 > 5000:
                    self._debug_print(f"Warning: Unusual CO2 reading: {co2} ppm", DEBUG_BASIC)
                    
                    # If it's extremely out of range, consider it an error
                    if co2 < 0 or co2 > 10000:
                        self._debug_print("Reading out of valid range, ignoring", DEBUG_BASIC)
                        self.error_count += 1
                        return self.last_co2_value
                
                self.last_co2_value = co2
                self.last_read_time = current_time
                self.successful_reads += 1
                
                # Log every 10th reading
                if self.read_count % 10 == 0 or self.debug_level >= DEBUG_DETAILED:
                    self._debug_print(f"CO2: {co2} ppm (Success rate: {self.successful_reads}/{self.read_count})", DEBUG_BASIC)
                
                return co2
            except Exception as e:
                self._debug_print(f"Error processing CO2 reading: {e}", DEBUG_BASIC)
                self.error_count += 1
                return self.last_co2_value
        else:
            self._debug_print("MH-Z19C read error", DEBUG_BASIC)
            return self.last_co2_value

    def calibrate_zero_point(self):
        """Calibrate zero point (400ppm).

        Note: Sensor must be in fresh air (400ppm) for at least 20 minutes before calibration.
        
        Returns:
            bool: True if calibration was successful, False otherwise
        """
        self._debug_print("MH-Z19C calibrating zero point...", DEBUG_BASIC)
        response = self._send_command(0x87)
        time.sleep(1)
        
        if response:
            self._debug_print("MH-Z19C zero point calibration complete", DEBUG_BASIC)
            return True
        else:
            self._debug_print("MH-Z19C zero point calibration failed", DEBUG_BASIC)
            return False

    def calibrate_span_point(self, span=2000):
        """Calibrate span point.

        Args:
            span (int): CO2 concentration in ppm (default: 2000)

        Note: Sensor must be in environment with known CO2 concentration for calibration.
        
        Returns:
            bool: True if calibration was successful, False otherwise
        """
        if span < 1000 or span > 5000:
            self._debug_print(f"Warning: Span value {span} ppm is outside recommended range (1000-5000)", DEBUG_BASIC)
        
        self._debug_print(f"MH-Z19C calibrating span point to {span}ppm...", DEBUG_BASIC)
        high_byte = (span >> 8) & 0xFF
        low_byte = span & 0xFF
        response = self._send_command(0x88, [high_byte, low_byte, 0, 0, 0])
        time.sleep(1)
        
        if response:
            self._debug_print("MH-Z19C span point calibration complete", DEBUG_BASIC)
            return True
        else:
            self._debug_print("MH-Z19C span point calibration failed", DEBUG_BASIC)
            return False

    def set_detection_range(self, range_ppm=5000):
        """Set detection range.

        Args:
            range_ppm (int): Detection range in ppm (default: 5000)
            
        Returns:
            bool: True if range was set successfully, False otherwise
        """
        if range_ppm not in [2000, 5000, 10000]:
            self._debug_print(f"MH-Z19C invalid range: {range_ppm}ppm (must be 2000, 5000, or 10000)", DEBUG_BASIC)
            return False

        self._debug_print(f"MH-Z19C setting detection range to {range_ppm}ppm...", DEBUG_BASIC)
        high_byte = (range_ppm >> 8) & 0xFF
        low_byte = range_ppm & 0xFF
        response = self._send_command(0x99, [0, high_byte, low_byte, 0, 0])
        time.sleep(1)
        
        if response:
            self._debug_print("MH-Z19C detection range set", DEBUG_BASIC)
            return True
        else:
            self._debug_print("MH-Z19C failed to set detection range", DEBUG_BASIC)
            return False
    
    def get_status(self):
        """Get sensor status information.
        
        Returns:
            dict: Status information including error count, read count, etc.
        """
        status = {
            "is_warmed_up": self.is_warmed_up,
            "last_co2_value": self.last_co2_value,
            "error_count": self.error_count,
            "read_count": self.read_count,
            "successful_reads": self.successful_reads,
            "success_rate": self.successful_reads / max(1, self.read_count),
            "last_read_time": self.last_read_time,
            "debug_level": self.debug_level
        }
        
        self._debug_print("Sensor status:", DEBUG_DETAILED)
        for key, value in status.items():
            self._debug_print(f"  {key}: {value}", DEBUG_DETAILED)
            
        return status

    def run_diagnostics(self):
        """Run sensor diagnostics.
        
        Returns:
            dict: Diagnostic results
        """
        self._debug_print("Running MH-Z19C diagnostics...", DEBUG_BASIC)
        
        # Check if sensor is responsive
        response = self._send_command(0x86, retries=2)
        responsive = response is not None
        
        # Check if sensor is warmed up
        current_time = time.time()
        warmup_status = "complete" if self.is_warmed_up else f"in progress ({int(self.warmup_time - (current_time - self.warmup_start))}s remaining)"
        
        # Try to read CO2 value
        if responsive and self.is_warmed_up:
            co2 = self.read_co2(retries=2)
            reading_successful = co2 > 0
        else:
            reading_successful = False
            co2 = 0
        
        # Compile diagnostic results
        results = {
            "responsive": responsive,
            "warmup_status": warmup_status,
            "is_warmed_up": self.is_warmed_up,
            "reading_successful": reading_successful,
            "co2_value": co2,
            "error_count": self.error_count,
            "success_rate": self.successful_reads / max(1, self.read_count),
            "uart_id": self.uart.id if hasattr(self.uart, 'id') else "unknown"
        }
        
        self._debug_print("Diagnostics complete:", DEBUG_BASIC)
        for key, value in results.items():
            self._debug_print(f"  {key}: {value}", DEBUG_BASIC)
            
        return results

# Example usage
if __name__ == "__main__":
    try:
        # Initialize sensor with debug level
        sensor = MHZ19C(debug_level=DEBUG_DETAILED)
        
        # Run diagnostics
        sensor.run_diagnostics()
        
        # Wait for warmup
        print("Waiting for sensor warmup...")
        start_time = time.time()
        while time.time() - start_time < sensor.warmup_time:
            remaining = sensor.warmup_time - (time.time() - start_time)
            if int(remaining) % 5 == 0:
                print(f"Warmup: {int(remaining)} seconds remaining")
            time.sleep(1)
        
        # Read CO2 value
        print("Reading CO2...")
        co2 = sensor.read_co2()
        print(f"CO2 concentration: {co2} ppm")
        
        # Get sensor status
        status = sensor.get_status()
        print("Sensor status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"Error in MH-Z19C test: {e}")
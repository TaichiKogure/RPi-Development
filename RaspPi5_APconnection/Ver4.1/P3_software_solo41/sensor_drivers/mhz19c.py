#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MH-Z19C CO2 Sensor Driver for Raspberry Pi Pico W
Version 1.1.0 (Enhanced for Ver4.1)

This module provides a driver for the MH-Z19C CO2 sensor connected to a Raspberry Pi Pico W.
The sensor uses UART communication and requires a 30-second warmup period before readings.

Enhancements in this version:
- Improved error handling and recovery
- Better logging for troubleshooting
- Retry mechanism for failed readings
- Graceful handling of communication errors
- Status tracking for sensor health

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

class MHZ19C:
    """Driver for MH-Z19C CO2 sensor."""

    def __init__(self, uart_id=1, tx_pin=8, rx_pin=9, baudrate=9600):
        """Initialize the MH-Z19C sensor.

        Args:
            uart_id (int): UART ID to use (default: 1)
            tx_pin (int): TX pin number (default: 8, connected to RX of sensor)
            rx_pin (int): RX pin number (default: 9, connected to TX of sensor)
            baudrate (int): Baud rate (default: 9600)
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
            
            print(f"MH-Z19C initialized on UART{uart_id} (TX: GP{tx_pin}, RX: GP{rx_pin})")
            print(f"Warming up for {self.warmup_time} seconds...")
            
            # Flush any data in the UART buffer
            while self.uart.any():
                self.uart.read()
                
        except Exception as e:
            print(f"Error initializing MH-Z19C: {e}")
            raise

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
            print(f"Error calculating checksum: {e}")
            return 0

    def _verify_checksum(self, response):
        """Verify checksum of response packet."""
        try:
            if len(response) < 9:
                print(f"Response too short: {len(response)} bytes")
                return False

            checksum = 0
            for byte in response[1:8]:
                checksum += byte
            checksum = ~checksum & 0xFF
            checksum += 1

            if checksum != response[8]:
                print(f"Checksum mismatch: calculated {checksum}, received {response[8]}")
                
            return checksum == response[8]
        except Exception as e:
            print(f"Error verifying checksum: {e}")
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
                    
                    if response and len(response) == 9 and response[0] == 0xFF and response[1] == 0x86:
                        if self._verify_checksum(response):
                            if attempt > 0:
                                print(f"Command 0x{command:02x} succeeded on attempt {attempt+1}")
                            return response
                        else:
                            print(f"Attempt {attempt+1}: Checksum error")
                    else:
                        print(f"Attempt {attempt+1}: Invalid response: {response if response else 'None'}")
                else:
                    print(f"Attempt {attempt+1}: No response within timeout")
                
                # Wait before retry
                if attempt < retries - 1:
                    time.sleep(0.2 * (attempt + 1))  # Progressive backoff
            
            except Exception as e:
                print(f"Error sending command (attempt {attempt+1}): {e}")
            
        # All retries failed
        self.error_count += 1
        print(f"Command 0x{command:02x} failed after {retries} attempts. Total errors: {self.error_count}")
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
                print("MH-Z19C warmup complete")
            else:
                remaining = self.warmup_time - (current_time - self.warmup_start)
                print(f"MH-Z19C still warming up ({remaining:.1f} seconds remaining)")
                return 0

        # Limit read frequency to once per second
        if current_time - self.last_read_time < 1:
            return self.last_co2_value

        # Increment read count
        self.read_count += 1
        
        # Send read command
        response = self._send_command(0x86, retries=retries)

        if response:
            try:
                # Extract CO2 value (high byte, low byte)
                co2 = (response[2] << 8) | response[3]
                
                # Validate reading (typical range 400-5000 ppm)
                if co2 < 0 or co2 > 5000:
                    print(f"Warning: Unusual CO2 reading: {co2} ppm")
                    
                    # If it's extremely out of range, consider it an error
                    if co2 < 0 or co2 > 10000:
                        print("Reading out of valid range, ignoring")
                        self.error_count += 1
                        return self.last_co2_value
                
                self.last_co2_value = co2
                self.last_read_time = current_time
                self.successful_reads += 1
                
                # Log every 10th reading
                if self.read_count % 10 == 0:
                    print(f"CO2: {co2} ppm (Success rate: {self.successful_reads}/{self.read_count})")
                
                return co2
            except Exception as e:
                print(f"Error processing CO2 reading: {e}")
                self.error_count += 1
                return self.last_co2_value
        else:
            print("MH-Z19C read error")
            return self.last_co2_value

    def calibrate_zero_point(self):
        """Calibrate zero point (400ppm).

        Note: Sensor must be in fresh air (400ppm) for at least 20 minutes before calibration.
        
        Returns:
            bool: True if calibration was successful, False otherwise
        """
        print("MH-Z19C calibrating zero point...")
        response = self._send_command(0x87)
        time.sleep(1)
        
        if response:
            print("MH-Z19C zero point calibration complete")
            return True
        else:
            print("MH-Z19C zero point calibration failed")
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
            print(f"Warning: Span value {span} ppm is outside recommended range (1000-5000)")
        
        print(f"MH-Z19C calibrating span point to {span}ppm...")
        high_byte = (span >> 8) & 0xFF
        low_byte = span & 0xFF
        response = self._send_command(0x88, [high_byte, low_byte, 0, 0, 0])
        time.sleep(1)
        
        if response:
            print("MH-Z19C span point calibration complete")
            return True
        else:
            print("MH-Z19C span point calibration failed")
            return False

    def set_detection_range(self, range_ppm=5000):
        """Set detection range.

        Args:
            range_ppm (int): Detection range in ppm (default: 5000)
            
        Returns:
            bool: True if range was set successfully, False otherwise
        """
        if range_ppm not in [2000, 5000, 10000]:
            print(f"MH-Z19C invalid range: {range_ppm}ppm (must be 2000, 5000, or 10000)")
            return False

        print(f"MH-Z19C setting detection range to {range_ppm}ppm...")
        high_byte = (range_ppm >> 8) & 0xFF
        low_byte = range_ppm & 0xFF
        response = self._send_command(0x99, [0, high_byte, low_byte, 0, 0])
        time.sleep(1)
        
        if response:
            print("MH-Z19C detection range set")
            return True
        else:
            print("MH-Z19C failed to set detection range")
            return False
    
    def get_status(self):
        """Get sensor status information.
        
        Returns:
            dict: Status information including error count, read count, etc.
        """
        return {
            "is_warmed_up": self.is_warmed_up,
            "last_co2_value": self.last_co2_value,
            "error_count": self.error_count,
            "read_count": self.read_count,
            "successful_reads": self.successful_reads,
            "success_rate": self.successful_reads / max(1, self.read_count),
            "last_read_time": self.last_read_time
        }

# Example usage
if __name__ == "__main__":
    try:
        # Initialize sensor
        sensor = MHZ19C()
        
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
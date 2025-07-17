#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MH-Z19 CO2 Sensor Data Logger for Raspberry Pi 5
Version 1.0.0

This program reads CO2 concentration data from an MH-Z19 sensor connected to a Raspberry Pi 5,
logs the data to a CSV file every 10 seconds, and properly handles initialization and cleanup.

Pin connections:
- VCC (red) -> 5V
- GND (black) -> GND
- TX (green) -> GPIO 14 (UART0 RX)
- RX (blue) -> GPIO 15 (UART0 TX)

Usage:
    python3 MZH19_test.py [output_file.csv]

Press Ctrl+C to exit the program.
"""

import time
import csv
import sys
import signal
import serial
import datetime
import os
import atexit

# Default CSV file path
DEFAULT_CSV_PATH = "mhz19_data.csv"

class MHZ19:
    """Driver for MH-Z19 CO2 sensor."""

    def __init__(self, uart_device='/dev/ttyAMA0', baudrate=9600):
        """Initialize the MH-Z19 sensor.

        Args:
            uart_device (str): UART device path (default: /dev/ttyAMA0)
            baudrate (int): Baud rate (default: 9600)
        """
        try:
            self.serial = serial.Serial(
                port=uart_device,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0
            )
            self.warmup_time = 30  # seconds
            self.warmup_start = time.time()
            self.is_warmed_up = False
            
            # Flush any data in the serial buffer
            self.serial.flushInput()
            
            print(f"MH-Z19 initialized on {uart_device}")
            print(f"Warming up for {self.warmup_time} seconds...")
            
        except Exception as e:
            print(f"Error initializing MH-Z19: {e}")
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

        for attempt in range(retries):
            try:
                # Create command packet
                packet = bytearray([0xFF, 0x01, command] + data)
                packet.append(self._calculate_checksum(packet))
                
                # Flush any existing data
                self.serial.flushInput()
                
                # Send command
                self.serial.write(packet)
                
                # Wait for response with timeout
                time.sleep(0.1)
                
                # Check if we have data
                if self.serial.in_waiting:
                    # Read response
                    response = self.serial.read(9)
                    
                    if response and len(response) == 9 and response[0] == 0xFF and response[1] == 0x86:
                        return response
                
                # Wait before retry
                if attempt < retries - 1:
                    time.sleep(0.2 * (attempt + 1))  # Progressive backoff
            
            except Exception as e:
                print(f"Error sending command (attempt {attempt+1}): {e}")
            
        # All retries failed
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
                print("MH-Z19 warmup complete")
            else:
                remaining = self.warmup_time - (current_time - self.warmup_start)
                print(f"MH-Z19 still warming up ({remaining:.1f} seconds remaining)")
                return 0

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
                        return 0
                
                return co2
            except Exception as e:
                print(f"Error processing CO2 reading: {e}")
                return 0
        else:
            print("MH-Z19 read error")
            return 0

    def close(self):
        """Close the serial connection to the sensor."""
        if hasattr(self, 'serial') and self.serial.is_open:
            self.serial.close()
            print("MH-Z19 connection closed")

def signal_handler(sig, frame):
    """Handle Ctrl+C and other signals to ensure clean exit."""
    print("\nProgram terminated by user")
    sys.exit(0)

def cleanup():
    """Cleanup function to ensure the sensor connection is properly closed."""
    if 'sensor' in globals() and sensor is not None:
        sensor.close()

def main():
    """Main function to read CO2 data and log to CSV."""
    global sensor
    
    # Register signal handler for clean exit
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Register cleanup function to ensure proper port release
    atexit.register(cleanup)
    
    # Determine CSV file path
    csv_path = DEFAULT_CSV_PATH
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    
    print(f"CO2 data will be logged to: {csv_path}")
    
    # Check if file exists to determine if we need to write headers
    file_exists = os.path.isfile(csv_path)
    
    # Initialize sensor
    try:
        sensor = MHZ19()
    except Exception as e:
        print(f"Failed to initialize MH-Z19 sensor: {e}")
        return 1
    
    # Main loop
    try:
        while True:
            # Read CO2 value
            co2 = sensor.read_co2()
            
            # Get current timestamp
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Only log if we have a valid reading
            if co2 > 0:
                # Open CSV file in append mode
                with open(csv_path, 'a', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Write headers if file is new
                    if not file_exists:
                        writer.writerow(['Timestamp', 'CO2 (ppm)'])
                        file_exists = True
                    
                    # Write data row
                    writer.writerow([timestamp, co2])
                
                print(f"{timestamp} - CO2: {co2} ppm")
            
            # Wait for next reading (10 seconds)
            time.sleep(10)
    
    except Exception as e:
        print(f"Error in main loop: {e}")
        return 1
    
    finally:
        # Ensure sensor is properly closed
        cleanup()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
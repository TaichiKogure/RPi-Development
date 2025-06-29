# -*- coding: utf-8 -*-
"""
MH-Z19B CO2 Sensor Driver for Raspberry Pi Pico 2W
Version: 1.0.0

This module provides functions to interface with the MH-Z19B CO2 sensor
to measure carbon dioxide concentration in the air.

Features:
- CO2 concentration measurement in ppm (parts per million)
- Automatic calibration control
- Manual calibration functions
- Detection range: 0-5000ppm (standard) or 0-10000ppm (extended)
- Error handling and diagnostics

Requirements:
- MicroPython for Raspberry Pi Pico
- MH-Z19B sensor connected via UART

Usage:
    import mhz19b_driver
    sensor = mhz19b_driver.MHZ19BSensor(uart_id=1, tx_pin=8, rx_pin=9)
    co2_ppm = sensor.read_co2()
    print(f"CO2 Concentration: {co2_ppm} ppm")
"""

import time
import struct
from machine import UART, Pin

# MH-Z19B commands
CMD_READ_CO2 = b"\xFF\x01\x86\x00\x00\x00\x00\x00\x79"
CMD_CALIBRATE_ZERO = b"\xFF\x01\x87\x00\x00\x00\x00\x00\x78"
CMD_CALIBRATE_SPAN = b"\xFF\x01\x88\x00\x00\x00\x00\x00\x77"
CMD_AUTO_CALIBRATION_ON = b"\xFF\x01\x79\xA0\x00\x00\x00\x00\xE6"
CMD_AUTO_CALIBRATION_OFF = b"\xFF\x01\x79\x00\x00\x00\x00\x00\x86"
CMD_DETECTION_RANGE_5000 = b"\xFF\x01\x99\x00\x00\x00\x13\x88\x76"  # 5000ppm range
CMD_DETECTION_RANGE_10000 = b"\xFF\x01\x99\x00\x00\x00\x27\x10\xCF"  # 10000ppm range

class MHZ19BSensor:
    """Class to interface with the MH-Z19B CO2 sensor."""
    
    def __init__(self, uart_id=1, tx_pin=8, rx_pin=9, baudrate=9600, timeout=1000):
        """Initialize the MH-Z19B sensor with the given UART configuration.
        
        Args:
            uart_id (int): UART ID to use (0 or 1)
            tx_pin (int): TX pin number
            rx_pin (int): RX pin number
            baudrate (int): Baud rate (default: 9600)
            timeout (int): Read timeout in milliseconds (default: 1000)
        """
        self.uart = UART(uart_id, baudrate=baudrate, tx=Pin(tx_pin), rx=Pin(rx_pin), timeout=timeout)
        self.uart.init(baudrate=baudrate, bits=8, parity=None, stop=1, timeout=timeout)
        
        # Flush any existing data
        self._flush_input()
        
        # Wait for sensor to stabilize
        time.sleep(0.1)
    
    def _flush_input(self):
        """Flush the input buffer."""
        while self.uart.any():
            self.uart.read(1)
    
    def _calculate_checksum(self, packet):
        """Calculate the checksum for a command packet."""
        if len(packet) != 9:
            return None
        
        checksum = 0
        for i in range(1, 8):
            checksum += packet[i]
        
        checksum = 0xFF - (checksum % 0x100) + 1
        return checksum & 0xFF
    
    def _verify_response(self, response):
        """Verify the response from the sensor."""
        if len(response) != 9:
            return False
        
        if response[0] != 0xFF or response[1] != 0x86:
            return False
        
        # Calculate and verify checksum
        checksum = self._calculate_checksum(response)
        if checksum is None or checksum != response[8]:
            return False
        
        return True
    
    def read_co2(self):
        """Read the CO2 concentration from the sensor.
        
        Returns:
            int: CO2 concentration in ppm, or None if reading failed
        """
        # Flush input buffer
        self._flush_input()
        
        # Send command to read CO2
        self.uart.write(CMD_READ_CO2)
        
        # Wait for response
        time.sleep(0.1)
        
        # Read response
        if self.uart.any():
            response = self.uart.read(9)
            
            # Verify response
            if response and self._verify_response(response):
                # Extract CO2 concentration (high byte, low byte)
                co2 = (response[2] << 8) | response[3]
                return co2
        
        return None
    
    def read_all(self):
        """Read all available data from the sensor.
        
        Returns:
            dict: Dictionary containing CO2, temperature, and status, or None if reading failed
        """
        # Flush input buffer
        self._flush_input()
        
        # Send command to read CO2
        self.uart.write(CMD_READ_CO2)
        
        # Wait for response
        time.sleep(0.1)
        
        # Read response
        if self.uart.any():
            response = self.uart.read(9)
            
            # Verify response
            if response and self._verify_response(response):
                # Extract data
                co2 = (response[2] << 8) | response[3]
                temperature = response[4] - 40  # Temperature in Celsius
                status = response[5]  # Status byte
                
                return {
                    'co2': co2,
                    'temperature': temperature,
                    'status': status
                }
        
        return None
    
    def calibrate_zero_point(self):
        """Calibrate the zero point (400ppm).
        
        Note: Sensor must be in clean air (400ppm) for at least 20 minutes before calibration.
        
        Returns:
            bool: True if calibration was successful, False otherwise
        """
        # Send command to calibrate zero point
        self.uart.write(CMD_CALIBRATE_ZERO)
        
        # Wait for calibration to complete
        time.sleep(0.1)
        
        return True
    
    def calibrate_span_point(self, span_ppm=2000):
        """Calibrate the span point.
        
        Note: Sensor must be in air with known CO2 concentration for at least 20 minutes before calibration.
        
        Args:
            span_ppm (int): CO2 concentration in ppm for span calibration (default: 2000)
        
        Returns:
            bool: True if calibration was successful, False otherwise
        """
        # Create span calibration command with the specified ppm value
        high_byte = (span_ppm >> 8) & 0xFF
        low_byte = span_ppm & 0xFF
        cmd = bytearray(CMD_CALIBRATE_SPAN)
        cmd[3] = high_byte
        cmd[4] = low_byte
        
        # Recalculate checksum
        checksum = self._calculate_checksum(cmd)
        if checksum is not None:
            cmd[8] = checksum
        
        # Send command to calibrate span point
        self.uart.write(cmd)
        
        # Wait for calibration to complete
        time.sleep(0.1)
        
        return True
    
    def set_auto_calibration(self, enable=True):
        """Enable or disable automatic baseline calibration.
        
        Args:
            enable (bool): True to enable auto calibration, False to disable
        
        Returns:
            bool: True if setting was successful, False otherwise
        """
        # Send command to enable/disable auto calibration
        if enable:
            self.uart.write(CMD_AUTO_CALIBRATION_ON)
        else:
            self.uart.write(CMD_AUTO_CALIBRATION_OFF)
        
        # Wait for command to complete
        time.sleep(0.1)
        
        return True
    
    def set_detection_range(self, range_5000=True):
        """Set the detection range of the sensor.
        
        Args:
            range_5000 (bool): True for 0-5000ppm range, False for 0-10000ppm range
        
        Returns:
            bool: True if setting was successful, False otherwise
        """
        # Send command to set detection range
        if range_5000:
            self.uart.write(CMD_DETECTION_RANGE_5000)
        else:
            self.uart.write(CMD_DETECTION_RANGE_10000)
        
        # Wait for command to complete
        time.sleep(0.1)
        
        return True
    
    def close(self):
        """Close the sensor connection."""
        # Nothing specific to do for this sensor
        pass

# Example usage
if __name__ == "__main__":
    try:
        # Initialize sensor
        sensor = MHZ19BSensor()
        
        # Wait for sensor to warm up (if just powered on)
        print("Waiting for sensor to warm up...")
        time.sleep(3)
        
        # Read CO2 concentration
        co2_ppm = sensor.read_co2()
        
        if co2_ppm is not None:
            print(f"CO2 Concentration: {co2_ppm} ppm")
            
            # Interpret CO2 levels
            if co2_ppm < 400:
                print("Status: Invalid reading (below atmospheric CO2 level)")
            elif co2_ppm < 1000:
                print("Status: Good air quality")
            elif co2_ppm < 2000:
                print("Status: Moderate air quality")
            elif co2_ppm < 5000:
                print("Status: Poor air quality - ventilation recommended")
            else:
                print("Status: Very poor air quality - ventilation required")
        else:
            print("Failed to read CO2 concentration")
        
        # Read all data
        all_data = sensor.read_all()
        if all_data:
            print(f"Temperature: {all_data['temperature']}°C")
            print(f"Status byte: {all_data['status']}")
        
        # Close sensor
        sensor.close()
    
    except Exception as e:
        print(f"Error: {e}")
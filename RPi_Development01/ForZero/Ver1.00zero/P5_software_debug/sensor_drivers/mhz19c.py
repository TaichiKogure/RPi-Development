#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MH-Z19C CO2 Sensor Driver for Raspberry Pi Pico 2W - Debug Version 4.18
Version: 4.18.0-debug

This module provides a driver for the MH-Z19C CO2 sensor, which measures
carbon dioxide concentration in the air.

Features:
- UART communication with MH-Z19C sensor
- CO2 concentration measurement
- Sensor calibration functions
- Error handling and diagnostics

Pin connections:
- VCC (red) -> VBUS (5V, Pin 40)
- GND (black) -> GND (Pin 38)
- TX (green) -> GP9 (Pin 12)
- RX (blue) -> GP8 (Pin 11)

Usage:
    This file should be imported by main.py on the Pico 2W.
"""

import time
import struct
from machine import UART, Pin

class MHZ19C:
    """Driver for MH-Z19C CO2 sensor."""
    
    # Command bytes
    CMD_READ_CO2 = b'\xFF\x01\x86\x00\x00\x00\x00\x00\x79'
    CMD_CALIBRATE_ZERO = b'\xFF\x01\x87\x00\x00\x00\x00\x00\x78'
    CMD_CALIBRATE_SPAN = b'\xFF\x01\x88\x00\x00\x00\x00\x00\x77'
    CMD_SET_RANGE_5000 = b'\xFF\x01\x99\x00\x00\x00\x13\x88\x76'
    CMD_ABC_ON = b'\xFF\x01\x79\xA0\x00\x00\x00\x00\xE6'
    CMD_ABC_OFF = b'\xFF\x01\x79\x00\x00\x00\x00\x00\x86'
    
    def __init__(self, uart_id=1, tx_pin=8, rx_pin=9, baudrate=9600, debug=False):
        """Initialize the MH-Z19C sensor.
        
        Args:
            uart_id (int): UART ID (0 or 1)
            tx_pin (int): TX pin number
            rx_pin (int): RX pin number
            baudrate (int): Baud rate (default: 9600)
            debug (bool): Enable debug output
        """
        self.uart = UART(uart_id, baudrate=baudrate, tx=Pin(tx_pin), rx=Pin(rx_pin))
        self.debug = debug
        self.last_reading = 0
        self.last_reading_time = 0
        
        # Clear any pending data
        if self.uart.any():
            self.uart.read()
        
        # Wait for sensor to stabilize
        time.sleep(0.1)
    
    def _calculate_checksum(self, packet):
        """Calculate checksum for command packet."""
        checksum = 0
        for i in range(1, 8):
            checksum += packet[i]
        checksum = 0xff - (checksum % 0x100) + 1
        return checksum & 0xff
    
    def _verify_checksum(self, response):
        """Verify checksum of response packet."""
        if len(response) < 9:
            return False
        
        checksum = self._calculate_checksum(response)
        return checksum == response[8]
    
    def _send_command(self, command, response_length=9):
        """Send command to sensor and read response.
        
        Args:
            command (bytes): Command bytes
            response_length (int): Expected response length
            
        Returns:
            bytes: Response bytes or None if error
        """
        # Clear any pending data
        if self.uart.any():
            self.uart.read()
        
        # Send command
        self.uart.write(command)
        
        # Wait for response
        start_time = time.time()
        while not self.uart.any() and time.time() - start_time < 1.0:
            time.sleep(0.01)
        
        # Read response
        if self.uart.any():
            response = self.uart.read(response_length)
            
            if self.debug:
                print(f"Command: {command.hex()}")
                print(f"Response: {response.hex() if response else 'None'}")
            
            if response and len(response) == response_length:
                if self._verify_checksum(response):
                    return response
                elif self.debug:
                    print("Checksum verification failed")
        
        if self.debug:
            print("No valid response received")
        
        return None
    
    def read_co2(self):
        """Read CO2 concentration from sensor.
        
        Returns:
            int: CO2 concentration in ppm, or 0 if error
        """
        # Check if it's time to update (at least 5 seconds since last reading)
        current_time = time.time()
        if current_time - self.last_reading_time < 5:
            return self.last_reading
        
        # Send command to read CO2
        response = self._send_command(self.CMD_READ_CO2)
        
        if response and len(response) >= 9:
            # Extract CO2 value from response
            co2 = (response[2] << 8) | response[3]
            
            # Update last reading
            self.last_reading = co2
            self.last_reading_time = current_time
            
            return co2
        
        return self.last_reading if self.last_reading > 0 else 0
    
    def calibrate_zero(self):
        """Calibrate zero point (400ppm).
        
        Note: Sensor must be in fresh air (400ppm) for at least 20 minutes before calibration.
        
        Returns:
            bool: True if successful, False otherwise
        """
        response = self._send_command(self.CMD_CALIBRATE_ZERO)
        return response is not None
    
    def calibrate_span(self, span_ppm=2000):
        """Calibrate span point.
        
        Note: Sensor must be in environment with known CO2 concentration for at least 20 minutes.
        
        Args:
            span_ppm (int): Span concentration in ppm (default: 2000)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Create command with span value
        cmd = bytearray(self.CMD_CALIBRATE_SPAN)
        cmd[3] = (span_ppm >> 8) & 0xFF
        cmd[4] = span_ppm & 0xFF
        
        # Recalculate checksum
        cmd[8] = self._calculate_checksum(cmd)
        
        response = self._send_command(bytes(cmd))
        return response is not None
    
    def set_range(self, range_ppm=5000):
        """Set measurement range.
        
        Args:
            range_ppm (int): Range in ppm (default: 5000)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Create command with range value
        cmd = bytearray(self.CMD_SET_RANGE_5000)
        cmd[6] = (range_ppm >> 8) & 0xFF
        cmd[7] = range_ppm & 0xFF
        
        # Recalculate checksum
        cmd[8] = self._calculate_checksum(cmd)
        
        response = self._send_command(bytes(cmd))
        return response is not None
    
    def set_abc(self, enable=True):
        """Enable or disable Automatic Baseline Correction (ABC).
        
        Args:
            enable (bool): True to enable ABC, False to disable
            
        Returns:
            bool: True if successful, False otherwise
        """
        cmd = self.CMD_ABC_ON if enable else self.CMD_ABC_OFF
        response = self._send_command(cmd)
        return response is not None
    
    def get_readings(self):
        """Get all sensor readings as a dictionary.
        
        Returns:
            dict: Sensor readings
        """
        return {
            "co2": self.read_co2()
        }
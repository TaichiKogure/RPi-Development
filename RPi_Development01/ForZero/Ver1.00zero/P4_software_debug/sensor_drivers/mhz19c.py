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
                else:
                    if self.debug:
                        print("Checksum verification failed")
            else:
                if self.debug:
                    print(f"Invalid response length: {len(response) if response else 0}, expected {response_length}")
        else:
            if self.debug:
                print("No response from sensor")
        
        return None
    
    def read_co2(self):
        """Read CO2 concentration from sensor.
        
        Returns:
            int: CO2 concentration in ppm, or None if error
        """
        response = self._send_command(self.CMD_READ_CO2)
        
        if response:
            # CO2 concentration is in bytes 2 and 3
            co2 = (response[2] << 8) | response[3]
            
            # Update last reading
            self.last_reading = co2
            self.last_reading_time = time.time()
            
            return co2
        
        # If we couldn't get a new reading, return the last one if it's recent
        if time.time() - self.last_reading_time < 60:  # Within the last minute
            return self.last_reading
        
        return None
    
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
        
        Note: Sensor must be in a stable environment with known CO2 concentration.
        
        Args:
            span_ppm (int): Span point in ppm (default: 2000)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Create command with span value
        command = bytearray(self.CMD_CALIBRATE_SPAN)
        command[3] = (span_ppm >> 8) & 0xff
        command[4] = span_ppm & 0xff
        
        # Recalculate checksum
        checksum = 0
        for i in range(1, 8):
            checksum += command[i]
        command[8] = 0xff - (checksum % 0x100) + 1
        
        response = self._send_command(bytes(command))
        return response is not None
    
    def set_range(self, range_ppm=5000):
        """Set the detection range of the sensor.
        
        Args:
            range_ppm (int): Detection range in ppm (default: 5000)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Create command with range value
        command = bytearray(self.CMD_SET_RANGE_5000)
        command[3] = (range_ppm >> 8) & 0xff
        command[4] = range_ppm & 0xff
        
        # Recalculate checksum
        checksum = 0
        for i in range(1, 8):
            checksum += command[i]
        command[8] = 0xff - (checksum % 0x100) + 1
        
        response = self._send_command(bytes(command))
        return response is not None
    
    def set_abc(self, enabled=True):
        """Enable or disable Automatic Baseline Correction (ABC).
        
        Args:
            enabled (bool): True to enable ABC, False to disable
            
        Returns:
            bool: True if successful, False otherwise
        """
        command = self.CMD_ABC_ON if enabled else self.CMD_ABC_OFF
        response = self._send_command(command)
        return response is not None
    
    def get_all_data(self):
        """Get all sensor data as a dictionary.
        
        Returns:
            dict: Sensor data or None if error
        """
        co2 = self.read_co2()
        
        if co2 is not None:
            return {
                "co2": co2,
                "timestamp": time.time()
            }
        
        return None
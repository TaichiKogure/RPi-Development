#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MH-Z19C CO2 Sensor Driver for Raspberry Pi Pico W
Version 1.0.0

This module provides a driver for the MH-Z19C CO2 sensor connected to a Raspberry Pi Pico W.
The sensor uses UART communication and requires a 30-second warmup period before readings.

Pin connections:
- VCC (red) -> VBUS (5V, pin 40)
- GND (black) -> GND (pin 38)
- TX (green) -> GP9 (pin 12)
- RX (blue) -> GP8 (pin 11)
"""

import time
import struct
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
        self.uart = UART(uart_id, baudrate=baudrate, tx=Pin(tx_pin), rx=Pin(rx_pin))
        self.warmup_time = 30  # seconds
        self.warmup_start = time.time()
        self.is_warmed_up = False
        self.last_read_time = 0
        self.last_co2_value = 0

        print(f"MH-Z19C initialized on UART{uart_id} (TX: GP{tx_pin}, RX: GP{rx_pin})")
        print(f"Warming up for {self.warmup_time} seconds...")

    def _calculate_checksum(self, packet):
        """Calculate checksum for command packet."""
        checksum = 0
        for byte in packet[1:8]:
            checksum += byte
        checksum = ~checksum & 0xFF
        checksum += 1
        return checksum

    def _verify_checksum(self, response):
        """Verify checksum of response packet."""
        if len(response) < 9:
            return False

        checksum = 0
        for byte in response[1:8]:
            checksum += byte
        checksum = ~checksum & 0xFF
        checksum += 1

        return checksum == response[8]

    def _send_command(self, command, data=None):
        """Send command to sensor and read response.

        Args:
            command (int): Command byte
            data (list): Optional data bytes (default: None)

        Returns:
            bytes: Response from sensor or None if error
        """
        if data is None:
            data = [0, 0, 0, 0, 0]

        # Create command packet
        packet = bytearray([0xFF, 0x01, command] + data)
        packet.append(self._calculate_checksum(packet))

        # Send command
        self.uart.write(packet)

        # Wait for response
        time.sleep(0.1)

        # Read response
        if self.uart.any():
            response = self.uart.read(9)
            if response and len(response) == 9 and response[0] == 0xFF and response[1] == 0x86:
                if self._verify_checksum(response):
                    return response
                else:
                    print("MH-Z19C checksum error")
            else:
                print(f"MH-Z19C invalid response: {response}")
        else:
            print("MH-Z19C no response")

        return None

    def read_co2(self):
        """Read CO2 concentration from sensor.

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

        # Send read command
        response = self._send_command(0x86)

        if response:
            # Extract CO2 value (high byte, low byte)
            co2 = (response[2] << 8) | response[3]
            self.last_co2_value = co2
            self.last_read_time = current_time
            return co2
        else:
            print("MH-Z19C read error")
            return 0

    def calibrate_zero_point(self):
        """Calibrate zero point (400ppm).

        Note: Sensor must be in fresh air (400ppm) for at least 20 minutes before calibration.
        """
        print("MH-Z19C calibrating zero point...")
        self._send_command(0x87)
        time.sleep(1)
        print("MH-Z19C zero point calibration complete")

    def calibrate_span_point(self, span=2000):
        """Calibrate span point.

        Args:
            span (int): CO2 concentration in ppm (default: 2000)

        Note: Sensor must be in environment with known CO2 concentration for calibration.
        """
        print(f"MH-Z19C calibrating span point to {span}ppm...")
        high_byte = (span >> 8) & 0xFF
        low_byte = span & 0xFF
        self._send_command(0x88, [high_byte, low_byte, 0, 0, 0])
        time.sleep(1)
        print("MH-Z19C span point calibration complete")

    def set_detection_range(self, range_ppm=5000):
        """Set detection range.

        Args:
            range_ppm (int): Detection range in ppm (default: 5000)
        """
        if range_ppm not in [2000, 5000, 10000]:
            print(f"MH-Z19C invalid range: {range_ppm}ppm (must be 2000, 5000, or 10000)")
            return

        print(f"MH-Z19C setting detection range to {range_ppm}ppm...")
        high_byte = (range_ppm >> 8) & 0xFF
        low_byte = range_ppm & 0xFF
        self._send_command(0x99, [0, high_byte, low_byte, 0, 0])
        time.sleep(1)
        print("MH-Z19C detection range set")

# Example usage
if __name__ == "__main__":
    # Initialize sensor
    sensor = MHZ19C()

    # Wait for warmup
    print("Waiting for sensor warmup...")
    time.sleep(30)

    # Read CO2 value
    co2 = sensor.read_co2()
    print(f"CO2 concentration: {co2} ppm")

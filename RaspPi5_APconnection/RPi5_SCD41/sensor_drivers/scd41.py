#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCD41 CO2 Sensor Driver for Raspberry Pi 5
Version: 1.0.0

This module provides a driver for the SCD41 CO2 sensor, which measures
carbon dioxide concentration, temperature, and humidity in the air.

Features:
- I2C communication with SCD41 sensor
- CO2 concentration measurement
- Temperature measurement
- Humidity measurement
- Error handling and diagnostics

Pin connections:
- VCC -> 3.3V
- GND -> GND
- SCL -> SCL (GPIO 3)
- SDA -> SDA (GPIO 2)

Usage:
    This file should be imported by the data collection script.
"""

import time
import struct
import smbus2

class SCD41:
    """Driver for SCD41 CO2 sensor."""
    
    # I2C address
    I2C_ADDR = 0x62
    
    # Command codes
    CMD_START_PERIODIC_MEASUREMENT = 0x21B1
    CMD_STOP_PERIODIC_MEASUREMENT = 0x3F86
    CMD_READ_MEASUREMENT = 0xEC05
    CMD_SET_TEMPERATURE_OFFSET = 0x241D
    CMD_SET_ALTITUDE_COMPENSATION = 0x2427
    CMD_SET_AMBIENT_PRESSURE = 0xE000
    CMD_PERFORM_FORCED_CALIBRATION = 0x362F
    CMD_SET_AUTOMATIC_SELF_CALIBRATION = 0x2416
    CMD_REINIT = 0x3646
    CMD_FACTORY_RESET = 0x3632
    CMD_MEASURE_SINGLE_SHOT = 0x219D
    CMD_MEASURE_SINGLE_SHOT_RHT_ONLY = 0x2196
    CMD_POWER_DOWN = 0x36E0
    CMD_WAKE_UP = 0x36F6
    CMD_GET_SERIAL_NUMBER = 0x3682
    
    def __init__(self, bus_num=1, debug=False):
        """Initialize the SCD41 sensor.
        
        Args:
            bus_num (int): I2C bus number
            debug (bool): Enable debug output
        """
        self.bus = smbus2.SMBus(bus_num)
        self.debug = debug
        self.last_measurement_time = 0
        self.last_co2 = 0
        self.last_temperature = 0
        self.last_humidity = 0
        
        # Wait for sensor to stabilize
        time.sleep(0.1)
        
        if self.debug:
            print("SCD41 initialized on I2C bus", bus_num)
    
    def _calculate_crc(self, data):
        """Calculate CRC-8 checksum for data.
        
        Args:
            data (bytes): Data to calculate CRC for
            
        Returns:
            int: CRC-8 checksum
        """
        crc = 0xFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x31
                else:
                    crc = crc << 1
            crc &= 0xFF
        return crc
    
    def _send_command(self, command, data=None):
        """Send command to sensor.
        
        Args:
            command (int): Command code
            data (bytes, optional): Data to send with command
        """
        cmd_msb = (command >> 8) & 0xFF
        cmd_lsb = command & 0xFF
        
        if data is None:
            try:
                self.bus.write_i2c_block_data(self.I2C_ADDR, cmd_msb, [cmd_lsb])
                if self.debug:
                    print(f"Command sent: 0x{command:04X}")
            except Exception as e:
                if self.debug:
                    print(f"Error sending command 0x{command:04X}: {e}")
        else:
            try:
                # Prepare data with CRC
                buffer = []
                for i in range(0, len(data), 2):
                    buffer.append(data[i])
                    buffer.append(data[i+1])
                    buffer.append(self._calculate_crc(data[i:i+2]))
                
                # Send command and data
                self.bus.write_i2c_block_data(self.I2C_ADDR, cmd_msb, [cmd_lsb] + buffer)
                if self.debug:
                    print(f"Command with data sent: 0x{command:04X}, data: {data.hex()}")
            except Exception as e:
                if self.debug:
                    print(f"Error sending command 0x{command:04X} with data: {e}")
    
    def _read_data(self, length):
        """Read data from sensor.
        
        Args:
            length (int): Number of bytes to read
            
        Returns:
            bytes: Data read from sensor or None if error
        """
        try:
            data = self.bus.read_i2c_block_data(self.I2C_ADDR, 0, length)
            if self.debug:
                print(f"Data read: {bytes(data).hex()}")
            return bytes(data)
        except Exception as e:
            if self.debug:
                print(f"Error reading data: {e}")
            return None
    
    def _verify_data(self, data):
        """Verify data using CRC.
        
        Args:
            data (bytes): Data to verify
            
        Returns:
            bool: True if data is valid, False otherwise
        """
        if not data or len(data) % 3 != 0:
            return False
        
        for i in range(0, len(data), 3):
            if self._calculate_crc(data[i:i+2]) != data[i+2]:
                if self.debug:
                    print(f"CRC error: calculated {self._calculate_crc(data[i:i+2])}, received {data[i+2]}")
                return False
        
        return True
    
    def start_periodic_measurement(self):
        """Start periodic measurement."""
        self._send_command(self.CMD_START_PERIODIC_MEASUREMENT)
        time.sleep(0.1)  # Wait for command to process
    
    def stop_periodic_measurement(self):
        """Stop periodic measurement."""
        self._send_command(self.CMD_STOP_PERIODIC_MEASUREMENT)
        time.sleep(0.5)  # Wait for command to process
    
    def read_measurement(self):
        """Read measurement from sensor.
        
        Returns:
            tuple: (CO2 (ppm), temperature (°C), humidity (%)) or (0, 0, 0) if error
        """
        # Check if it's time to update (at least 5 seconds since last reading)
        current_time = time.time()
        if current_time - self.last_measurement_time < 5:
            return (self.last_co2, self.last_temperature, self.last_humidity)
        
        # Send command to read measurement
        self._send_command(self.CMD_READ_MEASUREMENT)
        
        # Wait for measurement to be ready
        time.sleep(0.1)
        
        # Read data (9 bytes: 2 bytes CO2 + 1 byte CRC + 2 bytes temp + 1 byte CRC + 2 bytes humidity + 1 byte CRC)
        data = self._read_data(9)
        
        if data and len(data) == 9 and self._verify_data(data):
            # Extract CO2 value (first 2 bytes)
            co2 = (data[0] << 8) | data[1]
            
            # Extract temperature value (next 2 bytes)
            temp_raw = (data[3] << 8) | data[4]
            temperature = -45 + 175 * temp_raw / 65535.0
            
            # Extract humidity value (next 2 bytes)
            humidity_raw = (data[6] << 8) | data[7]
            humidity = 100 * humidity_raw / 65535.0
            
            # Update last readings
            self.last_co2 = co2
            self.last_temperature = round(temperature, 2)
            self.last_humidity = round(humidity, 2)
            self.last_measurement_time = current_time
            
            return (co2, round(temperature, 2), round(humidity, 2))
        
        # Return last valid readings if available, otherwise zeros
        if self.last_co2 > 0:
            return (self.last_co2, self.last_temperature, self.last_humidity)
        else:
            return (0, 0, 0)
    
    def set_temperature_offset(self, offset_celsius):
        """Set temperature offset.
        
        Args:
            offset_celsius (float): Temperature offset in °C
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Convert offset to raw value
        offset_raw = int((offset_celsius * 65535.0) / 175.0)
        
        # Prepare data
        data = bytes([
            (offset_raw >> 8) & 0xFF,
            offset_raw & 0xFF
        ])
        
        # Send command
        self._send_command(self.CMD_SET_TEMPERATURE_OFFSET, data)
        time.sleep(0.1)  # Wait for command to process
        
        return True
    
    def set_altitude_compensation(self, altitude_meters):
        """Set altitude compensation.
        
        Args:
            altitude_meters (int): Altitude in meters
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Prepare data
        data = bytes([
            (altitude_meters >> 8) & 0xFF,
            altitude_meters & 0xFF
        ])
        
        # Send command
        self._send_command(self.CMD_SET_ALTITUDE_COMPENSATION, data)
        time.sleep(0.1)  # Wait for command to process
        
        return True
    
    def set_ambient_pressure(self, pressure_pa):
        """Set ambient pressure compensation.
        
        Args:
            pressure_pa (int): Ambient pressure in Pa
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Convert pressure to raw value (divide by 100)
        pressure_raw = pressure_pa // 100
        
        # Prepare data
        data = bytes([
            (pressure_raw >> 8) & 0xFF,
            pressure_raw & 0xFF
        ])
        
        # Send command
        self._send_command(self.CMD_SET_AMBIENT_PRESSURE, data)
        time.sleep(0.1)  # Wait for command to process
        
        return True
    
    def set_automatic_self_calibration(self, enable=True):
        """Enable or disable automatic self-calibration.
        
        Args:
            enable (bool): True to enable, False to disable
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Prepare data
        data = bytes([
            0x00,
            0x01 if enable else 0x00
        ])
        
        # Send command
        self._send_command(self.CMD_SET_AUTOMATIC_SELF_CALIBRATION, data)
        time.sleep(0.1)  # Wait for command to process
        
        return True
    
    def factory_reset(self):
        """Perform factory reset.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self._send_command(self.CMD_FACTORY_RESET)
        time.sleep(1.0)  # Wait for reset to complete
        
        return True
    
    def get_readings(self):
        """Get all sensor readings as a dictionary.
        
        Returns:
            dict: Sensor readings
        """
        co2, temperature, humidity = self.read_measurement()
        
        return {
            "co2": co2,
            "temperature": temperature,
            "humidity": humidity
        }

# Example usage
if __name__ == "__main__":
    try:
        print("=== SCD41 CO2 Sensor Test (Ver 1.0.0) ===")
        
        # Initialize sensor
        sensor = SCD41(debug=True)
        print("SCD41 initialized")
        
        # Start periodic measurement
        sensor.start_periodic_measurement()
        print("Periodic measurement started")
        
        # Wait for sensor warmup
        print("Waiting for sensor warmup (5 seconds)...")
        time.sleep(5)
        
        # Read measurements in a loop
        print("Reading measurements...")
        for i in range(10):
            co2, temperature, humidity = sensor.read_measurement()
            print(f"CO2: {co2} ppm, Temperature: {temperature} °C, Humidity: {humidity} %")
            time.sleep(2)
        
        # Stop periodic measurement
        sensor.stop_periodic_measurement()
        print("Periodic measurement stopped")
        
        print("Test complete!")
        
    except Exception as e:
        print(f"Error: {e}")
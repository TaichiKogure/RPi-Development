#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BME680 Sensor Driver for Raspberry Pi Pico 2W - Debug Version 4.25.1
Version: 4.25.1-debug

This module provides a driver for the BME680 environmental sensor, which measures
temperature, humidity, pressure, and gas resistance.

Features:
- I2C communication with BME680 sensor
- Temperature, humidity, pressure, and gas resistance measurements
- Calibration and compensation for accurate readings using Adafruit's algorithm
- Error handling and diagnostics
- Improved stability for Thonny compatibility
- Auto-detection of I2C address (0x76 or 0x77)

Pin connections:
- VCC -> 3.3V (Pin 36)
- GND -> GND (Pin 38)
- SCL -> GP1 (Pin 2)
- SDA -> GP0 (Pin 1)

Usage:
    This file should be imported by main.py on the Pico 2W.
"""

import time
import math
import machine
from machine import I2C, Pin
from micropython import const
try:
    import struct
except ImportError:
    import ustruct as struct

# BME680 Register Addresses
BME680_REG_CHIP_ID = const(0xD0)
BME680_CHIP_ID = const(0x61)

# Registers for calibration data
BME680_BME680_COEFF_ADDR1 = const(0x89)
BME680_BME680_COEFF_ADDR2 = const(0xE1)
BME680_BME680_RES_HEAT_0 = const(0x5A)
BME680_BME680_GAS_WAIT_0 = const(0x64)

# Registers for sensor configuration
BME680_REG_SOFTRESET = const(0xE0)
BME680_REG_CTRL_GAS = const(0x71)
BME680_REG_CTRL_HUM = const(0x72)
BME680_REG_STATUS = const(0xF3)
BME680_REG_CTRL_MEAS = const(0x74)
BME680_REG_CONFIG = const(0x75)

BME680_REG_PAGE_SELECT = const(0x73)
BME680_REG_MEAS_STATUS = const(0x1D)
BME680_REG_PDATA = const(0x1F)
BME680_REG_TDATA = const(0x22)
BME680_REG_HDATA = const(0x25)

BME680_SAMPLERATES = (0, 1, 2, 4, 8, 16)
BME680_FILTERSIZES = (0, 1, 3, 7, 15, 31, 63, 127)

BME680_RUNGAS = const(0x10)

# Lookup tables for gas calculations
_LOOKUP_TABLE_1 = (2147483647.0, 2147483647.0, 2147483647.0, 2147483647.0, 2147483647.0,
                   2126008810.0, 2147483647.0, 2130303777.0, 2147483647.0, 2147483647.0,
                   2143188679.0, 2136746228.0, 2147483647.0, 2126008810.0, 2147483647.0,
                   2147483647.0)

_LOOKUP_TABLE_2 = (4096000000.0, 2048000000.0, 1024000000.0, 512000000.0, 255744255.0, 127110228.0,
                   64000000.0, 32258064.0, 16016016.0, 8000000.0, 4000000.0, 2000000.0, 1000000.0,
                   500000.0, 250000.0, 125000.0)

# Debug settings
DEBUG_PRINT = True  # Set to False to disable debug prints

def _read24(arr):
    """Parse an unsigned 24-bit value as a floating point and return it."""
    ret = 0.0
    for b in arr:
        ret *= 256.0
        ret += float(b & 0xFF)
    return ret

class BME680_I2C:
    """Driver for BME680 gas, pressure, temperature and humidity sensor.
    Based on Adafruit's BME680 driver."""

    @staticmethod
    def detect_address(i2c):
        """Detect the correct I2C address for the BME680 sensor.

        Args:
            i2c (I2C): I2C interface

        Returns:
            int: The detected I2C address (0x76 or 0x77) or None if not found
        """
        possible_addresses = [0x76, 0x77]

        for addr in possible_addresses:
            try:
                # Try to read the chip ID register
                chip_id = i2c.readfrom_mem(addr, BME680_REG_CHIP_ID, 1)[0]
                if chip_id == BME680_CHIP_ID:
                    if DEBUG_PRINT:
                        print(f"BME680 found at address {hex(addr)} with correct chip ID")
                    return addr
            except Exception as e:
                if DEBUG_PRINT:
                    print(f"No BME680 at address {hex(addr)}: {e}")
        
        if DEBUG_PRINT:
            print("BME680 not found at any address")
        return None

    def __init__(self, i2c, address=0x77, debug=False):
        """Initialize the BME680 sensor.

        Args:
            i2c (I2C): I2C interface
            address (int): I2C address (default: 0x77)
            debug (bool): Enable debug output
        """
        self.i2c = i2c
        self.address = address
        self.debug = debug
        self._chip_id = self._read_byte(BME680_REG_CHIP_ID)

        if self._chip_id != BME680_CHIP_ID:
            raise RuntimeError("Failed to find BME680! Chip ID 0x%x" % self._chip_id)

        if DEBUG_PRINT:
            print(f"BME680 found with correct chip ID")

        self._read_calibration()

        # Set humidity oversampling to 1x
        self._write_byte(BME680_REG_CTRL_HUM, 0x01)
        # Set temperature oversampling to 2x and pressure oversampling to 4x
        self._write_byte(BME680_REG_CTRL_MEAS, 0x24)
        # Set filter size to 3
        self._write_byte(BME680_REG_CONFIG, 0x03)

        # Enable gas measurement
        ctrl_gas = self._read_byte(BME680_REG_CTRL_GAS)
        ctrl_gas |= 0x10  # Set bit 4 (RUNGAS)
        self._write_byte(BME680_REG_CTRL_GAS, ctrl_gas)

        # Set gas heater temperature to 320°C and duration to 150ms
        self._write_byte(BME680_BME680_RES_HEAT_0, 0x73)
        self._write_byte(BME680_BME680_GAS_WAIT_0, 0x65)

        # Initial reading
        self.temperature = 0
        self.pressure = 0
        self.humidity = 0
        self.gas_resistance = 0
        self.perform_measurement()

    def _read_calibration(self):
        """Read calibration data from the sensor."""
        # Read temperature calibration data
        coeff = self._read_bytes(BME680_BME680_COEFF_ADDR1, 25)
        coeff += self._read_bytes(BME680_BME680_COEFF_ADDR2, 16)

        # Temperature related coefficients
        self.temp_calibration = []
        self.temp_calibration.append(coeff[33])
        self.temp_calibration.append(coeff[32] << 8 | coeff[31])
        self.temp_calibration.append(coeff[35] << 8 | coeff[34])

        # Pressure related coefficients
        self.pressure_calibration = []
        self.pressure_calibration.append(coeff[3] << 8 | coeff[2])
        self.pressure_calibration.append(coeff[5] << 8 | coeff[4])
        self.pressure_calibration.append(coeff[7])
        self.pressure_calibration.append(coeff[6])
        self.pressure_calibration.append(coeff[9])
        self.pressure_calibration.append(coeff[8])
        self.pressure_calibration.append(coeff[11] << 8 | coeff[10])
        self.pressure_calibration.append(coeff[13] << 8 | coeff[12])
        self.pressure_calibration.append(coeff[15])
        self.pressure_calibration.append(coeff[14])

        # Humidity related coefficients
        self.humidity_calibration = []
        self.humidity_calibration.append(coeff[26])
        self.humidity_calibration.append(coeff[25])
        self.humidity_calibration.append(coeff[28] << 4 | (coeff[27] & 0x0F))
        self.humidity_calibration.append(coeff[27] >> 4)
        self.humidity_calibration.append(coeff[29])
        self.humidity_calibration.append(coeff[30])

        # Gas heater related coefficients
        self.gas_calibration = []
        self.gas_calibration.append(coeff[37])
        self.gas_calibration.append(coeff[36])
        self.gas_calibration.append(coeff[39])
        self.gas_calibration.append(coeff[38])
        self.gas_calibration.append(coeff[41])
        self.gas_calibration.append(coeff[40])
        self.gas_calibration.append(coeff[43])
        self.gas_calibration.append(coeff[42])
        self.gas_calibration.append(coeff[45])
        self.gas_calibration.append(coeff[44])

        if DEBUG_PRINT:
            print("BME680 calibration read successfully")

    def _read_byte(self, register):
        """Read a byte from the specified register."""
        return self.i2c.readfrom_mem(self.address, register, 1)[0]

    def _read_bytes(self, register, length):
        """Read multiple bytes from the specified register."""
        return self.i2c.readfrom_mem(self.address, register, length)

    def _write_byte(self, register, value):
        """Write a byte to the specified register."""
        self.i2c.writeto_mem(self.address, register, bytes([value]))

    def perform_measurement(self):
        """Perform a measurement and update the sensor values."""
        # Set the sensor to forced mode to trigger a measurement
        ctrl_meas = self._read_byte(BME680_REG_CTRL_MEAS)
        ctrl_meas = (ctrl_meas & 0xFC) | 0x01  # Set mode to forced (01)
        self._write_byte(BME680_REG_CTRL_MEAS, ctrl_meas)

        # Wait for the measurement to complete
        start_time = time.time()
        while time.time() - start_time < 2.0:  # Timeout after 2 seconds
            status = self._read_byte(BME680_REG_MEAS_STATUS)
            if (status & 0x80) == 0:  # Check if measurement is complete
                break
            time.sleep(0.01)

        # Read the raw data
        data = self._read_bytes(BME680_REG_PDATA, 8)
        
        # Parse pressure, temperature, and humidity
        pressure_raw = ((data[0] << 16) | (data[1] << 8) | data[2]) >> 4
        temp_raw = ((data[3] << 16) | (data[4] << 8) | data[5]) >> 4
        humidity_raw = (data[6] << 8) | data[7]

        # Read gas resistance data
        self._write_byte(BME680_REG_PAGE_SELECT, 0x00)  # Select page 0
        status = self._read_byte(BME680_REG_MEAS_STATUS)
        gas_valid = (status & 0x20) == 0x20
        heat_stab = (status & 0x10) == 0x10
        
        gas_r_lsb = self._read_byte(0x2B)
        gas_r_msb = self._read_byte(0x2A)
        
        gas_resistance_raw = (gas_r_msb << 2) | (gas_r_lsb >> 6)
        gas_range = gas_r_lsb & 0x0F

        # Calculate temperature
        var1 = (temp_raw / 16384.0 - self.temp_calibration[0] / 1024.0) * self.temp_calibration[1]
        var2 = ((temp_raw / 131072.0 - self.temp_calibration[0] / 8192.0) * (
            temp_raw / 131072.0 - self.temp_calibration[0] / 8192.0)) * self.temp_calibration[2] * 16.0
        t_fine = var1 + var2
        self.temperature = t_fine / 5120.0

        # Calculate pressure
        var1 = (t_fine / 2.0) - 64000.0
        var2 = var1 * var1 * self.pressure_calibration[5] / 32768.0
        var2 = var2 + var1 * self.pressure_calibration[4] * 2.0
        var2 = (var2 / 4.0) + (self.pressure_calibration[3] * 65536.0)
        var1 = (self.pressure_calibration[2] * var1 * var1 / 524288.0 + 
                self.pressure_calibration[1] * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self.pressure_calibration[0]
        
        # Avoid division by zero
        if var1 == 0.0:
            self.pressure = 0
        else:
            pressure = 1048576.0 - pressure_raw
            pressure = ((pressure - (var2 / 4096.0)) * 6250.0) / var1
            var1 = self.pressure_calibration[8] * pressure * pressure / 2147483648.0
            var2 = pressure * self.pressure_calibration[7] / 32768.0
            pressure = pressure + (var1 + var2 + self.pressure_calibration[6]) / 16.0
            self.pressure = pressure / 100.0  # Convert to hPa

        # Calculate humidity
        temp_scaled = t_fine / 5120.0
        var1 = humidity_raw - (self.humidity_calibration[0] * 16.0 + 
                              (self.humidity_calibration[3] / 2.0) * temp_scaled)
        var2 = var1 * (self.humidity_calibration[1] / 65536.0 * (1.0 + 
                      self.humidity_calibration[2] / 67108864.0 * temp_scaled * 
                      (1.0 + self.humidity_calibration[5] / 67108864.0 * temp_scaled)))
        var3 = self.humidity_calibration[4] / 100.0
        var4 = var3 * var3 * var3 * var2
        var5 = var4 * (1.0 - self.humidity_calibration[0] * var2 / 524288.0)
        
        if var5 > 100.0:
            var5 = 100.0
        elif var5 < 0.0:
            var5 = 0.0
            
        self.humidity = var5

        # Calculate gas resistance
        if gas_valid and heat_stab:
            gas_range_int = gas_range
            var1 = ((1340.0 + 5.0 * self.gas_calibration[0]) * _LOOKUP_TABLE_1[gas_range_int]) / 65536.0
            var2 = ((self.gas_calibration[1] + 8.0) * _LOOKUP_TABLE_2[gas_range_int]) / 100.0
            var3 = 1.0 + var1 * var2 / 100.0
            var4 = 1.0 / var3
            
            var5 = 262144.0 / gas_resistance_raw
            var6 = var4 * var5
            
            self.gas_resistance = int(var6)
        else:
            self.gas_resistance = 0

        return self.temperature, self.humidity, self.pressure, self.gas_resistance

class BME680:
    """Simplified interface for BME680 sensor."""
    
    def __init__(self, i2c=None, address=None):
        """Initialize the BME680 sensor.
        
        Args:
            i2c (I2C): I2C interface (if None, will be created)
            address (int): I2C address (if None, will be auto-detected)
        """
        # Create I2C interface if not provided
        if i2c is None:
            i2c = I2C(0, sda=Pin(0), scl=Pin(1))
        
        # Auto-detect address if not provided
        if address is None:
            address = BME680_I2C.detect_address(i2c)
            if address is None:
                raise RuntimeError("BME680 not found on I2C bus")
        
        print(f"Initializing BME680 on I2C address {hex(address)}")
        
        # Create sensor interface
        self.sensor = BME680_I2C(i2c, address)
        
        # Initialize values
        self.temperature = 0
        self.humidity = 0
        self.pressure = 0
        self.gas_resistance = 0
        
        # Perform initial measurement
        self.perform_measurement()
        
        print("BME680 initialization complete")
    
    def perform_measurement(self):
        """Perform a measurement and update the sensor values."""
        try:
            self.temperature, self.humidity, self.pressure, self.gas_resistance = self.sensor.perform_measurement()
            return True
        except Exception as e:
            print(f"Error performing measurement: {e}")
            return False
    
    def get_temperature(self):
        """Get the temperature in degrees Celsius."""
        return self.temperature
    
    def get_humidity(self):
        """Get the relative humidity in percent."""
        return self.humidity
    
    def get_pressure(self):
        """Get the pressure in hPa."""
        return self.pressure
    
    def get_gas_resistance(self):
        """Get the gas resistance in ohms."""
        return self.gas_resistance
    
    def get_all_data(self):
        """Get all sensor data as a dictionary."""
        self.perform_measurement()
        return {
            "temperature": self.temperature,
            "humidity": self.humidity,
            "pressure": self.pressure,
            "gas_resistance": self.gas_resistance
        }
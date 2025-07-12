#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BME680 Sensor Driver for Raspberry Pi Pico 2W - Debug Version 4.18
Version: 4.18.0-debug

This module provides a driver for the BME680 environmental sensor, which measures
temperature, humidity, pressure, and gas resistance.

Features:
- I2C communication with BME680 sensor
- Temperature, humidity, pressure, and gas resistance measurements
- Calibration and compensation for accurate readings
- Error handling and diagnostics

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
from machine import I2C, Pin
from micropython import const

# BME680 Register Addresses
BME680_REG_CHIP_ID = const(0xD0)
BME680_CHIP_ID = const(0x61)

# Registers for calibration data
BME680_REG_COEFF_ADDR1 = const(0x89)
BME680_REG_COEFF_ADDR2 = const(0xE1)

# Registers for sensor configuration
BME680_REG_CTRL_HUM = const(0x72)
BME680_REG_CTRL_MEAS = const(0x74)
BME680_REG_CONFIG = const(0x75)
BME680_REG_CTRL_GAS_0 = const(0x70)
BME680_REG_CTRL_GAS_1 = const(0x71)
BME680_CTRL_GAS_ADDR = const(0x71)

# Registers for sensor data
BME680_REG_DATA_ADDR = const(0x1D)
BME680_REG_MEAS_STATUS = const(0x1D)

# Oversampling settings
BME680_OS_NONE = const(0)
BME680_OS_1X = const(1)
BME680_OS_2X = const(2)
BME680_OS_4X = const(3)
BME680_OS_8X = const(4)
BME680_OS_16X = const(5)

# IIR filter settings
BME680_FILTER_OFF = const(0)
BME680_FILTER_1 = const(1)
BME680_FILTER_3 = const(2)
BME680_FILTER_7 = const(3)
BME680_FILTER_15 = const(4)
BME680_FILTER_31 = const(5)
BME680_FILTER_63 = const(6)
BME680_FILTER_127 = const(7)

# Gas heater settings
BME680_HEATR_TEMP_OFF = const(0)
BME680_HEATR_DUR_OFF = const(0)

class BME680_I2C:
    """Driver for BME680 gas, pressure, temperature and humidity sensor."""

    def __init__(self, i2c, address=0x77, temp_offset=0):
        """Initialize the BME680 sensor.
        
        Args:
            i2c (I2C): I2C interface
            address (int): I2C address of the sensor (0x76 or 0x77)
            temp_offset (float): Temperature offset in degrees Celsius
        """
        self.i2c = i2c
        self.address = address
        self.temp_offset = temp_offset
        
        # Check if sensor is present
        print(f"Initializing BME680 on I2C address {hex(address)}")
        chip_id = self._read_byte(BME680_REG_CHIP_ID)
        if chip_id != BME680_CHIP_ID:
            raise RuntimeError(f"BME680 not found, invalid chip ID: {hex(chip_id)}")
        print("BME680 found with correct chip ID")
        
        # Read calibration data
        self._read_calibration()
        print("BME680 calibration read successfully")
        
        # Configure sensor
        self._configure()
        print("BME680 initialization complete")
        
        # Initialize data
        self._last_reading_time = 0
        self._temperature = 0
        self._pressure = 0
        self._humidity = 0
        self._gas = 0
        
        # Take initial reading
        self.update()

    def _read_byte(self, register):
        """Read a single byte from the given register."""
        return self.i2c.readfrom_mem(self.address, register, 1)[0]
    
    def _read_bytes(self, register, length):
        """Read multiple bytes from the given register."""
        return self.i2c.readfrom_mem(self.address, register, length)
    
    def _write_byte(self, register, value):
        """Write a single byte to the given register."""
        self.i2c.writeto_mem(self.address, register, bytes([value]))
    
    def _read_calibration(self):
        """Read calibration data from the sensor."""
        # Read temperature and pressure calibration data (coefficients 1)
        coeff1 = self._read_bytes(BME680_REG_COEFF_ADDR1, 25)
        
        # Read humidity calibration data (coefficients 2)
        coeff2 = self._read_bytes(BME680_REG_COEFF_ADDR2, 16)
        
        # Temperature calibration coefficients
        self.par_t1 = (coeff1[9] << 8) | coeff1[8]
        self.par_t2 = (coeff1[11] << 8) | coeff1[10]
        self.par_t2 = self._twos_comp(self.par_t2, 16)
        self.par_t3 = coeff1[12]
        self.par_t3 = self._twos_comp(self.par_t3, 8)
        
        # Pressure calibration coefficients
        self.par_p1 = (coeff1[1] << 8) | coeff1[0]
        self.par_p2 = (coeff1[3] << 8) | coeff1[2]
        self.par_p2 = self._twos_comp(self.par_p2, 16)
        self.par_p3 = coeff1[4]
        self.par_p3 = self._twos_comp(self.par_p3, 8)
        self.par_p4 = (coeff1[7] << 8) | coeff1[6]
        self.par_p4 = self._twos_comp(self.par_p4, 16)
        self.par_p5 = (coeff1[15] << 8) | coeff1[14]
        self.par_p5 = self._twos_comp(self.par_p5, 16)
        self.par_p6 = coeff1[16]
        self.par_p6 = self._twos_comp(self.par_p6, 8)
        self.par_p7 = coeff1[17]
        self.par_p7 = self._twos_comp(self.par_p7, 8)
        self.par_p8 = (coeff1[19] << 8) | coeff1[18]
        self.par_p8 = self._twos_comp(self.par_p8, 16)
        self.par_p9 = (coeff1[21] << 8) | coeff1[20]
        self.par_p9 = self._twos_comp(self.par_p9, 16)
        self.par_p10 = coeff1[22]
        
        # Humidity calibration coefficients
        self.par_h1 = (coeff2[2] << 4) | (coeff2[1] & 0x0F)
        self.par_h2 = (coeff2[0] << 4) | (coeff2[1] >> 4)
        self.par_h3 = coeff2[3]
        self.par_h3 = self._twos_comp(self.par_h3, 8)
        self.par_h4 = coeff2[4]
        self.par_h4 = self._twos_comp(self.par_h4, 8)
        self.par_h5 = coeff2[5]
        self.par_h5 = self._twos_comp(self.par_h5, 8)
        self.par_h6 = coeff2[6]
        self.par_h7 = coeff2[7]
        self.par_h7 = self._twos_comp(self.par_h7, 8)
        
        # Gas resistance calibration coefficients
        self.par_g1 = coeff2[8]
        self.par_g1 = self._twos_comp(self.par_g1, 8)
        self.par_g2 = (coeff2[10] << 8) | coeff2[9]
        self.par_g2 = self._twos_comp(self.par_g2, 16)
        self.par_g3 = coeff2[11]
        self.res_heat_range = (self._read_byte(0x02) >> 4) & 0x03
        self.res_heat_val = self._twos_comp(self._read_byte(0x00), 8)
        self.range_sw_err = (self._read_byte(0x04) >> 4) & 0x0F
    
    def _twos_comp(self, val, bits):
        """Compute the 2's complement of val for the given number of bits."""
        if val & (1 << (bits - 1)):
            val -= (1 << bits)
        return val
    
    def _configure(self):
        """Configure the sensor for normal operation."""
        # Set humidity oversampling to 1x
        self._write_byte(BME680_REG_CTRL_HUM, BME680_OS_1X)
        
        # Set temperature and pressure oversampling to 4x, and set mode to sleep
        self._write_byte(BME680_REG_CTRL_MEAS, (BME680_OS_4X << 5) | (BME680_OS_4X << 2) | 0)
        
        # Set IIR filter to 3
        self._write_byte(BME680_REG_CONFIG, BME680_FILTER_3 << 2)
        
        # Enable gas measurement with heater
        ctrl_gas = self._read_byte(BME680_CTRL_GAS_ADDR)
        ctrl_gas |= 0x10  # heater enable bit
        self._write_byte(BME680_CTRL_GAS_ADDR, ctrl_gas)
        
        # Set gas heater temperature to 320°C and duration to 150ms
        temp = 320  # Target temperature in Celsius
        amb_temp = 25  # Ambient temperature (assumed)
        
        # Calculate heater resistance
        heatr_res = int(3.4 + ((temp - 20) * 0.6 / 100) * 1000)
        heatr_res = min(max(0, heatr_res), 255)  # Limit to 0-255
        self._write_byte(0x5A, heatr_res)
        
        # Set gas heater duration
        heatr_dur = 150  # Duration in ms
        self._write_byte(0x64, heatr_dur)
        
        # Set gas heater profile 0
        self._write_byte(0x5B, 0)
    
    def update(self):
        """Update sensor readings."""
        # Check if it's time to update (at least 1 second since last reading)
        current_time = time.time()
        if current_time - self._last_reading_time < 1:
            return
        
        # Set mode to forced (one-shot measurement)
        ctrl_meas = self._read_byte(BME680_REG_CTRL_MEAS)
        self._write_byte(BME680_REG_CTRL_MEAS, (ctrl_meas & 0xFC) | 0x01)
        
        # Wait for measurement to complete
        while self._read_byte(BME680_REG_MEAS_STATUS) & 0x80 == 0:
            time.sleep(0.01)
        
        # Read raw data
        data = self._read_bytes(BME680_REG_DATA_ADDR, 15)
        
        # Parse temperature data
        temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        
        # Parse pressure data
        pres_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        
        # Parse humidity data
        hum_raw = (data[6] << 8) | data[7]
        
        # Parse gas resistance data
        gas_valid = (data[14] >> 5) & 1
        heat_stab = (data[14] >> 4) & 1
        gas_range = data[14] & 0x0F
        gas_res_raw = (data[13] << 2) | ((data[14] >> 6) & 0x03)
        
        # Compensate temperature
        var1 = (temp_raw / 16384.0 - self.par_t1 / 1024.0) * self.par_t2
        var2 = ((temp_raw / 131072.0 - self.par_t1 / 8192.0) ** 2) * self.par_t3 * 16
        t_fine = var1 + var2
        self._temperature = t_fine / 5120.0 + self.temp_offset
        
        # Compensate pressure
        var1 = (t_fine / 2.0) - 64000.0
        var2 = var1 * var1 * self.par_p6 / 131072.0
        var2 = var2 + (var1 * self.par_p5 * 2.0)
        var2 = (var2 / 4.0) + (self.par_p4 * 65536.0)
        var1 = (self.par_p3 * var1 * var1 / 16384.0 + self.par_p2 * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self.par_p1
        
        if var1 == 0:
            self._pressure = 0
        else:
            p = 1048576.0 - pres_raw
            p = ((p - (var2 / 4096.0)) * 6250.0) / var1
            var1 = self.par_p9 * p * p / 2147483648.0
            var2 = p * self.par_p8 / 32768.0
            p = p + (var1 + var2 + self.par_p7) / 16.0
            self._pressure = p / 100.0  # Convert to hPa
        
        # Compensate humidity
        temp_comp = t_fine / 5120.0
        var1 = hum_raw - (self.par_h1 * 16.0 + (self.par_h3 / 2.0) * temp_comp)
        var2 = var1 * (self.par_h2 / 262144.0 * (1.0 + self.par_h4 / 16384.0 * temp_comp + self.par_h5 / 1048576.0 * temp_comp * temp_comp))
        var3 = self.par_h6 / 16384.0
        var4 = self.par_h7 / 2097152.0
        h = var2 + ((var3 + var4 * temp_comp) * var2 * var2)
        
        if h > 100:
            h = 100
        elif h < 0:
            h = 0
        
        self._humidity = h
        
        # Compensate gas resistance
        if gas_valid and heat_stab:
            gas_range_lookup = [
                2147483647, 2147483647, 2147483647, 2147483647, 2147483647, 2126008810, 2147483647,
                2130303777, 2147483647, 2147483647, 2143188679, 2136746228, 2147483647, 2126008810,
                2147483647, 2147483647
            ]
            
            var1 = 262144 >> gas_range
            var2 = gas_res_raw - 512
            var2 *= 3
            var2 = 4096 + var2
            
            calc_gas_res = (1340 + (5 * self.range_sw_err)) * var1
            calc_gas_res = (calc_gas_res * 32768) // var2
            calc_gas_res = calc_gas_res * 5 // 8
            
            self._gas = calc_gas_res
        else:
            self._gas = 0
        
        self._last_reading_time = current_time
    
    @property
    def temperature(self):
        """Get the temperature in degrees Celsius."""
        self.update()
        return self._temperature
    
    @property
    def pressure(self):
        """Get the pressure in hPa."""
        self.update()
        return self._pressure
    
    @property
    def humidity(self):
        """Get the relative humidity in percent."""
        self.update()
        return self._humidity
    
    @property
    def gas(self):
        """Get the gas resistance in ohms."""
        self.update()
        return self._gas
    
    def get_readings(self):
        """Get all sensor readings as a dictionary."""
        self.update()
        return {
            "temperature": self._temperature,
            "pressure": self._pressure,
            "humidity": self._humidity,
            "gas_resistance": self._gas
        }

# Example usage
if __name__ == "__main__":
    try:
        print("=== BME680 Sensor Test (Ver 4.18.0) ===")
        
        # Initialize I2C
        i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=100000)
        
        # Scan for I2C devices
        devices = i2c.scan()
        print(f"I2C devices found: {[hex(addr) for addr in devices]}")
        
        # Initialize BME680
        bme = BME680_I2C(i2c, address=0x77)
        
        # Read and print sensor data in a loop
        print("Reading sensor data...")
        for i in range(10):
            readings = bme.get_readings()
            print(f"Temperature: {readings['temperature']:.1f}°C")
            print(f"Humidity: {readings['humidity']:.1f}%")
            print(f"Pressure: {readings['pressure']:.1f}hPa")
            print(f"Gas Resistance: {readings['gas_resistance']:.0f}Ω")
            print("---")
            time.sleep(1)
        
        print("Test complete!")
        
    except Exception as e:
        print(f"Error: {e}")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BME680 Sensor Driver for Raspberry Pi Pico 2W - Solo Version 4.44
Version: 4.44.0-solo

This module provides a driver for the BME680 environmental sensor, which measures
temperature, humidity, pressure, and gas resistance.

Features:
- I2C communication with BME680 sensor
- Temperature, humidity, pressure, and gas resistance measurements
- Calibration and compensation for accurate readings using Adafruit's algorithm
- Error handling and diagnostics
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
                    print(f"BME680 found at address {hex(addr)} with correct chip ID")
                    return addr
            except Exception as e:
                print(f"No BME680 at address {hex(addr)}: {e}")

        return None

    def __init__(self, i2c, address=None, temp_offset=0, refresh_rate=10):
        """Initialize the BME680 sensor.

        Args:
            i2c (I2C): I2C interface
            address (int, optional): I2C address of the sensor (0x76 or 0x77).
                                    If None, auto-detect the address.
            temp_offset (float): Temperature offset in degrees Celsius
            refresh_rate (int): Maximum number of readings per second
        """
        self.i2c = i2c
        self.temp_offset = temp_offset

        # Auto-detect address if not specified
        if address is None:
            detected_address = self.detect_address(i2c)
            if detected_address is None:
                raise RuntimeError("BME680 not found at any address")
            self.address = detected_address
            print(f"Auto-detected BME680 at address {hex(self.address)}")
        else:
            self.address = address
            print(f"Using specified BME680 address {hex(self.address)}")

        try:
            # Soft reset the sensor
            self._write(BME680_REG_SOFTRESET, [0xB6])
            time.sleep(0.005)  # Wait for reset to complete

            # Check if sensor is present at the specified address
            chip_id = self._read_byte(BME680_REG_CHIP_ID)
            if chip_id != BME680_CHIP_ID:
                raise RuntimeError(f"BME680 not found, invalid chip ID: {hex(chip_id)}")
            print("BME680 found with correct chip ID")

            # Read calibration data
            self._read_calibration()
            print("BME680 calibration read successfully")

            # Set up heater
            self._write(BME680_BME680_RES_HEAT_0, [0x73])
            self._write(BME680_BME680_GAS_WAIT_0, [0x65])

            # Default settings
            self.sea_level_pressure = 1013.25  # Pressure in hectoPascals at sea level
            self._pressure_oversample = 0b011   # x4
            self._temp_oversample = 0b100       # x8
            self._humidity_oversample = 0b010   # x2
            self._filter = 0b010                # Filter coefficient 3

            # Initialize data
            self._adc_pres = None
            self._adc_temp = None
            self._adc_hum = None
            self._adc_gas = None
            self._gas_range = None
            self._t_fine = None

            self._last_reading = time.ticks_ms()
            self._min_refresh_time = 1000 // refresh_rate

            # Enable gas measurement with heater
            ctrl_gas = self._read_byte(BME680_REG_CTRL_GAS)
            ctrl_gas |= 0x10  # heater enable bit
            self._write(BME680_REG_CTRL_GAS, [ctrl_gas])

            # Set gas heater temperature to 320°C
            temp = 320  # Target temperature in Celsius
            amb_temp = 25  # Ambient temperature (assumed)

            # Calculate heater resistance
            heatr_res = int(3.4 + ((temp - 20) * 0.6 / 100) * 1000)
            heatr_res = min(max(0, heatr_res), 255)  # Limit to 0-255
            self._write(BME680_BME680_RES_HEAT_0, [heatr_res])

            print("BME680 initialization complete")

            # Take initial reading
            self._perform_reading()
        except Exception as e:
            print(f"Error initializing BME680: {e}")
            raise

    def _read_byte(self, register):
        """Read a single byte from the given register."""
        try:
            return self._read(register, 1)[0]
        except Exception as e:
            print(f"Error reading byte from register {hex(register)}: {e}")
            raise

    def _read(self, register, length):
        """Read multiple bytes from the given register."""
        try:
            result = bytearray(length)
            self.i2c.readfrom_mem_into(self.address, register & 0xff, result)
            return result
        except Exception as e:
            print(f"Error reading from register {hex(register)}: {e}")
            raise

    def _write(self, register, values):
        """Write an array of bytes to the given register."""
        try:
            for value in values:
                self.i2c.writeto_mem(self.address, register, bytearray([value & 0xFF]))
                register += 1
        except Exception as e:
            print(f"Error writing to register {hex(register)}: {e}")
            raise

    def _read_calibration(self):
        """Read & save the calibration coefficients"""
        try:
            coeff = self._read(BME680_BME680_COEFF_ADDR1, 25)
            coeff += self._read(BME680_BME680_COEFF_ADDR2, 16)

            coeff = list(struct.unpack('<hbBHhbBhhbbHhhBBBHbbbBbHhbb', bytes(coeff[1:39])))
            coeff = [float(i) for i in coeff]

            self._temp_calibration = [coeff[x] for x in [23, 0, 1]]
            self._pressure_calibration = [coeff[x] for x in [3, 4, 5, 7, 8, 10, 9, 12, 13, 14]]
            self._humidity_calibration = [coeff[x] for x in [17, 16, 18, 19, 20, 21, 22]]
            self._gas_calibration = [coeff[x] for x in [25, 24, 26]]

            # Flip around H1 & H2
            self._humidity_calibration[1] *= 16
            self._humidity_calibration[1] += self._humidity_calibration[0] % 16
            self._humidity_calibration[0] /= 16

            self._heat_range = (self._read_byte(0x02) & 0x30) / 16
            self._heat_val = self._read_byte(0x00)
            self._sw_err = (self._read_byte(0x04) & 0xF0) / 16

            print("Calibration data loaded successfully")
        except Exception as e:
            print(f"Error reading calibration data: {e}")
            raise

    def _perform_reading(self):
        """Perform a single-shot reading from the sensor and fill internal data structure for
           calculations"""
        try:
            # Check if it's time to update
            expired = time.ticks_diff(self._last_reading, time.ticks_ms()) * time.ticks_diff(0, 1)
            if 0 <= expired < self._min_refresh_time:
                time.sleep_ms(self._min_refresh_time - expired)

            # Set filter
            self._write(BME680_REG_CONFIG, [self._filter << 2])
            # Turn on temp oversample & pressure oversample
            self._write(BME680_REG_CTRL_MEAS,
                        [(self._temp_oversample << 5)|(self._pressure_oversample << 2)])
            # Turn on humidity oversample
            self._write(BME680_REG_CTRL_HUM, [self._humidity_oversample])
            # Gas measurements enabled
            self._write(BME680_REG_CTRL_GAS, [BME680_RUNGAS])

            # Enable single shot mode
            ctrl = self._read_byte(BME680_REG_CTRL_MEAS)
            ctrl = (ctrl & 0xFC) | 0x01  # Enable single shot!
            self._write(BME680_REG_CTRL_MEAS, [ctrl])

            # Wait for measurement to complete
            new_data = False
            wait_start = time.time()
            while not new_data:
                data = self._read(BME680_REG_MEAS_STATUS, 15)
                new_data = data[0] & 0x80 != 0
                time.sleep(0.005)
                machine.idle()  # Allow background processing

                # Timeout after 1 second
                if time.time() - wait_start > 1:
                    print("BME680 measurement timeout")
                    return

            self._last_reading = time.ticks_ms()

            # Parse raw data
            self._adc_pres = _read24(data[2:5]) / 16
            self._adc_temp = _read24(data[5:8]) / 16
            self._adc_hum = struct.unpack('>H', bytes(data[8:10]))[0]
            self._adc_gas = int(struct.unpack('>H', bytes(data[13:15]))[0] / 64)
            self._gas_range = data[14] & 0x0F

            # Calculate temperature
            var1 = (self._adc_temp / 8) - (self._temp_calibration[0] * 2)
            var2 = (var1 * self._temp_calibration[1]) / 2048
            var3 = ((var1 / 2) * (var1 / 2)) / 4096
            var3 = (var3 * self._temp_calibration[2] * 16) / 16384
            self._t_fine = int(var2 + var3)

        except Exception as e:
            print(f"Error performing BME680 reading: {e}")
            # Keep previous readings

    @property
    def temperature(self):
        """The compensated temperature in degrees celsius."""
        try:
            self._perform_reading()
            calc_temp = (((self._t_fine * 5) + 128) / 256)
            return (calc_temp / 100) + self.temp_offset
        except Exception as e:
            print(f"Error reading temperature: {e}")
            # Return last calculated value or 0 if not available
            return 0 if self._t_fine is None else (((self._t_fine * 5) + 128) / 256) / 100 + self.temp_offset

    @property
    def pressure(self):
        """The barometric pressure in hectoPascals"""
        try:
            self._perform_reading()
            var1 = (self._t_fine / 2) - 64000
            var2 = ((var1 / 4) * (var1 / 4)) / 2048
            var2 = (var2 * self._pressure_calibration[5]) / 4
            var2 = var2 + (var1 * self._pressure_calibration[4] * 2)
            var2 = (var2 / 4) + (self._pressure_calibration[3] * 65536)
            var1 = (((((var1 / 4) * (var1 / 4)) / 8192) *
                    (self._pressure_calibration[2] * 32) / 8) +
                    ((self._pressure_calibration[1] * var1) / 2))
            var1 = var1 / 262144
            var1 = ((32768 + var1) * self._pressure_calibration[0]) / 32768
            calc_pres = 1048576 - self._adc_pres
            calc_pres = (calc_pres - (var2 / 4096)) * 3125
            calc_pres = (calc_pres / var1) * 2
            var1 = (self._pressure_calibration[8] * (((calc_pres / 8) * (calc_pres / 8)) / 8192)) / 4096
            var2 = ((calc_pres / 4) * self._pressure_calibration[7]) / 8192
            var3 = (((calc_pres / 256) ** 3) * self._pressure_calibration[9]) / 131072
            calc_pres += ((var1 + var2 + var3 + (self._pressure_calibration[6] * 128)) / 16)
            return calc_pres/100
        except Exception as e:
            print(f"Error reading pressure: {e}")
            return 0  # Return 0 on error

    @property
    def humidity(self):
        """The relative humidity in RH %"""
        try:
            self._perform_reading()
            temp_scaled = ((self._t_fine * 5) + 128) / 256
            var1 = ((self._adc_hum - (self._humidity_calibration[0] * 16)) -
                    ((temp_scaled * self._humidity_calibration[2]) / 200))
            var2 = (self._humidity_calibration[1] *
                    (((temp_scaled * self._humidity_calibration[3]) / 100) +
                     (((temp_scaled * ((temp_scaled * self._humidity_calibration[4]) / 100)) /
                       64) / 100) + 16384)) / 1024
            var3 = var1 * var2
            var4 = self._humidity_calibration[5] * 128
            var4 = (var4 + ((temp_scaled * self._humidity_calibration[6]) / 100)) / 16
            var5 = ((var3 / 16384) * (var3 / 16384)) / 1024
            var6 = (var4 * var5) / 2
            calc_hum = (((var3 + var6) / 1024) * 1000) / 4096
            calc_hum /= 1000  # get back to RH

            if calc_hum > 100:
                calc_hum = 100
            if calc_hum < 0:
                calc_hum = 0
            return calc_hum
        except Exception as e:
            print(f"Error reading humidity: {e}")
            return 0  # Return 0 on error

    @property
    def gas(self):
        """The gas resistance in ohms"""
        try:
            self._perform_reading()
            var1 = ((1340 + (5 * self._sw_err)) * (_LOOKUP_TABLE_1[self._gas_range])) / 65536
            var2 = ((self._adc_gas * 32768) - 16777216) + var1
            var3 = (_LOOKUP_TABLE_2[self._gas_range] * var1) / 512
            calc_gas_res = (var3 + (var2 / 2)) / var2
            return int(calc_gas_res)
        except Exception as e:
            print(f"Error reading gas resistance: {e}")
            return 0  # Return 0 on error

    @property
    def altitude(self):
        """The altitude based on current pressure vs sea level pressure"""
        try:
            pressure = self.pressure  # in Si units for hPascal
            return 44330.77 * (1.0 - math.pow(pressure / self.sea_level_pressure, 0.1902632))
        except Exception as e:
            print(f"Error calculating altitude: {e}")
            return 0  # Return 0 on error

    def get_readings(self):
        """Get all sensor readings as a dictionary."""
        try:
            return {
                "temperature": self.temperature,
                "pressure": self.pressure,
                "humidity": self.humidity,
                "gas_resistance": self.gas,
                "altitude": self.altitude
            }
        except Exception as e:
            print(f"Error getting readings: {e}")
            # Return zeros on error
            return {
                "temperature": 0,
                "pressure": 0,
                "humidity": 0,
                "gas_resistance": 0,
                "altitude": 0
            }
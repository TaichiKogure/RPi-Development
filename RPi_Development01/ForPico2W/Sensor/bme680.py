"""
BME680 Driver for MicroPython on Raspberry Pi Pico 2W
Based on Bosch BME680 datasheet and Adafruit's CircuitPython driver

This driver provides an interface to the BME680 environmental sensor,
which can measure temperature, humidity, pressure, and gas resistance.

Author: JetBrains
Version: 1.0
Date: 2025-07-27
"""

import time
import math
from micropython import const

# BME680 Register Addresses
_BME680_CHIPID = const(0xD0)
_BME680_RESET = const(0xE0)
_BME680_STATUS = const(0x73)
_BME680_CTRL_MEAS = const(0x74)
_BME680_CONFIG = const(0x75)
_BME680_CTRL_HUM = const(0x72)
_BME680_CTRL_GAS = const(0x71)
_BME680_GAS_WAIT = const(0x64)
_BME680_RES_HEAT = const(0x5A)
_BME680_IDAC_HEAT = const(0x50)
_BME680_GAS_R_LSB = const(0x2B)
_BME680_GAS_R_MSB = const(0x2A)
_BME680_HUM_LSB = const(0x26)
_BME680_HUM_MSB = const(0x25)
_BME680_TEMP_XLSB = const(0x24)
_BME680_TEMP_LSB = const(0x23)
_BME680_TEMP_MSB = const(0x22)
_BME680_PRESS_XLSB = const(0x21)
_BME680_PRESS_LSB = const(0x20)
_BME680_PRESS_MSB = const(0x1F)
_BME680_EAS_STATUS = const(0x1D)
_BME680_COEFF_ADDR1 = const(0x89)
_BME680_COEFF_ADDR2 = const(0xE1)

# BME680 specific constants
_BME680_CHIPID_VAL = const(0x61)
_BME680_RESET_VAL = const(0xB6)
_BME680_HEAT_RANGE_1 = const(0x00)
_BME680_HEAT_RANGE_2 = const(0x01)
_BME680_HEAT_RANGE_3 = const(0x02)
_BME680_HEAT_RANGE_4 = const(0x03)
_BME680_FILTER_SIZE_0 = const(0x00)
_BME680_FILTER_SIZE_1 = const(0x01)
_BME680_FILTER_SIZE_3 = const(0x02)
_BME680_FILTER_SIZE_7 = const(0x03)
_BME680_FILTER_SIZE_15 = const(0x04)
_BME680_FILTER_SIZE_31 = const(0x05)
_BME680_FILTER_SIZE_63 = const(0x06)
_BME680_FILTER_SIZE_127 = const(0x07)

class BME680_I2C:
    """Driver for the BME680 connected over I2C."""

    def __init__(self, i2c, address=0x77, debug=False):
        """Initialize the BME680 sensor over I2C.
        
        Args:
            i2c: The I2C bus.
            address: The I2C address of the BME680 (default: 0x77).
            debug: Enable debug output (default: False).
        """
        self.i2c = i2c
        self.address = address
        self.debug = debug
        self._chip_id = self._read_byte(_BME680_CHIPID)
        
        # Check if the chip ID is correct
        if self._chip_id != _BME680_CHIPID_VAL:
            raise RuntimeError("BME680 not found with correct chip ID")
            
        # Reset the device
        self._write_byte(_BME680_RESET, _BME680_RESET_VAL)
        time.sleep(0.005)  # 5ms delay
        
        # Wait for the device to be ready
        while self._read_byte(_BME680_STATUS) & 0x80:
            time.sleep(0.001)
            
        # Read calibration data
        self._read_calibration()
        
        # Configure the sensor
        self._write_byte(_BME680_CTRL_HUM, 0x01)  # Humidity oversampling x1
        self._write_byte(_BME680_CTRL_MEAS, 0x24)  # Temp oversampling x1, Pressure oversampling x1, Normal mode
        self._write_byte(_BME680_CONFIG, 0x10)  # Filter size 16, standby time 0.5ms
        
        # Configure gas sensor
        self._write_byte(_BME680_CTRL_GAS, 0x10)  # Enable gas sensor
        
        # Set gas heater temperature and duration
        self._write_byte(_BME680_GAS_WAIT, 0x59)  # 100ms heating time
        self._write_byte(_BME680_RES_HEAT, 0x50)  # 320°C heater temperature
        
        # Enable gas measurement
        ctrl_gas = self._read_byte(_BME680_CTRL_GAS)
        self._write_byte(_BME680_CTRL_GAS, ctrl_gas | 0x10)  # Enable gas measurement
        
        print("BME680 initialization complete")

    def _read_byte(self, register):
        """Read a byte from the specified register."""
        return self.i2c.readfrom_mem(self.address, register, 1)[0]
        
    def _write_byte(self, register, value):
        """Write a byte to the specified register."""
        self.i2c.writeto_mem(self.address, register, bytes([value]))
        
    def _read_bytes(self, register, length):
        """Read multiple bytes from the specified register."""
        return self.i2c.readfrom_mem(self.address, register, length)
        
    def _read_calibration(self):
        """Read and process the calibration data from the sensor."""
        # Read calibration data from the sensor
        coeff1 = self._read_bytes(_BME680_COEFF_ADDR1, 25)
        coeff2 = self._read_bytes(_BME680_COEFF_ADDR2, 16)
        
        # Temperature calibration coefficients
        self.temp_calib = {
            'par_t1': (coeff1[9] << 8) | coeff1[8],
            'par_t2': (coeff1[11] << 8) | coeff1[10],
            'par_t3': coeff1[12]
        }
        
        # Pressure calibration coefficients
        self.pres_calib = {
            'par_p1': (coeff1[1] << 8) | coeff1[0],
            'par_p2': (coeff1[3] << 8) | coeff1[2],
            'par_p3': coeff1[4],
            'par_p4': (coeff1[7] << 8) | coeff1[6],
            'par_p5': (coeff1[9] << 8) | coeff1[8],
            'par_p6': coeff1[12],
            'par_p7': coeff1[13],
            'par_p8': (coeff1[15] << 8) | coeff1[14],
            'par_p9': (coeff1[17] << 8) | coeff1[16],
            'par_p10': coeff1[18]
        }
        
        # Humidity calibration coefficients
        self.hum_calib = {
            'par_h1': ((coeff1[24] << 4) | (coeff1[23] & 0x0F)),
            'par_h2': ((coeff1[23] << 4) | (coeff1[22] >> 4)),
            'par_h3': coeff1[21],
            'par_h4': coeff1[20],
            'par_h5': coeff1[19],
            'par_h6': coeff2[0],
            'par_h7': coeff2[1]
        }
        
        # Gas calibration coefficients
        self.gas_calib = {
            'par_g1': coeff2[2],
            'par_g2': (coeff2[4] << 8) | coeff2[3],
            'par_g3': coeff2[5]
        }
        
        # Other calibration coefficients
        self.res_heat_range = (self._read_byte(0x02) & 0x30) >> 4
        self.res_heat_val = self._read_byte(0x00)
        self.range_sw_err = (self._read_byte(0x04) & 0xF0) >> 4
        
        if self.debug:
            print("Calibration data read successfully")

    def _read_raw_data(self):
        """Read raw data from the sensor."""
        # Set the sensor to forced mode to trigger a measurement
        ctrl_meas = self._read_byte(_BME680_CTRL_MEAS)
        self._write_byte(_BME680_CTRL_MEAS, ctrl_meas | 0x01)
        
        # Wait for the measurement to complete
        while self._read_byte(_BME680_STATUS) & 0x80:
            time.sleep(0.001)
            
        # Read the data
        data = self._read_bytes(_BME680_PRESS_MSB, 8)
        
        # Parse the data
        raw_temp = ((data[3] << 16) | (data[4] << 8) | data[5]) >> 4
        raw_pres = ((data[0] << 16) | (data[1] << 8) | data[2]) >> 4
        raw_hum = (data[6] << 8) | data[7]
        
        # Read gas resistance data
        gas_data = self._read_bytes(_BME680_GAS_R_MSB, 2)
        raw_gas = (gas_data[0] << 2) | (gas_data[1] >> 6)
        gas_range = gas_data[1] & 0x0F
        
        return raw_temp, raw_pres, raw_hum, raw_gas, gas_range

    def _calc_temperature(self, raw_temp):
        """Calculate the temperature from raw data."""
        var1 = ((raw_temp / 16384.0) - (self.temp_calib['par_t1'] / 1024.0)) * self.temp_calib['par_t2']
        var2 = (((raw_temp / 131072.0) - (self.temp_calib['par_t1'] / 8192.0)) ** 2) * self.temp_calib['par_t3'] * 16
        self.t_fine = var1 + var2
        return self.t_fine / 5120.0

    def _calc_pressure(self, raw_pres):
        """Calculate the pressure from raw data."""
        var1 = (self.t_fine / 2.0) - 64000.0
        var2 = var1 * var1 * self.pres_calib['par_p6'] / 131072.0
        var2 = var2 + (var1 * self.pres_calib['par_p5'] * 2.0)
        var2 = (var2 / 4.0) + (self.pres_calib['par_p4'] * 65536.0)
        var1 = ((self.pres_calib['par_p3'] * var1 * var1 / 16384.0) + 
                (self.pres_calib['par_p2'] * var1)) / 524288.0
        var1 = (1.0 + (var1 / 32768.0)) * self.pres_calib['par_p1']
        
        if var1 == 0:
            return 0
            
        pressure = 1048576.0 - raw_pres
        pressure = ((pressure - (var2 / 4096.0)) * 6250.0) / var1
        var1 = self.pres_calib['par_p9'] * pressure * pressure / 2147483648.0
        var2 = pressure * self.pres_calib['par_p8'] / 32768.0
        pressure = pressure + ((var1 + var2 + self.pres_calib['par_p7']) / 16.0)
        
        return pressure / 100.0  # Convert to hPa

    def _calc_humidity(self, raw_hum):
        """Calculate the humidity from raw data."""
        temp_comp = self.t_fine / 5120.0
        var1 = raw_hum - ((self.hum_calib['par_h1'] * 16.0) + 
                          ((self.hum_calib['par_h3'] / 2.0) * temp_comp))
        var2 = var1 * ((self.hum_calib['par_h2'] / 262144.0) * 
                       (1.0 + ((self.hum_calib['par_h4'] / 16384.0) * temp_comp) + 
                        ((self.hum_calib['par_h5'] / 1048576.0) * temp_comp * temp_comp)))
        var3 = self.hum_calib['par_h6'] / 16384.0
        var4 = self.hum_calib['par_h7'] / 2097152.0
        
        humidity = var2 + ((var3 + (var4 * temp_comp)) * var2 * var2)
        
        if humidity > 100.0:
            humidity = 100.0
        elif humidity < 0.0:
            humidity = 0.0
            
        return humidity

    def _calc_gas_resistance(self, raw_gas, gas_range):
        """Calculate the gas resistance from raw data."""
        var1 = 1340.0 + (5.0 * self.range_sw_err)
        var2 = var1 * (1.0 + self.gas_calib['par_g1'] / 100.0)
        var3 = 1.0 + (self.gas_calib['par_g2'] / 100.0)
        var4 = var3 * (1.0 + (self.gas_calib['par_g3'] / 100.0))
        var5 = 1.0 + (self.res_heat_range / 4.0)
        var6 = 1.0 + (self.res_heat_val / 64.0)
        
        # Calculate gas resistance
        gas_res = 1.0 / (var4 * (1.0 + (var1 * (raw_gas / 512.0))))
        
        # Apply range-specific multiplier
        range_multiplier = 1.0 / (1 << gas_range)
        gas_res = gas_res * range_multiplier
        
        return gas_res

    @property
    def temperature(self):
        """Get the temperature in degrees Celsius."""
        raw_temp, _, _, _, _ = self._read_raw_data()
        return self._calc_temperature(raw_temp)

    @property
    def pressure(self):
        """Get the pressure in hPa."""
        _, raw_pres, _, _, _ = self._read_raw_data()
        return self._calc_pressure(raw_pres)

    @property
    def humidity(self):
        """Get the relative humidity in percent."""
        _, _, raw_hum, _, _ = self._read_raw_data()
        return self._calc_humidity(raw_hum)

    @property
    def gas(self):
        """Get the gas resistance in ohms."""
        _, _, _, raw_gas, gas_range = self._read_raw_data()
        return int(self._calc_gas_resistance(raw_gas, gas_range))

    def read_all(self):
        """Read all sensor values at once."""
        raw_temp, raw_pres, raw_hum, raw_gas, gas_range = self._read_raw_data()
        
        temp = self._calc_temperature(raw_temp)
        pres = self._calc_pressure(raw_pres)
        hum = self._calc_humidity(raw_hum)
        gas = int(self._calc_gas_resistance(raw_gas, gas_range))
        
        return temp, pres, hum, gas
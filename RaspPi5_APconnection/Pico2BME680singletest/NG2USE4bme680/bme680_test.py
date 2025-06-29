# -*- coding: utf-8 -*-
"""
BME680 Simple Test Program for Raspberry Pi Pico 2W
Version: 1.0.0

This is a simple test program for the BME680 environmental sensor
connected to a Raspberry Pi Pico 2W. It reads temperature, humidity,
pressure, and gas resistance data from the sensor and displays it
in the Thonny console.

This program does not use WiFi functionality and is designed to be
the simplest possible implementation for testing the BME680 sensor.

Requirements:
- MicroPython for Raspberry Pi Pico W
- BME680 sensor connected via I2C

Connection:
- BME680 VCC → Pico 2W 3.3V
- BME680 GND → Pico 2W GND
- BME680 SCL → Pico 2W GP1
- BME680 SDA → Pico 2W GP0
"""

import time
from machine import I2C, Pin

# Status LED
LED_PIN = 25  # Onboard LED on Pico W

# BME680 I2C addresses
BME680_I2C_ADDR_PRIMARY = 0x76
BME680_I2C_ADDR_SECONDARY = 0x77

# BME680 register addresses
BME680_CHIP_ID_ADDR = 0xD0
BME680_RESET_ADDR = 0xE0
BME680_CTRL_HUM_ADDR = 0x72
BME680_CTRL_MEAS_ADDR = 0x74
BME680_CONFIG_ADDR = 0x75
BME680_CTRL_GAS_ADDR = 0x71
BME680_STATUS_ADDR = 0x73

# BME680 data registers
BME680_DATA_ADDR = 0x1D
BME680_TEMP_ADDR = 0x22
BME680_PRESS_ADDR = 0x1F
BME680_HUM_ADDR = 0x25
BME680_GAS_ADDR = 0x2A

# BME680 constants
BME680_CHIP_ID = 0x61
BME680_SOFT_RESET_CMD = 0xB6

# BME680 calibration registers
BME680_COEFF_ADDR1 = 0x89
BME680_COEFF_ADDR2 = 0xE1

class BME680Sensor:
    """Class to interface with the BME680 sensor."""
    
    def __init__(self, i2c=None, address=BME680_I2C_ADDR_PRIMARY, scl_pin=1, sda_pin=0):
        """Initialize the BME680 sensor with the given I2C bus and address."""
        # Initialize I2C if not provided
        if i2c is None:
            self.i2c = I2C(0, scl=Pin(scl_pin), sda=Pin(sda_pin), freq=100000)
        else:
            self.i2c = i2c
        
        self.address = address
        self.calibration_data = {}
        self.tph_settings = {}
        self.gas_settings = {}
        self.power_mode = 0
        
        # Initialize the sensor
        self._initialize()
    
    def _initialize(self):
        """Initialize the BME680 sensor."""
        # Check if sensor is present
        chip_id = self._read_byte(BME680_CHIP_ID_ADDR)
        if chip_id != BME680_CHIP_ID:
            raise RuntimeError(f"BME680 not found. Chip ID: {chip_id}")
        
        # Reset the sensor
        self._write_byte(BME680_RESET_ADDR, BME680_SOFT_RESET_CMD)
        time.sleep(0.01)  # Wait for reset to complete
        
        # Read calibration data
        self._read_calibration_data()
        
        # Set default settings
        self._set_default_settings()
    
    def _read_byte(self, register):
        """Read a single byte from the specified register."""
        return self.i2c.readfrom_mem(self.address, register, 1)[0]
    
    def _read_bytes(self, register, length):
        """Read multiple bytes from the specified register."""
        return self.i2c.readfrom_mem(self.address, register, length)
    
    def _write_byte(self, register, value):
        """Write a single byte to the specified register."""
        self.i2c.writeto_mem(self.address, register, bytes([value]))
    
    def _read_calibration_data(self):
        """Read the calibration data from the sensor."""
        # Read temperature calibration data
        coeff = self._read_bytes(BME680_COEFF_ADDR1, 25)
        coeff += self._read_bytes(BME680_COEFF_ADDR2, 16)
        
        # Temperature calibration
        self.calibration_data['par_t1'] = (coeff[34] << 8) | coeff[33]
        self.calibration_data['par_t2'] = (coeff[2] << 8) | coeff[1]
        self.calibration_data['par_t3'] = coeff[3]
        
        # Pressure calibration
        self.calibration_data['par_p1'] = (coeff[6] << 8) | coeff[5]
        self.calibration_data['par_p2'] = (coeff[8] << 8) | coeff[7]
        self.calibration_data['par_p3'] = coeff[9]
        self.calibration_data['par_p4'] = (coeff[12] << 8) | coeff[11]
        self.calibration_data['par_p5'] = (coeff[14] << 8) | coeff[13]
        self.calibration_data['par_p6'] = coeff[16]
        self.calibration_data['par_p7'] = coeff[15]
        self.calibration_data['par_p8'] = (coeff[20] << 8) | coeff[19]
        self.calibration_data['par_p9'] = (coeff[22] << 8) | coeff[21]
        self.calibration_data['par_p10'] = coeff[23]
        
        # Humidity calibration
        self.calibration_data['par_h1'] = (coeff[27] << 4) | (coeff[26] & 0x0F)
        self.calibration_data['par_h2'] = (coeff[25] << 4) | (coeff[26] >> 4)
        self.calibration_data['par_h3'] = coeff[28]
        self.calibration_data['par_h4'] = coeff[29]
        self.calibration_data['par_h5'] = coeff[30]
        self.calibration_data['par_h6'] = coeff[31]
        self.calibration_data['par_h7'] = coeff[32]
        
        # Gas calibration
        self.calibration_data['par_g1'] = coeff[37]
        self.calibration_data['par_g2'] = (coeff[36] << 8) | coeff[35]
        self.calibration_data['par_g3'] = coeff[38]
        self.calibration_data['res_heat_range'] = (self._read_byte(0x02) & 0x30) >> 4
        self.calibration_data['res_heat_val'] = self._read_byte(0x00)
        self.calibration_data['range_sw_err'] = (self._read_byte(0x04) & 0xF0) >> 4
    
    def _set_default_settings(self):
        """Set default settings for the sensor."""
        # TPH settings
        self.tph_settings['os_hum'] = 1  # Humidity oversampling x1
        self.tph_settings['os_temp'] = 2  # Temperature oversampling x2
        self.tph_settings['os_pres'] = 5  # Pressure oversampling x16
        self.tph_settings['filter'] = 3  # Filter coefficient 8
        
        # Gas settings
        self.gas_settings['run_gas'] = 1  # Enable gas measurements
        self.gas_settings['heatr_temp'] = 320  # Heater temperature in Celsius
        self.gas_settings['heatr_dur'] = 150  # Heater duration in ms
        
        # Power mode
        self.power_mode = 1  # Forced mode
        
        # Apply settings
        self._apply_settings()
    
    def _apply_settings(self):
        """Apply the current settings to the sensor."""
        # Set humidity oversampling
        self._write_byte(BME680_CTRL_HUM_ADDR, self.tph_settings['os_hum'])
        
        # Set temperature and pressure oversampling, and power mode
        reg = (self.tph_settings['os_temp'] << 5) | (self.tph_settings['os_pres'] << 2) | self.power_mode
        self._write_byte(BME680_CTRL_MEAS_ADDR, reg)
        
        # Set filter coefficient
        reg = self._read_byte(BME680_CONFIG_ADDR)
        reg = (reg & 0xE3) | (self.tph_settings['filter'] << 2)
        self._write_byte(BME680_CONFIG_ADDR, reg)
        
        # Set gas settings
        reg = self._read_byte(BME680_CTRL_GAS_ADDR)
        reg = (reg & 0xF0) | (self.gas_settings['run_gas'] << 1)
        self._write_byte(BME680_CTRL_GAS_ADDR, reg)
        
        # Set heater temperature and duration
        self._set_gas_heater(self.gas_settings['heatr_temp'], self.gas_settings['heatr_dur'])
    
    def _set_gas_heater(self, temperature, duration):
        """Set the gas heater temperature and duration."""
        # Calculate heater resistance
        temp = min(max(temperature, 200), 400)  # Clamp temperature to 200-400°C
        
        # Calculate heater resistance using calibration data
        var1 = (self.calibration_data['par_g1'] / 16.0) + 49.0
        var2 = ((self.calibration_data['par_g2'] / 32768.0) * 0.0005) + 0.00235
        var3 = self.calibration_data['par_g3'] / 1024.0
        var4 = var1 * (1.0 + (var2 * temp))
        var5 = var4 + (var3 * self.calibration_data['amb_temp'])
        
        # Calculate heater resistance
        heatr_res = 3.4 + ((temp - 20) * 0.6 / 100)
        heatr_res = int(3.4 + ((temp - 20) * 0.6 / 100) * 1000)
        
        # Set heater resistance
        self._write_byte(0x5A, heatr_res)
        
        # Set heater duration
        dur = min(max(duration, 1), 4032)  # Clamp duration to 1-4032ms
        self._write_byte(0x64, dur // 32)
    
    def _calc_temperature(self, temp_adc):
        """Calculate temperature from ADC value."""
        var1 = (temp_adc / 16384.0 - self.calibration_data['par_t1'] / 1024.0) * self.calibration_data['par_t2']
        var2 = ((temp_adc / 131072.0 - self.calibration_data['par_t1'] / 8192.0) ** 2) * self.calibration_data['par_t3'] * 16
        self.calibration_data['t_fine'] = var1 + var2
        return self.calibration_data['t_fine'] / 5120.0
    
    def _calc_pressure(self, pres_adc):
        """Calculate pressure from ADC value."""
        var1 = (self.calibration_data['t_fine'] / 2.0) - 64000.0
        var2 = var1 * var1 * self.calibration_data['par_p6'] / 131072.0
        var2 = var2 + (var1 * self.calibration_data['par_p5'] * 2.0)
        var2 = (var2 / 4.0) + (self.calibration_data['par_p4'] * 65536.0)
        var1 = (self.calibration_data['par_p3'] * var1 * var1 / 16384.0 + self.calibration_data['par_p2'] * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self.calibration_data['par_p1']
        
        if var1 == 0:
            return 0
        
        pressure = 1048576.0 - pres_adc
        pressure = ((pressure - var2 / 4096.0) * 6250.0) / var1
        var1 = self.calibration_data['par_p9'] * pressure * pressure / 2147483648.0
        var2 = pressure * self.calibration_data['par_p8'] / 32768.0
        pressure = pressure + (var1 + var2 + self.calibration_data['par_p7']) / 16.0
        
        return pressure / 100.0  # Convert to hPa
    
    def _calc_humidity(self, hum_adc):
        """Calculate humidity from ADC value."""
        temp_comp = self.calibration_data['t_fine'] / 5120.0
        var1 = hum_adc - (self.calibration_data['par_h1'] * 16 + (self.calibration_data['par_h3'] / 2.0 * temp_comp))
        var2 = var1 * (self.calibration_data['par_h2'] / 262144.0 * (1.0 + self.calibration_data['par_h4'] / 16384.0 * temp_comp + self.calibration_data['par_h5'] / 1048576.0 * temp_comp * temp_comp))
        var3 = self.calibration_data['par_h6'] / 16384.0
        var4 = self.calibration_data['par_h7'] / 2097152.0
        humidity = var2 + ((var3 + (var4 * temp_comp)) * var2 * var2)
        
        return min(max(humidity, 0), 100)  # Clamp to 0-100%
    
    def _calc_gas_resistance(self, gas_adc, gas_range):
        """Calculate gas resistance from ADC value and range."""
        var1 = 1340.0 + 5.0 * self.calibration_data['range_sw_err']
        var2 = var1 * (1.0 + self.calibration_data['par_g1'] / 100.0)
        var3 = 1.0 + self.calibration_data['par_g2'] / 100.0
        var4 = var3 * (1.0 + self.calibration_data['par_g3'] / 100.0)
        var5 = 1.0 + (self.calibration_data['res_heat_range'] / 4.0)
        var6 = 1.0 + (self.calibration_data['res_heat_val'] / 4.0)
        
        # Calculate gas resistance
        gas_res = var1 * var2 * var3 * var4 * var5 * var6
        gas_res = gas_res * (1.0 / (gas_adc + 512.0))
        
        return gas_res
    
    def _read_raw_data(self):
        """Read raw data from the sensor."""
        # Set sensor to forced mode to trigger a measurement
        if self.power_mode == 1:  # Forced mode
            reg = self._read_byte(BME680_CTRL_MEAS_ADDR)
            self._write_byte(BME680_CTRL_MEAS_ADDR, reg & 0xFC | 0x01)  # Set to forced mode
            
            # Wait for measurement to complete
            while True:
                status = self._read_byte(BME680_STATUS_ADDR)
                if (status & 0x80) == 0:  # Check if measuring bit is cleared
                    break
                time.sleep(0.01)
        
        # Read raw data
        data = self._read_bytes(BME680_DATA_ADDR, 15)
        
        # Extract raw values
        raw_temp = (data[5] << 12) | (data[6] << 4) | (data[7] >> 4)
        raw_pres = (data[2] << 12) | (data[3] << 4) | (data[4] >> 4)
        raw_hum = (data[8] << 8) | data[9]
        
        # Extract gas data
        gas_valid = (data[14] & 0x20) == 0x20
        heat_stab = (data[14] & 0x10) == 0x10
        
        if gas_valid and heat_stab:
            gas_range = data[14] & 0x0F
            raw_gas = (data[13] << 2) | (data[14] >> 6)
        else:
            gas_range = 0
            raw_gas = 0
        
        return {
            'temperature': raw_temp,
            'pressure': raw_pres,
            'humidity': raw_hum,
            'gas': raw_gas,
            'gas_range': gas_range,
            'gas_valid': gas_valid,
            'heat_stable': heat_stab
        }
    
    def get_readings(self):
        """Get sensor readings."""
        # Read raw data
        raw_data = self._read_raw_data()
        
        # Calculate compensated values
        temperature = self._calc_temperature(raw_data['temperature'])
        pressure = self._calc_pressure(raw_data['pressure'])
        humidity = self._calc_humidity(raw_data['humidity'])
        
        # Calculate gas resistance if valid
        gas_resistance = None
        if raw_data['gas_valid'] and raw_data['heat_stable']:
            gas_resistance = self._calc_gas_resistance(raw_data['gas'], raw_data['gas_range'])
        
        return {
            'temperature': temperature,
            'pressure': pressure,
            'humidity': humidity,
            'gas_resistance': gas_resistance,
            'gas_valid': raw_data['gas_valid'],
            'heat_stable': raw_data['heat_stable']
        }
    
    def close(self):
        """Close the sensor."""
        # Set sensor to sleep mode
        reg = self._read_byte(BME680_CTRL_MEAS_ADDR)
        self._write_byte(BME680_CTRL_MEAS_ADDR, reg & 0xFC)  # Set to sleep mode

def main():
    """Main function to read and display BME680 sensor data."""
    # Initialize LED
    led = Pin(LED_PIN, Pin.OUT)
    led.on()  # Turn on LED to indicate program is running
    
    print("BME680 Simple Test Program for Raspberry Pi Pico 2W")
    print("==================================================")
    print("Initializing BME680 sensor...")
    
    try:
        # Initialize sensor
        sensor = BME680Sensor()
        print("BME680 sensor initialized successfully!")
        
        # Main loop
        print("\nReading sensor data continuously. Press Ctrl+C to stop.")
        print("--------------------------------------------------")
        
        while True:
            # Blink LED to indicate activity
            led.off()
            time.sleep(0.1)
            led.on()
            
            # Get readings
            readings = sensor.get_readings()
            
            # Print readings
            print("\nBME680 Sensor Readings:")
            print(f"Temperature: {readings['temperature']:.2f} °C")
            print(f"Pressure: {readings['pressure']:.2f} hPa")
            print(f"Humidity: {readings['humidity']:.2f} %")
            
            if readings['gas_resistance'] is not None:
                print(f"Gas Resistance: {readings['gas_resistance']:.2f} Ohms")
            else:
                print("Gas measurement not available")
            
            # Wait before next reading
            time.sleep(2)
    
    except KeyboardInterrupt:
        print("\nProgram stopped by user")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        # Turn off LED
        led.off()
        print("Program ended")

if __name__ == "__main__":
    main()
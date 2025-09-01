#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P1_Sensor V1 - Environmental Monitoring System for Raspberry Pi 5
Version: 1.0.0

This program collects environmental data from MH-Z19 CO2 sensor and BME680 environmental
sensor connected to a Raspberry Pi 5, logs the data to CSV files, and displays it in
the terminal.

Features:
- MH-Z19 CO2 sensor integration via UART
- BME680 sensor integration via I2C (temperature, humidity, pressure, gas resistance)
- Data logging to CSV files with daily and consolidated formats
- Terminal display of sensor readings
- Error handling and recovery

Pin connections:
BME680:
- VCC -> 3.3V
- GND -> GND
- SCL -> SCL (GPIO 3, Pin 5)
- SDA -> SDA (GPIO 2, Pin 3)

MH-Z19:
- VCC (red) -> 5V
- GND (black) -> GND
- TX (green) -> GPIO 14 (UART0 RX, Pin 8)
- RX (blue) -> GPIO 15 (UART0 TX, Pin 10)

Usage:
    python3 P1_Sensor.py

Press Ctrl+C to exit the program.
"""

import time
import csv
import sys
import signal
import serial
import datetime
import os
import atexit
import smbus2
import math
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("p1_sensor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = "/var/lib(FromThonny)/raspap_solo/data/RawData_P1"
FIXED_CSV_PATH = os.path.join(DATA_DIR, "P1_fixed.csv")
SAMPLING_INTERVAL = 30  # seconds

# BME680 I2C Address
BME680_I2C_ADDR = 0x77  # or 0x76 depending on SDO pin

# BME680 Register Addresses
BME680_REG_CHIP_ID = 0xD0
BME680_CHIP_ID = 0x61

# MH-Z19 UART Configuration
MHZ19_UART_DEVICE = '/dev/ttyAMA0'
MHZ19_BAUDRATE = 9600

class BME680:
    """Driver for BME680 gas, pressure, temperature and humidity sensor."""

    def __init__(self, i2c_addr=BME680_I2C_ADDR, temp_offset=0):
        """Initialize the BME680 sensor.

        Args:
            i2c_addr (int): I2C address of the sensor (0x76 or 0x77)
            temp_offset (float): Temperature offset in degrees Celsius
        """
        self.i2c_addr = i2c_addr
        self.temp_offset = temp_offset
        self.bus = smbus2.SMBus(1)  # Use I2C bus 1 on Raspberry Pi

        # Check if sensor is present
        try:
            chip_id = self.bus.read_byte_data(self.i2c_addr, BME680_REG_CHIP_ID)
            if chip_id != BME680_CHIP_ID:
                raise RuntimeError(f"BME680 not found, invalid chip ID: {hex(chip_id)}")
            logger.info("BME680 found with correct chip ID")

            # Initialize sensor
            self._initialize()

        except Exception as e:
            logger.error(f"Error initializing BME680: {e}")
            raise

    def _initialize(self):
        """Initialize the BME680 sensor with default settings."""
        try:
            # Soft reset the sensor
            self.bus.write_byte_data(self.i2c_addr, 0xE0, 0xB6)
            time.sleep(0.005)  # Wait for reset to complete

            # Check if sensor is present
            chip_id = self.bus.read_byte_data(self.i2c_addr, BME680_REG_CHIP_ID)
            if chip_id != BME680_CHIP_ID:
                raise RuntimeError(f"BME680 not found, invalid chip ID: {hex(chip_id)}")

            # Read calibration data
            self._read_calibration_data()

            # Set up heater
            self.bus.write_byte_data(self.i2c_addr, 0x5A, 0x73)  # BME680_RES_HEAT_0
            self.bus.write_byte_data(self.i2c_addr, 0x64, 0x65)  # BME680_GAS_WAIT_0

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

            # Enable gas measurement with heater
            ctrl_gas = self.bus.read_byte_data(self.i2c_addr, 0x71)  # BME680_REG_CTRL_GAS
            ctrl_gas |= 0x10  # heater enable bit
            self.bus.write_byte_data(self.i2c_addr, 0x71, ctrl_gas)

            # Set humidity oversample
            self.bus.write_byte_data(self.i2c_addr, 0x72, self._humidity_oversample)  # BME680_REG_CTRL_HUM

            # Set pressure and temperature oversample
            self.bus.write_byte_data(self.i2c_addr, 0x74,  # BME680_REG_CTRL_MEAS
                                    (self._temp_oversample << 5) | (self._pressure_oversample << 2) | 0x01)

            # Set filter
            self.bus.write_byte_data(self.i2c_addr, 0x75, self._filter << 2)  # BME680_REG_CONFIG

            # Set gas heater temperature to 320°C
            temp = 320  # Target temperature in Celsius
            amb_temp = 25  # Ambient temperature (assumed)

            # Calculate heater resistance
            heatr_res = int(3.4 + ((temp - 20) * 0.6 / 100) * 1000)
            heatr_res = min(max(0, heatr_res), 255)  # Limit to 0-255
            self.bus.write_byte_data(self.i2c_addr, 0x5A, heatr_res)  # BME680_RES_HEAT_0

            logger.info("BME680 initialization complete")

            # Take initial reading
            self._perform_reading()

        except Exception as e:
            logger.error(f"Error initializing BME680: {e}")
            logger.error(traceback.format_exc())
            raise

    def _read_calibration_data(self):
        """Read and process calibration data from the sensor."""
        try:
            # Read calibration data
            calibration_data = []

            # Read first block of calibration data
            for i in range(0x89, 0x89 + 25):
                calibration_data.append(self.bus.read_byte_data(self.i2c_addr, i))

            # Read second block of calibration data
            for i in range(0xE1, 0xE1 + 16):
                calibration_data.append(self.bus.read_byte_data(self.i2c_addr, i))

            # Process calibration data
            # This is a simplified version of the calibration data processing
            # In a real implementation, this would be more complex

            # Store calibration data
            self._temp_calibration = [calibration_data[33], calibration_data[1], calibration_data[2]]
            self._pressure_calibration = [calibration_data[5], calibration_data[6], calibration_data[7],
                                         calibration_data[9], calibration_data[10], calibration_data[12],
                                         calibration_data[11], calibration_data[14], calibration_data[15],
                                         calibration_data[16]]
            self._humidity_calibration = [calibration_data[24], calibration_data[23], calibration_data[25],
                                         calibration_data[26], calibration_data[27], calibration_data[28],
                                         calibration_data[29]]
            self._gas_calibration = [calibration_data[36], calibration_data[35], calibration_data[37]]

            # Additional calibration data
            self._heat_range = (self.bus.read_byte_data(self.i2c_addr, 0x02) & 0x30) / 16
            self._heat_val = self.bus.read_byte_data(self.i2c_addr, 0x00)
            self._sw_err = (self.bus.read_byte_data(self.i2c_addr, 0x04) & 0xF0) / 16

            logger.info("BME680 calibration data read successfully")

        except Exception as e:
            logger.error(f"Error reading calibration data: {e}")
            logger.error(traceback.format_exc())
            raise

    def _perform_reading(self):
        """Perform a single-shot reading from the sensor and fill internal data structure for calculations."""
        try:
            # Enable gas measurement
            self.bus.write_byte_data(self.i2c_addr, 0x71, 0x10)  # BME680_REG_CTRL_GAS, BME680_RUNGAS

            # Enable single shot mode
            ctrl = self.bus.read_byte_data(self.i2c_addr, 0x74)  # BME680_REG_CTRL_MEAS
            ctrl = (ctrl & 0xFC) | 0x01  # Enable single shot!
            self.bus.write_byte_data(self.i2c_addr, 0x74, ctrl)  # BME680_REG_CTRL_MEAS

            # Wait for measurement to complete
            new_data = False
            wait_start = time.time()
            while not new_data:
                # Read status register
                status = self.bus.read_byte_data(self.i2c_addr, 0x1D)  # BME680_REG_MEAS_STATUS
                new_data = status & 0x80 != 0
                time.sleep(0.005)

                # Timeout after 1 second
                if time.time() - wait_start > 1:
                    logger.warning("BME680 measurement timeout")
                    return

            # Read data registers
            data = []
            for i in range(0x1F, 0x1F + 15):  # BME680_REG_PDATA to BME680_REG_PDATA + 15
                data.append(self.bus.read_byte_data(self.i2c_addr, i))

            # Parse raw data
            self._adc_pres = ((data[2] << 16) | (data[3] << 8) | data[4]) >> 4
            self._adc_temp = ((data[5] << 16) | (data[6] << 8) | data[7]) >> 4
            self._adc_hum = (data[8] << 8) | data[9]

            # Check if gas measurement is valid (heat_stable)
            heat_stable = (data[14] & 0x20) != 0
            if heat_stable:
                self._adc_gas = int((data[13] << 8) | (data[14] & 0x0F))
                self._gas_range = (data[14] & 0x0F)
            else:
                logger.debug("Gas measurement not stable")
                self._adc_gas = 0
                self._gas_range = 0

            # Calculate temperature
            var1 = (self._adc_temp / 8) - (self._temp_calibration[0] * 2)
            var2 = (var1 * self._temp_calibration[1]) / 2048
            var3 = ((var1 / 2) * (var1 / 2)) / 4096
            var3 = (var3 * self._temp_calibration[2] * 16) / 16384
            self._t_fine = int(var2 + var3)

            logger.debug("BME680 reading performed successfully")

        except Exception as e:
            logger.error(f"Error performing BME680 reading: {e}")
            logger.error(traceback.format_exc())

    def get_temperature(self):
        """Get the temperature in degrees Celsius."""
        try:
            self._perform_reading()
            calc_temp = (((self._t_fine * 5) + 128) / 256)
            return (calc_temp / 100) + self.temp_offset
        except Exception as e:
            logger.error(f"Error reading temperature: {e}")
            logger.error(traceback.format_exc())
            return 0

    def get_pressure(self):
        """Get the pressure in hectoPascals."""
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
            logger.error(f"Error reading pressure: {e}")
            logger.error(traceback.format_exc())
            return 0

    def get_humidity(self):
        """Get the relative humidity in percent."""
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
            logger.error(f"Error reading humidity: {e}")
            logger.error(traceback.format_exc())
            return 0

    def get_gas_resistance(self):
        """Get the gas resistance in ohms."""
        try:
            self._perform_reading()

            # If gas measurement is not valid, return 0
            if self._adc_gas == 0 or self._gas_range == 0:
                return 0

            # Calculate gas resistance using calibration data
            var1 = ((1340 + (5 * self._sw_err)) * (self._gas_calibration[0] / 65536)) / 1
            var2 = ((self._adc_gas * 32768) - 16777216) + var1
            var3 = (self._gas_calibration[1] * var1) / 512
            calc_gas_res = (var3 + (var2 / 2)) / var2

            return int(calc_gas_res)
        except Exception as e:
            logger.error(f"Error reading gas resistance: {e}")
            logger.error(traceback.format_exc())
            return 0

    def calculate_absolute_humidity(self, temperature, humidity):
        """Calculate absolute humidity in g/m³ from temperature (°C) and relative humidity (%).

        Args:
            temperature (float): Temperature in degrees Celsius
            humidity (float): Relative humidity in percent

        Returns:
            float: Absolute humidity in g/m³, rounded to 2 decimal places
        """
        try:
            # Calculate saturation vapor pressure (hPa)
            # Magnus formula: es = 6.1078 * 10^((7.5 * T) / (237.3 + T))
            saturation_vapor_pressure = 6.1078 * 10 ** ((7.5 * temperature) / (237.3 + temperature))

            # Calculate vapor pressure (hPa)
            vapor_pressure = saturation_vapor_pressure * humidity / 100.0

            # Calculate absolute humidity (g/m³)
            # Formula: AH = 216.7 * (VP / (273.15 + T))
            absolute_humidity = 216.7 * (vapor_pressure / (273.15 + temperature))

            return round(absolute_humidity, 2)
        except Exception as e:
            logger.error(f"Error calculating absolute humidity: {e}")
            return 0

    def get_readings(self):
        """Get all sensor readings as a dictionary.

        Returns:
            dict: Sensor readings including temperature, humidity, pressure, gas resistance, and absolute humidity
        """
        try:
            # Perform a single reading to get all values
            self._perform_reading()

            # Get individual readings
            temperature = self.get_temperature()
            humidity = self.get_humidity()
            pressure = self.get_pressure()
            gas_resistance = self.get_gas_resistance()

            # Calculate absolute humidity
            absolute_humidity = self.calculate_absolute_humidity(temperature, humidity)

            return {
                "temperature": temperature,
                "humidity": humidity,
                "pressure": pressure,
                "gas_resistance": gas_resistance,
                "absolute_humidity": absolute_humidity
            }
        except Exception as e:
            logger.error(f"Error getting BME680 readings: {e}")
            logger.error(traceback.format_exc())
            return {
                "temperature": 0,
                "humidity": 0,
                "pressure": 0,
                "gas_resistance": 0,
                "absolute_humidity": 0
            }

class MHZ19:
    """Driver for MH-Z19 CO2 sensor."""

    def __init__(self, uart_device=MHZ19_UART_DEVICE, baudrate=MHZ19_BAUDRATE):
        """Initialize the MH-Z19 sensor.

        Args:
            uart_device (str): UART device path
            baudrate (int): Baud rate
        """
        try:
            self.serial = serial.Serial(
                port=uart_device,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0
            )
            self.warmup_time = 30  # seconds
            self.warmup_start = time.time()
            self.is_warmed_up = False

            # Flush any data in the serial buffer
            self.serial.flushInput()

            logger.info(f"MH-Z19 initialized on {uart_device}")
            logger.info(f"Warming up for {self.warmup_time} seconds...")

        except Exception as e:
            logger.error(f"Error initializing MH-Z19: {e}")
            raise

    def _calculate_checksum(self, packet):
        """Calculate checksum for command packet."""
        try:
            checksum = 0
            for byte in packet[1:8]:
                checksum += byte
            checksum = ~checksum & 0xFF
            checksum += 1
            return checksum
        except Exception as e:
            logger.error(f"Error calculating checksum: {e}")
            return 0

    def _send_command(self, command, data=None, retries=3):
        """Send command to sensor and read response with retry.

        Args:
            command (int): Command byte
            data (list): Optional data bytes
            retries (int): Number of retry attempts

        Returns:
            bytes: Response from sensor or None if error
        """
        if data is None:
            data = [0, 0, 0, 0, 0]

        for attempt in range(retries):
            try:
                # Create command packet
                packet = bytearray([0xFF, 0x01, command] + data)
                packet.append(self._calculate_checksum(packet))

                # Flush any existing data
                self.serial.flushInput()

                # Send command
                self.serial.write(packet)

                # Wait for response with timeout
                time.sleep(0.1)

                # Check if we have data
                if self.serial.in_waiting:
                    # Read response
                    response = self.serial.read(9)

                    if response and len(response) == 9 and response[0] == 0xFF and response[1] == 0x86:
                        return response

                # Wait before retry
                if attempt < retries - 1:
                    time.sleep(0.2 * (attempt + 1))  # Progressive backoff

            except Exception as e:
                logger.error(f"Error sending command (attempt {attempt+1}): {e}")

        # All retries failed
        return None

    def read_co2(self, retries=3):
        """Read CO2 concentration from sensor.

        Args:
            retries (int): Number of retry attempts

        Returns:
            int: CO2 concentration in ppm or 0 if error
        """
        # Check if sensor is warmed up
        current_time = time.time()
        if not self.is_warmed_up:
            if current_time - self.warmup_start >= self.warmup_time:
                self.is_warmed_up = True
                logger.info("MH-Z19 warmup complete")
            else:
                remaining = self.warmup_time - (current_time - self.warmup_start)
                logger.info(f"MH-Z19 still warming up ({remaining:.1f} seconds remaining)")
                return 0

        # Send read command
        response = self._send_command(0x86, retries=retries)

        if response:
            try:
                # Extract CO2 value (high byte, low byte)
                co2 = (response[2] << 8) | response[3]

                # Validate reading (typical range 400-5000 ppm)
                if co2 < 0 or co2 > 5000:
                    logger.warning(f"Unusual CO2 reading: {co2} ppm")

                    # If it's extremely out of range, consider it an error
                    if co2 < 0 or co2 > 10000:
                        logger.warning("Reading out of valid range, ignoring")
                        return 0

                return co2
            except Exception as e:
                logger.error(f"Error processing CO2 reading: {e}")
                return 0
        else:
            logger.error("MH-Z19 read error")
            return 0

    def close(self):
        """Close the serial connection to the sensor."""
        if hasattr(self, 'serial') and self.serial.is_open:
            self.serial.close()
            logger.info("MH-Z19 connection closed")

    def get_readings(self):
        """Get all sensor readings as a dictionary.

        Returns:
            dict: Sensor readings including CO2 concentration
        """
        co2 = self.read_co2()
        return {
            "co2": co2
        }

class DataLogger:
    """Class to handle data logging to CSV files."""

    def __init__(self, data_dir=DATA_DIR, fixed_csv_path=FIXED_CSV_PATH):
        """Initialize the data logger.

        Args:
            data_dir (str): Directory to store daily CSV files
            fixed_csv_path (str): Path to the consolidated CSV file
        """
        self.data_dir = data_dir
        self.fixed_csv_path = fixed_csv_path

        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)

        logger.info(f"Data will be logged to: {data_dir}")
        logger.info(f"Consolidated data will be logged to: {fixed_csv_path}")

    def log_data(self, data):
        """Log data to CSV files.

        Args:
            data (dict): Data to log

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get current timestamp
            timestamp = datetime.datetime.now()
            timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

            # Add timestamp and device_id to data
            data["timestamp"] = timestamp_str
            data["device_id"] = "P1"

            # Get daily CSV file path
            daily_csv_path = os.path.join(self.data_dir, f"P1_{timestamp.strftime('%Y-%m-%d')}.csv")

            # Check if daily file exists
            daily_file_exists = os.path.isfile(daily_csv_path)

            # Check if fixed file exists
            fixed_file_exists = os.path.isfile(self.fixed_csv_path)

            # Define field names (headers)
            fieldnames = ["timestamp", "device_id", "temperature", "humidity", "pressure", "gas_resistance", "co2", "absolute_humidity"]

            # Write to daily CSV file
            with open(daily_csv_path, 'a', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                # Write headers if file is new
                if not daily_file_exists:
                    writer.writeheader()

                # Write data row
                writer.writerow(data)

            # Write to fixed CSV file
            with open(self.fixed_csv_path, 'a', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                # Write headers if file is new
                if not fixed_file_exists:
                    writer.writeheader()

                # Write data row
                writer.writerow(data)

            logger.info(f"Data logged to {daily_csv_path} and {self.fixed_csv_path}")
            return True

        except Exception as e:
            logger.error(f"Error logging data: {e}")
            logger.error(traceback.format_exc())
            return False

def signal_handler(sig, frame):
    """Handle Ctrl+C and other signals to ensure clean exit."""
    logger.info("\nProgram terminated by user")
    cleanup()
    sys.exit(0)

def cleanup():
    """Cleanup function to ensure sensor connections are properly closed."""
    if 'mhz19' in globals() and mhz19 is not None:
        mhz19.close()

def main():
    """Main function to read sensor data and log to CSV."""
    global mhz19

    # Register signal handler for clean exit
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Register cleanup function
    atexit.register(cleanup)

    logger.info("Starting P1_Sensor V1")

    # Initialize sensors
    try:
        logger.info("Initializing BME680 sensor...")
        bme680 = BME680()

        logger.info("Initializing MH-Z19 sensor...")
        mhz19 = MHZ19()

        # Wait for MH-Z19 to warm up
        if not mhz19.is_warmed_up:
            logger.info(f"Waiting for MH-Z19 to warm up ({mhz19.warmup_time} seconds)...")
            time.sleep(mhz19.warmup_time)
            mhz19.is_warmed_up = True
            logger.info("MH-Z19 warmup complete")

    except Exception as e:
        logger.error(f"Failed to initialize sensors: {e}")
        logger.error(traceback.format_exc())
        return 1

    # Initialize data logger
    try:
        logger.info("Initializing data logger...")
        data_logger = DataLogger()
    except Exception as e:
        logger.error(f"Failed to initialize data logger: {e}")
        logger.error(traceback.format_exc())
        return 1

    # Main loop
    try:
        logger.info(f"Starting main loop with {SAMPLING_INTERVAL} second interval...")

        while True:
            try:
                # Get BME680 readings
                bme680_readings = bme680.get_readings()

                # Get MH-Z19 readings
                mhz19_readings = mhz19.get_readings()

                # Combine readings
                combined_data = {**bme680_readings, **mhz19_readings}

                # Log data
                data_logger.log_data(combined_data)

                # Display readings in terminal
                logger.info(f"Temperature: {combined_data['temperature']:.1f}°C, "
                           f"Humidity: {combined_data['humidity']:.1f}%, "
                           f"Pressure: {combined_data['pressure']:.1f}hPa, "
                           f"Gas: {combined_data['gas_resistance']:.0f}Ω, "
                           f"CO2: {combined_data['co2']} ppm, "
                           f"Absolute Humidity: {combined_data['absolute_humidity']:.1f} g/m³")

                # Wait for next reading
                time.sleep(SAMPLING_INTERVAL)

            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                logger.error(traceback.format_exc())
                time.sleep(5)  # Wait a bit before retrying

    except KeyboardInterrupt:
        logger.info("Program stopped by user")

    finally:
        # Ensure sensors are properly closed
        cleanup()

    return 0

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
P1_Sensor V1 - Modified for CO2 integration and improved functionality
"""

import time
import csv
import sys
import signal
import serial
import datetime
import os
import atexit
import logging
from collections import OrderedDict

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("p1_sensor.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# --- Constants ---
DATA_DIR = "/var/lib(FromThonny)/raspap_solo/data/RawData_P1"
FIXED_CSV_PATH = os.path.join(DATA_DIR, "P1_fixed.csv")
SAMPLING_INTERVAL = 30  # seconds
BME680_I2C_ADDR = 0x77  # BME680 I2C address
MHZ19_UART_DEVICE = '/dev/ttyAMA0'
MHZ19_BAUDRATE = 9600


class SensorHandler:
    """A combined class for handling BME680 and MH-Z19 sensors."""

    def __init__(self):
        # Initialize BME680 and MH-Z19 sensors
        self.bme680 = self._initialize_bme680()
        self.mhz19 = self._initialize_mhz19()

    def _initialize_bme680(self):
        from bme680 import BME680  # Assuming BME680 module is installed.
        try:
            logger.info("Initializing BME680 sensor...")
            sensor = BME680(i2c_addr=BME680_I2C_ADDR)

            # Set oversampling and filter options using values from bme680 documentation or API
            sensor.set_humidity_oversample(sensor.OVERSAMPLE_2X)
            sensor.set_pressure_oversample(sensor.OVERSAMPLE_4X)
            sensor.set_temperature_oversample(sensor.OVERSAMPLE_8X)
            sensor.set_filter(sensor.FILTER_SIZE_3)
            sensor.set_gas_status(sensor.ENABLE_GAS_MEAS)

            sensor.set_gas_heater_temperature(320)  # Target heater temperature
            sensor.set_gas_heater_duration(150)  # Heater duration in ms
            sensor.select_gas_heater_profile(0)  # Use heater profile 0

            logger.info("BME680 initialized successfully.")
            return sensor
        except AttributeError as e:
            logger.error(f"BME680 attribute error: {e}. Check library version and functionality.")
            sys.exit(1)
        except Exception as e:
            logger.error(f"BME680 initialization failed: {e}")
            sys.exit(1)

    def _initialize_mhz19(self):
        try:
            logger.info("Initializing MH-Z19 sensor...")
            ser = serial.Serial(port=MHZ19_UART_DEVICE, baudrate=MHZ19_BAUDRATE, timeout=1.0)
            logger.info("MH-Z19 initialized successfully.")
            return ser
        except Exception as e:
            logger.error(f"MH-Z19 initialization failed: {e}")
            sys.exit(1)

    def read_bme680(self):
        try:
            reading = {
                "temperature": self.bme680.data.temperature,
                "humidity": self.bme680.data.humidity,
                "pressure": self.bme680.data.pressure,
                "gas": self.bme680.data.gas_resistance,
                "absolute_humidity": self.calculate_absolute_humidity(
                    self.bme680.data.temperature, self.bme680.data.humidity)
            }
            return reading
        except Exception as e:
            logger.error(f"Failed to read BME680: {e}")
            return {}

    def read_mhz19(self):
        try:
            command = b'\xff\x01\x86\x00\x00\x00\x00\x00\x79'
            self.mhz19.write(command)
            response = self.mhz19.read(9)
            if len(response) == 9 and response[0] == 0xFF and response[1] == 0x86:
                co2 = response[2] * 256 + response[3]
                return {"co2": co2}
            else:
                logger.warning("Invalid MH-Z19 response.")
                return {"co2": 0}
        except Exception as e:
            logger.error(f"Failed to read MH-Z19: {e}")
            return {"co2": 0}

    @staticmethod
    def calculate_absolute_humidity(temp, humidity):
        """Calculate absolute humidity (g/m³)"""
        try:
            if temp is None or humidity is None:
                return 0.0
            sat_vapor_pressure = 6.1078 * 10 ** ((7.5 * temp) / (237.3 + temp))
            vapor_pressure = sat_vapor_pressure * humidity / 100.0
            abs_humidity = 216.7 * (vapor_pressure / (273.15 + temp))
            return round(abs_humidity, 2)
        except Exception as e:
            logger.error(f"Failed to calculate absolute humidity: {e}")
            return 0.0


class DataLogger:
    """Handles logging of data to CSV files."""

    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)

    def log(self, data):
        timestamp = datetime.datetime.now()
        daily_csv_path = os.path.join(DATA_DIR, f"P1_{timestamp.strftime('%Y-%m-%d')}.csv")
        data["timestamp"] = timestamp.strftime("%Y-%m-%d %H:%M:%S")

        # Write data to daily CSV
        self._write_csv(daily_csv_path, data)

        # Write data to consolidated CSV
        self._write_csv(FIXED_CSV_PATH, data)

        logger.info("Saved data: " + ", ".join(f"{k}: {v}" for k, v in data.items()))

    def _write_csv(self, filepath, data):
        """Helper to write to CSV."""
        is_new = not os.path.exists(filepath)
        with open(filepath, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=data.keys())
            if is_new:
                writer.writeheader()
            writer.writerow(data)


def cleanup(signal_received, frame):
    """Clean up resources."""
    logger.info("Terminating program...")
    sys.exit(0)


def main():
    """Main loop for data collection."""
    # Setup signal handlers
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    sensors = SensorHandler()
    logger = DataLogger()

    while True:
        bme_data = sensors.read_bme680()
        mhz19_data = sensors.read_mhz19()
        combined_data = {**bme_data, **mhz19_data}
        logger.log(OrderedDict(combined_data))
        time.sleep(SAMPLING_INTERVAL)


if __name__ == "__main__":
    main()
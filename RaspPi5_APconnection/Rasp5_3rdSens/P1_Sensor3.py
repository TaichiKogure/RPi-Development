#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import csv
import os
import sys
import datetime
import serial
import logging
import signal
import bme680

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("p1_sensor.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# --- Constants ---
DATA_DIR = "/var/lib/raspap_solo/data/RawData_P1"
FIXED_CSV_PATH = os.path.join(DATA_DIR, "P1_fixed.csv")
SAMPLING_INTERVAL = 30  # seconds
MHZ19_UART_DEVICE = "/dev/ttyAMA0"
MHZ19_BAUDRATE = 9600

CSV_HEADER = [
    "timestamp",
    "device_id",
    "temperature",
    "humidity",
    "pressure",
    "gas_resistance",
    "co2",
    "absolute_humidity",
]

# --- Sensor Initialization ---
class Sensors:
    def __init__(self):
        self.bme680_sensor = self._initialize_bme680()
        self.mhz19_serial = self._initialize_mhz19()

    def _initialize_bme680(self):
        try:
            logger.info("Initializing BME680 sensor...")
            sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
            sensor.set_humidity_oversample(bme680.OS_2X)
            sensor.set_pressure_oversample(bme680.OS_4X)
            sensor.set_temperature_oversample(bme680.OS_8X)
            sensor.set_filter(bme680.FILTER_SIZE_3)
            sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
            sensor.set_gas_heater_temperature(320)
            sensor.set_gas_heater_duration(150)
            sensor.select_gas_heater_profile(0)
            logger.info("BME680 initialized successfully.")
            return sensor
        except (RuntimeError, IOError):
            try:
                return bme680.BME680(bme680.I2C_ADDR_SECONDARY)
            except Exception as e:
                logger.error(f"Failed to initialize BME680: {e}")
                sys.exit(1)

    def _initialize_mhz19(self):
        try:
            logger.info("Initializing MH-Z19 sensor...")
            ser = serial.Serial(
                port=MHZ19_UART_DEVICE, baudrate=MHZ19_BAUDRATE, timeout=1.0
            )
            logger.info("MH-Z19 initialized successfully.")
            return ser
        except Exception as e:
            logger.error(f"Failed to initialize MH-Z19: {e}")
            sys.exit(1)

    def get_bme680_data(self):
        try:
            if not self.bme680_sensor.get_sensor_data():
                return None
            data = {
                "temperature": self.bme680_sensor.data.temperature,
                "humidity": self.bme680_sensor.data.humidity,
                "pressure": self.bme680_sensor.data.pressure,
                "gas_resistance": self.bme680_sensor.data.gas_resistance,
                "absolute_humidity": self.calculate_absolute_humidity(
                    self.bme680_sensor.data.temperature,
                    self.bme680_sensor.data.humidity,
                ),
            }
            return data
        except Exception as e:
            logger.error(f"Error reading BME680 data: {e}")
            return None

    def get_mhz19_data(self):
        try:
            command = b"\xff\x01\x86\x00\x00\x00\x00\x00\x79"
            self.mhz19_serial.write(command)
            response = self.mhz19_serial.read(9)
            if len(response) == 9 and response[0] == 0xFF and response[1] == 0x86:
                co2 = response[2] * 256 + response[3]
                return {"co2": co2}
            else:
                logger.warning("Invalid response from MH-Z19 sensor.")
                return {"co2": None}
        except Exception as e:
            logger.error(f"Error reading MH-Z19 data: {e}")
            return {"co2": None}

    @staticmethod
    def calculate_absolute_humidity(temp, humidity):
        try:
            if temp is None or humidity is None:
                return 0
            sat_vapor_pressure = 6.1078 * 10 ** ((7.5 * temp) / (237.3 + temp))
            vapor_pressure = sat_vapor_pressure * humidity / 100
            absolute_humidity = 216.7 * (vapor_pressure / (273.15 + temp))
            return round(absolute_humidity, 2)
        except Exception as e:
            logger.error(f"Error calculating absolute humidity: {e}")
            return 0


# --- Data Logger ---
class DataLogger:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)

    def log_data(self, data):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data["timestamp"] = timestamp
        data["device_id"] = "P1"
        daily_path = os.path.join(DATA_DIR, f"P1_{datetime.datetime.now().strftime('%Y-%m-%d')}.csv")

        try:
            # Log to daily CSV
            self._write_to_csv(daily_path, data)
            # Log to fixed CSV
            self._write_to_csv(FIXED_CSV_PATH, data)
        except IOError as e:
            logger.error(f"Failed to write log data to CSV: {e}")

    def _write_to_csv(self, filepath, data):
        is_new_file = not os.path.exists(filepath)
        with open(filepath, mode="a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
            if is_new_file:
                writer.writeheader()  # Write header only once
            ordered_data = {key: data.get(key, None) for key in CSV_HEADER}
            writer.writerow(ordered_data)


# --- Main Function ---
def cleanup_handler(signal_received, frame):
    logger.info("Termination requested by user. Cleaning up and exiting...")
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, cleanup_handler)
    signal.signal(signal.SIGTERM, cleanup_handler)

    sensors = Sensors()
    logger_instance = DataLogger()

    while True:
        bme680_data = sensors.get_bme680_data()
        mhz19_data = sensors.get_mhz19_data()

        if bme680_data is None or mhz19_data.get("co2") is None:
            logger.warning("Skipping logging due to sensor read failure.")
        else:
            combined_data = {**bme680_data, **mhz19_data}
            logger_instance.log_data(combined_data)
            logger.info(
                f"Logged Data: {combined_data['timestamp']},{combined_data['device_id']},"
                f"{combined_data['temperature']},{combined_data['humidity']},"
                f"{combined_data['pressure']},{combined_data['gas_resistance']},"
                f"{combined_data['co2']},{combined_data['absolute_humidity']}"
            )

        time.sleep(SAMPLING_INTERVAL)


if __name__ == "__main__":
    main()
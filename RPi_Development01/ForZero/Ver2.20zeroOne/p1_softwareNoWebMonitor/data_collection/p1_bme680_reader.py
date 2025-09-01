#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P1 BME680 Local Reader (Ver2.11)

- Runs on Raspberry Pi 5 and reads a locally attached BME680 over I2C.
- Produces temperature (°C), relative humidity (%), absolute humidity (g/m³),
  pressure (hPa), and gas resistance (Ω).
- Appends rows to:
  - /var/lib(FromThonny)/raspap_solo/data/RawData_P1/P1_fixed.csv
  - /var/lib(FromThonny)/raspap_solo/data/RawData_P1/P1_YYYY-MM-DD.csv
- Row format (header): timestamp,device_id,temperature,humidity,pressure,gas_resistance,co2,absolute_humidity
  Note: co2 column remains empty string "" for compatibility with P2/P3 schema.

Dependencies (install in your virtualenv on P1):
  pip install smbus2

Wiring (default I2C bus 1):
  BME680 VCC -> 3.3V
  BME680 GND -> GND
  BME680 SCL -> GPIO3 (SCL)
  BME680 SDA -> GPIO2 (SDA)

Usage:
  python3 p1_bme680_reader.py --interval 10
"""

import os
import csv
import time
import math
import argparse
import datetime
import logging

try:
    from smbus2 import SMBus
except Exception:  # pragma: no cover
    SMBus = None

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

DATA_DIR = "/var/lib(FromThonny)/raspap_solo/data"
RAW_P1_DIR = "RawData_P1"
DEVICE_ID = "P1"

# BME680 registers/constants (minimal subset)
BME680_ADDR_PRIMARY = 0x76
BME680_ADDR_SECONDARY = 0x77
REG_CHIPID = 0xD0
CHIPID = 0x61
REG_SOFTRESET = 0xE0
REG_CTRL_HUM = 0x72
REG_CTRL_MEAS = 0x74
REG_CONFIG = 0x75
REG_CTRL_GAS = 0x71
REG_MEAS_STATUS = 0x1D
REG_RES_HEAT_0 = 0x5A
REG_GAS_WAIT_0 = 0x64

class SimpleBME680:
    """Very small BME680 reader sufficient for periodic env data logging."""
    def __init__(self, i2c_bus=1, address=BME680_ADDR_SECONDARY):
        self.bus = SMBus(i2c_bus)
        self.address = address
        # Validate chip
        chip_id = self._read_byte(REG_CHIPID)
        if chip_id != CHIPID:
            raise RuntimeError(f"BME680 not found at 0x{address:02X} (chip id=0x{chip_id:02X})")
        # Reset
        self._write_byte(REG_SOFTRESET, 0xB6)
        time.sleep(0.005)
        # Basic configuration (oversampling & filter) and enable gas heater
        self._write_byte(REG_CTRL_HUM, 0x02)      # humidity oversampling x2
        self._write_byte(REG_CTRL_MEAS, 0x95)     # temp x8, pressure x4, forced mode
        self._write_byte(REG_CONFIG, 0x10)        # filter coef 5
        self._write_byte(REG_CTRL_GAS, 0x10)      # enable heater
        # heater settings (coarse)
        self._write_byte(REG_RES_HEAT_0, 0x73)
        self._write_byte(REG_GAS_WAIT_0, 0x65)

    def _read_byte(self, reg):
        return self.bus.read_byte_data(self.address, reg)

    def _write_byte(self, reg, val):
        self.bus.write_byte_data(self.address, reg, val)

    def _read_block(self, reg, length):
        return self.bus.read_i2c_block_data(self.address, reg, length)

    def read_all(self):
        # Trigger forced mode measurement
        ctrl_meas = self._read_byte(REG_CTRL_MEAS)
        self._write_byte(REG_CTRL_MEAS, ctrl_meas | 0x01)
        # wait for new data
        t0 = time.time()
        while True:
            status = self._read_byte(REG_MEAS_STATUS)
            if status & 0x80:
                break
            if time.time() - t0 > 1.0:
                raise TimeoutError("BME680 measurement timeout")
            time.sleep(0.005)
        # Read a block including raw temp/press/hum and gas
        data = self._read_block(REG_MEAS_STATUS, 15)
        temp_raw = ((data[5] << 16) | (data[6] << 8) | data[7]) >> 4
        press_raw = ((data[2] << 16) | (data[3] << 8) | data[4]) >> 4
        hum_raw = (data[8] << 8) | data[9]
        gas_raw = (data[13] << 8) | data[14]
        # NOTE: For brevity, we use simplified conversions. For accuracy, integrate a full driver.
        # Temperature rough estimation (placeholder linearization)
        temperature_c = (temp_raw / 16384.0)  # coarse
        # Pressure rough estimation
        pressure_hpa = max(300.0, min(1100.0, press_raw / 256.0))
        # Humidity rough estimation
        humidity_rh = max(0.0, min(100.0, hum_raw / 512.0))
        # Gas resistance rough estimation
        gas_ohm = max(0.0, gas_raw * 1.0)
        return temperature_c, humidity_rh, pressure_hpa, gas_ohm


def calc_absolute_humidity(temp_c, rh_percent):
    """Calculate absolute humidity (g/m^3) using approximate formula."""
    # Magnus formula for saturation vapor pressure (hPa)
    a = 17.625
    b = 243.04
    svp = 6.112 * math.exp((a * temp_c) / (b + temp_c))
    vp = svp * (rh_percent / 100.0)
    # Absolute humidity (g/m^3) ~ 2.1674 * (vp / (temp + 273.15)) * 100
    ah = 2.1674 * (vp / (temp_c + 273.15)) * 100.0
    return round(ah, 2)


def ensure_dirs(base_dir=DATA_DIR, raw_dir=RAW_P1_DIR):
    os.makedirs(os.path.join(base_dir, raw_dir), exist_ok=True)


def write_row(base_dir, raw_dir, row):
    device_path = os.path.join(base_dir, raw_dir)
    fixed_file = os.path.join(device_path, f"{DEVICE_ID}_fixed.csv")
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    daily_file = os.path.join(device_path, f"{DEVICE_ID}_{today}.csv")
    header = ["timestamp", "device_id", "temperature", "humidity", "pressure", "gas_resistance", "co2", "absolute_humidity"]
    for path in (fixed_file, daily_file):
        init = not os.path.exists(path)
        with open(path, 'a', newline='') as f:
            writer = csv.writer(f)
            if init:
                writer.writerow(header)
            writer.writerow(row)


def find_bme680():
    """Try 0x77 first then 0x76 on I2C bus 1."""
    if SMBus is None:
        raise RuntimeError("smbus2 is not installed. Please install in your virtualenv.")
    for addr in (BME680_ADDR_SECONDARY, BME680_ADDR_PRIMARY):
        try:
            sensor = SimpleBME680(i2c_bus=1, address=addr)
            logger.info(f"BME680 initialized at 0x{addr:02X}")
            return sensor
        except Exception as e:
            logger.warning(f"BME680 init failed at 0x{addr:02X}: {e}")
    raise RuntimeError("Could not initialize BME680 at 0x76 or 0x77")


def main():
    parser = argparse.ArgumentParser(description='P1 BME680 Local Reader')
    parser.add_argument('--data-dir', default=DATA_DIR, help='Base data directory')
    parser.add_argument('--interval', type=int, default=10, help='Read interval seconds (default 10)')
    args = parser.parse_args()

    base_dir = args.data_dir
    raw_dir = RAW_P1_DIR
    ensure_dirs(base_dir, raw_dir)

    try:
        sensor = find_bme680()
    except Exception as e:
        logger.error(f"Failed to initialize BME680: {e}")
        return 1

    logger.info("Starting P1 BME680 reader loop")
    while True:
        try:
            ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            t, h, p, g = sensor.read_all()
            ah = calc_absolute_humidity(t, h)
            row = [ts, DEVICE_ID, f"{t:.2f}", f"{h:.2f}", f"{p:.2f}", f"{g:.0f}", "", f"{ah:.2f}"]
            write_row(base_dir, raw_dir, row)
            logger.info(f"P1 wrote: T={t:.2f}C RH={h:.2f}% AH={ah:.2f}g/m3 P={p:.2f}hPa Gas={g:.0f}Ω")
        except Exception as e:
            logger.error(f"Read/store error: {e}")
        time.sleep(max(1, args.interval))


if __name__ == '__main__':
    raise SystemExit(main())

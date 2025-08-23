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

class PortedBME680:
    """BME680 reader using accurate compensation logic adapted from OK2bme/Adafruit driver.
    This version uses smbus2 on Raspberry Pi (CPython).
    """
    # Registers from OK2bme driver
    _REG_CHIPID = 0xD0
    _CHIPID = 0x61
    _COEFF_ADDR1 = 0x89
    _COEFF_ADDR2 = 0xE1
    _REG_SOFTRESET = 0xE0
    _REG_CTRL_GAS = 0x71
    _REG_CTRL_HUM = 0x72
    _REG_CTRL_MEAS = 0x74
    _REG_CONFIG = 0x75
    _REG_PAGE_SELECT = 0x73
    _REG_MEAS_STATUS = 0x1D
    _REG_PDATA = 0x1F
    _REG_TDATA = 0x22
    _REG_HDATA = 0x25
    _RES_HEAT_0 = 0x5A
    _GAS_WAIT_0 = 0x64

    def __init__(self, i2c_bus=1, address=BME680_ADDR_SECONDARY):
        if SMBus is None:
            raise RuntimeError("smbus2 is not installed. Please install in your virtualenv.")
        self.bus = SMBus(i2c_bus)
        self.address = address
        # Reset and check chip
        self._write_byte(self._REG_SOFTRESET, 0xB6)
        time.sleep(0.005)
        chip_id = self._read_byte(self._REG_CHIPID)
        if chip_id != self._CHIPID:
            raise RuntimeError(f"BME680 not found at 0x{address:02X} (chip id=0x{chip_id:02X})")
        # Read calibration coefficients
        self._read_calibration()
        # Heater config (same as OK2bme)
        self._write_byte(self._RES_HEAT_0, 0x73)
        self._write_byte(self._GAS_WAIT_0, 0x65)
        # Default oversampling/filter
        self._pressure_oversample = 0b011
        self._temp_oversample = 0b100
        self._humidity_oversample = 0b010
        self._filter = 0b010
        # Internal state
        self._adc_pres = None
        self._adc_temp = None
        self._adc_hum = None
        self._adc_gas = None
        self._gas_range = None
        self._t_fine = None

    def _read_byte(self, reg):
        return self.bus.read_byte_data(self.address, reg)

    def _read_block(self, reg, length):
        return self.bus.read_i2c_block_data(self.address, reg & 0xFF, length)

    def _write_byte(self, reg, val):
        self.bus.write_byte_data(self.address, reg & 0xFF, val & 0xFF)

    def _read(self, register, length):
        return self._read_block(register, length)

    def _write(self, register, values):
        reg = register & 0xFF
        for v in values:
            self._write_byte(reg, v)
            reg += 1

    def _read_calibration(self):
        import struct
        coeff = self._read(self._COEFF_ADDR1, 25)
        coeff += self._read(self._COEFF_ADDR2, 16)
        coeff = list(struct.unpack('<hbBHhbBhhbbHhhBBBHbbbBbHhbb', bytes(coeff[1:39])))
        coeff = [float(i) for i in coeff]
        self._temp_calibration = [coeff[x] for x in [23, 0, 1]]
        self._pressure_calibration = [coeff[x] for x in [3, 4, 5, 7, 8, 10, 9, 12, 13, 14]]
        self._humidity_calibration = [coeff[x] for x in [17, 16, 18, 19, 20, 21, 22]]
        self._gas_calibration = [coeff[x] for x in [25, 24, 26]]
        # flip around H1 & H2
        self._humidity_calibration[1] *= 16
        self._humidity_calibration[1] += self._humidity_calibration[0] % 16
        self._humidity_calibration[0] /= 16
        # additional parameters
        self._heat_range = (self._read_byte(0x02) & 0x30) / 16
        self._heat_val = self._read_byte(0x00)
        self._sw_err = (self._read_byte(0x04) & 0xF0) / 16

    def _perform_reading(self):
        # configure filter and oversampling
        self._write(self._REG_CONFIG, [self._filter << 2])
        self._write(self._REG_CTRL_MEAS, [(self._temp_oversample << 5) | (self._pressure_oversample << 2)])
        self._write(self._REG_CTRL_HUM, [self._humidity_oversample])
        # enable gas measurement
        self._write(self._REG_CTRL_GAS, [0x10])
        # trigger forced mode
        ctrl = self._read_byte(self._REG_CTRL_MEAS)
        ctrl = (ctrl & 0xFC) | 0x01
        self._write(self._REG_CTRL_MEAS, [ctrl])
        # wait for new_data flag
        t0 = time.time()
        new_data = False
        while not new_data:
            data = self._read(self._REG_MEAS_STATUS, 15)
            new_data = (data[0] & 0x80) != 0
            if time.time() - t0 > 1.0:
                raise TimeoutError("BME680 measurement timeout")
            time.sleep(0.005)
        # parse raw values
        def _read24(arr):
            ret = 0.0
            for b in arr:
                ret *= 256.0
                ret += float(b & 0xFF)
            return ret
        import struct
        self._adc_pres = _read24(data[2:5]) / 16
        self._adc_temp = _read24(data[5:8]) / 16
        self._adc_hum = struct.unpack('>H', bytes(data[8:10]))[0]
        self._adc_gas = int(struct.unpack('>H', bytes(data[13:15]))[0] / 64)
        self._gas_range = data[14] & 0x0F
        var1 = (self._adc_temp / 8) - (self._temp_calibration[0] * 2)
        var2 = (var1 * self._temp_calibration[1]) / 2048
        var3 = ((var1 / 2) * (var1 / 2)) / 4096
        var3 = (var3 * self._temp_calibration[2] * 16) / 16384
        self._t_fine = int(var2 + var3)

    def read_all(self):
        self._perform_reading()
        # temperature
        calc_temp = (((self._t_fine * 5) + 128) / 256) / 100.0
        temperature_c = calc_temp
        # pressure
        var1 = (self._t_fine / 2) - 64000
        var2 = ((var1 / 4) * (var1 / 4)) / 2048
        var2 = (var2 * self._pressure_calibration[5]) / 4
        var2 = var2 + (var1 * self._pressure_calibration[4] * 2)
        var2 = (var2 / 4) + (self._pressure_calibration[3] * 65536)
        var1 = (((((var1 / 4) * (var1 / 4)) / 8192) * (self._pressure_calibration[2] * 32) / 8) +
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
        pressure_hpa = calc_pres / 100.0
        # humidity
        temp_scaled = ((self._t_fine * 5) + 128) / 256
        var1 = ((self._adc_hum - (self._humidity_calibration[0] * 16)) -
                ((temp_scaled * self._humidity_calibration[2]) / 200))
        var2 = (self._humidity_calibration[1] *
                (((temp_scaled * self._humidity_calibration[3]) / 100) +
                 (((temp_scaled * ((temp_scaled * self._humidity_calibration[4]) / 100)) / 64) / 100) + 16384)) / 1024
        var3 = var1 * var2
        var4 = self._humidity_calibration[5] * 128
        var4 = (var4 + ((temp_scaled * self._humidity_calibration[6]) / 100)) / 16
        var5 = ((var3 / 16384) * (var3 / 16384)) / 1024
        var6 = (var4 * var5) / 2
        calc_hum = (((var3 + var6) / 1024) * 1000) / 4096
        humidity_rh = max(0.0, min(100.0, calc_hum / 1000.0))
        # gas resistance (Ohms)
        LOOKUP_TABLE_1 = (2147483647.0, 2147483647.0, 2147483647.0, 2147483647.0, 2147483647.0,
                          2126008810.0, 2147483647.0, 2130303777.0, 2147483647.0, 2147483647.0,
                          2143188679.0, 2136746228.0, 2147483647.0, 2126008810.0, 2147483647.0,
                          2147483647.0)
        LOOKUP_TABLE_2 = (4096000000.0, 2048000000.0, 1024000000.0, 512000000.0, 255744255.0, 127110228.0,
                          64000000.0, 32258064.0, 16016016.0, 8000000.0, 4000000.0, 2000000.0, 1000000.0,
                          500000.0, 250000.0, 125000.0)
        var1 = ((1340 + (5 * self._sw_err)) * (LOOKUP_TABLE_1[self._gas_range])) / 65536
        var2 = ((self._adc_gas * 32768) - 16777216) + var1
        var3 = (LOOKUP_TABLE_2[self._gas_range] * var1) / 512
        gas_ohm = (var3 + (var2 / 2)) / var2
        return float(temperature_c), float(humidity_rh), float(pressure_hpa), float(int(gas_ohm))


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
            sensor = PortedBME680(i2c_bus=1, address=addr)
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

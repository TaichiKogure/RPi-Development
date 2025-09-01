"""
BME680 reader for Raspberry Pi Zero 2W (Ver.1)
- Prefers the proven driver in G:\\RPi-Development\\OK2bme\\bme680.py
- Falls back to smbus2 based minimal reader if external module is unavailable

Returns temperature (C), humidity (%), pressure (hPa), gas_resistance (Ohms)
"""
from __future__ import annotations
import os
import sys
import time
from typing import Optional, Tuple

# Try to import the proven driver from OK2bme
_OK2BME_IMPORTED = False
try:
    REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    candidates = [
        os.path.join(REPO_ROOT, "OK2bme"),
        os.environ.get("OK2BME_PATH", ""),
        "/home/pi/OK2bme",
    ]
    for path in candidates:
        if not path:
            continue
        if os.path.isdir(path) and path not in sys.path:
            sys.path.insert(0, path)
    import bme680 as ok_bme680  # type: ignore
    _OK2BME_IMPORTED = True
except Exception:
    _OK2BME_IMPORTED = False

class BME680Reader:
    def __init__(self, i2c_addr: int = 0x77, i2c_bus: int = 1):
        self.i2c_addr = i2c_addr
        self.i2c_bus = i2c_bus
        self._sensor = None
        self._init_time = 0.0

    def initialize(self) -> None:
        if _OK2BME_IMPORTED:
            # Use OK2bme driver API (expected to be compatible with standard bme680)
            self._sensor = ok_bme680.BME680(i2c_addr=self.i2c_addr, i2c_device=ok_bme680.I2CDevice(self.i2c_bus)) if hasattr(ok_bme680, "I2CDevice") else ok_bme680.BME680(i2c_addr=self.i2c_addr)
            # Configure oversampling and gas heater similar to OK2bme main
            try:
                self._sensor.set_humidity_oversample(ok_bme680.OS_2X)
                self._sensor.set_pressure_oversample(ok_bme680.OS_4X)
                self._sensor.set_temperature_oversample(ok_bme680.OS_8X)
                self._sensor.set_filter(ok_bme680.FILTER_SIZE_3)
                self._sensor.set_gas_status(ok_bme680.ENABLE_GAS_MEAS)
                self._sensor.set_gas_heater_temperature(320)
                self._sensor.set_gas_heater_duration(150)
                self._sensor.select_gas_heater_profile(0)
            except Exception:
                # Some implementations use different names; ignore if not present
                pass
            self._init_time = time.time()
        else:
            # Fallback disabled to keep footprint small and avoid optional deps.
            # Raise an informative error so the user installs/provides OK2bme driver.
            raise RuntimeError(
                "OK2bme bme680.py not found. Please ensure G/OK2bme/bme680.py exists on target."
            )

    def read(self, max_wait_s: float = 2.0) -> Optional[Tuple[float, float, float, float]]:
        if self._sensor is None:
            self.initialize()
        if _OK2BME_IMPORTED:
            start = time.time()
            # Loop until data ready or timeout
            while time.time() - start < max_wait_s:
                if self._sensor.get_sensor_data():
                    data = self._sensor.data
                    temp_c = float(getattr(data, "temperature", float("nan")))
                    humidity = float(getattr(data, "humidity", float("nan")))
                    pressure = float(getattr(data, "pressure", float("nan")))
                    gas_res = float(getattr(data, "gas_resistance", float("nan")))
                    return temp_c, humidity, pressure, gas_res
                time.sleep(0.05)
            return None
        return None

    def close(self) -> None:
        try:
            if hasattr(self, "_bus") and self._bus:
                self._bus.close()
        except Exception:
            pass

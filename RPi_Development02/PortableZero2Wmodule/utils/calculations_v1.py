"""
Utility calculations for Portable Zero2W module Ver.1
- Absolute Humidity (g/m^3)
- Discomfort Index (DI)
- Air pollution indicator from BME680 gas resistance
"""
from __future__ import annotations
import math
from typing import Tuple


def absolute_humidity_gm3(temperature_c: float, rh_percent: float) -> float:
    """Compute absolute humidity in g/m^3 using temperature (C) and relative humidity (%).
    Formula based on Magnus and ideal gas law.
    """
    if temperature_c is None or rh_percent is None:
        return float("nan")
    # Saturation vapor pressure (hPa)
    svp = 6.112 * math.exp((17.67 * temperature_c) / (temperature_c + 243.5))
    vp = svp * (rh_percent / 100.0)  # actual vapor pressure (hPa)
    # Absolute humidity (g/m^3)
    ah = 2.1674 * (vp * 100) / (273.15 + temperature_c)
    return ah


def discomfort_index(temperature_c: float, rh_percent: float) -> float:
    """Calculate the Thom Discomfort Index.
    DI = T - 0.55*(1 - RH/100)*(T - 14.5)
    """
    if temperature_c is None or rh_percent is None:
        return float("nan")
    return temperature_c - 0.55 * (1 - rh_percent / 100.0) * (temperature_c - 14.5)


def pollution_index_from_gas(gas_res_ohm: float) -> Tuple[float, str]:
    """Map BME680 gas resistance to a simple 0..100 pollution index (higher worse) and label.
    Heuristic: higher resistance -> cleaner air. Lower resistance -> polluted.
    We normalize between 5kΩ (very polluted) and 200kΩ (clean).
    """
    if gas_res_ohm is None or gas_res_ohm <= 0:
        return float("nan"), "unknown"
    min_r = 5_000.0
    max_r = 200_000.0
    clamped = max(min_r, min(max_r, gas_res_ohm))
    # Cleanliness fraction: 0 (min_r) .. 1 (max_r)
    clean_frac = (clamped - min_r) / (max_r - min_r)
    pollution_index = (1.0 - clean_frac) * 100.0
    if pollution_index < 20:
        level = "very_good"
    elif pollution_index < 40:
        level = "good"
    elif pollution_index < 60:
        level = "moderate"
    elif pollution_index < 80:
        level = "poor"
    else:
        level = "very_poor"
    return pollution_index, level

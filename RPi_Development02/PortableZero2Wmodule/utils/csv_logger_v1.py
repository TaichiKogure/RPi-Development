"""
CSV streaming logger for Portable Zero2W module Ver.1
- Writes to daily file (YYYY-MM-DD.csv) and total file (total.csv)
- Ensures header exists
- Rotates total.csv if size exceeds a threshold
- Minimal memory footprint (line-by-line)
"""
from __future__ import annotations
import os
import csv
import time
import datetime as dt
from typing import Dict, List, Optional

DEFAULT_FIELDS: List[str] = [
    "timestamp_iso",
    "timestamp_epoch",
    "temperature_c",
    "humidity_percent",
    "absolute_humidity_gm3",
    "pressure_hpa",
    "gas_resistance_ohm",
    "pollution_index",
    "pollution_level",
    "co2_ppm",
    "discomfort_index",
    "bme680_ok",
    "mhz19_ok",
]


class CSVLogger:
    def __init__(self, base_dir: str = "data", total_max_bytes: int = 10 * 1024 * 1024, fields: Optional[List[str]] = None):
        self.base_dir = base_dir
        self.daily_dir = os.path.join(base_dir, "daily")
        self.total_path = os.path.join(base_dir, "total.csv")
        self.total_max_bytes = total_max_bytes
        self.fields = fields or DEFAULT_FIELDS
        os.makedirs(self.daily_dir, exist_ok=True)
        os.makedirs(self.base_dir, exist_ok=True)

    def _ensure_header(self, path: str) -> None:
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.fields)
                writer.writeheader()

    def _rotate_total_if_needed(self) -> None:
        if os.path.exists(self.total_path) and os.path.getsize(self.total_path) > self.total_max_bytes:
            ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            rotated = os.path.join(self.base_dir, f"total_{ts}.csv")
            os.replace(self.total_path, rotated)

    def log(self, row: Dict[str, object]) -> None:
        # Fill missing fields with empty
        record = {k: row.get(k, "") for k in self.fields}
        today = dt.datetime.now().strftime("%Y-%m-%d")
        daily_path = os.path.join(self.daily_dir, f"{today}.csv")

        # Daily file
        self._ensure_header(daily_path)
        with open(daily_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.fields)
            writer.writerow(record)

        # Total file with rotation
        self._rotate_total_if_needed()
        self._ensure_header(self.total_path)
        with open(self.total_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.fields)
            writer.writerow(record)

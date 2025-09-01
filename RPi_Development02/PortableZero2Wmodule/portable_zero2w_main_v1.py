#!/usr/bin/env python3
"""
Portable Zero2W Environmental Monitor Ver.1
- BME680 (via OK2bme driver)
- MH-Z19(B/C) on /dev/serial0
- Console output, CSV logging (daily + total), basic analytics
- Auto-recovery: per-sensor reinit/retry with backoff
"""
from __future__ import annotations
import os
import sys
import time
import signal
import argparse
import datetime as dt
from typing import Optional

# Local imports
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
if MODULE_DIR not in sys.path:
    sys.path.insert(0, MODULE_DIR)

from sensors.bme680_reader_v1 import BME680Reader
from sensors.mhz19_reader_v1 import MHZ19Reader
from utils.calculations_v1 import absolute_humidity_gm3, discomfort_index, pollution_index_from_gas
from utils.csv_logger_v1 import CSVLogger

RUNNING = True

def _signal_handler(signum, frame):
    global RUNNING
    print(f"\n[INFO] Signal {signum} received. Shutting down...")
    RUNNING = False


def parse_args():
    p = argparse.ArgumentParser(description="Portable Zero2W Environmental Monitor Ver.1")
    p.add_argument("--interval", type=float, default=10.0, help="Sampling interval in seconds (default: 10)")
    p.add_argument("--data-dir", type=str, default=os.path.join(MODULE_DIR, "data"), help="Base directory for CSV logs")
    p.add_argument("--i2c-addr", type=lambda x: int(x, 0), default=0x77, help="BME680 I2C address (default: 0x77)")
    p.add_argument("--warmup", type=float, default=30.0, help="MH-Z19 warmup time in seconds (default: 30)")
    p.add_argument("--print-every", type=int, default=1, help="Print every N samples (default: 1)")
    return p.parse_args()


def main():
    args = parse_args()

    # Signal handlers
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    print("=== Portable Zero2W Environmental Monitor Ver.1 ===")
    print(f"Data directory: {args.data_dir}")
    print(f"Sampling interval: {args.interval}s; BME680 addr: 0x{args.i2c_addr:02X}; MH-Z19 warmup: {args.warmup}s")

    # Initialize components
    bme = BME680Reader(i2c_addr=args.i2c_addr)
    mhz = MHZ19Reader(port="/dev/serial0", baudrate=9600, timeout=1.0, retries=3)
    logger = CSVLogger(base_dir=args.data_dir)

    bme_ok = False
    mhz_ok = False
    next_bme_retry = 0.0
    next_mhz_retry = 0.0
    bme_backoff = 1.0
    mhz_backoff = 1.0

    # Warmup for MH-Z19 if requested
    if args.warmup > 0:
        print(f"[INFO] Warming up MH-Z19 for {args.warmup:.0f}s...")
        t0 = time.time()
        while RUNNING and time.time() - t0 < args.warmup:
            time.sleep(0.5)

    sample_count = 0

    while RUNNING:
        loop_start = time.time()
        ts = dt.datetime.now()
        epoch = int(ts.timestamp())

        # Read BME680
        temp_c = rh = press_hpa = gas_ohm = None
        try:
            if not bme_ok and time.time() >= next_bme_retry:
                print("[INFO] (Re)initializing BME680...")
                bme.initialize()
                bme_ok = True
                bme_backoff = 1.0
            if bme_ok:
                res = bme.read(max_wait_s=2.0)
                if res is None:
                    raise RuntimeError("BME680 timeout")
                temp_c, rh, press_hpa, gas_ohm = res
        except Exception as e:
            print(f"[WARN] BME680 read failed: {e}")
            bme_ok = False
            next_bme_retry = time.time() + bme_backoff
            bme_backoff = min(bme_backoff * 2.0, 60.0)

        # Read MH-Z19
        co2_ppm: Optional[int] = None
        try:
            if not mhz_ok and time.time() >= next_mhz_retry:
                print("[INFO] (Re)opening MH-Z19 serial port...")
                mhz.open()
                mhz_ok = True
                mhz_backoff = 1.0
            if mhz_ok:
                co2 = mhz.read_co2()
                if co2 is None:
                    raise RuntimeError("MH-Z19 timeout/invalid")
                co2_ppm = int(co2)
        except Exception as e:
            print(f"[WARN] MH-Z19 read failed: {e}")
            mhz_ok = False
            try:
                mhz.close()
            except Exception:
                pass
            next_mhz_retry = time.time() + mhz_backoff
            mhz_backoff = min(mhz_backoff * 2.0, 60.0)

        # Analytics
        abs_h = absolute_humidity_gm3(temp_c, rh) if (temp_c is not None and rh is not None) else float("nan")
        di = discomfort_index(temp_c, rh) if (temp_c is not None and rh is not None) else float("nan")
        pol_idx, pol_lvl = pollution_index_from_gas(gas_ohm if gas_ohm is not None else -1.0)

        # Log to CSV
        row = {
            "timestamp_iso": ts.isoformat(timespec="seconds"),
            "timestamp_epoch": epoch,
            "temperature_c": round(temp_c, 3) if isinstance(temp_c, (int, float)) else "",
            "humidity_percent": round(rh, 3) if isinstance(rh, (int, float)) else "",
            "absolute_humidity_gm3": round(abs_h, 3) if isinstance(abs_h, (int, float)) else "",
            "pressure_hpa": round(press_hpa, 3) if isinstance(press_hpa, (int, float)) else "",
            "gas_resistance_ohm": round(gas_ohm, 1) if isinstance(gas_ohm, (int, float)) else "",
            "pollution_index": round(pol_idx, 1) if isinstance(pol_idx, (int, float)) else "",
            "pollution_level": pol_lvl,
            "co2_ppm": co2_ppm if isinstance(co2_ppm, int) else "",
            "discomfort_index": round(di, 2) if isinstance(di, (int, float)) else "",
            "bme680_ok": bme_ok,
            "mhz19_ok": mhz_ok,
        }
        try:
            logger.log(row)
        except Exception as e:
            print(f"[ERROR] CSV log failed: {e}")

        # Console output (every N samples)
        sample_count += 1
        if sample_count % max(1, int(args.print_every)) == 0:
            print(
                f"[{ts.strftime('%H:%M:%S')}] "
                f"T={row['temperature_c']}C RH={row['humidity_percent']}% AH={row['absolute_humidity_gm3']}g/m3 "
                f"P={row['pressure_hpa']}hPa Gas={row['gas_resistance_ohm']}Ω CO2={row['co2_ppm']}ppm "
                f"DI={row['discomfort_index']} AQI*={row['pollution_index']}({row['pollution_level']}) "
                f"BME={'OK' if bme_ok else 'NG'} MHZ={'OK' if mhz_ok else 'NG'}"
            )

        # Sleep for the remainder of interval
        elapsed = time.time() - loop_start
        to_sleep = max(0.0, args.interval - elapsed)
        # Allow signals to be processed
        end = time.time() + to_sleep
        while RUNNING and time.time() < end:
            time.sleep(min(0.2, end - time.time()))

    # Cleanup
    try:
        mhz.close()
    except Exception:
        pass
    try:
        bme.close()
    except Exception:
        pass
    print("[INFO] Stopped. Bye.")


if __name__ == "__main__":
    main()

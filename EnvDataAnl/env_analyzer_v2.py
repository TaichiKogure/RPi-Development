#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Environmental Data Analyzer Ver2 - Noise-aware smoothing and gap filling

Adds to Ver1:
- Time-aware interpolation to fill missing values per device/parameter
- Rolling smoothing (moving average) to reduce noise
- Noise quantification per sensor (residual rolling std / MAD)
- Smoothed time-series plots and noise-over-time plots
- Hourly/day-night noise statistics and unified multi-sensor graphs

Usage examples:
  python env_analyzer_v2.py --days 7 --tz Asia/Tokyo
  python env_analyzer_v2.py --smooth-window 15 --noise-window 60 --resample "1T"

Requirements:
  pip install pandas numpy matplotlib seaborn

Outputs under ./output_v2 (next to this script by default or under --data-dir):
  - timeseries_<param>_smoothed_v2.png
  - noise_timeseries_<param>_v2.png
  - unified_smoothed_panel_v2.png
  - noise_hourly_stats_v2.csv, noise_daynight_stats_v2.csv
  - completeness_after_interp_v2.csv
  - summary_v2.json
"""

import argparse
import os
import json
import math
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager, rcParams
import seaborn as sns

# Reuse font config from v1 if available; otherwise set simple JP-capable defaults

def _configure_matplotlib_fonts():
    candidates = [
        "Noto Sans CJK JP",
        "Noto Sans JP",
        "IPAexGothic",
        "IPAGothic",
        "Yu Gothic",
        "MS Gothic",
        "Meiryo",
    ]
    try:
        available = set(f.name for f in font_manager.fontManager.ttflist)
    except Exception:
        available = set()
    for name in candidates:
        if name in available:
            rcParams["font.family"] = name
            break
    rcParams["axes.unicode_minus"] = False

try:
    _configure_matplotlib_fonts()
except Exception:
    pass

EXPECTED_COLUMNS = [
    "timestamp", "device_id", "temperature", "humidity", "pressure", "gas_resistance", "co2",
]
DEVICE_IDS = ["P1", "P2", "P3", "P4"]

# -----------------------------
# IO helpers
# -----------------------------

def _ensure_output_dir(base_dir: str) -> str:
    out = os.path.join(base_dir, "output_v2")
    os.makedirs(out, exist_ok=True)
    return out

def _is_numeric_series(s: pd.Series) -> bool:
    return np.issubdtype(s.dtype, np.number)

def _parse_timestamp(series: pd.Series) -> pd.Series:
    if _is_numeric_series(series):
        return pd.to_datetime(series, unit="s", errors="coerce")
    s = pd.to_datetime(series.astype(str), errors="coerce")
    if s.isna().all():
        digits = series.astype(str).str.extract(r"(\d{10})")
        if 0 in digits.columns:
            s2 = pd.to_datetime(digits[0], unit="s", errors="coerce")
            return s2
    return s

def _infer_device_id_from_path(path: str) -> Optional[str]:
    base = os.path.basename(path).upper()
    for d in DEVICE_IDS:
        if base.startswith(d + "_") or base.startswith(d + " ") or base.startswith(d) or (d + "_FIXED") in base:
            return d
    return None

def _normalize_columns(df: pd.DataFrame, device_id: Optional[str]) -> pd.DataFrame:
    cols = {c.lower().strip(): c for c in df.columns}
    variants = {
        "timestamp": ["time", "ts", "日時", "時刻", "date", "datetime"],
        "device_id": ["device", "id", "node", "デバイス", "機器"],
        "temperature": ["temp", "temperature_c", "氣温", "気温", "temp_c"],
        "humidity": ["rh", "relative_humidity", "湿度"],
        "pressure": ["press", "atm", "気圧", "pressure_hpa"],
        "gas_resistance": ["gas", "gas_kohm", "gas_res", "gasres", "gas_ohm", "gas_resistance_ohm"],
        "co2": ["co2_ppm", "co2ppm", "co₂", "co2_concentration"],
    }
    rename_map: Dict[str, str] = {}
    lower_cols = [c.lower().strip() for c in df.columns]

    def find_col(target: str) -> Optional[str]:
        if target in lower_cols:
            return cols[target]
        for v in variants.get(target, []):
            if v in lower_cols:
                return cols[v]
        return None

    for key in variants:
        src = find_col(key)
        if src is not None and src != key:
            rename_map[src] = key

    df = df.rename(columns=rename_map)
    if "device_id" not in df.columns:
        df["device_id"] = device_id if device_id else "UNKNOWN"

    if "timestamp" in df.columns:
        df["timestamp"] = _parse_timestamp(df["timestamp"])  # may yield NaT
        df = df.dropna(subset=["timestamp"]).sort_values("timestamp")

    for mcol in ["temperature", "humidity", "pressure", "gas_resistance", "co2"]:
        if mcol in df.columns:
            df[mcol] = pd.to_numeric(df[mcol], errors="coerce")
    return df


def discover_csv_files(data_dir: str, limit_to: Optional[List[str]] = None) -> List[str]:
    if not os.path.isdir(data_dir):
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    files: List[str] = []
    for name in os.listdir(data_dir):
        if not name.lower().endswith('.csv'):
            continue
        up = name.upper()
        if any(up.startswith(f"{d}") for d in DEVICE_IDS):
            files.append(os.path.join(data_dir, name))
    files.sort()
    if limit_to:
        wanted = {os.path.basename(f).lower(): True for f in limit_to}
        files = [f for f in files if os.path.basename(f).lower() in wanted]
    return files


def load_and_merge(files: List[str]) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for f in files:
        try:
            dev = _infer_device_id_from_path(f)
            df = pd.read_csv(f)
            df = _normalize_columns(df, dev)
            frames.append(df)
        except Exception as e:
            print(f"[WARN] Failed to load {f}: {e}")
    if not frames:
        raise RuntimeError("No valid CSV files could be loaded.")
    return pd.concat(frames, ignore_index=True)

# -----------------------------
# Feature engineering
# -----------------------------

def add_time_features(df: pd.DataFrame, tz: Optional[str] = None) -> pd.DataFrame:
    ts = df["timestamp"]
    if tz:
        try:
            if ts.dt.tz is None:
                ts = ts.dt.tz_localize(tz)
            else:
                ts = ts.dt.tz_convert(tz)
        except Exception:
            pass
    df["date"] = ts.dt.date
    df["hour"] = ts.dt.hour
    df["dow"] = ts.dt.dayofweek
    df["is_daytime"] = ((df["hour"] >= 6) & (df["hour"] < 18)).astype(int)
    df["is_night"] = 1 - df["is_daytime"]
    return df

# -----------------------------
# Interpolation, smoothing and noise
# -----------------------------

def interpolate_and_smooth(df: pd.DataFrame, value_cols: List[str], resample: Optional[str], smooth_window: int, noise_window: int) -> pd.DataFrame:
    """Per device & per column:
    - set time index
    - optional resample (asfreq) to a uniform grid
    - interpolate(method='time', both directions)
    - rolling mean for smoothing
    - residual = value - smoothed
    - noise metric = rolling std of residual (or MAD fallback)
    """
    out_parts: List[pd.DataFrame] = []
    for dev, sub in df.groupby("device_id"):
        sub = sub.sort_values("timestamp").copy()
        sub = sub.set_index("timestamp")
        # Optional resample to a regular grid
        if resample:
            # We use mean within bin; keep other columns by forward fill
            sub = sub.groupby(pd.Grouper(freq=resample)).mean(numeric_only=True).join(
                sub[[c for c in sub.columns if c not in value_cols]].groupby(pd.Grouper(freq=resample)).last()
            )
        # Interpolate measurements time-wise
        for c in value_cols:
            if c in sub.columns:
                sub[c] = sub[c].interpolate(method='time', limit_direction='both')
        # Smoothing and noise
        for c in value_cols:
            if c in sub.columns:
                sm_name = f"{c}_smoothed"
                res_name = f"{c}_residual"
                nz_name = f"{c}_noise"
                sub[sm_name] = sub[c].rolling(window=smooth_window, min_periods=max(3, smooth_window//5)).mean()
                sub[res_name] = sub[c] - sub[sm_name]
                # Rolling std as primary noise
                nz = sub[res_name].rolling(window=noise_window, min_periods=max(3, noise_window//5)).std()
                # Fallback: MAD scaled to std (~1.4826)
                mad = sub[res_name].rolling(window=noise_window, min_periods=max(3, noise_window//5)).apply(
                    lambda x: np.median(np.abs(x - np.nanmedian(x))) if np.isfinite(x).any() else np.nan,
                    raw=False
                )
                sub[nz_name] = nz.fillna(1.4826 * mad)
        sub["device_id"] = dev
        sub = sub.reset_index()
        out_parts.append(sub)
    return pd.concat(out_parts, axis=0, ignore_index=True)

# -----------------------------
# Plotting
# -----------------------------

def save_lineplot(df: pd.DataFrame, x: str, y: str, hue: Optional[str], title: str, out_path: str):
    plt.figure(figsize=(12, 5))
    try:
        sns.lineplot(data=df, x=x, y=y, hue=hue, errorbar=None)
        plt.title(title)
        plt.tight_layout()
        plt.savefig(out_path)
    finally:
        plt.close()


def save_unified_panel(df: pd.DataFrame, params: List[str], out_path: str):
    import matplotlib.gridspec as gridspec
    n = len(params)
    rows = int(np.ceil(n / 2))
    cols = 2 if n > 1 else 1
    plt.figure(figsize=(14, 4 * rows))
    gs = gridspec.GridSpec(rows, cols)
    for i, p in enumerate(params):
        ax = plt.subplot(gs[i])
        y = f"{p}_smoothed" if f"{p}_smoothed" in df.columns else p
        sns.lineplot(ax=ax, data=df, x="timestamp", y=y, hue="device_id", errorbar=None)
        ax.set_title(f"Smoothed {p}")
        ax.legend(loc='best', fontsize=8)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()

# -----------------------------
# Statistics helpers
# -----------------------------

def compute_hourly_noise(df: pd.DataFrame, value_cols: List[str]) -> pd.DataFrame:
    noise_cols = [f"{c}_noise" for c in value_cols if f"{c}_noise" in df.columns]
    grp = df.groupby(["device_id", pd.Grouper(key="timestamp", freq="1H")])[noise_cols]
    agg = grp.mean().reset_index().rename(columns={"timestamp": "hour"})
    return agg


def compute_daynight_noise(df: pd.DataFrame, value_cols: List[str]) -> pd.DataFrame:
    noise_cols = [f"{c}_noise" for c in value_cols if f"{c}_noise" in df.columns]
    temp = df.copy()
    temp["hour"] = temp["timestamp"].dt.hour
    temp["is_daytime"] = ((temp["hour"] >= 6) & (temp["hour"] < 18)).astype(int)
    grp = temp.groupby(["device_id", "date", "is_daytime"])[noise_cols]
    agg = grp.mean().reset_index()
    return agg

# -----------------------------
# Main pipeline
# -----------------------------

def analyze_v2(data_dir: str, files: Optional[List[str]], days: int, tz: Optional[str], resample_freq: Optional[str], smooth_window: int, noise_window: int) -> Dict[str, str]:
    out_dir = _ensure_output_dir(data_dir)

    csvs = discover_csv_files(data_dir, limit_to=files)
    if not csvs:
        raise RuntimeError("No CSV files found. Expected names like P1_fixed.csv, P2_fixed 2.csv, etc.")

    df = load_and_merge(csvs)
    df = add_time_features(df, tz=tz)

    if days > 0:
        cutoff = pd.Timestamp.now(tz=None) - pd.Timedelta(days=days)
        df = df[df["timestamp"] >= cutoff]

    value_cols = [c for c in ["temperature", "humidity", "pressure", "gas_resistance", "co2"] if c in df.columns]

    # Interpolate + Smooth + Noise
    df2 = interpolate_and_smooth(df, value_cols, resample=resample_freq, smooth_window=smooth_window, noise_window=noise_window)

    # Outputs
    # 1) Smoothed timeseries per parameter
    for c in value_cols:
        y = f"{c}_smoothed" if f"{c}_smoothed" in df2.columns else c
        p_sm = os.path.join(out_dir, f"timeseries_{c}_smoothed_v2.png")
        save_lineplot(df2, x="timestamp", y=y, hue="device_id", title=f"Smoothed Time Series: {c}", out_path=p_sm)
        # Noise time-series
        nz = f"{c}_noise"
        if nz in df2.columns:
            p_nz = os.path.join(out_dir, f"noise_timeseries_{c}_v2.png")
            save_lineplot(df2, x="timestamp", y=nz, hue="device_id", title=f"Noise over Time: {c}", out_path=p_nz)

    # 2) Unified panel figure across parameters
    panel_params = value_cols
    panel_path = os.path.join(out_dir, "unified_smoothed_panel_v2.png")
    save_unified_panel(df2, params=panel_params, out_path=panel_path)

    # 3) Noise statistics CSVs
    hourly_noise = compute_hourly_noise(df2, value_cols)
    dn_noise = compute_daynight_noise(df2, value_cols)
    hourly_noise_path = os.path.join(out_dir, "noise_hourly_stats_v2.csv")
    dn_noise_path = os.path.join(out_dir, "noise_daynight_stats_v2.csv")
    hourly_noise.to_csv(hourly_noise_path, index=False)
    dn_noise.to_csv(dn_noise_path, index=False)

    # 4) Completeness after interpolation (ratio of non-NaN in smoothed series)
    comp_cols = [f"{c}_smoothed" for c in value_cols]
    comp_df = df2.groupby("device_id")[comp_cols].apply(lambda x: x.notna().mean()).reset_index()
    comp_path = os.path.join(out_dir, "completeness_after_interp_v2.csv")
    comp_df.to_csv(comp_path, index=False)

    # Summary
    summary = {
        "output_dir": out_dir,
        "figures": sorted([f for f in os.listdir(out_dir) if f.lower().endswith('.png')]),
        "tables": [
            os.path.basename(hourly_noise_path),
            os.path.basename(dn_noise_path),
            os.path.basename(comp_path),
        ],
        "devices": sorted(df2["device_id"].dropna().unique().tolist()),
        "value_columns": value_cols,
        "rows": int(len(df2)),
        "params": {
            "resample_freq": resample_freq,
            "smooth_window": smooth_window,
            "noise_window": noise_window,
            "days": days,
            "tz": tz,
        }
    }
    with open(os.path.join(out_dir, "summary_v2.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return {"output_dir": out_dir}

# -----------------------------
# CLI
# -----------------------------

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="4-sensor environmental data analyzer Ver2 (noise-aware)")
    p.add_argument("--data-dir", type=str, default=os.path.dirname(os.path.abspath(__file__)), help="Directory containing CSV files")
    p.add_argument("--files", nargs='*', help="Specific CSV filenames to analyze (found under data-dir)")
    p.add_argument("--days", type=int, default=7, help="Analyze last N days (0=all)")
    p.add_argument("--tz", type=str, default=None, help="Timezone name (e.g., Asia/Tokyo)")
    p.add_argument("--resample", type=str, default=None, help="Optional pandas offset alias (e.g., '1T', '5T') for uniform grid")
    p.add_argument("--smooth-window", type=int, default=15, help="Rolling window (samples) for smoothing")
    p.add_argument("--noise-window", type=int, default=60, help="Rolling window (samples) for noise metric")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None):
    args = parse_args(argv)
    result = analyze_v2(
        data_dir=args.data_dir,
        files=args.files,
        days=args.days,
        tz=args.tz,
        resample_freq=args.resample,
        smooth_window=args.smooth_window,
        noise_window=args.noise_window,
    )
    print("Ver2 analysis complete. Results saved to:", result["output_dir"])


if __name__ == "__main__":
    main()

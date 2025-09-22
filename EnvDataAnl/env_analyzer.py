#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Environmental Data Analyzer for 4-sensor system

- Scans EnvDataAnl directory for CSV files like P1_fixed*.csv, P2_fixed*.csv, etc.
- Loads and normalizes columns (timestamp, temperature, humidity, pressure, gas_resistance, co2)
- Handles both numeric (UNIX seconds) and string timestamps
- Produces: time-series plots, hourly profiles, day/night comparison, correlation matrix, rolling trends
- Outputs figures (PNG) and summary CSV/JSON into ./output

Usage examples (from repository root or from EnvDataAnl):
  python env_analyzer.py                     # default scan current folder
  python env_analyzer.py --data-dir G:\\RPi-Development\\EnvDataAnl --days 7
  python env_analyzer.py --files P1_fixed 2.csv P2_fixed 2.csv P3_fixed 2.csv P4_fixed.csv

Requirements (install in your virtual environment on Raspberry Pi or Windows):
  pip install pandas numpy matplotlib seaborn plotly

Note: The script avoids heavy dependencies and should work offline.
"""

import argparse
import os
import sys
import json
import math
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager, rcParams
import seaborn as sns

# -----------------------------
# Matplotlib font configuration for Japanese glyphs
# -----------------------------

def _configure_matplotlib_fonts():
    """
    Configure Matplotlib to use a Japanese-capable font if available to suppress
    missing glyph warnings when titles or labels include Japanese text.

    Tries common fonts in order of preference. Safe to call multiple times.
    """
    candidates = [
        "Noto Sans CJK JP",
        "Noto Sans CJK JP Regular",
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

    selected = None
    for name in candidates:
        if name in available:
            selected = name
            break

    if selected is None:
        # As a last resort, try to pick by filename patterns
        try:
            for fpath in font_manager.findSystemFonts(fontpaths=None, fontext='ttf'):
                lower = fpath.lower()
                if any(k in lower for k in ["noto", "ipa", "yugoth", "msgothic", "meiryo"]):
                    try:
                        fp = font_manager.FontProperties(fname=fpath)
                        selected = fp.get_name()
                        if selected:
                            break
                    except Exception:
                        continue
        except Exception:
            pass

    if selected:
        rcParams["font.family"] = selected
    # Ensure minus sign renders correctly with unicode fonts
    rcParams["axes.unicode_minus"] = False

# Apply configuration at import time; never crash if it fails
try:
    _configure_matplotlib_fonts()
except Exception:
    pass

# -----------------------------
# Utility helpers
# -----------------------------

EXPECTED_COLUMNS = [
    "timestamp", "device_id", "temperature", "humidity", "pressure", "gas_resistance", "co2",
    # optional extras: battery, adc, etc. are preserved but not required
]

DEVICE_IDS = ["P1", "P2", "P3", "P4"]


def _ensure_output_dir(base_dir: str) -> str:
    out = os.path.join(base_dir, "output")
    os.makedirs(out, exist_ok=True)
    return out


def _is_numeric_series(s: pd.Series) -> bool:
    return np.issubdtype(s.dtype, np.number)


def _parse_timestamp(series: pd.Series) -> pd.Series:
    """Parse timestamp column that may be numeric (unix seconds) or string.
    Returns pd.DatetimeIndex-like Series (dtype datetime64[ns]) with NaT for invalid rows.
    """
    if _is_numeric_series(series):
        return pd.to_datetime(series, unit="s", errors="coerce")
    # strings: try as-is, then fallback to int seconds embedded in string
    s = pd.to_datetime(series.astype(str), errors="coerce")
    if s.isna().all():
        # try to extract digits
        digits = series.astype(str).str.extract(r"(\d{10})")
        if 0 in digits.columns:
            s2 = pd.to_datetime(digits[0], unit="s", errors="coerce")
            return s2
    return s


def _normalize_columns(df: pd.DataFrame, device_id: Optional[str]) -> pd.DataFrame:
    """Rename various possible header variants to canonical names, keep extras."""
    cols = {c.lower().strip(): c for c in df.columns}

    # Create a mapping from common variants to canonical
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
        # exact
        if target in lower_cols:
            return cols[target]
        # variants
        for v in variants.get(target, []):
            if v in lower_cols:
                return cols[v]
        return None

    for key in variants:
        src = find_col(key)
        if src is not None and src != key:
            rename_map[src] = key

    # If device_id missing, fill with provided device_id or derive from filename if present in df.attrs
    df = df.rename(columns=rename_map)
    if "device_id" not in df.columns:
        if device_id:
            df["device_id"] = device_id
        else:
            df["device_id"] = "UNKNOWN"

    # Parse timestamp
    if "timestamp" in df.columns:
        df["timestamp"] = _parse_timestamp(df["timestamp"])  # may yield NaT
        df = df.dropna(subset=["timestamp"])  # remove invalid rows
        df = df.sort_values("timestamp")

    # Ensure numeric types for measurements
    for mcol in ["temperature", "humidity", "pressure", "gas_resistance", "co2"]:
        if mcol in df.columns:
            df[mcol] = pd.to_numeric(df[mcol], errors="coerce")

    return df


def _infer_device_id_from_path(path: str) -> Optional[str]:
    base = os.path.basename(path).upper()
    for d in DEVICE_IDS:
        if base.startswith(d + "_") or base.startswith(d + " ") or base.startswith(d) or (d + "_FIXED") in base:
            return d
    return None


# -----------------------------
# Core loading
# -----------------------------

def discover_csv_files(data_dir: str, limit_to: Optional[List[str]] = None) -> List[str]:
    """Find plausible sensor CSVs under data_dir.
    Typical names: P1_fixed.csv, P2_fixed 2.csv, P3_2025-09-01.csv, etc.
    """
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
        # normalize provided names to absolute paths if needed
        selected = []
        wanted = {os.path.basename(f).lower(): True for f in limit_to}
        for f in files:
            if os.path.basename(f).lower() in wanted:
                selected.append(f)
        files = selected

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
    all_df = pd.concat(frames, ignore_index=True)
    # Keep only expected/known plus extras
    return all_df


# -----------------------------
# Feature engineering
# -----------------------------

def add_time_features(df: pd.DataFrame, tz: Optional[str] = None) -> pd.DataFrame:
    # Assume local time; if tz given, localize/convert
    ts = df["timestamp"]
    if tz:
        try:
            # If naive, localize; if tz-aware, convert
            if ts.dt.tz is None:
                ts = ts.dt.tz_localize(tz)
            else:
                ts = ts.dt.tz_convert(tz)
        except Exception:
            pass
    df["date"] = ts.dt.date
    df["hour"] = ts.dt.hour
    df["dow"] = ts.dt.dayofweek  # 0=Mon
    df["is_daytime"] = ((df["hour"] >= 6) & (df["hour"] < 18)).astype(int)
    df["is_night"] = 1 - df["is_daytime"]
    return df


def compute_hourly_stats(df: pd.DataFrame, value_cols: List[str]) -> pd.DataFrame:
    grp = df.groupby(["device_id", "date", "hour"])[value_cols]
    agg = grp.agg(["count", "mean", "std", "min", "max"])
    agg.columns = ['_'.join(col).strip() for col in agg.columns.values]
    return agg.reset_index()


def compute_day_night_stats(df: pd.DataFrame, value_cols: List[str]) -> pd.DataFrame:
    grp = df.groupby(["device_id", "date", "is_daytime"])[value_cols]
    agg = grp.agg(["count", "mean", "std", "min", "max"])
    agg.columns = ['_'.join(col).strip() for col in agg.columns.values]
    return agg.reset_index()


def compute_correlations(df: pd.DataFrame, value_cols: List[str]) -> Dict[str, pd.DataFrame]:
    out: Dict[str, pd.DataFrame] = {}
    for dev, sub in df.groupby("device_id"):
        vc = [c for c in value_cols if c in sub.columns]
        if len(vc) >= 2:
            out[dev] = sub[vc].corr()
    return out


def rolling_trends(df: pd.DataFrame, value_cols: List[str], window: int = 30) -> pd.DataFrame:
    # Compute device-wise rolling means (window in samples)
    def _apply(sub: pd.DataFrame) -> pd.DataFrame:
        sub = sub.sort_values("timestamp").copy()
        for c in value_cols:
            if c in sub.columns:
                sub[f"{c}_rollmean_{window}"] = sub[c].rolling(window=window, min_periods=max(3, window//5)).mean()
        return sub
    # Avoid FutureWarning from pandas about groupby.apply on grouping columns
    parts = []
    for _, subdf in df.groupby('device_id', sort=False):
        parts.append(_apply(subdf))
    if parts:
        try:
            return pd.concat(parts, axis=0)
        except Exception:
            # Fallback to original dataframe if concatenation fails
            return df
    return df


def detect_outliers_zscore(df: pd.DataFrame, value_cols: List[str], z_thresh: float = 3.5) -> pd.DataFrame:
    out = df.copy()
    for c in value_cols:
        if c in out.columns:
            x = out[c]
            mu = x.mean(skipna=True)
            sd = x.std(skipna=True)
            if sd and not math.isclose(sd, 0.0):
                z = (x - mu) / sd
                out[f"{c}_is_outlier"] = (np.abs(z) > z_thresh).astype(int)
            else:
                out[f"{c}_is_outlier"] = 0
    return out


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


def save_histplot(df: pd.DataFrame, x: str, hue: Optional[str], title: str, out_path: str):
    """Save histogram with safe KDE handling.

    - Enables KDE only when there are at least 2 valid samples overall and
      for each hue category (if provided), to avoid scipy gaussian_kde errors.
    - If data is insufficient, saves a placeholder figure indicating data shortage.
    """
    plt.figure(figsize=(8, 5))
    try:
        # Prepare data and determine if KDE can be used safely
        cols = [x]
        if hue:
            cols.append(hue)
        data = df[cols].dropna()

        kde_ok = False
        if not data.empty:
            total_valid = data[x].notna().sum()
            if hue:
                counts = data.groupby(hue)[x].apply(lambda s: s.notna().sum())
                kde_ok = (total_valid >= 2) and (counts.min() >= 2 if len(counts) > 0 else False)
            else:
                kde_ok = total_valid >= 2

        if data.empty or data[x].dropna().empty:
            # Not enough data to plot
            plt.text(0.5, 0.5, "データが不足しています", ha='center', va='center', fontsize=12)
            plt.title(title)
            plt.axis('off')
        else:
            sns.histplot(data=data, x=x, hue=hue, kde=kde_ok, stat='density', common_norm=False)
            plt.title(title)
        plt.tight_layout()
        plt.savefig(out_path)
    finally:
        plt.close()


def save_corr_heatmap(corr: pd.DataFrame, title: str, out_path: str):
    plt.figure(figsize=(6, 5))
    try:
        sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', vmin=-1, vmax=1)
        plt.title(title)
        plt.tight_layout()
        plt.savefig(out_path)
    finally:
        plt.close()


# -----------------------------
# Main pipeline
# -----------------------------

def analyze(data_dir: str, files: Optional[List[str]], days: int, tz: Optional[str]) -> Dict[str, str]:
    out_dir = _ensure_output_dir(data_dir)

    csvs = discover_csv_files(data_dir, limit_to=files)
    if not csvs:
        raise RuntimeError("No CSV files found. Expected names like P1_fixed.csv, P2_fixed 2.csv, etc.")

    df = load_and_merge(csvs)
    df = add_time_features(df, tz=tz)

    # Trim last N days if requested
    if days > 0:
        cutoff = pd.Timestamp.now(tz=None) - pd.Timedelta(days=days)
        df = df[df["timestamp"] >= cutoff]

    # Figure out which measurement columns are present
    value_cols = [c for c in ["temperature", "humidity", "pressure", "gas_resistance", "co2"] if c in df.columns]

    # Basic completeness report
    completeness = df.groupby("device_id")[value_cols].apply(lambda x: x.notna().mean()).reset_index()
    completeness_path = os.path.join(out_dir, "completeness_by_device.csv")
    completeness.to_csv(completeness_path, index=False)

    # Hourly stats and day/night
    hourly = compute_hourly_stats(df, value_cols)
    dn = compute_day_night_stats(df, value_cols)
    hourly_path = os.path.join(out_dir, "hourly_stats.csv")
    dn_path = os.path.join(out_dir, "daynight_stats.csv")
    hourly.to_csv(hourly_path, index=False)
    dn.to_csv(dn_path, index=False)

    # Rolling trends and outliers
    df_trend = rolling_trends(df, value_cols, window=30)
    df_ol = detect_outliers_zscore(df_trend, value_cols)
    trends_path = os.path.join(out_dir, "rolling_trends_sample.csv")
    df_ol.head(2000).to_csv(trends_path, index=False)

    # Save per-parameter plots
    for c in value_cols:
        # time-series by device
        p1 = os.path.join(out_dir, f"timeseries_{c}.png")
        save_lineplot(df, x="timestamp", y=c, hue="device_id", title=f"Time Series: {c}", out_path=p1)
        # hourly mean profile
        prof = df.groupby(["device_id", "hour"])[c].mean().reset_index()
        p2 = os.path.join(out_dir, f"hourly_profile_{c}.png")
        save_lineplot(prof, x="hour", y=c, hue="device_id", title=f"Hourly Profile: {c}", out_path=p2)
        # day vs night distribution
        dd = df.copy()
        dd["period"] = np.where(dd["is_daytime"] == 1, "day", "night")
        p3 = os.path.join(out_dir, f"daynight_hist_{c}.png")
        save_histplot(dd, x=c, hue="period", title=f"Day vs Night: {c}", out_path=p3)

    # Correlations per device
    corrs = compute_correlations(df, value_cols)
    for dev, cmat in corrs.items():
        cp = os.path.join(out_dir, f"corr_{dev}.png")
        save_corr_heatmap(cmat, title=f"Correlation ({dev})", out_path=cp)

    # Summary JSON (paths)
    summary = {
        "output_dir": out_dir,
        "figures": sorted([f for f in os.listdir(out_dir) if f.lower().endswith('.png')]),
        "tables": [os.path.basename(completeness_path), os.path.basename(hourly_path), os.path.basename(dn_path), os.path.basename(trends_path)],
        "devices": sorted(df["device_id"].unique().tolist()),
        "value_columns": value_cols,
        "rows": int(len(df)),
        "time_span": {
            "min": df["timestamp"].min().isoformat() if not df.empty else None,
            "max": df["timestamp"].max().isoformat() if not df.empty else None,
        }
    }
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return {"output_dir": out_dir}


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="4-sensor environmental data analyzer")
    p.add_argument("--data-dir", type=str, default=os.path.dirname(os.path.abspath(__file__)), help="Directory containing CSV files")
    p.add_argument("--files", nargs='*', help="Specific CSV filenames to analyze (found under data-dir)")
    p.add_argument("--days", type=int, default=7, help="Analyze last N days (0=all)")
    p.add_argument("--tz", type=str, default=None, help="Timezone name (e.g., Asia/Tokyo)")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None):
    args = parse_args(argv)
    result = analyze(args.data_dir, args.files, args.days, tz=args.tz)
    print("Analysis complete. Results saved to:", result["output_dir"])


if __name__ == "__main__":
    main()

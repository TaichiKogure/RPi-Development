# Office Environmental Data Heatmap Focus Ver3 (OffceAnalysisVer3)
#
# - Purpose: Produce detailed date×hour heatmaps per device (P1/P2/P3) for each parameter.
# - Inputs (default directory): G:\\RPi-Development\\EnvDataAnl\\OfficeENVData
#   Expected filenames (same as Ver1/Ver2):
#     P1_fixed Office.csv, P2_fixed Office.csv, P3_fixed Office.csv
# - Outputs: PNG heatmaps saved under OffceAnalysisVer3/output
# - Features:
#   * Robust timestamp parsing (UNIX seconds or string) and numeric coercion
#   * Absolute humidity auto-computation if missing
#   * Optional day-range filtering (e.g., last 30 days)
#   * For each device and parameter: pivot date (Y) × hour (X) mean values; fine y-ticks
#   * Dynamic figure height based on number of dates; small fonts
#   * CLI options for base dir, parameters, colormap, vmin/vmax, days, dpi
#
# Usage (PowerShell):
#   cd G:\\RPi-Development\\EnvDataAnl\\OfficeENVData\\OffceAnalysisVer3
#   python office_analysis_v3.py
#   # optional
#   python office_analysis_v3.py --days 30 --params temperature absolute_humidity co2 --cmap "turbo"
#
import os
import json
import argparse
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

DEFAULT_BASE_DIR = os.path.join("G:\\RPi-Development", "EnvDataAnl", "OfficeENVData")
OUTPUT_DIR_NAME = "output"

DEVICE_FILES = {
    "P1": "P1_fixed Office.csv",
    "P2": "P2_fixed Office.csv",
    "P3": "P3_fixed Office.csv",
}

# Standard parameter names we support
ALL_PARAMS = [
    "temperature",
    "absolute_humidity",
    "humidity",
    "co2",
    "pressure",
    "gas_resistance",
]

sns.set(style="whitegrid")


def ensure_output(base_dir: str) -> str:
    out_dir = os.path.join(base_dir, "OffceAnalysisVer3", OUTPUT_DIR_NAME)
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def _parse_timestamp(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_datetime(series, unit="s", errors="coerce")
    return pd.to_datetime(series.astype(str), errors="coerce")


def _find_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    low = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in low:
            return low[cand.lower()]
    return None


def _normalize_df(df: pd.DataFrame, device_id: str) -> pd.DataFrame:
    df = df.copy()
    ts_col = _find_col(df, ["timestamp", "time", "date", "日時", "時刻"]) or df.columns[0]
    df.rename(columns={ts_col: "timestamp"}, inplace=True)

    mapping_candidates = {
        "temperature": ["temperature", "temp", "氣温", "気温", "温度"],
        "humidity": ["humidity", "湿度"],
        "pressure": ["pressure", "press", "気圧"],
        "gas_resistance": ["gas_resistance", "gas", "gas_res", "gasr"],
        "co2": ["co2", "co2ppm", "co2_ppm", "co₂"],
        "absolute_humidity": ["absolute_humidity", "abs_hum", "abs_humidity", "絶対湿度"],
    }
    ren = {}
    for std, cands in mapping_candidates.items():
        col = _find_col(df, cands)
        if col:
            ren[col] = std
    if ren:
        df.rename(columns=ren, inplace=True)

    df["timestamp"] = _parse_timestamp(df["timestamp"]) 

    # Coerce numeric
    for col in set(ALL_PARAMS):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["device_id"] = device_id
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp")
    return df


def _compute_absolute_humidity_if_needed(df: pd.DataFrame) -> pd.DataFrame:
    # Compute absolute humidity [g/m^3] from T [C] and RH [%]
    if "absolute_humidity" not in df.columns:
        df["absolute_humidity"] = np.nan
    need = df["absolute_humidity"].isna()
    if ("temperature" in df.columns) and ("humidity" in df.columns):
        T = df.loc[need, "temperature"]
        RH = df.loc[need, "humidity"]
        # Magnus formula for saturation vapor pressure (hPa)
        es = 6.112 * np.exp((17.67 * T) / (T + 243.5))
        # actual vapor pressure (hPa)
        e = RH / 100.0 * es
        # convert to absolute humidity (g/m^3)
        # AH = 2.1674 * e / (T + 273.15)
        AH = 2.1674 * e / (T + 273.15)
        df.loc[need, "absolute_humidity"] = AH
    return df


def load_office_frames(base_dir: str, limit_days: Optional[int] = None) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for dev, fname in DEVICE_FILES.items():
        fpath = os.path.join(base_dir, fname)
        if not os.path.isfile(fpath):
            print(f"[WARN] Missing file for {dev}: {fpath}")
            continue
        try:
            raw = pd.read_csv(fpath)
            df = _normalize_df(raw, dev)
            df = _compute_absolute_humidity_if_needed(df)
            if limit_days and not df.empty:
                cutoff = pd.Timestamp.now() - pd.Timedelta(days=limit_days)
                df = df[df["timestamp"] >= cutoff]
            frames.append(df)
        except Exception as e:
            print(f"[WARN] Failed to load {fpath}: {e}")
    if not frames:
        raise RuntimeError("No input files could be loaded.")
    all_df = pd.concat(frames, ignore_index=True)
    return all_df


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["date"] = out["timestamp"].dt.date
    out["hour"] = out["timestamp"].dt.hour
    return out


def _dynamic_figsize(n_dates: int, base_w: float = 14.0) -> Tuple[float, float]:
    # Height scales with number of dates to keep rows readable
    h = max(6.0, min(0.22 * n_dates, 36.0))  # cap height to avoid extreme sizes
    return base_w, h


def plot_date_hour_heatmap(sub: pd.DataFrame, value_col: str, device_id: str, out_dir: str,
                           cmap: str = "viridis", vmin: Optional[float] = None, vmax: Optional[float] = None,
                           dpi: int = 150) -> Optional[str]:
    # Aggregate to mean per (date, hour)
    g = sub.groupby(["date", "hour"], as_index=False)[value_col].mean()
    # Pivot: index=date (Y), columns=hour (X)
    pv = g.pivot(index="date", columns="hour", values=value_col).sort_index()
    if pv.empty:
        return None

    # Prepare figure with dynamic height
    w, h = _dynamic_figsize(pv.shape[0])
    plt.figure(figsize=(w, h), dpi=dpi)
    try:
        ax = sns.heatmap(
            pv,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            cbar=True,
            linewidths=0.0,
            linecolor=None,
            square=False,
        )
        ax.set_title(f"{device_id} - {value_col} (Date × Hour)")
        ax.set_xlabel("Hour of Day")
        ax.set_ylabel("Date")
        # Improve tick label fonts for dense dates
        ax.set_xticklabels(ax.get_xticklabels(), rotation=0, fontsize=9)
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=6)
        plt.tight_layout()

        fname = f"heatmap_{value_col}_date_hour_{device_id}_v3.png"
        out_path = os.path.join(out_dir, fname)
        plt.savefig(out_path)
        return out_path
    finally:
        plt.close()


def run_ver3(base_dir: str,
             days: Optional[int] = None,
             params: Optional[List[str]] = None,
             cmap: str = "viridis",
             vmin: Optional[float] = None,
             vmax: Optional[float] = None,
             dpi: int = 150) -> Dict:
    out_dir = ensure_output(base_dir)

    df = load_office_frames(base_dir, limit_days=days)
    df = add_time_features(df)

    # Determine parameters to plot
    if params:
        plot_params = [p for p in params if p in ALL_PARAMS]
    else:
        # default: plot all available among ALL_PARAMS
        plot_params = [p for p in ALL_PARAMS if p in df.columns]

    results: Dict[str, Dict[str, Optional[str]]] = {}
    for dev, sub in df.groupby("device_id"):
        results[dev] = {}
        for p in plot_params:
            if p not in sub.columns:
                results[dev][p] = None
                continue
            out_path = plot_date_hour_heatmap(sub[["date", "hour", p]].dropna(), p, dev, out_dir,
                                              cmap=cmap, vmin=vmin, vmax=vmax, dpi=dpi)
            results[dev][p] = out_path

    # Save a summary JSON
    summary = {
        "base_dir": base_dir,
        "output_dir": out_dir,
        "devices": sorted(df["device_id"].unique().tolist()),
        "params": plot_params,
        "days_limit": days,
        "figures": results,
    }
    with open(os.path.join(out_dir, "summary_ver3.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"Ver3 heatmaps complete. Outputs in: {out_dir}")
    return summary


def parse_args():
    p = argparse.ArgumentParser(description="Office ENV Detailed Heatmaps Ver3")
    p.add_argument("--base-dir", type=str, default=DEFAULT_BASE_DIR, help="Directory holding Office CSV files")
    p.add_argument("--days", type=int, default=None, help="Limit to last N days")
    p.add_argument("--params", type=str, nargs="*", default=None, help=f"Parameters to plot from {ALL_PARAMS}")
    p.add_argument("--cmap", type=str, default="viridis", help="Matplotlib colormap name (e.g., viridis, magma, turbo)")
    p.add_argument("--vmin", type=float, default=None, help="Color scale minimum (optional)")
    p.add_argument("--vmax", type=float, default=None, help="Color scale maximum (optional)")
    p.add_argument("--dpi", type=int, default=150, help="Figure DPI")
    return p.parse_args()


def main():
    args = parse_args()
    run_ver3(
        base_dir=args.base_dir,
        days=args.days,
        params=args.params,
        cmap=args.cmap,
        vmin=args.vmin,
        vmax=args.vmax,
        dpi=args.dpi,
    )


if __name__ == "__main__":
    main()

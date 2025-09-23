# Office Occupancy Heatmap from CO2 (Ver4 add-on)
#
# Purpose
# - Based on Ver4 event detection and occupancy estimation, build date×hour heatmaps of
#   estimated people for P2 (capacity ~8) and P3 (capacity ~30).
# - Y-axis: date, X-axis: hour(0-23), Color: estimated number of people.
# - Correct occupancy by peak height and event duration (rise time) beyond simple slope-only estimation.
#
# Inputs (same base directory as other versions):
#   G:\\RPi-Development\\EnvDataAnl\\OfficeENVData
#   Files: P2_fixed Office.csv, P3_fixed Office.csv (P1 is ignored by default)
#
# Outputs (under OffceAnalysisVer4/output):
#   - occupancy_pivot_mean_P2_v4.csv, occupancy_pivot_mean_P3_v4.csv
#   - occupancy_pivot_max_P2_v4.csv,  occupancy_pivot_max_P3_v4.csv
#   - heatmap_occupancy_mean_P2_v4.png, heatmap_occupancy_mean_P3_v4.png
#   - heatmap_occupancy_max_P2_v4.png,  heatmap_occupancy_max_P3_v4.png
#   - summary_occupancy_heatmap_v4.json
#
# Usage (PowerShell):
#   cd G:\\RPi-Development\\EnvDataAnl\\OfficeENVData\\OffceAnalysisVer4
#   python office_occupancy_heatmap_v4.py
#   # options
#   python office_occupancy_heatmap_v4.py --days 120 --start-th 750 --end-th 680 --min-slope 2.0 \
#       --smooth 5 --p2-volume 120 --p3-volume 250 --ach 1.5 --q-per-person 0.004 --method mean
#
# Notes
# - This script reuses helper functions from office_analysis_v4.py. To avoid import path issues,
#   it will try to import them; if that fails, it falls back to local minimal implementations.

import os
import json
import argparse
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

matplotlib.use('Agg')
sns.set(style="whitegrid")

DEFAULT_BASE_DIR = os.path.join("G:\\RPi-Development", "EnvDataAnl", "OfficeENVData")
OUTPUT_DIR_NAME = "output"

# -----------------------------
# Try to reuse Ver4 helpers
# -----------------------------

try:
    from office_analysis_v4 import (
        ensure_output as v4_ensure_output,
        normalize_df as v4_normalize_df,
        load_frames as v4_load_frames,
        add_time_features as v4_add_time_features,
        smooth_series as v4_smooth_series,
        compute_slope as v4_compute_slope,
        detect_events as v4_detect_events,
        characterize_events as v4_characterize_events,
        CAPACITY as V4_CAPACITY,
    )
    HAVE_V4 = True
except Exception:
    HAVE_V4 = False

# -----------------------------
# Local fallbacks (minimal compatible subset)
# -----------------------------

def ensure_output(base_dir: str) -> str:
    out_dir = os.path.join(base_dir, OUTPUT_DIR_NAME)
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def _find_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    low = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in low:
            return low[cand.lower()]
    return None


def parse_timestamp(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_datetime(series, unit='s', errors='coerce')
    return pd.to_datetime(series.astype(str), errors='coerce')


def normalize_df(df: pd.DataFrame, device_id: str) -> pd.DataFrame:
    ts_col = _find_col(df, ["timestamp", "time", "date", "日時", "時刻"]) or df.columns[0]
    df = df.copy()
    df.rename(columns={ts_col: "timestamp"}, inplace=True)
    mapping = {
        "temperature": ["temperature", "temp", "氣温", "気温", "温度"],
        "humidity": ["humidity", "湿度"],
        "pressure": ["pressure", "press", "気圧"],
        "gas_resistance": ["gas_resistance", "gas", "gas_res", "gasr"],
        "co2": ["co2", "co2ppm", "co2_ppm", "co₂"],
        "absolute_humidity": ["absolute_humidity", "abs_hum", "abs_humidity", "絶対湿度"],
    }
    ren = {}
    for std, cands in mapping.items():
        col = _find_col(df, cands)
        if col:
            ren[col] = std
    if ren:
        df.rename(columns=ren, inplace=True)

    df["timestamp"] = parse_timestamp(df["timestamp"])  # NaT on failure
    for c in ["co2"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    df["device_id"] = device_id
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp")
    keep = [c for c in ["timestamp", "device_id", "co2"] if c in df.columns]
    return df[keep]


def load_frames(base_dir: str, files: Dict[str, str], limit_days: Optional[int] = None) -> pd.DataFrame:
    frames = []
    for dev, fname in files.items():
        fpath = os.path.join(base_dir, fname)
        if not os.path.isfile(fpath):
            print(f"[WARN] Missing file for {dev}: {fpath}")
            continue
        try:
            raw = pd.read_csv(fpath)
            df = (v4_normalize_df(raw, dev) if HAVE_V4 else normalize_df(raw, dev))
            if limit_days and not df.empty:
                cutoff = pd.Timestamp.now() - pd.Timedelta(days=limit_days)
                df = df[df["timestamp"] >= cutoff]
            frames.append(df)
        except Exception as e:
            print(f"[WARN] Failed to load {fpath}: {e}")
    if not frames:
        raise RuntimeError("No input files could be loaded.")
    return pd.concat(frames, ignore_index=True)


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["date"] = out["timestamp"].dt.date
    out["hour"] = out["timestamp"].dt.hour
    return out


def smooth_series(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window=window, min_periods=max(3, window//2)).median()


def compute_slope(sub: pd.DataFrame, smooth: int) -> pd.DataFrame:
    df = sub.sort_values("timestamp").copy()
    df["co2_smooth"] = smooth_series(df["co2"], window=max(3, smooth))
    dt_min = df["timestamp"].diff().dt.total_seconds() / 60.0
    dppm = df["co2_smooth"].diff()
    df["slope_ppm_per_min"] = dppm / dt_min
    return df


def detect_events(sub: pd.DataFrame,
                  start_th: float,
                  end_th: float,
                  min_slope: float,
                  min_duration_min: float = 5.0,
                  gap_close_min: float = 10.0) -> pd.DataFrame:
    if sub.empty or "co2" not in sub.columns:
        return pd.DataFrame(columns=["start", "end", "peak_time", "peak_co2", "start_co2", "end_co2"]).astype({})
    df = sub.copy()
    df["above_start"] = df["co2_smooth"] >= start_th
    df["below_end"] = df["co2_smooth"] <= end_th
    df["is_rising"] = df["slope_ppm_per_min"] >= min_slope
    df["is_falling"] = df["slope_ppm_per_min"] <= -min_slope
    events: List[Tuple[int, int]] = []
    start_idx: Optional[int] = None
    for i in range(len(df)):
        row = df.iloc[i]
        if start_idx is None:
            if row["above_start"] or row["is_rising"]:
                start_idx = i
        else:
            if row["below_end"] or row["is_falling"]:
                events.append((start_idx, i))
                start_idx = None
    if start_idx is not None:
        events.append((start_idx, len(df)-1))
    merged: List[Tuple[int, int]] = []
    for s, e in events:
        if not merged:
            merged.append((s, e))
        else:
            gap_sec = (df.iloc[s]["timestamp"] - df.iloc[merged[-1][1]]["timestamp"]).total_seconds()
            if gap_sec <= gap_close_min * 60:
                merged[-1] = (merged[-1][0], e)
            else:
                merged.append((s, e))
    rows: List[Dict] = []
    for s, e in merged:
        t_start = df.iloc[s]["timestamp"]
        t_end = df.iloc[e]["timestamp"]
        dur_min = (t_end - t_start).total_seconds() / 60.0
        if dur_min < min_duration_min:
            continue
        seg = df.iloc[s:e+1]
        peak_idx = seg["co2_smooth"].idxmax()
        peak_time = df.loc[peak_idx, "timestamp"]
        peak_val = float(df.loc[peak_idx, "co2_smooth"])
        rows.append({
            "start": t_start,
            "end": t_end,
            "duration_min": dur_min,
            "peak_time": peak_time,
            "peak_co2": peak_val,
            "start_co2": float(seg["co2_smooth"].iloc[0]),
            "end_co2": float(seg["co2_smooth"].iloc[-1]),
        })
    return pd.DataFrame(rows)


# -----------------------------
# Occupancy correction & assignment
# -----------------------------

CAPACITY = V4_CAPACITY if HAVE_V4 else {"P2": 8, "P3": 30}


def _baseline_estimated_people(sub_with_slope: pd.DataFrame,
                               events: pd.DataFrame,
                               device_id: str,
                               vol_m3: float,
                               q_per_person: float,
                               ach: float,
                               calib_high_pct: float = 0.95) -> pd.DataFrame:
    """Compute per-event baseline occupancy from slope using both mass-balance and heuristic,
    then return event table with columns: est_base, rise_rate_ppm_min, rise_time_min, peak_delta_ppm.
    """
    # reference slope from distribution
    ref = float(np.nanpercentile(
        sub_with_slope["slope_ppm_per_min"].replace([np.inf, -np.inf], np.nan).dropna(),
        calib_high_pct*100
    )) if sub_with_slope["slope_ppm_per_min"].notna().any() else 10.0

    rows = []
    for _, ev in events.iterrows():
        seg = sub_with_slope[(sub_with_slope["timestamp"] >= ev["start"]) & (sub_with_slope["timestamp"] <= ev["peak_time"])].copy()
        if seg.empty:
            continue
        dppm = float(seg["co2_smooth"].iloc[-1] - seg["co2_smooth"].iloc[0])
        dtm = (seg["timestamp"].iloc[-1] - seg["timestamp"].iloc[0]).total_seconds() / 60.0
        slope = dppm / dtm if dtm > 0 else 0.0
        # mass-balance
        n_mass = 0.0
        if slope > 0 and vol_m3 > 0 and q_per_person > 0:
            corr = 1.0 / (1.0 + max(0.0, ach) / 2.0)
            g = slope * vol_m3 / 1e6 * corr
            n_mass = g / q_per_person
        # heuristic scaled to capacity at ref slope
        cap = CAPACITY.get(device_id, 10)
        n_heur = cap * (slope / (ref if ref > 0 else 10.0))
        n_base = 0.6 * n_mass + 0.4 * n_heur
        rows.append({
            **ev.to_dict(),
            "rise_time_min": dtm,
            "rise_rate_ppm_min": slope,
            "peak_delta_ppm": float(ev["peak_co2"] - ev["start_co2"]),
            "est_base": float(np.clip(n_base, 0, cap)),
            "device_id": device_id,
        })
    return pd.DataFrame(rows)


def _apply_peak_duration_correction(ev_row: pd.Series, capacity: int) -> float:
    """Apply peak-height and duration corrections to base occupancy.
    - Peak correction: higher (peak - start) raises estimate up to +50%
    - Duration correction: very short rise implies steeper influx -> up to +30%;
      very long slow rise reduces up to -30%.
    """
    base = float(ev_row.get("est_base", 0.0))
    delta = float(ev_row.get("peak_delta_ppm", 0.0))
    dur = float(ev_row.get("rise_time_min", 0.0))
    # Peak height correction: scale per ~400 ppm blocks (rough heuristic)
    peak_corr = 1.0 + np.clip(delta / 400.0, -0.3, 0.5)  # -30% .. +50%
    # Duration correction: reference 20 minutes rise
    if dur <= 0:
        dur = 1.0
    dur_corr = np.clip(20.0 / dur, 0.7, 1.3)  # 0.7x .. 1.3x
    est = base * peak_corr * dur_corr
    return float(np.clip(est, 0.0, capacity))


def _assign_event_to_timeseries(ev: pd.Series) -> pd.DataFrame:
    """Expand an event into per-minute rows with corrected occupancy value."""
    t0 = pd.to_datetime(ev["start"])  # ensure Timestamp
    t1 = pd.to_datetime(ev["end"]) if "end" in ev else pd.to_datetime(ev["peak_time"])  # fallback
    if pd.isna(t0) or pd.isna(t1) or t1 <= t0:
        return pd.DataFrame(columns=["timestamp", "occupancy_est"])
    idx = pd.date_range(t0, t1, freq="1min")
    return pd.DataFrame({
        "timestamp": idx,
        "occupancy_est": ev["est_corrected"]
    })


def build_occupancy_series(sub_with_slope: pd.DataFrame,
                           events: pd.DataFrame,
                           device_id: str,
                           volume_m3: float,
                           q_per_person: float,
                           ach: float) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame(columns=["timestamp", "device_id", "occupancy_est"]) 
    base_ev = _baseline_estimated_people(sub_with_slope, events, device_id, volume_m3, q_per_person, ach)
    cap = CAPACITY.get(device_id, 10)
    base_ev["est_corrected"] = base_ev.apply(lambda r: _apply_peak_duration_correction(r, cap), axis=1)

    # Assign to time series per minute and combine
    parts = []
    for _, row in base_ev.iterrows():
        ts = _assign_event_to_timeseries(row)
        if not ts.empty:
            parts.append(ts)
    if not parts:
        return pd.DataFrame(columns=["timestamp", "device_id", "occupancy_est"]) 
    occ = pd.concat(parts, ignore_index=True)
    occ["device_id"] = device_id
    return occ


# -----------------------------
# Heatmap helpers
# -----------------------------

def _dynamic_figsize(n_dates: int, base_w: float = 14.0) -> Tuple[float, float]:
    h = max(6.0, min(0.22 * n_dates, 36.0))
    return base_w, h


def plot_heatmap(pivot: pd.DataFrame, title: str, out_path: str, cmap: str = "magma", vmin: Optional[float] = 0.0, vmax: Optional[float] = None, dpi: int = 150):
    if pivot.empty:
        return
    w, h = _dynamic_figsize(pivot.shape[0])
    plt.figure(figsize=(w, h), dpi=dpi)
    try:
        ax = sns.heatmap(pivot, cmap=cmap, vmin=vmin, vmax=vmax, cbar=True)
        ax.set_title(title)
        ax.set_xlabel("Hour of Day")
        ax.set_ylabel("Date")
        ax.set_xticklabels(ax.get_xticklabels(), rotation=0, fontsize=9)
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=6)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        plt.tight_layout()
        plt.savefig(out_path)
    finally:
        plt.close()


# -----------------------------
# Main
# -----------------------------

DEVICE_FILES = {"P2": "P2_fixed Office.csv", "P3": "P3_fixed Office.csv"}


def run(base_dir: str,
        days: Optional[int],
        start_th: float,
        end_th: float,
        min_slope: float,
        smooth: int,
        p2_volume: float,
        p3_volume: float,
        ach: float,
        q_per_person: float,
        method: str = "mean",
        cmap: str = "magma",
        dpi: int = 150) -> Dict:

    out_dir = (v4_ensure_output(base_dir) if HAVE_V4 else ensure_output(base_dir))

    # Load P2/P3 only
    df = load_frames(base_dir, DEVICE_FILES, limit_days=days)

    # For each device, smooth, slope, events, occupancy series
    results = {}
    occ_all = []
    for dev, sub in df.groupby("device_id"):
        if dev not in ("P2", "P3"):
            continue
        # smooth + slope
        sub2 = (v4_compute_slope(sub, smooth=smooth) if HAVE_V4 else compute_slope(sub, smooth=smooth))
        # detect events
        ev = (v4_detect_events(sub2, start_th=start_th, end_th=end_th, min_slope=min_slope)
              if HAVE_V4 else detect_events(sub2, start_th=start_th, end_th=end_th, min_slope=min_slope))
        # build occupancy series
        vol = p2_volume if dev == "P2" else p3_volume
        occ = build_occupancy_series(sub2, ev, dev, volume_m3=vol, q_per_person=q_per_person, ach=ach)
        occ_all.append(occ)
        results[dev] = {
            "events": int(len(ev)),
            "occupancy_points": int(len(occ))
        }

    if not occ_all:
        raise RuntimeError("No occupancy could be computed (no events found).")

    occ_df = pd.concat(occ_all, ignore_index=True)
    # Aggregate to date×hour
    occ_df["date"] = occ_df["timestamp"].dt.date
    occ_df["hour"] = occ_df["timestamp"].dt.hour

    pivots: Dict[str, Dict[str, str]] = {}
    for dev, sub in occ_df.groupby("device_id"):
        agg = sub.groupby(["date", "hour"], as_index=False)["occupancy_est"].agg(["mean", "max"])\
                 .reset_index().rename(columns={"mean": "occ_mean", "max": "occ_max"})
        # mean pivot
        pv_mean = agg.pivot(index="date", columns="hour", values="occ_mean").sort_index()
        # max pivot
        pv_max = agg.pivot(index="date", columns="hour", values="occ_max").sort_index()
        # Save CSVs
        csv_mean = os.path.join(out_dir, f"occupancy_pivot_mean_{dev}_v4.csv")
        csv_max = os.path.join(out_dir, f"occupancy_pivot_max_{dev}_v4.csv")
        pv_mean.to_csv(csv_mean, encoding="utf-8-sig")
        pv_max.to_csv(csv_max, encoding="utf-8-sig")
        pivots[dev] = {"mean_csv": csv_mean, "max_csv": csv_max}
        # Plot
        vmax_auto = CAPACITY.get(dev, 10)
        plot_heatmap(pv_mean, f"{dev} Occupancy (mean) Date×Hour", os.path.join(out_dir, f"heatmap_occupancy_mean_{dev}_v4.png"), cmap=cmap, vmin=0.0, vmax=vmax_auto, dpi=dpi)
        plot_heatmap(pv_max, f"{dev} Occupancy (max) Date×Hour", os.path.join(out_dir, f"heatmap_occupancy_max_{dev}_v4.png"), cmap=cmap, vmin=0.0, vmax=vmax_auto, dpi=dpi)

    # Summary JSON
    summary = {
        "base_dir": base_dir,
        "output_dir": out_dir,
        "days_limit": days,
        "thresholds": {"start_th": start_th, "end_th": end_th, "min_slope": min_slope},
        "smooth": smooth,
        "volumes": {"P2": p2_volume, "P3": p3_volume},
        "ach": ach,
        "q_per_person_m3_min": q_per_person,
        "aggregation": method,
        "capacity": CAPACITY,
        "pivots": pivots,
        "devices": results,
    }
    with open(os.path.join(out_dir, "summary_occupancy_heatmap_v4.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)

    print(f"Occupancy heatmaps generated. Outputs in: {out_dir}")
    return summary


def parse_args():
    p = argparse.ArgumentParser(description="Occupancy Heatmaps from CO2 (Ver4 add-on)")
    p.add_argument("--base-dir", type=str, default=DEFAULT_BASE_DIR, help="Directory holding Office CSV files")
    p.add_argument("--days", type=int, default=None, help="Limit to last N days")
    p.add_argument("--start-th", type=float, default=750.0, help="CO2 start threshold (ppm)")
    p.add_argument("--end-th", type=float, default=680.0, help="CO2 end threshold (ppm)")
    p.add_argument("--min-slope", type=float, default=2.0, help="Min slope (ppm/min) for event detection")
    p.add_argument("--smooth", type=int, default=5, help="Median window for CO2 smoothing (samples)")
    p.add_argument("--p2-volume", type=float, default=120.0, help="P2 room volume (m^3)")
    p.add_argument("--p3-volume", type=float, default=250.0, help="P3 room volume (m^3)")
    p.add_argument("--ach", type=float, default=1.5, help="Air changes per hour (ACH) assumption")
    p.add_argument("--q-per-person", type=float, default=0.004, help="CO2 generation per person (m^3/min) ~ 0.004 = 4 L/min")
    p.add_argument("--method", type=str, default="mean", choices=["mean", "max"], help="Aggregation for color; both are saved, this selects default view only")
    p.add_argument("--cmap", type=str, default="magma", help="Matplotlib colormap name")
    p.add_argument("--dpi", type=int, default=150, help="Figure DPI")
    return p.parse_args()


def main():
    args = parse_args()
    run(
        base_dir=args.base_dir,
        days=args.days,
        start_th=args.start_th,
        end_th=args.end_th,
        min_slope=args.min_slope,
        smooth=args.smooth,
        p2_volume=args.p2_volume,
        p3_volume=args.p3_volume,
        ach=args.ach,
        q_per_person=args.q_per_person,
        method=args.method,
        cmap=args.cmap,
        dpi=args.dpi,
    )


if __name__ == "__main__":
    main()

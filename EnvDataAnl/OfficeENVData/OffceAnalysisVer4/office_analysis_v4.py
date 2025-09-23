# Office Environmental CO2 Peak & Occupancy Estimation Ver4 (OffceAnalysisVer4)
#
# Goal:
# - Detect CO2 peak times, rise durations, and rise rates for P2/P3 (meeting rooms), P1 (office) for reference
# - Estimate number of people in rooms for P2 and P3 using multiple models
#   A) Heuristic calibration from rise slope to capacity (P2 max ~8, P3 max ~30)
#   B) Mass-balance approximation: n ≈ (dC/dt)*V / q, with optional ventilation (ACH)
#   C) Band mapping of slopes to occupancy ranges
# - Compute % of meetings where peak CO2 >= 1000 ppm for P2/P3
# - Save detailed event CSVs per device + summary JSON + optional plots
#
# Inputs (default directory): G:\\RPi-Development\\EnvDataAnl\\OfficeENVData
#   Files: P1_fixed Office.csv, P2_fixed Office.csv, P3_fixed Office.csv (same as Ver1/2/3)
# Outputs (under OffceAnalysisVer4/output):
#   - events_P2_v4.csv, events_P3_v4.csv, events_P1_v4.csv (optional)
#   - summary_co2_events_v4.json
#   - plots: ts_co2_events_P2_v4.png, ts_co2_events_P3_v4.png
#
# Usage (PowerShell):
#   cd G:\\RPi-Development\\EnvDataAnl\\OfficeENVData\\OffceAnalysisVer4
#   python office_analysis_v4.py
#   # options
#   python office_analysis_v4.py --days 90 --start-th 750 --end-th 680 --min-slope 2.0 \
#       --smooth 5 --people-model mass --p2-volume 120 --p3-volume 250 --ach 1.5 --q-per-person 0.004
#
# Notes:
# - Timestamps are parsed from numeric epoch seconds or strings; invalid rows dropped.
# - Slope (ppm/min) is computed from smoothed CO2 and time differences.
# - Events are rising episodes: start when CO2 crosses start_th upward OR sustained positive slope above min_slope;
#   end when CO2 falls below end_th or slope stays negative.
# - Occupancy estimates are rounded and clipped to [0, capacity]. Multiple model columns are provided.

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
DEVICE_FILES = {
    "P1": "P1_fixed Office.csv",
    "P2": "P2_fixed Office.csv",
    "P3": "P3_fixed Office.csv",
}

# Default capacities
CAPACITY = {"P1": 10, "P2": 8, "P3": 30}

# -----------------------------
# Utilities
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
    for c in ["temperature", "humidity", "pressure", "gas_resistance", "co2", "absolute_humidity"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    df["device_id"] = device_id
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp")
    keep = [c for c in ["timestamp", "device_id", "co2", "temperature", "humidity", "pressure", "absolute_humidity", "gas_resistance"] if c in df.columns]
    return df[keep]


def load_frames(base_dir: str, limit_days: Optional[int] = None) -> pd.DataFrame:
    frames = []
    for dev, fname in DEVICE_FILES.items():
        fpath = os.path.join(base_dir, fname)
        if not os.path.isfile(fpath):
            print(f"[WARN] Missing file for {dev}: {fpath}")
            continue
        try:
            raw = pd.read_csv(fpath)
            df = normalize_df(raw, dev)
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
    ts = out["timestamp"]
    out["date"] = ts.dt.date
    out["hour"] = ts.dt.hour
    out["dow"] = ts.dt.dayofweek
    return out

# -----------------------------
# CO2 Event Detection & Slope
# -----------------------------

def smooth_series(s: pd.Series, window: int) -> pd.Series:
    if window <= 1:
        return s
    return s.rolling(window=window, min_periods=max(2, window//2), center=True).median()


def compute_slope(sub: pd.DataFrame, smooth: int) -> pd.DataFrame:
    sub = sub.sort_values("timestamp").copy()
    co2s = smooth_series(sub["co2"], smooth) if "co2" in sub.columns else sub["co2"]
    sub["co2_smooth"] = co2s
    # Compute slope in ppm/min
    t = sub["timestamp"].astype('int64') // 10**9  # seconds epoch
    dt = t.diff().fillna(0).clip(lower=1)  # avoid divide-by-zero
    dco2 = sub["co2_smooth"].diff().fillna(0)
    sub["slope_ppm_per_min"] = (dco2 / dt) * 60.0
    return sub


def detect_events(sub: pd.DataFrame,
                  start_th: float,
                  end_th: float,
                  min_slope: float,
                  min_duration_min: float = 5.0,
                  gap_close_min: float = 10.0) -> pd.DataFrame:
    """Return events with start/end/peak based on thresholds and slope.
    - start: co2 crosses start_th upward OR slope > min_slope for >=2 samples
    - end: co2 falls below end_th OR sustained negative slope
    - Merge events separated by small gaps (< gap_close_min)
    """
    if sub.empty or "co2" not in sub.columns:
        return pd.DataFrame(columns=["start", "end", "peak_time", "peak_co2", "start_co2", "end_co2"]).astype({})

    df = sub.copy()
    df["above_start"] = df["co2_smooth"] >= start_th
    df["below_end"] = df["co2_smooth"] <= end_th
    df["is_rising"] = df["slope_ppm_per_min"] >= min_slope
    df["is_falling"] = df["slope_ppm_per_min"] <= -min_slope

    # Identify candidate indices
    events: List[Tuple[int, int]] = []
    start_idx: Optional[int] = None

    for i in range(len(df)):
        row = df.iloc[i]
        if start_idx is None:
            # Start condition
            if row["above_start"] or row["is_rising"]:
                start_idx = i
        else:
            # End condition
            if row["below_end"] or row["is_falling"]:
                events.append((start_idx, i))
                start_idx = None
    if start_idx is not None:
        events.append((start_idx, len(df) - 1))

    # Merge close events
    merged: List[Tuple[int, int]] = []
    for s, e in events:
        if not merged:
            merged.append((s, e))
        else:
            last_s, last_e = merged[-1]
            # time gap between last end and new start
            gap_sec = (df.iloc[s]["timestamp"] - df.iloc[last_e]["timestamp"]).total_seconds()
            if gap_sec <= gap_close_min * 60:
                merged[-1] = (last_s, e)
            else:
                merged.append((s, e))

    # Build event records with duration filter
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
# Occupancy Estimation Models
# -----------------------------

def estimate_people_heuristic(slope_ppm_min: float, device_id: str, calib_high_pct: float, ref_slope: Optional[float]=None) -> float:
    """Map slope to occupancy using capacity and empirical scaling.
    If ref_slope is None, assume slope at calib_high_pct (e.g., 95th percentile) corresponds to capacity.
    """
    cap = CAPACITY.get(device_id, 10)
    if ref_slope is None or ref_slope <= 0:
        # fall back to proportional with soft saturation
        # assume slope 10 ppm/min reaches capacity
        ref_slope = 10.0
    n = cap * (slope_ppm_min / ref_slope)
    return float(np.clip(n, 0, cap))


def estimate_people_mass_balance(slope_ppm_min: float, volume_m3: float, q_per_person_m3_min: float, ach: float = 0.0) -> float:
    """Mass-balance approximation.
    dC/dt (ppm/min) ≈ (G/V) * 1e6, where G is m3 CO2 per min; here we use ppm directly:
    G (m3/min) ≈ slope(ppm/min) * V / 1e6. If q per person is m3/min, n ≈ G/q.
    ACH reduces effective slope during steady rise: optional correction factor (1 / (1 + ACH/alpha)).
    """
    if slope_ppm_min <= 0 or volume_m3 <= 0 or q_per_person_m3_min <= 0:
        return 0.0
    # simple correction for ventilation impact on observed slope
    corr = 1.0 / (1.0 + max(0.0, ach) / 2.0)
    g = slope_ppm_min * volume_m3 / 1e6 * corr
    n = g / q_per_person_m3_min
    return float(max(0.0, n))


# -----------------------------
# Event Post-processing per device
# -----------------------------

def characterize_events(sub: pd.DataFrame,
                         events: pd.DataFrame,
                         device_id: str,
                         calib_high_pct: float,
                         vol_m3: float,
                         q_per_person: float,
                         ach: float,
                         capacity: int) -> pd.DataFrame:
    if events.empty:
        return events

    # Compute slope between start and peak for each event
    out_rows = []
    for _, ev in events.iterrows():
        seg = sub[(sub["timestamp"] >= ev["start"]) & (sub["timestamp"] <= ev["peak_time"])].copy()
        if seg.empty:
            continue
        # robust slope: (peak - start) / minutes
        dppm = float(seg["co2_smooth"].iloc[-1] - seg["co2_smooth"].iloc[0])
        dtm = (seg["timestamp"].iloc[-1] - seg["timestamp"].iloc[0]).total_seconds() / 60.0
        slope = dppm / dtm if dtm > 0 else 0.0

        # Heuristic ref slope: high-percentile of device slopes over whole series
        # We'll compute once per function call using sub's slope distribution
        # Compute cached values on first use
        # Precompute slope values if not available
        if "slope_ppm_per_min" not in sub.columns:
            # Should not happen if compute_slope already called
            seg2 = compute_slope(sub, smooth=3)
            sub["slope_ppm_per_min"] = seg2["slope_ppm_per_min"]
        ref = float(np.nanpercentile(sub["slope_ppm_per_min"].replace([np.inf, -np.inf], np.nan).dropna(), calib_high_pct*100)) if sub["slope_ppm_per_min"].notna().any() else 10.0

        n_heur = estimate_people_heuristic(slope, device_id, calib_high_pct, ref_slope=ref)
        n_mass = estimate_people_mass_balance(slope, volume_m3=vol_m3, q_per_person_m3_min=q_per_person, ach=ach)
        n_band = band_mapping(slope, capacity)

        out = ev.to_dict()
        out.update({
            "rise_time_min": dtm,
            "rise_rate_ppm_min": slope,
            "est_people_heuristic": round(n_heur, 1),
            "est_people_mass": round(min(n_mass, capacity), 1),
            "est_people_band": n_band,
            "device_id": device_id,
        })
        out_rows.append(out)

    return pd.DataFrame(out_rows)


def band_mapping(slope_ppm_min: float, capacity: int) -> str:
    """Simple band mapping of slope to occupancy ranges."""
    if slope_ppm_min < 1.0:
        return "~0-10% cap"
    if slope_ppm_min < 2.5:
        return "10-30% cap"
    if slope_ppm_min < 5.0:
        return "30-60% cap"
    if slope_ppm_min < 8.0:
        return "60-90% cap"
    return ">=90% cap"


# -----------------------------
# Plotting
# -----------------------------

def plot_events_timeseries(sub: pd.DataFrame, events: pd.DataFrame, title: str, out_path: str):
    if sub.empty:
        return
    plt.figure(figsize=(14, 6))
    try:
        sns.lineplot(data=sub, x="timestamp", y="co2", alpha=0.3, label="CO2 raw")
        if "co2_smooth" in sub.columns:
            sns.lineplot(data=sub, x="timestamp", y="co2_smooth", label="CO2 smooth")
        for _, ev in events.iterrows():
            plt.axvspan(ev["start"], ev["end"], color='orange', alpha=0.15)
            plt.axvline(ev["peak_time"], color='red', linestyle='--', alpha=0.6)
        plt.title(title)
        plt.ylabel("CO2 (ppm)")
        plt.tight_layout()
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        plt.savefig(out_path, dpi=150)
    finally:
        plt.close()


# -----------------------------
# Main pipeline
# -----------------------------

def run_analysis(base_dir: str,
                 days: Optional[int],
                 start_th: float,
                 end_th: float,
                 min_slope: float,
                 smooth: int,
                 calib_high_pct: float,
                 p2_volume: float,
                 p3_volume: float,
                 ach: float,
                 q_per_person: float,
                 include_p1: bool = False) -> Dict:
    out_dir = ensure_output(os.path.join(base_dir, "OffceAnalysisVer4"))

    df = load_frames(base_dir, limit_days=days)
    df = add_time_features(df)

    summary: Dict = {
        "base_dir": base_dir,
        "output_dir": out_dir,
        "params": {
            "days": days,
            "start_th": start_th,
            "end_th": end_th,
            "min_slope": min_slope,
            "smooth": smooth,
            "calib_high_pct": calib_high_pct,
            "p2_volume_m3": p2_volume,
            "p3_volume_m3": p3_volume,
            "ach": ach,
            "q_per_person_m3_min": q_per_person,
        }
    }

    devices = ["P2", "P3"] + (["P1"] if include_p1 else [])
    all_events = []
    pct_over_1000: Dict[str, float] = {}

    for dev in devices:
        sub = df[(df["device_id"] == dev) & (df["co2"].notna())].copy()
        if sub.empty:
            print(f"[INFO] No CO2 data for {dev}")
            continue
        sub = compute_slope(sub, smooth=smooth)
        ev = detect_events(sub, start_th=start_th, end_th=end_th, min_slope=min_slope)
        # characterize
        vol = p2_volume if dev == "P2" else (p3_volume if dev == "P3" else 180)
        cap = CAPACITY.get(dev, 10)
        evc = characterize_events(sub, ev, dev, calib_high_pct, vol, q_per_person, ach, cap)

        # percent meetings exceeding 1000 ppm
        if not evc.empty:
            pct_over_1000[dev] = float(100.0 * (evc["peak_co2"] >= 1000.0).mean())
            evc.to_csv(os.path.join(out_dir, f"events_{dev}_v4.csv"), index=False, encoding='utf-8-sig')
            all_events.append(evc.assign(device_id=dev))
            plot_events_timeseries(sub, evc, title=f"{dev} CO2 Events (Ver4)", out_path=os.path.join(out_dir, f"ts_co2_events_{dev}_v4.png"))
        else:
            pct_over_1000[dev] = 0.0

    summary["pct_meetings_peak_over_1000ppm"] = pct_over_1000

    if all_events:
        ev_all = pd.concat(all_events, ignore_index=True)
        summary["total_events"] = int(len(ev_all))
        # Save overall summary stats per device
        per_dev = {}
        for dev, sub in ev_all.groupby("device_id"):
            per_dev[dev] = {
                "events": int(len(sub)),
                "median_rise_rate_ppm_min": float(sub["rise_rate_ppm_min"].median()),
                "median_rise_time_min": float(sub["rise_time_min"].median()),
                "median_peak_co2": float(sub["peak_co2"].median()),
                "median_people_heuristic": float(sub["est_people_heuristic"].median()),
                "median_people_mass": float(sub["est_people_mass"].median()),
            }
        summary["per_device_stats"] = per_dev
    else:
        summary["total_events"] = 0

    # Save summary JSON
    with open(os.path.join(out_dir, "summary_co2_events_v4.json"), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)

    print(f"Ver4 CO2 event analysis complete. Outputs in: {out_dir}")
    return summary


def parse_args():
    p = argparse.ArgumentParser(description="Office CO2 Peak & Occupancy Estimation Ver4")
    p.add_argument("--base-dir", type=str, default=DEFAULT_BASE_DIR, help="Directory holding Office CSV files")
    p.add_argument("--days", type=int, default=None, help="Limit to last N days")
    p.add_argument("--start-th", type=float, default=750.0, help="Start threshold for CO2 (ppm)")
    p.add_argument("--end-th", type=float, default=680.0, help="End threshold for CO2 (ppm)")
    p.add_argument("--min-slope", type=float, default=2.0, help="Minimum slope (ppm/min) to consider rising")
    p.add_argument("--smooth", type=int, default=5, help="Rolling median window for CO2 smoothing (samples)")
    p.add_argument("--calib-high-pct", type=float, default=0.95, help="Percentile for heuristic capacity calibration (0..1)")
    p.add_argument("--p2-volume", type=float, default=120.0, help="Room volume for P2 in m^3")
    p.add_argument("--p3-volume", type=float, default=250.0, help="Room volume for P3 in m^3")
    p.add_argument("--ach", type=float, default=1.5, help="Air changes per hour (ACH) for mass-balance correction")
    p.add_argument("--q-per-person", type=float, default=0.004, help="CO2 generation per person (m^3/min), ~0.004–0.005")
    p.add_argument("--include-p1", action='store_true', help="Include P1 office events for reference")
    return p.parse_args()


def main():
    args = parse_args()
    run_analysis(base_dir=args.base_dir,
                 days=args.days,
                 start_th=args.start_th,
                 end_th=args.end_th,
                 min_slope=args.min_slope,
                 smooth=args.smooth,
                 calib_high_pct=args.calib_high_pct,
                 p2_volume=args.p2_volume,
                 p3_volume=args.p3_volume,
                 ach=args.ach,
                 q_per_person=args.q_per_person,
                 include_p1=args.include_p1)


if __name__ == "__main__":
    main()

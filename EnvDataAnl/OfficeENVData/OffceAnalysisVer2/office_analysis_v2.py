# Office Environmental Data Analysis Ver2 (OffceAnalysisVer2)
#
# Focus: temperature, absolute_humidity, co2
# - Robust CSV loading for P1/P2/P3 under EnvDataAnl/OfficeENVData
# - Cleans, harmonizes columns, computes absolute humidity if missing
# - Time features: day/night, hour, weekday, week, month
# - Produces 10+ statistical analyses and plots:
#   1) Overall stats (JSON)
#   2) Day vs Night stats (CSV + plots)
#   3) Hourly stats (CSV + heatmaps)
#   4) Weekday stats (CSV + line profiles)
#   5) Weekly stats (CSV + bar plots)
#   6) Monthly stats (CSV + bar plots)
#   7) Time-series with rolling mean (per metric)
#   8) Histograms + KDE (per metric)
#   9) Box/Violin by day/night
#   10) Correlation heatmaps
#   11) Scatter plots (Temp vs AbsHum colored by CO2)
#   12) High-value (top percentile) period detection (CSV + heatmap)
#
# Usage (PowerShell):
#   cd G:\RPi-Development\EnvDataAnl\OfficeENVData\OffceAnalysisVer2
#   python office_analysis_v2.py
#   # options
#   python office_analysis_v2.py --base-dir "G:\\RPi-Development\\EnvDataAnl\\OfficeENVData" --days 90 --day-start 6 --p-high-pct 0.9

import os
import json
import argparse
import math
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

# Set non-interactive backend to avoid GUI requirements
matplotlib.use('Agg')

sns.set(style="whitegrid", context="talk")

DEFAULT_BASE_DIR = os.path.join("G:\\RPi-Development", "EnvDataAnl", "OfficeENVData")
OUTPUT_DIR_NAME = "output"
DEVICE_FILES = {
    "P1": "P1_fixed Office.csv",
    "P2": "P2_fixed Office.csv",
    "P3": "P3_fixed Office.csv",
}

FOCUS_COLS = ["temperature", "absolute_humidity", "co2"]
EXTRA_COLS = ["humidity", "pressure", "gas_resistance"]

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


def compute_absolute_humidity(temp_c: pd.Series, rh: pd.Series) -> pd.Series:
    """
    Approximate absolute humidity (g/m^3) from temperature (°C) and relative humidity (%).
    Formula based on Magnus equation.
    """
    # Avoid invalid
    t = pd.to_numeric(temp_c, errors='coerce')
    rh = pd.to_numeric(rh, errors='coerce')
    # Saturation vapor pressure (hPa)
    es = 6.112 * np.exp((17.67 * t) / (t + 243.5))
    # Actual vapor pressure (hPa)
    e = (rh / 100.0) * es
    # Absolute humidity (g/m^3)
    ah = (2.1674 * e) / (273.15 + t) * 100.0  # Convert hPa to kPa factor simplified
    return ah


def normalize_df(df: pd.DataFrame, device_id: str) -> pd.DataFrame:
    # Detect timestamp column
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

    # Parse timestamp
    df["timestamp"] = parse_timestamp(df["timestamp"])  # NaT on failure

    # Coerce numerics
    for c in set(FOCUS_COLS + EXTRA_COLS):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    # Compute absolute_humidity if missing and RH & Temp exist
    if "absolute_humidity" not in df.columns:
        if "temperature" in df.columns and "humidity" in df.columns:
            df["absolute_humidity"] = compute_absolute_humidity(df["temperature"], df["humidity"])

    df["device_id"] = device_id
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp")

    # Keep only expected columns if present
    keep = [c for c in ["timestamp", "device_id"] + FOCUS_COLS + EXTRA_COLS if c in df.columns]
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


def add_time_features(df: pd.DataFrame, day_start: int = 6) -> pd.DataFrame:
    out = df.copy()
    ts = out["timestamp"]
    out["date"] = ts.dt.date
    out["hour"] = ts.dt.hour
    out["dow"] = ts.dt.dayofweek  # 0=Mon
    out["week"] = ts.dt.isocalendar().week.astype(int)
    out["month"] = ts.dt.month
    # day_start..day_start+12 as daytime window default 6..18
    day_end = (day_start + 12) % 24
    if day_start < day_end:
        is_day = (out["hour"] >= day_start) & (out["hour"] < day_end)
    else:
        # wrap around midnight
        is_day = (out["hour"] >= day_start) | (out["hour"] < day_end)
    out["is_daytime"] = is_day.astype(int)
    out["is_night"] = 1 - out["is_daytime"]
    return out


# -----------------------------
# Statistics / Aggregations
# -----------------------------

def summarize(df: pd.DataFrame, cols: List[str]) -> Dict[str, Dict[str, float]]:
    res: Dict[str, Dict[str, float]] = {}
    for c in cols:
        if c in df.columns:
            s = df[c]
            res[c] = {
                "count": int(s.count()),
                "mean": float(np.nanmean(s.values)) if s.count() else np.nan,
                "std": float(np.nanstd(s.values)) if s.count() else np.nan,
                "min": float(np.nanmin(s.values)) if s.count() else np.nan,
                "max": float(np.nanmax(s.values)) if s.count() else np.nan,
            }
    return res


def group_stats(df: pd.DataFrame, by: List[str], cols: List[str], extra_aggs: Optional[Dict]=None) -> pd.DataFrame:
    aggs = {c: ["count", "mean", "std", "min", "max"] for c in cols if c in df.columns}
    if extra_aggs:
        for k, v in extra_aggs.items():
            aggs[k] = v
    g = df.groupby(by).agg(aggs)
    g.columns = ["_".join([a for a in col if a]) for col in g.columns.to_flat_index()]
    return g.reset_index()


def compute_correlations(df: pd.DataFrame, cols: List[str]) -> Dict[str, pd.DataFrame]:
    out: Dict[str, pd.DataFrame] = {}
    for dev, sub in df.groupby("device_id"):
        vc = [c for c in cols if c in sub.columns]
        if len(vc) >= 2:
            out[dev] = sub[vc].corr()
    return out


def detect_high_periods(df: pd.DataFrame, metric: str, pct: float = 0.9) -> pd.DataFrame:
    """Mark periods exceeding percentile threshold per device, return intervals list."""
    rows = []
    for dev, sub in df.dropna(subset=[metric]).sort_values("timestamp").groupby("device_id"):
        thr = sub[metric].quantile(pct)
        above = sub[metric] >= thr
        if above.empty:
            continue
        start = None
        for t, flag in zip(sub["timestamp"], above):
            if flag and start is None:
                start = t
            if (not flag) and start is not None:
                rows.append({"device_id": dev, "metric": metric, "start": start, "end": t})
                start = None
        if start is not None:
            rows.append({"device_id": dev, "metric": metric, "start": start, "end": sub["timestamp"].iloc[-1]})
    return pd.DataFrame(rows)


# -----------------------------
# Plotting helpers
# -----------------------------

def save_fig(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def ts_with_rolling(df: pd.DataFrame, col: str, out_dir: str):
    rdf = df.sort_values(["device_id", "timestamp"]).copy()
    rdf[f"{col}_rollmean_30"] = rdf.groupby("device_id")[col].transform(lambda s: s.rolling(window=30, min_periods=5).mean())
    plt.figure(figsize=(14, 6))
    try:
        sns.lineplot(data=rdf, x="timestamp", y=col, hue="device_id", alpha=0.25, legend=False)
        sns.lineplot(data=rdf, x="timestamp", y=f"{col}_rollmean_30", hue="device_id")
        plt.title(f"{col} Raw + 30-sample Rolling Mean")
        save_fig(os.path.join(out_dir, f"timeseries_{col}_with_rolling_v2.png"))
    finally:
        plt.close()


def hist_kde(df: pd.DataFrame, col: str, out_dir: str):
    plt.figure(figsize=(12, 6))
    try:
        for dev, sub in df.groupby("device_id"):
            sns.kdeplot(sub[col].dropna(), label=f"{dev} KDE", fill=True, alpha=0.2)
            sns.histplot(sub[col].dropna(), bins=40, stat='density', element='step', fill=False, label=f"{dev} Hist", alpha=0.4)
        plt.legend()
        plt.title(f"{col} Distribution (Histogram + KDE)")
        save_fig(os.path.join(out_dir, f"dist_{col}_hist_kde_v2.png"))
    finally:
        plt.close()


def box_violin_daynight(df: pd.DataFrame, col: str, out_dir: str):
    plt.figure(figsize=(12, 6))
    try:
        tidy = df[["device_id", "is_daytime", col]].dropna().copy()
        tidy["period"] = np.where(tidy["is_daytime"] == 1, "Day", "Night")
        ax = sns.violinplot(data=tidy, x="period", y=col, hue="device_id", cut=0, inner=None)
        sns.boxplot(data=tidy, x="period", y=col, hue="device_id", showcaps=True, boxprops={'facecolor':'None'}, showfliers=False, whiskerprops={'linewidth':1}, ax=ax)
        plt.title(f"{col} Day vs Night (Violin + Box)")
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2)
        save_fig(os.path.join(out_dir, f"daynight_{col}_violin_box_v2.png"))
    finally:
        plt.close()


def weekday_hour_heatmap(df: pd.DataFrame, col: str, out_dir: str):
    plt.figure(figsize=(12, 6))
    try:
        # Average across devices for a general office view
        pivot = df.pivot_table(values=col, index="dow", columns="hour", aggfunc='mean')
        sns.heatmap(pivot, cmap='YlOrRd', annot=False)
        plt.title(f"{col} Heatmap (Weekday x Hour)")
        plt.ylabel("Weekday (0=Mon)")
        plt.xlabel("Hour")
        save_fig(os.path.join(out_dir, f"heatmap_{col}_weekday_hour_v2.png"))
    finally:
        plt.close()


def daily_hour_heatmap(df: pd.DataFrame, col: str, out_dir: str):
    plt.figure(figsize=(16, 6))
    try:
        # Daily average by hour (across devices)
        pivot = df.pivot_table(values=col, index="date", columns="hour", aggfunc='mean')
        sns.heatmap(pivot, cmap='viridis')
        plt.title(f"{col} Heatmap (Date x Hour)")
        plt.ylabel("Date")
        plt.xlabel("Hour")
        save_fig(os.path.join(out_dir, f"heatmap_{col}_date_hour_v2.png"))
    finally:
        plt.close()


def monthly_bar(df: pd.DataFrame, col: str, out_dir: str):
    plt.figure(figsize=(12, 6))
    try:
        g = df.groupby(["device_id", "month"], as_index=False)[col].mean()
        sns.barplot(data=g, x="month", y=col, hue="device_id")
        plt.title(f"{col} Monthly Mean by Device")
        save_fig(os.path.join(out_dir, f"monthly_{col}_bar_v2.png"))
    finally:
        plt.close()


def weekly_bar(df: pd.DataFrame, col: str, out_dir: str):
    plt.figure(figsize=(12, 6))
    try:
        g = df.groupby(["device_id", "week"], as_index=False)[col].mean()
        sns.lineplot(data=g, x="week", y=col, hue="device_id", marker='o')
        plt.title(f"{col} Weekly Mean by Device")
        save_fig(os.path.join(out_dir, f"weekly_{col}_line_v2.png"))
    finally:
        plt.close()


def weekday_profile(df: pd.DataFrame, col: str, out_dir: str):
    plt.figure(figsize=(12, 6))
    try:
        g = df.groupby(["device_id", "dow"], as_index=False)[col].mean()
        sns.lineplot(data=g, x="dow", y=col, hue="device_id", marker='o')
        plt.title(f"{col} Weekday Mean by Device (0=Mon)")
        save_fig(os.path.join(out_dir, f"weekday_{col}_line_v2.png"))
    finally:
        plt.close()


def corr_heatmap(df: pd.DataFrame, cols: List[str], out_dir: str):
    for dev, sub in df.groupby("device_id"):
        vc = [c for c in cols if c in sub.columns]
        if len(vc) < 2:
            continue
        plt.figure(figsize=(6, 5))
        try:
            corr = sub[vc].corr()
            sns.heatmap(corr, annot=True, vmin=-1, vmax=1, cmap='coolwarm')
            plt.title(f"Correlation ({dev})")
            save_fig(os.path.join(out_dir, f"corr_{dev}_v2.png"))
        finally:
            plt.close()


def scatter_temp_abs_col_co2(df: pd.DataFrame, out_dir: str):
    if not {"temperature", "absolute_humidity", "co2"}.issubset(df.columns):
        return
    plt.figure(figsize=(10, 8))
    try:
        sc = plt.scatter(df["temperature"], df["absolute_humidity"], c=df["co2"], cmap='plasma', s=12, alpha=0.6)
        cbar = plt.colorbar(sc)
        cbar.set_label("CO2 (ppm)")
        plt.xlabel("Temperature (°C)")
        plt.ylabel("Absolute Humidity (g/m³)")
        plt.title("Temp vs Absolute Humidity (Colored by CO2)")
        save_fig(os.path.join(out_dir, "scatter_temp_abs_col_co2_v2.png"))
    finally:
        plt.close()


def plot_day_night_means(df: pd.DataFrame, col: str, out_dir: str):
    plt.figure(figsize=(10, 6))
    try:
        tidy = df[["device_id", "is_daytime", col]].dropna().copy()
        tidy["period"] = np.where(tidy["is_daytime"] == 1, "Day", "Night")
        g = tidy.groupby(["device_id", "period"], as_index=False)[col].mean()
        sns.barplot(data=g, x="period", y=col, hue="device_id")
        plt.title(f"{col} Day vs Night Mean")
        save_fig(os.path.join(out_dir, f"daynight_{col}_bar_v2.png"))
    finally:
        plt.close()


def high_value_heatmap(df: pd.DataFrame, col: str, pct: float, out_dir: str):
    # Mark values above threshold per device and average by (date, hour)
    marks = []
    for dev, sub in df.dropna(subset=[col]).groupby("device_id"):
        thr = sub[col].quantile(pct)
        s = (sub[["timestamp", col]].copy())
        s["date"] = s["timestamp"].dt.date
        s["hour"] = s["timestamp"].dt.hour
        s["is_high"] = (s[col] >= thr).astype(int)
        agg = s.groupby(["date", "hour"], as_index=False)["is_high"].mean()
        agg["device_id"] = dev
        marks.append(agg)
    if not marks:
        return
    mdf = pd.concat(marks, ignore_index=True)
    for dev, sub in mdf.groupby("device_id"):
        pivot = sub.pivot_table(values="is_high", index="date", columns="hour", aggfunc='mean', fill_value=0.0)
        plt.figure(figsize=(14, 6))
        try:
            sns.heatmap(pivot, cmap='Reds', vmin=0, vmax=1)
            plt.title(f"High-{col} Fraction per (Date x Hour) for {dev} (pct>={pct})")
            plt.ylabel("Date")
            plt.xlabel("Hour")
            save_fig(os.path.join(out_dir, f"high_{col}_date_hour_{dev}_v2.png"))
        finally:
            plt.close()


# -----------------------------
# Main pipeline
# -----------------------------

def run_analysis(base_dir: str, days: Optional[int], day_start: int, p_high_pct: float) -> Dict:
    out_dir = ensure_output(os.path.join(base_dir, "OffceAnalysisVer2"))

    df = load_frames(base_dir, limit_days=days)
    df = add_time_features(df, day_start=day_start)

    available = [c for c in FOCUS_COLS if c in df.columns]

    summary: Dict = {
        "base_dir": base_dir,
        "output_dir": out_dir,
        "devices": sorted(df["device_id"].unique().tolist()),
        "rows": int(len(df)),
        "cols": df.columns.tolist(),
        "focus_metrics": available,
        "day_start": day_start,
        "p_high_pct": p_high_pct,
    }

    # 1) Overall stats
    summary["overall_stats"] = summarize(df, available)
    with open(os.path.join(out_dir, "summary_overall_v2.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)

    # 2) Day vs Night stats
    dn = group_stats(df, by=["device_id", "date", "is_daytime"], cols=available)
    dn_path = os.path.join(out_dir, "stats_day_night_v2.csv")
    dn.to_csv(dn_path, index=False, encoding="utf-8-sig")

    # 3) Hourly stats
    hourly = group_stats(df, by=["device_id", "date", "hour"], cols=available)
    hourly_path = os.path.join(out_dir, "stats_hourly_v2.csv")
    hourly.to_csv(hourly_path, index=False, encoding="utf-8-sig")

    # 4) Weekday stats
    wday = group_stats(df, by=["device_id", "dow"], cols=available)
    wday_path = os.path.join(out_dir, "stats_weekday_v2.csv")
    wday.to_csv(wday_path, index=False, encoding="utf-8-sig")

    # 5) Weekly stats
    week = group_stats(df, by=["device_id", "week"], cols=available)
    week_path = os.path.join(out_dir, "stats_weekly_v2.csv")
    week.to_csv(week_path, index=False, encoding="utf-8-sig")

    # 6) Monthly stats
    month = group_stats(df, by=["device_id", "month"], cols=available)
    month_path = os.path.join(out_dir, "stats_monthly_v2.csv")
    month.to_csv(month_path, index=False, encoding="utf-8-sig")

    # 7) High-value periods
    high_periods_all = []
    for c in available:
        hp = detect_high_periods(df, c, pct=p_high_pct)
        if not hp.empty:
            hp.to_csv(os.path.join(out_dir, f"high_periods_{c}_v2.csv"), index=False, encoding="utf-8-sig")
            high_periods_all.append(hp)
    if high_periods_all:
        pd.concat(high_periods_all, ignore_index=True).to_csv(os.path.join(out_dir, "high_periods_all_v2.csv"), index=False, encoding="utf-8-sig")

    # 8) Correlations
    corr_heatmap(df, available, out_dir)

    # 9) Plots per metric
    for c in available:
        ts_with_rolling(df[["timestamp", "device_id", c]].dropna(), c, out_dir)
        hist_kde(df[["device_id", c]].dropna(), c, out_dir)
        box_violin_daynight(df[["device_id", "is_daytime", c]].dropna(), c, out_dir)
        weekday_hour_heatmap(df[["dow", "hour", c]].dropna(), c, out_dir)
        daily_hour_heatmap(df[["date", "hour", c]].dropna(), c, out_dir)
        monthly_bar(df[["device_id", "month", c]].dropna(), c, out_dir)
        weekly_bar(df[["device_id", "week", c]].dropna(), c, out_dir)
        weekday_profile(df[["device_id", "dow", c]].dropna(), c, out_dir)
        plot_day_night_means(df[["device_id", "is_daytime", c]].dropna(), c, out_dir)
        high_value_heatmap(df[["timestamp", "device_id", c]].dropna(), c, p_high_pct, out_dir)

    # 10) Cross-metric scatter
    scatter_temp_abs_col_co2(df.dropna(subset=["temperature", "absolute_humidity", "co2"]), out_dir)

    print(f"Ver2 analysis complete. Outputs in: {out_dir}")
    return summary


def parse_args():
    p = argparse.ArgumentParser(description="Office Environmental Data Analysis Ver2")
    p.add_argument("--base-dir", type=str, default=DEFAULT_BASE_DIR, help="Directory holding Office CSV files")
    p.add_argument("--days", type=int, default=None, help="Limit to last N days")
    p.add_argument("--day-start", type=int, default=6, help="Hour-of-day for daytime start (default 6)")
    p.add_argument("--p-high-pct", type=float, default=0.9, help="Percentile threshold (0..1) for high-value detection (default 0.9)")
    return p.parse_args()


def main():
    args = parse_args()
    run_analysis(args.base_dir, args.days, args.day_start, args.p_high_pct)


if __name__ == "__main__":
    main()

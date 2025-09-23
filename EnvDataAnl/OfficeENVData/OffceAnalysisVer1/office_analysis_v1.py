# Office Environmental Data Analysis Ver1 (OffceAnalysisVer1)
#
# - Reads three CSVs under EnvDataAnl/OfficeENVData: P1_fixed Office.csv, P2_fixed Office.csv, P3_fixed Office.csv
# - Cleans and harmonizes columns
# - Focuses on humidity and CO2 trends
# - Produces day vs night and weekday analyses per device and overall
# - Handles missing/invalid rows by coercing and dropping where appropriate
# - Saves figures (PNG) and a summary JSON into ./OffceAnalysisVer1/output
#
# Usage (PowerShell):
#   cd G:\RPi-Development\EnvDataAnl\OfficeENVData\OffceAnalysisVer1
#   python office_analysis_v1.py
#   # or with options
#   python office_analysis_v1.py --base-dir "G:\\RPi-Development\\EnvDataAnl\\OfficeENVData" --days 30

import os
import json
import argparse
from typing import Dict, List, Optional

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

FOCUS_COLS = ["humidity", "co2"]
EXTRA_COLS = ["temperature", "pressure", "gas_resistance", "absolute_humidity"]

sns.set(style="whitegrid")


def _ensure_output(out_base: str) -> str:
    out_dir = os.path.join(out_base, OUTPUT_DIR_NAME)
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def _parse_timestamp(series: pd.Series) -> pd.Series:
    # Accept numeric epoch seconds or string ISO; coerce invalid to NaT
    if pd.api.types.is_numeric_dtype(series):
        ts = pd.to_datetime(series, unit="s", errors="coerce")
    else:
        ts = pd.to_datetime(series.astype(str), errors="coerce")
    return ts


def _find_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    low = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in low:
            return low[cand.lower()]
    return None


def _normalize_df(df: pd.DataFrame, device_id: str) -> pd.DataFrame:
    # Common possible timestamp header names
    ts_col = _find_col(df, ["timestamp", "time", "date", "日時", "時刻"]) or "timestamp"
    if ts_col not in df.columns:
        # try first column fallback
        ts_col = df.columns[0]
    df = df.copy()
    df.rename(columns={ts_col: "timestamp"}, inplace=True)

    # Map numeric columns (case-insensitive)
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

    # Parse timestamp
    df["timestamp"] = _parse_timestamp(df["timestamp"])

    # Coerce numeric of interest
    for col in set(FOCUS_COLS + EXTRA_COLS):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Add device id and drop invalid timestamps
    df["device_id"] = device_id
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp")

    return df


essential_cols = ["timestamp", "device_id"] + FOCUS_COLS + EXTRA_COLS


def load_office_frames(base_dir: str, limit_days: Optional[int] = None) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for dev, fname in DEVICE_FILES.items():
        fpath = os.path.join(base_dir, fname)
        if not os.path.isfile(fpath):
            print(f"[WARN] Missing file for {dev}: {fpath}")
            continue
        try:
            df = pd.read_csv(fpath)
            df = _normalize_df(df, dev)
            if limit_days and not df.empty:
                cutoff = pd.Timestamp.now() - pd.Timedelta(days=limit_days)
                df = df[df["timestamp"] >= cutoff]
            # keep only known columns
            keep = [c for c in essential_cols if c in df.columns]
            df = df[keep]
            frames.append(df)
        except Exception as e:
            print(f"[WARN] Failed to load {fpath}: {e}")
    if not frames:
        raise RuntimeError("No input files could be loaded.")
    all_df = pd.concat(frames, ignore_index=True)
    return all_df


def add_time_flags(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["date"] = out["timestamp"].dt.date
    out["hour"] = out["timestamp"].dt.hour
    out["dow"] = out["timestamp"].dt.dayofweek  # 0=Mon
    out["is_daytime"] = ((out["hour"] >= 6) & (out["hour"] < 18)).astype(int)
    out["is_night"] = 1 - out["is_daytime"]
    return out


def summarize_day_night(df: pd.DataFrame, value_cols: List[str]) -> pd.DataFrame:
    grp = df.groupby(["device_id", "date", "is_daytime"])[value_cols]
    agg = grp.agg(["count", "mean", "std", "min", "max"]).reset_index()
    # flatten columns
    agg.columns = ["_".join(map(str, c)).strip("_") for c in agg.columns.values]
    return agg


def summarize_weekday(df: pd.DataFrame, value_cols: List[str]) -> pd.DataFrame:
    grp = df.groupby(["device_id", "dow"])[value_cols].agg(["count", "mean", "std"]).reset_index()
    grp.columns = ["_".join(map(str, c)).strip("_") for c in grp.columns.values]
    return grp


def rolling_trend(df: pd.DataFrame, col: str, window: int = 30) -> pd.DataFrame:
    sub = df.sort_values(["device_id", "timestamp"]).copy()
    sub[f"{col}_rollmean_{window}"] = sub.groupby("device_id")[col].transform(
        lambda s: s.rolling(window=window, min_periods=max(3, window//5)).mean()
    )
    return sub


def _save_lineplot(df: pd.DataFrame, x: str, y: str, hue: Optional[str], title: str, out_path: str):
    plt.figure(figsize=(12, 5))
    try:
        sns.lineplot(data=df, x=x, y=y, hue=hue, errorbar=None)
        plt.title(title)
        plt.tight_layout()
        plt.savefig(out_path)
    finally:
        plt.close()


def run_analysis(base_dir: str, days: Optional[int] = None) -> Dict:
    out_dir = _ensure_output(os.path.join(base_dir, "OffceAnalysisVer1"))

    df = load_office_frames(base_dir, limit_days=days)
    df = add_time_flags(df)

    # Focus metrics present
    available_focus = [c for c in FOCUS_COLS if c in df.columns]

    summary: Dict = {
        "base_dir": base_dir,
        "output_dir": out_dir,
        "devices": sorted(df["device_id"].unique().tolist()),
        "rows": int(len(df)),
        "cols": df.columns.tolist(),
        "focus_metrics": available_focus,
    }

    # Day vs Night summaries
    if available_focus:
        dn = summarize_day_night(df, available_focus)
        dn_out = os.path.join(out_dir, "day_night_summary.csv")
        dn.to_csv(dn_out, index=False, encoding="utf-8-sig")
        summary["day_night_summary"] = dn_out

        # Plot day vs night means per device
        melt_cols = []
        for metric in available_focus:
            mean_col = f"{metric}_mean"
            # columns are like humidity_mean, but grouped multi-index flatten may include suffixes
            # find columns that end with _mean for each metric
            candidates = [c for c in dn.columns if c.endswith(f"{metric}_mean") or c == f"{metric}_mean"]
            if metric == "co2":
                candidates += [c for c in dn.columns if c.endswith("co2_mean")]
            for c in candidates:
                if c not in melt_cols:
                    melt_cols.append(c)
        # Construct a plot table
        plot_dn = dn[["device_id", "is_daytime"] + [c for c in dn.columns if c.endswith("_mean")]].copy()
        plot_dn = plot_dn.melt(id_vars=["device_id", "is_daytime"], var_name="metric", value_name="mean")
        plot_dn["period"] = np.where(plot_dn["is_daytime"] == 1, "Day", "Night")
        _save_lineplot(
            plot_dn,
            x="period",
            y="mean",
            hue="device_id",
            title="Day vs Night Mean (Humidity/CO2)",
            out_path=os.path.join(out_dir, "day_vs_night_means.png"),
        )

    # Weekday profiles
    if available_focus:
        wd = summarize_weekday(df, available_focus)
        wd_out = os.path.join(out_dir, "weekday_summary.csv")
        wd.to_csv(wd_out, index=False, encoding="utf-8-sig")
        summary["weekday_summary"] = wd_out

        # Prepare a plot: average by weekday
        # Rebuild a tidy df for plotting
        tidy = []
        for dev in df["device_id"].unique():
            sub = df[df["device_id"] == dev]
            for metric in available_focus:
                if metric in sub.columns:
                    g = sub.groupby("dow")[metric].mean().reset_index()
                    g["device_id"] = dev
                    g["metric"] = metric
                    tidy.append(g)
        if tidy:
            tdf = pd.concat(tidy, ignore_index=True)
            # Label weekdays
            labels = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
            tdf["weekday"] = tdf["dow"].map(labels)
            plt.figure(figsize=(12, 6))
            try:
                sns.lineplot(data=tdf, x="weekday", y=metric, hue="device_id", style="metric", markers=True)
                plt.title("Weekday Mean Profiles (Humidity/CO2)")
                plt.tight_layout()
                plt.savefig(os.path.join(out_dir, "weekday_profiles.png"))
            finally:
                plt.close()

    # Rolling trend plots for focus metrics
    for col in available_focus:
        if col not in df.columns:
            continue
        rdf = rolling_trend(df[["timestamp", "device_id", col]].dropna(), col, window=30)
        # Plot raw + rolling mean
        plt.figure(figsize=(13, 6))
        try:
            sns.lineplot(data=rdf, x="timestamp", y=col, hue="device_id", alpha=0.25, legend=False)
            sns.lineplot(data=rdf, x="timestamp", y=f"{col}_rollmean_30", hue="device_id")
            plt.title(f"{col.upper()} Raw + 30-sample Rolling Mean")
            plt.tight_layout()
            plt.savefig(os.path.join(out_dir, f"timeseries_{col}_with_rolling.png"))
        finally:
            plt.close()

    # Save overall stats
    overall_stats = {}
    for col in available_focus:
        s = df[col]
        overall_stats[col] = {
            "count": int(s.count()),
            "mean": float(np.nanmean(s.values)),
            "std": float(np.nanstd(s.values)),
            "min": float(np.nanmin(s.values)) if s.count() > 0 else None,
            "max": float(np.nanmax(s.values)) if s.count() > 0 else None,
        }
    summary["overall_stats"] = overall_stats

    # Save JSON summary
    sum_path = os.path.join(out_dir, "summary_office_v1.json")
    with open(sum_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"Analysis complete. Outputs in: {out_dir}")
    return summary


def parse_args():
    p = argparse.ArgumentParser(description="Office Environmental Data Analysis Ver1")
    p.add_argument("--base-dir", type=str, default=DEFAULT_BASE_DIR, help="Directory holding Office CSV files")
    p.add_argument("--days", type=int, default=None, help="Limit to last N days")
    return p.parse_args()


def main():
    args = parse_args()
    run_analysis(args.base_dir, args.days)


if __name__ == "__main__":
    main()

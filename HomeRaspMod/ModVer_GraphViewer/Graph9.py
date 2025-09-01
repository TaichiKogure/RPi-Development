import os
import time
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Style
plt.style.use('default')

# =========================
# Configurable parameters
# =========================
MAX_POINTS = 2000  # target max points per line for plotting (auto downsampling)
AGG_METHOD = 'mean'  # 'mean'|'median'|'min'|'max'
USE_PARQUET = False  # optional fast IO sidecar
USE_FEATHER = False  # optional fast IO sidecar (exclusive with parquet)
PLOT_REFRESH_SEC = 80

# CSV inputs and needed columns per file (lowercase-normalized keys will be handled)
DATA_FILES: List[Tuple[str, str]] = [
    ("/home/koguretaichi/Documents/Flask/BedRoomEnv.csv", 'current_time'),
    ("/home/koguretaichi/Documents/Flask/OutsideEnv.csv", 'current_time'),
    ("/home/koguretaichi/Documents/Flask/PicodataX.csv", 'current_time'),
    ("/home/koguretaichi/Documents/Flask/LR_env.csv", 'current_time'),
    ("/home/koguretaichi/Env_data_BME680.csv", 'current_time'),
]

REQUIRED_COLS: Dict[str, List[str]] = {
    "/home/koguretaichi/Documents/Flask/BedRoomEnv.csv": [
        'current_time', 'Tempereture', 'Humidity', 'Pressure', 'GasResistance', 'CO2'
    ],
    "/home/koguretaichi/Documents/Flask/OutsideEnv.csv": [
        'current_time', 'Temperature-outside', 'Humidity-outside', 'Pressure-outside', 'GasResistance-outside'
    ],
    "/home/koguretaichi/Documents/Flask/PicodataX.csv": [
        'current_time', 'Tempereture'
    ],
    "/home/koguretaichi/Documents/Flask/LR_env.csv": [
        'current_time', 'Temperature_DS18B20', 'Humidity_DHT11', 'AnalogValue', 'CO2'
    ],
    "/home/koguretaichi/Env_data_BME680.csv": [
        'current_time', 'temperature', 'humidity', 'pressure', 'gas_resistance'
    ],
}

# Column normalization mapping (handles misspellings / variants)
COLMAP = {
    'tempereture': 'temperature',  # fix misspelling
    'temperature-outside': 'temperature_outside',
    'humidity-outside': 'humidity_outside',
    'pressure-outside': 'pressure_outside',
    'gasresistance-outside': 'gas_resistance_outside',
    'temperature_ds18b20': 'temperature_ds18b20',
    'humidity_dht11': 'humidity_dht11',
    'analogvalue': 'analog_value',
    'gasresistance': 'gas_resistance',
    'desk_temp': 'temperature',
    'desk_humidity': 'humidity',
    'desk_pressure': 'pressure',
}

# Basic dtype hints (best-effort; non-matching columns are ignored)
DTYPES_HINT = {
    'co2': 'float64',
    'temperature': 'float64',
    'temperature_outside': 'float64',
    'temperature_ds18b20': 'float64',
    'humidity': 'float64',
    'humidity_outside': 'float64',
    'humidity_dht11': 'float64',
    'pressure': 'float64',
    'pressure_outside': 'float64',
    'gas_resistance': 'float64',
    'gas_resistance_outside': 'float64',
    'analog_value': 'float64',
}

# Cache for incremental reads
_FILE_CACHE: Dict[str, Dict] = {}


def _sidecar_path(csv_path: str) -> str:
    if USE_PARQUET:
        return os.path.splitext(csv_path)[0] + '.parquet'
    if USE_FEATHER:
        return os.path.splitext(csv_path)[0] + '.feather'
    return ''


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    # lower-case first
    rename_map = {}
    for c in df.columns:
        lc = c.lower()
        rename_map[c] = COLMAP.get(lc, lc)
    df = df.rename(columns=rename_map)
    return df


def _enforce_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    for col, dt in DTYPES_HINT.items():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


def _vector_abs_humidity(temp: pd.Series, rh: pd.Series) -> pd.Series:
    # AH = (6.112 * exp((17.67*T)/(T+243.5)) * RH * 2.1674) / (273.15+T)
    T = temp.astype(float)
    RH = rh.astype(float)
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        ah = (6.112 * np.exp((17.67 * T) / (T + 243.5)) * RH * 2.1674) / (273.15 + T)
    return pd.Series(ah, index=temp.index)


def _basic_stats(df: pd.DataFrame, cols: List[str]) -> Dict[str, Dict[str, float]]:
    stats = {}
    for c in cols:
        if c in df.columns:
            s = df[c]
            stats[c] = {
                'count': int(s.count()),
                'min': float(np.nanmin(s.values)) if s.count() else np.nan,
                'max': float(np.nanmax(s.values)) if s.count() else np.nan,
                'mean': float(np.nanmean(s.values)) if s.count() else np.nan,
                'missing_rate': float(np.mean(s.isna())) if len(s) else 1.0,
            }
    return stats


def _read_csv_incremental(file_path: str, date_column: str, usecols: Optional[List[str]] = None) -> pd.DataFrame:
    """Incremental CSV reader with caching and robust datetime parsing.
    - Uses file size/mtime and previous row count to only read appended rows when possible.
    - Forces dtype (best-effort) and parses datetime with errors='coerce'.
    - Drops rows with invalid datetime.
    - Optionally updates/uses parquet/feather sidecar for faster reloads.
    """
    st = os.stat(file_path)
    size, mtime = st.st_size, st.st_mtime
    cache = _FILE_CACHE.get(file_path)

    # If unchanged, return cached df
    if cache and cache.get('mtime') == mtime and cache.get('size') == size:
        return cache['df']

    # Decide fast path read (sidecar) only on full reloads
    sidecar = _sidecar_path(file_path)
    full_reload = True
    prev_rows = 0
    if cache:
        prev_rows = cache.get('rows', 0)
        if size > cache.get('size', 0) and cache.get('rows', 0) > 0:
            full_reload = False

    # Build usecols (ensure date column included)
    cols = list(usecols) if usecols else None
    if cols and date_column not in cols:
        cols = [date_column] + cols

    if not full_reload:
        # Read only appended rows by skipping known data rows (keep header)
        try:
            df_new = pd.read_csv(
                file_path,
                usecols=cols,
                skiprows=range(1, prev_rows + 1),  # skip header's following rows
                low_memory=False,
            )
        except Exception:
            # Fallback to full reload on any error
            df_new = None
            full_reload = True
        if df_new is not None and len(df_new) > 0:
            df = pd.concat([cache['df'].reset_index(), df_new], ignore_index=True)
        else:
            # nothing appended (rare), use cache
            _FILE_CACHE[file_path] = {
                'df': cache['df'], 'rows': cache['rows'], 'size': size, 'mtime': mtime
            }
            return cache['df']
    if full_reload:
        # Try sidecar fast path
        if sidecar and os.path.exists(sidecar):
            try:
                if USE_PARQUET:
                    df = pd.read_parquet(sidecar)
                elif USE_FEATHER:
                    df = pd.read_feather(sidecar)
                else:
                    df = pd.read_csv(file_path, usecols=cols, low_memory=False)
            except Exception:
                df = pd.read_csv(file_path, usecols=cols, low_memory=False)
        else:
            df = pd.read_csv(file_path, usecols=cols, low_memory=False)

    # Normalize columns and parse datetime
    df = _normalize_columns(df)
    date_col_norm = date_column.lower()
    if date_col_norm not in df.columns:
        # try original date_column (case sensitive) if normalization removed it
        if date_column in df.columns:
            date_col_norm = date_column
        else:
            raise KeyError(f"Date column '{date_column}' not found in {file_path}")

    # Robust datetime parse
    dt = pd.to_datetime(df[date_col_norm], errors='coerce')
    bad = dt.isna().sum()
    if bad:
        print(f"[WARN] {file_path}: dropped {bad} rows due to invalid datetime in '{date_col_norm}'")
    df[date_col_norm] = dt
    df = df.dropna(subset=[date_col_norm])
    df = df.set_index(date_col_norm).sort_index()

    # Enforce numeric dtypes
    df = _enforce_dtypes(df)

    # Update sidecar on full reload for faster subsequent loads
    if full_reload and sidecar:
        try:
            if USE_PARQUET:
                df.reset_index().to_parquet(sidecar, index=False)
            elif USE_FEATHER:
                df.reset_index().to_feather(sidecar)
        except Exception:
            pass

    # Update cache
    _FILE_CACHE[file_path] = {
        'df': df,
        'rows': len(df),
        'size': size,
        'mtime': mtime,
    }
    return df


def _auto_resample_rule(index: pd.DatetimeIndex, max_points: int) -> Optional[str]:
    if len(index) <= max_points:
        return None
    total_seconds = (index.max() - index.min()).total_seconds()
    if total_seconds <= 0:
        return None
    sec_per_point = max(1, int(total_seconds / max_points))
    return f"{sec_per_point}S"


def resample_downsample(df: pd.DataFrame, max_points: int = MAX_POINTS, agg: str = AGG_METHOD,
                        reference_index: Optional[pd.DatetimeIndex] = None) -> Tuple[pd.DataFrame, float]:
    """Resample to a dynamic frequency to limit point count. Returns (df_ds, compression_ratio)."""
    original_points = len(df)
    rule = _auto_resample_rule(df.index, max_points)
    if rule is None:
        df_ds = df
    else:
        if agg == 'median':
            df_ds = df.resample(rule).median()
        elif agg == 'min':
            df_ds = df.resample(rule).min()
        elif agg == 'max':
            df_ds = df.resample(rule).max()
        else:
            df_ds = df.resample(rule).mean()
    if reference_index is not None and len(reference_index) > 0:
        # align by nearest timestamps
        df_ds = df_ds.reindex(reference_index, method='nearest')
    compression = (original_points / max(1, len(df_ds))) if len(df_ds) else 1.0
    return df_ds, compression


def plot_lines(ax, x_data, y_data_dict, labels, colors, linestyles, ylabel, y_scale=None):
    for y_key, label, color, linestyle in zip(y_data_dict, labels, colors, linestyles):
        ax.plot(x_data, y_data_dict[y_key], label=label, color=color, linestyle=linestyle)
    ax.set_ylabel(ylabel)
    if y_scale:
        ax.set_ylim(y_scale)
    ax.grid(True)
    ax.legend(loc='best')


def create_subplot(index, row, x_data, y_data_dict, labels, colors, linestyles, ylabel, y_scale=None, sharex=None):
    ax = plt.subplot(3, 2, index, sharex=sharex)
    plot_lines(ax, x_data, y_data_dict, labels, colors, linestyles, ylabel, y_scale)
    if index >= 5:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
    return ax


def plot_data(start_time: Optional[str] = None, y_scales: Optional[Dict[str, Tuple[float, float]]] = None):
    plt.figure()

    while True:
        # ===============
        # Load & prepare
        # ===============
        datasets = []
        for file, date_col in DATA_FILES:
            usecols = REQUIRED_COLS.get(file)
            df = _read_csv_incremental(file, date_col, usecols=usecols)
            datasets.append(df)

        # Choose reference index from first dataset (after potential downsampling)
        # First, compute absolute humidity vectorized for needed datasets
        bed_data, out_data, pico_data, lr_data, bme680_data = datasets

        # Compute absolute humidity (vectorized, NaN-safe)
        if {'temperature', 'humidity'}.issubset(bme680_data.columns):
            bme680_data['absolute_humidity'] = _vector_abs_humidity(bme680_data['temperature'], bme680_data['humidity'])
        if {'tempereture', 'humidity'}.issubset(bed_data.columns):
            # 'tempereture' already normalized to 'temperature' in COLMAP, but if original remains:
            if 'temperature' in bed_data.columns:
                bed_data['absolute_humidity'] = _vector_abs_humidity(bed_data['temperature'], bed_data['humidity'])
            else:
                bed_data['absolute_humidity'] = _vector_abs_humidity(bed_data['tempereture'], bed_data['humidity'])
        if {'temperature_outside', 'humidity_outside'}.issubset(out_data.columns):
            out_data['absolute_humidity'] = _vector_abs_humidity(out_data['temperature_outside'], out_data['humidity_outside'])
        if {'temperature_ds18b20', 'humidity_dht11'}.issubset(lr_data.columns):
            lr_data['absolute_humidity'] = _vector_abs_humidity(lr_data['temperature_ds18b20'], lr_data['humidity_dht11'])

        # Downsample each to similar density and align to a reference
        # Use the first dataset as reference after its own downsampling
        bed_ds, comp_bed = resample_downsample(bed_data)
        ref_index = bed_ds.index
        out_ds, comp_out = resample_downsample(out_data, reference_index=ref_index)
        pico_ds, comp_pico = resample_downsample(pico_data, reference_index=ref_index)
        lr_ds, comp_lr = resample_downsample(lr_data, reference_index=ref_index)
        bme_ds, comp_bme = resample_downsample(bme680_data, reference_index=ref_index)

        print(f"[INFO] Downsample compression ratios - Bed:{comp_bed:.2f}x Out:{comp_out:.2f}x Pico:{comp_pico:.2f}x LR:{comp_lr:.2f}x BME:{comp_bme:.2f}x")

        # Basic stats log for a small subset
        stats = _basic_stats(bed_ds, [c for c in ['temperature', 'humidity', 'pressure', 'gas_resistance', 'co2'] if c in bed_ds.columns])
        if stats:
            print(f"[INFO] BedRoom basic stats: {stats}")

        plt.clf()
        x_start = pd.to_datetime(start_time) if start_time else bed_ds.index.min()
        x_end = bed_ds.index.max()

        # =====================
        # Gas normalization (expanding mean)
        # =====================
        if 'gas_resistance' in bed_ds.columns:
            bed_ds['gas_resistance_avg'] = bed_ds['gas_resistance'].expanding().mean()
            bed_ds['gas_resistance_norm'] = bed_ds['gas_resistance'] / bed_ds['gas_resistance_avg'].shift(1).fillna(1)
        if 'gas_resistance_outside' in out_ds.columns:
            out_ds['gas_resistance_avg'] = out_ds['gas_resistance_outside'].expanding().mean()
            out_ds['gas_resistance_norm'] = out_ds['gas_resistance_outside'] / out_ds['gas_resistance_avg'].shift(1).fillna(1)
        if 'analog_value' in lr_ds.columns:
            lr_ds['analog_value_avg'] = lr_ds['analog_value'].expanding().mean()
            lr_ds['analog_value_norm'] = lr_ds['analog_value'] / lr_ds['analog_value_avg'].shift(1).fillna(1)
        if 'gas_resistance' in bme_ds.columns:
            bme_ds['gas_resistance_avg'] = bme_ds['gas_resistance'].expanding().mean()
            bme_ds['gas_resistance_norm'] = bme_ds['gas_resistance'] / bme_ds['gas_resistance_avg'].shift(1).fillna(1)

        # =====================
        # Subplots
        # =====================
        ax1 = create_subplot(1, 6, ref_index, {
            'CO2': bed_ds['co2'] if 'co2' in bed_ds.columns else pd.Series(index=ref_index, dtype=float),
            'CO2_LR': lr_ds['co2'] if 'co2' in lr_ds.columns else pd.Series(index=ref_index, dtype=float)
        }, ['BedRoom', 'DiningRoom'], ['c', 'k'], ['solid', 'solid'], 'CO2',
           y_scales.get('CO2') if y_scales else None)

        ax2 = create_subplot(2, 6, ref_index, {
            'BedRoom Temperature': (bed_ds['temperature'] if 'temperature' in bed_ds.columns else (bed_ds['tempereture'] if 'tempereture' in bed_ds.columns else pd.Series(index=ref_index, dtype=float))),
            'Outside Temperature': out_ds['temperature_outside'] if 'temperature_outside' in out_ds.columns else pd.Series(index=ref_index, dtype=float),
            'Outside Temperature-2': pico_ds['tempereture'] if 'tempereture' in pico_ds.columns else (pico_ds['temperature'] if 'temperature' in pico_ds.columns else pd.Series(index=ref_index, dtype=float)),
            'temp_C_Sensor2': lr_ds['temperature_ds18b20'] if 'temperature_ds18b20' in lr_ds.columns else pd.Series(index=ref_index, dtype=float),
            'Desk_temp': bme_ds['temperature'] if 'temperature' in bme_ds.columns else pd.Series(index=ref_index, dtype=float)
        }, ['BedRoom', 'Outside1', 'Outside2', 'DiningRoom Temp.', 'Desk'], ['c', 'r', 'blue', 'k', 'blue'],
           ['solid', 'dashed', 'solid', 'dotted', 'dashdot'], 'Temperature', y_scales.get('Temperature') if y_scales else None, sharex=ax1)

        ax3 = create_subplot(3, 6, ref_index, {
            'BedRoom Humidity': bed_ds['humidity'] if 'humidity' in bed_ds.columns else pd.Series(index=ref_index, dtype=float),
            'Outside Humidity': out_ds['humidity_outside'] if 'humidity_outside' in out_ds.columns else pd.Series(index=ref_index, dtype=float),
            'Humid_LR': lr_ds['humidity_dht11'] if 'humidity_dht11' in lr_ds.columns else pd.Series(index=ref_index, dtype=float),
            'Desk_humidity': bme_ds['humidity'] if 'humidity' in bme_ds.columns else pd.Series(index=ref_index, dtype=float)
        }, ['BedRoom', 'Outside', 'Dining', 'Desk'], ['c', 'r', 'k', 'blue'], ['solid', 'dashed', 'dashdot', 'solid'],
           'Humidity', y_scales.get('Humidity') if y_scales else None, sharex=ax1)

        ax4 = create_subplot(4, 6, ref_index, {
            'BedRoom Pressure': bed_ds['pressure'] if 'pressure' in bed_ds.columns else pd.Series(index=ref_index, dtype=float),
            'Outside Pressure': out_ds['pressure_outside'] if 'pressure_outside' in out_ds.columns else pd.Series(index=ref_index, dtype=float),
            'Desk_pressure': bme_ds['pressure'] if 'pressure' in bme_ds.columns else pd.Series(index=ref_index, dtype=float)
        }, ['BedRoom', 'Outside', 'Desk'], ['c', 'r', 'blue'], ['solid', 'dashed', 'solid'], 'Pressure',
           y_scales.get('Pressure') if y_scales else None, sharex=ax1)

        ax5 = create_subplot(5, 6, ref_index, {
            'Absolute Humidity - BedRoom': bed_ds['absolute_humidity'] if 'absolute_humidity' in bed_ds.columns else pd.Series(index=ref_index, dtype=float),
            'Absolute Humidity - Outside': out_ds['absolute_humidity'] if 'absolute_humidity' in out_ds.columns else pd.Series(index=ref_index, dtype=float),
            'Absolute Humidity - DiningRoom': lr_ds['absolute_humidity'] if 'absolute_humidity' in lr_ds.columns else pd.Series(index=ref_index, dtype=float),
            'Desk Absolute Humidity': bme_ds['absolute_humidity'] if 'absolute_humidity' in bme_ds.columns else pd.Series(index=ref_index, dtype=float)
        }, ['BedRoom', 'Outside', 'DiningRoom', 'Desk'], ['c', 'r', 'k', 'blue'], ['solid', 'dashed', '-.', 'solid'],
           'Absolute Humidity (g/m³)', y_scales.get('Absolute Humidity') if y_scales else None, sharex=ax1)

        ax6 = create_subplot(6, 6, ref_index, {
            'BedRoom GasResistance Normalized': bed_ds['gas_resistance_norm'] if 'gas_resistance_norm' in bed_ds.columns else pd.Series(index=ref_index, dtype=float),
            'Outside GasResistance Normalized': out_ds['gas_resistance_norm'] if 'gas_resistance_norm' in out_ds.columns else pd.Series(index=ref_index, dtype=float),
            'Gas_LR Normalized': lr_ds['analog_value_norm'] if 'analog_value_norm' in lr_ds.columns else pd.Series(index=ref_index, dtype=float),
            'Desk_gas Normalized': bme_ds['gas_resistance_norm'] if 'gas_resistance_norm' in bme_ds.columns else pd.Series(index=ref_index, dtype=float)
        }, ['BedRoom', 'Outside', 'DiningRoom', 'Desk'], ['c', 'r', 'k', 'blue'], ['solid', 'dashed', 'solid', 'dotted'],
           'GasResistance Normalized', y_scales.get('GasResistance Normalized') if y_scales else None, sharex=ax1)

        plt.xlim(x_start, x_end)
        plt.tight_layout()
        plt.draw()
        plt.pause(PLOT_REFRESH_SEC)


if __name__ == '__main__':
    plot_data(
        start_time="2025-08-20 00:00:00",
        y_scales={
            'CO2': (400, 1000),
            'Temperature': (17, 40),
            'Humidity': (20, 100),
            'Pressure': (970, 1015),
            'GasResistance': (10000, 150000),
            'GasResistance Normalized': (0, 3),
            'Absolute Humidity': (8, 25),
        }
    )

import os
import re
import time
import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# =========================
# Logger setup
# =========================
logger = logging.getLogger("Graph10X")
if not logger.handlers:
    handler = logging.StreamHandler()
    fmt = logging.Formatter('[%(levelname)s] %(message)s')
    handler.setFormatter(fmt)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Matplotlib style
plt.style.use('default')

# =========================
# Configurable parameters
# =========================
MAX_POINTS = 2000         # target max points per line for plotting (auto downsampling)
AGG_METHOD = 'mean'       # 'mean'|'median'|'min'|'max'
USE_PARQUET = False       # optional fast IO sidecar
USE_FEATHER = False       # optional fast IO sidecar (exclusive with parquet)
PLOT_REFRESH_SEC = 80
DROP_WARN_THRESHOLD = 0.10  # 10%

# CSV inputs and needed columns per file (original headers as they appear on disk)
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

# =========================
# Normalization rules
# =========================
# 1) Canonical name map (after delimiter normalization to underscore)
COLMAP_BASE = {
    'tempereture': 'temperature',
    'temperature-outside': 'temperature_outside',
    'temperature outside': 'temperature_outside',
    'temperature_outside': 'temperature_outside',
    'humidity-outside': 'humidity_outside',
    'humidity outside': 'humidity_outside',
    'humidity_outside': 'humidity_outside',
    'pressure-outside': 'pressure_outside',
    'pressure outside': 'pressure_outside',
    'pressure_outside': 'pressure_outside',
    'gasresistance-outside': 'gas_resistance_outside',
    'gasresistance outside': 'gas_resistance_outside',
    'gas_resistance-outside': 'gas_resistance_outside',
    'gas_resistance outside': 'gas_resistance_outside',
    'gasresistance_outside': 'gas_resistance_outside',
    'temperature_ds18b20': 'temperature_ds18b20',
    'humidity_dht11': 'humidity_dht11',
    'analogvalue': 'analog_value',
    'gasresistance': 'gas_resistance',
    'desk_temp': 'temperature',
    'desk_humidity': 'humidity',
    'desk_pressure': 'pressure',
}

# 2) Alias sets (expanded as requested)
ALIASES: Dict[str, List[str]] = {
    'temperature': ["temperature", "tempereture", "temp", "desk_temp", "temperature_inside"],
    'humidity': ["humidity", "humid", "desk_humidity", "humidity_dht11"],
    'pressure': ["pressure", "press", "desk_pressure", "pressure_outside"],
    'gas_resistance': ["gas_resistance", "gasresistance", "gas_resistance_outside", "analogvalue", "analog_value"],
    'co2': ["co2", "co₂", "co2_ppm"],
}

# Suffix variants to include for sub systems
SUFFIX_VARIANTS = ["_outside", "_ds18b20", "_inside"]

# Numeric dtype hints (for cleansing)
NUMERIC_COLS = {
    'co2', 'temperature', 'temperature_outside', 'temperature_ds18b20',
    'humidity', 'humidity_outside', 'humidity_dht11',
    'pressure', 'pressure_outside',
    'gas_resistance', 'gas_resistance_outside',
    'analog_value', 'absolute_humidity'
}

# Cache for incremental reads
_FILE_CACHE: Dict[str, Dict] = {}

# =========================
# Helpers: normalization & parsing
# =========================
_fullwidth_map = {ord('０'): '0', ord('１'): '1', ord('２'): '2', ord('３'): '3', ord('４'): '4',
                  ord('５'): '5', ord('６'): '6', ord('７'): '7', ord('８'): '8', ord('９'): '9',
                  ord('－'): '-', ord('／'): '/', ord('：'): ':', ord('．'): '.', ord('＋'): '+',
                  ord('，'): ',', ord('　'): ' '}  # ideographic space

def normalize_col_token(token: str) -> str:
    s = (token or '').strip().lower()
    # unify delimiters to underscore
    s = re.sub(r'[\s\-]+', '_', s)
    s = re.sub(r'__+', '_', s)
    s = s.strip('_')
    return s

def build_alias_map() -> Dict[str, str]:
    m: Dict[str, str] = {}
    # base map
    for k, v in COLMAP_BASE.items():
        m[normalize_col_token(k)] = v
    # aliases
    for canonical, names in ALIASES.items():
        for nm in names:
            m[normalize_col_token(nm)] = canonical
            # suffix variants
            for suf in SUFFIX_VARIANTS:
                m[normalize_col_token(nm + suf)] = canonical + suf
    return m

ALIAS_MAP = build_alias_map()

def normalize_columns_collision_safe(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str], List[str]]:
    """
    Normalize column names:
    - trim/lower/unify delimiters
    - map via ALIAS_MAP to canonical names
    - avoid collisions: if two columns map to same canonical name, keep first, skip later and log
    Returns: (df_renamed, rename_map_used, skipped_original_columns)
    """
    rename_map: Dict[str, str] = {}
    used: set = set()
    skipped: List[str] = []
    for c in df.columns:
        norm = normalize_col_token(c)
        mapped = ALIAS_MAP.get(norm, norm)
        if mapped in used:
            logger.warning(f"Column collision on '{mapped}' from original '{c}', skipping this column")
            skipped.append(c)
            continue
        rename_map[c] = mapped
        used.add(mapped)
    df2 = df.rename(columns=rename_map)
    # Drop skipped originals if they remained
    if skipped:
        df2 = df2.drop(columns=[c for c in skipped if c in df2.columns], errors='ignore')
    return df2, rename_map, skipped

# =========================
# Datetime tolerant parsing
# =========================

def preprocess_datetime_series(s: pd.Series) -> pd.Series:
    # to string, strip, full-width -> half-width, unify '/'
    s2 = s.astype(str).str.strip()
    s2 = s2.str.translate(_fullwidth_map)
    s2 = s2.str.replace('/', '-', regex=False)
    return s2

def parse_datetime_tolerant(s: pd.Series) -> Tuple[pd.Series, int, List[str]]:
    """Return parsed datetime Series, dropped_count, sample_bad_values"""
    s_pre = preprocess_datetime_series(s)
    # Try numeric epoch (s or ms)
    num = pd.to_numeric(s_pre, errors='coerce')
    parsed = None
    if num.notna().mean() > 0.6:  # likely numeric epoch
        # Decide unit by magnitude
        median_val = num.dropna().median()
        if median_val > 1e12:
            parsed = pd.to_datetime(num, unit='ms', errors='coerce', utc=False)
        else:
            parsed = pd.to_datetime(num, unit='s', errors='coerce', utc=False)
    else:
        # Try ISO/known formats with timezone support
        parsed = pd.to_datetime(s_pre, errors='coerce', utc=False, infer_datetime_format=True)
        # As fallback, try explicit common formats
        if parsed.isna().mean() > 0.4:
            fmts = [
                '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y/%m/%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d %H:%M:%S%z',
            ]
            for fmt in fmts:
                trial = pd.to_datetime(s_pre, format=fmt, errors='coerce', utc=False)
                if trial.notna().sum() > parsed.notna().sum():
                    parsed = trial
    bad_mask = parsed.isna()
    bad_count = int(bad_mask.sum())
    samples = s_pre[bad_mask].head(5).tolist() if bad_count else []
    return parsed, bad_count, samples

# =========================
# Numeric cleansing with units
# =========================
UNIT_PATTERNS = [
    (re.compile(r'\s*°c', re.IGNORECASE), ''),
    (re.compile(r'\s*%', re.IGNORECASE), ''),
    (re.compile(r'\s*hpa', re.IGNORECASE), ''),
    (re.compile(r'\s*ppm', re.IGNORECASE), ''),
    (re.compile(r'\s*ohm', re.IGNORECASE), ''),
    (re.compile(r'\s*ω', re.IGNORECASE), ''),
    (re.compile(r'\s*Ω'), ''),
]

K_MULTIPLIERS = [
    (re.compile(r'\s*kΩ', re.IGNORECASE), 1000.0),
    (re.compile(r'\s*kohm', re.IGNORECASE), 1000.0),
    (re.compile(r'\s*k$', re.IGNORECASE), 1000.0),
]

def clean_numeric_series(s: pd.Series) -> Tuple[pd.Series, int, int]:
    """Clean units/commas/NA text and convert to float. Returns (series, unit_hits, k_hits)."""
    unit_hits = 0
    k_hits = 0
    x = s.astype(str).str.strip().str.translate(_fullwidth_map).str.lower()
    # normalize null tokens
    x = x.replace({'': np.nan, 'na': np.nan, 'nan': np.nan, 'null': np.nan, 'none': np.nan})
    # commas removal
    x = x.str.replace(',', '', regex=False)
    # k-multipliers: replace marker, then multiply after to_numeric
    k_mask = pd.Series(False, index=x.index)
    for pat, mult in K_MULTIPLIERS:
        mk = x.str.contains(pat)
        if mk.any():
            k_hits += int(mk.sum())
            x = x.str.replace(pat, '', regex=True)
            k_mask = k_mask | mk
    # generic units removal
    for pat, _ in UNIT_PATTERNS:
        hit = x.str.contains(pat)
        if hit.any():
            unit_hits += int(hit.sum())
            x = x.str.replace(pat, '', regex=True)
    vals = pd.to_numeric(x, errors='coerce')
    vals.loc[k_mask & vals.notna()] = vals.loc[k_mask & vals.notna()] * 1000.0
    return vals.astype(float), unit_hits, k_hits

# Range validation per column
RANGE_RULES = {
    'humidity': (0, 100),
    'humidity_outside': (0, 100),
    'temperature': (-40, 85),
    'temperature_outside': (-50, 85),
    'temperature_ds18b20': (-55, 125),
    'pressure': (800, 1100),
    'pressure_outside': (800, 1100),
    'co2': (0, 5000),
    'gas_resistance': (0, np.inf),
    'gas_resistance_outside': (0, np.inf),
    'absolute_humidity': (0, 50),
}

def range_check(df: pd.DataFrame) -> Dict[str, int]:
    warn_counts: Dict[str, int] = {}
    for col, (lo, hi) in RANGE_RULES.items():
        if col in df.columns:
            s = df[col]
            bad = ((s < lo) | (s > hi)) & s.notna()
            cnt = int(bad.sum())
            if cnt:
                warn_counts[col] = cnt
                logger.warning(f"Abnormal values in '{col}': {cnt} samples outside [{lo}, {hi}]")
    return warn_counts

# =========================
# IO helpers (incremental read)
# =========================

def _sidecar_path(csv_path: str) -> str:
    if USE_PARQUET:
        return os.path.splitext(csv_path)[0] + '.parquet'
    if USE_FEATHER:
        return os.path.splitext(csv_path)[0] + '.feather'
    return ''


def _drop_duplicate_headers_and_blank(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Drop duplicate header rows and all-blank rows."""
    before = len(df)
    # all-blank rows: all NaN or empty strings
    df2 = df.replace(r'^\s*$', np.nan, regex=True)
    df2 = df2.dropna(how='all')
    # duplicate header rows: if a row equals the column names after normalization attempt
    # A simple heuristic: if any row value equals its column name string (case-insensitive) for many columns
    mask = pd.Series(False, index=df2.index)
    cols_lower = [str(c).lower() for c in df2.columns]
    for idx, row in df2.iterrows():
        row_vals = [str(v).strip().lower() for v in row.values]
        # if > half match, consider it a header row
        matches = sum(1 for v, c in zip(row_vals, cols_lower) if v == c)
        if matches >= max(2, len(cols_lower)//2):
            mask.loc[idx] = True
    if mask.any():
        df2 = df2.loc[~mask]
    dropped = before - len(df2)
    return df2, dropped


def _normalize_pipeline(df: pd.DataFrame, date_column_original: str, file_path: str) -> pd.DataFrame:
    # 1) collision-safe column normalization
    df, rename_map, skipped = normalize_columns_collision_safe(df)

    # 2) remove header duplicates / blanks
    df, dup_drop = _drop_duplicate_headers_and_blank(df)
    if dup_drop:
        logger.info(f"{os.path.basename(file_path)}: removed {dup_drop} duplicate/blank rows")

    # 3) datetime tolerant parsing
    date_guess = normalize_col_token(date_column_original)
    # after rename_map, determine the actual column name
    # prefer exact mapped name if exists, else try original
    date_col = None
    for cand in [date_guess, date_column_original, 'timestamp', 'date', 'time']:
        if cand in df.columns:
            date_col = cand
            break
    if date_col is None:
        raise KeyError(f"Date column '{date_column_original}' not found in {file_path}")

    parsed_dt, bad_count, samples = parse_datetime_tolerant(df[date_col])
    if bad_count:
        frac = bad_count / max(1, len(df))
        sample_str = "; ".join(map(str, samples))
        level = logging.WARNING if frac >= DROP_WARN_THRESHOLD else logging.INFO
        logger.log(level, f"{os.path.basename(file_path)}: dropped {bad_count} rows (rate {frac:.1%}) due to invalid datetime. Samples: {sample_str}")
    df[date_col] = parsed_dt
    df = df.dropna(subset=[date_col])
    df = df.set_index(date_col).sort_index()

    # 4) numeric cleansing on numeric-like columns
    total_unit_hits = 0
    total_k_hits = 0
    for col in list(df.columns):
        if col in NUMERIC_COLS:
            cleaned, unit_hits, k_hits = clean_numeric_series(df[col])
            total_unit_hits += unit_hits
            total_k_hits += k_hits
            df[col] = cleaned
    if total_unit_hits or total_k_hits:
        logger.info(f"{os.path.basename(file_path)}: unit removals={total_unit_hits}, k-mults={total_k_hits}")

    # 5) range checks
    range_warns = range_check(df)
    if range_warns:
        total_bad = sum(range_warns.values())
        logger.warning(f"{os.path.basename(file_path)}: abnormal-range samples total={total_bad} details={range_warns}")

    return df


def _read_csv_incremental(file_path: str, date_column: str, usecols: Optional[List[str]] = None) -> pd.DataFrame:
    """Incremental CSV reader with caching and robust normalization.
    - Uses file size/mtime and previous row count to only read appended rows when possible.
    - Always applies normalization pipeline after loading/merging.
    - Uses optional parquet/feather sidecar on full reloads.
    """
    st = os.stat(file_path)
    size, mtime = st.st_size, st.st_mtime
    cache = _FILE_CACHE.get(file_path)

    # unchanged -> return cached df
    if cache and cache.get('mtime') == mtime and cache.get('size') == size:
        return cache['df']

    sidecar = _sidecar_path(file_path)
    full_reload = True
    prev_rows = 0
    if cache:
        prev_rows = cache.get('rows', 0)
        if size > cache.get('size', 0) and prev_rows > 0:
            full_reload = False

    # Build usecols (ensure date column included)
    cols = list(usecols) if usecols else None
    if cols and date_column not in cols:
        cols = [date_column] + cols

    if not full_reload:
        try:
            df_new = pd.read_csv(
                file_path,
                usecols=cols,
                skiprows=range(1, prev_rows + 1),
                low_memory=False,
            )
        except Exception:
            df_new = None
            full_reload = True
        if df_new is not None and len(df_new) > 0:
            df_all = pd.concat([cache['raw'].reset_index(drop=True), df_new], ignore_index=True)
        else:
            # nothing appended
            _FILE_CACHE[file_path] = {
                'df': cache['df'], 'raw': cache['raw'], 'rows': cache['rows'], 'size': size, 'mtime': mtime
            }
            return cache['df']
    if full_reload:
        if sidecar and os.path.exists(sidecar):
            try:
                if USE_PARQUET:
                    df_all = pd.read_parquet(sidecar)
                elif USE_FEATHER:
                    df_all = pd.read_feather(sidecar)
                else:
                    df_all = pd.read_csv(file_path, usecols=cols, low_memory=False)
            except Exception:
                df_all = pd.read_csv(file_path, usecols=cols, low_memory=False)
        else:
            df_all = pd.read_csv(file_path, usecols=cols, low_memory=False)

    # Apply normalization pipeline (this covers header duplicates, datetime, numeric cleansing, range checks)
    df_norm = _normalize_pipeline(df_all, date_column, file_path)

    # Update sidecar on full reload for faster subsequent loads
    if full_reload and sidecar:
        try:
            if USE_PARQUET:
                df_norm.reset_index().to_parquet(sidecar, index=False)
            elif USE_FEATHER:
                df_norm.reset_index().to_feather(sidecar)
        except Exception:
            pass

    # Update cache
    _FILE_CACHE[file_path] = {
        'df': df_norm,
        'raw': df_all,
        'rows': len(df_all),
        'size': size,
        'mtime': mtime,
    }
    return df_norm

# =========================
# Analytics
# =========================

def _vector_abs_humidity(temp: pd.Series, rh: pd.Series) -> pd.Series:
    T = temp.astype(float)
    RH = rh.astype(float)
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        ah = (6.112 * np.exp((17.67 * T) / (T + 243.5)) * RH * 2.1674) / (273.15 + T)
    return pd.Series(ah, index=temp.index)

# Absolute humidity input pair resolution
AH_PAIR_PRIORITY = [
    ("temperature", "humidity"),
    ("temperature_outside", "humidity_outside"),
    ("temperature_ds18b20", "humidity_dht11"),
]

def ensure_absolute_humidity(df: pd.DataFrame, label: str) -> None:
    if 'absolute_humidity' in df.columns:
        return
    for t_col, h_col in AH_PAIR_PRIORITY:
        if t_col in df.columns and h_col in df.columns:
            df['absolute_humidity'] = _vector_abs_humidity(df[t_col], df[h_col])
            return
    logger.info(f"{label}: absolute humidity skipped (no suitable temperature/humidity pair found)")

# =========================
# Downsampling / resampling
# =========================

def _auto_resample_rule(index: pd.DatetimeIndex, max_points: int) -> Optional[str]:
    if len(index) <= max_points:
        return None
    total_seconds = (index.max() - index.min()).total_seconds()
    if total_seconds <= 0:
        return None
    sec_per_point = max(1, int(total_seconds / max_points))
    return f"{sec_per_point}s"  # lower-case as requested


def resample_downsample(df: pd.DataFrame, max_points: int = MAX_POINTS, agg: str = AGG_METHOD,
                        reference_index: Optional[pd.DatetimeIndex] = None) -> Tuple[pd.DataFrame, float]:
    original_points = len(df)
    if original_points == 0:
        return df, 1.0
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
        df_ds = df_ds.reindex(reference_index, method='nearest')
    compression = (original_points / max(1, len(df_ds))) if len(df_ds) else 1.0
    return df_ds, compression

# =========================
# Plotting
# =========================

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

# =========================
# Main loop
# =========================

def plot_data(start_time: Optional[str] = None, y_scales: Optional[Dict[str, Tuple[float, float]]] = None):
    plt.figure()

    while True:
        datasets = []
        for file, date_col in DATA_FILES:
            usecols = REQUIRED_COLS.get(file)
            df = _read_csv_incremental(file, date_col, usecols=usecols)
            datasets.append(df)

        # Unpack
        bed_data, out_data, pico_data, lr_data, bme680_data = datasets

        # Absolute humidity per dataset using priority pairs
        ensure_absolute_humidity(bed_data, 'BedRoom')
        ensure_absolute_humidity(out_data, 'Outside')
        ensure_absolute_humidity(lr_data, 'DiningRoom')
        ensure_absolute_humidity(bme680_data, 'Desk')

        # Downsample and align
        bed_ds, comp_bed = resample_downsample(bed_data)
        ref_index = bed_ds.index
        out_ds, comp_out = resample_downsample(out_data, reference_index=ref_index)
        pico_ds, comp_pico = resample_downsample(pico_data, reference_index=ref_index)
        lr_ds, comp_lr = resample_downsample(lr_data, reference_index=ref_index)
        bme_ds, comp_bme = resample_downsample(bme680_data, reference_index=ref_index)

        logger.info(f"Compression ratios - Bed:{comp_bed:.2f}x Out:{comp_out:.2f}x Pico:{comp_pico:.2f}x LR:{comp_lr:.2f}x BME:{comp_bme:.2f}x")

        plt.clf()
        x_start = pd.to_datetime(start_time) if start_time else bed_ds.index.min()
        x_end = bed_ds.index.max()

        # Gas normalization (expanding mean)
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

        # Subplots
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

# =========================
# Entry point
# =========================
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

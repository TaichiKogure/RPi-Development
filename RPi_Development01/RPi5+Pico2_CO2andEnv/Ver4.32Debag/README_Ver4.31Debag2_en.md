# Ver4.31 Debug 2 - Improvements to Graph Rendering and Data Logging

## Changes Made

### Issues Identified
1. Graph scales and plots always starting at 0
   - Even with dynamic Y-axis range settings, `fig.add_trace(...)` might not be receiving actual values properly.

2. Data ranges not clearly displayed
   - Data ranges (min, max) were not being logged, making problem diagnosis difficult.

3. Historical data being cached, preventing display of latest data
   - The `get_historical_data()` method was using cached data, which sometimes prevented the latest data from being displayed.

### Fixes Implemented

1. Improvements to the `get_historical_data()` method
   - Disabled caching to always load the latest data from files
   - Added file-specific logging to clearly show which files are being read

2. Data range logging
   - Added logging of P2 and P3 data ranges (timestamp min/max, parameter min/max)
   - This makes it easier to identify why graphs might not be rendering correctly

## Technical Details

### 1. Cache Invalidation

```python
def get_historical_data(self, device_id, days=1):
    # ...
    force_reload = True  # Always reload data from files
    
    # Only use cache if caching is enabled and cache is still valid
    if not force_reload and self.data_cache[device_id] is not None:
        # ...
```

### 2. File Reading Logs

```python
file_path = os.path.join(full_dir, f"{device_id}_{date_str}.csv")
if os.path.exists(file_path):
    logger.info(f"Reading historical data for {device_id} from file: {file_path}")
    try:
        df = pd.read_csv(file_path)
        # ...
```

### 3. Data Range Logging

```python
# Log data ranges
if df_p2 is not None and not df_p2.empty and parameter in df_p2.columns:
    logger.info(f"P2[{parameter}] from {df_p2['timestamp'].min()} to {df_p2['timestamp'].max()} range: {df_p2[parameter].min()} – {df_p2[parameter].max()}")

if df_p3 is not None and not df_p3.empty and parameter in df_p3.columns:
    logger.info(f"P3[{parameter}] from {df_p3['timestamp'].min()} to {df_p3['timestamp'].max()} range: {df_p3[parameter].min()} – {df_p3[parameter].max()}")
```

## Usage

These changes provide the following improvements:

1. Graphs will always display the latest data
2. The log file (`/var/log/web_interface_solo.log`) will contain data ranges, making problem diagnosis easier
3. The logs will show which files are being read, making it easier to identify data source issues

Switching the UI day selection ("1 Day" → "7 Day" → "1 Day") will force the cache to reload, ensuring the latest data is displayed.
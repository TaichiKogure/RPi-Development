# Ver4.25.5 Debug - Fixes and Improvements

## Overview
This version addresses the following issues with the P1 data collection and visualization system:

1. **Timestamp Conversion Issue**:
   - Fixed the issue where timestamp columns were not being converted to datetime format
   - Implemented forced conversion using `pd.to_datetime()` and handling of invalid values

2. **Identical P2 and P3 Graphs Issue**:
   - Fixed data caching problems
   - Modified the code to return copies of cached data to prevent modifications to the original data

3. **Connection Status Display Issue**:
   - Fixed integration with the connection monitor API
   - Modified the API endpoint to directly call the connection monitor API

## Detailed Fixes

### 1. Timestamp Conversion Issue

Enhanced the timestamp conversion process in the `get_historical_data` function:

```python
# Before
combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])

# After
combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'], errors='coerce')
combined_df = combined_df.dropna(subset=['timestamp'])
```

These changes:
- Add the `errors='coerce'` parameter to set invalid values to NaT (Not a Time)
- Remove rows with invalid timestamps to prevent errors during graph plotting

### 2. Identical P2 and P3 Graphs Issue

Improved the data caching process:

```python
# Before
self.data_cache[device_id] = (datetime.datetime.now(), combined_df)
return combined_df

# After
self.data_cache[device_id] = (datetime.datetime.now(), combined_df.copy())
return combined_df.copy()
```

These changes:
- Create a copy of the data before storing it in the cache to prevent modifications to the original data
- Return a copy of the data when retrieving from the cache

Also added debug logging to facilitate problem diagnosis:

```python
logger.info(f"Getting historical data for {device_id}, days={days}")
logger.info(f"Using cached data for {device_id}, {len(df)} rows")
logger.info(f"Caching data for {device_id}, {len(combined_df)} rows")
```

### 3. Connection Status Display Issue

Fixed the connection status API endpoint:

```python
# Before
@app.route('/api/connection/status')
def get_connection_status():
    """API endpoint to get the connection status."""
    return jsonify(visualizer.get_connection_status())

# After
@app.route('/api/connection/status')
def get_connection_status():
    """API endpoint to get the connection status."""
    try:
        # Try to get connection status from the API
        response = requests.get(f"{visualizer.config['monitor_api_url']}/api/connection/latest", timeout=2)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            logger.warning(f"Failed to get connection status: {response.status_code}")
            return jsonify({})
    except Exception as e:
        logger.error(f"Error getting connection status: {e}")
        return jsonify({})
```

These changes:
- Directly call the connection monitor API to correctly retrieve connection status information
- Enhance error handling to properly respond even when the API is unavailable

## Added Debug Logging

Added the following debug logs to facilitate diagnosis of the graph creation process:

```python
logger.info(f"Creating time series graph for {parameter}, days={days}, show_p2={show_p2}, show_p3={show_p3}")
logger.info(f"P2 data: {df_p2 is not None and not df_p2.empty}, P3 data: {df_p3 is not None and not df_p3.empty}")
logger.info(f"Adding P2 data for {parameter}, {len(df_p2)} rows, timestamp type: {type(df_p2['timestamp'].iloc[0])}")
```

This allows for checking data retrieval status and timestamp types.

## Notes

- These fixes are applied only to the P1 web interface
- Please ensure that the connection monitor API is functioning correctly
- Verify that the data directory structure (RawData_P2, RawData_P3) is correctly configured
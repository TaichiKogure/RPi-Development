# API Endpoints Logging Update

## Overview

This document describes the changes made to address the issue where sensor data was not being updated and graphs were not being drawn. The issue was that the `/api/graphs` endpoint was not being logged, making it difficult to diagnose why the graphs were not being displayed.

## Changes Made

### 1. Added Logging to the `/api/graphs` Endpoint

Logging was added to the `/api/graphs` endpoint in the `routes.py` file to track when it's being called and what data it's returning:

```python
@self.app.route('/api/graphs', methods=['GET'])
def get_graph_data_csv():
    """Get structured data for graphs using GraphGenerator."""
    try:
        # Get query parameters
        days = request.args.get('days', default=1, type=int)
        show_p2 = request.args.get('show_p2', default='true').lower() == 'true'
        show_p3 = request.args.get('show_p3', default='true').lower() == 'true'

        logger.info(f"Received request for /api/graphs with days={days}, show_p2={show_p2}, show_p3={show_p3}")

        # Use GraphGenerator to get structured data
        result = self.graph_generator.generate_graph_data(days=days, show_p2=show_p2, show_p3=show_p3)

        logger.info(f"Generated graph data with keys: {list(result.keys())}")

        return jsonify(result)
    except Exception as e:
        logger.error(f"Graph data generation failed: {e}")
        return jsonify({"error": str(e)}), 500
```

This will log:
- When a request is received for the `/api/graphs` endpoint
- The query parameters (days, show_p2, show_p3)
- The keys in the result (which should include "P2" and/or "P3" if data was found)

### 2. Added Extensive Logging to the `get_historical_data` Method

Extensive logging was added to the `get_historical_data` method in the `data_manager.py` file to track file paths and data loading:

```python
def get_historical_data(self, device_id, days=1):
    """
    Get historical data for the specified device.

    Args:
        device_id (str): The device ID to get data for
        days (int, optional): Number of days of data to retrieve. Defaults to 1.

    Returns:
        pandas.DataFrame: The historical data
    """
    try:
        # Check if we have cached data
        with self.lock:
            if self.data_cache[device_id] is not None:
                logger.info(f"Using cached data for {device_id}")
                return self.data_cache[device_id]

        # Determine the appropriate directory for the device
        device_dir = self.config["rawdata_p2_dir"] if device_id == "P2" else self.config["rawdata_p3_dir"]
        logger.info(f"Looking for {device_id} data in directory: {device_dir}")

        # Calculate the cutoff date
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
        logger.info(f"Cutoff date for {device_id} data: {cutoff_date}")

        # Try to read the fixed CSV file first
        fixed_csv_path = os.path.join(self.config["data_dir"], device_dir, f"{device_id}_fixed.csv")
        logger.info(f"Checking for fixed CSV file: {fixed_csv_path}")
        if os.path.exists(fixed_csv_path):
            logger.info(f"Fixed CSV file found for {device_id}: {fixed_csv_path}")
            try:
                df = pd.read_csv(fixed_csv_path)
                logger.info(f"Read {len(df)} rows from fixed CSV file for {device_id}")
                if not df.empty:
                    # Convert timestamp to datetime
                    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                    logger.info(f"Converted timestamp to datetime for {device_id}")

                    # Filter by date
                    df = df[df['timestamp'] >= cutoff_date]
                    logger.info(f"Filtered data by date for {device_id}, {len(df)} rows remaining")

                    # Cache the data
                    with self.lock:
                        self.data_cache[device_id] = df

                    return df
            except Exception as e:
                logger.error(f"Error reading fixed CSV file for {device_id}: {e}")
        else:
            logger.warning(f"Fixed CSV file not found for {device_id}: {fixed_csv_path}")

        # If fixed file doesn't exist or is empty, try the date-based files
        # ... (similar logging for date-based files)
```

This will log:
- The directory where the method is looking for data
- The cutoff date for filtering data
- The path of the fixed CSV file it's checking for
- Whether the fixed CSV file was found
- How many rows were read from the fixed CSV file
- Whether the timestamp column was successfully converted to datetime
- How many rows remain after filtering by date
- Similar information for date-based files

## Testing

To test these changes, you can:

1. Start the web interface
2. Open the dashboard in a web browser
3. Check the logs for messages related to the `/api/graphs` endpoint and the `get_historical_data` method
4. Verify that the graphs are displayed correctly

## Expected Results

With these changes, you should see log messages that help diagnose why the graphs might not be being displayed. Possible issues that might be revealed include:

1. The CSV files are not being found (you'll see warnings like "Fixed CSV file not found for P2: /var/lib/raspap_solo/data/RawData_P2/P2_fixed.csv")
2. The CSV files are being found but are empty (you'll see messages like "Read 0 rows from fixed CSV file for P2")
3. The timestamp column is not being converted to datetime correctly (you'll see errors related to this)
4. The data is being filtered out by the cutoff date (you'll see messages like "Filtered data by date for P2, 0 rows remaining")

By examining the logs, you should be able to determine why the graphs are not being displayed and take appropriate action to fix the issue.
# GraphGenerator Update

## Overview

This document describes the changes made to address the issue where sensor data was not being updated and graphs were not being drawn. The issue was that the GraphGenerator class was not correctly finding the CSV files because they were in a different location than expected.

## Issue Description

The GraphGenerator class was using the DataManager.get_historical_data method to retrieve data for graphs, but this method was not correctly finding the CSV files. The CSV files are located in the RawData_P2 and RawData_P3 directories, but the code was looking for them directly in the data directory.

## Solution

The GraphGenerator.generate_graph_data method was modified to implement a load_latest_fixed_csv function that looks for *_fixed.csv files in the RawData_P2 and RawData_P3 directories, selects the latest one based on modification time, and loads it into a DataFrame.

## Implementation Details

### 1. Added Missing Imports

Added imports for os, datetime, and pandas at the top of the file:

```python
import os
import logging
import json
import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
```

### 2. Modified generate_graph_data Method

The generate_graph_data method was modified to use the load_latest_fixed_csv function instead of the DataManager.get_historical_data method:

```python
def generate_graph_data(self, days=1, show_p2=True, show_p3=True):
    """
    Generate structured data for graphs.

    Args:
        days (int, optional): Number of days of data to retrieve. Defaults to 1.
        show_p2 (bool, optional): Whether to include P2 data. Defaults to True.
        show_p3 (bool, optional): Whether to include P3 data. Defaults to True.

    Returns:
        dict: Structured data for graphs
    """
    try:
        # Calculate the cutoff date
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
        logger.info(f"Cutoff date for data: {cutoff}")

        def load_latest_fixed_csv(device_id):
            """
            Load the latest fixed CSV file for the specified device.
            
            Args:
                device_id (str): The device ID to load data for (P2 or P3)
                
            Returns:
                pandas.DataFrame: The loaded data, or None if no data found
            """
            # Determine the appropriate directory for the device
            device_dir = "RawData_P2" if device_id == "P2" else "RawData_P3"
            folder = os.path.join(self.config["data_dir"], device_dir)
            logger.info(f"Looking for fixed CSVs in: {folder}")
            
            # Check if the directory exists
            if not os.path.isdir(folder):
                logger.warning(f"Directory not found: {folder}")
                return None
            
            # Find all *_fixed.csv files in the directory
            candidates = [f for f in os.listdir(folder) if f.endswith("_fixed.csv")]
            if not candidates:
                logger.warning(f"No _fixed.csv files in {folder}")
                return None
            
            # Get the latest file based on modification time
            latest_file = max(candidates, key=lambda f: os.path.getmtime(os.path.join(folder, f)))
            logger.info(f"Latest fixed CSV file for {device_id}: {latest_file}")
            
            try:
                # Read the CSV file
                file_path = os.path.join(folder, latest_file)
                logger.info(f"Reading CSV file: {file_path}")
                df = pd.read_csv(file_path)
                logger.info(f"Read {len(df)} rows from {file_path}")
                
                if not df.empty:
                    # Convert timestamp to datetime
                    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                    logger.info(f"Converted timestamp to datetime for {device_id}")
                    
                    # Filter by date
                    df = df[df['timestamp'] > cutoff]
                    logger.info(f"Filtered data by date for {device_id}, {len(df)} rows remaining")
                    
                    return df
                else:
                    logger.warning(f"CSV file is empty: {file_path}")
                    return None
            except Exception as e:
                logger.error(f"Error loading {latest_file}: {e}")
                return None
        
        # Load data for P2 and P3
        df_p2 = load_latest_fixed_csv("P2") if show_p2 else None
        df_p3 = load_latest_fixed_csv("P3") if show_p3 else None
```

## Testing

To test these changes, you can:

1. Start the web interface
2. Open the dashboard in a web browser
3. Check the logs for messages related to the GraphGenerator.generate_graph_data method
4. Verify that the graphs are displayed correctly

## Expected Results

With these changes, the GraphGenerator class should be able to correctly find and load the CSV files from the RawData_P2 and RawData_P3 directories, and the graphs should be displayed correctly on the dashboard.

## Conclusion

These changes should resolve the issue where sensor data was not being updated and graphs were not being drawn. The GraphGenerator class now correctly looks for CSV files in the RawData_P2 and RawData_P3 directories, and the graphs should be displayed correctly on the dashboard.
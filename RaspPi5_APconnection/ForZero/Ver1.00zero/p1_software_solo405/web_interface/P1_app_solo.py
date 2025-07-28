#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi 5 Environmental Data Web Interface for Solo Version
Version: 4.0.0-solo

This module provides a web interface for visualizing environmental data
collected from P2 and P3 sensor nodes with BME680 and MH-Z19C sensors. It displays real-time data,
historical trends, and allows for data export.

Features:
- Real-time display of current sensor readings from both P2 and P3 (including CO2)
- Time-series graphs of historical data with flexible Y-axis ranges
- Toggle options to show/hide P2 and P3 data on the same graph
- Display of absolute humidity calculated from temperature and humidity
- Data export in CSV format
- Responsive design for mobile and desktop viewing
- Auto-refresh functionality
- Real-time signal strength display for both P2 and P3

Requirements:
- Python 3.7+
- Flask for the web server
- Pandas for data manipulation
- Plotly for interactive graphs

Usage:
    python3 P1_app_solo.py [--port PORT] [--data-dir DIR]
"""

import os
import sys
import time
import json
import argparse
import logging
import datetime
import threading
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_file, Response
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/web_interface_solo.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "web_port": 80,
    "data_dir": "/var/lib(FromThonny)/raspap_solo/data",
    "rawdata_p2_dir": "RawData_P2",
    "rawdata_p3_dir": "RawData_P3",
    "api_url": "http://localhost:5001",
    "monitor_api_url": "http://localhost:5002",
    "refresh_interval": 10,  # seconds
    "graph_points": 100,  # number of data points to show in graphs
    "debug_mode": False
}

# Initialize Flask app
app = Flask(__name__)

class DataVisualizer:
    """Class to handle data visualization and processing."""

    def __init__(self, config=None):
        """Initialize the data visualizer with the given configuration."""
        self.config = config or DEFAULT_CONFIG.copy()
        self.last_data = {}
        self.data_cache = {"P2": None, "P3": None}
        self.lock = threading.Lock()

        # Ensure the data directories exist
        os.makedirs(self.config["data_dir"], exist_ok=True)
        os.makedirs(os.path.join(self.config["data_dir"], self.config["rawdata_p2_dir"]), exist_ok=True)
        os.makedirs(os.path.join(self.config["data_dir"], self.config["rawdata_p3_dir"]), exist_ok=True)

    def get_latest_data(self):
        """Get the latest data from the API or cached data."""
        try:
            # In a real implementation, this would call the API
            # For now, we'll simulate by reading the latest data from CSV files
            with self.lock:
                latest_data = self.last_data.copy()

            if not latest_data or len(latest_data) < 2:  # Check if we have data for both P2 and P3
                # If no data in cache, try to read from CSV
                today = datetime.datetime.now().strftime("%Y-%m-%d")

                for device in ["P2", "P3"]:
                    # Determine the appropriate directory for each device
                    device_dir = self.config["rawdata_p2_dir"] if device == "P2" else self.config["rawdata_p3_dir"]
                    csv_path = os.path.join(self.config["data_dir"], device_dir, f"{device}_{today}.csv")

                    if os.path.exists(csv_path):
                        try:
                            df = pd.read_csv(csv_path)
                            if not df.empty:
                                latest_row = df.iloc[-1].to_dict()
                                latest_data[device] = latest_row
                        except Exception as e:
                            logger.error(f"Error reading CSV for {device}: {e}")

            return latest_data
        except Exception as e:
            logger.error(f"Error getting latest data: {e}")
            return {}

    def get_connection_status(self):
        """Get the connection status from the connection monitor API."""
        try:
            # Try to get connection status from the API
            response = requests.get(f"{self.config['monitor_api_url']}/api/connection/latest", timeout=2)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to get connection status: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"Error getting connection status: {e}")
            return {}

    def get_historical_data(self, device_id, days=1):
        """Get historical data for the specified device."""
        import pandas as pd
        import datetime
        import os

        if device_id not in ["P2", "P3", "P4", "P5", "P6"]:
            return None

        logger.info(f"Getting historical data for {device_id}, days={days}")

        force_reload = True  # Always reload data from files

        # Check if we have cached data and it's still valid
        if not force_reload and self.data_cache[device_id] is not None:
            cache_time, df = self.data_cache[device_id]
            if (datetime.datetime.now() - cache_time).total_seconds() < 60:  # Cache for 1 minute
                logger.info(f"Using cached data for {device_id}, {len(df)} rows")
                return df.copy()  # Return a copy to prevent modifications to the cached data

        # Explicitly specify the data directories
        if device_id == "P2":
            full_dir = "/var/lib(FromThonny)/raspap_solo/data/RawData_P2"
        elif device_id == "P3":
            full_dir = "/var/lib(FromThonny)/raspap_solo/data/RawData_P3"
        elif device_id == "P4":
            full_dir = "/var/lib(FromThonny)/raspap_solo/data/RawData_P4"
        elif device_id == "P5":
            full_dir = "/var/lib(FromThonny)/raspap_solo/data/RawData_P5"
        else:  # P6
            full_dir = "/var/lib(FromThonny)/raspap_solo/data/RawData_P6"
        if not os.path.exists(full_dir):
            logger.warning(f"Directory not found: {full_dir}")
            return None

        # First try to read from the fixed file
        fixed_file_path = os.path.join(full_dir, f"{device_id}_fixed.csv")
        if os.path.exists(fixed_file_path):
            logger.info(f"Reading historical data for {device_id} from fixed file: {fixed_file_path}")
            try:
                df = pd.read_csv(fixed_file_path)
                # Check timestamp data type and convert appropriately
                if df['timestamp'].dtype == 'int64' or df['timestamp'].dtype == 'float64':
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
                else:
                    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                df = df.dropna(subset=['timestamp'])

                # Limit to the last N points for performance
                if len(df) > self.config["graph_points"]:
                    df = df.tail(self.config["graph_points"])

                # Cache the result
                logger.info(f"Caching data for {device_id} from fixed file, {len(df)} rows")
                self.data_cache[device_id] = (datetime.datetime.now(), df.copy())

                return df.copy()
            except Exception as e:
                logger.error(f"Failed to read fixed CSV {fixed_file_path}: {e}")
                logger.info(f"Falling back to date-based files for {device_id}")
                # Fall back to date-based files
        else:
            logger.warning(f"Fixed file not found for {device_id}: {fixed_file_path}")
            logger.info(f"Falling back to date-based files for {device_id}")

        # If we couldn't read from the fixed file, try date-based files
        end_date = datetime.datetime.now().date()
        date_list = [(end_date - datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]

        frames = []
        for date_str in date_list:
            file_path = os.path.join(full_dir, f"{device_id}_{date_str}.csv")
            if os.path.exists(file_path):
                logger.info(f"Reading historical data for {device_id} from file: {file_path}")
                try:
                    df = pd.read_csv(file_path)
                    # Check timestamp data type and convert appropriately
                    if df['timestamp'].dtype == 'int64' or df['timestamp'].dtype == 'float64':
                        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
                    else:
                        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                    df = df.dropna(subset=['timestamp'])
                    frames.append(df)
                except Exception as e:
                    logger.error(f"Failed to read CSV {file_path}: {e}")

        if not frames:
            logger.warning(f"No data found for {device_id} in the specified date range")
            return None

        df_all = pd.concat(frames, ignore_index=True)
        df_all.sort_values(by='timestamp', inplace=True)

        # Limit to the last N points for performance
        if len(df_all) > self.config["graph_points"]:
            df_all = df_all.tail(self.config["graph_points"])

        # Cache the result
        logger.info(f"Caching data for {device_id} from date-based files, {len(df_all)} rows")
        self.data_cache[device_id] = (datetime.datetime.now(), df_all.copy())

        return df_all.copy()

    def create_time_series_graph(self, parameter, days=1, show_p2=True, show_p3=True, show_p4=True, show_p5=True, show_p6=True):
        """Create a time series graph for the specified parameter with data from all sensor nodes."""
        logger.info(f"Creating time series graph for {parameter}, days={days}, show_p2={show_p2}, show_p3={show_p3}, show_p4={show_p4}, show_p5={show_p5}, show_p6={show_p6}")

        # Get data for all devices
        df_p2 = self.get_historical_data("P2", days) if show_p2 else None
        df_p3 = self.get_historical_data("P3", days) if show_p3 else None
        df_p4 = self.get_historical_data("P4", days) if show_p4 else None
        df_p5 = self.get_historical_data("P5", days) if show_p5 else None
        df_p6 = self.get_historical_data("P6", days) if show_p6 else None

        # Ensure timestamps are properly converted to datetime
        if df_p2 is not None and not df_p2.empty and 'timestamp' in df_p2.columns:
            # Check timestamp data type and convert appropriately
            if df_p2['timestamp'].dtype == 'int64' or df_p2['timestamp'].dtype == 'float64':
                df_p2['timestamp'] = pd.to_datetime(df_p2['timestamp'], unit='s', errors='coerce')
            else:
                df_p2['timestamp'] = pd.to_datetime(df_p2['timestamp'], errors='coerce')
            df_p2 = df_p2.dropna(subset=['timestamp'])

        if df_p3 is not None and not df_p3.empty and 'timestamp' in df_p3.columns:
            # Check timestamp data type and convert appropriately
            if df_p3['timestamp'].dtype == 'int64' or df_p3['timestamp'].dtype == 'float64':
                df_p3['timestamp'] = pd.to_datetime(df_p3['timestamp'], unit='s', errors='coerce')
            else:
                df_p3['timestamp'] = pd.to_datetime(df_p3['timestamp'], errors='coerce')
            df_p3 = df_p3.dropna(subset=['timestamp'])
            
        if df_p4 is not None and not df_p4.empty and 'timestamp' in df_p4.columns:
            # Check timestamp data type and convert appropriately
            if df_p4['timestamp'].dtype == 'int64' or df_p4['timestamp'].dtype == 'float64':
                df_p4['timestamp'] = pd.to_datetime(df_p4['timestamp'], unit='s', errors='coerce')
            else:
                df_p4['timestamp'] = pd.to_datetime(df_p4['timestamp'], errors='coerce')
            df_p4 = df_p4.dropna(subset=['timestamp'])
            
        if df_p5 is not None and not df_p5.empty and 'timestamp' in df_p5.columns:
            # Check timestamp data type and convert appropriately
            if df_p5['timestamp'].dtype == 'int64' or df_p5['timestamp'].dtype == 'float64':
                df_p5['timestamp'] = pd.to_datetime(df_p5['timestamp'], unit='s', errors='coerce')
            else:
                df_p5['timestamp'] = pd.to_datetime(df_p5['timestamp'], errors='coerce')
            df_p5 = df_p5.dropna(subset=['timestamp'])
            
        if df_p6 is not None and not df_p6.empty and 'timestamp' in df_p6.columns:
            # Check timestamp data type and convert appropriately
            if df_p6['timestamp'].dtype == 'int64' or df_p6['timestamp'].dtype == 'float64':
                df_p6['timestamp'] = pd.to_datetime(df_p6['timestamp'], unit='s', errors='coerce')
            else:
                df_p6['timestamp'] = pd.to_datetime(df_p6['timestamp'], errors='coerce')
            df_p6 = df_p6.dropna(subset=['timestamp'])

        # Log data availability
        logger.info(f"P2 data: {df_p2 is not None and not df_p2.empty}, P3 data: {df_p3 is not None and not df_p3.empty}, P4 data: {df_p4 is not None and not df_p4.empty}, P5 data: {df_p5 is not None and not df_p5.empty}, P6 data: {df_p6 is not None and not df_p6.empty}")

        # Log data ranges for debugging
        if df_p2 is not None and not df_p2.empty and parameter in df_p2.columns:
            logger.info(f"P2[{parameter}] from {df_p2['timestamp'].min()} to {df_p2['timestamp'].max()} range: {df_p2[parameter].min()} – {df_p2[parameter].max()}")

        if df_p3 is not None and not df_p3.empty and parameter in df_p3.columns:
            logger.info(f"P3[{parameter}] from {df_p3['timestamp'].min()} to {df_p3['timestamp'].max()} range: {df_p3[parameter].min()} – {df_p3[parameter].max()}")
            
        if df_p4 is not None and not df_p4.empty and parameter in df_p4.columns:
            logger.info(f"P4[{parameter}] from {df_p4['timestamp'].min()} to {df_p4['timestamp'].max()} range: {df_p4[parameter].min()} – {df_p4[parameter].max()}")
            
        if df_p5 is not None and not df_p5.empty and parameter in df_p5.columns:
            logger.info(f"P5[{parameter}] from {df_p5['timestamp'].min()} to {df_p5['timestamp'].max()} range: {df_p5[parameter].min()} – {df_p5[parameter].max()}")
            
        if df_p6 is not None and not df_p6.empty and parameter in df_p6.columns:
            logger.info(f"P6[{parameter}] from {df_p6['timestamp'].min()} to {df_p6['timestamp'].max()} range: {df_p6[parameter].min()} – {df_p6[parameter].max()}")

        # Check if we have any data
        if (df_p2 is None or df_p2.empty) and (df_p3 is None or df_p3.empty) and (df_p4 is None or df_p4.empty) and (df_p5 is None or df_p5.empty) and (df_p6 is None or df_p6.empty):
            logger.warning(f"No data available for {parameter}")
            return None

        try:
            # Create a new figure
            fig = go.Figure()

            # Check for valid data points (at least 2 unique non-NaN values)
            p2_valid = False
            p3_valid = False
            y_min = None
            y_max = None

            # Validate P2 data
            if show_p2 and df_p2 is not None and not df_p2.empty and parameter in df_p2.columns:
                # Check for at least 2 unique non-NaN values
                p2_unique = df_p2[parameter].dropna().unique()
                if len(p2_unique) >= 2:
                    p2_valid = True
                    # Update min/max for Y-axis scaling
                    p2_min = df_p2[parameter].min()
                    p2_max = df_p2[parameter].max()
                    y_min = p2_min if y_min is None else min(y_min, p2_min)
                    y_max = p2_max if y_max is None else max(y_max, p2_max)

                    logger.info(f"Adding P2 data for {parameter}, {len(df_p2)} rows, unique values: {len(p2_unique)}")
                    fig.add_trace(go.Scatter(
                        x=df_p2['timestamp'],
                        y=df_p2[parameter],
                        mode='lines',
                        name=f'P2 {parameter.capitalize()}',
                        line=dict(color='blue')
                    ))
                else:
                    logger.warning(f"P2 data for {parameter} has fewer than 2 unique values: {p2_unique}")
            else:
                logger.warning(f"Not adding P2 data for {parameter}: show_p2={show_p2}, df_p2 exists={df_p2 is not None}, df_p2 not empty={not df_p2.empty if df_p2 is not None else False}, parameter in columns={parameter in df_p2.columns if df_p2 is not None else False}")

            # Validate P3 data
            if show_p3 and df_p3 is not None and not df_p3.empty and parameter in df_p3.columns:
                # Check for at least 2 unique non-NaN values
                p3_unique = df_p3[parameter].dropna().unique()
                if len(p3_unique) >= 2:
                    p3_valid = True
                    # Update min/max for Y-axis scaling
                    p3_min = df_p3[parameter].min()
                    p3_max = df_p3[parameter].max()
                    y_min = p3_min if y_min is None else min(y_min, p3_min)
                    y_max = p3_max if y_max is None else max(y_max, p3_max)

                    logger.info(f"Adding P3 data for {parameter}, {len(df_p3)} rows, unique values: {len(p3_unique)}")
                    fig.add_trace(go.Scatter(
                        x=df_p3['timestamp'],
                        y=df_p3[parameter],
                        mode='lines',
                        name=f'P3 {parameter.capitalize()}',
                        line=dict(color='red')
                    ))
                else:
                    logger.warning(f"P3 data for {parameter} has fewer than 2 unique values: {p3_unique}")
            else:
                logger.warning(f"Not adding P3 data for {parameter}: show_p3={show_p3}, df_p3 exists={df_p3 is not None}, df_p3 not empty={not df_p3.empty if df_p3 is not None else False}, parameter in columns={parameter in df_p3.columns if df_p3 is not None else False}")
                
            # Validate P4 data
            p4_valid = False
            if show_p4 and df_p4 is not None and not df_p4.empty and parameter in df_p4.columns:
                # Check for at least 2 unique non-NaN values
                p4_unique = df_p4[parameter].dropna().unique()
                if len(p4_unique) >= 2:
                    p4_valid = True
                    # Update min/max for Y-axis scaling
                    p4_min = df_p4[parameter].min()
                    p4_max = df_p4[parameter].max()
                    y_min = p4_min if y_min is None else min(y_min, p4_min)
                    y_max = p4_max if y_max is None else max(y_max, p4_max)

                    logger.info(f"Adding P4 data for {parameter}, {len(df_p4)} rows, unique values: {len(p4_unique)}")
                    fig.add_trace(go.Scatter(
                        x=df_p4['timestamp'],
                        y=df_p4[parameter],
                        mode='lines',
                        name=f'P4 {parameter.capitalize()}',
                        line=dict(color='green')
                    ))
                else:
                    logger.warning(f"P4 data for {parameter} has fewer than 2 unique values: {p4_unique}")
            else:
                logger.warning(f"Not adding P4 data for {parameter}: show_p4={show_p4}, df_p4 exists={df_p4 is not None}, df_p4 not empty={not df_p4.empty if df_p4 is not None else False}, parameter in columns={parameter in df_p4.columns if df_p4 is not None else False}")
                
            # Validate P5 data
            p5_valid = False
            if show_p5 and df_p5 is not None and not df_p5.empty and parameter in df_p5.columns:
                # Check for at least 2 unique non-NaN values
                p5_unique = df_p5[parameter].dropna().unique()
                if len(p5_unique) >= 2:
                    p5_valid = True
                    # Update min/max for Y-axis scaling
                    p5_min = df_p5[parameter].min()
                    p5_max = df_p5[parameter].max()
                    y_min = p5_min if y_min is None else min(y_min, p5_min)
                    y_max = p5_max if y_max is None else max(y_max, p5_max)

                    logger.info(f"Adding P5 data for {parameter}, {len(df_p5)} rows, unique values: {len(p5_unique)}")
                    fig.add_trace(go.Scatter(
                        x=df_p5['timestamp'],
                        y=df_p5[parameter],
                        mode='lines',
                        name=f'P5 {parameter.capitalize()}',
                        line=dict(color='purple')
                    ))
                else:
                    logger.warning(f"P5 data for {parameter} has fewer than 2 unique values: {p5_unique}")
            else:
                logger.warning(f"Not adding P5 data for {parameter}: show_p5={show_p5}, df_p5 exists={df_p5 is not None}, df_p5 not empty={not df_p5.empty if df_p5 is not None else False}, parameter in columns={parameter in df_p5.columns if df_p5 is not None else False}")
                
            # Validate P6 data
            p6_valid = False
            if show_p6 and df_p6 is not None and not df_p6.empty and parameter in df_p6.columns:
                # Check for at least 2 unique non-NaN values
                p6_unique = df_p6[parameter].dropna().unique()
                if len(p6_unique) >= 2:
                    p6_valid = True
                    # Update min/max for Y-axis scaling
                    p6_min = df_p6[parameter].min()
                    p6_max = df_p6[parameter].max()
                    y_min = p6_min if y_min is None else min(y_min, p6_min)
                    y_max = p6_max if y_max is None else max(y_max, p6_max)

                    logger.info(f"Adding P6 data for {parameter}, {len(df_p6)} rows, unique values: {len(p6_unique)}")
                    fig.add_trace(go.Scatter(
                        x=df_p6['timestamp'],
                        y=df_p6[parameter],
                        mode='lines',
                        name=f'P6 {parameter.capitalize()}',
                        line=dict(color='orange')
                    ))
                else:
                    logger.warning(f"P6 data for {parameter} has fewer than 2 unique values: {p6_unique}")
            else:
                logger.warning(f"Not adding P6 data for {parameter}: show_p6={show_p6}, df_p6 exists={df_p6 is not None}, df_p6 not empty={not df_p6.empty if df_p6 is not None else False}, parameter in columns={parameter in df_p6.columns if df_p6 is not None else False}")

            # If no dataset is valid, return None
            if not p2_valid and not p3_valid and not p4_valid and not p5_valid and not p6_valid:
                logger.warning(f"No valid data available for {parameter} graph (need at least 2 unique values)")
                return None

            # Set title and labels
            yaxis_config = {}

            # Set Y-axis range if we have valid min/max values
            if y_min is not None and y_max is not None:
                # Add a small padding (5%) to make the graph look better
                y_range = y_max - y_min
                padding = y_range * 0.05 if y_range > 0 else 1
                yaxis_config['range'] = [y_min - padding, y_max + padding]
                logger.info(f"Setting Y-axis range for {parameter}: {yaxis_config['range']}")
            else:
                # Fallback to auto-range
                yaxis_config['autorange'] = True
                yaxis_config['rangemode'] = 'normal'

            fig.update_layout(
                title=f"{parameter.capitalize()} over time",
                xaxis_title="Time",
                yaxis_title=parameter.capitalize(),
                margin=dict(l=20, r=20, t=40, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                hovermode='closest',
                yaxis=yaxis_config,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )

            # Check if fig.data is empty (no traces were added)
            if not fig.data:
                logger.warning(f"No valid data to plot for {parameter}")
                return json.dumps({"error": f"No valid data to plot for {parameter}"})

            return fig.to_json()
        except Exception as e:
            logger.error(f"Error creating graph for {parameter}: {e}")
            return json.dumps({"error": f"Graph creation failed: {e}"})

    def create_dashboard_graphs(self, days=1, show_p2=True, show_p3=True, show_p4=True, show_p5=True, show_p6=True):
        """Create all graphs for the dashboard, including absolute humidity."""
        parameters = ['temperature', 'humidity', 'pressure', 'gas_resistance', 'co2', 'absolute_humidity']
        graphs = {}
        errors = {}

        for param in parameters:
            graph_json = self.create_time_series_graph(param, days, show_p2, show_p3, show_p4, show_p5, show_p6)
            if graph_json:
                # Check if the result is an error message
                try:
                    graph_data = json.loads(graph_json)
                    if isinstance(graph_data, dict) and "error" in graph_data:
                        # This is an error message
                        errors[param] = graph_data["error"]
                        logger.warning(f"Error creating graph for {param}: {graph_data['error']}")
                    else:
                        # This is a valid graph
                        graphs[param] = graph_json
                except json.JSONDecodeError:
                    # If we can't parse the JSON, assume it's a valid graph
                    graphs[param] = graph_json

        # If we have no graphs but have errors, return the errors
        if not graphs and errors:
            return {"errors": errors}

        return graphs

    def export_csv(self, device_id, start_date, end_date):
        """Export data to CSV for the specified date range."""
        if device_id not in ["P2", "P3", "P4", "P5", "P6", "all"]:
            return None

        try:
            # Parse dates
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")

            # Determine which devices to export
            devices = []
            if device_id == "all":
                devices = ["P2", "P3", "P4", "P5", "P6"]
            else:
                devices = [device_id]

            all_data_frames = []

            # Process each device
            for device in devices:
                # Determine the appropriate directory for the device
                if device == "P2":
                    device_dir = self.config["rawdata_p2_dir"]
                elif device == "P3":
                    device_dir = self.config["rawdata_p3_dir"]
                elif device == "P4":
                    device_dir = self.config["rawdata_p4_dir"]
                elif device == "P5":
                    device_dir = self.config["rawdata_p5_dir"]
                else:  # P6
                    device_dir = self.config["rawdata_p6_dir"]

                # Get list of CSV files in date range
                data_frames = []
                current_date = start_date
                while current_date <= end_date:
                    date_str = current_date.strftime("%Y-%m-%d")
                    csv_path = os.path.join(self.config["data_dir"], device_dir, f"{device}_{date_str}.csv")

                    if os.path.exists(csv_path):
                        try:
                            df = pd.read_csv(csv_path)
                            data_frames.append(df)
                        except Exception as e:
                            logger.error(f"Error reading CSV {csv_path}: {e}")

                    current_date += datetime.timedelta(days=1)

                # Combine all data frames for this device
                if data_frames:
                    device_df = pd.concat(data_frames, ignore_index=True)
                    all_data_frames.append(device_df)

            # Combine data from all devices
            if all_data_frames:
                combined_df = pd.concat(all_data_frames, ignore_index=True)

                # Create a temporary file for download
                temp_file = os.path.join(self.config["data_dir"], f"export_{device_id}_{int(time.time())}.csv")
                combined_df.to_csv(temp_file, index=False)

                return temp_file
            else:
                logger.warning(f"No data found for {device_id} in the specified date range")
                return None
        except Exception as e:
            logger.error(f"Error exporting CSV for {device_id}: {e}")
            return None

# Create a global instance of the data visualizer
visualizer = None

@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html', 
                          refresh_interval=visualizer.config["refresh_interval"],
                          last_update=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@app.route('/dashboard')
def dashboard():
    """Render the dashboard for all devices."""
    days = request.args.get('days', default=1, type=int)
    show_p2 = request.args.get('show_p2', default='true').lower() == 'true'
    show_p3 = request.args.get('show_p3', default='true').lower() == 'true'
    show_p4 = request.args.get('show_p4', default='true').lower() == 'true'
    show_p5 = request.args.get('show_p5', default='true').lower() == 'true'
    show_p6 = request.args.get('show_p6', default='true').lower() == 'true'

    return render_template('dashboard.html',
                          days=days,
                          show_p2=show_p2,
                          show_p3=show_p3,
                          show_p4=show_p4,
                          show_p5=show_p5,
                          show_p6=show_p6,
                          refresh_interval=visualizer.config["refresh_interval"],
                          last_update=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@app.route('/api/latest')
def get_latest_data():
    """API endpoint to get the latest data."""
    return jsonify(visualizer.get_latest_data())

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

@app.route('/api/device/<device_id>')
def get_device_data(device_id):
    """API endpoint to get data for a specific device."""
    if device_id not in ["P2", "P3", "P4", "P5", "P6"]:
        return jsonify({"error": "Invalid device ID"}), 400

    latest_data = visualizer.get_latest_data()

    if device_id in latest_data:
        return jsonify(latest_data[device_id])
    else:
        return jsonify({"error": "No data available for this device"}), 404

@app.route('/api/graphs')
def get_graphs():
    """API endpoint to get graphs for all devices."""
    days = request.args.get('days', default=1, type=int)
    show_p2 = request.args.get('show_p2', default='true').lower() == 'true'
    show_p3 = request.args.get('show_p3', default='true').lower() == 'true'
    show_p4 = request.args.get('show_p4', default='true').lower() == 'true'
    show_p5 = request.args.get('show_p5', default='true').lower() == 'true'
    show_p6 = request.args.get('show_p6', default='true').lower() == 'true'

    graphs = visualizer.create_dashboard_graphs(days, show_p2, show_p3, show_p4, show_p5, show_p6)

    if not graphs:
        return jsonify({"error": "No data available for graphs"}), 404

    # Check if the result contains errors
    if isinstance(graphs, dict) and "errors" in graphs:
        # Return the errors with a 400 status code
        return jsonify(graphs), 400

    # Return the graphs
    return jsonify(graphs)

@app.route('/api/export/<device_id>')
def export_data(device_id):
    """API endpoint to export data for a specific device or all devices."""
    if device_id not in ["P2", "P3", "P4", "P5", "P6", "all"]:
        return jsonify({"error": "Invalid device ID"}), 400

    start_date = request.args.get('start_date', default=(datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d"))
    end_date = request.args.get('end_date', default=datetime.datetime.now().strftime("%Y-%m-%d"))

    csv_file = visualizer.export_csv(device_id, start_date, end_date)

    if csv_file:
        return send_file(csv_file, 
                        mimetype='text/csv',
                        as_attachment=True,
                        download_name=f"{device_id}_data_{start_date}_to_{end_date}.csv")
    else:
        return jsonify({"error": "No data available for export"}), 404

def create_templates():
    """Create the HTML templates for the web interface."""
    # Create templates directory
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    os.makedirs(templates_dir, exist_ok=True)

    # Create base template
    base_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Environmental Data Monitor - Solo{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <style>
        body {
            padding-top: 20px;
            background-color: #f5f5f5;
        }
        .card {
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .card-header {
            background-color: #007bff;
            color: white;
            font-weight: bold;
        }
        .navbar {
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        .data-value {
            font-size: 24px;
            font-weight: bold;
        }
        .data-unit {
            font-size: 14px;
            color: #6c757d;
        }
        .last-update {
            font-size: 12px;
            color: #6c757d;
            text-align: right;
            margin-top: 10px;
        }
        .graph-container {
            height: 300px;
            width: 100%;
        }
        .signal-strength {
            display: flex;
            align-items: center;
            margin-top: 10px;
        }
        .signal-bar {
            width: 5px;
            margin-right: 2px;
            background-color: #ccc;
            border-radius: 1px;
        }
        .signal-bar.active {
            background-color: #28a745;
        }
        .signal-text {
            margin-left: 5px;
            font-size: 12px;
        }
        .device-toggle {
            margin-right: 15px;
        }
        .p2-color {
            color: blue;
        }
        .p3-color {
            color: red;
        }
    </style>
    {% block head %}{% endblock %}
</head>
<body>
    <div class="container">
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary rounded">
            <div class="container-fluid">
                <a class="navbar-brand" href="/">Environmental Data Monitor - Solo Ver 4.0</a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav">
                        <li class="nav-item">
                            <a class="nav-link" href="/">Home</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/dashboard">Dashboard</a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>

        {% block content %}{% endblock %}

        <footer class="mt-5 text-center text-muted">
            <p>Raspberry Pi 5 Environmental Data Monitor - Solo Version v4.0.0</p>
        </footer>
    </div>

    {% block scripts %}{% endblock %}
</body>
</html>
"""

    # Create index template
    index_html = """{% extends "base.html" %}

{% block title %}Environmental Data Monitor - Solo - Home{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <div class="card">
            <div class="card-header">
                System Overview
            </div>
            <div class="card-body">
                <p>Welcome to the Environmental Data Monitoring System - Solo Version 4.0. This interface allows you to view real-time and historical environmental data collected by the P2 and P3 sensor nodes with BME680 and MH-Z19C sensors.</p>
                <p>Select the dashboard below to view detailed information:</p>
                <div class="row mt-4">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">P2 Sensor Node</div>
                            <div class="card-body" id="p2-overview">
                                <div class="text-center" id="loading-p2-data">
                                    <div class="spinner-border text-primary" role="status">
                                        <span class="visually-hidden">Loading...</span>
                                    </div>
                                    <p>Loading data...</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">P3 Sensor Node</div>
                            <div class="card-body" id="p3-overview">
                                <div class="text-center" id="loading-p3-data">
                                    <div class="spinner-border text-primary" role="status">
                                        <span class="visually-hidden">Loading...</span>
                                    </div>
                                    <p>Loading data...</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="text-center mt-3">
                    <a href="/dashboard" class="btn btn-primary">View Dashboard</a>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="row mt-3">
    <div class="col-md-12">
        <div class="card">
            <div class="card-header">
                Connection Status
            </div>
            <div class="card-body" id="connection-status">
                <div class="text-center" id="loading-connection">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p>Loading connection data...</p>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="last-update">
    Last updated: <span id="last-update">{{ last_update }}</span>
</div>
{% endblock %}

{% block scripts %}
<script>
    // Function to update the overview data
    function updateOverview() {
        $.ajax({
            url: '/api/latest',
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                // Update P2 overview
                $('#loading-p2-data').hide();
                if (data.P2) {
                    var p2Html = `
                        <div class="row">
                            <div class="col-6 col-md-4">
                                <p>Temperature</p>
                                <p class="data-value">${parseFloat(data.P2.temperature).toFixed(1)}<span class="data-unit">°C</span></p>
                            </div>
                            <div class="col-6 col-md-4">
                                <p>Humidity</p>
                                <p class="data-value">${parseFloat(data.P2.humidity).toFixed(1)}<span class="data-unit">%</span></p>
                            </div>
                            <div class="col-6 col-md-4">
                                <p>Abs. Humidity</p>
                                <p class="data-value">${data.P2.absolute_humidity ? parseFloat(data.P2.absolute_humidity).toFixed(1) : "N/A"}<span class="data-unit">g/m³</span></p>
                            </div>
                        </div>
                        <div class="row mt-2">
                            <div class="col-6 col-md-4">
                                <p>Pressure</p>
                                <p class="data-value">${parseFloat(data.P2.pressure).toFixed(1)}<span class="data-unit">hPa</span></p>
                            </div>
                            <div class="col-6 col-md-4">
                                <p>CO2</p>
                                <p class="data-value">${data.P2.co2 ? parseFloat(data.P2.co2).toFixed(0) : "N/A"}<span class="data-unit">ppm</span></p>
                            </div>
                            <div class="col-6 col-md-4">
                                <p>Last Reading</p>
                                <p class="data-value">${data.P2.timestamp ? data.P2.timestamp.split(' ')[1] : "N/A"}</p>
                            </div>
                        </div>
                    `;
                    $('#p2-overview').html(p2Html);
                } else {
                    $('#p2-overview').html('<div class="alert alert-warning">No data available</div>');
                }

                // Update P3 overview
                $('#loading-p3-data').hide();
                if (data.P3) {
                    var p3Html = `
                        <div class="row">
                            <div class="col-6 col-md-4">
                                <p>Temperature</p>
                                <p class="data-value">${parseFloat(data.P3.temperature).toFixed(1)}<span class="data-unit">°C</span></p>
                            </div>
                            <div class="col-6 col-md-4">
                                <p>Humidity</p>
                                <p class="data-value">${parseFloat(data.P3.humidity).toFixed(1)}<span class="data-unit">%</span></p>
                            </div>
                            <div class="col-6 col-md-4">
                                <p>Abs. Humidity</p>
                                <p class="data-value">${data.P3.absolute_humidity ? parseFloat(data.P3.absolute_humidity).toFixed(1) : "N/A"}<span class="data-unit">g/m³</span></p>
                            </div>
                        </div>
                        <div class="row mt-2">
                            <div class="col-6 col-md-4">
                                <p>Pressure</p>
                                <p class="data-value">${parseFloat(data.P3.pressure).toFixed(1)}<span class="data-unit">hPa</span></p>
                            </div>
                            <div class="col-6 col-md-4">
                                <p>CO2</p>
                                <p class="data-value">${data.P3.co2 ? parseFloat(data.P3.co2).toFixed(0) : "N/A"}<span class="data-unit">ppm</span></p>
                            </div>
                            <div class="col-6 col-md-4">
                                <p>Last Reading</p>
                                <p class="data-value">${data.P3.timestamp ? data.P3.timestamp.split(' ')[1] : "N/A"}</p>
                            </div>
                        </div>
                    `;
                    $('#p3-overview').html(p3Html);
                } else {
                    $('#p3-overview').html('<div class="alert alert-warning">No data available</div>');
                }

                // Update last update time
                $('#last-update').text(new Date().toLocaleString());
            },
            error: function() {
                // Remove loading indicators and show error
                $('#loading-p2-data, #loading-p3-data').hide();
                $('#p2-overview, #p3-overview').html('<div class="alert alert-danger">Error loading data</div>');
            }
        });
    }

    // Function to update connection status
    function updateConnectionStatus() {
        $.ajax({
            url: '/api/connection/status',
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                // Remove loading indicator
                $('#loading-connection').hide();

                var html = '<div class="row">';

                // Check if we have P2 data
                if (data.P2 && data.P2.latest) {
                    var p2Data = data.P2.latest;
                    var status = p2Data.online ? "Online" : "Offline";
                    var statusClass = p2Data.online ? "text-success" : "text-danger";

                    // Calculate signal quality
                    var signalQuality = "Unknown";
                    var signalBars = 0;

                    if (p2Data.signal_strength) {
                        var signal = p2Data.signal_strength;
                        if (signal >= -50) {
                            signalQuality = "Excellent";
                            signalBars = 5;
                        } else if (signal >= -60) {
                            signalQuality = "Very Good";
                            signalBars = 4;
                        } else if (signal >= -70) {
                            signalQuality = "Good";
                            signalBars = 3;
                        } else if (signal >= -80) {
                            signalQuality = "Fair";
                            signalBars = 2;
                        } else {
                            signalQuality = "Poor";
                            signalBars = 1;
                        }
                    }

                    // Create signal bars HTML
                    var signalBarsHtml = '';
                    for (var i = 1; i <= 5; i++) {
                        var barHeight = i * 3 + 5; // 8px, 11px, 14px, 17px, 20px
                        var barClass = i <= signalBars ? 'active' : '';
                        signalBarsHtml += `<div class="signal-bar ${barClass}" style="height: ${barHeight}px;"></div>`;
                    }

                    html += `
                        <div class="col-md-6">
                            <h5 class="p2-color">P2 Sensor Node</h5>
                            <p>Status: <span class="${statusClass}">${status}</span></p>
                            <div class="signal-strength">
                                ${signalBarsHtml}
                                <span class="signal-text">${signalQuality} (${p2Data.signal_strength || 'N/A'} dBm)</span>
                            </div>
                            <p>Ping: ${p2Data.ping_time ? p2Data.ping_time.toFixed(2) + ' ms' : 'N/A'}</p>
                            <p>Noise Level: ${p2Data.noise_level || 'N/A'} dBm</p>
                        </div>
                    `;
                } else {
                    html += `
                        <div class="col-md-6">
                            <h5 class="p2-color">P2 Sensor Node</h5>
                            <div class="alert alert-warning">No connection data available</div>
                        </div>
                    `;
                }

                // Check if we have P3 data
                if (data.P3 && data.P3.latest) {
                    var p3Data = data.P3.latest;
                    var status = p3Data.online ? "Online" : "Offline";
                    var statusClass = p3Data.online ? "text-success" : "text-danger";

                    // Calculate signal quality
                    var signalQuality = "Unknown";
                    var signalBars = 0;

                    if (p3Data.signal_strength) {
                        var signal = p3Data.signal_strength;
                        if (signal >= -50) {
                            signalQuality = "Excellent";
                            signalBars = 5;
                        } else if (signal >= -60) {
                            signalQuality = "Very Good";
                            signalBars = 4;
                        } else if (signal >= -70) {
                            signalQuality = "Good";
                            signalBars = 3;
                        } else if (signal >= -80) {
                            signalQuality = "Fair";
                            signalBars = 2;
                        } else {
                            signalQuality = "Poor";
                            signalBars = 1;
                        }
                    }

                    // Create signal bars HTML
                    var signalBarsHtml = '';
                    for (var i = 1; i <= 5; i++) {
                        var barHeight = i * 3 + 5; // 8px, 11px, 14px, 17px, 20px
                        var barClass = i <= signalBars ? 'active' : '';
                        signalBarsHtml += `<div class="signal-bar ${barClass}" style="height: ${barHeight}px;"></div>`;
                    }

                    html += `
                        <div class="col-md-6">
                            <h5 class="p3-color">P3 Sensor Node</h5>
                            <p>Status: <span class="${statusClass}">${status}</span></p>
                            <div class="signal-strength">
                                ${signalBarsHtml}
                                <span class="signal-text">${signalQuality} (${p3Data.signal_strength || 'N/A'} dBm)</span>
                            </div>
                            <p>Ping: ${p3Data.ping_time ? p3Data.ping_time.toFixed(2) + ' ms' : 'N/A'}</p>
                            <p>Noise Level: ${p3Data.noise_level || 'N/A'} dBm</p>
                        </div>
                    `;
                } else {
                    html += `
                        <div class="col-md-6">
                            <h5 class="p3-color">P3 Sensor Node</h5>
                            <div class="alert alert-warning">No connection data available</div>
                        </div>
                    `;
                }

                html += '</div>';
                $('#connection-status').html(html);
            },
            error: function() {
                // Remove loading indicator and show error
                $('#loading-connection').hide();
                $('#connection-status').html('<div class="alert alert-danger">Error loading connection data</div>');
            }
        });
    }

    // Update data on page load
    $(document).ready(function() {
        updateOverview();
        updateConnectionStatus();

        // Set up auto-refresh
        setInterval(function() {
            updateOverview();
            updateConnectionStatus();
        }, {{ refresh_interval * 1000 }});
    });
</script>
{% endblock %}
"""

    # Create dashboard template
    dashboard_html = """{% extends "base.html" %}

{% block title %}Environmental Data Dashboard{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <span>Environmental Data Dashboard</span>
                <div class="btn-group" role="group">
                    <a href="/dashboard?days=1&show_p2={{ show_p2|lower }}&show_p3={{ show_p3|lower }}" class="btn btn-sm btn-outline-light {% if days == 1 %}active{% endif %}">1 Day</a>
                    <a href="/dashboard?days=7&show_p2={{ show_p2|lower }}&show_p3={{ show_p3|lower }}" class="btn btn-sm btn-outline-light {% if days == 7 %}active{% endif %}">1 Week</a>
                    <a href="/dashboard?days=30&show_p2={{ show_p2|lower }}&show_p3={{ show_p3|lower }}" class="btn btn-sm btn-outline-light {% if days == 30 %}active{% endif %}">1 Month</a>
                </div>
            </div>
            <div class="card-body">
                <div class="row mb-3">
                    <div class="col-md-12">
                        <div class="form-check form-check-inline device-toggle">
                            <input class="form-check-input" type="checkbox" id="show-p2" {% if show_p2 %}checked{% endif %}>
                            <label class="form-check-label p2-color" for="show-p2">Show P2 Data</label>
                        </div>
                        <div class="form-check form-check-inline device-toggle">
                            <input class="form-check-input" type="checkbox" id="show-p3" {% if show_p3 %}checked{% endif %}>
                            <label class="form-check-label p3-color" for="show-p3">Show P3 Data</label>
                        </div>
                        <button id="apply-filters" class="btn btn-sm btn-primary">Apply</button>
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-header">Current Readings</div>
                            <div class="card-body">
                                <ul class="nav nav-tabs" id="readings-tabs" role="tablist">
                                    <li class="nav-item" role="presentation">
                                        <button class="nav-link active" id="p2-tab" data-bs-toggle="tab" data-bs-target="#p2-readings" type="button" role="tab">P2</button>
                                    </li>
                                    <li class="nav-item" role="presentation">
                                        <button class="nav-link" id="p3-tab" data-bs-toggle="tab" data-bs-target="#p3-readings" type="button" role="tab">P3</button>
                                    </li>
                                </ul>
                                <div class="tab-content mt-3" id="readings-content">
                                    <div class="tab-pane fade show active" id="p2-readings" role="tabpanel">
                                        <div class="text-center" id="loading-p2-readings">
                                            <div class="spinner-border text-primary" role="status">
                                                <span class="visually-hidden">Loading...</span>
                                            </div>
                                            <p>Loading data...</p>
                                        </div>
                                    </div>
                                    <div class="tab-pane fade" id="p3-readings" role="tabpanel">
                                        <div class="text-center" id="loading-p3-readings">
                                            <div class="spinner-border text-primary" role="status">
                                                <span class="visually-hidden">Loading...</span>
                                            </div>
                                            <p>Loading data...</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="card mt-3">
                            <div class="card-header">Connection Status</div>
                            <div class="card-body" id="connection-status">
                                <div class="text-center" id="loading-connection">
                                    <div class="spinner-border text-primary" role="status">
                                        <span class="visually-hidden">Loading...</span>
                                    </div>
                                    <p>Loading connection data...</p>
                                </div>
                            </div>
                        </div>

                        <div class="card mt-3">
                            <div class="card-header">Export Data</div>
                            <div class="card-body">
                                <form id="export-form">
                                    <div class="mb-3">
                                        <label for="device-select" class="form-label">Device</label>
                                        <select class="form-select" id="device-select" name="device">
                                            <option value="P2">P2</option>
                                            <option value="P3">P3</option>
                                            <option value="all">All Devices</option>
                                        </select>
                                    </div>
                                    <div class="mb-3">
                                        <label for="start-date" class="form-label">Start Date</label>
                                        <input type="date" class="form-control" id="start-date" name="start_date">
                                    </div>
                                    <div class="mb-3">
                                        <label for="end-date" class="form-label">End Date</label>
                                        <input type="date" class="form-control" id="end-date" name="end_date">
                                    </div>
                                    <button type="submit" class="btn btn-primary">Export CSV</button>
                                </form>
                            </div>
                        </div>
                    </div>

                    <div class="col-md-8">
                        <div class="card">
                            <div class="card-header">Temperature (°C)</div>
                            <div class="card-body">
                                <div id="temperature-graph" class="graph-container">
                                    <div class="text-center" id="loading-temp">
                                        <div class="spinner-border text-primary" role="status">
                                            <span class="visually-hidden">Loading...</span>
                                        </div>
                                        <p>Loading graph...</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="card mt-3">
                            <div class="card-header">Humidity (%)</div>
                            <div class="card-body">
                                <div id="humidity-graph" class="graph-container">
                                    <div class="text-center" id="loading-humidity">
                                        <div class="spinner-border text-primary" role="status">
                                            <span class="visually-hidden">Loading...</span>
                                        </div>
                                        <p>Loading graph...</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="card mt-3">
                            <div class="card-header">Absolute Humidity (g/m³)</div>
                            <div class="card-body">
                                <div id="absolute-humidity-graph" class="graph-container">
                                    <div class="text-center" id="loading-abs-humidity">
                                        <div class="spinner-border text-primary" role="status">
                                            <span class="visually-hidden">Loading...</span>
                                        </div>
                                        <p>Loading graph...</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="card mt-3">
                            <div class="card-header">CO2 (ppm)</div>
                            <div class="card-body">
                                <div id="co2-graph" class="graph-container">
                                    <div class="text-center" id="loading-co2">
                                        <div class="spinner-border text-primary" role="status">
                                            <span class="visually-hidden">Loading...</span>
                                        </div>
                                        <p>Loading graph...</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="row mt-3">
                            <div class="col-md-6">
                                <div class="card">
                                    <div class="card-header">Pressure (hPa)</div>
                                    <div class="card-body">
                                        <div id="pressure-graph" class="graph-container">
                                            <div class="text-center" id="loading-pressure">
                                                <div class="spinner-border text-primary" role="status">
                                                    <span class="visually-hidden">Loading...</span>
                                                </div>
                                                <p>Loading graph...</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="card">
                                    <div class="card-header">Gas Resistance (Ohms)</div>
                                    <div class="card-body">
                                        <div id="gas-graph" class="graph-container">
                                            <div class="text-center" id="loading-gas">
                                                <div class="spinner-border text-primary" role="status">
                                                    <span class="visually-hidden">Loading...</span>
                                                </div>
                                                <p>Loading graph...</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="last-update">
    Last updated: <span id="last-update">{{ last_update }}</span>
</div>
{% endblock %}

{% block scripts %}
<script>
    // Function to update the current readings
    function updateCurrentReadings() {
        // Update P2 readings
        $.ajax({
            url: '/api/device/P2',
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                // Remove loading indicator
                $('#loading-p2-readings').hide();

                if (data && !data.error) {
                    var html = `
                        <div class="row">
                            <div class="col-6">
                                <p>Temperature</p>
                                <p class="data-value">${parseFloat(data.temperature).toFixed(1)}<span class="data-unit">°C</span></p>
                            </div>
                            <div class="col-6">
                                <p>Humidity</p>
                                <p class="data-value">${parseFloat(data.humidity).toFixed(1)}<span class="data-unit">%</span></p>
                            </div>
                        </div>
                        <div class="row mt-2">
                            <div class="col-6">
                                <p>Abs. Humidity</p>
                                <p class="data-value">${data.absolute_humidity ? parseFloat(data.absolute_humidity).toFixed(1) : "N/A"}<span class="data-unit">g/m³</span></p>
                            </div>
                            <div class="col-6">
                                <p>Pressure</p>
                                <p class="data-value">${parseFloat(data.pressure).toFixed(1)}<span class="data-unit">hPa</span></p>
                            </div>
                        </div>
                        <div class="row mt-2">
                            <div class="col-6">
                                <p>Gas Resistance</p>
                                <p class="data-value">${parseFloat(data.gas_resistance).toFixed(0)}<span class="data-unit">Ω</span></p>
                            </div>
                            <div class="col-6">
                                <p>CO2</p>
                                <p class="data-value">${data.co2 ? parseFloat(data.co2).toFixed(0) : "N/A"}<span class="data-unit">ppm</span></p>
                            </div>
                        </div>
                        <div class="row mt-2">
                            <div class="col-12">
                                <p>Last Reading</p>
                                <p class="data-value">${data.timestamp ? data.timestamp.split(' ')[1] : "N/A"}</p>
                            </div>
                        </div>
                    `;
                    $('#p2-readings').html(html);
                } else {
                    $('#p2-readings').html('<div class="alert alert-warning">No data available</div>');
                }
            },
            error: function() {
                // Remove loading indicator and show error
                $('#loading-p2-readings').hide();
                $('#p2-readings').html('<div class="alert alert-danger">Error loading data</div>');
            }
        });

        // Update P3 readings
        $.ajax({
            url: '/api/device/P3',
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                // Remove loading indicator
                $('#loading-p3-readings').hide();

                if (data && !data.error) {
                    var html = `
                        <div class="row">
                            <div class="col-6">
                                <p>Temperature</p>
                                <p class="data-value">${parseFloat(data.temperature).toFixed(1)}<span class="data-unit">°C</span></p>
                            </div>
                            <div class="col-6">
                                <p>Humidity</p>
                                <p class="data-value">${parseFloat(data.humidity).toFixed(1)}<span class="data-unit">%</span></p>
                            </div>
                        </div>
                        <div class="row mt-2">
                            <div class="col-6">
                                <p>Abs. Humidity</p>
                                <p class="data-value">${data.absolute_humidity ? parseFloat(data.absolute_humidity).toFixed(1) : "N/A"}<span class="data-unit">g/m³</span></p>
                            </div>
                            <div class="col-6">
                                <p>Pressure</p>
                                <p class="data-value">${parseFloat(data.pressure).toFixed(1)}<span class="data-unit">hPa</span></p>
                            </div>
                        </div>
                        <div class="row mt-2">
                            <div class="col-6">
                                <p>Gas Resistance</p>
                                <p class="data-value">${parseFloat(data.gas_resistance).toFixed(0)}<span class="data-unit">Ω</span></p>
                            </div>
                            <div class="col-6">
                                <p>CO2</p>
                                <p class="data-value">${data.co2 ? parseFloat(data.co2).toFixed(0) : "N/A"}<span class="data-unit">ppm</span></p>
                            </div>
                        </div>
                        <div class="row mt-2">
                            <div class="col-12">
                                <p>Last Reading</p>
                                <p class="data-value">${data.timestamp ? data.timestamp.split(' ')[1] : "N/A"}</p>
                            </div>
                        </div>
                    `;
                    $('#p3-readings').html(html);
                } else {
                    $('#p3-readings').html('<div class="alert alert-warning">No data available</div>');
                }

                // Update last update time
                $('#last-update').text(new Date().toLocaleString());
            },
            error: function() {
                // Remove loading indicator and show error
                $('#loading-p3-readings').hide();
                $('#p3-readings').html('<div class="alert alert-danger">Error loading data</div>');
            }
        });
    }

    // Function to update connection status
    function updateConnectionStatus() {
        $.ajax({
            url: '/api/connection/status',
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                // Remove loading indicator
                $('#loading-connection').hide();

                var html = '<div class="row">';

                // Check if we have P2 data
                if (data.P2 && data.P2.latest) {
                    var p2Data = data.P2.latest;
                    var status = p2Data.online ? "Online" : "Offline";
                    var statusClass = p2Data.online ? "text-success" : "text-danger";

                    // Calculate signal quality
                    var signalQuality = "Unknown";
                    var signalBars = 0;

                    if (p2Data.signal_strength) {
                        var signal = p2Data.signal_strength;
                        if (signal >= -50) {
                            signalQuality = "Excellent";
                            signalBars = 5;
                        } else if (signal >= -60) {
                            signalQuality = "Very Good";
                            signalBars = 4;
                        } else if (signal >= -70) {
                            signalQuality = "Good";
                            signalBars = 3;
                        } else if (signal >= -80) {
                            signalQuality = "Fair";
                            signalBars = 2;
                        } else {
                            signalQuality = "Poor";
                            signalBars = 1;
                        }
                    }

                    // Create signal bars HTML
                    var signalBarsHtml = '';
                    for (var i = 1; i <= 5; i++) {
                        var barHeight = i * 3 + 5; // 8px, 11px, 14px, 17px, 20px
                        var barClass = i <= signalBars ? 'active' : '';
                        signalBarsHtml += `<div class="signal-bar ${barClass}" style="height: ${barHeight}px;"></div>`;
                    }

                    html += `
                        <div class="col-md-6">
                            <h5 class="p2-color">P2 Sensor Node</h5>
                            <p>Status: <span class="${statusClass}">${status}</span></p>
                            <div class="signal-strength">
                                ${signalBarsHtml}
                                <span class="signal-text">${signalQuality} (${p2Data.signal_strength || 'N/A'} dBm)</span>
                            </div>
                            <p>Ping: ${p2Data.ping_time ? p2Data.ping_time.toFixed(2) + ' ms' : 'N/A'}</p>
                        </div>
                    `;
                } else {
                    html += `
                        <div class="col-md-6">
                            <h5 class="p2-color">P2 Sensor Node</h5>
                            <div class="alert alert-warning">No connection data available</div>
                        </div>
                    `;
                }

                // Check if we have P3 data
                if (data.P3 && data.P3.latest) {
                    var p3Data = data.P3.latest;
                    var status = p3Data.online ? "Online" : "Offline";
                    var statusClass = p3Data.online ? "text-success" : "text-danger";

                    // Calculate signal quality
                    var signalQuality = "Unknown";
                    var signalBars = 0;

                    if (p3Data.signal_strength) {
                        var signal = p3Data.signal_strength;
                        if (signal >= -50) {
                            signalQuality = "Excellent";
                            signalBars = 5;
                        } else if (signal >= -60) {
                            signalQuality = "Very Good";
                            signalBars = 4;
                        } else if (signal >= -70) {
                            signalQuality = "Good";
                            signalBars = 3;
                        } else if (signal >= -80) {
                            signalQuality = "Fair";
                            signalBars = 2;
                        } else {
                            signalQuality = "Poor";
                            signalBars = 1;
                        }
                    }

                    // Create signal bars HTML
                    var signalBarsHtml = '';
                    for (var i = 1; i <= 5; i++) {
                        var barHeight = i * 3 + 5; // 8px, 11px, 14px, 17px, 20px
                        var barClass = i <= signalBars ? 'active' : '';
                        signalBarsHtml += `<div class="signal-bar ${barClass}" style="height: ${barHeight}px;"></div>`;
                    }

                    html += `
                        <div class="col-md-6">
                            <h5 class="p3-color">P3 Sensor Node</h5>
                            <p>Status: <span class="${statusClass}">${status}</span></p>
                            <div class="signal-strength">
                                ${signalBarsHtml}
                                <span class="signal-text">${signalQuality} (${p3Data.signal_strength || 'N/A'} dBm)</span>
                            </div>
                            <p>Ping: ${p3Data.ping_time ? p3Data.ping_time.toFixed(2) + ' ms' : 'N/A'}</p>
                        </div>
                    `;
                } else {
                    html += `
                        <div class="col-md-6">
                            <h5 class="p3-color">P3 Sensor Node</h5>
                            <div class="alert alert-warning">No connection data available</div>
                        </div>
                    `;
                }

                html += '</div>';
                $('#connection-status').html(html);
            },
            error: function() {
                // Remove loading indicator and show error
                $('#loading-connection').hide();
                $('#connection-status').html('<div class="alert alert-danger">Error loading connection data</div>');
            }
        });
    }

    // Function to load graphs
    function loadGraphs() {
        var showP2 = $('#show-p2').is(':checked');
        var showP3 = $('#show-p3').is(':checked');

        $.ajax({
            url: `/api/graphs?days={{ days }}&show_p2=${showP2}&show_p3=${showP3}`,
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                // Check if we have errors for specific parameters
                if (data && data.errors) {
                    // Handle parameter-specific errors
                    const parameters = ['temperature', 'humidity', 'absolute_humidity', 'co2', 'pressure', 'gas_resistance'];

                    // Process each parameter
                    parameters.forEach(param => {
                        const elementId = param === 'gas_resistance' ? 'gas' : 
                                         param === 'absolute_humidity' ? 'abs-humidity' : param;

                        // Hide loading indicator
                        $(`#loading-${elementId}`).hide();

                        // Show error if this parameter has an error, otherwise show "no data" message
                        if (data.errors[param]) {
                            $(`#${elementId}-graph`).html(`<div class="alert alert-danger">Error: ${data.errors[param]}</div>`);
                        } else {
                            $(`#${elementId}-graph`).html('<div class="alert alert-warning">No data available</div>');
                        }
                    });

                    return;
                }

                // Check for general error
                if (data && data.error) {
                    // Hide all loading indicators and show error
                    $('.spinner-border').parent().hide();
                    $('.graph-container').html(`<div class="alert alert-danger">Error: ${data.error}</div>`);
                    return;
                }

                // Process graphs if we have data
                if (data) {
                    // Load temperature graph
                    if (data.temperature) {
                        $('#loading-temp').hide();
                        Plotly.newPlot('temperature-graph', JSON.parse(data.temperature).data, JSON.parse(data.temperature).layout);
                    } else {
                        $('#loading-temp').hide();
                        $('#temperature-graph').html('<div class="alert alert-warning">No temperature data available</div>');
                    }

                    // Load humidity graph
                    if (data.humidity) {
                        $('#loading-humidity').hide();
                        Plotly.newPlot('humidity-graph', JSON.parse(data.humidity).data, JSON.parse(data.humidity).layout);
                    } else {
                        $('#loading-humidity').hide();
                        $('#humidity-graph').html('<div class="alert alert-warning">No humidity data available</div>');
                    }

                    // Load absolute humidity graph
                    if (data.absolute_humidity) {
                        $('#loading-abs-humidity').hide();
                        Plotly.newPlot('absolute-humidity-graph', JSON.parse(data.absolute_humidity).data, JSON.parse(data.absolute_humidity).layout);
                    } else {
                        $('#loading-abs-humidity').hide();
                        $('#absolute-humidity-graph').html('<div class="alert alert-warning">No absolute humidity data available</div>');
                    }

                    // Load CO2 graph
                    if (data.co2) {
                        $('#loading-co2').hide();
                        Plotly.newPlot('co2-graph', JSON.parse(data.co2).data, JSON.parse(data.co2).layout);
                    } else {
                        $('#loading-co2').hide();
                        $('#co2-graph').html('<div class="alert alert-warning">No CO2 data available</div>');
                    }

                    // Load pressure graph
                    if (data.pressure) {
                        $('#loading-pressure').hide();
                        Plotly.newPlot('pressure-graph', JSON.parse(data.pressure).data, JSON.parse(data.pressure).layout);
                    } else {
                        $('#loading-pressure').hide();
                        $('#pressure-graph').html('<div class="alert alert-warning">No pressure data available</div>');
                    }

                    // Load gas resistance graph
                    if (data.gas_resistance) {
                        $('#loading-gas').hide();
                        Plotly.newPlot('gas-graph', JSON.parse(data.gas_resistance).data, JSON.parse(data.gas_resistance).layout);
                    } else {
                        $('#loading-gas').hide();
                        $('#gas-graph').html('<div class="alert alert-warning">No gas resistance data available</div>');
                    }
                } else {
                    // Hide all loading indicators and show error
                    $('.spinner-border').parent().hide();
                    $('.graph-container').html('<div class="alert alert-warning">No data available for graphs</div>');
                }
            },
            error: function(xhr, status, error) {
                // Hide all loading indicators and show error
                $('.spinner-border').parent().hide();

                // Try to parse the error response
                let errorMessage = 'Error loading graphs';
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response && response.error) {
                        errorMessage = `Error: ${response.error}`;
                    }
                } catch (e) {
                    // If we can't parse the response, use the default error message
                }

                $('.graph-container').html(`<div class="alert alert-danger">${errorMessage}</div>`);
            }
        });
    }

    // Handle apply filters button
    $('#apply-filters').click(function() {
        var showP2 = $('#show-p2').is(':checked');
        var showP3 = $('#show-p3').is(':checked');

        // Redirect to the same page with updated query parameters
        window.location.href = `/dashboard?days={{ days }}&show_p2=${showP2}&show_p3=${showP3}`;
    });

    // Handle export form submission
    $('#export-form').submit(function(e) {
        e.preventDefault();

        var device = $('#device-select').val();
        var startDate = $('#start-date').val();
        var endDate = $('#end-date').val();

        if (!startDate || !endDate) {
            alert('Please select both start and end dates');
            return;
        }

        window.location.href = `/api/export/${device}?start_date=${startDate}&end_date=${endDate}`;
    });

    // Update data on page load
    $(document).ready(function() {
        // Set default dates for export form
        var today = new Date();
        var oneWeekAgo = new Date();
        oneWeekAgo.setDate(today.getDate() - 7);

        $('#end-date').val(today.toISOString().split('T')[0]);
        $('#start-date').val(oneWeekAgo.toISOString().split('T')[0]);

        // Load initial data
        updateCurrentReadings();
        updateConnectionStatus();
        loadGraphs();

        // Set up auto-refresh for current readings, connection status, and graphs
        setInterval(function() {
            updateCurrentReadings();
            updateConnectionStatus();
            loadGraphs();
        }, {{ refresh_interval * 1000 }});
    });
</script>
{% endblock %}
"""

    # Write templates to files
    with open(os.path.join(templates_dir, 'base.html'), 'w') as f:
        f.write(base_html)

    with open(os.path.join(templates_dir, 'index.html'), 'w') as f:
        f.write(index_html)

    with open(os.path.join(templates_dir, 'dashboard.html'), 'w') as f:
        f.write(dashboard_html)

    logger.info("HTML templates created successfully")

def main():
    """Main function to parse arguments and start the web server."""
    parser = argparse.ArgumentParser(description="Raspberry Pi 5 Environmental Data Web Interface - Solo Version 4.0")
    parser.add_argument("--port", type=int, default=DEFAULT_CONFIG["web_port"],
                        help=f"Port to listen on (default: {DEFAULT_CONFIG['web_port']})")
    parser.add_argument("--data-dir", type=str, default=DEFAULT_CONFIG["data_dir"],
                        help=f"Directory to read data from (default: {DEFAULT_CONFIG['data_dir']})")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    # Update configuration with command-line arguments
    config = DEFAULT_CONFIG.copy()
    config["web_port"] = args.port
    config["data_dir"] = args.data_dir
    config["debug_mode"] = args.debug

    # Create templates
    create_templates()

    # Create global data visualizer
    global visualizer
    visualizer = DataVisualizer(config)

    # Start the web server
    logger.info(f"Starting web server on port {config['web_port']}")
    app.run(host='0.0.0.0', port=config['web_port'], debug=config['debug_mode'])

if __name__ == "__main__":
    main()

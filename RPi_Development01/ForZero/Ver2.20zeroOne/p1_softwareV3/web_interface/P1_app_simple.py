#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi 5 Environmental Data Web Interface - Simple Text-Only Version
Version: 2.0.0

This module provides a simplified web interface for the environmental data collection system.
It displays text-only information from P2, P3, P4, P5, and P6 Pico devices with BME680 sensors without graph rendering.

Features:
- Displays latest data from P2, P3, P4, P5, and P6 devices in text format
- Shows connection status for all devices
- Provides data export functionality
- Optimized for lightweight operation
- Ver2.0 supports only BME680 sensors (no CO2 sensors)

Requirements:
- Python 3.7+
- Flask for the web server
- pandas for data manipulation

Usage:
    python3 P1_app_simple.py [--port PORT] [--data-dir DIR]
"""

import os
import sys
import time
import json
import argparse
import logging
import datetime
import threading
from pathlib import Path
import pandas as pd
import numpy as np
from flask import Flask, render_template_string, render_template, jsonify, request, send_file, Response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/web_interface_simple.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add the parent directory to the Python path so we can import from p1_software_Zero
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Default configuration
DEFAULT_CONFIG = {
    "web_port": 80,
    "data_dir": "/var/lib(FromThonny)/raspap_solo/data",
    "rawdata_p1_dir": "RawData_P1",
    "rawdata_p2_dir": "RawData_P2",
    "rawdata_p3_dir": "RawData_P3",
    "rawdata_p4_dir": "RawData_P4",
    "refresh_interval": 10,  # seconds
    "data_api_url": "http://localhost:5001/api/data/latest",
    "connection_api_url": "http://localhost:5002/api/connection/status"
}

class DataVisualizer:
    """Simple data visualizer for environmental data."""
    
    def __init__(self, config=None):
        """Initialize the data visualizer with the given configuration."""
        self.config = config or DEFAULT_CONFIG
        self.app = Flask(__name__)
        self._setup_routes()
    
    def _read_fixed_csv(self, device_id, days=1):
        """Read fixed CSV for a device (P1–P4) and return a processed DataFrame or None."""
        if device_id not in ["P1", "P2", "P3", "P4"]:
            return None
        dir_key = f"rawdata_{device_id.lower()}_dir"
        base_dir = self.config.get("data_dir", ".")
        device_dir = self.config.get(dir_key)
        if not device_dir:
            logger.warning(f"No directory configured for {device_id}")
            return None
        csv_path = os.path.join(base_dir, device_dir, f"{device_id}_fixed.csv")
        if not os.path.exists(csv_path):
            logger.warning(f"CSV not found for {device_id}: {csv_path}")
            return None
        try:
            df = pd.read_csv(csv_path)
            if 'timestamp' in df.columns:
                # handle numeric or string timestamps robustly
                try:
                    if pd.api.types.is_numeric_dtype(df['timestamp']):
                        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
                    else:
                        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(str), errors='coerce')
                except Exception:
                    df['timestamp'] = pd.to_datetime(df['timestamp'].astype(str), errors='coerce')
            else:
                logger.warning(f"timestamp column missing in {csv_path}")
                return None
            df = df.dropna(subset=['timestamp'])
            # Coerce numeric columns
            for col in ["temperature", "humidity", "pressure", "gas_resistance", "absolute_humidity"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            # Filter by days
            if days and days > 0:
                cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
                df = df[df['timestamp'] >= cutoff]
            df = df.sort_values('timestamp')
            return df
        except Exception as e:
            logger.error(f"Error reading CSV for {device_id}: {e}")
            return None
    
    def get_latest_data(self):
        """Get the latest data from all devices."""
        try:
            import requests
            response = requests.get(self.config["data_api_url"], timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to get latest data: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"Error getting latest data: {e}")
            return {}
    
    def get_connection_status(self):
        """Get the connection status of all devices."""
        try:
            import requests
            response = requests.get(self.config["connection_api_url"], timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to get connection status: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"Error getting connection status: {e}")
            return {}
    
    def export_csv(self, device_id, start_date, end_date):
        """Export data to CSV for the specified device and date range."""
        import pandas as pd
        import datetime
        import os
        
        if device_id not in ["P1", "P2", "P3", "P4"]:
            return None
        
        try:
            # Convert string dates to datetime objects
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            
            # Ensure end_date is at the end of the day
            end_date = end_date.replace(hour=23, minute=59, second=59)
            
            # Resolve device directory dynamically (supports P1–P4)
            device_dir_key = f"rawdata_{device_id.lower()}_dir"
            device_dir = self.config.get(device_dir_key)
            if not device_dir:
                logger.warning(f"No directory configured for {device_id} (missing {device_dir_key})")
                return None
            
            # Get all CSV files for the device
            dir_path = os.path.join(self.config["data_dir"], device_dir)
            if not os.path.exists(dir_path):
                logger.warning(f"Directory not found: {dir_path}")
                return None
            
            # Get all date-based CSV files
            csv_files = []
            for filename in os.listdir(dir_path):
                if not filename.endswith(".csv") or not filename.startswith(f"{device_id}_"):
                    continue
                
                try:
                    # Extract date from filename (format: P4_YYYY-MM-DD.csv)
                    date_str = filename.split("_")[1].split(".")[0]
                    file_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                    
                    # Check if file is within date range
                    if start_date <= file_date <= end_date:
                        csv_files.append(os.path.join(dir_path, filename))
                except (IndexError, ValueError) as e:
                    logger.warning(f"Could not parse date from filename {filename}: {e}")
            
            if not csv_files:
                logger.warning(f"No CSV files found for {device_id} in date range {start_date} to {end_date}")
                return None
            
            # Read all CSV files and concatenate
            dfs = []
            for csv_file in csv_files:
                try:
                    df = pd.read_csv(csv_file)
                    dfs.append(df)
                except Exception as e:
                    logger.warning(f"Error reading CSV file {csv_file}: {e}")
            
            if not dfs:
                logger.warning(f"No data found for {device_id} in date range {start_date} to {end_date}")
                return None
            
            # Concatenate all dataframes
            df_all = pd.concat(dfs, ignore_index=True)
            
            # Filter by date range
            if 'timestamp' in df_all.columns:
                df_all['timestamp'] = pd.to_datetime(df_all['timestamp'])
                df_all = df_all[(df_all['timestamp'] >= start_date) & (df_all['timestamp'] <= end_date)]
            
            # Create a temporary file for download
            temp_file = os.path.join(self.config["data_dir"], f"{device_id}_{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}.csv")
            df_all.to_csv(temp_file, index=False)
            
            return temp_file
        except Exception as e:
            logger.error(f"Error exporting CSV for {device_id}: {e}")
            return None
    
    def _setup_routes(self):
        """Set up the Flask routes."""
        app = self.app

        # Dashboard UI (graphs)
        @app.route('/dashboard')
        def dashboard():
            return render_template('dashboard.html')
        
        @app.route('/')
        def index():
            """Render the main (text) page."""
            return render_template_string(HTML_TEMPLATE, refresh_interval=self.config["refresh_interval"])
        
        @app.route('/api/latest-data')
        def get_latest_data():
            """Get the latest data from all devices."""
            return jsonify(self.get_latest_data())
        
        
        @app.route('/api/device/<device_id>')
        def get_device_data(device_id):
            """Get the latest data for a specific device."""
            if device_id not in ["P1", "P2", "P3", "P4"]:
                return jsonify({"error": "Invalid device ID"}), 400
            
            data = self.get_latest_data()
            if device_id in data:
                return jsonify(data[device_id])
            else:
                return jsonify({"error": "Device data not found"}), 404

        @app.route('/api/graphs')
        def get_graphs():
            """Return structured time-series data for graphs from fixed CSVs (no CO2)."""
            try:
                days = request.args.get('days', default=1, type=int)
                show_p1 = request.args.get('show_p1', default='true').lower() == 'true'
                show_p2 = request.args.get('show_p2', default='true').lower() == 'true'
                show_p3 = request.args.get('show_p3', default='true').lower() == 'true'
                show_p4 = request.args.get('show_p4', default='true').lower() == 'true'
                result = {}
                for dev, show in [("P1", show_p1), ("P2", show_p2), ("P3", show_p3), ("P4", show_p4)]:
                    if not show:
                        continue
                    df = self._read_fixed_csv(dev, days=days)
                    if df is None or df.empty:
                        continue
                    result[dev] = {
                        'timestamp': df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                        'temperature': df['temperature'].tolist() if 'temperature' in df else [],
                        'humidity': df['humidity'].tolist() if 'humidity' in df else [],
                        'absolute_humidity': df['absolute_humidity'].tolist() if 'absolute_humidity' in df else [],
                        'pressure': df['pressure'].tolist() if 'pressure' in df else [],
                        'gas_resistance': df['gas_resistance'].tolist() if 'gas_resistance' in df else []
                    }
                return jsonify(result)
            except Exception as e:
                logger.error(f"Error generating graph data: {e}")
                return jsonify({'error': str(e)}), 500

        @app.route('/api/latest-data-table')
        def latest_data_table():
            """Return a small HTML table of the latest row per device from fixed CSVs."""
            devices = ["P1", "P2", "P3", "P4"]
            rows = []
            for dev in devices:
                df = self._read_fixed_csv(dev, days=7)
                if df is not None and not df.empty:
                    last = df.iloc[-1]
                    rows.append(f"<tr><td>{dev}</td><td>{last['timestamp']}</td><td>{last.get('temperature', '')}</td><td>{last.get('humidity','')}</td><td>{last.get('pressure','')}</td><td>{last.get('gas_resistance','')}</td><td>{last.get('absolute_humidity','')}</td></tr>")
            if not rows:
                return Response("<p>No data available</p>", mimetype='text/html')
            header = "<tr><th>Device</th><th>Timestamp</th><th>Temperature</th><th>Humidity</th><th>Pressure</th><th>Gas Resistance</th><th>Absolute Humidity</th></tr>"
            html = f"<table>{header}{''.join(rows)}</table>"
            return Response(html, mimetype='text/html')

        @app.route('/api/connection-status-table')
        def connection_status_table():
            """Return a small HTML table for connection status (best-effort)."""
            status = self.get_connection_status()
            devices = ["P1", "P2", "P3", "P4"]
            header = "<tr><th>Device</th><th>Online</th><th>Signal</th><th>Ping</th></tr>"
            rows = []
            for dev in devices:
                info = status.get(dev, {}) if isinstance(status, dict) else {}
                online = info.get('online', 'N/A')
                signal = info.get('signal_strength', 'N/A')
                ping = info.get('ping_time', 'N/A')
                rows.append(f"<tr><td>{dev}</td><td>{online}</td><td>{signal}</td><td>{ping}</td></tr>")
            html = f"<table>{header}{''.join(rows)}</table>"
            return Response(html, mimetype='text/html')
        
        @app.route('/export/<device_id>')
        def export_data(device_id):
            """Export data to CSV for the specified device and date range."""
            if device_id not in ["P2", "P3", "P4", "P5", "P6"]:
                return jsonify({"error": "Invalid device ID"}), 400
            
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            if not start_date or not end_date:
                return jsonify({"error": "Missing start_date or end_date parameter"}), 400
            
            csv_file = self.export_csv(device_id, start_date, end_date)
            if csv_file:
                return send_file(csv_file, as_attachment=True, download_name=os.path.basename(csv_file))
            else:
                return jsonify({"error": "Failed to export data"}), 500
    
    def run(self, host='0.0.0.0', port=None, debug=False):
        """Run the Flask application."""
        port = port or self.config["web_port"]
        self.app.run(host=host, port=port, debug=debug)

# HTML template for the main page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Environmental Data Monitor</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        h1, h2 {
            color: #333;
        }
        .data-container {
            margin-bottom: 20px;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 5px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f2f2f2;
        }
        .status-online {
            color: green;
            font-weight: bold;
        }
        .status-offline {
            color: red;
            font-weight: bold;
        }
        .export-form {
            margin-top: 20px;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 5px;
        }
        .export-form label, .export-form input, .export-form select, .export-form button {
            margin: 5px;
        }
        button {
            padding: 8px 15px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Environmental Data Monitor</h1>
        
        <div class="data-container">
            <h2>Latest Sensor Data</h2>
            <div id="latest-data">Loading...</div>
        </div>
        
        <div class="export-form">
            <h2>Export Data</h2>
            <form id="export-form">
                <label for="device-select">Device:</label>
                <select id="device-select" name="device">
                    <option value="P1">P1</option>
                    <option value="P2">P2</option>
                    <option value="P3">P3</option>
                    <option value="P4">P4</option>
                </select>
                
                <label for="start-date">Start Date:</label>
                <input type="date" id="start-date" name="start_date" required>
                
                <label for="end-date">End Date:</label>
                <input type="date" id="end-date" name="end_date" required>
                
                <button type="submit">Export CSV</button>
            </form>
        </div>
    </div>
    
    <script>
        // Function to format timestamp
        function formatTimestamp(timestamp) {
            if (!timestamp) return 'N/A';
            return new Date(timestamp).toLocaleString();
        }
        
        // Function to create a table from data
        function createDataTable(data) {
            if (!data || Object.keys(data).length === 0) {
                return '<p>No data available</p>';
            }
            
            let html = '<table>';
            // Ver2.0: CO2 column removed as we're disabling CO2 sensor functionality
            html += '<tr><th>Device</th><th>Timestamp</th><th>Temperature (°C)</th><th>Humidity (%)</th><th>Pressure (hPa)</th><th>Gas Resistance (Ω)</th><th>Absolute Humidity (g/m³)</th></tr>';
            
            for (const [deviceId, deviceData] of Object.entries(data)) {
                if (deviceData && typeof deviceData === 'object') {
                    html += `<tr>
                        <td>${deviceId}</td>
                        <td>${formatTimestamp(deviceData.timestamp)}</td>
                        <td>${deviceData.temperature !== undefined ? deviceData.temperature : 'N/A'}</td>
                        <td>${deviceData.humidity !== undefined ? deviceData.humidity : 'N/A'}</td>
                        <td>${deviceData.pressure !== undefined ? deviceData.pressure : 'N/A'}</td>
                        <td>${deviceData.gas_resistance !== undefined ? deviceData.gas_resistance : 'N/A'}</td>
                        <!-- Ver2.0: CO2 data cell removed as we're disabling CO2 sensor functionality -->
                        <td>${deviceData.absolute_humidity !== undefined ? deviceData.absolute_humidity : 'N/A'}</td>
                    </tr>`;
                }
            }
            
            html += '</table>';
            return html;
        }
        
        // Function to load latest data
        function loadLatestData() {
            fetch('/api/latest-data')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('latest-data').innerHTML = createDataTable(data);
                })
                .catch(error => {
                    console.error('Error fetching latest data:', error);
                    document.getElementById('latest-data').innerHTML = '<p>Error loading data</p>';
                });
        }
        
        // Set up export form submission
        document.getElementById('export-form').addEventListener('submit', function(event) {
            event.preventDefault();
            
            const deviceId = document.getElementById('device-select').value;
            const startDate = document.getElementById('start-date').value;
            const endDate = document.getElementById('end-date').value;
            
            window.location.href = `/export/${deviceId}?start_date=${startDate}&end_date=${endDate}`;
        });
        
        // Load data on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadLatestData();
            
            // Set up auto-refresh
            setInterval(loadLatestData, {{ refresh_interval * 1000 }});
            
            // Set default dates for export form
            const today = new Date();
            const yesterday = new Date(today);
            yesterday.setDate(yesterday.getDate() - 1);
            
            document.getElementById('start-date').value = yesterday.toISOString().split('T')[0];
            document.getElementById('end-date').value = today.toISOString().split('T')[0];
        });
    </script>
</body>
</html>
"""

def main():
    """Main function to run the web interface."""
    parser = argparse.ArgumentParser(description='Environmental Data Web Interface - Simple Text-Only Version')
    parser.add_argument('--port', type=int, help='Port to listen on')
    parser.add_argument('--data-dir', type=str, help='Directory to store data')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    config = DEFAULT_CONFIG.copy()
    
    if args.port:
        config["web_port"] = args.port
    
    if args.data_dir:
        config["data_dir"] = args.data_dir
    
    visualizer = DataVisualizer(config)
    visualizer.run(debug=args.debug)

if __name__ == "__main__":
    main()
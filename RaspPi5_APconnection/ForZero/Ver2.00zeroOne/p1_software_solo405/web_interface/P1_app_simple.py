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
from flask import Flask, render_template_string, jsonify, request, send_file, Response

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

# Add the parent directory to the Python path so we can import from p1_software_solo405
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Default configuration
DEFAULT_CONFIG = {
    "web_port": 80,
    "data_dir": "/var/lib/raspap_solo/data",
    "rawdata_p2_dir": "RawData_P2",
    "rawdata_p3_dir": "RawData_P3",
    "rawdata_p4_dir": "RawData_P4",
    "rawdata_p5_dir": "RawData_P5",
    "rawdata_p6_dir": "RawData_P6",
    "refresh_interval": 10,  # seconds
    "data_api_url": "http://localhost:5001/api/data/latest",
    "connection_api_url": "http://localhost:5001/api/connection/status"
}

class DataVisualizer:
    """Simple data visualizer for environmental data."""
    
    def __init__(self, config=None):
        """Initialize the data visualizer with the given configuration."""
        self.config = config or DEFAULT_CONFIG
        self.app = Flask(__name__)
        self._setup_routes()
    
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
        
        if device_id not in ["P2", "P3", "P4", "P5", "P6"]:
            return None
        
        try:
            # Convert string dates to datetime objects
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            
            # Ensure end_date is at the end of the day
            end_date = end_date.replace(hour=23, minute=59, second=59)
            
            # Get the appropriate directory for the device
            if device_id == "P4":
                device_dir = self.config["rawdata_p4_dir"]
            elif device_id == "P5":
                device_dir = self.config["rawdata_p5_dir"]
            else:  # P6
                device_dir = self.config["rawdata_p6_dir"]
            
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
        
        @app.route('/')
        def index():
            """Render the main page."""
            return render_template_string(HTML_TEMPLATE, refresh_interval=self.config["refresh_interval"])
        
        @app.route('/api/latest-data')
        def get_latest_data():
            """Get the latest data from all devices."""
            return jsonify(self.get_latest_data())
        
        @app.route('/api/connection-status')
        def get_connection_status():
            """Get the connection status of all devices."""
            return jsonify(self.get_connection_status())
        
        @app.route('/api/device/<device_id>')
        def get_device_data(device_id):
            """Get the latest data for a specific device."""
            if device_id not in ["P2", "P3", "P4", "P5", "P6"]:
                return jsonify({"error": "Invalid device ID"}), 400
            
            data = self.get_latest_data()
            if device_id in data:
                return jsonify(data[device_id])
            else:
                return jsonify({"error": "Device data not found"}), 404
        
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
        
        <div class="data-container">
            <h2>Connection Status</h2>
            <div id="connection-status">Loading...</div>
        </div>
        
        <div class="export-form">
            <h2>Export Data</h2>
            <form id="export-form">
                <label for="device-select">Device:</label>
                <select id="device-select" name="device">
                    <option value="P4">P4</option>
                    <option value="P5">P5</option>
                    <option value="P6">P6</option>
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
        
        // Function to create a connection status table
        function createStatusTable(data) {
            if (!data || Object.keys(data).length === 0) {
                return '<p>No connection data available</p>';
            }
            
            let html = '<table>';
            html += '<tr><th>Device</th><th>Status</th><th>Last Update</th><th>Signal Strength</th><th>Noise Level</th><th>SNR</th><th>Ping Time</th></tr>';
            
            for (const [deviceId, statusData] of Object.entries(data)) {
                if (statusData && typeof statusData === 'object') {
                    const statusClass = statusData.online ? 'status-online' : 'status-offline';
                    const statusText = statusData.online ? 'Online' : 'Offline';
                    
                    html += `<tr>
                        <td>${deviceId}</td>
                        <td class="${statusClass}">${statusText}</td>
                        <td>${formatTimestamp(statusData.timestamp)}</td>
                        <td>${statusData.signal_strength !== undefined ? statusData.signal_strength + ' dBm' : 'N/A'}</td>
                        <td>${statusData.noise_level !== undefined ? statusData.noise_level + ' dBm' : 'N/A'}</td>
                        <td>${statusData.snr !== undefined ? statusData.snr + ' dB' : 'N/A'}</td>
                        <td>${statusData.ping_time !== undefined ? statusData.ping_time + ' ms' : 'N/A'}</td>
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
        
        // Function to load connection status
        function loadConnectionStatus() {
            fetch('/api/connection-status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('connection-status').innerHTML = createStatusTable(data);
                })
                .catch(error => {
                    console.error('Error fetching connection status:', error);
                    document.getElementById('connection-status').innerHTML = '<p>Error loading connection status</p>';
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
            loadConnectionStatus();
            
            // Set up auto-refresh
            setInterval(loadLatestData, {{ refresh_interval * 1000 }});
            setInterval(loadConnectionStatus, {{ refresh_interval * 1000 }});
            
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
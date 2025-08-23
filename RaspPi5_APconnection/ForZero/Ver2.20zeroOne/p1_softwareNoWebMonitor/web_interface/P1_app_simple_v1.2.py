"""
Simplified Web Interface for Environmental Data Monitoring
Version: 1.2

This module provides a simplified web interface for displaying environmental data
collected from sensor nodes. It is optimized for Raspberry Pi Zero 2W with reduced
resource usage and text-only display.
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
try:
    from flask import Flask, render_template, jsonify, request, send_file, Response
except ImportError:
    logging.error("Flask not installed. Please install with: pip install flask")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/web_interface_solo.log')
    ]
)
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "data_dir": "/var/lib(FromThonny)/raspap_solo/data",
    "rawdata_p4_dir": "RawData_P4",
    "rawdata_p5_dir": "RawData_P5",
    "rawdata_p6_dir": "RawData_P6",
    "web_port": 80,
    "refresh_interval": 30,  # Increased from 10 to 30 seconds
    "debug_mode": False
}

class DataVisualizer:
    """Class for visualizing environmental data."""

    def __init__(self, config=None):
        """
        Initialize the data visualizer with the given configuration.
        
        Args:
            config (dict, optional): Configuration dictionary. Defaults to None.
        """
        self.config = config or DEFAULT_CONFIG.copy()
        self.app = Flask(__name__)
        self.data_cache = {"P4": None, "P5": None, "P6": None}
        self._setup_routes()
        
    def get_latest_data(self):
        """
        Get the latest data from all devices.
        
        Returns:
            dict: The latest data from all devices.
        """
        try:
            # Try to get data from the data collector API
            response = requests.get(f"http://localhost:{self.config.get('data_collector_port', 5000)}/api/data/latest")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to get data from data collector API: {e}")
        
        # Fallback: Read data from files
        result = {}
        for device_id in ["P4", "P5", "P6"]:
            try:
                device_dir = self.config[f"rawdata_{device_id.lower()}_dir"]
                latest_file = os.path.join(self.config["data_dir"], device_dir, f"{device_id}_latest.json")
                if os.path.exists(latest_file):
                    with open(latest_file, 'r') as f:
                        result[device_id] = json.load(f)
            except Exception as e:
                logger.error(f"Error reading latest data for {device_id}: {e}")
        
        return result
    
    def get_connection_status(self):
        """
        Get the connection status of all devices.
        
        Returns:
            dict: The connection status of all devices.
        """
        try:
            # Try to get data from the connection monitor API
            response = requests.get(f"http://localhost:{self.config.get('connection_monitor_port', 5001)}/api/connection/status")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to get data from connection monitor API: {e}")
        
        # Fallback: Return empty status
        return {
            "P4": {"online": False, "last_seen": None, "signal_strength": None},
            "P5": {"online": False, "last_seen": None, "signal_strength": None},
            "P6": {"online": False, "last_seen": None, "signal_strength": None}
        }
    
    def get_historical_data_summary(self, device_id, days=1):
        """
        Get a summary of historical data for a specific device.
        
        Args:
            device_id (str): The device ID.
            days (int, optional): Number of days to include. Defaults to 1.
            
        Returns:
            dict: Summary statistics for the device's data.
        """
        try:
            # Get the device's data directory
            device_dir = self.config[f"rawdata_{device_id.lower()}_dir"]
            data_dir = os.path.join(self.config["data_dir"], device_dir)
            
            # Calculate the cutoff date
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
            cutoff_str = cutoff_date.strftime("%Y-%m-%d")
            
            # Find all CSV files for the device within the date range
            csv_files = []
            for filename in os.listdir(data_dir):
                if filename.startswith(f"{device_id}_") and filename.endswith(".csv"):
                    # Extract date from filename (format: P4_2025-07-22.csv)
                    try:
                        file_date_str = filename.split('_')[1].split('.')[0]
                        file_date = datetime.datetime.strptime(file_date_str, "%Y-%m-%d")
                        if file_date >= cutoff_date:
                            csv_files.append(os.path.join(data_dir, filename))
                    except (IndexError, ValueError):
                        # If filename doesn't match expected format, check if it's the fixed file
                        if filename == f"{device_id}_fixed.csv":
                            csv_files.append(os.path.join(data_dir, filename))
            
            if not csv_files:
                return {"error": f"No data found for {device_id} in the last {days} days"}
            
            # Read and combine CSV files
            all_data = []
            for csv_file in csv_files:
                try:
                    with open(csv_file, 'r') as f:
                        # Skip header
                        header = f.readline().strip().split(',')
                        for line in f:
                            values = line.strip().split(',')
                            if len(values) >= len(header):
                                data_point = {header[i]: values[i] for i in range(len(header))}
                                all_data.append(data_point)
                except Exception as e:
                    logger.error(f"Error reading CSV file {csv_file}: {e}")
            
            if not all_data:
                return {"error": f"No valid data found for {device_id} in the last {days} days"}
            
            # Calculate summary statistics
            summary = {
                "device_id": device_id,
                "days": days,
                "total_readings": len(all_data),
                "parameters": {}
            }
            
            # Parameters to summarize
            parameters = ["temperature", "humidity", "pressure", "gas_resistance", "co2", "absolute_humidity"]
            
            for param in parameters:
                values = []
                for data_point in all_data:
                    if param in data_point and data_point[param]:
                        try:
                            value = float(data_point[param])
                            values.append(value)
                        except ValueError:
                            pass
                
                if values:
                    summary["parameters"][param] = {
                        "min": min(values),
                        "max": max(values),
                        "avg": sum(values) / len(values),
                        "readings": len(values)
                    }
            
            return summary
        
        except Exception as e:
            logger.error(f"Error generating historical data summary for {device_id}: {e}")
            return {"error": f"Failed to generate summary: {str(e)}"}
    
    def export_csv(self, device_id, start_date, end_date):
        """
        Export data to CSV for the specified device and date range.
        
        Args:
            device_id (str): The device ID.
            start_date (str): The start date (YYYY-MM-DD).
            end_date (str): The end date (YYYY-MM-DD).
            
        Returns:
            str: The path to the exported CSV file, or None if export failed.
        """
        try:
            # Parse dates
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            
            # Get the device's data directory
            device_dir = self.config[f"rawdata_{device_id.lower()}_dir"]
            data_dir = os.path.join(self.config["data_dir"], device_dir)
            
            # Find all CSV files for the device within the date range
            csv_files = []
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                csv_file = os.path.join(data_dir, f"{device_id}_{date_str}.csv")
                if os.path.exists(csv_file):
                    csv_files.append(csv_file)
                current_date += datetime.timedelta(days=1)
            
            # Also check for the fixed file
            fixed_file = os.path.join(data_dir, f"{device_id}_fixed.csv")
            if os.path.exists(fixed_file):
                csv_files.append(fixed_file)
            
            if not csv_files:
                logger.warning(f"No CSV files found for {device_id} between {start_date} and {end_date}")
                return None
            
            # Read and combine CSV files
            all_data = []
            header = None
            for csv_file in csv_files:
                try:
                    with open(csv_file, 'r') as f:
                        file_header = f.readline().strip().split(',')
                        if header is None:
                            header = file_header
                        
                        for line in f:
                            values = line.strip().split(',')
                            if len(values) >= len(header):
                                data_point = {header[i]: values[i] for i in range(len(header))}
                                
                                # Check if timestamp is within range
                                try:
                                    timestamp = data_point.get("timestamp")
                                    if timestamp:
                                        # Try different timestamp formats
                                        try:
                                            # Try ISO format
                                            dt = datetime.datetime.fromisoformat(timestamp)
                                        except ValueError:
                                            try:
                                                # Try Unix timestamp
                                                dt = datetime.datetime.fromtimestamp(float(timestamp))
                                            except ValueError:
                                                # Try custom format
                                                dt = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                                        
                                        # Check if within range
                                        if start_date.date() <= dt.date() <= end_date.date():
                                            all_data.append(data_point)
                                except Exception as e:
                                    logger.warning(f"Error parsing timestamp {timestamp}: {e}")
                                    # Include data point anyway if timestamp parsing fails
                                    all_data.append(data_point)
                except Exception as e:
                    logger.error(f"Error reading CSV file {csv_file}: {e}")
            
            if not all_data:
                logger.warning(f"No data found for {device_id} between {start_date} and {end_date}")
                return None
            
            # Create a temporary file for download
            temp_file = os.path.join(self.config["data_dir"], f"{device_id}_{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}.csv")
            
            # Write data to CSV
            with open(temp_file, 'w') as f:
                f.write(','.join(header) + '\n')
                for data_point in all_data:
                    values = [data_point.get(h, '') for h in header]
                    f.write(','.join(values) + '\n')
            
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
            return render_template('dashboard_text_only.html', refresh_interval=self.config["refresh_interval"])
        
        @app.route('/api/latest-data')
        def get_latest_data():
            """Get the latest data from all devices."""
            return jsonify(self.get_latest_data())
        
        @app.route('/api/latest-data-table')
        def get_latest_data_table():
            """Get the latest data from all devices as an HTML table."""
            data = self.get_latest_data()
            html = '<table class="data-table">'
            html += '<tr><th>Device</th><th>Timestamp</th><th>Temperature (°C)</th><th>Humidity (%)</th><th>Pressure (hPa)</th><th>CO2 (ppm)</th><th>Gas Resistance (Ω)</th></tr>'
            
            for device_id in ["P4", "P5", "P6"]:
                if device_id in data:
                    device_data = data[device_id]
                    timestamp = device_data.get("timestamp", "N/A")
                    temperature = device_data.get("temperature", "N/A")
                    humidity = device_data.get("humidity", "N/A")
                    pressure = device_data.get("pressure", "N/A")
                    co2 = device_data.get("co2", "N/A")
                    gas_resistance = device_data.get("gas_resistance", "N/A")
                    
                    html += f'<tr>'
                    html += f'<td>{device_id}</td>'
                    html += f'<td>{timestamp}</td>'
                    html += f'<td>{temperature}</td>'
                    html += f'<td>{humidity}</td>'
                    html += f'<td>{pressure}</td>'
                    html += f'<td>{co2}</td>'
                    html += f'<td>{gas_resistance}</td>'
                    html += f'</tr>'
                else:
                    html += f'<tr><td>{device_id}</td><td colspan="6">No data available</td></tr>'
            
            html += '</table>'
            return html
        
        @app.route('/api/connection-status')
        def get_connection_status():
            """Get the connection status of all devices."""
            return jsonify(self.get_connection_status())
        
        @app.route('/api/connection-status-table')
        def get_connection_status_table():
            """Get the connection status of all devices as an HTML table."""
            status = self.get_connection_status()
            html = '<table class="data-table">'
            html += '<tr><th>Device</th><th>Status</th><th>Last Seen</th><th>Signal Strength</th><th>Ping (ms)</th></tr>'
            
            for device_id in ["P4", "P5", "P6"]:
                if device_id in status:
                    device_status = status[device_id]
                    online = device_status.get("online", False)
                    last_seen = device_status.get("last_seen", "N/A")
                    signal_strength = device_status.get("signal_strength", "N/A")
                    ping = device_status.get("ping_time", "N/A")
                    
                    status_class = "status-online" if online else "status-offline"
                    status_text = "Online" if online else "Offline"
                    
                    html += f'<tr>'
                    html += f'<td>{device_id}</td>'
                    html += f'<td class="{status_class}">{status_text}</td>'
                    html += f'<td>{last_seen}</td>'
                    html += f'<td>{signal_strength} dBm</td>'
                    html += f'<td>{ping}</td>'
                    html += f'</tr>'
                else:
                    html += f'<tr><td>{device_id}</td><td class="status-offline">Offline</td><td colspan="3">No data available</td></tr>'
            
            html += '</table>'
            return html
        
        @app.route('/api/device/<device_id>')
        def get_device_data(device_id):
            """Get the latest data for a specific device."""
            if device_id not in ["P4", "P5", "P6"]:
                return jsonify({"error": "Invalid device ID"}), 400
            
            data = self.get_latest_data()
            if device_id in data:
                return jsonify(data[device_id])
            else:
                return jsonify({"error": "Device data not found"}), 404
        
        @app.route('/api/data/summary/<device_id>')
        def get_data_summary(device_id):
            """Get a summary of historical data for a specific device."""
            if device_id not in ["P4", "P5", "P6"]:
                return jsonify({"error": "Invalid device ID"}), 400
            
            days = request.args.get('days', default=1, type=int)
            summary = self.get_historical_data_summary(device_id, days)
            
            if "error" in summary:
                return jsonify(summary), 404
            
            # Generate HTML table from summary
            html = '<table class="data-table">'
            html += f'<tr><th colspan="5">Summary for {device_id} (Last {days} days)</th></tr>'
            html += '<tr><th>Parameter</th><th>Min</th><th>Max</th><th>Average</th><th>Readings</th></tr>'
            
            for param, stats in summary["parameters"].items():
                param_name = param.replace("_", " ").title()
                html += f'<tr>'
                html += f'<td>{param_name}</td>'
                html += f'<td>{stats["min"]:.2f}</td>'
                html += f'<td>{stats["max"]:.2f}</td>'
                html += f'<td>{stats["avg"]:.2f}</td>'
                html += f'<td>{stats["readings"]}</td>'
                html += f'</tr>'
            
            html += '</table>'
            html += f'<p>Total readings: {summary["total_readings"]}</p>'
            
            return html
        
        @app.route('/api/data/export/<device_id>')
        def export_data(device_id):
            """Export data to CSV for the specified device and date range."""
            if device_id not in ["P4", "P5", "P6"]:
                return jsonify({"error": "Invalid device ID"}), 400
            
            start_date = request.args.get('start')
            end_date = request.args.get('end')
            
            if not start_date or not end_date:
                return jsonify({"error": "Missing start or end parameter"}), 400
            
            csv_file = self.export_csv(device_id, start_date, end_date)
            if csv_file:
                return send_file(csv_file, as_attachment=True, download_name=os.path.basename(csv_file))
            else:
                return jsonify({"error": "Failed to export data"}), 500
    
    def run(self, host='0.0.0.0', port=None, debug=False):
        """Run the Flask application."""
        port = port or self.config["web_port"]
        self.app.run(host=host, port=port, debug=debug)

def main():
    """Main entry point for the web interface."""
    parser = argparse.ArgumentParser(description='Environmental Data Web Interface')
    parser.add_argument('--port', type=int, help='Port to listen on')
    parser.add_argument('--data-dir', type=str, help='Data directory')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    config = DEFAULT_CONFIG.copy()
    
    if args.port:
        config["web_port"] = args.port
    
    if args.data_dir:
        config["data_dir"] = args.data_dir
    
    if args.debug:
        config["debug_mode"] = True
    
    # Ensure data directory exists
    os.makedirs(config["data_dir"], exist_ok=True)
    
    # Create and run the data visualizer
    visualizer = DataVisualizer(config)
    visualizer.run(debug=config["debug_mode"])

if __name__ == "__main__":
    # Add a small delay to ensure other services are ready
    time.sleep(2)
    
    try:
        import requests
    except ImportError:
        logger.warning("requests module not found, falling back to file-based data access")
    
    main()
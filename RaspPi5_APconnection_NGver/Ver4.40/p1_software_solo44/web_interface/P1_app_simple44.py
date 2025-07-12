#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi 5 Environmental Data Web Interface - Simple Version
Version: 4.40.0-solo

This module provides a simplified web interface for visualizing environmental data
collected from P2 and P3 sensor nodes with BME680 and MH-Z19C sensors. It displays real-time data,
historical trends, and allows for data export.

Features:
- Real-time display of current sensor readings from both P2 and P3 (including CO2)
- Time-series graphs of historical data with proper Y-axis ranges
- Toggle options to show/hide P2 and P3 data on the same graph
- Display of absolute humidity calculated from temperature and humidity
- Data export in CSV format
- Responsive design for mobile and desktop viewing
- Auto-refresh functionality

Requirements:
- Python 3.7+
- Flask for the web server
- Pandas for data manipulation
- Plotly for interactive graphs

Usage:
    python3 P1_app_simple44.py [--port PORT] [--data-dir DIR]
"""

import os
import sys
import time
import json
import argparse
import logging
import datetime
import pandas as pd
import plotly.graph_objs as go
from flask import Flask, render_template_string, jsonify, request, send_file, Response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/web_interface_simple44.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "web_port": 80,
    "data_dir": "/var/lib/raspap_solo/data",
    "rawdata_p2_dir": "RawData_P2",
    "rawdata_p3_dir": "RawData_P3",
    "refresh_interval": 10,  # seconds
    "graph_points": 100,  # number of data points to show in graphs
    "debug_mode": False
}

# Initialize Flask app
app = Flask(__name__)

# HTML Template with Plotly.js integration
TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Environmental Data Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
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
        .graph-container {
            height: 400px;
            margin-bottom: 20px;
        }
        .control-panel {
            margin-bottom: 20px;
        }
        .p2-color {
            color: blue;
        }
        .p3-color {
            color: red;
        }
        .loading {
            text-align: center;
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="text-center mb-4">Environmental Data Dashboard</h1>
        
        <div class="card control-panel">
            <div class="card-header">Controls</div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-4">
                        <div class="form-check form-switch">
                            <input class="form-check-input" type="checkbox" id="show-p2" checked>
                            <label class="form-check-label p2-color" for="show-p2">Show P2 Data</label>
                        </div>
                        <div class="form-check form-switch">
                            <input class="form-check-input" type="checkbox" id="show-p3" checked>
                            <label class="form-check-label p3-color" for="show-p3">Show P3 Data</label>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="form-group">
                            <label for="days-select">Time Range:</label>
                            <select class="form-control" id="days-select">
                                <option value="1">1 Day</option>
                                <option value="3">3 Days</option>
                                <option value="7">7 Days</option>
                                <option value="14">14 Days</option>
                                <option value="30">30 Days</option>
                            </select>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="form-group">
                            <label for="refresh-interval">Auto-refresh:</label>
                            <select class="form-control" id="refresh-interval">
                                <option value="0">Off</option>
                                <option value="10" selected>10 seconds</option>
                                <option value="30">30 seconds</option>
                                <option value="60">1 minute</option>
                                <option value="300">5 minutes</option>
                            </select>
                        </div>
                    </div>
                </div>
                <div class="row mt-3">
                    <div class="col-md-6">
                        <button id="refresh-btn" class="btn btn-primary">Refresh Now</button>
                        <span id="last-update" class="ms-3">Last update: Never</span>
                    </div>
                    <div class="col-md-6 text-end">
                        <button id="export-btn" class="btn btn-success">Export Data</button>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">Temperature (°C)</div>
                    <div class="card-body">
                        <div id="graph_temperature" class="graph-container">
                            <div class="loading">
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
                    <div class="card-header">Relative Humidity (%)</div>
                    <div class="card-body">
                        <div id="graph_humidity" class="graph-container">
                            <div class="loading">
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

        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">Absolute Humidity (g/m³)</div>
                    <div class="card-body">
                        <div id="graph_absolute_humidity" class="graph-container">
                            <div class="loading">
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
                    <div class="card-header">CO2 Concentration (ppm)</div>
                    <div class="card-body">
                        <div id="graph_co2" class="graph-container">
                            <div class="loading">
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

        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">Pressure (hPa)</div>
                    <div class="card-body">
                        <div id="graph_pressure" class="graph-container">
                            <div class="loading">
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
                    <div class="card-header">Gas Resistance (Ω)</div>
                    <div class="card-body">
                        <div id="graph_gas_resistance" class="graph-container">
                            <div class="loading">
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

        <div class="card mt-4">
            <div class="card-header">Connection Status</div>
            <div class="card-body">
                <div id="connection-status">
                    <div class="loading">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <p>Loading connection data...</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Export Modal -->
        <div class="modal fade" id="export-modal" tabindex="-1" aria-labelledby="export-modal-label" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="export-modal-label">Export Data</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label for="export-device">Device:</label>
                            <select class="form-control" id="export-device">
                                <option value="P2">P2</option>
                                <option value="P3">P3</option>
                                <option value="all">All Devices</option>
                            </select>
                        </div>
                        <div class="form-group mt-3">
                            <label for="export-start-date">Start Date:</label>
                            <input type="date" class="form-control" id="export-start-date">
                        </div>
                        <div class="form-group mt-3">
                            <label for="export-end-date">End Date:</label>
                            <input type="date" class="form-control" id="export-end-date">
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" id="export-confirm">Export</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Initialize variables
        let refreshTimer = null;
        const exportModal = new bootstrap.Modal(document.getElementById('export-modal'));
        
        // Set default dates for export
        const today = new Date();
        const oneWeekAgo = new Date();
        oneWeekAgo.setDate(today.getDate() - 7);
        
        document.getElementById('export-end-date').value = today.toISOString().split('T')[0];
        document.getElementById('export-start-date').value = oneWeekAgo.toISOString().split('T')[0];
        
        // Function to load all graphs
        function loadGraphs() {
            const days = document.getElementById('days-select').value;
            const showP2 = document.getElementById('show-p2').checked;
            const showP3 = document.getElementById('show-p3').checked;
            
            // Update last update time
            document.getElementById('last-update').textContent = `Last update: ${new Date().toLocaleTimeString()}`;
            
            // Load each graph
            const parameters = ['temperature', 'humidity', 'absolute_humidity', 'co2', 'pressure', 'gas_resistance'];
            
            parameters.forEach(param => {
                fetch(`/data/${param}?days=${days}&show_p2=${showP2}&show_p3=${showP3}`)
                    .then(response => response.json())
                    .then(data => {
                        // Clear loading indicator
                        document.getElementById(`graph_${param}`).innerHTML = '';
                        
                        // Check for errors
                        if (data.error) {
                            document.getElementById(`graph_${param}`).innerHTML = 
                                `<div class="alert alert-danger">${data.error}</div>`;
                            return;
                        }
                        
                        // Plot the graph
                        Plotly.newPlot(`graph_${param}`, data.data, data.layout);
                    })
                    .catch(error => {
                        document.getElementById(`graph_${param}`).innerHTML = 
                            `<div class="alert alert-danger">Error loading graph: ${error}</div>`;
                    });
            });
            
            // Load connection status
            loadConnectionStatus();
        }
        
        // Function to load connection status
        function loadConnectionStatus() {
            fetch('/api/connection/status')
                .then(response => response.json())
                .then(data => {
                    const statusDiv = document.getElementById('connection-status');
                    let html = '<div class="row">';
                    
                    if (data.P2) {
                        html += `
                            <div class="col-md-6">
                                <h5 class="p2-color">P2 Sensor Node</h5>
                                <table class="table table-sm">
                                    <tr>
                                        <th>Signal Strength:</th>
                                        <td>${data.P2.signal_strength} dBm</td>
                                    </tr>
                                    <tr>
                                        <th>Ping:</th>
                                        <td>${data.P2.ping_ms} ms</td>
                                    </tr>
                                    <tr>
                                        <th>Noise:</th>
                                        <td>${data.P2.noise} dBm</td>
                                    </tr>
                                    <tr>
                                        <th>Last Update:</th>
                                        <td>${data.P2.last_update}</td>
                                    </tr>
                                </table>
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
                    
                    if (data.P3) {
                        html += `
                            <div class="col-md-6">
                                <h5 class="p3-color">P3 Sensor Node</h5>
                                <table class="table table-sm">
                                    <tr>
                                        <th>Signal Strength:</th>
                                        <td>${data.P3.signal_strength} dBm</td>
                                    </tr>
                                    <tr>
                                        <th>Ping:</th>
                                        <td>${data.P3.ping_ms} ms</td>
                                    </tr>
                                    <tr>
                                        <th>Noise:</th>
                                        <td>${data.P3.noise} dBm</td>
                                    </tr>
                                    <tr>
                                        <th>Last Update:</th>
                                        <td>${data.P3.last_update}</td>
                                    </tr>
                                </table>
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
                    statusDiv.innerHTML = html;
                })
                .catch(error => {
                    document.getElementById('connection-status').innerHTML = 
                        `<div class="alert alert-danger">Error loading connection data: ${error}</div>`;
                });
        }
        
        // Function to set up auto-refresh
        function setupAutoRefresh() {
            // Clear existing timer
            if (refreshTimer) {
                clearInterval(refreshTimer);
                refreshTimer = null;
            }
            
            // Get refresh interval
            const interval = parseInt(document.getElementById('refresh-interval').value);
            
            // Set up new timer if interval > 0
            if (interval > 0) {
                refreshTimer = setInterval(loadGraphs, interval * 1000);
            }
        }
        
        // Event listeners
        document.getElementById('refresh-btn').addEventListener('click', loadGraphs);
        document.getElementById('refresh-interval').addEventListener('change', setupAutoRefresh);
        document.getElementById('days-select').addEventListener('change', loadGraphs);
        document.getElementById('show-p2').addEventListener('change', loadGraphs);
        document.getElementById('show-p3').addEventListener('change', loadGraphs);
        
        // Export functionality
        document.getElementById('export-btn').addEventListener('click', function() {
            exportModal.show();
        });
        
        document.getElementById('export-confirm').addEventListener('click', function() {
            const device = document.getElementById('export-device').value;
            const startDate = document.getElementById('export-start-date').value;
            const endDate = document.getElementById('export-end-date').value;
            
            window.location.href = `/api/export/${device}?start_date=${startDate}&end_date=${endDate}`;
            exportModal.hide();
        });
        
        // Initial load
        loadGraphs();
        setupAutoRefresh();
    </script>
</body>
</html>
"""

def read_csv_data(device_id, days=1):
    """Read data from CSV files for the specified device and time range."""
    # Define file paths
    if device_id == "P2":
        csv_path = os.path.join(DEFAULT_CONFIG["data_dir"], DEFAULT_CONFIG["rawdata_p2_dir"], "P2_fixed.csv")
    elif device_id == "P3":
        csv_path = os.path.join(DEFAULT_CONFIG["data_dir"], DEFAULT_CONFIG["rawdata_p3_dir"], "P3_fixed.csv")
    else:
        logger.error(f"Invalid device ID: {device_id}")
        return None
    
    # Check if file exists
    if not os.path.exists(csv_path):
        logger.warning(f"CSV file not found: {csv_path}")
        return None
    
    try:
        # Read CSV file
        df = pd.read_csv(csv_path)
        
        # Convert timestamp to datetime
        if 'timestamp' in df.columns:
            if df['timestamp'].dtype == 'int64' or df['timestamp'].dtype == 'float64':
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
            else:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
        # Drop rows with invalid timestamps
        df = df.dropna(subset=['timestamp'])
        
        # Filter data for the specified time range
        if days > 0:
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
            df = df[df['timestamp'] >= cutoff_date]
        
        # Sort by timestamp
        df = df.sort_values(by='timestamp')
        
        return df
    
    except Exception as e:
        logger.error(f"Error reading CSV file {csv_path}: {e}")
        return None

def generate_graph(parameter, days=1, show_p2=True, show_p3=True):
    """Generate a graph for the specified parameter."""
    # Define parameter labels
    label_map = {
        "temperature": "Temperature (°C)",
        "humidity": "Relative Humidity (%)",
        "absolute_humidity": "Absolute Humidity (g/m³)",
        "co2": "CO2 Concentration (ppm)",
        "pressure": "Pressure (hPa)",
        "gas_resistance": "Gas Resistance (Ω)"
    }
    label = label_map.get(parameter, parameter.capitalize())
    
    # Read data for P2 and P3
    df_p2 = read_csv_data("P2", days) if show_p2 else None
    df_p3 = read_csv_data("P3", days) if show_p3 else None
    
    # Check if we have any data
    if (df_p2 is None or df_p2.empty) and (df_p3 is None or df_p3.empty):
        logger.warning(f"No data available for {parameter}")
        return {"error": f"No data available for {parameter}"}
    
    # Create figure
    fig = go.Figure()
    
    # Add P2 data if available
    if show_p2 and df_p2 is not None and not df_p2.empty and parameter in df_p2.columns:
        # Check for valid data (at least 2 unique non-NaN values)
        p2_values = df_p2[parameter].dropna()
        if len(p2_values) > 0 and len(p2_values.unique()) >= 2:
            logger.info(f"Adding P2 data for {parameter}: {len(p2_values)} points, range: {p2_values.min()} - {p2_values.max()}")
            fig.add_trace(go.Scatter(
                x=df_p2['timestamp'],
                y=df_p2[parameter],
                mode='lines',
                name=f'P2 {parameter.capitalize()}',
                line=dict(color='blue')
            ))
        else:
            logger.warning(f"P2 data for {parameter} has insufficient unique values")
    
    # Add P3 data if available
    if show_p3 and df_p3 is not None and not df_p3.empty and parameter in df_p3.columns:
        # Check for valid data (at least 2 unique non-NaN values)
        p3_values = df_p3[parameter].dropna()
        if len(p3_values) > 0 and len(p3_values.unique()) >= 2:
            logger.info(f"Adding P3 data for {parameter}: {len(p3_values)} points, range: {p3_values.min()} - {p3_values.max()}")
            fig.add_trace(go.Scatter(
                x=df_p3['timestamp'],
                y=df_p3[parameter],
                mode='lines',
                name=f'P3 {parameter.capitalize()}',
                line=dict(color='red')
            ))
        else:
            logger.warning(f"P3 data for {parameter} has insufficient unique values")
    
    # Check if we have any traces
    if not fig.data:
        logger.warning(f"No valid data to plot for {parameter}")
        return {"error": f"No valid data to plot for {parameter}"}
    
    # Update layout
    fig.update_layout(
        title=f"{label} over time",
        xaxis_title="Time",
        yaxis_title=label,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode='closest',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Set Y-axis to auto-range
    fig.update_yaxes(autorange=True)
    
    return fig

@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template_string(TEMPLATE)

@app.route('/data/<parameter>')
def get_graph_data(parameter):
    """API endpoint to get graph data for a specific parameter."""
    days = request.args.get('days', default=1, type=int)
    show_p2 = request.args.get('show_p2', default='true').lower() == 'true'
    show_p3 = request.args.get('show_p3', default='true').lower() == 'true'
    
    # Generate graph
    fig = generate_graph(parameter, days, show_p2, show_p3)
    
    # Check for errors
    if isinstance(fig, dict) and "error" in fig:
        return jsonify(fig)
    
    # Return graph data
    return jsonify(fig.to_dict())

@app.route('/api/connection/status')
def get_connection_status():
    """API endpoint to get connection status for P2 and P3."""
    # This would normally call the connection monitor API
    # For now, we'll return dummy data
    status = {
        "P2": {
            "signal_strength": -65,
            "ping_ms": 12,
            "noise": -95,
            "last_update": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "P3": {
            "signal_strength": -70,
            "ping_ms": 15,
            "noise": -92,
            "last_update": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }
    
    return jsonify(status)

@app.route('/api/export/<device_id>')
def export_data(device_id):
    """API endpoint to export data for a specific device or all devices."""
    if device_id not in ["P2", "P3", "all"]:
        return jsonify({"error": "Invalid device ID"}), 400
    
    start_date = request.args.get('start_date', default=(datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d"))
    end_date = request.args.get('end_date', default=datetime.datetime.now().strftime("%Y-%m-%d"))
    
    try:
        # Parse dates
        start_date_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_date_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        
        # Read data
        if device_id == "all":
            df_p2 = read_csv_data("P2")
            df_p3 = read_csv_data("P3")
            
            # Filter by date range
            if df_p2 is not None:
                df_p2 = df_p2[(df_p2['timestamp'].dt.date >= start_date_dt.date()) & 
                              (df_p2['timestamp'].dt.date <= end_date_dt.date())]
            
            if df_p3 is not None:
                df_p3 = df_p3[(df_p3['timestamp'].dt.date >= start_date_dt.date()) & 
                              (df_p3['timestamp'].dt.date <= end_date_dt.date())]
            
            # Combine data
            if df_p2 is not None and df_p3 is not None:
                df = pd.concat([df_p2, df_p3], ignore_index=True)
            elif df_p2 is not None:
                df = df_p2
            elif df_p3 is not None:
                df = df_p3
            else:
                return jsonify({"error": "No data available for export"}), 404
        else:
            df = read_csv_data(device_id)
            
            # Filter by date range
            if df is not None:
                df = df[(df['timestamp'].dt.date >= start_date_dt.date()) & 
                        (df['timestamp'].dt.date <= end_date_dt.date())]
            else:
                return jsonify({"error": "No data available for export"}), 404
        
        # Check if we have any data
        if df is None or df.empty:
            return jsonify({"error": "No data available for the specified date range"}), 404
        
        # Create temporary file for download
        temp_file = os.path.join(DEFAULT_CONFIG["data_dir"], f"export_{device_id}_{int(time.time())}.csv")
        df.to_csv(temp_file, index=False)
        
        return send_file(temp_file, 
                        mimetype='text/csv',
                        as_attachment=True,
                        download_name=f"{device_id}_data_{start_date}_to_{end_date}.csv")
    
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        return jsonify({"error": f"Error exporting data: {e}"}), 500

def main():
    """Main function to run the web interface."""
    parser = argparse.ArgumentParser(description='Environmental Data Web Interface - Simple Version')
    parser.add_argument('--port', type=int, help='Port to listen on')
    parser.add_argument('--data-dir', type=str, help='Directory to read data from')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    # Update configuration
    if args.port:
        DEFAULT_CONFIG["web_port"] = args.port
    
    if args.data_dir:
        DEFAULT_CONFIG["data_dir"] = args.data_dir
    
    if args.debug:
        DEFAULT_CONFIG["debug_mode"] = True
    
    # Start the web server
    app.run(host='0.0.0.0', port=DEFAULT_CONFIG["web_port"], debug=DEFAULT_CONFIG["debug_mode"])

if __name__ == "__main__":
    main()
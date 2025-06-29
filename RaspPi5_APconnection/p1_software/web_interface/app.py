#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi 5 Environmental Data Web Interface
Version: 1.0.0

This module provides a web interface for visualizing environmental data
collected from P2 and P3 sensor nodes. It displays real-time data,
historical trends, and allows for data export.

Features:
- Real-time display of current sensor readings
- Time-series graphs of historical data
- Data export in CSV format
- Responsive design for mobile and desktop viewing
- Auto-refresh functionality

Requirements:
- Python 3.7+
- Flask for the web server
- Pandas for data manipulation
- Plotly for interactive graphs

Usage:
    python3 app.py [--port PORT] [--data-dir DIR]
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/web_interface.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "web_port": 80,
    "data_dir": "/var/lib/raspap/data",
    "api_url": "http://localhost:5001",
    "refresh_interval": 30,  # seconds
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
        
        # Ensure the data directory exists
        os.makedirs(self.config["data_dir"], exist_ok=True)
    
    def get_latest_data(self):
        """Get the latest data from the API or cached data."""
        try:
            # In a real implementation, this would call the API
            # For now, we'll simulate by reading the latest data from CSV files
            with self.lock:
                latest_data = self.last_data.copy()
            
            if not latest_data:
                # If no data in cache, try to read from CSV
                today = datetime.datetime.now().strftime("%Y-%m-%d")
                for device in ["P2", "P3"]:
                    csv_path = os.path.join(self.config["data_dir"], f"{device}_{today}.csv")
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
    
    def get_historical_data(self, device_id, days=1):
        """Get historical data for the specified device."""
        if device_id not in ["P2", "P3"]:
            return None
        
        # Check if we have cached data and it's still valid
        if self.data_cache[device_id] is not None:
            cache_time, df = self.data_cache[device_id]
            if (datetime.datetime.now() - cache_time).total_seconds() < 60:  # Cache for 1 minute
                return df
        
        try:
            # Calculate date range
            end_date = datetime.datetime.now()
            start_date = end_date - datetime.timedelta(days=days)
            
            # Get list of CSV files in date range
            data_frames = []
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                csv_path = os.path.join(self.config["data_dir"], f"{device_id}_{date_str}.csv")
                
                if os.path.exists(csv_path):
                    try:
                        df = pd.read_csv(csv_path)
                        data_frames.append(df)
                    except Exception as e:
                        logger.error(f"Error reading CSV {csv_path}: {e}")
                
                current_date += datetime.timedelta(days=1)
            
            # Combine all data frames
            if data_frames:
                combined_df = pd.concat(data_frames, ignore_index=True)
                
                # Convert timestamp to datetime
                combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
                
                # Sort by timestamp
                combined_df = combined_df.sort_values('timestamp')
                
                # Limit to the last N points for performance
                if len(combined_df) > self.config["graph_points"]:
                    combined_df = combined_df.tail(self.config["graph_points"])
                
                # Cache the result
                self.data_cache[device_id] = (datetime.datetime.now(), combined_df)
                
                return combined_df
            else:
                logger.warning(f"No data found for {device_id} in the specified date range")
                return None
        except Exception as e:
            logger.error(f"Error getting historical data for {device_id}: {e}")
            return None
    
    def create_time_series_graph(self, device_id, parameter, days=1):
        """Create a time series graph for the specified parameter."""
        df = self.get_historical_data(device_id, days)
        
        if df is None or df.empty:
            return None
        
        try:
            # Create the graph
            fig = px.line(
                df, 
                x='timestamp', 
                y=parameter,
                title=f"{parameter.capitalize()} over time for {device_id}",
                labels={
                    'timestamp': 'Time',
                    parameter: parameter.capitalize()
                }
            )
            
            # Customize layout
            fig.update_layout(
                margin=dict(l=20, r=20, t=40, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                hovermode='closest'
            )
            
            return fig.to_json()
        except Exception as e:
            logger.error(f"Error creating graph for {device_id} {parameter}: {e}")
            return None
    
    def create_dashboard_graphs(self, device_id, days=1):
        """Create all graphs for the dashboard."""
        parameters = ['temperature', 'humidity', 'pressure', 'gas_resistance', 'co2_level']
        graphs = {}
        
        for param in parameters:
            graph_json = self.create_time_series_graph(device_id, param, days)
            if graph_json:
                graphs[param] = graph_json
        
        return graphs
    
    def export_csv(self, device_id, start_date, end_date):
        """Export data to CSV for the specified date range."""
        if device_id not in ["P2", "P3"]:
            return None
        
        try:
            # Parse dates
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            
            # Get list of CSV files in date range
            data_frames = []
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                csv_path = os.path.join(self.config["data_dir"], f"{device_id}_{date_str}.csv")
                
                if os.path.exists(csv_path):
                    try:
                        df = pd.read_csv(csv_path)
                        data_frames.append(df)
                    except Exception as e:
                        logger.error(f"Error reading CSV {csv_path}: {e}")
                
                current_date += datetime.timedelta(days=1)
            
            # Combine all data frames
            if data_frames:
                combined_df = pd.concat(data_frames, ignore_index=True)
                
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

@app.route('/dashboard/<device_id>')
def dashboard(device_id):
    """Render the dashboard for a specific device."""
    if device_id not in ["P2", "P3"]:
        return "Invalid device ID", 400
    
    days = request.args.get('days', default=1, type=int)
    
    return render_template('dashboard.html',
                          device_id=device_id,
                          days=days,
                          refresh_interval=visualizer.config["refresh_interval"],
                          last_update=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@app.route('/api/latest')
def get_latest_data():
    """API endpoint to get the latest data."""
    return jsonify(visualizer.get_latest_data())

@app.route('/api/device/<device_id>')
def get_device_data(device_id):
    """API endpoint to get data for a specific device."""
    if device_id not in ["P2", "P3"]:
        return jsonify({"error": "Invalid device ID"}), 400
    
    latest_data = visualizer.get_latest_data()
    
    if device_id in latest_data:
        return jsonify(latest_data[device_id])
    else:
        return jsonify({"error": "No data available for this device"}), 404

@app.route('/api/graphs/<device_id>')
def get_graphs(device_id):
    """API endpoint to get graphs for a specific device."""
    if device_id not in ["P2", "P3"]:
        return jsonify({"error": "Invalid device ID"}), 400
    
    days = request.args.get('days', default=1, type=int)
    
    graphs = visualizer.create_dashboard_graphs(device_id, days)
    
    if graphs:
        return jsonify(graphs)
    else:
        return jsonify({"error": "No data available for graphs"}), 404

@app.route('/api/export/<device_id>')
def export_data(device_id):
    """API endpoint to export data for a specific device."""
    if device_id not in ["P2", "P3"]:
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
    <title>{% block title %}Environmental Data Monitor{% endblock %}</title>
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
    </style>
    {% block head %}{% endblock %}
</head>
<body>
    <div class="container">
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary rounded">
            <div class="container-fluid">
                <a class="navbar-brand" href="/">Environmental Data Monitor</a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav">
                        <li class="nav-item">
                            <a class="nav-link" href="/">Home</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/dashboard/P2">P2 Dashboard</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/dashboard/P3">P3 Dashboard</a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>
        
        {% block content %}{% endblock %}
        
        <footer class="mt-5 text-center text-muted">
            <p>Raspberry Pi 5 Environmental Data Monitor v1.0.0</p>
        </footer>
    </div>
    
    {% block scripts %}{% endblock %}
</body>
</html>
"""
    
    # Create index template
    index_html = """{% extends "base.html" %}

{% block title %}Environmental Data Monitor - Home{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <div class="card">
            <div class="card-header">
                System Overview
            </div>
            <div class="card-body">
                <p>Welcome to the Environmental Data Monitoring System. This interface allows you to view real-time and historical environmental data collected by the P2 and P3 sensor nodes.</p>
                <p>Select a device dashboard below to view detailed information:</p>
                <div class="row mt-4">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">P2 Sensor Node</div>
                            <div class="card-body" id="p2-overview">
                                <div class="text-center">
                                    <div class="spinner-border text-primary" role="status">
                                        <span class="visually-hidden">Loading...</span>
                                    </div>
                                    <p>Loading data...</p>
                                </div>
                            </div>
                            <div class="card-footer">
                                <a href="/dashboard/P2" class="btn btn-primary">View Dashboard</a>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">P3 Sensor Node</div>
                            <div class="card-body" id="p3-overview">
                                <div class="text-center">
                                    <div class="spinner-border text-primary" role="status">
                                        <span class="visually-hidden">Loading...</span>
                                    </div>
                                    <p>Loading data...</p>
                                </div>
                            </div>
                            <div class="card-footer">
                                <a href="/dashboard/P3" class="btn btn-primary">View Dashboard</a>
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
    // Function to update the overview data
    function updateOverview() {
        $.ajax({
            url: '/api/latest',
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                // Update P2 overview
                if (data.P2) {
                    var p2Html = `
                        <div class="row">
                            <div class="col-6">
                                <p>Temperature</p>
                                <p class="data-value">${parseFloat(data.P2.temperature).toFixed(1)}<span class="data-unit">°C</span></p>
                            </div>
                            <div class="col-6">
                                <p>Humidity</p>
                                <p class="data-value">${parseFloat(data.P2.humidity).toFixed(1)}<span class="data-unit">%</span></p>
                            </div>
                        </div>
                        <div class="row mt-3">
                            <div class="col-6">
                                <p>CO2 Level</p>
                                <p class="data-value">${parseFloat(data.P2.co2_level).toFixed(0)}<span class="data-unit">ppm</span></p>
                            </div>
                            <div class="col-6">
                                <p>Last Reading</p>
                                <p class="data-value">${data.P2.timestamp.split(' ')[1]}</p>
                            </div>
                        </div>
                    `;
                    $('#p2-overview').html(p2Html);
                } else {
                    $('#p2-overview').html('<div class="alert alert-warning">No data available</div>');
                }
                
                // Update P3 overview
                if (data.P3) {
                    var p3Html = `
                        <div class="row">
                            <div class="col-6">
                                <p>Temperature</p>
                                <p class="data-value">${parseFloat(data.P3.temperature).toFixed(1)}<span class="data-unit">°C</span></p>
                            </div>
                            <div class="col-6">
                                <p>Humidity</p>
                                <p class="data-value">${parseFloat(data.P3.humidity).toFixed(1)}<span class="data-unit">%</span></p>
                            </div>
                        </div>
                        <div class="row mt-3">
                            <div class="col-6">
                                <p>CO2 Level</p>
                                <p class="data-value">${parseFloat(data.P3.co2_level).toFixed(0)}<span class="data-unit">ppm</span></p>
                            </div>
                            <div class="col-6">
                                <p>Last Reading</p>
                                <p class="data-value">${data.P3.timestamp.split(' ')[1]}</p>
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
                $('#p2-overview').html('<div class="alert alert-danger">Error loading data</div>');
                $('#p3-overview').html('<div class="alert alert-danger">Error loading data</div>');
            }
        });
    }
    
    // Update data on page load
    $(document).ready(function() {
        updateOverview();
        
        // Set up auto-refresh
        setInterval(updateOverview, {{ refresh_interval * 1000 }});
    });
</script>
{% endblock %}
"""
    
    # Create dashboard template
    dashboard_html = """{% extends "base.html" %}

{% block title %}{{ device_id }} Dashboard{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <span>{{ device_id }} Dashboard</span>
                <div class="btn-group" role="group">
                    <a href="/dashboard/{{ device_id }}?days=1" class="btn btn-sm btn-outline-light {% if days == 1 %}active{% endif %}">1 Day</a>
                    <a href="/dashboard/{{ device_id }}?days=7" class="btn btn-sm btn-outline-light {% if days == 7 %}active{% endif %}">1 Week</a>
                    <a href="/dashboard/{{ device_id }}?days=30" class="btn btn-sm btn-outline-light {% if days == 30 %}active{% endif %}">1 Month</a>
                </div>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-header">Current Readings</div>
                            <div class="card-body" id="current-readings">
                                <div class="text-center">
                                    <div class="spinner-border text-primary" role="status">
                                        <span class="visually-hidden">Loading...</span>
                                    </div>
                                    <p>Loading data...</p>
                                </div>
                            </div>
                        </div>
                        
                        <div class="card mt-3">
                            <div class="card-header">Export Data</div>
                            <div class="card-body">
                                <form id="export-form">
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
                                    <div class="text-center">
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
                                    <div class="text-center">
                                        <div class="spinner-border text-primary" role="status">
                                            <span class="visually-hidden">Loading...</span>
                                        </div>
                                        <p>Loading graph...</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="card mt-3">
                            <div class="card-header">CO2 Level (ppm)</div>
                            <div class="card-body">
                                <div id="co2-graph" class="graph-container">
                                    <div class="text-center">
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
                                            <div class="text-center">
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
                                            <div class="text-center">
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
        $.ajax({
            url: '/api/device/{{ device_id }}',
            type: 'GET',
            dataType: 'json',
            success: function(data) {
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
                        <div class="row mt-3">
                            <div class="col-6">
                                <p>Pressure</p>
                                <p class="data-value">${parseFloat(data.pressure).toFixed(1)}<span class="data-unit">hPa</span></p>
                            </div>
                            <div class="col-6">
                                <p>Gas Resistance</p>
                                <p class="data-value">${parseFloat(data.gas_resistance).toFixed(0)}<span class="data-unit">Ω</span></p>
                            </div>
                        </div>
                        <div class="row mt-3">
                            <div class="col-6">
                                <p>CO2 Level</p>
                                <p class="data-value">${parseFloat(data.co2_level).toFixed(0)}<span class="data-unit">ppm</span></p>
                            </div>
                            <div class="col-6">
                                <p>Last Reading</p>
                                <p class="data-value">${data.timestamp.split(' ')[1]}</p>
                            </div>
                        </div>
                    `;
                    $('#current-readings').html(html);
                } else {
                    $('#current-readings').html('<div class="alert alert-warning">No data available</div>');
                }
                
                // Update last update time
                $('#last-update').text(new Date().toLocaleString());
            },
            error: function() {
                $('#current-readings').html('<div class="alert alert-danger">Error loading data</div>');
            }
        });
    }
    
    // Function to update the graphs
    function updateGraphs() {
        $.ajax({
            url: '/api/graphs/{{ device_id }}?days={{ days }}',
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                if (data && !data.error) {
                    // Update temperature graph
                    if (data.temperature) {
                        var tempGraph = JSON.parse(data.temperature);
                        Plotly.newPlot('temperature-graph', tempGraph.data, tempGraph.layout);
                    } else {
                        $('#temperature-graph').html('<div class="alert alert-warning">No temperature data available</div>');
                    }
                    
                    // Update humidity graph
                    if (data.humidity) {
                        var humidityGraph = JSON.parse(data.humidity);
                        Plotly.newPlot('humidity-graph', humidityGraph.data, humidityGraph.layout);
                    } else {
                        $('#humidity-graph').html('<div class="alert alert-warning">No humidity data available</div>');
                    }
                    
                    // Update CO2 graph
                    if (data.co2_level) {
                        var co2Graph = JSON.parse(data.co2_level);
                        Plotly.newPlot('co2-graph', co2Graph.data, co2Graph.layout);
                    } else {
                        $('#co2-graph').html('<div class="alert alert-warning">No CO2 data available</div>');
                    }
                    
                    // Update pressure graph
                    if (data.pressure) {
                        var pressureGraph = JSON.parse(data.pressure);
                        Plotly.newPlot('pressure-graph', pressureGraph.data, pressureGraph.layout);
                    } else {
                        $('#pressure-graph').html('<div class="alert alert-warning">No pressure data available</div>');
                    }
                    
                    // Update gas resistance graph
                    if (data.gas_resistance) {
                        var gasGraph = JSON.parse(data.gas_resistance);
                        Plotly.newPlot('gas-graph', gasGraph.data, gasGraph.layout);
                    } else {
                        $('#gas-graph').html('<div class="alert alert-warning">No gas resistance data available</div>');
                    }
                } else {
                    $('.graph-container').html('<div class="alert alert-warning">No data available for graphs</div>');
                }
            },
            error: function() {
                $('.graph-container').html('<div class="alert alert-danger">Error loading graphs</div>');
            }
        });
    }
    
    // Set up export form
    function setupExportForm() {
        // Set default dates (last 7 days)
        var today = new Date();
        var lastWeek = new Date();
        lastWeek.setDate(today.getDate() - 7);
        
        $('#end-date').val(today.toISOString().split('T')[0]);
        $('#start-date').val(lastWeek.toISOString().split('T')[0]);
        
        // Handle form submission
        $('#export-form').submit(function(e) {
            e.preventDefault();
            
            var startDate = $('#start-date').val();
            var endDate = $('#end-date').val();
            
            if (!startDate || !endDate) {
                alert('Please select both start and end dates');
                return;
            }
            
            // Redirect to export URL
            window.location.href = '/api/export/{{ device_id }}?start_date=' + startDate + '&end_date=' + endDate;
        });
    }
    
    // Update data on page load
    $(document).ready(function() {
        updateCurrentReadings();
        updateGraphs();
        setupExportForm();
        
        // Set up auto-refresh
        setInterval(function() {
            updateCurrentReadings();
            // Don't auto-refresh graphs to save bandwidth
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
    """Main function to parse arguments and start the web interface."""
    parser = argparse.ArgumentParser(description="Raspberry Pi 5 Environmental Data Web Interface")
    parser.add_argument("--port", type=int, default=DEFAULT_CONFIG["web_port"],
                        help=f"Port to listen on (default: {DEFAULT_CONFIG['web_port']})")
    parser.add_argument("--data-dir", type=str, default=DEFAULT_CONFIG["data_dir"],
                        help=f"Directory to read data from (default: {DEFAULT_CONFIG['data_dir']})")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Update configuration with command-line arguments
    config = DEFAULT_CONFIG.copy()
    config["web_port"] = args.port
    config["data_dir"] = args.data_dir
    config["debug_mode"] = args.debug
    
    # Create templates
    create_templates()
    
    # Create global visualizer instance
    global visualizer
    visualizer = DataVisualizer(config)
    
    # Start the web server
    print(f"Web interface running on port {config['web_port']}")
    print("Press Ctrl+C to stop")
    
    app.run(host='0.0.0.0', port=config['web_port'], debug=config['debug_mode'])

if __name__ == "__main__":
    main()
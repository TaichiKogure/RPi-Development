#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi 5 Environmental Data Web Interface - Modular Version
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
    python3 P1_app_simple44_modular.py [--port PORT] [--data-dir DIR]
"""

import os
import sys
import argparse
import logging
from flask import Flask

# モジュールのインポート
from modules import read_csv_data, get_latest_data, calculate_absolute_humidity
from modules import generate_graph, generate_all_graphs, PARAMETER_LABELS
from modules import setup_routes

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/web_interface_simple44_modular.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# デフォルト設定
DEFAULT_CONFIG = {
    "web_port": 80,
    "data_dir": "/var/lib/raspap_solo/data",
    "rawdata_p2_dir": "RawData_P2",
    "rawdata_p3_dir": "RawData_P3",
    "refresh_interval": 10,  # seconds
    "graph_points": 100,  # number of data points to show in graphs
    "debug_mode": False
}

# HTMLテンプレート（Plotly.js統合）
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
        
        <!-- Control Panel -->
        <div class="card control-panel">
            <div class="card-header">Control Panel</div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-3">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="showP2" checked>
                            <label class="form-check-label p2-color" for="showP2">
                                Show P2 Data
                            </label>
                        </div>
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="showP3" checked>
                            <label class="form-check-label p3-color" for="showP3">
                                Show P3 Data
                            </label>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="form-group">
                            <label for="timeRange">Time Range:</label>
                            <select class="form-control" id="timeRange">
                                <option value="1">1 Day</option>
                                <option value="3">3 Days</option>
                                <option value="7">7 Days</option>
                                <option value="14">14 Days</option>
                                <option value="30">30 Days</option>
                            </select>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="form-group">
                            <label for="refreshInterval">Auto Refresh:</label>
                            <select class="form-control" id="refreshInterval">
                                <option value="0">Off</option>
                                <option value="10" selected>10 seconds</option>
                                <option value="30">30 seconds</option>
                                <option value="60">1 minute</option>
                                <option value="300">5 minutes</option>
                            </select>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <button id="refreshButton" class="btn btn-primary mt-4">Refresh Now</button>
                        <button id="exportButton" class="btn btn-success mt-4">Export Data</button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Latest Data -->
        <div class="card">
            <div class="card-header">Latest Readings</div>
            <div class="card-body">
                <div class="row" id="latestData">
                    <div class="col-md-6">
                        <h5 class="p2-color">P2 Sensor</h5>
                        <div id="p2-latest" class="loading">Loading latest data...</div>
                    </div>
                    <div class="col-md-6">
                        <h5 class="p3-color">P3 Sensor</h5>
                        <div id="p3-latest" class="loading">Loading latest data...</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Connection Status -->
        <div class="card">
            <div class="card-header">Connection Status</div>
            <div class="card-body">
                <div class="row" id="connectionStatus">
                    <div class="col-md-6">
                        <h5 class="p2-color">P2 Connection</h5>
                        <div id="p2-connection" class="loading">Loading connection data...</div>
                    </div>
                    <div class="col-md-6">
                        <h5 class="p3-color">P3 Connection</h5>
                        <div id="p3-connection" class="loading">Loading connection data...</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Graphs -->
        <div class="card">
            <div class="card-header">Temperature</div>
            <div class="card-body">
                <div id="temperature-graph" class="graph-container loading">Loading graph...</div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">Humidity</div>
            <div class="card-body">
                <div id="humidity-graph" class="graph-container loading">Loading graph...</div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">Absolute Humidity</div>
            <div class="card-body">
                <div id="absolute_humidity-graph" class="graph-container loading">Loading graph...</div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">CO2 Concentration</div>
            <div class="card-body">
                <div id="co2-graph" class="graph-container loading">Loading graph...</div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">Pressure</div>
            <div class="card-body">
                <div id="pressure-graph" class="graph-container loading">Loading graph...</div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">Gas Resistance</div>
            <div class="card-body">
                <div id="gas_resistance-graph" class="graph-container loading">Loading graph...</div>
            </div>
        </div>
    </div>
    
    <!-- Export Modal -->
    <div class="modal fade" id="exportModal" tabindex="-1" aria-labelledby="exportModalLabel" aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="exportModalLabel">Export Data</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label for="exportDevice">Device:</label>
                        <select class="form-control" id="exportDevice">
                            <option value="P2">P2</option>
                            <option value="P3">P3</option>
                            <option value="all">All Devices</option>
                        </select>
                    </div>
                    <div class="form-group mt-3">
                        <label for="exportStartDate">Start Date:</label>
                        <input type="date" class="form-control" id="exportStartDate">
                    </div>
                    <div class="form-group mt-3">
                        <label for="exportEndDate">End Date:</label>
                        <input type="date" class="form-control" id="exportEndDate">
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    <button type="button" class="btn btn-primary" id="doExport">Export</button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
        // Initialize Bootstrap modal
        var exportModal = new bootstrap.Modal(document.getElementById('exportModal'));
        
        // Set default dates for export
        document.getElementById('exportStartDate').valueAsDate = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
        document.getElementById('exportEndDate').valueAsDate = new Date();
        
        // Function to load graph data
        function loadGraph(parameter) {
            const days = document.getElementById('timeRange').value;
            const showP2 = document.getElementById('showP2').checked;
            const showP3 = document.getElementById('showP3').checked;
            
            // Show loading indicator
            document.getElementById(`${parameter}-graph`).innerHTML = 'Loading graph...';
            document.getElementById(`${parameter}-graph`).classList.add('loading');
            
            fetch(`/data/${parameter}?days=${days}&show_p2=${showP2}&show_p3=${showP3}`)
                .then(response => response.json())
                .then(data => {
                    // Remove loading indicator
                    document.getElementById(`${parameter}-graph`).classList.remove('loading');
                    
                    if (data.error) {
                        document.getElementById(`${parameter}-graph`).innerHTML = `<div class="alert alert-warning">${data.error}</div>`;
                    } else {
                        Plotly.newPlot(`${parameter}-graph`, JSON.parse(data));
                    }
                })
                .catch(error => {
                    document.getElementById(`${parameter}-graph`).classList.remove('loading');
                    document.getElementById(`${parameter}-graph`).innerHTML = `<div class="alert alert-danger">Error loading graph: ${error}</div>`;
                });
        }
        
        // Function to load all graphs
        function loadGraphs() {
            loadGraph('temperature');
            loadGraph('humidity');
            loadGraph('absolute_humidity');
            loadGraph('co2');
            loadGraph('pressure');
            loadGraph('gas_resistance');
        }
        
        // Function to load latest data
        function loadLatestData() {
            // P2 latest data
            fetch('/api/latest/P2')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        document.getElementById('p2-latest').innerHTML = `<div class="alert alert-warning">${data.error}</div>`;
                    } else {
                        let html = '<table class="table table-sm">';
                        html += `<tr><td>Timestamp:</td><td>${data.timestamp}</td></tr>`;
                        html += `<tr><td>Temperature:</td><td>${data.temperature} °C</td></tr>`;
                        html += `<tr><td>Humidity:</td><td>${data.humidity} %</td></tr>`;
                        html += `<tr><td>Absolute Humidity:</td><td>${data.absolute_humidity} g/m³</td></tr>`;
                        html += `<tr><td>CO2:</td><td>${data.co2} ppm</td></tr>`;
                        html += `<tr><td>Pressure:</td><td>${data.pressure} hPa</td></tr>`;
                        html += `<tr><td>Gas Resistance:</td><td>${data.gas_resistance} Ω</td></tr>`;
                        html += '</table>';
                        document.getElementById('p2-latest').innerHTML = html;
                    }
                })
                .catch(error => {
                    document.getElementById('p2-latest').innerHTML = `<div class="alert alert-danger">Error loading data: ${error}</div>`;
                });
            
            // P3 latest data
            fetch('/api/latest/P3')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        document.getElementById('p3-latest').innerHTML = `<div class="alert alert-warning">${data.error}</div>`;
                    } else {
                        let html = '<table class="table table-sm">';
                        html += `<tr><td>Timestamp:</td><td>${data.timestamp}</td></tr>`;
                        html += `<tr><td>Temperature:</td><td>${data.temperature} °C</td></tr>`;
                        html += `<tr><td>Humidity:</td><td>${data.humidity} %</td></tr>`;
                        html += `<tr><td>Absolute Humidity:</td><td>${data.absolute_humidity} g/m³</td></tr>`;
                        html += `<tr><td>CO2:</td><td>${data.co2} ppm</td></tr>`;
                        html += `<tr><td>Pressure:</td><td>${data.pressure} hPa</td></tr>`;
                        html += `<tr><td>Gas Resistance:</td><td>${data.gas_resistance} Ω</td></tr>`;
                        html += '</table>';
                        document.getElementById('p3-latest').innerHTML = html;
                    }
                })
                .catch(error => {
                    document.getElementById('p3-latest').innerHTML = `<div class="alert alert-danger">Error loading data: ${error}</div>`;
                });
        }
        
        // Function to load connection status
        function loadConnectionStatus() {
            fetch('/api/connection/status')
                .then(response => response.json())
                .then(data => {
                    // P2 connection status
                    let p2Html = '<table class="table table-sm">';
                    p2Html += `<tr><td>Signal Strength:</td><td>${data.P2.signal_strength} dBm</td></tr>`;
                    p2Html += `<tr><td>Ping:</td><td>${data.P2.ping_ms} ms</td></tr>`;
                    p2Html += `<tr><td>Noise:</td><td>${data.P2.noise} dBm</td></tr>`;
                    p2Html += `<tr><td>Last Update:</td><td>${data.P2.last_update}</td></tr>`;
                    p2Html += '</table>';
                    document.getElementById('p2-connection').innerHTML = p2Html;
                    
                    // P3 connection status
                    let p3Html = '<table class="table table-sm">';
                    p3Html += `<tr><td>Signal Strength:</td><td>${data.P3.signal_strength} dBm</td></tr>`;
                    p3Html += `<tr><td>Ping:</td><td>${data.P3.ping_ms} ms</td></tr>`;
                    p3Html += `<tr><td>Noise:</td><td>${data.P3.noise} dBm</td></tr>`;
                    p3Html += `<tr><td>Last Update:</td><td>${data.P3.last_update}</td></tr>`;
                    p3Html += '</table>';
                    document.getElementById('p3-connection').innerHTML = p3Html;
                })
                .catch(error => {
                    document.getElementById('p2-connection').innerHTML = `<div class="alert alert-danger">Error loading connection status: ${error}</div>`;
                    document.getElementById('p3-connection').innerHTML = `<div class="alert alert-danger">Error loading connection status: ${error}</div>`;
                });
        }
        
        // Function to set up auto-refresh
        function setupAutoRefresh() {
            const interval = document.getElementById('refreshInterval').value;
            if (window.refreshTimer) {
                clearInterval(window.refreshTimer);
                window.refreshTimer = null;
            }
            
            if (interval > 0) {
                window.refreshTimer = setInterval(() => {
                    loadGraphs();
                    loadLatestData();
                    loadConnectionStatus();
                }, interval * 1000);
            }
        }
        
        // Event listeners
        document.getElementById('refreshButton').addEventListener('click', () => {
            loadGraphs();
            loadLatestData();
            loadConnectionStatus();
        });
        
        document.getElementById('showP2').addEventListener('change', loadGraphs);
        document.getElementById('showP3').addEventListener('change', loadGraphs);
        document.getElementById('timeRange').addEventListener('change', loadGraphs);
        document.getElementById('refreshInterval').addEventListener('change', setupAutoRefresh);
        
        document.getElementById('exportButton').addEventListener('click', () => {
            exportModal.show();
        });
        
        document.getElementById('doExport').addEventListener('click', () => {
            const device = document.getElementById('exportDevice').value;
            const startDate = document.getElementById('exportStartDate').value;
            const endDate = document.getElementById('exportEndDate').value;
            
            window.location.href = `/api/export/${device}?start_date=${startDate}&end_date=${endDate}`;
            exportModal.hide();
        });
        
        // Initial load
        loadGraphs();
        loadLatestData();
        loadConnectionStatus();
        setupAutoRefresh();
    </script>
</body>
</html>
"""

def main():
    """メイン関数：Webインターフェースを実行します。"""
    parser = argparse.ArgumentParser(description='Environmental Data Web Interface - Modular Version')
    parser.add_argument('--port', type=int, default=DEFAULT_CONFIG["web_port"],
                        help=f'Port to listen on (default: {DEFAULT_CONFIG["web_port"]})')
    parser.add_argument('--data-dir', type=str, default=DEFAULT_CONFIG["data_dir"],
                        help=f'Directory to read data from (default: {DEFAULT_CONFIG["data_dir"]})')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode')
    
    args = parser.parse_args()
    
    # 設定の更新
    config = DEFAULT_CONFIG.copy()
    config["web_port"] = args.port
    config["data_dir"] = args.data_dir
    config["debug_mode"] = args.debug
    
    # Flaskアプリの初期化
    app = Flask(__name__)
    
    # APIルートの設定
    app = setup_routes(app, TEMPLATE, config)
    
    # 追加のAPIエンドポイント
    @app.route('/api/latest/<device_id>')
    def get_latest_device_data(device_id):
        """最新のデバイスデータを取得するAPIエンドポイント。"""
        if device_id not in ["P2", "P3"]:
            return jsonify({"error": "無効なデバイスID"}), 400
        
        latest_data = get_latest_data(device_id, config)
        if latest_data is None:
            return jsonify({"error": f"{device_id}のデータがありません"}), 404
        
        # 絶対湿度の計算
        if 'temperature' in latest_data and 'humidity' in latest_data:
            latest_data['absolute_humidity'] = calculate_absolute_humidity(
                latest_data['temperature'], latest_data['humidity']
            )
        
        return jsonify(latest_data)
    
    # アプリの実行
    logger.info(f"Starting web interface on port {config['web_port']}")
    app.run(host='0.0.0.0', port=config['web_port'], debug=config['debug_mode'])

if __name__ == "__main__":
    main()
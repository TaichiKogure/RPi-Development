#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi 5 Environmental Data Web Interface
Version: 4.5.3-solo-Uni
Date: 2025-07-06

This module provides a web interface for displaying real-time environmental data
collected from P2 and P3 sensor nodes with BME680 and MH-Z19C sensors. It displays real-time data,
connection status information, and historical data graphs.

Features:
- Real-time display of current sensor readings from both P2 and P3 (including CO2)
- Connection status monitoring (signal strength, ping, noise)
- Historical data visualization with interactive graphs
- Automatic periodic data loading or manual button-triggered loading
- Customizable time range for displayed data
- Data export in CSV format
- Responsive design for mobile and desktop viewing

Requirements:
- Python 3.7+
- Flask for the web server
- Pandas for data manipulation
- Plotly for interactive graphs
- Requests for API communication

Usage:
    python3 P1_app_simple45_Uni.py [--port PORT] [--data-dir DIR]
"""

import os
import sys
import time
import json
import argparse
import logging
import datetime
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import requests
from flask import Flask, render_template_string, jsonify, request, send_file, Response

def jsonify_numpy(obj):
    """Convert NumPy arrays to Python lists for JSON serialization.

    Args:
        obj: The object to convert (can be a dict, list, or NumPy array)

    Returns:
        The converted object with NumPy arrays replaced by Python lists
    """
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: jsonify_numpy(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [jsonify_numpy(i) for i in obj]
    return obj

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/web_interface_simple45_Uni.log"),
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
    "refresh_interval": 10,  # seconds for sensor data refresh
    "graph_refresh_interval": 30,  # seconds for graph refresh
    "debug_mode": False,
    "data_collector_api_url": "http://localhost:5001",  # API URL for data collector
    "connection_monitor_api_url": "http://localhost:5002",  # API URL for connection monitor
    "default_days": 1,  # Default number of days to display in graphs
    "p2_csv_path": "/var/lib/raspap_solo/data/RawData_P2/P2_fixed.csv",  # Default P2 CSV path
    "p3_csv_path": "/var/lib/raspap_solo/data/RawData_P3/P3_fixed.csv"   # Default P3 CSV path
}

# Initialize Flask app
app = Flask(__name__)

# HTML Template
TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>環境データモニター</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
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
            background-color: #e9ecef;
            font-weight: bold;
        }
        .sensor-value {
            font-size: 1.2em;
            font-weight: bold;
        }
        .timestamp {
            font-size: 0.8em;
            color: #6c757d;
        }
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 5px;
        }
        .status-online {
            background-color: #28a745;
        }
        .status-offline {
            background-color: #dc3545;
        }
        .graph-container {
            height: 400px;
            margin-bottom: 20px;
        }
        .loading-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(255, 255, 255, 0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        .graph-controls {
            margin-bottom: 20px;
        }
        .btn-group {
            margin-right: 10px;
        }
        #update-spinner {
            display: none;
        }
        #cancel-update {
            display: none;
        }
        .graph-mode-controls {
            margin-bottom: 20px;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="text-center mb-4">環境データモニター</h1>

        <!-- Sensor Data Cards -->
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        P2 センサーデータ
                        <span id="p2-status-indicator" class="status-indicator status-offline"></span>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-6">
                                <p>気温: <span id="p2-temperature" class="sensor-value">--</span> °C</p>
                                <p>相対湿度: <span id="p2-humidity" class="sensor-value">--</span> %</p>
                                <p>絶対湿度: <span id="p2-absolute-humidity" class="sensor-value">--</span> g/m³</p>
                            </div>
                            <div class="col-6">
                                <p>気圧: <span id="p2-pressure" class="sensor-value">--</span> hPa</p>
                                <p>ガス抵抗: <span id="p2-gas-resistance" class="sensor-value">--</span> Ω</p>
                                <p>CO2濃度: <span id="p2-co2" class="sensor-value">--</span> ppm</p>
                            </div>
                        </div>
                        <p class="timestamp">最終更新: <span id="p2-timestamp">--</span></p>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        P3 センサーデータ
                        <span id="p3-status-indicator" class="status-indicator status-offline"></span>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-6">
                                <p>気温: <span id="p3-temperature" class="sensor-value">--</span> °C</p>
                                <p>相対湿度: <span id="p3-humidity" class="sensor-value">--</span> %</p>
                                <p>絶対湿度: <span id="p3-absolute-humidity" class="sensor-value">--</span> g/m³</p>
                            </div>
                            <div class="col-6">
                                <p>気圧: <span id="p3-pressure" class="sensor-value">--</span> hPa</p>
                                <p>ガス抵抗: <span id="p3-gas-resistance" class="sensor-value">--</span> Ω</p>
                                <p>CO2濃度: <span id="p3-co2" class="sensor-value">--</span> ppm</p>
                            </div>
                        </div>
                        <p class="timestamp">最終更新: <span id="p3-timestamp">--</span></p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Connection Status Card -->
        <div class="card mb-4">
            <div class="card-header">接続状態</div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <h5>P2</h5>
                        <p>信号強度: <span id="p2-signal-strength">--</span> dBm</p>
                        <p>ノイズレベル: <span id="p2-noise-level">--</span> dBm</p>
                        <p>SNR: <span id="p2-snr">--</span> dB</p>
                        <p>Ping時間: <span id="p2-ping-time">--</span> ms</p>
                    </div>
                    <div class="col-md-6">
                        <h5>P3</h5>
                        <p>信号強度: <span id="p3-signal-strength">--</span> dBm</p>
                        <p>ノイズレベル: <span id="p3-noise-level">--</span> dBm</p>
                        <p>SNR: <span id="p3-snr">--</span> dB</p>
                        <p>Ping時間: <span id="p3-ping-time">--</span> ms</p>
                    </div>
                </div>
                <p class="timestamp">最終更新: <span id="connection-timestamp">--</span></p>
            </div>
        </div>

        <!-- Graph Controls -->
        <div class="card mb-4">
            <div class="card-header">グラフ設定</div>
            <div class="card-body">
                <div class="row graph-controls">
                    <div class="col-md-6">
                        <div class="form-check form-check-inline">
                            <input class="form-check-input" type="checkbox" id="show-p2" checked>
                            <label class="form-check-label" for="show-p2">P2データを表示</label>
                        </div>
                        <div class="form-check form-check-inline">
                            <input class="form-check-input" type="checkbox" id="show-p3" checked>
                            <label class="form-check-label" for="show-p3">P3データを表示</label>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="input-group">
                            <label class="input-group-text" for="days-select">期間</label>
                            <select class="form-select" id="days-select">
                                <option value="1" selected>1日</option>
                                <option value="3">3日</option>
                                <option value="7">1週間</option>
                                <option value="30">1ヶ月</option>
                                <option value="90">3ヶ月</option>
                                <option value="180">6ヶ月</option>
                                <option value="365">1年</option>
                                <option value="0">すべて</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- Graph Mode Controls (New) -->
                <div class="graph-mode-controls">
                    <div class="row">
                        <div class="col-md-6">
                            <h5>グラフ更新モード</h5>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="graph-mode" id="auto-mode" checked>
                                <label class="form-check-label" for="auto-mode">
                                    自動更新モード
                                </label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="graph-mode" id="manual-mode">
                                <label class="form-check-label" for="manual-mode">
                                    手動更新モード
                                </label>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="input-group mb-3">
                                <label class="input-group-text" for="refresh-interval">自動更新間隔</label>
                                <select class="form-select" id="refresh-interval">
                                    <option value="0">オフ</option>
                                    <option value="30" selected>30秒</option>
                                    <option value="60">1分</option>
                                    <option value="300">5分</option>
                                    <option value="600">10分</option>
                                </select>
                            </div>
                            <button id="refresh-graphs-btn" class="btn btn-primary">
                                グラフを更新
                                <span id="update-spinner" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                            </button>
                            <button id="cancel-update" class="btn btn-danger btn-sm">キャンセル</button>
                        </div>
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-12 text-end">
                        <button id="refresh-btn" class="btn btn-secondary me-2">センサーデータを更新</button>
                        <button id="export-btn" class="btn btn-success me-2">データをエクスポート</button>
                        <button id="save-graphs-btn" class="btn btn-info">グラフを保存</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Graphs -->
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">気温</div>
                    <div class="card-body position-relative">
                        <div id="temperature-graph" class="graph-container"></div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">相対湿度</div>
                    <div class="card-body position-relative">
                        <div id="humidity-graph" class="graph-container"></div>
                    </div>
                </div>
            </div>
        </div>
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">絶対湿度</div>
                    <div class="card-body position-relative">
                        <div id="absolute_humidity-graph" class="graph-container"></div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">CO2濃度</div>
                    <div class="card-body position-relative">
                        <div id="co2-graph" class="graph-container"></div>
                    </div>
                </div>
            </div>
        </div>
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">気圧</div>
                    <div class="card-body position-relative">
                        <div id="pressure-graph" class="graph-container"></div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">ガス抵抗</div>
                    <div class="card-body position-relative">
                        <div id="gas_resistance-graph" class="graph-container"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Export Modal -->
    <div class="modal fade" id="export-modal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">データをエクスポート</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-3">
                        <label for="export-device" class="form-label">デバイス</label>
                        <select class="form-select" id="export-device">
                            <option value="P2">P2</option>
                            <option value="P3">P3</option>
                            <option value="all">すべて</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label for="export-start-date" class="form-label">開始日</label>
                        <input type="date" class="form-control" id="export-start-date">
                    </div>
                    <div class="mb-3">
                        <label for="export-end-date" class="form-label">終了日</label>
                        <input type="date" class="form-control" id="export-end-date">
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">キャンセル</button>
                    <button type="button" class="btn btn-primary" id="export-confirm">エクスポート</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Save Graphs Modal -->
    <div class="modal fade" id="save-graphs-modal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">グラフを保存</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-3">
                        <label for="filename" class="form-label">ファイル名</label>
                        <input type="text" class="form-control" id="filename" value="environmental_data">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">保存するグラフ</label>
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="save-temperature" checked>
                            <label class="form-check-label" for="save-temperature">気温</label>
                        </div>
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="save-humidity" checked>
                            <label class="form-check-label" for="save-humidity">相対湿度</label>
                        </div>
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="save-absolute-humidity" checked>
                            <label class="form-check-label" for="save-absolute-humidity">絶対湿度</label>
                        </div>
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="save-co2" checked>
                            <label class="form-check-label" for="save-co2">CO2濃度</label>
                        </div>
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="save-pressure" checked>
                            <label class="form-check-label" for="save-pressure">気圧</label>
                        </div>
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="save-gas-resistance" checked>
                            <label class="form-check-label" for="save-gas-resistance">ガス抵抗</label>
                        </div>
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="save-dashboard" checked>
                            <label class="form-check-label" for="save-dashboard">ダッシュボード（すべてのグラフ）</label>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">キャンセル</button>
                    <button type="button" class="btn btn-primary" id="save-graphs-confirm">保存</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>

    <script>
        // Initialize modals
        const exportModal = new bootstrap.Modal(document.getElementById('export-modal'));
        const saveGraphsModal = new bootstrap.Modal(document.getElementById('save-graphs-modal'));

        // Set default dates for export
        const today = new Date();
        const oneWeekAgo = new Date();
        oneWeekAgo.setDate(today.getDate() - 7);

        document.getElementById('export-start-date').value = oneWeekAgo.toISOString().split('T')[0];
        document.getElementById('export-end-date').value = today.toISOString().split('T')[0];

        // Variables for auto-refresh
        let sensorDataInterval;
        let graphDataInterval;
        let updateCancelled = false;

        // Function to update sensor data
        function updateSensorData() {
            fetch('/api/latest-data')
                .then(response => response.json())
                .then(data => {
                    // Update P2 data
                    if (data.p2) {
                        document.getElementById('p2-status-indicator').className = 'status-indicator ' + 
                            (data.p2.online ? 'status-online' : 'status-offline');
                        document.getElementById('p2-temperature').textContent = data.p2.temperature !== null ? data.p2.temperature.toFixed(2) : '--';
                        document.getElementById('p2-humidity').textContent = data.p2.humidity !== null ? data.p2.humidity.toFixed(2) : '--';
                        document.getElementById('p2-absolute-humidity').textContent = data.p2.absolute_humidity !== null ? data.p2.absolute_humidity.toFixed(2) : '--';
                        document.getElementById('p2-pressure').textContent = data.p2.pressure !== null ? data.p2.pressure.toFixed(2) : '--';
                        document.getElementById('p2-gas-resistance').textContent = data.p2.gas_resistance !== null ? data.p2.gas_resistance : '--';
                        document.getElementById('p2-co2').textContent = data.p2.co2 !== null ? data.p2.co2 : '--';
                        document.getElementById('p2-timestamp').textContent = data.p2.timestamp || '--';
                    }

                    // Update P3 data
                    if (data.p3) {
                        document.getElementById('p3-status-indicator').className = 'status-indicator ' + 
                            (data.p3.online ? 'status-online' : 'status-offline');
                        document.getElementById('p3-temperature').textContent = data.p3.temperature !== null ? data.p3.temperature.toFixed(2) : '--';
                        document.getElementById('p3-humidity').textContent = data.p3.humidity !== null ? data.p3.humidity.toFixed(2) : '--';
                        document.getElementById('p3-absolute-humidity').textContent = data.p3.absolute_humidity !== null ? data.p3.absolute_humidity.toFixed(2) : '--';
                        document.getElementById('p3-pressure').textContent = data.p3.pressure !== null ? data.p3.pressure.toFixed(2) : '--';
                        document.getElementById('p3-gas-resistance').textContent = data.p3.gas_resistance !== null ? data.p3.gas_resistance : '--';
                        document.getElementById('p3-co2').textContent = data.p3.co2 !== null ? data.p3.co2 : '--';
                        document.getElementById('p3-timestamp').textContent = data.p3.timestamp || '--';
                    }
                })
                .catch(error => console.error('Error fetching sensor data:', error));

            // Update connection status
            fetch('/api/connection/status')
                .then(response => response.json())
                .then(data => {
                    // Update P2 connection data
                    if (data.p2) {
                        document.getElementById('p2-signal-strength').textContent = data.p2.signal_strength !== null ? data.p2.signal_strength : '--';
                        document.getElementById('p2-noise-level').textContent = data.p2.noise_level !== null ? data.p2.noise_level : '--';
                        document.getElementById('p2-snr').textContent = data.p2.snr !== null ? data.p2.snr : '--';
                        document.getElementById('p2-ping-time').textContent = data.p2.ping_time !== null ? data.p2.ping_time : '--';
                    }

                    // Update P3 connection data
                    if (data.p3) {
                        document.getElementById('p3-signal-strength').textContent = data.p3.signal_strength !== null ? data.p3.signal_strength : '--';
                        document.getElementById('p3-noise-level').textContent = data.p3.noise_level !== null ? data.p3.noise_level : '--';
                        document.getElementById('p3-snr').textContent = data.p3.snr !== null ? data.p3.snr : '--';
                        document.getElementById('p3-ping-time').textContent = data.p3.ping_time !== null ? data.p3.ping_time : '--';
                    }

                    document.getElementById('connection-timestamp').textContent = data.timestamp || '--';
                })
                .catch(error => console.error('Error fetching connection status:', error));
        }

        // Function to load graphs
        function loadGraphs() {
            // Show loading spinner
            document.getElementById('update-spinner').style.display = 'inline-block';
            document.getElementById('cancel-update').style.display = 'inline-block';
            updateCancelled = false;

            // Get parameters
            const days = document.getElementById('days-select').value;
            const showP2 = document.getElementById('show-p2').checked;
            const showP3 = document.getElementById('show-p3').checked;

            // Parameters to load
            const parameters = ['temperature', 'humidity', 'absolute_humidity', 'co2', 'pressure', 'gas_resistance'];
            let loadedCount = 0;

            // Load each graph
            parameters.forEach(param => {
                if (updateCancelled) return;

                fetch(`/data/${param}?days=${days}&show_p2=${showP2}&show_p3=${showP3}`)
                    .then(response => response.json())
                    .then(data => {
                        if (updateCancelled) return;

                        if (data.error) {
                            console.error(`Error loading ${param} graph:`, data.error);
                            document.getElementById(`${param}-graph`).innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                        } else {
                            Plotly.newPlot(`${param}-graph`, data.data, data.layout);
                        }

                        loadedCount++;
                        if (loadedCount === parameters.length) {
                            // Hide loading spinner when all graphs are loaded
                            document.getElementById('update-spinner').style.display = 'none';
                            document.getElementById('cancel-update').style.display = 'none';
                        }
                    })
                    .catch(error => {
                        console.error(`Error loading ${param} graph:`, error);
                        document.getElementById(`${param}-graph`).innerHTML = `<div class="alert alert-danger">グラフの読み込みに失敗しました</div>`;

                        loadedCount++;
                        if (loadedCount === parameters.length) {
                            // Hide loading spinner when all graphs are loaded
                            document.getElementById('update-spinner').style.display = 'none';
                            document.getElementById('cancel-update').style.display = 'none';
                        }
                    });
            });
        }

        // Function to set up auto-refresh
        function setupAutoRefresh() {
            // Clear existing intervals
            if (sensorDataInterval) clearInterval(sensorDataInterval);
            if (graphDataInterval) clearInterval(graphDataInterval);

            // Set up sensor data refresh
            const refreshInterval = 10 * 1000; // 10 seconds
            sensorDataInterval = setInterval(updateSensorData, refreshInterval);

            // Set up graph data refresh if auto mode is selected
            if (document.getElementById('auto-mode').checked) {
                const graphRefreshInterval = parseInt(document.getElementById('refresh-interval').value) * 1000;
                if (graphRefreshInterval > 0) {
                    graphDataInterval = setInterval(loadGraphs, graphRefreshInterval);
                }
            }
        }

        // Function to save graphs
        function saveGraphs() {
            // Get parameters
            const filename = document.getElementById('filename').value || 'environmental_data';
            const saveTemperature = document.getElementById('save-temperature').checked;
            const saveHumidity = document.getElementById('save-humidity').checked;
            const saveAbsoluteHumidity = document.getElementById('save-absolute-humidity').checked;
            const saveCO2 = document.getElementById('save-co2').checked;
            const savePressure = document.getElementById('save-pressure').checked;
            const saveGasResistance = document.getElementById('save-gas-resistance').checked;
            const saveDashboard = document.getElementById('save-dashboard').checked;

            // Create a form to submit
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/api/save-graphs';

            // Add parameters
            const addParam = (name, value) => {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = name;
                input.value = value;
                form.appendChild(input);
            };

            addParam('filename', filename);
            addParam('save_temperature', saveTemperature);
            addParam('save_humidity', saveHumidity);
            addParam('save_absolute_humidity', saveAbsoluteHumidity);
            addParam('save_co2', saveCO2);
            addParam('save_pressure', savePressure);
            addParam('save_gas_resistance', saveGasResistance);
            addParam('save_dashboard', saveDashboard);
            addParam('days', document.getElementById('days-select').value);
            addParam('show_p2', document.getElementById('show-p2').checked);
            addParam('show_p3', document.getElementById('show-p3').checked);

            // Submit the form
            document.body.appendChild(form);
            form.submit();
            document.body.removeChild(form);

            // Hide the modal
            saveGraphsModal.hide();
        }

        // Event listeners
        document.getElementById('refresh-btn').addEventListener('click', updateSensorData);
        document.getElementById('refresh-graphs-btn').addEventListener('click', loadGraphs);
        document.getElementById('cancel-update').addEventListener('click', function() {
            updateCancelled = true;
            document.getElementById('update-spinner').style.display = 'none';
            document.getElementById('cancel-update').style.display = 'none';
        });

        // Graph mode event listeners
        document.getElementById('auto-mode').addEventListener('change', function() {
            if (this.checked) {
                setupAutoRefresh();
            } else {
                if (graphDataInterval) clearInterval(graphDataInterval);
            }
        });

        document.getElementById('manual-mode').addEventListener('change', function() {
            if (this.checked) {
                if (graphDataInterval) clearInterval(graphDataInterval);
            }
        });

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

        // Save graphs functionality
        document.getElementById('save-graphs-btn').addEventListener('click', function() {
            saveGraphsModal.show();
        });

        document.getElementById('save-graphs-confirm').addEventListener('click', saveGraphs);

        // Initial load
        updateSensorData();
        loadGraphs();
        setupAutoRefresh();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template_string(TEMPLATE)

@app.route('/favicon.ico')
def favicon():
    """Return 204 No Content for favicon requests to avoid 404 errors."""
    return Response(status=204)

@app.route('/graph_info')
def graph_info():
    """Information page about the graph functionality."""
    info_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>グラフ機能について</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-4">
            <h1>グラフ機能について</h1>
            <div class="alert alert-info">
                グラフ表示機能がWebインターフェースに統合されました。
            </div>

            <h2>グラフ機能の使用方法</h2>
            <p>環境データのグラフは、メインページで直接表示されるようになりました。以下の機能が利用可能です：</p>

            <h3>グラフコントロール</h3>
            <ul>
                <li><strong>P2/P3データの表示切替</strong>: チェックボックスでP2とP3のデータ表示を個別に切り替えられます</li>
                <li><strong>期間選択</strong>: 1日、3日、1週間、1ヶ月、3ヶ月、6ヶ月、1年、またはすべてのデータから選択できます</li>
                <li><strong>自動更新</strong>: グラフの自動更新間隔を設定できます（オフ、30秒、1分、5分、10分）</li>
                <li><strong>手動更新</strong>: 「グラフを更新」ボタンで任意のタイミングで更新できます</li>
                <li><strong>グラフ保存</strong>: 「グラフ保存」ボタンで現在表示中のグラフをHTMLファイルとして保存できます</li>
            </ul>

            <h3>表示されるグラフ</h3>
            <ul>
                <li><strong>気温</strong>: 気温の経時変化（°C）</li>
                <li><strong>相対湿度</strong>: 相対湿度の経時変化（%）</li>
                <li><strong>絶対湿度</strong>: 絶対湿度の経時変化（g/m³）</li>
                <li><strong>CO2濃度</strong>: CO2濃度の経時変化（ppm）</li>
                <li><strong>気圧</strong>: 気圧の経時変化（hPa）</li>
                <li><strong>ガス抵抗</strong>: ガス抵抗の経時変化（Ω）</li>
            </ul>

            <h3>グラフ更新モード</h3>
            <ul>
                <li><strong>自動更新モード</strong>: 設定した間隔でグラフが自動的に更新されます</li>
                <li><strong>手動更新モード</strong>: 「グラフを更新」ボタンを押したときのみグラフが更新されます</li>
            </ul>

            <h3>データエクスポート</h3>
            <p>「データをエクスポート」ボタンを使用して、P2またはP3のデータをCSVファイルとしてエクスポートできます。
            期間を指定してエクスポートすることも可能です。</p>

            <div class="mt-4">
                <a href="/" class="btn btn-primary">メインページに戻る</a>
            </div>
        </div>
    </body>
    </html>
    """
    return info_html

@app.route('/api/connection/status')
def get_connection_status():
    """API endpoint to get connection status for P2 and P3."""
    try:
        # Try to get connection status from connection monitor API
        response = requests.get(f"{DEFAULT_CONFIG['connection_monitor_api_url']}/status", timeout=5)
        if response.status_code == 200:
            return jsonify(response.json())
    except Exception as e:
        logger.error(f"Error getting connection status from API: {e}")

    # If API call fails, return dummy data
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return jsonify({
        "timestamp": current_time,
        "p2": {
            "timestamp": current_time,
            "online": False,
            "signal_strength": None,
            "noise_level": None,
            "snr": None,
            "ping_time": None
        },
        "p3": {
            "timestamp": current_time,
            "online": False,
            "signal_strength": None,
            "noise_level": None,
            "snr": None,
            "ping_time": None
        }
    })

@app.route('/api/latest-data')
def get_latest_data():
    """API endpoint to get latest sensor data for P2 and P3."""
    try:
        # Try to get latest data from data collector API
        response = requests.get(f"{DEFAULT_CONFIG['data_collector_api_url']}/latest", timeout=5)
        if response.status_code == 200:
            return jsonify(response.json())
    except Exception as e:
        logger.error(f"Error getting latest data from API: {e}")

    # If API call fails, return dummy data
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return jsonify({
        "timestamp": current_time,
        "p2": {
            "timestamp": current_time,
            "online": False,
            "temperature": None,
            "humidity": None,
            "pressure": None,
            "gas_resistance": None,
            "co2": None,
            "absolute_humidity": None
        },
        "p3": {
            "timestamp": current_time,
            "online": False,
            "temperature": None,
            "humidity": None,
            "pressure": None,
            "gas_resistance": None,
            "co2": None,
            "absolute_humidity": None
        }
    })

@app.route('/api/export/<device_id>')
def export_data(device_id):
    """API endpoint to export data as CSV."""
    if device_id not in ["P2", "P3", "all"]:
        return jsonify({"error": "無効なデバイスID"}), 400

    start_date = request.args.get('start_date', default=(datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d"))
    end_date = request.args.get('end_date', default=datetime.datetime.now().strftime("%Y-%m-%d"))

    try:
        # Parse dates
        start_date_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_date_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")

        # Define file paths
        p2_path = os.path.join(DEFAULT_CONFIG["data_dir"], DEFAULT_CONFIG["rawdata_p2_dir"], "P2_fixed.csv")
        p3_path = os.path.join(DEFAULT_CONFIG["data_dir"], DEFAULT_CONFIG["rawdata_p3_dir"], "P3_fixed.csv")

        # Create temporary file for download
        temp_file = os.path.join(DEFAULT_CONFIG["data_dir"], f"export_{device_id}_{int(time.time())}.csv")

        # Export based on device ID
        if device_id == "P2":
            if not os.path.exists(p2_path):
                return jsonify({"error": "P2のデータファイルが見つかりません"}), 404
            os.system(f"cp {p2_path} {temp_file}")
        elif device_id == "P3":
            if not os.path.exists(p3_path):
                return jsonify({"error": "P3のデータファイルが見つかりません"}), 404
            os.system(f"cp {p3_path} {temp_file}")
        else:  # all
            if not os.path.exists(p2_path) and not os.path.exists(p3_path):
                return jsonify({"error": "データファイルが見つかりません"}), 404

            # Combine P2 and P3 data
            with open(temp_file, 'w') as outfile:
                # Write header
                outfile.write("device_id,timestamp,temperature,humidity,pressure,gas_resistance,co2,absolute_humidity\n")

                # Add P2 data if available
                if os.path.exists(p2_path):
                    with open(p2_path, 'r') as infile:
                        header = infile.readline()  # Skip header
                        for line in infile:
                            outfile.write(f"P2,{line}")

                # Add P3 data if available
                if os.path.exists(p3_path):
                    with open(p3_path, 'r') as infile:
                        header = infile.readline()  # Skip header
                        for line in infile:
                            outfile.write(f"P3,{line}")

        return send_file(temp_file, 
                        mimetype='text/csv',
                        as_attachment=True,
                        download_name=f"{device_id}_data_{start_date}_to_{end_date}.csv")

    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        return jsonify({"error": f"データエクスポート中にエラーが発生しました: {e}"}), 500

def read_csv_data(csv_path, days=1):
    """Read data from CSV file and process it."""
    # Check if file exists
    if not os.path.exists(csv_path):
        logger.warning(f"CSV file not found: {csv_path}")
        return None

    try:
        # Read CSV file
        logger.info(f"Reading CSV file: {csv_path}")
        df = pd.read_csv(csv_path)

        # Log initial data types and sample data
        logger.info(f"CSV columns and types: {df.dtypes}")
        if not df.empty:
            logger.info(f"Sample data (first row): {df.iloc[0].to_dict()}")

        # Convert timestamp to datetime - simplified approach that handles both numeric and string formats
        if 'timestamp' in df.columns:
            logger.info(f"Original timestamp dtype: {df['timestamp'].dtype}")

            # Check if timestamp is numeric (int64 or float64)
            if df['timestamp'].dtype == 'int64' or df['timestamp'].dtype == 'float64':
                logger.info("Detected numeric timestamp format (seconds since epoch)")
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
            else:
                # Convert to string first to handle any format safely
                logger.info("Detected string timestamp format")
                df['timestamp'] = pd.to_datetime(df['timestamp'].astype(str), errors='coerce')

            logger.info(f"Converted timestamp dtype: {df['timestamp'].dtype}")
            logger.info(f"Timestamp range: {df['timestamp'].min()} to {df['timestamp'].max()}")

        # Drop rows with invalid timestamps
        original_count = len(df)
        df = df.dropna(subset=['timestamp'])
        if len(df) < original_count:
            logger.warning(f"Dropped {original_count - len(df)} rows with invalid timestamps")

        # Convert all numeric columns to proper numeric types
        numeric_columns = ["temperature", "humidity", "pressure", "gas_resistance", "co2", "absolute_humidity"]
        for col in numeric_columns:
            if col in df.columns:
                # Log original data type
                logger.info(f"Column '{col}' original dtype: {df[col].dtype}")

                # Store original values for comparison
                original_values = df[col].copy()

                # Convert to numeric - force conversion to handle any format
                df[col] = pd.to_numeric(df[col], errors='coerce')

                # Check if conversion changed any values or created NaNs
                changed_count = (df[col] != original_values).sum()
                nan_count = df[col].isna().sum()

                logger.info(f"Column '{col}' converted to numeric. Changed values: {changed_count}, NaN values: {nan_count}")
                if not df[col].empty and not df[col].isna().all():
                    logger.info(f"Column '{col}' range: {df[col].min()} to {df[col].max()}")

        # Filter data for the specified time range
        if days > 0:
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
            before_count = len(df)
            df = df[df['timestamp'] >= cutoff_date]
            logger.info(f"Filtered data for last {days} days: {before_count} -> {len(df)} rows")

        # Sort by timestamp
        df = df.sort_values(by='timestamp')

        return df

    except Exception as e:
        logger.error(f"Error reading CSV file {csv_path}: {e}")
        return None

def generate_graph(parameter, df_p2, df_p3, show_p2=True, show_p3=True):
    """Generate a graph for the specified parameter."""
    # Define parameter labels
    label_map = {
        "temperature": "気温 (°C)",
        "humidity": "相対湿度 (%)",
        "absolute_humidity": "絶対湿度 (g/m³)",
        "co2": "CO2濃度 (ppm)",
        "pressure": "気圧 (hPa)",
        "gas_resistance": "ガス抵抗 (Ω)"
    }
    label = label_map.get(parameter, parameter.capitalize())

    # Create figure
    fig = go.Figure()

    # Add P2 data if available
    if show_p2 and df_p2 is not None and not df_p2.empty and parameter in df_p2.columns:
        # Check for valid data (at least 2 unique non-NaN values)
        p2_values = df_p2[parameter].dropna()
        if len(p2_values) > 0 and len(p2_values.unique()) >= 2:
            # Log detailed information about the data being plotted
            min_val = p2_values.min()
            max_val = p2_values.max()
            mean_val = p2_values.mean()
            logger.info(f"Adding P2 data for {parameter}: {len(p2_values)} points, range: {min_val} - {max_val}, mean: {mean_val}")

            # Verify timestamp data is properly formatted
            if not pd.api.types.is_datetime64_any_dtype(df_p2['timestamp']):
                logger.warning(f"P2 timestamp column is not datetime type: {df_p2['timestamp'].dtype}")
                # Try to convert again as a last resort
                df_p2['timestamp'] = pd.to_datetime(df_p2['timestamp'], errors='coerce')
                df_p2 = df_p2.dropna(subset=['timestamp'])
                logger.info(f"Converted P2 timestamps. Remaining rows: {len(df_p2)}")

            # Add trace to the figure
            fig.add_trace(go.Scatter(
                x=df_p2['timestamp'],
                y=df_p2[parameter],
                mode='lines',
                name=f'P2 {label}',
                line=dict(color='blue')
            ))
        else:
            logger.warning(f"P2 data for {parameter} has insufficient unique values: {len(p2_values)} points, {len(p2_values.unique())} unique values")

    # Add P3 data if available
    if show_p3 and df_p3 is not None and not df_p3.empty and parameter in df_p3.columns:
        # Check for valid data (at least 2 unique non-NaN values)
        p3_values = df_p3[parameter].dropna()
        if len(p3_values) > 0 and len(p3_values.unique()) >= 2:
            # Log detailed information about the data being plotted
            min_val = p3_values.min()
            max_val = p3_values.max()
            mean_val = p3_values.mean()
            logger.info(f"Adding P3 data for {parameter}: {len(p3_values)} points, range: {min_val} - {max_val}, mean: {mean_val}")

            # Verify timestamp data is properly formatted
            if not pd.api.types.is_datetime64_any_dtype(df_p3['timestamp']):
                logger.warning(f"P3 timestamp column is not datetime type: {df_p3['timestamp'].dtype}")
                # Try to convert again as a last resort
                df_p3['timestamp'] = pd.to_datetime(df_p3['timestamp'], errors='coerce')
                df_p3 = df_p3.dropna(subset=['timestamp'])
                logger.info(f"Converted P3 timestamps. Remaining rows: {len(df_p3)}")

            # Add trace to the figure
            fig.add_trace(go.Scatter(
                x=df_p3['timestamp'],
                y=df_p3[parameter],
                mode='lines',
                name=f'P3 {label}',
                line=dict(color='red')
            ))
        else:
            logger.warning(f"P3 data for {parameter} has insufficient unique values: {len(p3_values)} points, {len(p3_values.unique())} unique values")

    # Check if we have any traces
    if not fig.data:
        logger.warning(f"No valid data to plot for {parameter}")
        return None

    # Calculate appropriate Y-axis range with padding
    all_y_values = []
    if show_p2 and df_p2 is not None and not df_p2.empty and parameter in df_p2.columns:
        all_y_values.extend(df_p2[parameter].dropna().tolist())
    if show_p3 and df_p3 is not None and not df_p3.empty and parameter in df_p3.columns:
        all_y_values.extend(df_p3[parameter].dropna().tolist())

    if all_y_values:
        min_y = min(all_y_values)
        max_y = max(all_y_values)
        padding = (max_y - min_y) * 0.05  # 5% padding

        # Determine appropriate minimum value based on parameter
        if parameter in ["co2", "gas_resistance", "absolute_humidity"]:
            # These values are never negative
            min_range = max(0, min_y - padding)
        else:
            # Use actual minimum with padding
            min_range = min_y - padding

        # Set Y-axis range
        y_range = [min_range, max_y + padding]
        logger.info(f"Setting Y-axis range for {parameter}: {y_range}")
    else:
        y_range = None

    # Update layout with improved settings
    fig.update_layout(
        title=f"{label}の経時変化",
        xaxis_title="時間",
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
        ),
        # Ensure X-axis is properly formatted as a date
        xaxis=dict(
            type='date',
            tickformat='%Y-%m-%d %H:%M',
            tickangle=-45
        )
    )

    # Set Y-axis range if calculated
    if y_range:
        fig.update_yaxes(
            range=y_range,
            autorange=False,
            # Use "tozero" for parameters that should never be negative
            rangemode="tozero" if parameter in ["co2", "gas_resistance", "absolute_humidity"] else "normal"
        )

    return fig

def create_dashboard(df_p2, df_p3, show_p2=True, show_p3=True):
    """Create a dashboard with all parameters."""
    # Define parameters to plot
    parameters = ["temperature", "humidity", "absolute_humidity", "co2", "pressure", "gas_resistance"]

    # Create a subplot figure with 3x2 grid
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=[
            "気温 (°C)", "相対湿度 (%)",
            "絶対湿度 (g/m³)", "CO2濃度 (ppm)",
            "気圧 (hPa)", "ガス抵抗 (Ω)"
        ],
        vertical_spacing=0.1,
        horizontal_spacing=0.05
    )

    # Map parameters to subplot positions
    param_positions = {
        "temperature": (1, 1),
        "humidity": (1, 2),
        "absolute_humidity": (2, 1),
        "co2": (2, 2),
        "pressure": (3, 1),
        "gas_resistance": (3, 2)
    }

    # Add traces for each parameter
    for param, (row, col) in param_positions.items():
        # Add P2 data if available
        if show_p2 and df_p2 is not None and not df_p2.empty and param in df_p2.columns:
            p2_values = df_p2[param].dropna()
            if len(p2_values) > 0 and len(p2_values.unique()) >= 2:
                fig.add_trace(
                    go.Scatter(
                        x=df_p2['timestamp'],
                        y=df_p2[param],
                        mode='lines',
                        name=f'P2 {param}',
                        line=dict(color='blue')
                    ),
                    row=row, col=col
                )

        # Add P3 data if available
        if show_p3 and df_p3 is not None and not df_p3.empty and param in df_p3.columns:
            p3_values = df_p3[param].dropna()
            if len(p3_values) > 0 and len(p3_values.unique()) >= 2:
                fig.add_trace(
                    go.Scatter(
                        x=df_p3['timestamp'],
                        y=df_p3[param],
                        mode='lines',
                        name=f'P3 {param}',
                        line=dict(color='red')
                    ),
                    row=row, col=col
                )

        # Calculate appropriate Y-axis range
        all_y_values = []
        if show_p2 and df_p2 is not None and not df_p2.empty and param in df_p2.columns:
            all_y_values.extend(df_p2[param].dropna().tolist())
        if show_p3 and df_p3 is not None and not df_p3.empty and param in df_p3.columns:
            all_y_values.extend(df_p3[param].dropna().tolist())

        if all_y_values:
            min_y = min(all_y_values)
            max_y = max(all_y_values)
            padding = (max_y - min_y) * 0.05  # 5% padding

            # Determine appropriate minimum value based on parameter
            if param in ["co2", "gas_resistance", "absolute_humidity"]:
                # These values are never negative
                min_range = max(0, min_y - padding)
            else:
                # Use actual minimum with padding
                min_range = min_y - padding

            # Set Y-axis range
            y_range = [min_range, max_y + padding]

            # Update Y-axis for this subplot
            fig.update_yaxes(
                range=y_range,
                autorange=False,
                rangemode="tozero" if param in ["co2", "gas_resistance", "absolute_humidity"] else "normal",
                row=row, col=col
            )

    # Update layout
    fig.update_layout(
        title="環境データダッシュボード",
        height=900,
        width=1200,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    # Update all X-axes to be date type
    for i in range(1, 4):
        for j in range(1, 3):
            fig.update_xaxes(
                type='date',
                tickformat='%Y-%m-%d %H:%M',
                tickangle=-45,
                row=i, col=j
            )

    return fig

@app.route('/data/<parameter>')
def get_graph_data(parameter):
    """API endpoint to get graph data for a specific parameter."""
    days = request.args.get('days', default=1, type=int)
    show_p2 = request.args.get('show_p2', default='true').lower() == 'true'
    show_p3 = request.args.get('show_p3', default='true').lower() == 'true'

    # Read data
    p2_path = DEFAULT_CONFIG["p2_csv_path"]
    p3_path = DEFAULT_CONFIG["p3_csv_path"]

    df_p2 = read_csv_data(p2_path, days) if show_p2 else None
    df_p3 = read_csv_data(p3_path, days) if show_p3 else None

    # Check if we have any data
    if (df_p2 is None or df_p2.empty) and (df_p3 is None or df_p3.empty):
        return jsonify({"error": "データが見つかりませんでした"})

    try:
        # Generate graph
        fig = generate_graph(parameter, df_p2, df_p3, show_p2, show_p3)

        if fig is None:
            return jsonify({"error": f"{parameter}の有効なデータがありません"})

        # Convert to JSON
        graph_json = jsonify_numpy(fig.to_dict())
        return jsonify(graph_json)
    except Exception as e:
        logger.error(f"Error generating graph for {parameter}: {e}")
        return jsonify({"error": f"グラフ生成エラー: {e}"})

@app.route('/api/save-graphs', methods=['POST'])
def save_graphs():
    """API endpoint to save graphs as HTML files."""
    try:
        # Get parameters from form
        filename = request.form.get('filename', 'environmental_data')
        save_temperature = request.form.get('save_temperature') == 'true'
        save_humidity = request.form.get('save_humidity') == 'true'
        save_absolute_humidity = request.form.get('save_absolute_humidity') == 'true'
        save_co2 = request.form.get('save_co2') == 'true'
        save_pressure = request.form.get('save_pressure') == 'true'
        save_gas_resistance = request.form.get('save_gas_resistance') == 'true'
        save_dashboard = request.form.get('save_dashboard') == 'true'
        days = int(request.form.get('days', 1))
        show_p2 = request.form.get('show_p2') == 'true'
        show_p3 = request.form.get('show_p3') == 'true'

        # Read data
        p2_path = DEFAULT_CONFIG["p2_csv_path"]
        p3_path = DEFAULT_CONFIG["p3_csv_path"]

        df_p2 = read_csv_data(p2_path, days) if show_p2 else None
        df_p3 = read_csv_data(p3_path, days) if show_p3 else None

        # Create a zip file to store all graphs
        import zipfile
        import io

        # Create a BytesIO object to store the zip file
        zip_buffer = io.BytesIO()

        # Create a ZipFile object
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Save individual graphs
            parameters = []
            if save_temperature:
                parameters.append('temperature')
            if save_humidity:
                parameters.append('humidity')
            if save_absolute_humidity:
                parameters.append('absolute_humidity')
            if save_co2:
                parameters.append('co2')
            if save_pressure:
                parameters.append('pressure')
            if save_gas_resistance:
                parameters.append('gas_resistance')

            # Generate and save individual graphs
            for param in parameters:
                fig = generate_graph(param, df_p2, df_p3, show_p2, show_p3)
                if fig:  # Skip if there was an error
                    html = fig.to_html(full_html=True, include_plotlyjs='cdn')
                    zip_file.writestr(f"{filename}_{param}.html", html)

            # Generate and save dashboard
            if save_dashboard:
                dashboard = create_dashboard(df_p2, df_p3, show_p2, show_p3)
                html = dashboard.to_html(full_html=True, include_plotlyjs='cdn')
                zip_file.writestr(f"{filename}_dashboard.html", html)

        # Reset buffer position
        zip_buffer.seek(0)

        # Return the zip file
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"{filename}_graphs.zip"
        )

    except Exception as e:
        logger.error(f"Error saving graphs: {e}")
        return jsonify({"error": f"グラフの保存中にエラーが発生しました: {e}"}), 500

def main():
    """Main function to run the web interface."""
    parser = argparse.ArgumentParser(description='環境データウェブインターフェース')
    parser.add_argument('--port', type=int, help='リッスンするポート')
    parser.add_argument('--data-dir', type=str, help='データを読み込むディレクトリ')
    parser.add_argument('--p2-path', type=str, help='P2のCSVデータファイルのパス')
    parser.add_argument('--p3-path', type=str, help='P3のCSVデータファイルのパス')
    parser.add_argument('--debug', action='store_true', help='デバッグモードを有効にする')
    args = parser.parse_args()

    # Update configuration
    if args.port:
        DEFAULT_CONFIG["web_port"] = args.port

    if args.data_dir:
        DEFAULT_CONFIG["data_dir"] = args.data_dir
        DEFAULT_CONFIG["p2_csv_path"] = os.path.join(args.data_dir, DEFAULT_CONFIG["rawdata_p2_dir"], "P2_fixed.csv")
        DEFAULT_CONFIG["p3_csv_path"] = os.path.join(args.data_dir, DEFAULT_CONFIG["rawdata_p3_dir"], "P3_fixed.csv")

    if args.p2_path:
        DEFAULT_CONFIG["p2_csv_path"] = args.p2_path

    if args.p3_path:
        DEFAULT_CONFIG["p3_csv_path"] = args.p3_path

    if args.debug:
        DEFAULT_CONFIG["debug_mode"] = True

    logger.info("グラフ描画機能を統合しました")
    logger.info(f"P2データパス: {DEFAULT_CONFIG['p2_csv_path']}")
    logger.info(f"P3データパス: {DEFAULT_CONFIG['p3_csv_path']}")

    # 明示的にファイルの存在確認
    if not os.path.exists(DEFAULT_CONFIG['p2_csv_path']):
        logger.error(f"P2ファイルが見つかりません: {DEFAULT_CONFIG['p2_csv_path']}")
    if not os.path.exists(DEFAULT_CONFIG['p3_csv_path']):
        logger.error(f"P3ファイルが見つかりません: {DEFAULT_CONFIG['p3_csv_path']}")

    # Start the web server
    app.run(host='0.0.0.0', port=DEFAULT_CONFIG["web_port"], debug=DEFAULT_CONFIG["debug_mode"])

if __name__ == "__main__":
    main()

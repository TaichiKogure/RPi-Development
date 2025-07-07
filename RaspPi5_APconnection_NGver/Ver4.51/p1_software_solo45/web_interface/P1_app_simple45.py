#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi 5 Environmental Data Web Interface - Simple Version
Version: 4.5.0-solo

This module provides a simplified web interface for visualizing environmental data
collected from P2 and P3 sensor nodes with BME680 and MH-Z19C sensors. It displays real-time data,
historical trends, and allows for data export.

Features:
- Real-time display of current sensor readings from both P2 and P3 (including CO2)
- Time-series graphs of historical data with proper Y-axis ranges
- Toggle options to show/hide P2 and P3 data on the same graph
- Display of absolute humidity calculated from temperature and humidity
- Data export in CSV format
- Graph saving functionality
- Responsive design for mobile and desktop viewing
- Auto-refresh functionality (30 seconds)
- Connection status updates (10 seconds)
- Extended time period selection (1 day, 3 days, 1 week, 3 months, 6 months, 1 year, all)

Requirements:
- Python 3.7+
- Flask for the web server
- Pandas for data manipulation
- Plotly for interactive graphs

Usage:
    python3 P1_app_simple45.py [--port PORT] [--data-dir DIR]
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
        logging.FileHandler("/var/log/web_interface_simple45.log"),
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
    "refresh_interval": 30,  # seconds (changed from 10 to 30)
    "connection_refresh_interval": 10,  # seconds (new)
    "graph_points": 100,  # number of data points to show in graphs
    "debug_mode": False,
    "data_collector_api_url": "http://localhost:5001",  # API URL for data collector
    "connection_monitor_api_url": "http://localhost:5002"  # API URL for connection monitor
}

# Initialize Flask app
app = Flask(__name__)

# HTML Template with Plotly.js integration
TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>環境データダッシュボード</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
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
        .sensor-value {
            font-size: 1.2em;
            font-weight: bold;
        }
        .sensor-card {
            text-align: center;
            padding: 10px;
        }
        .sensor-label {
            font-size: 0.9em;
            color: #666;
        }
        .update-spinner {
            display: none;
            margin-left: 10px;
        }
        .cancel-update {
            display: none;
            margin-left: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="text-center mb-4">環境データダッシュボード</h1>

        <!-- Real-time sensor values -->
        <div class="card mb-4">
            <div class="card-header">リアルタイムセンサー値</div>
            <div class="card-body">
                <div class="row" id="realtime-values">
                    <div class="col-12 text-center">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">読み込み中...</span>
                        </div>
                        <p>センサーデータを読み込み中...</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="card control-panel">
            <div class="card-header">コントロール</div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-4">
                        <div class="form-check form-switch">
                            <input class="form-check-input" type="checkbox" id="show-p2" checked>
                            <label class="form-check-label p2-color" for="show-p2">P2データを表示</label>
                        </div>
                        <div class="form-check form-switch">
                            <input class="form-check-input" type="checkbox" id="show-p3" checked>
                            <label class="form-check-label p3-color" for="show-p3">P3データを表示</label>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="form-group">
                            <label for="days-select">期間:</label>
                            <select class="form-control" id="days-select">
                                <option value="1">1日</option>
                                <option value="3">3日</option>
                                <option value="7">1週間</option>
                                <option value="90">3ヶ月</option>
                                <option value="180">6ヶ月</option>
                                <option value="365">1年</option>
                                <option value="0">すべて</option>
                            </select>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="form-group">
                            <label for="refresh-interval">自動更新:</label>
                            <select class="form-control" id="refresh-interval">
                                <option value="0">オフ</option>
                                <option value="30" selected>30秒</option>
                                <option value="60">1分</option>
                                <option value="300">5分</option>
                            </select>
                        </div>
                    </div>
                </div>
                <div class="row mt-3">
                    <div class="col-md-6">
                        <button id="refresh-btn" class="btn btn-primary">今すぐ更新</button>
                        <div class="spinner-border text-primary update-spinner" id="update-spinner" role="status">
                            <span class="visually-hidden">更新中...</span>
                        </div>
                        <button id="cancel-update" class="btn btn-danger btn-sm cancel-update">キャンセル</button>
                        <span id="last-update" class="ms-3">最終更新: なし</span>
                    </div>
                    <div class="col-md-6 text-end">
                        <button id="export-btn" class="btn btn-success me-2">データエクスポート</button>
                        <button id="save-graphs-btn" class="btn btn-info">グラフ保存</button>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">気温 (°C)</div>
                    <div class="card-body">
                        <div id="graph_temperature" class="graph-container">
                            <div class="loading">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">読み込み中...</span>
                                </div>
                                <p>グラフを読み込み中...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">相対湿度 (%)</div>
                    <div class="card-body">
                        <div id="graph_humidity" class="graph-container">
                            <div class="loading">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">読み込み中...</span>
                                </div>
                                <p>グラフを読み込み中...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">絶対湿度 (g/m³)</div>
                    <div class="card-body">
                        <div id="graph_absolute_humidity" class="graph-container">
                            <div class="loading">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">読み込み中...</span>
                                </div>
                                <p>グラフを読み込み中...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">CO2濃度 (ppm)</div>
                    <div class="card-body">
                        <div id="graph_co2" class="graph-container">
                            <div class="loading">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">読み込み中...</span>
                                </div>
                                <p>グラフを読み込み中...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">気圧 (hPa)</div>
                    <div class="card-body">
                        <div id="graph_pressure" class="graph-container">
                            <div class="loading">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">読み込み中...</span>
                                </div>
                                <p>グラフを読み込み中...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">ガス抵抗 (Ω)</div>
                    <div class="card-body">
                        <div id="graph_gas_resistance" class="graph-container">
                            <div class="loading">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">読み込み中...</span>
                                </div>
                                <p>グラフを読み込み中...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="card mt-4">
            <div class="card-header">接続状態</div>
            <div class="card-body">
                <div id="connection-status">
                    <div class="loading">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">読み込み中...</span>
                        </div>
                        <p>接続データを読み込み中...</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Export Modal -->
        <div class="modal fade" id="export-modal" tabindex="-1" aria-labelledby="export-modal-label" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="export-modal-label">データエクスポート</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="閉じる"></button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label for="export-device">デバイス:</label>
                            <select class="form-control" id="export-device">
                                <option value="P2">P2</option>
                                <option value="P3">P3</option>
                                <option value="all">すべてのデバイス</option>
                            </select>
                        </div>
                        <div class="form-group mt-3">
                            <label for="export-start-date">開始日:</label>
                            <input type="date" class="form-control" id="export-start-date">
                        </div>
                        <div class="form-group mt-3">
                            <label for="export-end-date">終了日:</label>
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
        <div class="modal fade" id="save-graphs-modal" tabindex="-1" aria-labelledby="save-graphs-modal-label" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="save-graphs-modal-label">グラフ保存</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="閉じる"></button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label for="save-graphs-filename">ファイル名:</label>
                            <input type="text" class="form-control" id="save-graphs-filename" value="environmental_data">
                        </div>
                        <div class="form-group mt-3">
                            <label>保存するグラフ:</label>
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
                                <label class="form-check-label" for="save-dashboard">ダッシュボード (すべてのグラフ)</label>
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
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Initialize variables
        let refreshTimer = null;
        let connectionTimer = null;
        let updateInProgress = false;
        let updateCancelled = false;
        const exportModal = new bootstrap.Modal(document.getElementById('export-modal'));
        const saveGraphsModal = new bootstrap.Modal(document.getElementById('save-graphs-modal'));

        // Set default dates for export
        const today = new Date();
        const oneWeekAgo = new Date();
        oneWeekAgo.setDate(today.getDate() - 7);

        document.getElementById('export-end-date').value = today.toISOString().split('T')[0];
        document.getElementById('export-start-date').value = oneWeekAgo.toISOString().split('T')[0];

        // Function to load real-time sensor values
        function loadRealtimeValues() {
            fetch('/api/data/latest')
                .then(response => response.json())
                .then(data => {
                    const valuesDiv = document.getElementById('realtime-values');
                    let html = '<div class="row">';

                    // P2 sensor values
                    if (data.P2) {
                        html += `
                            <div class="col-md-6">
                                <h5 class="p2-color">P2センサーノード</h5>
                                <div class="row">
                                    <div class="col-4 sensor-card">
                                        <div class="sensor-value">${parseFloat(data.P2.temperature).toFixed(1)}°C</div>
                                        <div class="sensor-label">気温</div>
                                    </div>
                                    <div class="col-4 sensor-card">
                                        <div class="sensor-value">${parseFloat(data.P2.humidity).toFixed(1)}%</div>
                                        <div class="sensor-label">相対湿度</div>
                                    </div>
                                    <div class="col-4 sensor-card">
                                        <div class="sensor-value">${parseFloat(data.P2.absolute_humidity).toFixed(1)} g/m³</div>
                                        <div class="sensor-label">絶対湿度</div>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-4 sensor-card">
                                        <div class="sensor-value">${data.P2.co2 ? parseFloat(data.P2.co2).toFixed(0) : 'N/A'} ppm</div>
                                        <div class="sensor-label">CO2濃度</div>
                                    </div>
                                    <div class="col-4 sensor-card">
                                        <div class="sensor-value">${parseFloat(data.P2.pressure).toFixed(1)} hPa</div>
                                        <div class="sensor-label">気圧</div>
                                    </div>
                                    <div class="col-4 sensor-card">
                                        <div class="sensor-value">${parseFloat(data.P2.gas_resistance).toFixed(0)} Ω</div>
                                        <div class="sensor-label">ガス抵抗</div>
                                    </div>
                                </div>
                                <div class="text-muted text-center mt-2">最終更新: ${data.P2.timestamp}</div>
                            </div>
                        `;
                    } else {
                        html += `
                            <div class="col-md-6">
                                <h5 class="p2-color">P2センサーノード</h5>
                                <div class="alert alert-warning">データがありません</div>
                            </div>
                        `;
                    }

                    // P3 sensor values
                    if (data.P3) {
                        html += `
                            <div class="col-md-6">
                                <h5 class="p3-color">P3センサーノード</h5>
                                <div class="row">
                                    <div class="col-4 sensor-card">
                                        <div class="sensor-value">${parseFloat(data.P3.temperature).toFixed(1)}°C</div>
                                        <div class="sensor-label">気温</div>
                                    </div>
                                    <div class="col-4 sensor-card">
                                        <div class="sensor-value">${parseFloat(data.P3.humidity).toFixed(1)}%</div>
                                        <div class="sensor-label">相対湿度</div>
                                    </div>
                                    <div class="col-4 sensor-card">
                                        <div class="sensor-value">${parseFloat(data.P3.absolute_humidity).toFixed(1)} g/m³</div>
                                        <div class="sensor-label">絶対湿度</div>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-4 sensor-card">
                                        <div class="sensor-value">${data.P3.co2 ? parseFloat(data.P3.co2).toFixed(0) : 'N/A'} ppm</div>
                                        <div class="sensor-label">CO2濃度</div>
                                    </div>
                                    <div class="col-4 sensor-card">
                                        <div class="sensor-value">${parseFloat(data.P3.pressure).toFixed(1)} hPa</div>
                                        <div class="sensor-label">気圧</div>
                                    </div>
                                    <div class="col-4 sensor-card">
                                        <div class="sensor-value">${parseFloat(data.P3.gas_resistance).toFixed(0)} Ω</div>
                                        <div class="sensor-label">ガス抵抗</div>
                                    </div>
                                </div>
                                <div class="text-muted text-center mt-2">最終更新: ${data.P3.timestamp}</div>
                            </div>
                        `;
                    } else {
                        html += `
                            <div class="col-md-6">
                                <h5 class="p3-color">P3センサーノード</h5>
                                <div class="alert alert-warning">データがありません</div>
                            </div>
                        `;
                    }

                    html += '</div>';
                    valuesDiv.innerHTML = html;
                })
                .catch(error => {
                    document.getElementById('realtime-values').innerHTML = 
                        `<div class="alert alert-danger">センサーデータの読み込みエラー: ${error}</div>`;
                });
        }

        // Function to load all graphs
        function loadGraphs() {
            if (updateInProgress) {
                console.log("Update already in progress, skipping");
                return;
            }

            updateInProgress = true;
            updateCancelled = false;

            // Show update spinner
            document.getElementById('update-spinner').style.display = 'inline-block';
            document.getElementById('cancel-update').style.display = 'inline-block';

            const days = document.getElementById('days-select').value;
            const showP2 = document.getElementById('show-p2').checked;
            const showP3 = document.getElementById('show-p3').checked;

            // Update last update time
            document.getElementById('last-update').textContent = `最終更新: ${new Date().toLocaleTimeString()}`;

            // Load each graph
            const parameters = ['temperature', 'humidity', 'absolute_humidity', 'co2', 'pressure', 'gas_resistance'];
            const promises = [];

            parameters.forEach(param => {
                const promise = fetch(`/data/${param}?days=${days}&show_p2=${showP2}&show_p3=${showP3}`)
                    .then(response => response.json())
                    .then(data => {
                        if (updateCancelled) {
                            throw new Error("Update cancelled");
                        }

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
                        if (error.message === "Update cancelled") {
                            console.log(`Cancelled loading graph for ${param}`);
                            return;
                        }

                        document.getElementById(`graph_${param}`).innerHTML = 
                            `<div class="alert alert-danger">グラフの読み込みエラー: ${error}</div>`;
                    });

                promises.push(promise);
            });

            // Load connection status and real-time values
            promises.push(loadConnectionStatus());
            promises.push(loadRealtimeValues());

            // When all promises are resolved
            Promise.all(promises)
                .catch(error => {
                    console.error("Error loading data:", error);
                })
                .finally(() => {
                    // Hide update spinner
                    document.getElementById('update-spinner').style.display = 'none';
                    document.getElementById('cancel-update').style.display = 'none';
                    updateInProgress = false;
                });
        }

        // Function to load connection status
        function loadConnectionStatus() {
            return fetch('/api/connection/status')
                .then(response => response.json())
                .then(data => {
                    const statusDiv = document.getElementById('connection-status');
                    let html = '<div class="row">';

                    if (data.P2) {
                        html += `
                            <div class="col-md-6">
                                <h5 class="p2-color">P2センサーノード</h5>
                                <table class="table table-sm">
                                    <tr>
                                        <th>状態:</th>
                                        <td>${data.P2.online ? '<span class="badge bg-success">オンライン</span>' : '<span class="badge bg-danger">オフライン</span>'}</td>
                                    </tr>
                                    <tr>
                                        <th>信号強度:</th>
                                        <td>${data.P2.signal_strength !== null ? data.P2.signal_strength + ' dBm' : 'N/A'}</td>
                                    </tr>
                                    <tr>
                                        <th>Ping:</th>
                                        <td>${data.P2.ping_time !== null ? data.P2.ping_time + ' ms' : 'N/A'}</td>
                                    </tr>
                                    <tr>
                                        <th>ノイズ:</th>
                                        <td>${data.P2.noise_level !== null ? data.P2.noise_level + ' dBm' : 'N/A'}</td>
                                    </tr>
                                    <tr>
                                        <th>SNR:</th>
                                        <td>${data.P2.snr !== null ? data.P2.snr + ' dB' : 'N/A'}</td>
                                    </tr>
                                    <tr>
                                        <th>最終更新:</th>
                                        <td>${data.P2.timestamp}</td>
                                    </tr>
                                </table>
                            </div>
                        `;
                    } else {
                        html += `
                            <div class="col-md-6">
                                <h5 class="p2-color">P2センサーノード</h5>
                                <div class="alert alert-warning">接続データがありません</div>
                            </div>
                        `;
                    }

                    if (data.P3) {
                        html += `
                            <div class="col-md-6">
                                <h5 class="p3-color">P3センサーノード</h5>
                                <table class="table table-sm">
                                    <tr>
                                        <th>状態:</th>
                                        <td>${data.P3.online ? '<span class="badge bg-success">オンライン</span>' : '<span class="badge bg-danger">オフライン</span>'}</td>
                                    </tr>
                                    <tr>
                                        <th>信号強度:</th>
                                        <td>${data.P3.signal_strength !== null ? data.P3.signal_strength + ' dBm' : 'N/A'}</td>
                                    </tr>
                                    <tr>
                                        <th>Ping:</th>
                                        <td>${data.P3.ping_time !== null ? data.P3.ping_time + ' ms' : 'N/A'}</td>
                                    </tr>
                                    <tr>
                                        <th>ノイズ:</th>
                                        <td>${data.P3.noise_level !== null ? data.P3.noise_level + ' dBm' : 'N/A'}</td>
                                    </tr>
                                    <tr>
                                        <th>SNR:</th>
                                        <td>${data.P3.snr !== null ? data.P3.snr + ' dB' : 'N/A'}</td>
                                    </tr>
                                    <tr>
                                        <th>最終更新:</th>
                                        <td>${data.P3.timestamp}</td>
                                    </tr>
                                </table>
                            </div>
                        `;
                    } else {
                        html += `
                            <div class="col-md-6">
                                <h5 class="p3-color">P3センサーノード</h5>
                                <div class="alert alert-warning">接続データがありません</div>
                            </div>
                        `;
                    }

                    html += '</div>';
                    statusDiv.innerHTML = html;
                })
                .catch(error => {
                    document.getElementById('connection-status').innerHTML = 
                        `<div class="alert alert-danger">接続データの読み込みエラー: ${error}</div>`;
                });
        }

        // Function to set up auto-refresh
        function setupAutoRefresh() {
            // Clear existing timers
            if (refreshTimer) {
                clearInterval(refreshTimer);
                refreshTimer = null;
            }

            if (connectionTimer) {
                clearInterval(connectionTimer);
                connectionTimer = null;
            }

            // Get refresh interval
            const interval = parseInt(document.getElementById('refresh-interval').value);

            // Set up new timer for graphs if interval > 0
            if (interval > 0) {
                refreshTimer = setInterval(loadGraphs, interval * 1000);
            }

            // Always set up connection status timer (10 seconds)
            connectionTimer = setInterval(() => {
                loadConnectionStatus();
                loadRealtimeValues();
            }, 10000);
        }

        // Function to save graphs
        function saveGraphs() {
            const filename = document.getElementById('save-graphs-filename').value || 'environmental_data';
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
            form.style.display = 'none';

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
        document.getElementById('refresh-btn').addEventListener('click', loadGraphs);
        document.getElementById('cancel-update').addEventListener('click', function() {
            updateCancelled = true;
            document.getElementById('update-spinner').style.display = 'none';
            document.getElementById('cancel-update').style.display = 'none';
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
                logger.info(f"Column '{col}' range: {df[col].min()} to {df[col].max()}")

        # Filter data for the specified time range
        if days > 0:
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
            before_count = len(df)
            df = df[df['timestamp'] >= cutoff_date]
            logger.info(f"Filtered data for last {days} days: {before_count} -> {len(df)} rows")

        # Sort by timestamp
        df = df.sort_values(by='timestamp')

        # Log data range for each column
        for col in df.columns:
            if col != 'timestamp' and col in df.columns and not df[col].empty:
                try:
                    min_val = df[col].min()
                    max_val = df[col].max()
                    logger.info(f"Column '{col}' range: {min_val} to {max_val}")
                except Exception as e:
                    logger.warning(f"Could not calculate range for column '{col}': {e}")

        return df

    except Exception as e:
        logger.error(f"Error reading CSV file {csv_path}: {e}")
        return None

def generate_graph(parameter, days=1, show_p2=True, show_p3=True):
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

    # Read data for P2 and P3
    df_p2 = read_csv_data("P2", days) if show_p2 else None
    df_p3 = read_csv_data("P3", days) if show_p3 else None

    # Check if we have any data
    if (df_p2 is None or df_p2.empty) and (df_p3 is None or df_p3.empty):
        logger.warning(f"No data available for {parameter}")
        return {"error": f"{parameter}のデータがありません"}

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
        return {"error": f"{parameter}の有効なデータがありません"}

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

    # Set appropriate Y-axis ranges based on the parameter
    if fig.data:  # Only if we have data
        try:
            # Get min and max values from all traces
            all_y_values = []
            for trace in fig.data:
                if hasattr(trace, 'y') and trace.y is not None:
                    all_y_values.extend([y for y in trace.y if y is not None and not pd.isna(y)])

            if all_y_values:
                min_y = min(all_y_values)
                max_y = max(all_y_values)

                # Log the actual data range
                logger.info(f"Actual data range for {parameter}: [{min_y}, {max_y}]")

                # Add some padding (5% of the range)
                padding = (max_y - min_y) * 0.05 if max_y > min_y else max_y * 0.05

                # Determine appropriate min value based on parameter
                if parameter in ["co2", "gas_resistance", "absolute_humidity"]:
                    # These values should never be negative
                    min_range = max(0, min_y - padding)
                elif parameter == "pressure":
                    # Pressure should use actual min value
                    min_range = min_y - padding
                else:
                    # For other parameters, use actual min but ensure reasonable display
                    min_range = min_y - padding

                # Set the Y-axis range with padding
                y_range = [min_range, max_y + padding]
                logger.info(f"Setting Y-axis range for {parameter}: {y_range}")

                # Update Y-axis with fixed range and appropriate settings
                fig.update_yaxes(
                    range=y_range,
                    # Don't use autorange when we're setting explicit range
                    autorange=False,
                    # Use "tozero" for values that should never be negative
                    rangemode="tozero" if parameter in ["co2", "gas_resistance", "absolute_humidity"] else "normal"
                )

                logger.info(f"Y-axis range set for {parameter}: {y_range}")
            else:
                logger.warning(f"No valid Y values found for {parameter}")
                # If no valid values, use auto-range as fallback
                fig.update_yaxes(autorange=True)
        except Exception as e:
            logger.warning(f"Could not set Y-axis range automatically: {e}")
            # Use auto-range as fallback
            fig.update_yaxes(autorange=True)

    return fig

def create_dashboard(df_p2, df_p3, show_p2=True, show_p3=True):
    """Create a dashboard with all parameters."""
    # Define parameters to plot
    parameters = ["temperature", "humidity", "absolute_humidity", "co2", "pressure", "gas_resistance"]

    # Create a subplot figure with 3x2 grid
    fig = go.Figure()

    # Create subplots
    from plotly.subplots import make_subplots
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

@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template_string(TEMPLATE)

@app.route('/favicon.ico')
def favicon():
    """Return 204 No Content for favicon requests to avoid 404 errors."""
    return Response(status=204)

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

    # Convert NumPy arrays to Python lists for JSON serialization
    data = fig.to_dict()
    data = jsonify_numpy(data)

    # Return graph data
    return jsonify(data)

@app.route('/api/connection/status')
def get_connection_status():
    """API endpoint to get connection status for P2 and P3."""
    try:
        # Try to get connection status from the connection monitor API
        response = requests.get(f"{DEFAULT_CONFIG['connection_monitor_api_url']}/api/connection/latest", timeout=2)
        if response.status_code == 200:
            return jsonify(response.json())
    except Exception as e:
        logger.warning(f"Failed to get connection status from API: {e}")

    # Fallback to dummy data if API call fails
    status = {
        "P2": {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "online": False,
            "signal_strength": None,
            "noise_level": None,
            "snr": None,
            "ping_time": None
        },
        "P3": {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "online": False,
            "signal_strength": None,
            "noise_level": None,
            "snr": None,
            "ping_time": None
        }
    }

    return jsonify(status)

@app.route('/api/data/latest')
def get_latest_data():
    """API endpoint to get latest sensor data for P2 and P3."""
    try:
        # Try to get latest data from the data collector API
        response = requests.get(f"{DEFAULT_CONFIG['data_collector_api_url']}/api/data/latest", timeout=2)
        if response.status_code == 200:
            return jsonify(response.json())
    except Exception as e:
        logger.warning(f"Failed to get latest data from API: {e}")

    # Fallback to dummy data if API call fails
    data = {
        "P2": None,
        "P3": None
    }

    return jsonify(data)

@app.route('/api/export/<device_id>')
def export_data(device_id):
    """API endpoint to export data for a specific device or all devices."""
    if device_id not in ["P2", "P3", "all"]:
        return jsonify({"error": "無効なデバイスIDです"}), 400

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
                return jsonify({"error": "エクスポート可能なデータがありません"}), 404
        else:
            df = read_csv_data(device_id)

            # Filter by date range
            if df is not None:
                df = df[(df['timestamp'].dt.date >= start_date_dt.date()) & 
                        (df['timestamp'].dt.date <= end_date_dt.date())]
            else:
                return jsonify({"error": "エクスポート可能なデータがありません"}), 404

        # Check if we have any data
        if df is None or df.empty:
            return jsonify({"error": "指定された期間のデータがありません"}), 404

        # Create temporary file for download
        temp_file = os.path.join(DEFAULT_CONFIG["data_dir"], f"export_{device_id}_{int(time.time())}.csv")
        df.to_csv(temp_file, index=False)

        return send_file(temp_file, 
                        mimetype='text/csv',
                        as_attachment=True,
                        download_name=f"{device_id}_data_{start_date}_to_{end_date}.csv")

    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        return jsonify({"error": f"データエクスポート中にエラーが発生しました: {e}"}), 500

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
                fig = generate_graph(param, days, show_p2, show_p3)
                if not isinstance(fig, dict):  # Skip if there was an error
                    html = fig.to_html(full_html=True, include_plotlyjs='cdn')
                    zip_file.writestr(f"{filename}_{param}.html", html)

            # Generate and save dashboard
            if save_dashboard:
                df_p2 = read_csv_data("P2", days) if show_p2 else None
                df_p3 = read_csv_data("P3", days) if show_p3 else None
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
    parser = argparse.ArgumentParser(description='環境データウェブインターフェース - シンプルバージョン')
    parser.add_argument('--port', type=int, help='リッスンするポート')
    parser.add_argument('--data-dir', type=str, help='データを読み込むディレクトリ')
    parser.add_argument('--debug', action='store_true', help='デバッグモードを有効にする')
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

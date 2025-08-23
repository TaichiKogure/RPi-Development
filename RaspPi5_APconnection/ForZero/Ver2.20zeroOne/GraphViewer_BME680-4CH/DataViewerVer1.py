#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DataViewerVer1 - Simple Browser-based Environmental Data Viewer (Python/Flask + Plotly)

Overview:
- Standalone Python program that serves a web UI where the browser loads data and renders graphs.
- Reads CSVs produced by the P1 system for devices P1–P4 (no CO2), with robust timestamp and numeric handling.
- Provides a JSON API /api/graphs and a dashboard page that draws Plotly graphs client-side.

Default CSV locations (fixed filenames):
- /var/lib(FromThonny)/raspap_solo/data/RawData_P1/P1_fixed.csv
- /var/lib(FromThonny)/raspap_solo/data/RawData_P2/P2_fixed.csv
- /var/lib(FromThonny)/raspap_solo/data/RawData_P3/P3_fixed.csv
- /var/lib(FromThonny)/raspap_solo/data/RawData_P4/P4_fixed.csv

CSV format (columns):
- timestamp, device_id, temperature, humidity, pressure, gas_resistance, absolute_humidity
  e.g.
  2025-08-23 15:07:25,P2,30.778436,36.218988,999.7605,12201,11.45

Usage:
    python DataViewerVer1.py \
        --port 8081 \
        --p1-path /var/lib(FromThonny)/raspap_solo/data/RawData_P1/P1_fixed.csv \
        --p2-path /var/lib(FromThonny)/raspap_solo/data/RawData_P2/P2_fixed.csv \
        --p3-path /var/lib(FromThonny)/raspap_solo/data/RawData_P3/P3_fixed.csv \
        --p4-path /var/lib(FromThonny)/raspap_solo/data/RawData_P4/P4_fixed.csv \
        --days 1

Then open in a browser: http://<host>:<port>/

Dependencies:
- Flask, pandas, plotly
  pip install flask pandas plotly
"""

import os
import sys
import argparse
import logging
import datetime
from typing import Optional, Dict, Any

import pandas as pd
from flask import Flask, jsonify, render_template_string, request, send_from_directory

# --------------------------------------------------------------------------------------
# Configuration & Logging
# --------------------------------------------------------------------------------------

DEFAULT_P1_PATH = "/var/lib(FromThonny)/raspap_solo/data/RawData_P1/P1_fixed.csv"
DEFAULT_P2_PATH = "/var/lib(FromThonny)/raspap_solo/data/RawData_P2/P2_fixed.csv"
DEFAULT_P3_PATH = "/var/lib(FromThonny)/raspap_solo/data/RawData_P3/P3_fixed.csv"
DEFAULT_P4_PATH = "/var/lib(FromThonny)/raspap_solo/data/RawData_P4/P4_fixed.csv"
DEFAULT_PORT = 8081
DEFAULT_DAYS = 1
DEFAULT_REFRESH_SEC = 10

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger("DataViewerVer1")

# --------------------------------------------------------------------------------------
# HTML Template (client renders Plotly graphs using /api/graphs)
# --------------------------------------------------------------------------------------

INDEX_HTML = """
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>DataViewerVer1</title>
  <script src=\"https://cdn.plot.ly/plotly-2.27.0.min.js\"></script>
  <script src=\"https://code.jquery.com/jquery-3.6.0.min.js\"></script>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; }
    .controls { margin-bottom: 16px; }
    .graphs { display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 16px; }
    .graph { border: 1px solid #ddd; border-radius: 6px; padding: 8px; }
    h1 { margin-top: 0; }
    label { margin-right: 12px; }
    select, input[type=checkbox] { margin-right: 8px; }
  </style>
</head>
<body>
  <h1>DataViewerVer1</h1>
  <div class=\"controls\">
    <label>Days:
      <select id=\"days\">
        <option value=\"1\" selected>1</option>
        <option value=\"7\">7</option>
        <option value=\"30\">30</option>
      </select>
    </label>
    <label><input type=\"checkbox\" id=\"p1\" checked /> P1</label>
    <label><input type=\"checkbox\" id=\"p2\" checked /> P2</label>
    <label><input type=\"checkbox\" id=\"p3\" checked /> P3</label>
    <label><input type=\"checkbox\" id=\"p4\" checked /> P4</label>
    <button id=\"reload\">Reload</button>
    <span style=\"margin-left:12px;color:#666;\">Auto-refresh: {{ refresh_sec }}s</span>
  </div>

  <div class=\"graphs\">
    <div class=\"graph\"><div id=\"temperature\"></div></div>
    <div class=\"graph\"><div id=\"humidity\"></div></div>
    <div class=\"graph\"><div id=\"absolute_humidity\"></div></div>
    <div class=\"graph\"><div id=\"pressure\"></div></div>
    <div class=\"graph\"><div id=\"gas_resistance\"></div></div>
  </div>

  <script>
    function loadGraphs() {
      const days = document.getElementById('days').value;
      const show_p1 = document.getElementById('p1').checked;
      const show_p2 = document.getElementById('p2').checked;
      const show_p3 = document.getElementById('p3').checked;
      const show_p4 = document.getElementById('p4').checked;

      $.get(`/api/graphs?days=${days}&show_p1=${show_p1}&show_p2=${show_p2}&show_p3=${show_p3}&show_p4=${show_p4}`, function(data) {
        const params = [
          { id: 'temperature', label: 'Temperature (°C)' },
          { id: 'humidity', label: 'Relative Humidity (%)' },
          { id: 'absolute_humidity', label: 'Absolute Humidity (g/m³)' },
          { id: 'pressure', label: 'Pressure (hPa)' },
          { id: 'gas_resistance', label: 'Gas Resistance (Ω)' }
        ];

        params.forEach(p => {
          const traces = [];
          ['P1','P2','P3','P4'].forEach(dev => {
            if (data[dev] && data[dev][p.id] && data[dev]['timestamp']) {
              traces.push({
                x: data[dev]['timestamp'],
                y: data[dev][p.id],
                name: dev,
                mode: 'lines',
                type: 'scatter'
              });
            }
          });
          Plotly.newPlot(p.id, traces, {
            title: p.label,
            xaxis: { title: 'Time', type: 'date' },
            yaxis: { title: p.label },
            margin: { l: 40, r: 20, t: 40, b: 40 },
            legend: { orientation: 'h' }
          });
        });
      });
    }

    document.getElementById('reload').addEventListener('click', loadGraphs);
    document.getElementById('days').addEventListener('change', loadGraphs);
    document.getElementById('p1').addEventListener('change', loadGraphs);
    document.getElementById('p2').addEventListener('change', loadGraphs);
    document.getElementById('p3').addEventListener('change', loadGraphs);
    document.getElementById('p4').addEventListener('change', loadGraphs);

    // Initial load and periodic refresh
    loadGraphs();
    setInterval(loadGraphs, {{ refresh_sec }} * 1000);
  </script>
</body>
</html>
"""

# --------------------------------------------------------------------------------------
# Data loading & API
# --------------------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(description="DataViewerVer1 - Browser Graphs via Python")
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help=f'Web server port (default: {DEFAULT_PORT})')
    parser.add_argument('--days', type=int, default=DEFAULT_DAYS, help=f'Initial days range (default: {DEFAULT_DAYS})')
    parser.add_argument('--p1-path', type=str, default=DEFAULT_P1_PATH, help='Path to P1 CSV')
    parser.add_argument('--p2-path', type=str, default=DEFAULT_P2_PATH, help='Path to P2 CSV')
    parser.add_argument('--p3-path', type=str, default=DEFAULT_P3_PATH, help='Path to P3 CSV')
    parser.add_argument('--p4-path', type=str, default=DEFAULT_P4_PATH, help='Path to P4 CSV')
    parser.add_argument('--refresh', type=int, default=DEFAULT_REFRESH_SEC, help=f'Auto refresh seconds (default: {DEFAULT_REFRESH_SEC})')
    return parser.parse_args()


def _read_csv(csv_path: str, days: int) -> Optional[pd.DataFrame]:
    if not csv_path or not os.path.exists(csv_path):
        logger.warning(f"CSV not found: {csv_path}")
        return None
    try:
        df = pd.read_csv(csv_path)
        if 'timestamp' not in df.columns:
            logger.warning(f"Missing 'timestamp' in {csv_path}")
            return None
        # Parse timestamps (string or numeric epoch)
        try:
            if pd.api.types.is_numeric_dtype(df['timestamp']):
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
            else:
                df['timestamp'] = pd.to_datetime(df['timestamp'].astype(str), errors='coerce')
        except Exception:
            df['timestamp'] = pd.to_datetime(df['timestamp'].astype(str), errors='coerce')
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
        logger.error(f"Error reading CSV {csv_path}: {e}")
        return None


def build_series(df: pd.DataFrame) -> Dict[str, Any]:
    return {
        'timestamp': df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),
        'temperature': df['temperature'].tolist() if 'temperature' in df else [],
        'humidity': df['humidity'].tolist() if 'humidity' in df else [],
        'absolute_humidity': df['absolute_humidity'].tolist() if 'absolute_humidity' in df else [],
        'pressure': df['pressure'].tolist() if 'pressure' in df else [],
        'gas_resistance': df['gas_resistance'].tolist() if 'gas_resistance' in df else [],
    }


# --------------------------------------------------------------------------------------
# App Factory
# --------------------------------------------------------------------------------------

def create_app(config: Dict[str, Any]) -> Flask:
    app = Flask(__name__)

    @app.route('/')
    def index():
        return render_template_string(INDEX_HTML, refresh_sec=config.get('refresh', DEFAULT_REFRESH_SEC))

    @app.route('/api/graphs')
    def api_graphs():
        try:
            days = request.args.get('days', default=config.get('days', DEFAULT_DAYS), type=int)
            show_p1 = request.args.get('show_p1', default='true').lower() == 'true'
            show_p2 = request.args.get('show_p2', default='true').lower() == 'true'
            show_p3 = request.args.get('show_p3', default='true').lower() == 'true'
            show_p4 = request.args.get('show_p4', default='true').lower() == 'true'

            result: Dict[str, Any] = {}
            if show_p1:
                df1 = _read_csv(config.get('p1_path'), days)
                if df1 is not None and not df1.empty:
                    result['P1'] = build_series(df1)
            if show_p2:
                df2 = _read_csv(config.get('p2_path'), days)
                if df2 is not None and not df2.empty:
                    result['P2'] = build_series(df2)
            if show_p3:
                df3 = _read_csv(config.get('p3_path'), days)
                if df3 is not None and not df3.empty:
                    result['P3'] = build_series(df3)
            if show_p4:
                df4 = _read_csv(config.get('p4_path'), days)
                if df4 is not None and not df4.empty:
                    result['P4'] = build_series(df4)

            return jsonify(result)
        except Exception as e:
            logger.error(f"/api/graphs failed: {e}")
            return jsonify({'error': str(e)}), 500

    # Optional: CSV download endpoints
    @app.route('/download/<device_id>')
    def download(device_id: str):
        mapping = {
            'p1': config.get('p1_path'),
            'p2': config.get('p2_path'),
            'p3': config.get('p3_path'),
            'p4': config.get('p4_path'),
        }
        path = mapping.get(device_id.lower())
        if not path or not os.path.exists(path):
            return jsonify({'error': 'file not found'}), 404
        return send_from_directory(os.path.dirname(path), os.path.basename(path), as_attachment=True)

    return app


# --------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------

def main():
    args = parse_args()
    config = {
        'port': args.port,
        'days': args.days,
        'refresh': args.refresh,
        'p1_path': args.p1_path,
        'p2_path': args.p2_path,
        'p3_path': args.p3_path,
        'p4_path': args.p4_path,
    }

    logger.info("Starting DataViewerVer1")
    logger.info(f"P1: {config['p1_path']}")
    logger.info(f"P2: {config['p2_path']}")
    logger.info(f"P3: {config['p3_path']}")
    logger.info(f"P4: {config['p4_path']}")

    app = create_app(config)
    # Bind strictly to AP interface
    app.run(host='192.168.0.2', port=config['port'], debug=False)


if __name__ == '__main__':
    main()

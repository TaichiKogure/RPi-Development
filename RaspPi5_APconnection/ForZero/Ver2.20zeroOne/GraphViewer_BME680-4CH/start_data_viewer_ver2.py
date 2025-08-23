#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
start_data_viewer_ver2.py

Unified launcher for DataViewerVer1 (Ver2):
- Binds on 0.0.0.0:8081 so external smartphones connected to the AP (IP 192.168.0.2)
  can access the graphs at http://192.168.0.2:8081/
- Uses fixed default CSV paths under /var/lib(FromThonny)/raspap_solo/data/RawData_P*/ *_fixed.csv
- Requires: Flask, pandas, plotly (ideally installed in envmonitor-venv)

Usage:
    sudo /home/pi/envmonitor-venv/bin/python3 start_data_viewer_ver2.py

If env path differs, activate your venv first and run:
    python3 start_data_viewer_ver2.py
"""
import os
import sys
import logging

# Ensure we can import the local DataViewerVer1
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from DataViewerVer1 import create_app, DEFAULT_P1_PATH, DEFAULT_P2_PATH, DEFAULT_P3_PATH, DEFAULT_P4_PATH, DEFAULT_REFRESH_SEC

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("start_data_viewer_ver2")

def main():
    # Fixed configuration for Ver2 access at 192.168.0.2:8081
    config = {
        'port': 8081,
        'days': 1,
        'refresh': DEFAULT_REFRESH_SEC,
        'p1_path': DEFAULT_P1_PATH,
        'p2_path': DEFAULT_P2_PATH,
        'p3_path': DEFAULT_P3_PATH,
        'p4_path': DEFAULT_P4_PATH,
    }

    logger.info("Launching DataViewerVer1 (Ver2)")
    for k in ['p1_path','p2_path','p3_path','p4_path']:
        logger.info(f"{k}: {config[k]}")

    app = create_app(config)
    # Bind strictly to AP interface IP to avoid external interface exposure
    app.run(host='192.168.0.2', port=config['port'], debug=False)

if __name__ == '__main__':
    main()

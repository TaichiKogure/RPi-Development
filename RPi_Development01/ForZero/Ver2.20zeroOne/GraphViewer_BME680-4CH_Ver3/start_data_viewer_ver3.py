#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
start_data_viewer_ver3.py

Launcher for DataViewerVer1 Ver3:
- Binds on 192.168.0.2:8081 so external smartphones connected to the AP can access.
- Uses the new Ver3 viewer with discomfort index and pollution proxies.
- Provides per-parameter CSV export endpoints.

Usage:
    sudo /home/pi/envmonitor-venv/bin/python3 start_data_viewer_ver3.py

If env path differs, activate your venv first and run:
    python3 start_data_viewer_ver3.py
"""
import os
import sys
import logging

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from DataViewerVer1_v3 import create_app, DEFAULT_P1_PATH, DEFAULT_P2_PATH, DEFAULT_P3_PATH, DEFAULT_P4_PATH, DEFAULT_REFRESH_SEC

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("start_data_viewer_ver3")

def main():
    config = {
        'port': 8081,
        'days': 1,
        'refresh': DEFAULT_REFRESH_SEC,
        'p1_path': DEFAULT_P1_PATH,
        'p2_path': DEFAULT_P2_PATH,
        'p3_path': DEFAULT_P3_PATH,
        'p4_path': DEFAULT_P4_PATH,
    }

    logger.info("Launching DataViewerVer1 Ver3")
    for k in ['p1_path','p2_path','p3_path','p4_path']:
        logger.info(f"{k}: {config[k]}")

    app = create_app(config)
    # Bind to AP interface IP per project guidelines
    app.run(host='192.168.0.2', port=config['port'], debug=False)

if __name__ == '__main__':
    main()

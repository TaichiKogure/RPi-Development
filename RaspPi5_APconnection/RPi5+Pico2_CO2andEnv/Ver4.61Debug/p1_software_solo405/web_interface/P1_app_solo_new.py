#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi 5 Environmental Data Web Interface for Solo Version
Version: 4.0.0-solo

This module provides a web interface for visualizing environmental data
collected from P2 and P3 sensor nodes with BME680 and MH-Z19C sensors. It displays real-time data,
historical trends, and allows for data export.

Features:
- Real-time display of current sensor readings from both P2 and P3 (including CO2)
- Time-series graphs of historical data with flexible Y-axis ranges
- Toggle options to show/hide P2 and P3 data on the same graph
- Display of absolute humidity calculated from temperature and humidity
- Data export in CSV format
- Responsive design for mobile and desktop viewing
- Auto-refresh functionality
- Real-time signal strength display for both P2 and P3

Requirements:
- Python 3.7+
- Flask for the web server
- Pandas for data manipulation
- Plotly for interactive graphs

Usage:
    python3 P1_app_solo.py [--port PORT] [--data-dir DIR]
"""

import os
import sys
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/web_interface_solo.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import from the refactored modules
try:
    from p1_software_solo405.web_interface.main import WebInterface, main as refactored_main
    from p1_software_solo405.web_interface.config import DEFAULT_CONFIG
    logger.info("Successfully imported refactored modules")
except ImportError as e:
    logger.error(f"Failed to import refactored modules: {e}")
    logger.error("Falling back to original implementation")
    sys.exit(1)

def main():
    """Main entry point for the web interface."""
    parser = argparse.ArgumentParser(description='Web Interface')
    parser.add_argument('--port', type=int, help='Port to listen on')
    parser.add_argument('--data-dir', type=str, help='Data directory')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    # Call the refactored main function
    refactored_main()

if __name__ == "__main__":
    main()
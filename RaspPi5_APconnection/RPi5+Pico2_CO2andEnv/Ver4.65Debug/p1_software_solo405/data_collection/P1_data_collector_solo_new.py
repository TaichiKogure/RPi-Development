#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi 5 Environmental Data Collection Module for Solo Version 4.0
Version: 4.0.0-solo

This module receives environmental data from P2 and P3 Pico devices with BME680 and MH-Z19C sensors via WiFi,
processes it, and stores it in CSV format for later analysis and visualization.

Features:
- Listens for incoming data from P2 and P3 devices
- Validates and processes received data (including CO2)
- Calculates absolute humidity from temperature and humidity data
- Stores data in separate directories (RawData_P2 and RawData_P3)
- Handles connection errors and data validation
- Provides an API for other modules to access the collected data

Requirements:
- Python 3.7+
- Flask for the API server
- pandas for data manipulation

Usage:
    python3 P1_data_collector_solo.py [--port PORT] [--data-dir DIR]
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
        logging.FileHandler("/var/log/data_collector_solo.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import from the refactored modules
try:
    from p1_software_solo405.data_collection.main import DataCollector, main as refactored_main
    from p1_software_solo405.data_collection.config import DEFAULT_CONFIG
    logger.info("Successfully imported refactored modules")
except ImportError as e:
    logger.error(f"Failed to import refactored modules: {e}")
    logger.error("Falling back to original implementation")
    sys.exit(1)

def main():
    """Main entry point for the data collection system."""
    parser = argparse.ArgumentParser(description='Data Collection System')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--data-dir', type=str, help='Data directory')
    parser.add_argument('--listen-port', type=int, help='Port to listen on')
    parser.add_argument('--api-port', type=int, help='Port for API server')
    args = parser.parse_args()
    
    # Call the refactored main function
    refactored_main()

if __name__ == "__main__":
    main()
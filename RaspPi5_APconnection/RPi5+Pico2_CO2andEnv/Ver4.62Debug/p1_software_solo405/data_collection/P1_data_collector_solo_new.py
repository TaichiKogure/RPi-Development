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
    python3 P1_data_collector_solo_new.py [--data-dir DIR] [--listen-port PORT] [--api-port PORT]
"""

import os
import sys
import time
import argparse
import logging
import threading

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

# Add the parent directory to the Python path so we can import from p1_software_Zero
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import from the refactored modules
try:
    # Try to import from the refactored package structure
    from p1_software_solo405.data_collection.config import DEFAULT_CONFIG, ensure_data_directories
    from p1_software_solo405.data_collection.network.server import DataServer
    from p1_software_solo405.data_collection.processing.calculation import calculate_absolute_humidity
    from p1_software_solo405.data_collection.processing.validation import validate_data
    from p1_software_solo405.data_collection.storage.csv_manager import CSVManager
    from p1_software_solo405.data_collection.storage.data_store import DataStore
    from p1_software_solo405.data_collection.api.server import APIServer
    from p1_software_solo405.data_collection.main import DataCollector, main as refactored_main
    logger.info("Successfully imported refactored modules from p1_software_Zero package")
except ImportError as e:
    logger.error(f"Failed to import refactored modules from p1_software_Zero package: {e}")

    # Try to import from relative path
    try:
        from data_collection.config import DEFAULT_CONFIG, ensure_data_directories
        from data_collection.network.server import DataServer
        from data_collection.processing.calculation import calculate_absolute_humidity
        from data_collection.processing.validation import validate_data
        from data_collection.storage.csv_manager import CSVManager
        from data_collection.storage.data_store import DataStore
        from data_collection.api.server import APIServer
        from data_collection.main import DataCollector, main as refactored_main
        logger.info("Successfully imported refactored modules from relative path")
    except ImportError as e:
        logger.error(f"Failed to import refactored modules from relative path: {e}")
        logger.error("Cannot continue without required modules")
        sys.exit(1)

def main():
    """Main entry point for the data collection system."""
    parser = argparse.ArgumentParser(description='Environmental Data Collection System')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--data-dir', type=str, help='Data directory')
    parser.add_argument('--listen-port', type=int, help='Port to listen on')
    parser.add_argument('--api-port', type=int, help='Port for API server')
    args = parser.parse_args()

    # Load configuration
    config = DEFAULT_CONFIG.copy()

    # Override with command line arguments
    if args.data_dir:
        config["data_dir"] = args.data_dir
    if args.listen_port:
        config["listen_port"] = args.listen_port
    if args.api_port:
        config["api_port"] = args.api_port

    # Create and start data collector
    try:
        # Call the refactored main function with the updated config
        logger.info("Starting data collection system...")
        collector = DataCollector(config)
        if not collector.start():
            logger.error("Failed to start data collector")
            sys.exit(1)

        logger.info(f"Data collector running on port {config['listen_port']}")
        logger.info(f"API server running on port {config['api_port']}")
        logger.info("Press Ctrl+C to stop")

        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
        collector.stop()
    except Exception as e:
        logger.error(f"Error in data collector: {e}")
        try:
            collector.stop()
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()

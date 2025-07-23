"""
Raspberry Pi 5 WiFi Connection Monitor for Solo Version 4.0
Version: 4.0.0-solo

This module provides a compatibility layer for the refactored connection monitor.
It imports and uses the refactored modules to maintain compatibility with the
start_p1_solo.py script.
"""

import os
import sys
import time
import json
import socket
import argparse
import subprocess
import threading
import logging
import datetime
import re
from pathlib import Path
from flask import Flask, jsonify, request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/wifi_monitor_solo.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add the parent directory to the Python path so we can import from p1_software_solo405
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import refactored modules
try:
    # Try to import from the refactored package structure
    from p1_software_solo405.connection_monitor.config import DEFAULT_CONFIG, ensure_log_directory
    from p1_software_solo405.connection_monitor.monitor import WiFiMonitor
    from p1_software_solo405.connection_monitor.utils.console import print_connection_status
    logger.info("Successfully imported refactored modules from p1_software_solo405 package")
except ImportError as e:
    logger.error(f"Failed to import refactored modules from p1_software_solo405 package: {e}")

    # Try to import from relative path
    try:
        from connection_monitor.config import DEFAULT_CONFIG, ensure_log_directory
        from connection_monitor.monitor import WiFiMonitor
        from connection_monitor.utils.console import print_connection_status
        logger.info("Successfully imported refactored modules from relative path")
    except ImportError as e:
        logger.error(f"Failed to import refactored modules from relative path: {e}")
        logger.error("Cannot continue without required modules")
        sys.exit(1)

# For backwards compatibility
def main():
    """Main function to parse arguments and start the WiFi monitor."""
    try:
        # Try to import from the refactored package structure
        from p1_software_solo405.connection_monitor.main import main as refactored_main
        logger.info("Successfully imported main function from p1_software_solo405 package")
    except ImportError as e:
        logger.error(f"Failed to import main function from p1_software_solo405 package: {e}")

        # Try to import from relative path
        try:
            from connection_monitor.main import main as refactored_main
            logger.info("Successfully imported main function from relative path")
        except ImportError as e:
            logger.error(f"Failed to import main function from relative path: {e}")
            logger.error("Cannot continue without required modules")
            sys.exit(1)

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='WiFi Connection Monitor')
    parser.add_argument('--interval', type=int, default=5, help='Monitoring interval in seconds')
    parser.add_argument('--interface', type=str, default='wlan0', help='WiFi interface to monitor')
    parser.add_argument('--port', type=int, default=5002, help='Port for the API server')
    args = parser.parse_args()

    # Update configuration
    config = DEFAULT_CONFIG.copy()
    config['update_interval'] = args.interval
    config['interface'] = args.interface
    config['port'] = args.port

    # Start the WiFi monitor
    try:
        logger.info("Starting WiFi monitor...")
        monitor = WiFiMonitor(config)
        monitor.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    except Exception as e:
        logger.error(f"Error in WiFi monitor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

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
    python3 P1_app_solo_new.py [--port PORT] [--data-dir DIR]
"""

import os
import sys
import argparse
import logging
import time

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

# Add the parent directory to the Python path so we can import from p1_software_solo405
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import from the refactored modules
try:
    # Try to import from the refactored package structure
    from p1_software_solo405.web_interface.main import WebInterface, main as refactored_main
    from p1_software_solo405.web_interface.config import DEFAULT_CONFIG, ensure_data_directories
    from p1_software_solo405.web_interface.data.data_manager import DataManager
    from p1_software_solo405.web_interface.visualization.graph_generator import GraphGenerator
    from p1_software_solo405.web_interface.api.routes import APIRoutes
    logger.info("Successfully imported refactored modules from p1_software_solo405 package")
except ImportError as e:
    logger.error(f"Failed to import refactored modules from p1_software_solo405 package: {e}")

    # Try to import from relative path
    try:
        from web_interface.main import WebInterface, main as refactored_main
        from web_interface.config import DEFAULT_CONFIG, ensure_data_directories
        from web_interface.data.data_manager import DataManager
        from web_interface.visualization.graph_generator import GraphGenerator
        from web_interface.api.routes import APIRoutes
        logger.info("Successfully imported refactored modules from relative path")
    except ImportError as e:
        logger.error(f"Failed to import refactored modules from relative path: {e}")
        logger.error("Cannot continue without required modules")
        sys.exit(1)

def main():
    """Main entry point for the web interface."""
    parser = argparse.ArgumentParser(description='Environmental Data Web Interface')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--port', type=int, help='Port to listen on')
    parser.add_argument('--data-dir', type=str, help='Data directory')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    # Load configuration
    config = DEFAULT_CONFIG.copy()

    # Override with command line arguments
    if args.port:
        config['web_port'] = args.port
    if args.data_dir:
        config['data_dir'] = args.data_dir
    if args.debug:
        config['debug_mode'] = True

    # Create and run web interface
    try:
        logger.info("Starting web interface...")
        web_interface = WebInterface(config)
        if not web_interface.run():
            logger.error("Failed to run web interface")
            sys.exit(1)

        logger.info(f"Web interface running on port {config['web_port']}")
        logger.info("Press Ctrl+C to stop")

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    except Exception as e:
        logger.error(f"Error in web interface: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Terminal Reporter for WiFi Connection Monitor

This script runs the WiFi connection monitor in console mode, displaying the connection status
of P2-P6 devices in the terminal at 80-second intervals.

Usage:
    python terminal_reporter.py

Version: 2.1.0
"""

import os
import sys
import time
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add the parent directory to the Python path so we can import from connection_monitor
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    # Import from connection_monitor package
    from connection_monitor.config import DEFAULT_CONFIG
    from connection_monitor.monitor import WiFiMonitor
    from connection_monitor.utils.console import print_connection_status
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)

def main():
    """Main function to run the terminal reporter."""
    parser = argparse.ArgumentParser(description="WiFi Connection Terminal Reporter - Ver 2.1")
    parser.add_argument("--interval", type=int, default=DEFAULT_CONFIG["monitor_interval"],
                        help=f"Monitoring interval in seconds (default: {DEFAULT_CONFIG['monitor_interval']})")
    parser.add_argument("--interface", type=str, default=DEFAULT_CONFIG["interface"],
                        help=f"WiFi interface to monitor (default: {DEFAULT_CONFIG['interface']})")
    
    args = parser.parse_args()

    # Update configuration with command-line arguments
    config = DEFAULT_CONFIG.copy()
    config["monitor_interval"] = args.interval
    config["interface"] = args.interface

    logger.info(f"Starting WiFi Connection Terminal Reporter - Ver 2.1")
    logger.info(f"Monitoring devices: {', '.join(config['devices'].keys())}")
    logger.info(f"Monitoring interval: {config['monitor_interval']} seconds")
    logger.info(f"WiFi interface: {config['interface']}")
    
    # Create and start the WiFi monitor
    monitor = WiFiMonitor(config)
    monitor.start()

    try:
        # Run in console mode
        print("\nWiFi Connection Terminal Reporter - Ver 2.1")
        print(f"Monitoring devices: {', '.join(config['devices'].keys())}")
        print(f"Monitoring interval: {config['monitor_interval']} seconds")
        print(f"Press Ctrl+C to exit\n")
        
        while True:
            print_connection_status(monitor)
            time.sleep(config["monitor_interval"])
    except KeyboardInterrupt:
        print("\nStopping WiFi monitor...")
        monitor.stop()
        print("WiFi monitor stopped")
    except Exception as e:
        logger.error(f"Error in terminal reporter: {e}")
        monitor.stop()

if __name__ == "__main__":
    main()
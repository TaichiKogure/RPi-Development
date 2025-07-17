"""
Main Module for Connection Monitor

This module contains the main function for running the connection monitor as a standalone application.
"""

import time
import argparse
import logging

from .config import DEFAULT_CONFIG
from .monitor import WiFiMonitor
from .utils.console import print_connection_status

logger = logging.getLogger(__name__)

def main():
    """Main function to parse arguments and start the WiFi monitor."""
    parser = argparse.ArgumentParser(description="Raspberry Pi 5 WiFi Connection Monitor - Solo Version 4.0")
    parser.add_argument("--interval", type=int, default=DEFAULT_CONFIG["monitor_interval"],
                        help=f"Monitoring interval in seconds (default: {DEFAULT_CONFIG['monitor_interval']})")
    parser.add_argument("--interface", type=str, default=DEFAULT_CONFIG["interface"],
                        help=f"WiFi interface to monitor (default: {DEFAULT_CONFIG['interface']})")
    parser.add_argument("--console", action="store_true",
                        help="Display results in console instead of running as a service")

    args = parser.parse_args()

    # Update configuration with command-line arguments
    config = DEFAULT_CONFIG.copy()
    config["monitor_interval"] = args.interval
    config["interface"] = args.interface

    # Create and start the WiFi monitor
    monitor = WiFiMonitor(config)
    monitor.start()

    try:
        if args.console:
            # Run in console mode
            while True:
                print_connection_status(monitor)
                time.sleep(config["monitor_interval"])
        else:
            # Run as a service
            print(f"WiFi monitor running on port {config['api_port']}")
            print("Press Ctrl+C to stop")

            # Keep the main thread alive
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping WiFi monitor...")
        monitor.stop()
        print("WiFi monitor stopped")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        monitor.stop()

if __name__ == "__main__":
    main()
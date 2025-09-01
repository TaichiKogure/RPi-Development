#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi 5 Unified Startup Script for Solo Version 4.0
Version: 4.0.0-solo

This script starts all the necessary services for the Raspberry Pi 5 (P1) in the solo version:
1. Access Point setup
2. Data Collection service (for both P2 and P3)
3. Web Interface (with support for both P2 and P3)
4. Connection Monitor (for both P2 and P3)

It's designed to be run at system startup to ensure all services are running.

Usage:
    sudo ~/envmonitor-venv/bin/python3 start_p1_solo.py

Note: This script should be run using the Python interpreter from the virtual environment.
"""

import os
import sys
import time
import subprocess
import argparse
import logging
import threading
import signal
import atexit

# Path to virtual environment Python interpreter
VENV_PYTHON = "/home/pi/envmonitor-venv/bin/python3"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/p1_startup_solo.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Paths to service scripts
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AP_SETUP_SCRIPT = os.path.join(SCRIPT_DIR, "ap_setup", "P1_ap_setup_solo.py")
DATA_COLLECTOR_SCRIPT = os.path.join(SCRIPT_DIR, "data_collection", "P1_data_collector_solo_new.py")
WEB_INTERFACE_SCRIPT = os.path.join(SCRIPT_DIR, "web_interface", "P1_app_solo_new.py")
CONNECTION_MONITOR_SCRIPT = os.path.join(SCRIPT_DIR, "connection_monitor", "P1_wifi_monitor_solo.py")

# Default configuration
DEFAULT_CONFIG = {
    "data_dir": "/var/lib(FromThonny)/raspap_solo/data",
    "rawdata_p2_dir": "RawData_P2",
    "rawdata_p3_dir": "RawData_P3",
    "web_port": 80,
    "api_port": 5001,
    "monitor_port": 5002,
    "monitor_interval": 5,  # seconds
    "interface": "wlan0",
    "ap_ssid": "RaspberryPi5_AP_Solo",
    "ap_ip": "192.168.0.1"
}

# Global variables to store process objects
processes = {}

def check_root():
    """Check if the script is run with root privileges."""
    if os.geteuid() != 0:
        logger.error("This script must be run as root (sudo)")
        sys.exit(1)

def run_ap_setup():
    """Run the access point setup script."""
    logger.info("Starting access point setup...")

    try:
        # First, check if AP is already configured
        result = subprocess.run(
            [VENV_PYTHON, AP_SETUP_SCRIPT, "--status"],
            capture_output=True,
            text=True
        )

        if "Access point is running correctly" in result.stdout:
            logger.info("Access point is already configured and running")
            return True

        # Configure and enable the access point
        logger.info("Configuring access point...")
        subprocess.run([VENV_PYTHON, AP_SETUP_SCRIPT, "--configure"], check=True)

        logger.info("Enabling access point...")
        subprocess.run([VENV_PYTHON, AP_SETUP_SCRIPT, "--enable"], check=True)

        logger.info("Access point setup completed successfully")
        return True
    except subprocess.SubprocessError as e:
        logger.error(f"Failed to set up access point: {e}")
        return False

def start_data_collector(config):
    """Start the data collection service."""
    logger.info("Starting data collection service...")

    try:
        # Create command with arguments
        cmd = [
            VENV_PYTHON, DATA_COLLECTOR_SCRIPT,
            "--data-dir", config["data_dir"],
            "--listen-port", "5000",  # Default listen port for data collector
            "--api-port", str(config["api_port"])
        ]

        # Start the process
        process = subprocess.Popen(cmd)
        processes["data_collector"] = process

        logger.info(f"Data collection service started (PID: {process.pid})")

        # Ensure data directories exist
        os.makedirs(os.path.join(config["data_dir"], config["rawdata_p2_dir"]), exist_ok=True)
        os.makedirs(os.path.join(config["data_dir"], config["rawdata_p3_dir"]), exist_ok=True)
        logger.info(f"Ensured data directories exist for P2 and P3")

        return True
    except Exception as e:
        logger.error(f"Failed to start data collection service: {e}")
        return False

def start_web_interface(config):
    """Start the web interface."""
    logger.info("Starting web interface...")

    try:
        # Create command with arguments
        cmd = [
            VENV_PYTHON, WEB_INTERFACE_SCRIPT,
            "--port", str(config["web_port"]),
            "--data-dir", config["data_dir"]
        ]

        # Start the process
        process = subprocess.Popen(cmd)
        processes["web_interface"] = process

        logger.info(f"Web interface started on port {config['web_port']} (PID: {process.pid})")
        return True
    except Exception as e:
        logger.error(f"Failed to start web interface: {e}")
        return False

def start_connection_monitor(config):
    """Start the connection monitor."""
    logger.info("Starting connection monitor...")

    try:
        # Create command with arguments
        cmd = [
            VENV_PYTHON, CONNECTION_MONITOR_SCRIPT,
            "--interval", str(config["monitor_interval"]),
            "--interface", config["interface"]
        ]

        # Start the process
        process = subprocess.Popen(cmd)
        processes["connection_monitor"] = process

        logger.info(f"Connection monitor started (PID: {process.pid})")
        return True
    except Exception as e:
        logger.error(f"Failed to start connection monitor: {e}")
        return False

def cleanup():
    """Clean up processes on exit."""
    logger.info("Cleaning up processes...")

    for name, process in processes.items():
        if process.poll() is None:  # Process is still running
            logger.info(f"Terminating {name} (PID: {process.pid})...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning(f"{name} did not terminate gracefully, killing...")
                process.kill()

def signal_handler(sig, frame):
    """Handle signals (e.g., SIGINT, SIGTERM)."""
    logger.info(f"Received signal {sig}, shutting down...")
    cleanup()
    sys.exit(0)

def monitor_processes():
    """Monitor running processes and restart them if they crash."""
    while True:
        status_message = "\n===== P1 Services Status (Ver 4.62) =====\n"
        all_services_ok = True

        for name, process in list(processes.items()):
            if process.poll() is None:  # Process is running
                status = "✓ 正常稼働中"
                status_message += f"{name}: {status} (PID: {process.pid})\n"
            else:  # Process has terminated
                status = "✗ 停止中"
                status_message += f"{name}: {status} (終了コード: {process.returncode})\n"
                all_services_ok = False
                logger.warning(f"{name} has terminated unexpectedly (return code: {process.returncode}), restarting...")

                # Restart the process based on its name
                if name == "data_collector":
                    start_data_collector(DEFAULT_CONFIG)
                elif name == "web_interface":
                    start_web_interface(DEFAULT_CONFIG)
                elif name == "connection_monitor":
                    start_connection_monitor(DEFAULT_CONFIG)

        # Add overall status
        if all_services_ok:
            status_message += "\n全サービスが正常に稼働しています。\n"
        else:
            status_message += "\n一部のサービスに問題があります。再起動を試みています。\n"

        status_message += "=============================\n"

        # Print status to console
        print(status_message)

        # Check every 10 seconds
        time.sleep(10)

def main():
    """Main function to start all services."""
    parser = argparse.ArgumentParser(description="Raspberry Pi 5 Unified Startup Script for Solo Version 4.0")
    parser.add_argument("--data-dir", type=str, default=DEFAULT_CONFIG["data_dir"],
                        help=f"Directory to store data (default: {DEFAULT_CONFIG['data_dir']})")
    parser.add_argument("--web-port", type=int, default=DEFAULT_CONFIG["web_port"],
                        help=f"Port for web interface (default: {DEFAULT_CONFIG['web_port']})")
    parser.add_argument("--api-port", type=int, default=DEFAULT_CONFIG["api_port"],
                        help=f"Port for data API (default: {DEFAULT_CONFIG['api_port']})")
    parser.add_argument("--monitor-port", type=int, default=DEFAULT_CONFIG["monitor_port"],
                        help=f"Port for connection monitor API (default: {DEFAULT_CONFIG['monitor_port']})")
    parser.add_argument("--monitor-interval", type=int, default=DEFAULT_CONFIG["monitor_interval"],
                        help=f"Monitoring interval in seconds (default: {DEFAULT_CONFIG['monitor_interval']})")
    parser.add_argument("--interface", type=str, default=DEFAULT_CONFIG["interface"],
                        help=f"WiFi interface to monitor (default: {DEFAULT_CONFIG['interface']})")

    args = parser.parse_args()

    # Update configuration with command-line arguments
    config = DEFAULT_CONFIG.copy()
    config["data_dir"] = args.data_dir
    config["web_port"] = args.web_port
    config["api_port"] = args.api_port
    config["monitor_port"] = args.monitor_port
    config["monitor_interval"] = args.monitor_interval
    config["interface"] = args.interface

    # Check if running as root
    check_root()

    # Register signal handlers and cleanup function
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup)

    # Run access point setup
    if not run_ap_setup():
        logger.error("Failed to set up access point, exiting")
        sys.exit(1)

    # Start services
    if not start_data_collector(config):
        logger.error("Failed to start data collection service, exiting")
        sys.exit(1)

    if not start_web_interface(config):
        logger.error("Failed to start web interface, exiting")
        sys.exit(1)

    if not start_connection_monitor(config):
        logger.error("Failed to start connection monitor, exiting")
        sys.exit(1)

    logger.info("All services started successfully")
    print("\n===== Raspberry Pi 5 Environmental Monitor Ver4.62 =====")
    print("All services started successfully!")
    print(f"- Access Point: SSID={DEFAULT_CONFIG['ap_ssid']}, IP={DEFAULT_CONFIG['ap_ip']}")
    print(f"- Web Interface: http://{DEFAULT_CONFIG['ap_ip']}:{config['web_port']}")
    print(f"- Data API: http://{DEFAULT_CONFIG['ap_ip']}:{config['api_port']}")
    print(f"- Connection Monitor API: http://{DEFAULT_CONFIG['ap_ip']}:{config['monitor_port']}")
    print("- P2 and P3 data directories created and ready")
    print("====================================================\n")

    # Start process monitor in a separate thread
    monitor_thread = threading.Thread(target=monitor_processes)
    monitor_thread.daemon = True
    monitor_thread.start()

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        cleanup()
        sys.exit(0)

if __name__ == "__main__":
    main()

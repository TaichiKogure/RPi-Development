#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi Zero 2W Unified Startup Script for Solo Version 1.5
Version: 1.5.0-solo

This script starts all the necessary services for the Raspberry Pi Zero 2W (P1) in the solo version:
1. Access Point setup
2. Data Collection service (for P4, P5, and P6)
3. Web Interface (with support for P4, P5, and P6)
4. Connection Monitor (for P4, P5, and P6)

It's designed to be run at system startup to ensure all services are running.
It includes enhanced self-diagnostics and recovery mechanisms for error handling.

Usage:
    sudo ~/envmonitor-venv/bin/python3 start_p1_solo_v1.5.py

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
import datetime

# Try to import psutil, but handle the case when it's not installed
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil module not found. System resource monitoring will be disabled.")
    logging.warning("To enable system resource monitoring, install psutil: pip install psutil")

# Path to virtual environment Python interpreter
VENV_PYTHON = "/home/pi/envmonitor-venv/bin/python3"

# Configure logging
LOG_DIR = "/var/log"
LOG_FILE = os.path.join(LOG_DIR, "p1_startup_solo_v1.5.log")

os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Paths to service scripts
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AP_SETUP_SCRIPT = os.path.join(SCRIPT_DIR, "ap_setup", "P1_ap_setup_solo.py")
DATA_COLLECTOR_SCRIPT = os.path.join(SCRIPT_DIR, "data_collection", "P1_data_collector_solo_v1.2.py")
WEB_INTERFACE_SCRIPT = os.path.join(SCRIPT_DIR, "web_interface", "P1_app_simple_v1.2.py")
CONNECTION_MONITOR_SCRIPT = os.path.join(SCRIPT_DIR, "connection_monitor", "monitor_v1.2.py")

# Default configuration
DEFAULT_CONFIG = {
    "data_dir": "/var/lib(FromThonny)/raspap_solo/data",
    "rawdata_p4_dir": "RawData_P4",
    "rawdata_p5_dir": "RawData_P5",
    "rawdata_p6_dir": "RawData_P6",
    "web_port": 80,
    "api_port": 5001,
    "monitor_port": 5002,
    "monitor_interval": 30,  # Increased from 5 to 30 seconds for Zero 2W
    "interface": "wlan0",
    "ap_ssid": "RaspberryPi5_AP_Solo",
    "ap_ip": "192.168.0.1",
    "log_dir": LOG_DIR,
    "max_restart_attempts": 5,  # Maximum number of restart attempts before system reboot
    "restart_backoff_factor": 1.5,  # Backoff factor for restart attempts
    "initial_restart_delay": 5,  # Initial delay before first restart (seconds)
    "memory_threshold": 80,  # Memory usage threshold (percentage)
    "cpu_threshold": 80,  # CPU usage threshold (percentage)
    "system_check_interval": 60,  # System resource check interval (seconds)
    "process_monitor_interval": 30  # Process monitoring interval (seconds)
}

# Global variables to store process objects and their restart information
processes = {}
restart_attempts = {}
last_restart_time = {}

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

        # Add a small delay to allow the system to process the configuration
        time.sleep(2)

        logger.info("Enabling access point...")
        subprocess.run([VENV_PYTHON, AP_SETUP_SCRIPT, "--enable"], check=True)

        # Add a small delay to allow the access point to start
        time.sleep(5)

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
            "--api-port", str(config["api_port"])
        ]

        # Start the process
        process = subprocess.Popen(cmd)
        processes["data_collector"] = process
        restart_attempts["data_collector"] = 0
        last_restart_time["data_collector"] = time.time()

        logger.info(f"Data collection service started (PID: {process.pid})")

        # Ensure data directories exist
        os.makedirs(os.path.join(config["data_dir"], config["rawdata_p4_dir"]), exist_ok=True)
        os.makedirs(os.path.join(config["data_dir"], config["rawdata_p5_dir"]), exist_ok=True)
        os.makedirs(os.path.join(config["data_dir"], config["rawdata_p6_dir"]), exist_ok=True)
        logger.info(f"Ensured data directories exist for P4, P5, and P6")

        # Add a small delay to allow the service to initialize
        time.sleep(2)

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

        # Set environment variables
        env = os.environ.copy()
        # Add the parent directory of p1_software_Zero to PYTHONPATH
        parent_dir = os.path.dirname(SCRIPT_DIR)
        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = f"{parent_dir}{os.pathsep}{env['PYTHONPATH']}"
        else:
            env["PYTHONPATH"] = parent_dir
        logger.info(f"Setting PYTHONPATH to include: {parent_dir}")

        # Start the process with the modified environment
        process = subprocess.Popen(cmd, env=env)
        processes["web_interface"] = process
        restart_attempts["web_interface"] = 0
        last_restart_time["web_interface"] = time.time()

        logger.info(f"Web interface started on port {config['web_port']} (PID: {process.pid})")

        # Add a small delay to allow the service to initialize
        time.sleep(2)

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
        restart_attempts["connection_monitor"] = 0
        last_restart_time["connection_monitor"] = time.time()

        logger.info(f"Connection monitor started (PID: {process.pid})")

        # Add a small delay to allow the service to initialize
        time.sleep(2)

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

def check_system_resources():
    """Check system resources and log warnings if thresholds are exceeded."""
    if not PSUTIL_AVAILABLE:
        logger.debug("System resource monitoring is disabled because psutil is not installed")
        return None, None
    
    try:
        # Get memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        # Get CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # Log resource usage
        logger.info(f"System resources - Memory: {memory_percent:.1f}%, CPU: {cpu_percent:.1f}%")

        # Check if thresholds are exceeded
        if memory_percent > DEFAULT_CONFIG["memory_threshold"]:
            logger.warning(f"Memory usage is high: {memory_percent:.1f}% (threshold: {DEFAULT_CONFIG['memory_threshold']}%)")

        if cpu_percent > DEFAULT_CONFIG["cpu_threshold"]:
            logger.warning(f"CPU usage is high: {cpu_percent:.1f}% (threshold: {DEFAULT_CONFIG['cpu_threshold']}%)")

        return memory_percent, cpu_percent
    except Exception as e:
        logger.error(f"Error checking system resources: {e}")
        return None, None

def should_reboot_system(name):
    """Determine if the system should be rebooted based on restart attempts."""
    if restart_attempts[name] >= DEFAULT_CONFIG["max_restart_attempts"]:
        logger.critical(f"{name} has failed {restart_attempts[name]} times, triggering system reboot")
        return True
    return False

def restart_process(name, config):
    """Restart a process with exponential backoff."""
    # Calculate delay based on restart attempts
    delay = DEFAULT_CONFIG["initial_restart_delay"] * (DEFAULT_CONFIG["restart_backoff_factor"] ** restart_attempts[name])
    restart_attempts[name] += 1
    
    logger.warning(f"Restarting {name} (attempt {restart_attempts[name]}) after {delay:.1f} seconds delay...")
    
    # Wait before restarting
    time.sleep(delay)
    
    # Check if we should reboot the system instead
    if should_reboot_system(name):
        logger.critical(f"Too many restart attempts for {name}, rebooting system...")
        reboot_system()
        return
    
    # Restart the process based on its name
    if name == "data_collector":
        start_data_collector(config)
    elif name == "web_interface":
        start_web_interface(config)
    elif name == "connection_monitor":
        start_connection_monitor(config)
    
    # Update last restart time
    last_restart_time[name] = time.time()

def reboot_system():
    """Reboot the system."""
    logger.critical("Rebooting system due to persistent errors...")
    try:
        # Clean up before reboot
        cleanup()
        # Reboot the system
        subprocess.run(["sudo", "reboot"], check=True)
    except Exception as e:
        logger.error(f"Failed to reboot system: {e}")

def monitor_processes():
    """Monitor running processes and restart them if they crash."""
    while True:
        status_message = f"\n===== P1 Services Status (Ver 1.5) - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =====\n"
        all_services_ok = True
        
        # Check system resources if psutil is available
        memory_percent, cpu_percent = check_system_resources()
        if memory_percent is not None and cpu_percent is not None:
            status_message += f"System Resources - Memory: {memory_percent:.1f}%, CPU: {cpu_percent:.1f}%\n"
        else:
            status_message += "System resource monitoring disabled (psutil not installed)\n"
        
        for name, process in list(processes.items()):
            if process.poll() is None:  # Process is running
                status = "✓ 正常稼働中"
                status_message += f"{name}: {status} (PID: {process.pid})\n"
            else:  # Process has terminated
                status = "✗ 停止中"
                status_message += f"{name}: {status} (終了コード: {process.returncode})\n"
                all_services_ok = False
                
                logger.warning(f"{name} has terminated unexpectedly (return code: {process.returncode})")
                
                # Check if enough time has passed since the last restart
                current_time = time.time()
                if current_time - last_restart_time[name] > 60:  # At least 60 seconds between restarts
                    restart_process(name, DEFAULT_CONFIG)
                else:
                    logger.warning(f"Skipping immediate restart of {name} as it was recently restarted")
        
        # Add overall status
        if all_services_ok:
            status_message += "\n全サービスが正常に稼働しています。\n"
        else:
            status_message += "\n一部のサービスに問題があります。再起動を試みています。\n"
        
        status_message += "=============================\n"
        
        # Print status to console
        print(status_message)
        
        # Check every process_monitor_interval seconds
        time.sleep(DEFAULT_CONFIG["process_monitor_interval"])

def create_systemd_service():
    """Create a systemd service file for auto-starting on boot."""
    logger.info("Creating systemd service file for auto-starting on boot...")
    
    service_content = f"""[Unit]
Description=Raspberry Pi Zero 2W Environmental Monitor
After=network.target

[Service]
ExecStart={VENV_PYTHON} {os.path.abspath(__file__)}
WorkingDirectory={os.path.dirname(os.path.abspath(__file__))}
StandardOutput=inherit
StandardError=inherit
Restart=always
User=root

[Install]
WantedBy=multi-user.target
"""
    
    service_path = "/etc/systemd/system/p1-environmental-monitor.service"
    
    try:
        with open(service_path, 'w') as f:
            f.write(service_content)
        
        logger.info(f"Created systemd service file at {service_path}")
        
        # Enable and start the service
        subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
        subprocess.run(["sudo", "systemctl", "enable", "p1-environmental-monitor.service"], check=True)
        
        logger.info("Systemd service enabled for auto-starting on boot")
        return True
    except Exception as e:
        logger.error(f"Failed to create systemd service file: {e}")
        return False

def main():
    """Main function to start all services."""
    parser = argparse.ArgumentParser(description="Raspberry Pi Zero 2W Unified Startup Script for Solo Version 1.5")
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
    parser.add_argument("--create-service", action="store_true",
                        help="Create systemd service for auto-starting on boot")

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

    # Create systemd service if requested
    if args.create_service:
        if create_systemd_service():
            logger.info("Systemd service created successfully")
        else:
            logger.error("Failed to create systemd service")
            sys.exit(1)
        return

    # Register signal handlers and cleanup function
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup)

    # Run access point setup
    if not run_ap_setup():
        logger.error("Failed to set up access point, exiting")
        sys.exit(1)

    # Start services with delays between them to reduce resource contention
    logger.info("Starting services with delays to reduce resource contention...")
    
    if not start_data_collector(config):
        logger.error("Failed to start data collection service, exiting")
        sys.exit(1)
    
    # Add delay between service starts
    time.sleep(5)
    
    if not start_web_interface(config):
        logger.error("Failed to start web interface, exiting")
        sys.exit(1)
    
    # Add delay between service starts
    time.sleep(5)
    
    if not start_connection_monitor(config):
        logger.error("Failed to start connection monitor, exiting")
        sys.exit(1)

    logger.info("All services started successfully")
    print("\n===== Raspberry Pi Zero 2W Environmental Monitor Ver1.5 =====")
    print("All services started successfully!")
    print(f"- Access Point: SSID={DEFAULT_CONFIG['ap_ssid']}, IP={DEFAULT_CONFIG['ap_ip']}")
    print(f"- Web Interface: http://{DEFAULT_CONFIG['ap_ip']}:{config['web_port']}")
    print(f"- Data API: http://{DEFAULT_CONFIG['ap_ip']}:{config['api_port']}")
    print(f"- Connection Monitor API: http://{DEFAULT_CONFIG['ap_ip']}:{config['monitor_port']}")
    print("- P4, P5, and P6 data directories created and ready")
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
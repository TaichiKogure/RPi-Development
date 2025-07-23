"""
Configuration Module for Connection Monitor

This module contains configuration settings and logging setup for the connection monitor.
"""

import logging
from pathlib import Path

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

# Default configuration
DEFAULT_CONFIG = {
    "monitor_interval": 5,  # seconds
    "api_port": 5002,
    "log_dir": "/var/lib/raspap_solo/logs",
    "devices": {
        "P4": {"ip": "192.168.0.101", "mac": None},
        "P5": {"ip": "192.168.0.102", "mac": None},
        "P6": {"ip": "192.168.0.103", "mac": None}
    },
    "interface": "wlan0",
    "ping_count": 3,
    "ping_timeout": 1,  # seconds
    "history_size": 100  # number of historical data points to keep
}

# Ensure log directory exists
def ensure_log_directory():
    """Ensure the log directory exists."""
    Path(DEFAULT_CONFIG["log_dir"]).mkdir(parents=True, exist_ok=True)
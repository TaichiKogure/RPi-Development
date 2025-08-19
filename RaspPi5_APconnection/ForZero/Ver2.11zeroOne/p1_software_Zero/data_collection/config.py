"""
Configuration Module for Data Collection

This module contains configuration settings for the data collection system.
"""

import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "listen_port": 5000,
    "data_dir": "/var/lib(FromThonny)/raspap_solo/data",
    "rawdata_p1_dir": "RawData_P1",
    "rawdata_p2_dir": "RawData_P2",
    "rawdata_p3_dir": "RawData_P3",
    "rawdata_p4_dir": "RawData_P4",
    "rawdata_p5_dir": "RawData_P5",
    "rawdata_p6_dir": "RawData_P6",
    "api_port": 5001,
    "max_file_size_mb": 10,
    "rotation_interval_days": 7,
    "device_timeout_seconds": 120
}

# WiFi monitor configuration
MONITOR_CONFIG = {
    "devices": {
        "P2": {
            "ip": None,
            "mac": None,
            "channel": 6
        },
        "P3": {
            "ip": None,
            "mac": None,
            "channel": 6
        },
        "P4": {
            "ip": None,
            "mac": None,
            "channel": 6
        },
        "P5": {
            "ip": None,
            "mac": None,
            "channel": 6
        },
        "P6": {
            "ip": None,
            "mac": None,
            "channel": 6
        }
    },
    "update_interval": 5,
    "ping_count": 3,
    "ping_timeout": 1
}

def ensure_data_directories(config=None):
    """Ensure that the data directories exist."""
    config = config or DEFAULT_CONFIG.copy()
    
    # Ensure data directories exist
    os.makedirs(config["data_dir"], exist_ok=True)
    os.makedirs(os.path.join(config["data_dir"], config["rawdata_p1_dir"]), exist_ok=True)
    os.makedirs(os.path.join(config["data_dir"], config["rawdata_p2_dir"]), exist_ok=True)
    os.makedirs(os.path.join(config["data_dir"], config["rawdata_p3_dir"]), exist_ok=True)
    os.makedirs(os.path.join(config["data_dir"], config["rawdata_p4_dir"]), exist_ok=True)
    os.makedirs(os.path.join(config["data_dir"], config["rawdata_p5_dir"]), exist_ok=True)
    os.makedirs(os.path.join(config["data_dir"], config["rawdata_p6_dir"]), exist_ok=True)
    
    logger.info("Data directories created or verified")
    return config
"""
Configuration Module for Web Interface

This module contains configuration settings for the web interface.
"""

import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "web_port": 80,
    "data_dir": "/var/lib/raspap_solo/data",
    "rawdata_p2_dir": "RawData_P2",
    "rawdata_p3_dir": "RawData_P3",
    "rawdata_p4_dir": "RawData_P4",
    "rawdata_p5_dir": "RawData_P5",
    "rawdata_p6_dir": "RawData_P6",
    "api_url": "http://localhost:5001",
    "monitor_api_url": "http://localhost:5002",
    "refresh_interval": 10,  # seconds
    "graph_points": 100,  # number of data points to show in graphs
    "debug_mode": False
}

def ensure_data_directories(config=None):
    """Ensure that the data directories exist."""
    config = config or DEFAULT_CONFIG.copy()
    
    # Ensure data directories exist
    os.makedirs(config["data_dir"], exist_ok=True)
    os.makedirs(os.path.join(config["data_dir"], config["rawdata_p2_dir"]), exist_ok=True)
    os.makedirs(os.path.join(config["data_dir"], config["rawdata_p3_dir"]), exist_ok=True)
    os.makedirs(os.path.join(config["data_dir"], config["rawdata_p4_dir"]), exist_ok=True)
    os.makedirs(os.path.join(config["data_dir"], config["rawdata_p5_dir"]), exist_ok=True)
    os.makedirs(os.path.join(config["data_dir"], config["rawdata_p6_dir"]), exist_ok=True)
    
    logger.info("Data directories created or verified")
    return config
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

# Add the parent directory to the Python path so we can import from connection_monitor
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import refactored modules
from connection_monitor.config import DEFAULT_CONFIG, ensure_log_directory
from connection_monitor.monitor import WiFiMonitor
from connection_monitor.utils.console import print_connection_status

# Configure logging
logger = logging.getLogger(__name__)

# For backwards compatibility
def main():
    """Main function to parse arguments and start the WiFi monitor."""
    from connection_monitor.main import main as refactored_main
    refactored_main()

if __name__ == "__main__":
    main()

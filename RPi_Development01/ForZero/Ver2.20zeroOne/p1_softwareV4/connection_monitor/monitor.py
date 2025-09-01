"""
WiFi Monitor Module

This module contains the core WiFiMonitor class for monitoring WiFi connections.
"""

import os
import time
import threading
import logging
import datetime

from .config import DEFAULT_CONFIG
from .measurements.signal_strength import get_signal_strength
from .measurements.noise_level import get_noise_level
from .measurements.ping import measure_ping, check_device_online
from .api.server import create_api_app, run_api_server

logger = logging.getLogger(__name__)

class WiFiMonitor:
    """Class to monitor WiFi connection quality with configured devices (P2–P4)."""

    def __init__(self, config=None):
        """
        Initialize the WiFi monitor with the given configuration.
        
        Args:
            config (dict, optional): Configuration dictionary. Defaults to None.
        """
        self.config = config or DEFAULT_CONFIG.copy()
        # Initialize per-device connection data dynamically from config
        self.connection_data = {dev: {"history": []} for dev in self.config.get("devices", {}).keys()}
        self.lock = threading.Lock()
        self.running = False

        # Ensure log directory exists
        os.makedirs(self.config["log_dir"], exist_ok=True)

        # Initialize API server
        self.api_app = create_api_app(self.connection_data, self.lock)
        self.api_thread = None
        self.monitor_thread = None

    def _monitor_connections(self):
        """Monitor connections to all devices."""
        while self.running:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            noise_level = get_noise_level(self.config["interface"])

            for device_id in self.config["devices"]:
                # Check if device is online
                device_info = self.config["devices"][device_id]
                online = check_device_online(device_id, device_info)

                if online:
                    # Get signal strength and ping time
                    signal_strength = get_signal_strength(device_id, device_info, self.config["interface"])
                    ping_time = measure_ping(
                        device_id, 
                        device_info, 
                        self.config["ping_count"], 
                        self.config["ping_timeout"]
                    )

                    # Calculate signal-to-noise ratio if both values are available
                    snr = None
                    if signal_strength is not None and noise_level is not None:
                        snr = signal_strength - noise_level

                    # Create data point
                    data_point = {
                        "timestamp": timestamp,
                        "online": True,
                        "signal_strength": signal_strength,
                        "noise_level": noise_level,
                        "snr": snr,
                        "ping_time": ping_time
                    }
                else:
                    # Device is offline
                    data_point = {
                        "timestamp": timestamp,
                        "online": False,
                        "signal_strength": None,
                        "noise_level": noise_level,
                        "snr": None,
                        "ping_time": None
                    }

                # Update connection data
                with self.lock:
                    self.connection_data[device_id]["history"].append(data_point)

                    # Limit history size
                    if len(self.connection_data[device_id]["history"]) > self.config["history_size"]:
                        self.connection_data[device_id]["history"] = self.connection_data[device_id]["history"][-self.config["history_size"]:]

                    # Update latest data
                    self.connection_data[device_id]["latest"] = data_point

                logger.info(f"Connection data for {device_id}: {data_point}")

            # Sleep until next monitoring interval
            time.sleep(self.config["monitor_interval"])

    def start(self):
        """Start the WiFi monitor."""
        if not self.running:
            self.running = True

            # Start monitoring thread
            self.monitor_thread = threading.Thread(target=self._monitor_connections)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()

            # Start API server
            self.api_thread = threading.Thread(
                target=run_api_server,
                args=(self.api_app, self.config["api_port"])
            )
            self.api_thread.daemon = True
            self.api_thread.start()

            logger.info("WiFi monitor started")

    def update_device_ip(self, device_id, new_ip):
        """
        Update the IP address for a device and force MAC re-resolution.

        Args:
            device_id (str): The device ID (e.g., P2, P3, P4)
            new_ip (str): The new IP address for the device
        """
        if device_id not in self.config['devices']:
            logger.warning(f"Unknown device ID {device_id} - cannot update IP")
            return

        old_ip = self.config['devices'][device_id]['ip']
        if old_ip != new_ip:
            logger.info(f"Updating {device_id} IP: {old_ip} -> {new_ip}")
            self.config['devices'][device_id]['ip'] = new_ip
            self.config['devices'][device_id]['mac'] = None  # force MAC re-resolution

    def stop(self):
        """Stop the WiFi monitor."""
        if self.running:
            self.running = False
            logger.info("WiFi monitor stopped")
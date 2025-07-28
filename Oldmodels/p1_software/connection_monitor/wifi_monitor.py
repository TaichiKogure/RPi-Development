#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi 5 WiFi Connection Monitor
Version: 1.0.0

This module monitors the WiFi connection quality between the Raspberry Pi 5 (P1)
and the Pico 2W devices (P2, P3). It measures signal strength, ping times,
and noise levels to help optimize device placement.

Features:
- Real-time monitoring of WiFi signal strength
- Ping time measurement for connection latency
- Noise level detection
- Configurable monitoring interval
- Data logging for trend analysis
- Web interface integration
- Command-line interface for direct use

Requirements:
- Python 3.7+
- iwconfig/iw tools for WiFi signal measurement
- ping utility for latency measurement

Usage:
    python3 wifi_monitor.py [--interval SECONDS] [--devices DEVICE_LIST]
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/wifi_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "monitor_interval": 5,  # seconds
    "api_port": 5002,
    "log_dir": "/var/lib(FromThonny)/raspap/logs",
    "devices": {
        "P2": {"ip": "192.168.900.101", "mac": None},
        "P3": {"ip": "192.168.900.102", "mac": None}
    },
    "interface": "wlan0",
    "ping_count": 3,
    "ping_timeout": 1,  # seconds
    "history_size": 100  # number of historical data points to keep
}

class WiFiMonitor:
    """Class to monitor WiFi connection quality with P2 and P3 devices."""
    
    def __init__(self, config=None):
        """Initialize the WiFi monitor with the given configuration."""
        self.config = config or DEFAULT_CONFIG.copy()
        self.connection_data = {
            "P2": {"history": []},
            "P3": {"history": []}
        }
        self.lock = threading.Lock()
        self.running = False
        
        # Ensure log directory exists
        os.makedirs(self.config["log_dir"], exist_ok=True)
        
        # Initialize API server
        self.api_app = Flask(__name__)
        self._setup_api_routes()
        self.api_thread = None
    
    def _get_signal_strength(self, device_id):
        """Get the WiFi signal strength for the specified device."""
        device_info = self.config["devices"].get(device_id)
        if not device_info or not device_info.get("ip"):
            logger.warning(f"No IP address configured for {device_id}")
            return None
        
        # First, try to get the MAC address if we don't have it
        if not device_info.get("mac"):
            try:
                # Ping the device to ensure it's in the ARP table
                subprocess.run(
                    ["ping", "-c", "1", "-W", "1", device_info["ip"]],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                # Get the MAC address from the ARP table
                arp_output = subprocess.check_output(
                    ["arp", "-n", device_info["ip"]],
                    universal_newlines=True
                )
                
                # Extract MAC address using regex
                mac_match = re.search(r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})", arp_output)
                if mac_match:
                    device_info["mac"] = mac_match.group(0)
                    logger.info(f"Found MAC address for {device_id}: {device_info['mac']}")
                else:
                    logger.warning(f"Could not find MAC address for {device_id}")
                    return None
            except subprocess.SubprocessError as e:
                logger.error(f"Error getting MAC address for {device_id}: {e}")
                return None
        
        try:
            # Get signal strength using iw
            iw_output = subprocess.check_output(
                ["iw", "dev", self.config["interface"], "station", "dump"],
                universal_newlines=True
            )
            
            # Find the section for our device's MAC address
            mac_section = None
            sections = iw_output.split("Station")
            for section in sections:
                if device_info["mac"].lower() in section.lower():
                    mac_section = section
                    break
            
            if not mac_section:
                logger.warning(f"Device {device_id} ({device_info['mac']}) not found in iw output")
                return None
            
            # Extract signal strength
            signal_match = re.search(r"signal:\s*([-\d]+)\s*dBm", mac_section)
            if signal_match:
                signal_strength = int(signal_match.group(1))
                logger.debug(f"Signal strength for {device_id}: {signal_strength} dBm")
                return signal_strength
            else:
                logger.warning(f"Could not find signal strength for {device_id}")
                return None
        except subprocess.SubprocessError as e:
            logger.error(f"Error getting signal strength for {device_id}: {e}")
            return None
    
    def _get_noise_level(self):
        """Get the WiFi noise level on the current channel."""
        try:
            # Get the current channel
            iw_output = subprocess.check_output(
                ["iw", "dev", self.config["interface"], "info"],
                universal_newlines=True
            )
            
            channel_match = re.search(r"channel\s*(\d+)", iw_output)
            if not channel_match:
                logger.warning("Could not determine current WiFi channel")
                return None
            
            channel = channel_match.group(1)
            
            # Get noise level using iw survey
            survey_output = subprocess.check_output(
                ["iw", "dev", self.config["interface"], "survey", "dump"],
                universal_newlines=True
            )
            
            # Find the section for the current frequency
            noise_level = None
            in_current_channel = False
            for line in survey_output.splitlines():
                if f"frequency:" in line and channel in line:
                    in_current_channel = True
                elif "frequency:" in line and in_current_channel:
                    break
                elif in_current_channel and "noise:" in line:
                    noise_match = re.search(r"noise:\s*([-\d]+)\s*dBm", line)
                    if noise_match:
                        noise_level = int(noise_match.group(1))
                        break
            
            if noise_level is not None:
                logger.debug(f"Noise level on channel {channel}: {noise_level} dBm")
                return noise_level
            else:
                logger.warning(f"Could not find noise level for channel {channel}")
                return None
        except subprocess.SubprocessError as e:
            logger.error(f"Error getting noise level: {e}")
            return None
    
    def _measure_ping(self, device_id):
        """Measure ping time to the specified device."""
        device_info = self.config["devices"].get(device_id)
        if not device_info or not device_info.get("ip"):
            logger.warning(f"No IP address configured for {device_id}")
            return None
        
        try:
            # Measure ping time
            ping_output = subprocess.check_output(
                [
                    "ping", "-c", str(self.config["ping_count"]),
                    "-W", str(self.config["ping_timeout"]),
                    device_info["ip"]
                ],
                universal_newlines=True
            )
            
            # Extract average ping time
            avg_match = re.search(r"min/avg/max/mdev = [\d.]+/([\d.]+)/[\d.]+/[\d.]+", ping_output)
            if avg_match:
                avg_ping = float(avg_match.group(1))
                logger.debug(f"Average ping time to {device_id}: {avg_ping} ms")
                return avg_ping
            else:
                logger.warning(f"Could not extract ping time for {device_id}")
                return None
        except subprocess.SubprocessError as e:
            logger.error(f"Error pinging {device_id}: {e}")
            return None
    
    def _check_device_online(self, device_id):
        """Check if the device is online."""
        device_info = self.config["devices"].get(device_id)
        if not device_info or not device_info.get("ip"):
            return False
        
        try:
            # Try to ping the device once
            result = subprocess.run(
                [
                    "ping", "-c", "1", "-W", "1", device_info["ip"]
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            return result.returncode == 0
        except subprocess.SubprocessError:
            return False
    
    def _monitor_connections(self):
        """Monitor connections to all devices."""
        while self.running:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            noise_level = self._get_noise_level()
            
            for device_id in self.config["devices"]:
                # Check if device is online
                online = self._check_device_online(device_id)
                
                if online:
                    # Get signal strength and ping time
                    signal_strength = self._get_signal_strength(device_id)
                    ping_time = self._measure_ping(device_id)
                    
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
    
    def _setup_api_routes(self):
        """Set up API routes for data access."""
        app = self.api_app
        
        @app.route('/api/connection/latest', methods=['GET'])
        def get_latest_data():
            """Get the latest connection data for all devices."""
            with self.lock:
                latest_data = {
                    device_id: data.get("latest", {})
                    for device_id, data in self.connection_data.items()
                }
                return jsonify(latest_data)
        
        @app.route('/api/connection/device/<device_id>', methods=['GET'])
        def get_device_data(device_id):
            """Get the latest connection data for a specific device."""
            if device_id not in self.config["devices"]:
                return jsonify({"error": "Invalid device ID"}), 400
            
            with self.lock:
                if "latest" in self.connection_data[device_id]:
                    return jsonify(self.connection_data[device_id]["latest"])
                else:
                    return jsonify({"error": "No data available for this device"}), 404
        
        @app.route('/api/connection/history/<device_id>', methods=['GET'])
        def get_device_history(device_id):
            """Get the connection history for a specific device."""
            if device_id not in self.config["devices"]:
                return jsonify({"error": "Invalid device ID"}), 400
            
            # Get optional limit parameter
            limit = request.args.get('limit', default=None, type=int)
            
            with self.lock:
                history = self.connection_data[device_id]["history"]
                
                if limit and limit > 0:
                    history = history[-limit:]
                
                return jsonify(history)
    
    def _run_api(self):
        """Run the API server."""
        self.api_app.run(host='0.0.0.0', port=self.config["api_port"])
    
    def start(self):
        """Start the WiFi monitor."""
        if not self.running:
            self.running = True
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(target=self._monitor_connections)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            
            # Start API server
            self.api_thread = threading.Thread(target=self._run_api)
            self.api_thread.daemon = True
            self.api_thread.start()
            
            logger.info("WiFi monitor started")
    
    def stop(self):
        """Stop the WiFi monitor."""
        if self.running:
            self.running = False
            logger.info("WiFi monitor stopped")

def print_connection_status(monitor):
    """Print the current connection status to the console."""
    with monitor.lock:
        latest_data = {
            device_id: data.get("latest", {})
            for device_id, data in monitor.connection_data.items()
        }
    
    print("\n" + "=" * 60)
    print(f"WiFi Connection Status - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    for device_id, data in latest_data.items():
        print(f"\nDevice: {device_id}")
        print("-" * 30)
        
        if not data:
            print("No data available")
            continue
        
        status = "ONLINE" if data.get("online", False) else "OFFLINE"
        print(f"Status: {status}")
        
        if data.get("online", False):
            signal_str = f"{data.get('signal_strength')} dBm" if data.get('signal_strength') is not None else "N/A"
            print(f"Signal Strength: {signal_str}")
            
            noise_str = f"{data.get('noise_level')} dBm" if data.get('noise_level') is not None else "N/A"
            print(f"Noise Level: {noise_str}")
            
            snr_str = f"{data.get('snr')} dB" if data.get('snr') is not None else "N/A"
            print(f"Signal-to-Noise Ratio: {snr_str}")
            
            ping_str = f"{data.get('ping_time'):.2f} ms" if data.get('ping_time') is not None else "N/A"
            print(f"Ping Time: {ping_str}")
            
            # Add signal quality assessment
            if data.get('signal_strength') is not None:
                signal = data.get('signal_strength')
                if signal >= -50:
                    quality = "Excellent"
                elif signal >= -60:
                    quality = "Very Good"
                elif signal >= -70:
                    quality = "Good"
                elif signal >= -80:
                    quality = "Fair"
                else:
                    quality = "Poor"
                print(f"Signal Quality: {quality}")
    
    print("\n" + "=" * 60)
    print("Press Ctrl+C to exit")

def main():
    """Main function to parse arguments and start the WiFi monitor."""
    parser = argparse.ArgumentParser(description="Raspberry Pi 5 WiFi Connection Monitor")
    parser.add_argument("--interval", type=int, default=DEFAULT_CONFIG["monitor_interval"],
                        help=f"Monitoring interval in seconds (default: {DEFAULT_CONFIG['monitor_interval']})")
    parser.add_argument("--devices", type=str, default="P2,P3",
                        help="Comma-separated list of devices to monitor (default: P2,P3)")
    parser.add_argument("--interface", type=str, default=DEFAULT_CONFIG["interface"],
                        help=f"WiFi interface to monitor (default: {DEFAULT_CONFIG['interface']})")
    parser.add_argument("--console", action="store_true",
                        help="Display results in console instead of running as a service")
    
    args = parser.parse_args()
    
    # Update configuration with command-line arguments
    config = DEFAULT_CONFIG.copy()
    config["monitor_interval"] = args.interval
    config["interface"] = args.interface
    
    # Filter devices based on command-line argument
    device_list = args.devices.split(",")
    config["devices"] = {
        device_id: config["devices"][device_id]
        for device_id in config["devices"]
        if device_id in device_list
    }
    
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
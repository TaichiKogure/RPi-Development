"""
WiFi Monitor Module
Version: 1.2

This module contains the core WiFiMonitor class for monitoring WiFi connections.
This version is optimized for Raspberry Pi Zero 2W with reduced resource usage.
"""

import os
import time
import threading
import logging
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/wifi_monitor_solo.log')
    ]
)
logger = logging.getLogger(__name__)

# Default configuration with optimized settings
DEFAULT_CONFIG = {
    "interface": "wlan0",
    "devices": {
        "P4": {
            "ip": "192.168.0.50",
            "mac": None
        },
        "P5": {
            "ip": "192.168.0.51",
            "mac": None
        },
        "P6": {
            "ip": "192.168.0.52",
            "mac": None
        }
    },
    "ping_count": 3,  # Reduced from 5 to 3
    "ping_timeout": 1,  # Reduced from 2 to 1 second
    "monitor_interval": 30,  # Increased from 5 to 30 seconds
    "history_size": 60,  # Reduced from 100 to 60 data points
    "api_port": 5001,
    "log_dir": "/var/log",
    "log_frequency": 5,  # Log only every 5th measurement
    "rest_time": 0.1,  # Rest time between operations (100ms)
    "debug_mode": False
}

def ensure_log_directory(config):
    """Ensure the log directory exists."""
    os.makedirs(config["log_dir"], exist_ok=True)

class WiFiMonitor:
    """Class to monitor WiFi connection quality with P4, P5, and P6 devices."""

    def __init__(self, config=None):
        """
        Initialize the WiFi monitor with the given configuration.
        
        Args:
            config (dict, optional): Configuration dictionary. Defaults to None.
        """
        self.config = config or DEFAULT_CONFIG.copy()
        self.connection_data = {
            "P4": {"history": []},
            "P5": {"history": []},
            "P6": {"history": []}
        }
        self.lock = threading.Lock()
        self.running = False
        self.log_counter = {}  # Counter for logging frequency

        # Ensure log directory exists
        ensure_log_directory(self.config)

        # Initialize API server
        try:
            from .api.server import create_api_app, run_api_server
            self.api_app = create_api_app(self.connection_data, self.lock)
            self.api_thread = None
        except ImportError:
            logger.warning("Flask not installed. API server will not be available.")
            self.api_app = None
        
        self.monitor_thread = None

    def _monitor_connections(self):
        """Monitor connections to all devices."""
        from .measurements.signal_strength import get_signal_strength
        from .measurements.noise_level import get_noise_level
        from .measurements.ping import measure_ping, check_device_online
        
        while self.running:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Add rest time before getting noise level
            time.sleep(self.config["rest_time"])
            
            # Get noise level once for all devices
            noise_level = get_noise_level(self.config["interface"])
            
            for device_id in self.config["devices"]:
                # Initialize log counter for this device if not exists
                if device_id not in self.log_counter:
                    self.log_counter[device_id] = 0
                
                # Check if device is online
                device_info = self.config["devices"][device_id]
                
                # Add rest time before checking if device is online
                time.sleep(self.config["rest_time"])
                
                online = check_device_online(device_id, device_info)

                if online:
                    # Add rest time before getting signal strength
                    time.sleep(self.config["rest_time"])
                    
                    # Get signal strength
                    signal_strength = get_signal_strength(device_id, device_info, self.config["interface"])
                    
                    # Add rest time before measuring ping
                    time.sleep(self.config["rest_time"])
                    
                    # Measure ping
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

                # Increment log counter for this device
                self.log_counter[device_id] += 1
                
                # Log only every nth measurement to reduce logging frequency
                if self.log_counter[device_id] % self.config["log_frequency"] == 0:
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
            if self.api_app is not None:
                try:
                    from .api.server import run_api_server
                    self.api_thread = threading.Thread(
                        target=run_api_server,
                        args=(self.api_app, self.config["api_port"])
                    )
                    self.api_thread.daemon = True
                    self.api_thread.start()
                except ImportError:
                    logger.warning("Failed to start API server. Flask may not be installed.")

            logger.info("WiFi monitor started")

    def update_device_ip(self, device_id, new_ip):
        """
        Update the IP address for a device and force MAC re-resolution.

        Args:
            device_id (str): The device ID (P4, P5, or P6)
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

def main():
    """Main function to parse arguments and start the WiFi monitor."""
    import argparse
    
    parser = argparse.ArgumentParser(description='WiFi Connection Monitor')
    parser.add_argument('--interface', type=str, help='WiFi interface to monitor')
    parser.add_argument('--interval', type=int, help='Monitoring interval in seconds')
    parser.add_argument('--port', type=int, help='API server port')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    config = DEFAULT_CONFIG.copy()
    
    if args.interface:
        config["interface"] = args.interface
    
    if args.interval:
        config["monitor_interval"] = args.interval
    
    if args.port:
        config["api_port"] = args.port
    
    if args.debug:
        config["debug_mode"] = True
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and start the WiFi monitor
    monitor = WiFiMonitor(config)
    
    try:
        monitor.start()
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Stopping...")
    finally:
        monitor.stop()

if __name__ == "__main__":
    # Add a small delay to ensure other services are ready
    time.sleep(2)
    
    try:
        from .api.server import create_api_app, run_api_server
        from .measurements.signal_strength import get_signal_strength
        from .measurements.noise_level import get_noise_level
        from .measurements.ping import measure_ping, check_device_online
    except ImportError:
        logger.warning("Failed to import required modules. Some functionality may be limited.")
    
    main()
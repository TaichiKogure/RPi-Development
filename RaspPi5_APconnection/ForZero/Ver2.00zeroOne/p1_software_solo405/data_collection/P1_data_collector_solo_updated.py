#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi 5 Environmental Data Collection Module for Solo Version 2.0
Version: 2.0.0-solo

This module receives environmental data from P2, P3, P4, P5, and P6 Pico devices with BME680 sensors via WiFi,
processes it, and stores it in CSV format for later analysis and visualization.

Features:
- Listens for incoming data from P2, P3, P4, P5, and P6 devices
- Validates and processes received data (BME680 sensors only)
- Calculates absolute humidity from temperature and humidity data
- Stores data in separate directories (RawData_P2, RawData_P3, RawData_P4, RawData_P5, and RawData_P6)
- Handles connection errors and data validation
- Provides an API for other modules to access the collected data

Requirements:
- Python 3.7+
- Flask for the API server
- pandas for data manipulation

Usage:
    python3 P1_data_collector_solo.py [--port PORT] [--data-dir DIR]
"""

import os
import sys
import argparse
import logging
import threading
import datetime
import json
import csv
import socket
import time
from collections import deque
from functools import wraps
from flask import Flask, jsonify, request, send_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/data_collector_solo.log')
    ]
)
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "data_dir": "/var/lib/raspap_solo/data",
    "rawdata_p2_dir": "RawData_P2",
    "rawdata_p3_dir": "RawData_P3",
    "rawdata_p4_dir": "RawData_P4",
    "rawdata_p5_dir": "RawData_P5",
    "rawdata_p6_dir": "RawData_P6",
    "listen_port": 5000,
    "api_port": 5000,
    "file_rotation_interval": 86400,  # 24 hours in seconds
    "cleanup_interval": 3600,  # 1 hour in seconds
    "retention_days": 30,
    "log_level": "INFO",
    "debug_mode": False,
    "rest_time": 0.1,  # Added rest time between operations (100ms)
    "log_frequency": 5,  # Log only every 5th data point
    "rate_limit_window": 60,  # Rate limit window in seconds
    "rate_limit_count": 10,  # Maximum number of requests per window
}

# Rate limiting implementation
class RateLimiter:
    """Simple rate limiter for API endpoints."""
    
    def __init__(self, window_size=60, max_requests=10):
        """
        Initialize the rate limiter.
        
        Args:
            window_size (int): The window size in seconds.
            max_requests (int): The maximum number of requests allowed in the window.
        """
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests = {}
        
    def is_allowed(self, client_ip):
        """
        Check if a request from the given client IP is allowed.
        
        Args:
            client_ip (str): The client IP address.
            
        Returns:
            bool: True if the request is allowed, False otherwise.
        """
        now = time.time()
        
        # Clean up old requests
        for ip in list(self.requests.keys()):
            self.requests[ip] = [timestamp for timestamp in self.requests[ip] if now - timestamp < self.window_size]
            if not self.requests[ip]:
                del self.requests[ip]
        
        # Check if client has exceeded rate limit
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        if len(self.requests[client_ip]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[client_ip].append(now)
        return True

# API rate limiting decorator
def rate_limit(limiter):
    """
    Decorator for rate limiting API endpoints.
    
    Args:
        limiter (RateLimiter): The rate limiter to use.
        
    Returns:
        function: The decorated function.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.remote_addr
            if not limiter.is_allowed(client_ip):
                return jsonify({"error": "Rate limit exceeded"}), 429
            return f(*args, **kwargs)
        return decorated_function
    return decorator

class DataCollector:
    """Class to collect and store environmental data from sensor nodes."""
    
    def __init__(self, config=None):
        """
        Initialize the data collector with the given configuration.
        
        Args:
            config (dict, optional): Configuration dictionary. Defaults to None.
        """
        self.config = config or DEFAULT_CONFIG.copy()
        self.lock = threading.Lock()
        self.last_data = {}
        self.csv_files = {}
        self.csv_writers = {}
        self.fixed_csv_files = {}
        self.fixed_csv_writers = {}
        self.running = False
        self.server_socket = None
        self.server_thread = None
        self.api_app = None
        self.api_thread = None
        self.cleanup_thread = None
        self.request_count = 0
        self.rate_limiter = RateLimiter(
            window_size=self.config["rate_limit_window"],
            max_requests=self.config["rate_limit_count"]
        )
        
        # Initialize CSV files
        self._init_csv_files()
    
    def _init_csv_files(self):
        """Initialize CSV files for data storage."""
        # Ensure data directories exist
        os.makedirs(self.config["data_dir"], exist_ok=True)
        
        for device_id in ["P2", "P3", "P4", "P5", "P6"]:
            # Determine the appropriate directory for each device
            device_dir_key = f"rawdata_{device_id.lower()}_dir"
            device_dir = self.config[device_dir_key]
            device_path = os.path.join(self.config["data_dir"], device_dir)
            
            # Create device directory if it doesn't exist
            os.makedirs(device_path, exist_ok=True)
            
            # Get today's date
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            
            # Create or open today's CSV file
            today_file = os.path.join(device_path, f"{device_id}_{today}.csv")
            file_exists = os.path.exists(today_file)
            
            self.csv_files[device_id] = open(today_file, 'a', newline='')
            self.csv_writers[device_id] = csv.writer(self.csv_files[device_id])
            
            # Write header if file is new
            if not file_exists:
                self.csv_writers[device_id].writerow([
                    "timestamp", "device_id", "temperature", "humidity", 
                    "pressure", "gas_resistance", "", "absolute_humidity"  # Empty column for CO2 (removed)
                ])
                self.csv_files[device_id].flush()
            
            # Create or open fixed CSV file
            fixed_file = os.path.join(device_path, f"{device_id}_fixed.csv")
            fixed_file_exists = os.path.exists(fixed_file)
            
            self.fixed_csv_files[device_id] = open(fixed_file, 'a', newline='')
            self.fixed_csv_writers[device_id] = csv.writer(self.fixed_csv_files[device_id])
            
            # Write header if fixed file is new
            if not fixed_file_exists:
                self.fixed_csv_writers[device_id].writerow([
                    "timestamp", "device_id", "temperature", "humidity", 
                    "pressure", "gas_resistance", "", "absolute_humidity"  # Empty column for CO2 (removed)
                ])
                self.fixed_csv_files[device_id].flush()
        
        logger.info("CSV files initialized")
    
    def _rotate_csv_files(self):
        """Rotate CSV files based on date."""
        with self.lock:
            # Close current files
            for device_id in self.csv_files:
                self.csv_files[device_id].close()
            
            # Re-initialize CSV files
            self._init_csv_files()
            
            logger.info("CSV files rotated")
    
    def _cleanup_old_files(self):
        """Clean up old CSV files based on retention policy."""
        try:
            # Calculate cutoff date
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=self.config["retention_days"])
            cutoff_str = cutoff_date.strftime("%Y-%m-%d")
            
            # Check each device directory
            for device_id in ["P2", "P3", "P4", "P5", "P6"]:
                device_dir_key = f"rawdata_{device_id.lower()}_dir"
                device_dir = self.config[device_dir_key]
                device_path = os.path.join(self.config["data_dir"], device_dir)
                
                # Skip if directory doesn't exist
                if not os.path.exists(device_path):
                    continue
                
                # Check each file in the directory
                for filename in os.listdir(device_path):
                    # Skip fixed files
                    if "fixed" in filename:
                        continue
                    
                    # Check if file is a date-based CSV
                    if filename.startswith(f"{device_id}_") and filename.endswith(".csv"):
                        try:
                            # Extract date from filename
                            file_date = filename.replace(f"{device_id}_", "").replace(".csv", "")
                            
                            # Delete if older than cutoff
                            if file_date < cutoff_str:
                                os.remove(os.path.join(device_path, filename))
                                logger.info(f"Deleted old file: {filename}")
                        except Exception as e:
                            logger.warning(f"Error processing file {filename}: {e}")
            
            logger.info("Cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def _calculate_absolute_humidity(self, temperature, humidity):
        """
        Calculate absolute humidity from temperature and relative humidity.
        
        Args:
            temperature (float): Temperature in Celsius
            humidity (float): Relative humidity as a percentage (0-100)
            
        Returns:
            float: Absolute humidity in g/m³, rounded to 2 decimal places
        """
        try:
            # Validate inputs
            if temperature is None or humidity is None:
                return None
            
            # Convert to float if they're strings
            if isinstance(temperature, str):
                temperature = float(temperature)
            if isinstance(humidity, str):
                humidity = float(humidity)
            
            # Calculate saturation vapor pressure (hPa)
            # Magnus formula
            svp = 6.1078 * 10 ** ((7.5 * temperature) / (237.3 + temperature))
            
            # Calculate vapor pressure
            vp = svp * humidity / 100.0
            
            # Calculate absolute humidity
            ah = 216.7 * vp / (273.15 + temperature)
            
            return round(ah, 2)
        except (ValueError, TypeError, ZeroDivisionError):
            logger.warning(f"Failed to calculate absolute humidity: temperature={temperature}, humidity={humidity}")
            return None
    
    def _validate_data(self, data):
        """
        Validate the received data.
        
        Args:
            data (dict): The data to validate.
            
        Returns:
            bool: True if the data is valid, False otherwise.
        """
        # Check if data is a dictionary
        if not isinstance(data, dict):
            logger.warning("Received data is not a dictionary")
            return False
        
        # Check if required fields are present
        required_fields = ["device_id", "timestamp"]
        for field in required_fields:
            if field not in data:
                logger.warning(f"Required field '{field}' missing in data")
                return False
        
        # Check if device_id is valid
        if data["device_id"] not in ["P2", "P3", "P4", "P5", "P6"]:
            logger.warning(f"Invalid device_id: {data['device_id']}")
            return False
        
        # Check if at least one sensor reading is present
        # Ver2.00zeroOne: Removed "co2" from sensor_fields as we're disabling CO2 sensor functionality
        sensor_fields = ["temperature", "humidity", "pressure", "gas_resistance"]  # "co2" removed
        if not any(field in data for field in sensor_fields):
            logger.warning("No sensor readings found in data")
            return False
        
        # Validate timestamp format
        try:
            # Try parsing as ISO format
            datetime.datetime.fromisoformat(data["timestamp"])
        except ValueError:
            try:
                # Try parsing as Unix timestamp
                datetime.datetime.fromtimestamp(float(data["timestamp"]))
            except ValueError:
                try:
                    # Try parsing as custom format
                    datetime.datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    logger.warning(f"Invalid timestamp format: {data['timestamp']}")
                    return False
        
        return True
    
    def _store_data(self, data):
        """
        Store the received data.
        
        Args:
            data (dict): The data to store.
            
        Returns:
            bool: True if the data was stored successfully, False otherwise.
        """
        try:
            device_id = data["device_id"]
            timestamp = data["timestamp"]
            
            # Calculate absolute humidity if temperature and humidity are present
            absolute_humidity = None
            if "temperature" in data and "humidity" in data:
                absolute_humidity = self._calculate_absolute_humidity(data["temperature"], data["humidity"])
            
            # Get device directory
            device_dir_key = f"rawdata_{device_id.lower()}_dir"
            device_dir = self.config[device_dir_key]
            device_path = os.path.join(self.config["data_dir"], device_dir)
            
            # Get today's date
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            
            # Append to today's CSV file
            today_file = os.path.join(device_path, f"{device_id}_{today}.csv")
            with open(today_file, 'a', newline='') as f:
                writer = csv.writer(f)
                # Ver2.00zeroOne: Commented out "co2" data as we're disabling CO2 sensor functionality
                row = [
                    timestamp,
                    device_id,
                    data.get("temperature", ""),
                    data.get("humidity", ""),
                    data.get("pressure", ""),
                    data.get("gas_resistance", ""),
                    "",  # data.get("co2", "") - CO2 data removed
                    absolute_humidity or ""
                ]
                writer.writerow(row)
            
            # Append to fixed CSV file
            fixed_file = os.path.join(device_path, f"{device_id}_fixed.csv")
            with open(fixed_file, 'a', newline='') as f:
                writer = csv.writer(f)
                # Ver2.00zeroOne: Commented out "co2" data as we're disabling CO2 sensor functionality
                row = [
                    timestamp,
                    device_id,
                    data.get("temperature", ""),
                    data.get("humidity", ""),
                    data.get("pressure", ""),
                    data.get("gas_resistance", ""),
                    "",  # data.get("co2", "") - CO2 data removed
                    absolute_humidity or ""
                ]
                writer.writerow(row)
            
            # Update last data
            with self.lock:
                self.last_data[device_id] = {
                    "timestamp": timestamp,
                    "temperature": data.get("temperature"),
                    "humidity": data.get("humidity"),
                    "pressure": data.get("pressure"),
                    "gas_resistance": data.get("gas_resistance"),
                    # "co2": data.get("co2"),  # CO2 data removed
                    "absolute_humidity": absolute_humidity
                }
            
            # Log data reception (but not too frequently)
            self.request_count += 1
            if self.request_count % self.config["log_frequency"] == 0:
                logger.info(f"Received data from {device_id}: temp={data.get('temperature')}°C, humidity={data.get('humidity')}%")
            
            return True
        except Exception as e:
            logger.error(f"Error storing data: {e}")
            return False
    
    def _handle_client(self, client_socket, addr):
        """
        Handle a client connection.
        
        Args:
            client_socket (socket.socket): The client socket
            addr (tuple): The client address (ip, port)
        """
        try:
            # Apply rate limiting
            if not self.rate_limiter.is_allowed(addr[0]):
                logger.warning(f"Rate limit exceeded for {addr[0]}")
                client_socket.sendall(b'{"status": "error", "message": "Rate limit exceeded"}')
                return
            
            # Set a timeout for receiving data
            client_socket.settimeout(5)
            
            # Receive data
            data = b""
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                data += chunk
                
                # Check if we have a complete JSON object
                try:
                    # Try to decode and parse the data
                    json_data = json.loads(data.decode('utf-8'))
                    
                    # Validate the data
                    if not self._validate_data(json_data):
                        client_socket.sendall(b'{"status": "error", "message": "Invalid data format"}')
                        return
                    
                    # Store the data
                    if self._store_data(json_data):
                        client_socket.sendall(b'{"status": "success"}')
                    else:
                        client_socket.sendall(b'{"status": "error", "message": "Failed to store data"}')
                    
                    break
                except json.JSONDecodeError:
                    # Not a complete JSON object yet, continue receiving
                    continue
                except Exception as e:
                    logger.error(f"Error processing data: {e}")
                    client_socket.sendall(b'{"status": "error", "message": "Error processing data"}')
                    return
        except socket.timeout:
            logger.warning(f"Connection from {addr[0]} timed out")
        except Exception as e:
            logger.error(f"Error handling client {addr[0]}: {e}")
        finally:
            # Close the connection
            client_socket.close()
    
    def _run_server(self):
        """Run the data collection server."""
        try:
            # Create socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to port
            self.server_socket.bind(('0.0.0.0', self.config["listen_port"]))
            
            # Listen for connections
            self.server_socket.listen(5)
            
            logger.info(f"Server listening on port {self.config['listen_port']}")
            
            # Accept connections
            while self.running:
                try:
                    # Accept connection with timeout to allow for clean shutdown
                    self.server_socket.settimeout(1)
                    client_socket, addr = self.server_socket.accept()
                    
                    # Handle client in a new thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                    # Add a small rest to prevent CPU hogging
                    time.sleep(self.config["rest_time"])
                except socket.timeout:
                    # This is expected, just continue the loop
                    continue
                except Exception as e:
                    if self.running:
                        logger.error(f"Error accepting connection: {e}")
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            # Close the socket
            if self.server_socket:
                self.server_socket.close()
    
    def _setup_api_routes(self):
        """Set up API routes for the Flask app."""
        # Flask imports are already at the top of the file
        
        self.api_app = Flask(__name__)
        
        @self.api_app.route('/api/latest-data', methods=['GET'])
        def get_latest_data():
            """Get the latest data for all devices."""
            with self.lock:
                return jsonify(self.last_data)
        
        @self.api_app.route('/api/device/<device_id>', methods=['GET'])
        def get_device_data(device_id):
            """Get the latest data for a specific device."""
            with self.lock:
                if device_id in self.last_data:
                    return jsonify(self.last_data[device_id])
                else:
                    return jsonify({"error": f"No data available for device {device_id}"}), 404
        
        @self.api_app.route('/api/csv/<device_id>', methods=['GET'])
        def get_csv_data(device_id):
            """Get CSV data for a specific device."""
            try:
                # Check if device_id is valid
                if device_id not in ["P2", "P3", "P4", "P5", "P6"]:
                    return jsonify({"error": f"Invalid device_id: {device_id}"}), 400
                
                # Get device directory
                device_dir_key = f"rawdata_{device_id.lower()}_dir"
                device_dir = self.config[device_dir_key]
                device_path = os.path.join(self.config["data_dir"], device_dir)
                
                # Get fixed CSV file
                fixed_file = os.path.join(device_path, f"{device_id}_fixed.csv")
                
                # Check if file exists
                if not os.path.exists(fixed_file):
                    return jsonify({"error": f"No data available for device {device_id}"}), 404
                
                # Return the file
                return send_file(fixed_file, as_attachment=True, download_name=f"{device_id}_data.csv")
            except Exception as e:
                logger.error(f"Error getting CSV data: {e}")
                return jsonify({"error": str(e)}), 500
    
    def _run_api(self):
        """Run the API server."""
        self.api_app.run(host='0.0.0.0', port=self.config["api_port"], debug=False, use_reloader=False)
    
    def start(self):
        """Start the data collector."""
        if self.running:
            logger.warning("Data collector is already running")
            return False
        
        try:
            # Set running flag
            self.running = True
            
            # Start server thread
            self.server_thread = threading.Thread(target=self._run_server)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            # Set up API routes
            self._setup_api_routes()
            
            # Start API thread
            self.api_thread = threading.Thread(target=self._run_api)
            self.api_thread.daemon = True
            self.api_thread.start()
            
            # Start cleanup thread
            def cleanup_thread():
                while self.running:
                    # Sleep for cleanup interval
                    time.sleep(self.config["cleanup_interval"])
                    
                    # Perform cleanup
                    if self.running:
                        self._cleanup_old_files()
            
            self.cleanup_thread = threading.Thread(target=cleanup_thread)
            self.cleanup_thread.daemon = True
            self.cleanup_thread.start()
            
            logger.info("Data collector started")
            return True
        except Exception as e:
            logger.error(f"Error starting data collector: {e}")
            self.running = False
            return False
    
    def stop(self):
        """Stop the data collector."""
        if not self.running:
            logger.warning("Data collector is not running")
            return False
        
        try:
            # Set running flag to False
            self.running = False
            
            # Close CSV files
            for device_id in self.csv_files:
                self.csv_files[device_id].close()
            
            for device_id in self.fixed_csv_files:
                self.fixed_csv_files[device_id].close()
            
            logger.info("Data collector stopped")
            return True
        except Exception as e:
            logger.error(f"Error stopping data collector: {e}")
            return False

def main():
    """Main function to parse arguments and start the data collector."""
    parser = argparse.ArgumentParser(description="Environmental Data Collector for Solo Version 2.0")
    parser.add_argument("--port", type=int, help="Port to listen on")
    parser.add_argument("--data-dir", type=str, help="Directory to store data")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Create configuration
    config = DEFAULT_CONFIG.copy()
    
    # Override with command line arguments
    if args.port:
        config["listen_port"] = args.port
        config["api_port"] = args.port
    
    if args.data_dir:
        config["data_dir"] = args.data_dir
    
    if args.debug:
        config["debug_mode"] = True
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and start data collector
    collector = DataCollector(config)
    if collector.start():
        try:
            # Keep the main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down...")
            collector.stop()
    else:
        logger.error("Failed to start data collector")
        sys.exit(1)

if __name__ == "__main__":
    main()
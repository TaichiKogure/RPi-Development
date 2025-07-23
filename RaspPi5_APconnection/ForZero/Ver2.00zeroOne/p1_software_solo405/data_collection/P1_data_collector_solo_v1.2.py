"""
Data Collector for Environmental Monitoring System
Version: 1.2

This module provides a data collector for the environmental monitoring system.
It collects data from sensor nodes and stores it in CSV files.
This version is optimized for Raspberry Pi Zero 2W with reduced resource usage.
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
    """Class for collecting and storing environmental data."""
    
    def __init__(self, config=None):
        """
        Initialize the data collector with the given configuration.
        
        Args:
            config (dict, optional): Configuration dictionary. Defaults to None.
        """
        self.config = config or DEFAULT_CONFIG.copy()
        self.lock = threading.Lock()
        self.running = False
        self.last_data = {}
        self.last_rotation = time.time()
        self.last_cleanup = time.time()
        self.wifi_monitor = None
        self.log_counter = {}  # Counter for logging frequency
        
        # Set up rate limiter
        self.rate_limiter = RateLimiter(
            window_size=self.config["rate_limit_window"],
            max_requests=self.config["rate_limit_count"]
        )
        
        # Set up API server
        try:
            from flask import Flask, jsonify, request
            self.api_app = Flask(__name__)
            self._setup_api_routes()
        except ImportError:
            logger.warning("Flask not installed. API server will not be available.")
            self.api_app = None
        
        # Ensure data directories exist
        self._init_csv_files()
    
    def _init_csv_files(self):
        """Initialize CSV files for storing data."""
        # Create data directory if it doesn't exist
        os.makedirs(self.config["data_dir"], exist_ok=True)
        
        # Create device-specific directories
        for device_id in ["P4", "P5", "P6"]:
            device_dir = self.config[f"rawdata_{device_id.lower()}_dir"]
            device_path = os.path.join(self.config["data_dir"], device_dir)
            os.makedirs(device_path, exist_ok=True)
            
            # Create fixed CSV file if it doesn't exist
            fixed_file = os.path.join(device_path, f"{device_id}_fixed.csv")
            if not os.path.exists(fixed_file):
                with open(fixed_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["timestamp", "device_id", "temperature", "humidity", "pressure", "gas_resistance", "co2", "absolute_humidity"])
            
            # Create today's CSV file if it doesn't exist
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            today_file = os.path.join(device_path, f"{device_id}_{today}.csv")
            if not os.path.exists(today_file):
                with open(today_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["timestamp", "device_id", "temperature", "humidity", "pressure", "gas_resistance", "co2", "absolute_humidity"])
            
            # Create latest JSON file if it doesn't exist
            latest_file = os.path.join(device_path, f"{device_id}_latest.json")
            if not os.path.exists(latest_file):
                with open(latest_file, 'w') as f:
                    json.dump({}, f)
        
        logger.info("CSV files initialized")
    
    def _rotate_csv_files(self):
        """Rotate CSV files if needed."""
        now = time.time()
        
        # Check if it's time to rotate files
        if now - self.last_rotation < self.config["file_rotation_interval"]:
            return
        
        self.last_rotation = now
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        for device_id in ["P4", "P5", "P6"]:
            device_dir = self.config[f"rawdata_{device_id.lower()}_dir"]
            device_path = os.path.join(self.config["data_dir"], device_dir)
            
            # Create today's CSV file if it doesn't exist
            today_file = os.path.join(device_path, f"{device_id}_{today}.csv")
            if not os.path.exists(today_file):
                with open(today_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["timestamp", "device_id", "temperature", "humidity", "pressure", "gas_resistance", "co2", "absolute_humidity"])
                
                logger.info(f"Created new CSV file for {device_id}: {today_file}")
        
        # Add a small rest time after file rotation
        time.sleep(self.config["rest_time"])
    
    def _cleanup_old_files(self):
        """Clean up old CSV files."""
        now = time.time()
        
        # Check if it's time to clean up
        if now - self.last_cleanup < self.config["cleanup_interval"]:
            return
        
        self.last_cleanup = now
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=self.config["retention_days"])
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")
        
        for device_id in ["P4", "P5", "P6"]:
            device_dir = self.config[f"rawdata_{device_id.lower()}_dir"]
            device_path = os.path.join(self.config["data_dir"], device_dir)
            
            # Find and delete old CSV files
            for filename in os.listdir(device_path):
                if filename.startswith(f"{device_id}_") and filename.endswith(".csv") and not filename.endswith("_fixed.csv"):
                    try:
                        # Extract date from filename (format: P4_2025-07-22.csv)
                        file_date_str = filename.split('_')[1].split('.')[0]
                        if file_date_str < cutoff_str:
                            os.remove(os.path.join(device_path, filename))
                            logger.info(f"Deleted old CSV file: {filename}")
                    except (IndexError, ValueError):
                        # Skip files that don't match the expected format
                        pass
        
        # Add a small rest time after cleanup
        time.sleep(self.config["rest_time"])
    
    def _calculate_absolute_humidity(self, temperature, humidity):
        """
        Calculate absolute humidity from temperature and relative humidity.
        
        Args:
            temperature (float): Temperature in Celsius.
            humidity (float): Relative humidity in percent.
            
        Returns:
            float: Absolute humidity in g/m³.
        """
        try:
            # Convert temperature and humidity to float
            temperature = float(temperature)
            humidity = float(humidity)
            
            # Calculate saturation vapor pressure
            svp = 6.112 * pow(2.71828, (17.67 * temperature) / (temperature + 243.5))
            
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
        if data["device_id"] not in ["P4", "P5", "P6"]:
            logger.warning(f"Invalid device_id: {data['device_id']}")
            return False
        
        # Check if at least one sensor reading is present
        sensor_fields = ["temperature", "humidity", "pressure", "gas_resistance", "co2"]
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
            device_dir = self.config[f"rawdata_{device_id.lower()}_dir"]
            device_path = os.path.join(self.config["data_dir"], device_dir)
            
            # Get today's date
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            
            # Append to today's CSV file
            today_file = os.path.join(device_path, f"{device_id}_{today}.csv")
            with open(today_file, 'a', newline='') as f:
                writer = csv.writer(f)
                row = [
                    timestamp,
                    device_id,
                    data.get("temperature", ""),
                    data.get("humidity", ""),
                    data.get("pressure", ""),
                    data.get("gas_resistance", ""),
                    data.get("co2", ""),
                    absolute_humidity or ""
                ]
                writer.writerow(row)
            
            # Append to fixed CSV file
            fixed_file = os.path.join(device_path, f"{device_id}_fixed.csv")
            with open(fixed_file, 'a', newline='') as f:
                writer = csv.writer(f)
                row = [
                    timestamp,
                    device_id,
                    data.get("temperature", ""),
                    data.get("humidity", ""),
                    data.get("pressure", ""),
                    data.get("gas_resistance", ""),
                    data.get("co2", ""),
                    absolute_humidity or ""
                ]
                writer.writerow(row)
            
            # Update latest JSON file
            latest_file = os.path.join(device_path, f"{device_id}_latest.json")
            latest_data = {
                "timestamp": timestamp,
                "device_id": device_id,
                "temperature": data.get("temperature", None),
                "humidity": data.get("humidity", None),
                "pressure": data.get("pressure", None),
                "gas_resistance": data.get("gas_resistance", None),
                "co2": data.get("co2", None),
                "absolute_humidity": absolute_humidity
            }
            with open(latest_file, 'w') as f:
                json.dump(latest_data, f, indent=2)
            
            # Update last_data
            with self.lock:
                self.last_data[device_id] = {
                    "timestamp": timestamp,
                    **data,
                    "absolute_humidity": absolute_humidity
                }
            
            # Increment log counter for this device
            if device_id not in self.log_counter:
                self.log_counter[device_id] = 0
            self.log_counter[device_id] += 1
            
            # Log only every nth data point to reduce logging frequency
            if self.log_counter[device_id] % self.config["log_frequency"] == 0:
                logger.info(f"Stored data from {device_id} at {timestamp}")
            
            return True
        except Exception as e:
            logger.error(f"Error storing data: {e}")
            return False
    
    def _handle_client(self, client_socket, addr):
        """
        Handle incoming client connection and data.
        
        Args:
            client_socket (socket.socket): The client socket.
            addr (tuple): The client address.
        """
        logger.info(f"Connection from {addr}")
        sender_ip = addr[0]  # Extract sender IP address
        
        try:
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
                if data.endswith(b"}"):
                    break
                
                # Add rest time between receiving chunks to reduce CPU usage
                time.sleep(self.config["rest_time"])
            
            # Parse JSON data
            if data:
                try:
                    json_data = json.loads(data.decode('utf-8'))
                    
                    # Reduce logging frequency - log only basic info
                    logger.debug(f"Received data from {addr}")
                    
                    # Validate data
                    if self._validate_data(json_data):
                        # Update device IP in WiFi monitor if available
                        if self.wifi_monitor is not None and "device_id" in json_data:
                            try:
                                # Only update IP if it's different from the current one
                                device_id = json_data["device_id"]
                                current_ip = None
                                if hasattr(self.wifi_monitor, 'config') and 'devices' in self.wifi_monitor.config:
                                    if device_id in self.wifi_monitor.config['devices']:
                                        current_ip = self.wifi_monitor.config['devices'][device_id].get('ip')
                                
                                if current_ip != sender_ip:
                                    self.wifi_monitor.update_device_ip(device_id, sender_ip)
                                    logger.info(f"Updated {device_id} IP to {sender_ip} in WiFi monitor")
                            except Exception as e:
                                logger.error(f"Failed to update device IP in WiFi monitor: {e}")
                        
                        # Store data
                        if self._store_data(json_data):
                            # Send acknowledgment
                            client_socket.sendall(b'{"status": "success"}')
                        else:
                            client_socket.sendall(b'{"status": "error", "message": "Failed to store data"}')
                    else:
                        client_socket.sendall(b'{"status": "error", "message": "Invalid data format"}')
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON data: {e}")
                    client_socket.sendall(b'{"status": "error", "message": "Invalid JSON format"}')
            else:
                logger.warning("Received empty data")
                client_socket.sendall(b'{"status": "error", "message": "Empty data"}')
        
        except socket.timeout:
            logger.warning(f"Connection timeout from {addr}")
            client_socket.sendall(b'{"status": "error", "message": "Connection timeout"}')
        except Exception as e:
            logger.error(f"Error handling client {addr}: {e}")
            try:
                client_socket.sendall(b'{"status": "error", "message": "Server error"}')
            except:
                pass
        finally:
            client_socket.close()
            
            # Add rest time after handling client to reduce CPU usage
            time.sleep(self.config["rest_time"])
    
    def _run_server(self):
        """Run the data collection server."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind(('0.0.0.0', self.config["listen_port"]))
            server_socket.listen(5)
            logger.info(f"Server listening on port {self.config['listen_port']}")
            
            while self.running:
                try:
                    # Set a timeout for accept to allow for periodic checks
                    server_socket.settimeout(1.0)
                    
                    try:
                        client_socket, addr = server_socket.accept()
                        client_thread = threading.Thread(
                            target=self._handle_client,
                            args=(client_socket, addr)
                        )
                        client_thread.daemon = True
                        client_thread.start()
                    except socket.timeout:
                        # This is expected - just continue the loop
                        pass
                    
                    # Rotate CSV files if needed
                    self._rotate_csv_files()
                    
                    # Clean up old files if needed
                    self._cleanup_old_files()
                    
                    # Add rest time in the main server loop to reduce CPU usage
                    time.sleep(self.config["rest_time"])
                    
                except Exception as e:
                    if self.running:
                        logger.error(f"Error accepting connection: {e}")
                        time.sleep(1)
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            server_socket.close()
    
    def _setup_api_routes(self):
        """Set up API routes for data access."""
        if self.api_app is None:
            return
        
        app = self.api_app
        
        @app.route('/api/data/latest', methods=['GET'])
        @rate_limit(self.rate_limiter)
        def get_latest_data():
            """Get the latest data from all devices."""
            with self.lock:
                return jsonify(self.last_data)
        
        @app.route('/api/data/device/<device_id>', methods=['GET'])
        @rate_limit(self.rate_limiter)
        def get_device_data(device_id):
            """Get the latest data for a specific device."""
            if device_id not in ["P4", "P5", "P6"]:
                return jsonify({"error": "Invalid device ID"}), 400
            
            with self.lock:
                if device_id in self.last_data:
                    return jsonify(self.last_data[device_id])
                else:
                    return jsonify({"error": "Device data not found"}), 404
        
        @app.route('/api/data/csv/<device_id>', methods=['GET'])
        @rate_limit(self.rate_limiter)
        def get_csv_data(device_id):
            """Get CSV data for a specific device."""
            if device_id not in ["P4", "P5", "P6"]:
                return jsonify({"error": "Invalid device ID"}), 400
            
            try:
                device_dir = self.config[f"rawdata_{device_id.lower()}_dir"]
                fixed_file = os.path.join(self.config["data_dir"], device_dir, f"{device_id}_fixed.csv")
                
                if os.path.exists(fixed_file):
                    with open(fixed_file, 'r') as f:
                        csv_data = f.read()
                    
                    return Response(csv_data, mimetype='text/csv')
                else:
                    return jsonify({"error": "CSV file not found"}), 404
            except Exception as e:
                logger.error(f"Error getting CSV data: {e}")
                return jsonify({"error": "Failed to get CSV data"}), 500
    
    def _run_api(self):
        """Run the API server."""
        if self.api_app is None:
            return
        
        self.api_app.run(host='0.0.0.0', port=self.config["api_port"])
    
    def start(self):
        """Start the data collector."""
        if not self.running:
            self.running = True
            
            # Start server thread
            self.server_thread = threading.Thread(target=self._run_server)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            # Start API server thread
            if self.api_app is not None:
                self.api_thread = threading.Thread(target=self._run_api)
                self.api_thread.daemon = True
                self.api_thread.start()
            
            # Start cleanup thread
            def cleanup_thread():
                while self.running:
                    try:
                        self._rotate_csv_files()
                        self._cleanup_old_files()
                    except Exception as e:
                        logger.error(f"Error in cleanup thread: {e}")
                    
                    # Sleep for a while before next cleanup check
                    time.sleep(60)
            
            self.cleanup_thread = threading.Thread(target=cleanup_thread)
            self.cleanup_thread.daemon = True
            self.cleanup_thread.start()
            
            logger.info("Data collector started")
    
    def stop(self):
        """Stop the data collector."""
        if self.running:
            self.running = False
            
            # Wait for threads to finish
            if hasattr(self, 'server_thread'):
                self.server_thread.join(timeout=5)
            
            if hasattr(self, 'api_thread') and self.api_thread is not None:
                self.api_thread.join(timeout=5)
            
            if hasattr(self, 'cleanup_thread'):
                self.cleanup_thread.join(timeout=5)
            
            logger.info("Data collector stopped")

def main():
    """Main entry point for the data collector."""
    parser = argparse.ArgumentParser(description='Environmental Data Collector')
    parser.add_argument('--port', type=int, help='Port to listen on')
    parser.add_argument('--api-port', type=int, help='Port for API server')
    parser.add_argument('--data-dir', type=str, help='Data directory')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    config = DEFAULT_CONFIG.copy()
    
    if args.port:
        config["listen_port"] = args.port
    
    if args.api_port:
        config["api_port"] = args.api_port
    
    if args.data_dir:
        config["data_dir"] = args.data_dir
    
    if args.debug:
        config["debug_mode"] = True
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and start the data collector
    collector = DataCollector(config)
    
    try:
        # Try to import and set up WiFi monitor
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from connection_monitor.monitor import WiFiMonitor
        
        wifi_monitor = WiFiMonitor()
        collector.wifi_monitor = wifi_monitor
        logger.info("WiFi monitor integration enabled")
    except ImportError:
        logger.warning("WiFi monitor module not found. WiFi monitor integration disabled.")
    
    # Start the collector
    collector.start()
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Stopping...")
    finally:
        collector.stop()

if __name__ == "__main__":
    # Add a small delay to ensure other services are ready
    time.sleep(2)
    
    try:
        from flask import Flask, jsonify, request, Response
    except ImportError:
        logger.warning("Flask not installed. API server will not be available.")
    
    main()
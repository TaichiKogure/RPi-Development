#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi 5 Environmental Data Collection Module for Solo Version 4.0
Version: 4.0.0-solo

This module receives environmental data from P2 and P3 Pico devices with BME680 and MH-Z19C sensors via WiFi,
processes it, and stores it in CSV format for later analysis and visualization.

Features:
- Listens for incoming data from P2 and P3 devices
- Validates and processes received data (including CO2)
- Calculates absolute humidity from temperature and humidity data
- Stores data in separate directories (RawData_P2 and RawData_P3)
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
import time
import json
import socket
import argparse
import threading
import logging
import csv
import datetime
import math
from pathlib import Path
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/data_collector_solo.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "listen_port": 5000,
    "data_dir": "/var/lib(FromThonny)/raspap_solo/data",
    "rawdata_p2_dir": "RawData_P2",
    "rawdata_p3_dir": "RawData_P3",
    "api_port": 5001,
    "max_file_size_mb": 10,
    "rotation_interval_days": 7,
    "device_timeout_seconds": 120
}

class DataCollector:
    """Class to collect and store environmental data from sensor nodes."""
    
    def __init__(self, config=None):
        """Initialize the data collector with the given configuration."""
        self.config = config or DEFAULT_CONFIG.copy()
        self.devices = {}  # Store device information
        self.last_data = {}  # Store the last received data for each device
        self.lock = threading.Lock()  # Lock for thread-safe operations
        
        # Ensure data directories exist
        os.makedirs(self.config["data_dir"], exist_ok=True)
        os.makedirs(os.path.join(self.config["data_dir"], self.config["rawdata_p2_dir"]), exist_ok=True)
        os.makedirs(os.path.join(self.config["data_dir"], self.config["rawdata_p3_dir"]), exist_ok=True)
        
        # Initialize CSV files
        self._init_csv_files()
        
        # Start the data collection server
        self.server_thread = threading.Thread(target=self._run_server)
        self.server_thread.daemon = True
        
        # Start the API server
        self.api_app = Flask(__name__)
        self._setup_api_routes()
        self.api_thread = threading.Thread(target=self._run_api)
        self.api_thread.daemon = True
        
        # Flag to control server operation
        self.running = False
    
    def _init_csv_files(self):
        """Initialize CSV files for data storage."""
        self.csv_files = {}
        self.csv_writers = {}
        
        # Create a new CSV file for today if it doesn't exist for each device
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        for device in ["P2", "P3"]:
            # Determine the appropriate directory for each device
            device_dir = self.config["rawdata_p2_dir"] if device == "P2" else self.config["rawdata_p3_dir"]
            csv_path = os.path.join(self.config["data_dir"], device_dir, f"{device}_{today}.csv")
            
            # Check if file exists
            file_exists = os.path.exists(csv_path)
            
            # Open file and create writer
            self.csv_files[device] = open(csv_path, 'a', newline='')
            self.csv_writers[device] = csv.writer(self.csv_files[device])
            
            # Write header if file is new
            if not file_exists:
                self.csv_writers[device].writerow([
                    "timestamp", "device_id", "temperature", "humidity", 
                    "pressure", "gas_resistance", "co2", "absolute_humidity"
                ])
                self.csv_files[device].flush()
        
        logger.info(f"CSV files initialized for today ({today})")
    
    def _rotate_csv_files(self):
        """Rotate CSV files based on date or size."""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        for device in ["P2", "P3"]:
            # Close current file
            self.csv_files[device].close()
            
            # Determine the appropriate directory for each device
            device_dir = self.config["rawdata_p2_dir"] if device == "P2" else self.config["rawdata_p3_dir"]
            
            # Create new file for today
            csv_path = os.path.join(self.config["data_dir"], device_dir, f"{device}_{today}.csv")
            file_exists = os.path.exists(csv_path)
            
            self.csv_files[device] = open(csv_path, 'a', newline='')
            self.csv_writers[device] = csv.writer(self.csv_files[device])
            
            # Write header if file is new
            if not file_exists:
                self.csv_writers[device].writerow([
                    "timestamp", "device_id", "temperature", "humidity", 
                    "pressure", "gas_resistance", "co2", "absolute_humidity"
                ])
                self.csv_files[device].flush()
        
        logger.info(f"CSV files rotated for today ({today})")
    
    def _cleanup_old_files(self):
        """Remove old data files based on rotation interval."""
        cutoff_date = datetime.datetime.now() - datetime.timedelta(
            days=self.config["rotation_interval_days"]
        )
        
        # Clean up files in both P2 and P3 directories
        for device_dir in [self.config["rawdata_p2_dir"], self.config["rawdata_p3_dir"]]:
            dir_path = os.path.join(self.config["data_dir"], device_dir)
            
            if not os.path.exists(dir_path):
                continue
                
            for filename in os.listdir(dir_path):
                if not filename.endswith(".csv"):
                    continue
                
                try:
                    # Extract date from filename (format: P2_YYYY-MM-DD.csv or P3_YYYY-MM-DD.csv)
                    date_str = filename.split("_")[1].split(".")[0]
                    file_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                    
                    # Remove file if older than cutoff date
                    if file_date < cutoff_date:
                        os.remove(os.path.join(dir_path, filename))
                        logger.info(f"Removed old data file: {filename}")
                except (IndexError, ValueError) as e:
                    logger.warning(f"Could not parse date from filename {filename}: {e}")
    
    def _calculate_absolute_humidity(self, temperature, humidity):
        """Calculate absolute humidity in g/m³ from temperature (°C) and relative humidity (%)."""
        try:
            # Convert temperature and humidity to float
            temp = float(temperature)
            rel_humidity = float(humidity)
            
            # Calculate saturation vapor pressure (hPa)
            # Magnus formula: es = 6.1078 * 10^((7.5 * T) / (237.3 + T))
            saturation_vapor_pressure = 6.1078 * 10 ** ((7.5 * temp) / (237.3 + temp))
            
            # Calculate vapor pressure (hPa)
            vapor_pressure = saturation_vapor_pressure * rel_humidity / 100.0
            
            # Calculate absolute humidity (g/m³)
            # Formula: AH = 216.7 * (VP / (273.15 + T))
            absolute_humidity = 216.7 * (vapor_pressure / (273.15 + temp))
            
            return round(absolute_humidity, 2)
        except Exception as e:
            logger.error(f"Error calculating absolute humidity: {e}")
            return None
    
    def _validate_data(self, data):
        """Validate the received data format and values."""
        required_fields = [
            "device_id", "temperature", "humidity", "pressure", 
            "gas_resistance"
        ]
        
        # Check if all required fields are present
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate device_id
        if data["device_id"] not in ["P2", "P3"]:
            logger.warning(f"Invalid device_id: {data['device_id']}")
            return False
        
        # Validate numeric fields
        numeric_fields = [
            "temperature", "humidity", "pressure", 
            "gas_resistance"
        ]
        
        # Add CO2 to numeric fields if present
        if "co2" in data:
            numeric_fields.append("co2")
        
        for field in numeric_fields:
            try:
                float(data[field])
            except (ValueError, TypeError):
                logger.warning(f"Invalid value for {field}: {data[field]}")
                return False
        
        # Validate ranges
        if not (-40 <= float(data["temperature"]) <= 85):
            logger.warning(f"Temperature out of range: {data['temperature']}")
            return False
        
        if not (0 <= float(data["humidity"]) <= 100):
            logger.warning(f"Humidity out of range: {data['humidity']}")
            return False
        
        if not (300 <= float(data["pressure"]) <= 1100):
            logger.warning(f"Pressure out of range: {data['pressure']}")
            return False
        
        # Validate CO2 range if present
        if "co2" in data and not (400 <= float(data["co2"]) <= 5000):
            logger.warning(f"CO2 out of range: {data['co2']}")
            return False
        
        return True
    
    def _store_data(self, data):
        """Store the validated data in CSV file."""
        device_id = data["device_id"]
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Check if we need to rotate files (new day)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        current_file = self.csv_files[device_id].name
        if today not in current_file:
            self._rotate_csv_files()
        
        # Calculate absolute humidity
        absolute_humidity = self._calculate_absolute_humidity(
            data["temperature"], 
            data["humidity"]
        )
        
        # Prepare row data
        row_data = [
            timestamp,
            device_id,
            data["temperature"],
            data["humidity"],
            data["pressure"],
            data["gas_resistance"]
        ]
        
        # Add CO2 if present
        if "co2" in data:
            row_data.append(data["co2"])
        else:
            row_data.append("")  # Empty value for CO2
        
        # Add absolute humidity
        row_data.append(absolute_humidity if absolute_humidity is not None else "")
        
        # Write data to CSV
        self.csv_writers[device_id].writerow(row_data)
        self.csv_files[device_id].flush()
        
        # Update last data
        with self.lock:
            self.last_data[device_id] = {
                "timestamp": timestamp,
                **data,
                "absolute_humidity": absolute_humidity
            }
        
        logger.info(f"Stored data from {device_id} at {timestamp}")
        return True
    
    def _handle_client(self, client_socket, addr):
        """Handle incoming client connection and data."""
        logger.info(f"Connection from {addr}")
        
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
            
            # Parse JSON data
            if data:
                try:
                    json_data = json.loads(data.decode('utf-8'))
                    logger.info(f"Received data: {json_data}")
                    
                    # Validate data
                    if self._validate_data(json_data):
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
                    client_socket, addr = server_socket.accept()
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()
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
        app = self.api_app
        
        @app.route('/api/data/latest', methods=['GET'])
        def get_latest_data():
            """Get the latest data from all devices."""
            with self.lock:
                return jsonify(self.last_data)
        
        @app.route('/api/data/device/<device_id>', methods=['GET'])
        def get_device_data(device_id):
            """Get the latest data for a specific device."""
            if device_id not in ["P2", "P3"]:
                return jsonify({"error": "Invalid device ID"}), 400
            
            with self.lock:
                if device_id in self.last_data:
                    return jsonify(self.last_data[device_id])
                else:
                    return jsonify({"error": "No data available for this device"}), 404
        
        @app.route('/api/data/csv/<device_id>', methods=['GET'])
        def get_csv_data(device_id):
            """Get the path to the CSV file for a specific device."""
            if device_id not in ["P2", "P3"]:
                return jsonify({"error": "Invalid device ID"}), 400
            
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            device_dir = self.config["rawdata_p2_dir"] if device_id == "P2" else self.config["rawdata_p3_dir"]
            csv_path = os.path.join(self.config["data_dir"], device_dir, f"{device_id}_{today}.csv")
            
            if os.path.exists(csv_path):
                return jsonify({"csv_path": csv_path})
            else:
                return jsonify({"error": "CSV file not found"}), 404
    
    def _run_api(self):
        """Run the API server."""
        self.api_app.run(host='0.0.0.0', port=self.config["api_port"])
    
    def start(self):
        """Start the data collector."""
        if not self.running:
            self.running = True
            self.server_thread.start()
            self.api_thread.start()
            logger.info("Data collector started")
            
            # Start a thread to clean up old files periodically
            def cleanup_thread():
                while self.running:
                    self._cleanup_old_files()
                    time.sleep(86400)  # Run once a day
            
            cleanup = threading.Thread(target=cleanup_thread)
            cleanup.daemon = True
            cleanup.start()
    
    def stop(self):
        """Stop the data collector."""
        if self.running:
            self.running = False
            
            # Close CSV files
            for file in self.csv_files.values():
                file.close()
            
            logger.info("Data collector stopped")

def main():
    """Main function to run the data collector."""
    parser = argparse.ArgumentParser(description='Environmental Data Collector for P2 and P3 devices')
    parser.add_argument('--port', type=int, help='Port to listen on')
    parser.add_argument('--data-dir', type=str, help='Directory to store data')
    parser.add_argument('--api-port', type=int, help='Port for the API server')
    args = parser.parse_args()
    
    # Create configuration
    config = DEFAULT_CONFIG.copy()
    
    if args.port:
        config["listen_port"] = args.port
    
    if args.data_dir:
        config["data_dir"] = args.data_dir
    
    if args.api_port:
        config["api_port"] = args.api_port
    
    # Create and start the data collector
    collector = DataCollector(config)
    
    try:
        collector.start()
        logger.info("Data collector running. Press Ctrl+C to stop.")
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Stopping data collector...")
        collector.stop()
        logger.info("Data collector stopped.")
    
    except Exception as e:
        logger.error(f"Error in data collector: {e}")
        collector.stop()
        sys.exit(1)

if __name__ == "__main__":
    main()
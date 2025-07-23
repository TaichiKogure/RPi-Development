#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi 5 Environmental Data Collection Module for Solo Version
Version: 1.0.0-solo

This module receives environmental data from a single P2 Pico device with BME680 sensor via WiFi,
processes it, and stores it in CSV format for later analysis and visualization.

Features:
- Listens for incoming data from P2 device
- Validates and processes received data
- Stores data in CSV files with timestamps
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
    "data_dir": "/var/lib/raspap_solo/data",
    "api_port": 5001,
    "max_file_size_mb": 10,
    "rotation_interval_days": 7,
    "device_timeout_seconds": 120
}

class DataCollector:
    """Class to collect and store environmental data from sensor node."""
    
    def __init__(self, config=None):
        """Initialize the data collector with the given configuration."""
        self.config = config or DEFAULT_CONFIG.copy()
        self.devices = {}  # Store device information
        self.last_data = {}  # Store the last received data for each device
        self.lock = threading.Lock()  # Lock for thread-safe operations
        
        # Ensure data directory exists
        os.makedirs(self.config["data_dir"], exist_ok=True)
        
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
        
        # Create a new CSV file for today if it doesn't exist
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        device = "P2"  # Solo version only uses P2
        csv_path = os.path.join(self.config["data_dir"], f"{device}_{today}.csv")
        
        # Check if file exists
        file_exists = os.path.exists(csv_path)
        
        # Open file and create writer
        self.csv_files[device] = open(csv_path, 'a', newline='')
        self.csv_writers[device] = csv.writer(self.csv_files[device])
        
        # Write header if file is new
        if not file_exists:
            self.csv_writers[device].writerow([
                "timestamp", "device_id", "temperature", "humidity", 
                "pressure", "gas_resistance"
            ])
            self.csv_files[device].flush()
        
        logger.info(f"CSV files initialized for today ({today})")
    
    def _rotate_csv_files(self):
        """Rotate CSV files based on date or size."""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        device = "P2"  # Solo version only uses P2
        # Close current file
        self.csv_files[device].close()
        
        # Create new file for today
        csv_path = os.path.join(self.config["data_dir"], f"{device}_{today}.csv")
        file_exists = os.path.exists(csv_path)
        
        self.csv_files[device] = open(csv_path, 'a', newline='')
        self.csv_writers[device] = csv.writer(self.csv_files[device])
        
        # Write header if file is new
        if not file_exists:
            self.csv_writers[device].writerow([
                "timestamp", "device_id", "temperature", "humidity", 
                "pressure", "gas_resistance"
            ])
            self.csv_files[device].flush()
        
        logger.info(f"CSV files rotated for today ({today})")
    
    def _cleanup_old_files(self):
        """Remove old data files based on rotation interval."""
        cutoff_date = datetime.datetime.now() - datetime.timedelta(
            days=self.config["rotation_interval_days"]
        )
        
        for filename in os.listdir(self.config["data_dir"]):
            if not filename.endswith(".csv"):
                continue
            
            try:
                # Extract date from filename (format: P2_YYYY-MM-DD.csv)
                date_str = filename.split("_")[1].split(".")[0]
                file_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                
                # Remove file if older than cutoff date
                if file_date < cutoff_date:
                    os.remove(os.path.join(self.config["data_dir"], filename))
                    logger.info(f"Removed old data file: {filename}")
            except (IndexError, ValueError) as e:
                logger.warning(f"Could not parse date from filename {filename}: {e}")
    
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
        if data["device_id"] != "P2":
            logger.warning(f"Invalid device_id: {data['device_id']}")
            return False
        
        # Validate numeric fields
        numeric_fields = [
            "temperature", "humidity", "pressure", 
            "gas_resistance"
        ]
        
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
        
        # Write data to CSV
        self.csv_writers[device_id].writerow([
            timestamp,
            device_id,
            data["temperature"],
            data["humidity"],
            data["pressure"],
            data["gas_resistance"]
        ])
        self.csv_files[device_id].flush()
        
        # Update last data
        with self.lock:
            self.last_data[device_id] = {
                "timestamp": timestamp,
                **data
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
            if device_id != "P2":
                return jsonify({"error": "Invalid device ID"}), 400
            
            with self.lock:
                if device_id in self.last_data:
                    return jsonify(self.last_data[device_id])
                else:
                    return jsonify({"error": "No data available for this device"}), 404
        
        @app.route('/api/data/csv/<device_id>', methods=['GET'])
        def get_csv_data(device_id):
            """Get the path to the CSV file for a specific device."""
            if device_id != "P2":
                return jsonify({"error": "Invalid device ID"}), 400
            
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            csv_path = os.path.join(self.config["data_dir"], f"{device_id}_{today}.csv")
            
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
    """Main function to parse arguments and start the data collector."""
    parser = argparse.ArgumentParser(description="Raspberry Pi 5 Environmental Data Collector for Solo Version")
    parser.add_argument("--port", type=int, default=DEFAULT_CONFIG["listen_port"],
                        help=f"Port to listen on (default: {DEFAULT_CONFIG['listen_port']})")
    parser.add_argument("--data-dir", type=str, default=DEFAULT_CONFIG["data_dir"],
                        help=f"Directory to store data (default: {DEFAULT_CONFIG['data_dir']})")
    parser.add_argument("--api-port", type=int, default=DEFAULT_CONFIG["api_port"],
                        help=f"Port for API server (default: {DEFAULT_CONFIG['api_port']})")
    
    args = parser.parse_args()
    
    # Update configuration with command-line arguments
    config = DEFAULT_CONFIG.copy()
    config["listen_port"] = args.port
    config["data_dir"] = args.data_dir
    config["api_port"] = args.api_port
    
    # Create and start the data collector
    collector = DataCollector(config)
    
    try:
        collector.start()
        print(f"Data collector running on port {config['listen_port']}")
        print(f"API server running on port {config['api_port']}")
        print("Press Ctrl+C to stop")
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping data collector...")
        collector.stop()
        print("Data collector stopped")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        collector.stop()

if __name__ == "__main__":
    main()
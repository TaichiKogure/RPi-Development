#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCD41 Data Collector for Raspberry Pi 5
Version: 1.0.0

This module collects data from the SCD41 CO2 sensor and stores it in CSV format
compatible with the P1 data format from Ver4.66Debug.

Features:
- Collects CO2, temperature, and humidity data from SCD41 sensor
- Calculates absolute humidity from temperature and humidity data
- Stores data in CSV format with timestamp, device_id, temperature, humidity,
  pressure, gas_resistance, co2, absolute_humidity
- Uses placeholder values (6000) for pressure and gas_resistance

Usage:
    python3 scd41_data_collector.py [--data-dir DIR] [--interval SECONDS]
"""

import os
import sys
import argparse
import logging
import time
import datetime
import csv
import signal

# Add the parent directory to the Python path so we can import from sensor_drivers
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import the SCD41 sensor driver
try:
    from sensor_drivers.scd41 import SCD41
except ImportError as e:
    print(f"Failed to import SCD41 sensor driver: {e}")
    print("Make sure the sensor_drivers directory is in the Python path.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scd41_data_collector.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SCD41DataCollector:
    """Class to collect and store data from SCD41 sensor."""
    
    def __init__(self, config=None):
        """Initialize the data collector with the given configuration."""
        self.config = config or {
            "data_dir": "data",
            "interval": 30,  # seconds
            "device_id": "SCD41",
            "placeholder_value": 6000  # Placeholder value for pressure and gas_resistance
        }
        
        # Ensure data directory exists
        os.makedirs(self.config["data_dir"], exist_ok=True)
        
        # Initialize CSV file
        self.csv_file = None
        self.csv_writer = None
        self._init_csv_file()
        
        # Initialize sensor
        try:
            self.sensor = SCD41(debug=False)
            logger.info("SCD41 sensor initialized")
            
            # Start periodic measurement
            self.sensor.start_periodic_measurement()
            logger.info("Periodic measurement started")
            
            # Wait for sensor warmup
            logger.info("Waiting for sensor warmup (5 seconds)...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Failed to initialize SCD41 sensor: {e}")
            sys.exit(1)
        
        # Flag to control data collection
        self.running = False
    
    def _init_csv_file(self):
        """Initialize CSV file for data storage."""
        # Create a new CSV file for today if it doesn't exist
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        csv_path = os.path.join(self.config["data_dir"], f"{self.config['device_id']}_{today}.csv")
        file_exists = os.path.exists(csv_path)
        
        # Open file and create writer
        self.csv_file = open(csv_path, 'a', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        
        # Write header if file is new
        if not file_exists:
            self.csv_writer.writerow([
                "timestamp", "device_id", "temperature", "humidity", 
                "pressure", "gas_resistance", "co2", "absolute_humidity"
            ])
            self.csv_file.flush()
        
        logger.info(f"CSV file initialized: {csv_path}")
    
    def _rotate_csv_file(self):
        """Rotate CSV file based on date."""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        current_file = self.csv_file.name
        
        if today not in current_file:
            # Close current file
            self.csv_file.close()
            
            # Create new file for today
            csv_path = os.path.join(self.config["data_dir"], f"{self.config['device_id']}_{today}.csv")
            file_exists = os.path.exists(csv_path)
            
            self.csv_file = open(csv_path, 'a', newline='')
            self.csv_writer = csv.writer(self.csv_file)
            
            # Write header if file is new
            if not file_exists:
                self.csv_writer.writerow([
                    "timestamp", "device_id", "temperature", "humidity", 
                    "pressure", "gas_resistance", "co2", "absolute_humidity"
                ])
                self.csv_file.flush()
            
            logger.info(f"CSV file rotated: {csv_path}")
    
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
    
    def _store_data(self, data):
        """Store the data in CSV file."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Check if we need to rotate files (new day)
        self._rotate_csv_file()
        
        # Calculate absolute humidity
        absolute_humidity = self._calculate_absolute_humidity(
            data["temperature"], 
            data["humidity"]
        )
        
        # Prepare row data
        row_data = [
            timestamp,
            self.config["device_id"],
            data["temperature"],
            data["humidity"],
            self.config["placeholder_value"],  # Placeholder for pressure
            self.config["placeholder_value"],  # Placeholder for gas_resistance
            data["co2"],
            absolute_humidity if absolute_humidity is not None else ""
        ]
        
        # Write data to CSV
        self.csv_writer.writerow(row_data)
        self.csv_file.flush()
        
        logger.info(f"Data stored: CO2={data['co2']} ppm, Temp={data['temperature']} °C, Humidity={data['humidity']} %, Abs. Humidity={absolute_humidity} g/m³")
        return True
    
    def collect_data(self):
        """Collect data from sensor and store it."""
        try:
            # Read data from sensor
            readings = self.sensor.get_readings()
            
            # Store data
            if self._store_data(readings):
                return True
            else:
                logger.error("Failed to store data")
                return False
        except Exception as e:
            logger.error(f"Error collecting data: {e}")
            return False
    
    def start(self):
        """Start the data collector."""
        if not self.running:
            self.running = True
            logger.info("Data collector started")
            
            try:
                while self.running:
                    # Collect and store data
                    self.collect_data()
                    
                    # Wait for next collection interval
                    time.sleep(self.config["interval"])
            except KeyboardInterrupt:
                logger.info("Data collection interrupted by user")
            except Exception as e:
                logger.error(f"Error in data collection loop: {e}")
            finally:
                self.stop()
    
    def stop(self):
        """Stop the data collector."""
        if self.running:
            self.running = False
            
            # Stop periodic measurement
            try:
                self.sensor.stop_periodic_measurement()
                logger.info("Periodic measurement stopped")
            except Exception as e:
                logger.error(f"Error stopping periodic measurement: {e}")
            
            # Close CSV file
            if self.csv_file:
                self.csv_file.close()
                logger.info("CSV file closed")
            
            logger.info("Data collector stopped")

def signal_handler(sig, frame):
    """Handle signals to gracefully stop the data collector."""
    logger.info(f"Received signal {sig}, stopping data collector...")
    if 'collector' in globals():
        collector.stop()
    sys.exit(0)

def main():
    """Main function to run the data collector."""
    parser = argparse.ArgumentParser(description='SCD41 Data Collector')
    parser.add_argument('--data-dir', type=str, default='data', help='Directory to store data')
    parser.add_argument('--interval', type=int, default=30, help='Data collection interval in seconds')
    parser.add_argument('--device-id', type=str, default='SCD41', help='Device ID for CSV data')
    args = parser.parse_args()
    
    # Create configuration
    config = {
        "data_dir": args.data_dir,
        "interval": args.interval,
        "device_id": args.device_id,
        "placeholder_value": 6000  # Placeholder value for pressure and gas_resistance
    }
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start the data collector
    global collector
    collector = SCD41DataCollector(config)
    
    try:
        collector.start()
    except Exception as e:
        logger.error(f"Error in data collector: {e}")
        collector.stop()
        sys.exit(1)

if __name__ == "__main__":
    main()
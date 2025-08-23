"""
CSV Manager Module for Data Storage

This module contains functions for managing CSV files for data storage.
Version: 2.0.0-solo - Updated for BME680 sensors only (no CO2 sensors)
"""

import os
import csv
import logging
import datetime
import threading
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class CSVManager:
    """Class to manage CSV files for data storage."""
    
    def __init__(self, config):
        """
        Initialize the CSV manager with the given configuration.
        
        Args:
            config (dict): Configuration dictionary
        """
        self.config = config
        self.csv_files = {}
        self.csv_writers = {}
        self.fixed_csv_files = {}
        self.fixed_csv_writers = {}
        self.lock = threading.Lock()
        
        # Initialize CSV files
        self._init_csv_files()
        
    def _init_csv_files(self):
        """Initialize CSV files for data storage."""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        for device in ["P2", "P3", "P4", "P5", "P6"]:
            # Determine the appropriate directory for each device
            if device == "P2":
                device_dir = self.config["rawdata_p2_dir"]
            elif device == "P3":
                device_dir = self.config["rawdata_p3_dir"]
            elif device == "P4":
                device_dir = self.config["rawdata_p4_dir"]
            elif device == "P5":
                device_dir = self.config["rawdata_p5_dir"]
            else:  # P6
                device_dir = self.config["rawdata_p6_dir"]
            
            # Date-based CSV file
            csv_path = os.path.join(self.config["data_dir"], device_dir, f"{device}_{today}.csv")
            file_exists = os.path.exists(csv_path)
            
            # Open file and create writer
            self.csv_files[device] = open(csv_path, 'a', newline='')
            self.csv_writers[device] = csv.writer(self.csv_files[device])
            
            # Write header if file is new
            if not file_exists:
                # Ver2.00zeroOne: Replaced "co2" with empty column as we're disabling CO2 sensor functionality
                self.csv_writers[device].writerow([
                    "timestamp", "device_id", "temperature", "humidity", 
                    "pressure", "gas_resistance", "", "absolute_humidity"
                ])
                self.csv_files[device].flush()
            
            # Fixed CSV file
            fixed_csv_path = os.path.join(self.config["data_dir"], device_dir, f"{device}_fixed.csv")
            fixed_file_exists = os.path.exists(fixed_csv_path)
            
            # Open fixed file and create writer
            self.fixed_csv_files[device] = open(fixed_csv_path, 'a', newline='')
            self.fixed_csv_writers[device] = csv.writer(self.fixed_csv_files[device])
            
            # Write header if fixed file is new
            if not fixed_file_exists:
                # Ver2.00zeroOne: Replaced "co2" with empty column as we're disabling CO2 sensor functionality
                self.fixed_csv_writers[device].writerow([
                    "timestamp", "device_id", "temperature", "humidity", 
                    "pressure", "gas_resistance", "", "absolute_humidity"
                ])
                self.fixed_csv_files[device].flush()
        
        logger.info(f"CSV files initialized for today ({today}) and fixed files")
    
    def rotate_csv_files(self):
        """Rotate CSV files based on date or size."""
        with self.lock:
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            
            for device in ["P2", "P3", "P4", "P5", "P6"]:
                # Close current date-based file
                self.csv_files[device].close()
                
                # Determine the appropriate directory for each device
                if device == "P2":
                    device_dir = self.config["rawdata_p2_dir"]
                elif device == "P3":
                    device_dir = self.config["rawdata_p3_dir"]
                elif device == "P4":
                    device_dir = self.config["rawdata_p4_dir"]
                elif device == "P5":
                    device_dir = self.config["rawdata_p5_dir"]
                else:  # P6
                    device_dir = self.config["rawdata_p6_dir"]
                
                # Create new file for today
                csv_path = os.path.join(self.config["data_dir"], device_dir, f"{device}_{today}.csv")
                file_exists = os.path.exists(csv_path)
                
                # Open file and create writer
                self.csv_files[device] = open(csv_path, 'a', newline='')
                self.csv_writers[device] = csv.writer(self.csv_files[device])
                
                # Write header if file is new
                if not file_exists:
                    # Ver2.00zeroOne: Replaced "co2" with empty column as we're disabling CO2 sensor functionality
                    self.csv_writers[device].writerow([
                        "timestamp", "device_id", "temperature", "humidity", 
                        "pressure", "gas_resistance", "", "absolute_humidity"
                    ])
                    self.csv_files[device].flush()
            
            logger.info(f"CSV files rotated for today ({today})")
    
    def write_data(self, device_id, data):
        """
        Write data to CSV files.
        
        Args:
            device_id (str): The device ID
            data (dict): The data to write
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.lock:
                # Check if we need to rotate files (new day)
                today = datetime.datetime.now().strftime("%Y-%m-%d")
                current_file = self.csv_files[device_id].name
                if today not in current_file:
                    self.rotate_csv_files()
                
                # Prepare row data
                # Ver2.00zeroOne: Replaced "co2" with empty string as we're disabling CO2 sensor functionality
                row_data = [
                    data["timestamp"],
                    device_id,
                    data.get("temperature", ""),
                    data.get("humidity", ""),
                    data.get("pressure", ""),
                    data.get("gas_resistance", ""),
                    "",  # Empty column for CO2 (removed)
                    data.get("absolute_humidity", "")
                ]
                
                # Write to date-based CSV
                self.csv_writers[device_id].writerow(row_data)
                self.csv_files[device_id].flush()
                
                # Write to fixed CSV
                self.fixed_csv_writers[device_id].writerow(row_data)
                self.fixed_csv_files[device_id].flush()
                
                return True
        except Exception as e:
            logger.error(f"Error writing data to CSV: {e}")
            return False
    
    def close(self):
        """Close all CSV files."""
        with self.lock:
            for device in self.csv_files:
                self.csv_files[device].close()
            
            for device in self.fixed_csv_files:
                self.fixed_csv_files[device].close()
            
            logger.info("CSV files closed")
    
    def get_csv_data(self, device_id, start_date=None, end_date=None):
        """
        Get CSV data for a specific device.
        
        Args:
            device_id (str): The device ID
            start_date (datetime.datetime, optional): Start date for data. Defaults to None.
            end_date (datetime.datetime, optional): End date for data. Defaults to None.
            
        Returns:
            list: List of data rows
        """
        try:
            # Determine the appropriate directory for the device
            if device_id == "P2":
                device_dir = self.config["rawdata_p2_dir"]
            elif device_id == "P3":
                device_dir = self.config["rawdata_p3_dir"]
            elif device_id == "P4":
                device_dir = self.config["rawdata_p4_dir"]
            elif device_id == "P5":
                device_dir = self.config["rawdata_p5_dir"]
            elif device_id == "P6":
                device_dir = self.config["rawdata_p6_dir"]
            else:
                logger.error(f"Invalid device ID: {device_id}")
                return []
            
            # Set default dates if not provided
            if start_date is None:
                start_date = datetime.datetime.now() - datetime.timedelta(days=7)
            if end_date is None:
                end_date = datetime.datetime.now()
            
            # Generate a list of dates in the range
            current_date = start_date
            date_list = []
            while current_date <= end_date:
                date_list.append(current_date.strftime("%Y-%m-%d"))
                current_date += datetime.timedelta(days=1)
            
            # Read data from CSV files
            data_rows = []
            for date_str in date_list:
                csv_path = os.path.join(self.config["data_dir"], device_dir, f"{device_id}_{date_str}.csv")
                if os.path.exists(csv_path):
                    with open(csv_path, 'r') as f:
                        reader = csv.reader(f)
                        next(reader)  # Skip header
                        for row in reader:
                            data_rows.append(row)
            
            return data_rows
        except Exception as e:
            logger.error(f"Error getting CSV data: {e}")
            return []
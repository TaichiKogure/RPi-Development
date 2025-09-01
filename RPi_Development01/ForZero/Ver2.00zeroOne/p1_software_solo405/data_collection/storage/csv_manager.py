"""
CSV Manager Module for Data Storage

This module contains functions for managing CSV files for data storage.
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
                self.csv_writers[device].writerow([
                    "timestamp", "device_id", "temperature", "humidity", 
                    "pressure", "gas_resistance", "co2", "absolute_humidity"
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
                self.fixed_csv_writers[device].writerow([
                    "timestamp", "device_id", "temperature", "humidity", 
                    "pressure", "gas_resistance", "co2", "absolute_humidity"
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
    
    def cleanup_old_files(self):
        """Clean up old CSV files based on retention policy."""
        with self.lock:
            # Calculate the cutoff date
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=self.config["rotation_interval_days"])
            cutoff_str = cutoff_date.strftime("%Y-%m-%d")
            
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
                
                directory = os.path.join(self.config["data_dir"], device_dir)
                
                # List all CSV files in the directory
                try:
                    for filename in os.listdir(directory):
                        if filename.startswith(f"{device}_") and filename.endswith(".csv") and not filename.endswith("_fixed.csv"):
                            # Extract date from filename
                            try:
                                file_date = filename.split("_")[1].split(".")[0]
                                if file_date < cutoff_str:
                                    file_path = os.path.join(directory, filename)
                                    os.remove(file_path)
                                    logger.info(f"Deleted old CSV file: {file_path}")
                            except Exception as e:
                                logger.error(f"Error parsing date from filename {filename}: {e}")
                except Exception as e:
                    logger.error(f"Error cleaning up old files in {directory}: {e}")
            
            logger.info(f"Cleaned up CSV files older than {cutoff_str}")
    
    def write_data(self, data):
        """
        Write data to CSV files.
        
        Args:
            data (dict): The data to write
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.lock:
                device = data["device_id"]
                
                # Prepare row data
                row = [
                    data["timestamp"],
                    device,
                    data.get("temperature", ""),
                    data.get("humidity", ""),
                    data.get("pressure", ""),
                    data.get("gas_resistance", ""),
                    data.get("co2", ""),
                    data.get("absolute_humidity", "")
                ]
                
                # Write to date-based CSV file
                self.csv_writers[device].writerow(row)
                self.csv_files[device].flush()
                
                # Write to fixed CSV file
                self.fixed_csv_writers[device].writerow(row)
                self.fixed_csv_files[device].flush()
                
                return True
        except Exception as e:
            logger.error(f"Error writing data to CSV: {e}")
            return False
    
    def close(self):
        """Close all CSV files."""
        with self.lock:
            for device in ["P2", "P3", "P4", "P5", "P6"]:
                try:
                    self.csv_files[device].close()
                    self.fixed_csv_files[device].close()
                except Exception as e:
                    logger.error(f"Error closing CSV files for {device}: {e}")
            
            logger.info("CSV files closed")
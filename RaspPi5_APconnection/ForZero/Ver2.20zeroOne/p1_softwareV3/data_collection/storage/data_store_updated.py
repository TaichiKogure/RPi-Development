"""
Data Store Module for Data Storage

This module contains functions for storing and retrieving sensor data.
Version: 2.0.0-solo - Updated for BME680 sensors only (no CO2 sensors) and all devices (P2-P6)
"""

import logging
import threading
import datetime
import json

# Configure logging
logger = logging.getLogger(__name__)

class DataStore:
    """Class to store and retrieve sensor data."""
    
    def __init__(self, config):
        """
        Initialize the data store with the given configuration.
        
        Args:
            config (dict): Configuration dictionary
        """
        self.config = config
        self.devices = {}  # Store device information
        self.last_data = {}  # Store the last received data for each device
        self.lock = threading.Lock()  # Lock for thread-safe operations
    
    def store_data(self, data):
        """
        Store the data in memory.
        
        Args:
            data (dict): The data to store
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.lock:
                device_id = data["device_id"]
                
                # Store the data
                self.last_data[device_id] = data
                
                # Update device information
                if device_id not in self.devices:
                    self.devices[device_id] = {}
                
                # Update last seen timestamp
                self.devices[device_id]["last_seen"] = datetime.datetime.now()
                
                return True
        except Exception as e:
            logger.error(f"Error storing data: {e}")
            return False
    
    def get_latest_data(self, device_id=None):
        """
        Get the latest data for the specified device.
        
        Args:
            device_id (str, optional): The device ID to get data for. If None, returns data for all devices.
            
        Returns:
            dict or list: The latest data for the specified device or all devices
        """
        with self.lock:
            if device_id:
                return self.last_data.get(device_id)
            else:
                return self.last_data
    
    def get_device_status(self, device_id):
        """
        Get the status of the specified device.
        
        Args:
            device_id (str): The device ID to get status for
            
        Returns:
            dict: The device status
        """
        with self.lock:
            if device_id not in self.devices:
                return {"online": False, "last_seen": None}
            
            last_seen = self.devices[device_id].get("last_seen")
            if last_seen:
                # Check if the device is online based on the timeout
                now = datetime.datetime.now()
                time_diff = (now - last_seen).total_seconds()
                online = time_diff < self.config["device_timeout_seconds"]
                
                return {
                    "online": online,
                    "last_seen": last_seen.strftime("%Y-%m-%d %H:%M:%S"),
                    "time_since_last_seen": time_diff
                }
            else:
                return {"online": False, "last_seen": None}
    
    def get_all_devices_status(self):
        """
        Get the status of all devices.
        
        Returns:
            dict: The status of all devices
        """
        with self.lock:
            result = {}
            # Ver2.00zeroOne: Updated to include P2, P3, P4, P5, and P6
            for device_id in ["P2", "P3", "P4", "P5", "P6"]:
                result[device_id] = self.get_device_status(device_id)
            return result
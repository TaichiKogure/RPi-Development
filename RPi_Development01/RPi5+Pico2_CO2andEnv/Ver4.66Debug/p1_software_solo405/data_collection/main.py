"""
Main Module for Data Collection

This module provides the main entry point for the data collection system.
It integrates all the components (network, processing, storage, api) to collect
and store data from sensor nodes.
"""

import os
import sys
import time
import json
import argparse
import threading
import logging
import datetime
from pathlib import Path

# Import components
from p1_software_solo405.data_collection.config import DEFAULT_CONFIG, MONITOR_CONFIG, ensure_data_directories
from p1_software_solo405.data_collection.network.server import DataServer
from p1_software_solo405.data_collection.processing.calculation import calculate_absolute_humidity
from p1_software_solo405.data_collection.processing.validation import validate_data
from p1_software_solo405.data_collection.storage.csv_manager import CSVManager
from p1_software_solo405.data_collection.storage.data_store import DataStore
from p1_software_solo405.data_collection.api.server import APIServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataCollector:
    """Class to collect and store environmental data from sensor nodes."""
    
    def __init__(self, config=None):
        """Initialize the data collector with the given configuration."""
        self.config = config or DEFAULT_CONFIG.copy()
        
        # Ensure data directories exist
        ensure_data_directories(self.config)
        
        # Initialize components
        self.data_store = DataStore(self.config)
        self.csv_manager = CSVManager(self.config)
        
        # Initialize WiFi monitor for dynamic IP tracking
        self.wifi_monitor = None
        try:
            # Import here to avoid circular imports
            from p1_software_solo405.connection_monitor.monitor import WiFiMonitor
            self.wifi_monitor = WiFiMonitor(MONITOR_CONFIG.copy())
            logger.info("WiFi monitor initialized for dynamic IP tracking")
        except Exception as e:
            logger.error(f"Failed to initialize WiFi monitor: {e}")
        
        # Initialize data server
        self.data_server = DataServer(self.config, self._handle_data)
        
        # Initialize API server
        self.api_server = APIServer(self.config, self.data_store)
        
        # Set up cleanup thread
        self.cleanup_thread = None
        self.running = False
    
    def _handle_data(self, data, addr):
        """
        Handle data received from a sensor node.
        
        Args:
            data (dict): The data received
            addr (tuple): The address of the sender (ip, port)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate data
            is_valid, validated_data, error = validate_data(data)
            if not is_valid:
                logger.error(f"Invalid data received: {error}")
                return False
            
            # Calculate absolute humidity if temperature and humidity are available
            if "temperature" in validated_data and "humidity" in validated_data:
                absolute_humidity = calculate_absolute_humidity(
                    validated_data["temperature"],
                    validated_data["humidity"]
                )
                validated_data["absolute_humidity"] = absolute_humidity
            
            # Store data in memory
            self.data_store.store_data(validated_data)
            
            # Store data in CSV files
            result = self.csv_manager.write_data(validated_data)
            
            # Update WiFi monitor with sender IP if available
            if self.wifi_monitor and "device_id" in validated_data:
                device_id = validated_data["device_id"]
                sender_ip = addr[0]
                try:
                    # Update device IP in WiFi monitor
                    self.wifi_monitor.update_device_ip(device_id, sender_ip)
                except Exception as e:
                    logger.error(f"Error updating device IP in WiFi monitor: {e}")
            
            return result
        except Exception as e:
            logger.error(f"Error handling data: {e}")
            return False
    
    def start(self):
        """Start the data collector."""
        if self.running:
            logger.warning("Data collector is already running")
            return False
        
        try:
            # Start data server
            if not self.data_server.start():
                logger.error("Failed to start data server")
                return False
            
            # Start API server
            if not self.api_server.start():
                logger.error("Failed to start API server")
                self.data_server.stop()
                return False
            
            # Start cleanup thread
            self.running = True
            self.cleanup_thread = threading.Thread(target=self._cleanup_thread)
            self.cleanup_thread.daemon = True
            self.cleanup_thread.start()
            
            logger.info("Data collector started")
            return True
        except Exception as e:
            logger.error(f"Error starting data collector: {e}")
            return False
    
    def _cleanup_thread(self):
        """Thread to periodically clean up old files and rotate CSV files."""
        while self.running:
            try:
                # Sleep for a day
                for _ in range(24 * 60 * 60):
                    if not self.running:
                        break
                    time.sleep(1)
                
                if not self.running:
                    break
                
                # Rotate CSV files
                self.csv_manager.rotate_csv_files()
                
                # Clean up old files
                self.csv_manager.cleanup_old_files()
            except Exception as e:
                logger.error(f"Error in cleanup thread: {e}")
    
    def stop(self):
        """Stop the data collector."""
        if not self.running:
            logger.warning("Data collector is not running")
            return False
        
        try:
            # Set running flag to False
            self.running = False
            
            # Stop data server
            self.data_server.stop()
            
            # Stop API server
            self.api_server.stop()
            
            # Close CSV files
            self.csv_manager.close()
            
            # Wait for cleanup thread to finish
            if self.cleanup_thread and self.cleanup_thread.is_alive():
                self.cleanup_thread.join(timeout=5)
            
            logger.info("Data collector stopped")
            return True
        except Exception as e:
            logger.error(f"Error stopping data collector: {e}")
            return False

def main():
    """Main entry point for the data collection system."""
    parser = argparse.ArgumentParser(description='Data Collection System')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--data-dir', type=str, help='Data directory')
    parser.add_argument('--listen-port', type=int, help='Port to listen on')
    parser.add_argument('--api-port', type=int, help='Port for API server')
    args = parser.parse_args()
    
    # Load configuration
    config = DEFAULT_CONFIG.copy()
    
    # Override with command line arguments
    if args.data_dir:
        config["data_dir"] = args.data_dir
    if args.listen_port:
        config["listen_port"] = args.listen_port
    if args.api_port:
        config["api_port"] = args.api_port
    
    # Create and start data collector
    collector = DataCollector(config)
    if not collector.start():
        logger.error("Failed to start data collector")
        sys.exit(1)
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    finally:
        collector.stop()

if __name__ == "__main__":
    main()
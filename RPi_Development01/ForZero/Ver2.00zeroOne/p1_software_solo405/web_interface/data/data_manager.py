"""
Data Manager Module for Web Interface

This module contains functions for loading and processing data from CSV files.
"""

import os
import logging
import threading
import datetime
import pandas as pd
import requests

# Configure logging
logger = logging.getLogger(__name__)

class DataManager:
    """Class to handle data loading and processing."""

    def __init__(self, config):
        """
        Initialize the data manager with the given configuration.

        Args:
            config (dict): Configuration dictionary
        """
        self.config = config
        self.last_data = {}
        self.data_cache = {"P2": None, "P3": None}
        self.lock = threading.Lock()

    def get_latest_data(self):
        """
        Get the latest data from the API or cached data.

        Returns:
            dict: The latest data for all devices
        """
        try:
            # Try to get data from the API
            try:
                response = requests.get(f"{self.config['api_url']}/api/latest-data", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    with self.lock:
                        self.last_data = data
                    return data
            except Exception as e:
                logger.warning(f"Failed to get data from API: {e}")

            # If API fails, use cached data
            with self.lock:
                latest_data = self.last_data.copy()

            if not latest_data or len(latest_data) < 2:  # Check if we have data for both P2 and P3
                # If no data in cache, try to read from CSV
                today = datetime.datetime.now().strftime("%Y-%m-%d")

                for device in ["P2", "P3"]:
                    # Determine the appropriate directory for each device
                    device_dir = self.config["rawdata_p2_dir"] if device == "P2" else self.config["rawdata_p3_dir"]

                    # Try to read the fixed CSV file first
                    fixed_csv_path = os.path.join(self.config["data_dir"], device_dir, f"{device}_fixed.csv")
                    if os.path.exists(fixed_csv_path):
                        try:
                            df = pd.read_csv(fixed_csv_path)
                            if not df.empty:
                                # Get the latest row
                                latest_row = df.iloc[-1].to_dict()
                                with self.lock:
                                    self.last_data[device] = latest_row
                        except Exception as e:
                            logger.error(f"Error reading fixed CSV file for {device}: {e}")

                    # If fixed file doesn't exist or is empty, try the date-based file
                    if device not in self.last_data or not self.last_data[device]:
                        csv_path = os.path.join(self.config["data_dir"], device_dir, f"{device}_{today}.csv")
                        if os.path.exists(csv_path):
                            try:
                                df = pd.read_csv(csv_path)
                                if not df.empty:
                                    # Get the latest row
                                    latest_row = df.iloc[-1].to_dict()
                                    with self.lock:
                                        self.last_data[device] = latest_row
                            except Exception as e:
                                logger.error(f"Error reading CSV file for {device}: {e}")

                # Return the updated data
                with self.lock:
                    latest_data = self.last_data.copy()

            return latest_data
        except Exception as e:
            logger.error(f"Error getting latest data: {e}")
            return {}

    def get_historical_data(self, device_id, days=1):
        """
        Get historical data for the specified device.

        Args:
            device_id (str): The device ID to get data for
            days (int, optional): Number of days of data to retrieve. Defaults to 1.

        Returns:
            pandas.DataFrame: The historical data
        """
        try:
            # Check if we have cached data
            with self.lock:
                if self.data_cache[device_id] is not None:
                    logger.info(f"Using cached data for {device_id}")
                    return self.data_cache[device_id]

            # Determine the appropriate directory for the device
            device_dir = self.config["rawdata_p2_dir"] if device_id == "P2" else self.config["rawdata_p3_dir"]
            logger.info(f"Looking for {device_id} data in directory: {device_dir}")

            # Calculate the cutoff date
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
            logger.info(f"Cutoff date for {device_id} data: {cutoff_date}")

            # Try to read the fixed CSV file first
            fixed_csv_path = os.path.join(self.config["data_dir"], device_dir, f"{device_id}_fixed.csv")
            logger.info(f"Checking for fixed CSV file: {fixed_csv_path}")
            if os.path.exists(fixed_csv_path):
                logger.info(f"Fixed CSV file found for {device_id}: {fixed_csv_path}")
                try:
                    df = pd.read_csv(fixed_csv_path)
                    logger.info(f"Read {len(df)} rows from fixed CSV file for {device_id}")
                    if not df.empty:
                        # Convert timestamp to datetime
                        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                        logger.info(f"Converted timestamp to datetime for {device_id}")

                        # Filter by date
                        df = df[df['timestamp'] >= cutoff_date]
                        logger.info(f"Filtered data by date for {device_id}, {len(df)} rows remaining")

                        # Cache the data
                        with self.lock:
                            self.data_cache[device_id] = df

                        return df
                except Exception as e:
                    logger.error(f"Error reading fixed CSV file for {device_id}: {e}")
            else:
                logger.warning(f"Fixed CSV file not found for {device_id}: {fixed_csv_path}")

            # If fixed file doesn't exist or is empty, try the date-based files
            # Generate a list of dates to check
            date_list = []
            current_date = datetime.datetime.now()
            for i in range(days):
                date_str = (current_date - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
                date_list.append(date_str)
            logger.info(f"Checking date-based files for {device_id}: {date_list}")

            # Read data from each date file
            dfs = []
            for date_str in date_list:
                csv_path = os.path.join(self.config["data_dir"], device_dir, f"{device_id}_{date_str}.csv")
                logger.info(f"Checking for date-based CSV file: {csv_path}")
                if os.path.exists(csv_path):
                    logger.info(f"Date-based CSV file found for {device_id}: {csv_path}")
                    try:
                        df = pd.read_csv(csv_path)
                        logger.info(f"Read {len(df)} rows from date-based CSV file for {device_id} on {date_str}")
                        if not df.empty:
                            dfs.append(df)
                    except Exception as e:
                        logger.error(f"Error reading CSV file for {device_id} on {date_str}: {e}")
                else:
                    logger.warning(f"Date-based CSV file not found for {device_id} on {date_str}: {csv_path}")

            # Combine all dataframes
            if dfs:
                logger.info(f"Combining {len(dfs)} dataframes for {device_id}")
                df = pd.concat(dfs, ignore_index=True)
                logger.info(f"Combined dataframe has {len(df)} rows for {device_id}")

                # Convert timestamp to datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                logger.info(f"Converted timestamp to datetime for {device_id}")

                # Filter by date
                df = df[df['timestamp'] >= cutoff_date]
                logger.info(f"Filtered data by date for {device_id}, {len(df)} rows remaining")

                # Sort by timestamp
                df = df.sort_values('timestamp')
                logger.info(f"Sorted data by timestamp for {device_id}")

                # Cache the data
                with self.lock:
                    self.data_cache[device_id] = df

                return df
            else:
                logger.warning(f"No date-based CSV files found for {device_id}")

            # If no data found, return empty dataframe
            logger.warning(f"No data found for {device_id}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error getting historical data for {device_id}: {e}")
            return pd.DataFrame()

    def get_connection_status(self):
        """
        Get the connection status for all devices.

        Returns:
            dict: The connection status for all devices
        """
        try:
            # Try to get data from the monitor API
            try:
                response = requests.get(f"{self.config['monitor_api_url']}/api/status", timeout=2)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.warning(f"Failed to get connection status from API: {e}")

            # If API fails, return empty status
            return {
                "P2": {"online": False, "signal_strength": None, "noise_level": None, "ping_time": None},
                "P3": {"online": False, "signal_strength": None, "noise_level": None, "ping_time": None}
            }
        except Exception as e:
            logger.error(f"Error getting connection status: {e}")
            return {
                "P2": {"online": False, "signal_strength": None, "noise_level": None, "ping_time": None},
                "P3": {"online": False, "signal_strength": None, "noise_level": None, "ping_time": None}
            }

    def get_latest_device_data(self, device_id):
        """
        Get the latest data for the specified device.

        Args:
            device_id (str): The device ID to get data for

        Returns:
            dict: The latest data for the specified device
        """
        try:
            # Get the latest data for all devices
            all_data = self.get_latest_data()

            # Extract the data for the specified device
            if device_id in all_data:
                return all_data[device_id]
            else:
                logger.warning(f"No data found for device {device_id}")
                return None
        except Exception as e:
            logger.error(f"Error getting latest data for device {device_id}: {e}")
            return None

    def export_data_as_csv(self, device_id, start_date, end_date):
        """
        Export data as CSV for the specified device and date range.

        Args:
            device_id (str): The device ID to export data for
            start_date (datetime.datetime): Start date for the export
            end_date (datetime.datetime): End date for the export

        Returns:
            str: CSV data as a string
        """
        try:
            # Determine the appropriate directory for the device
            device_dir = self.config["rawdata_p2_dir"] if device_id == "P2" else self.config["rawdata_p3_dir"]

            # Generate a list of dates to check
            date_list = []
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                date_list.append(date_str)
                current_date += datetime.timedelta(days=1)

            # Read data from each date file
            dfs = []
            for date_str in date_list:
                csv_path = os.path.join(self.config["data_dir"], device_dir, f"{device_id}_{date_str}.csv")
                if os.path.exists(csv_path):
                    try:
                        df = pd.read_csv(csv_path)
                        if not df.empty:
                            dfs.append(df)
                    except Exception as e:
                        logger.error(f"Error reading CSV file for {device_id} on {date_str}: {e}")

            # Combine all dataframes
            if dfs:
                df = pd.concat(dfs, ignore_index=True)

                # Convert timestamp to datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

                # Filter by date range
                df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]

                # Sort by timestamp
                df = df.sort_values('timestamp')

                # Convert back to CSV
                return df.to_csv(index=False)

            # If no data found, return empty string
            return ""
        except Exception as e:
            logger.error(f"Error exporting data for {device_id}: {e}")
            return ""

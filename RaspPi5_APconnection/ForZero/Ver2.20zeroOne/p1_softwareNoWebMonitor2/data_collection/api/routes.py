"""
Routes Module for API

This module contains the API route handlers for the data collection system.
"""

import logging
import json
import datetime
import csv
import io
from flask import jsonify, request, Response

# Configure logging
logger = logging.getLogger(__name__)

class APIRoutes:
    """Class to handle API routes for the data collection system."""
    
    def __init__(self, app, data_store, config):
        """
        Initialize the API routes with the given Flask app and data store.
        
        Args:
            app (Flask): The Flask application
            data_store (DataStore): The data store
            config (dict): Configuration dictionary
        """
        self.app = app
        self.data_store = data_store
        self.config = config
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register API routes."""
        
        @self.app.route('/api/latest-data', methods=['GET'])
        def get_latest_data():
            """Get the latest data for all devices."""
            try:
                data = self.data_store.get_latest_data()
                return jsonify(data)
            except Exception as e:
                logger.error(f"Error getting latest data: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/device/<device_id>', methods=['GET'])
        def get_device_data(device_id):
            """Get the latest data for the specified device."""
            try:
                if device_id not in ["P1", "P2", "P3"]:
                    return jsonify({"error": f"Invalid device ID: {device_id}"}), 400
                
                data = self.data_store.get_latest_data(device_id)
                if data:
                    return jsonify(data)
                else:
                    return jsonify({"error": f"No data available for device {device_id}"}), 404
            except Exception as e:
                logger.error(f"Error getting data for device {device_id}: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/device/<device_id>/csv', methods=['GET'])
        def get_csv_data(device_id):
            """Get the data for the specified device as CSV."""
            try:
                if device_id not in ["P1", "P2", "P3"]:
                    return jsonify({"error": f"Invalid device ID: {device_id}"}), 400
                
                # Get date range from query parameters
                start_date = request.args.get('start_date')
                end_date = request.args.get('end_date')
                
                # Validate dates
                try:
                    if start_date:
                        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
                    else:
                        # Default to 7 days ago
                        start_date = datetime.datetime.now() - datetime.timedelta(days=7)
                    
                    if end_date:
                        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
                    else:
                        # Default to today
                        end_date = datetime.datetime.now()
                except ValueError as e:
                    return jsonify({"error": f"Invalid date format: {e}"}), 400
                
                # Create CSV in memory
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write header
                writer.writerow([
                    "timestamp", "device_id", "temperature", "humidity", 
                    "pressure", "gas_resistance", "co2", "absolute_humidity"
                ])
                
                # Determine the appropriate directory for the device
                if device_id == "P1":
                    device_dir = self.config.get("rawdata_p1_dir", "RawData_P1")
                elif device_id == "P2":
                    device_dir = self.config["rawdata_p2_dir"]
                else:
                    device_dir = self.config["rawdata_p3_dir"]
                
                # Generate a list of dates in the range
                current_date = start_date
                while current_date <= end_date:
                    date_str = current_date.strftime("%Y-%m-%d")
                    
                    # Try to open the CSV file for this date
                    try:
                        csv_path = f"{self.config['data_dir']}/{device_dir}/{device_id}_{date_str}.csv"
                        with open(csv_path, 'r') as f:
                            # Skip header
                            next(f)
                            # Copy data to output
                            for line in f:
                                writer.writerow(line.strip().split(','))
                    except FileNotFoundError:
                        # No data for this date, continue
                        pass
                    except Exception as e:
                        logger.error(f"Error reading CSV file for {device_id} on {date_str}: {e}")
                    
                    # Move to next day
                    current_date += datetime.timedelta(days=1)
                
                # Prepare response
                output.seek(0)
                return Response(
                    output.getvalue(),
                    mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment;filename={device_id}_data.csv"}
                )
            except Exception as e:
                logger.error(f"Error getting CSV data for device {device_id}: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            """Get the status of all devices."""
            try:
                status = self.data_store.get_all_devices_status()
                return jsonify(status)
            except Exception as e:
                logger.error(f"Error getting device status: {e}")
                return jsonify({"error": str(e)}), 500
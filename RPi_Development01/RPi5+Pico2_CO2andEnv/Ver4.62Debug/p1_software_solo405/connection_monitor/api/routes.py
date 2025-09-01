"""
API Routes Module for Connection Monitor

This module contains functions for setting up API routes for the connection monitor.
"""

import logging
from flask import jsonify, request

logger = logging.getLogger(__name__)

def setup_api_routes(app, connection_data, lock):
    """
    Set up API routes for data access.
    
    Args:
        app (Flask): The Flask application
        connection_data (dict): Dictionary containing connection data
        lock (threading.Lock): Lock for thread-safe access to connection_data
    """
    @app.route('/api/connection/latest', methods=['GET'])
    def get_latest_data():
        """Get the latest connection data for all devices."""
        with lock:
            latest_data = {
                device_id: data.get("latest", {})
                for device_id, data in connection_data.items()
            }
            return jsonify(latest_data)

    @app.route('/api/connection/device/<device_id>', methods=['GET'])
    def get_device_data(device_id):
        """Get the latest connection data for a specific device."""
        if device_id not in ["P2", "P3"]:  # Ver4.0 accepts both P2 and P3
            return jsonify({"error": "Invalid device ID"}), 400

        with lock:
            if device_id in connection_data and "latest" in connection_data[device_id]:
                return jsonify(connection_data[device_id]["latest"])
            else:
                return jsonify({"error": "No data available for this device"}), 404

    @app.route('/api/connection/history/<device_id>', methods=['GET'])
    def get_device_history(device_id):
        """Get the connection history for a specific device."""
        if device_id not in ["P2", "P3"]:  # Ver4.0 accepts both P2 and P3
            return jsonify({"error": "Invalid device ID"}), 400

        # Get optional limit parameter
        limit = request.args.get('limit', default=None, type=int)

        with lock:
            if device_id in connection_data:
                history = connection_data[device_id]["history"]

                if limit and limit > 0:
                    history = history[-limit:]

                return jsonify(history)
            else:
                return jsonify({"error": "No data available for this device"}), 404
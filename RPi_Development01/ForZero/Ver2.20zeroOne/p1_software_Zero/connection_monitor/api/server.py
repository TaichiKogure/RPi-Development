"""
API Server Module for Connection Monitor

This module contains functions for running the API server for the connection monitor.
"""

import logging
from flask import Flask

from .routes import setup_api_routes

logger = logging.getLogger(__name__)

def create_api_app(connection_data, lock):
    """
    Create a Flask application for the API server.
    
    Args:
        connection_data (dict): Dictionary containing connection data
        lock (threading.Lock): Lock for thread-safe access to connection_data
        
    Returns:
        Flask: The Flask application
    """
    app = Flask(__name__)
    setup_api_routes(app, connection_data, lock)
    return app

def run_api_server(app, port):
    """
    Run the API server.
    
    Args:
        app (Flask): The Flask application
        port (int): The port to run the server on
    """
    app.run(host='0.0.0.0', port=port)
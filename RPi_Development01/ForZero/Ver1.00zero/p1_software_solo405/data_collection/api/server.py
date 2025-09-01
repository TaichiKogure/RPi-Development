"""
Server Module for API

This module contains the Flask server setup for the data collection API.
"""

import logging
import threading
from flask import Flask

# Configure logging
logger = logging.getLogger(__name__)

class APIServer:
    """Class to manage the Flask server for the data collection API."""
    
    def __init__(self, config, data_store):
        """
        Initialize the API server with the given configuration.
        
        Args:
            config (dict): Configuration dictionary
            data_store (DataStore): The data store
        """
        self.config = config
        self.data_store = data_store
        self.app = Flask(__name__)
        self.thread = None
        self.running = False
    
    def setup_routes(self):
        """Set up API routes."""
        from p1_software_solo405.data_collection.api.routes import APIRoutes
        self.routes = APIRoutes(self.app, self.data_store, self.config)
        logger.info("API routes set up")
    
    def start(self):
        """Start the API server."""
        if self.running:
            logger.warning("API server is already running")
            return False
        
        try:
            # Set up routes
            self.setup_routes()
            
            # Set running flag
            self.running = True
            
            # Start server thread
            self.thread = threading.Thread(target=self._run_server)
            self.thread.daemon = True
            self.thread.start()
            
            logger.info(f"API server started on port {self.config['api_port']}")
            return True
        except Exception as e:
            logger.error(f"Error starting API server: {e}")
            return False
    
    def _run_server(self):
        """Run the Flask server."""
        try:
            self.app.run(
                host='0.0.0.0',
                port=self.config['api_port'],
                debug=False,
                use_reloader=False,
                threaded=True
            )
        except Exception as e:
            logger.error(f"Error running API server: {e}")
            self.running = False
    
    def stop(self):
        """Stop the API server."""
        if not self.running:
            logger.warning("API server is not running")
            return False
        
        try:
            # Set running flag to False
            self.running = False
            
            # Shut down the Flask server
            # Note: This is a bit tricky with Flask, as it doesn't have a clean shutdown method
            # We'll rely on the thread being a daemon thread, which will be terminated when the main thread exits
            
            logger.info("API server stopped")
            return True
        except Exception as e:
            logger.error(f"Error stopping API server: {e}")
            return False
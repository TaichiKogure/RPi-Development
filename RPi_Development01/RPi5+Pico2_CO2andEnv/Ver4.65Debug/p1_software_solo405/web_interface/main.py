"""
Main Module for Web Interface

This module provides the main entry point for the web interface.
It integrates all the components (data, visualization, api) to provide
a web interface for visualizing environmental data.
"""

import os
import sys
import argparse
import logging
import threading
from flask import Flask, render_template, send_from_directory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/web_interface_solo.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import components
from p1_software_solo405.web_interface.config import DEFAULT_CONFIG, ensure_data_directories
from p1_software_solo405.web_interface.data.data_manager import DataManager
from p1_software_solo405.web_interface.visualization.graph_generator import GraphGenerator
from p1_software_solo405.web_interface.api.routes import APIRoutes

# Import create_templates function from P1_app_solo.py
try:
    from p1_software_solo405.web_interface.P1_app_solo import create_templates
    logger.info("Successfully imported create_templates from P1_app_solo")
except ImportError as e:
    logger.warning(f"Failed to import create_templates from P1_app_solo: {e}")
    # Define a fallback create_templates function
    def create_templates():
        """Create basic templates if P1_app_solo.create_templates is not available."""
        templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
        os.makedirs(templates_dir, exist_ok=True)

        # Create a basic index.html template
        index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Environmental Data Monitor - Solo</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
</head>
<body>
    <div class="container">
        <h1>Environmental Data Monitor - Solo</h1>
        <p>Welcome to the Environmental Data Monitor. Please use the navigation to view data.</p>
    </div>
</body>
</html>"""

        with open(os.path.join(templates_dir, 'index.html'), 'w') as f:
            f.write(index_html)

        logger.info("Created basic templates as fallback")

# Logger is already configured at the top of the file

class WebInterface:
    """Class to handle the web interface."""

    def __init__(self, config=None):
        """
        Initialize the web interface with the given configuration.

        Args:
            config (dict, optional): Configuration dictionary. Defaults to None.
        """
        self.config = config or DEFAULT_CONFIG.copy()

        # Ensure data directories exist
        ensure_data_directories(self.config)

        # Initialize Flask app
        self.app = Flask(
            __name__,
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), 'static')
        )

        # Initialize components
        self.data_manager = DataManager(self.config)
        self.graph_generator = GraphGenerator(self.config)

        # Register routes
        self._register_routes()
        self.api_routes = APIRoutes(self.app, self.data_manager, self.graph_generator)

    def _register_routes(self):
        """Register web interface routes."""

        @self.app.route('/')
        def index():
            """Render the index page."""
            return render_template('index.html', refresh_interval=self.config.get('refresh_interval', 10))

        @self.app.route('/dashboard')
        def dashboard():
            """Render the dashboard page."""
            return render_template('dashboard.html', refresh_interval=self.config.get('refresh_interval', 10))

        @self.app.route('/favicon.ico')
        def favicon():
            """Serve the favicon."""
            return send_from_directory(
                os.path.join(self.app.static_folder, 'img'),
                'favicon.ico',
                mimetype='image/vnd.microsoft.icon'
            )

    def run(self):
        """Run the web interface."""
        try:
            self.app.run(
                host='0.0.0.0',
                port=self.config['web_port'],
                debug=self.config['debug_mode']
            )
        except Exception as e:
            logger.error(f"Error running web interface: {e}")
            return False

        return True

def main():
    """Main entry point for the web interface."""
    parser = argparse.ArgumentParser(description='Web Interface')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--port', type=int, help='Port to listen on')
    parser.add_argument('--data-dir', type=str, help='Data directory')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    # Load configuration
    config = DEFAULT_CONFIG.copy()

    # Override with command line arguments
    if args.port:
        config['web_port'] = args.port
    if args.data_dir:
        config['data_dir'] = args.data_dir
    if args.debug:
        config['debug_mode'] = True

    # Create templates
    try:
        logger.info("Creating templates...")
        create_templates()
        logger.info("Templates created successfully")
    except Exception as e:
        logger.error(f"Error creating templates: {e}")
        # Continue anyway, as the templates might already exist

    # Create and run web interface
    web_interface = WebInterface(config)
    if not web_interface.run():
        logger.error("Failed to run web interface")
        sys.exit(1)

if __name__ == "__main__":
    main()

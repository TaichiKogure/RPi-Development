"""
Routes Module for Web Interface API

This module contains functions for handling API routes.
"""

import logging
import datetime
from flask import jsonify, request, send_file, Response
import io

# Configure logging
logger = logging.getLogger(__name__)

class APIRoutes:
    """Class to handle API routes for the web interface."""
    
    def __init__(self, app, data_manager, graph_generator):
        """
        Initialize the API routes with the given Flask app and data manager.
        
        Args:
            app (Flask): The Flask application
            data_manager (DataManager): The data manager
            graph_generator (GraphGenerator): The graph generator
        """
        self.app = app
        self.data_manager = data_manager
        self.graph_generator = graph_generator
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register API routes."""
        
        @self.app.route('/api/latest-data', methods=['GET'])
        def get_latest_data():
            """Get the latest data for all devices."""
            try:
                data = self.data_manager.get_latest_data()
                return jsonify(data)
            except Exception as e:
                logger.error(f"Error getting latest data: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/data/<parameter>', methods=['GET'])
        def get_graph_data(parameter):
            """Get graph data for the specified parameter."""
            try:
                # Get query parameters
                days = request.args.get('days', default=1, type=int)
                show_p2 = request.args.get('show_p2', default='true').lower() == 'true'
                show_p3 = request.args.get('show_p3', default='true').lower() == 'true'
                
                # Get historical data
                df_p2 = self.data_manager.get_historical_data("P2", days) if show_p2 else None
                df_p3 = self.data_manager.get_historical_data("P3", days) if show_p3 else None
                
                # Create graph
                graph_json = self.graph_generator.create_time_series_graph(df_p2, df_p3, parameter, show_p2, show_p3)
                
                return graph_json
            except Exception as e:
                logger.error(f"Error getting graph data for {parameter}: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/dashboard', methods=['GET'])
        def get_dashboard():
            """Get dashboard data for all parameters."""
            try:
                # Get query parameters
                days = request.args.get('days', default=1, type=int)
                show_p2 = request.args.get('show_p2', default='true').lower() == 'true'
                show_p3 = request.args.get('show_p3', default='true').lower() == 'true'
                
                # Get historical data
                df_p2 = self.data_manager.get_historical_data("P2", days) if show_p2 else None
                df_p3 = self.data_manager.get_historical_data("P3", days) if show_p3 else None
                
                # Create dashboard
                dashboard = self.graph_generator.create_dashboard_graphs(df_p2, df_p3, show_p2, show_p3)
                
                return jsonify(dashboard)
            except Exception as e:
                logger.error(f"Error getting dashboard data: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/combined-dashboard', methods=['GET'])
        def get_combined_dashboard():
            """Get combined dashboard data for all parameters."""
            try:
                # Get query parameters
                days = request.args.get('days', default=1, type=int)
                show_p2 = request.args.get('show_p2', default='true').lower() == 'true'
                show_p3 = request.args.get('show_p3', default='true').lower() == 'true'
                
                # Get historical data
                df_p2 = self.data_manager.get_historical_data("P2", days) if show_p2 else None
                df_p3 = self.data_manager.get_historical_data("P3", days) if show_p3 else None
                
                # Create combined dashboard
                dashboard = self.graph_generator.create_combined_dashboard(df_p2, df_p3, show_p2, show_p3)
                
                return dashboard
            except Exception as e:
                logger.error(f"Error getting combined dashboard data: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/connection/status', methods=['GET'])
        def get_connection_status():
            """Get the connection status for all devices."""
            try:
                status = self.data_manager.get_connection_status()
                return jsonify(status)
            except Exception as e:
                logger.error(f"Error getting connection status: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/export/csv/<device_id>', methods=['GET'])
        def export_csv(device_id):
            """Export data as CSV for the specified device."""
            try:
                # Validate device ID
                if device_id not in ["P2", "P3"]:
                    return jsonify({"error": f"Invalid device ID: {device_id}"}), 400
                
                # Get date range from query parameters
                start_date_str = request.args.get('start_date')
                end_date_str = request.args.get('end_date')
                
                # Parse dates
                try:
                    if start_date_str:
                        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
                    else:
                        # Default to 7 days ago
                        start_date = datetime.datetime.now() - datetime.timedelta(days=7)
                    
                    if end_date_str:
                        end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")
                    else:
                        # Default to today
                        end_date = datetime.datetime.now()
                except ValueError as e:
                    return jsonify({"error": f"Invalid date format: {e}"}), 400
                
                # Export data
                csv_data = self.data_manager.export_data_as_csv(device_id, start_date, end_date)
                
                # Create response
                return Response(
                    csv_data,
                    mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment;filename={device_id}_data.csv"}
                )
            except Exception as e:
                logger.error(f"Error exporting CSV for {device_id}: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/latest-data-table', methods=['GET'])
        def get_latest_data_table():
            """Get the latest data as an HTML table."""
            try:
                # Get latest data
                latest_data = self.data_manager.get_latest_data()
                
                # Create table
                table_html = self.graph_generator.create_latest_data_table(latest_data)
                
                return table_html
            except Exception as e:
                logger.error(f"Error getting latest data table: {e}")
                return f"<p>Error: {str(e)}</p>", 500
        
        @self.app.route('/api/connection-status-table', methods=['GET'])
        def get_connection_status_table():
            """Get the connection status as an HTML table."""
            try:
                # Get connection status
                connection_status = self.data_manager.get_connection_status()
                
                # Create table
                table_html = self.graph_generator.create_connection_status_table(connection_status)
                
                return table_html
            except Exception as e:
                logger.error(f"Error getting connection status table: {e}")
                return f"<p>Error: {str(e)}</p>", 500
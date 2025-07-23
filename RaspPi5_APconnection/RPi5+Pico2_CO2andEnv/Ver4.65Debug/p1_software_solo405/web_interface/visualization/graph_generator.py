"""
Graph Generator Module for Web Interface

This module contains functions for generating graphs and visualizations.
"""

import logging
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configure logging
logger = logging.getLogger(__name__)

class GraphGenerator:
    """Class to handle graph generation."""

    def __init__(self, config):
        """
        Initialize the graph generator with the given configuration.

        Args:
            config (dict): Configuration dictionary
        """
        self.config = config

    def create_time_series_graph(self, df_p2, df_p3, parameter, show_p2=True, show_p3=True):
        """
        Create a time series graph for the specified parameter.

        Args:
            df_p2 (pandas.DataFrame): Data for P2
            df_p3 (pandas.DataFrame): Data for P3
            parameter (str): The parameter to plot
            show_p2 (bool, optional): Whether to show P2 data. Defaults to True.
            show_p3 (bool, optional): Whether to show P3 data. Defaults to True.

        Returns:
            str: JSON representation of the graph
        """
        try:
            # Check if we have any data to plot
            if (df_p2 is None or df_p2.empty) and (df_p3 is None or df_p3.empty):
                logger.warning(f"No data available for {parameter}")
                return json.dumps({"error": f"No data available for {parameter}"})

            # Create figure
            fig = go.Figure()

            # Add P2 data if available and requested
            if show_p2 and df_p2 is not None and not df_p2.empty and parameter in df_p2.columns:
                # Log data range for debugging
                logger.info(f"Adding P2 data for {parameter}: {len(df_p2)} points, range: {df_p2[parameter].min()} - {df_p2[parameter].max()}")

                fig.add_trace(go.Scatter(
                    x=df_p2['timestamp'],
                    y=df_p2[parameter],
                    mode='lines',
                    name=f'P2 {parameter.capitalize()}',
                    line=dict(color='blue')
                ))

            # Add P3 data if available and requested
            if show_p3 and df_p3 is not None and not df_p3.empty and parameter in df_p3.columns:
                # Log data range for debugging
                logger.info(f"Adding P3 data for {parameter}: {len(df_p3)} points, range: {df_p3[parameter].min()} - {df_p3[parameter].max()}")

                fig.add_trace(go.Scatter(
                    x=df_p3['timestamp'],
                    y=df_p3[parameter],
                    mode='lines',
                    name=f'P3 {parameter.capitalize()}',
                    line=dict(color='red')
                ))

            # Check if we have any traces
            if not fig.data:
                logger.warning(f"No valid data to plot for {parameter}")
                return json.dumps({"error": f"No valid data to plot for {parameter}"})

            # Update layout
            fig.update_layout(
                title=f"{parameter.capitalize()} over time",
                xaxis_title="Time",
                yaxis_title=parameter.capitalize(),
                margin=dict(l=20, r=20, t=40, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                hovermode='closest',
                yaxis=dict(
                    autorange=True,
                    rangemode='normal'
                ),
                xaxis=dict(
                    type='date'
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )

            # Convert to JSON
            return fig.to_json()
        except Exception as e:
            logger.error(f"Error creating graph for {parameter}: {e}")
            return json.dumps({"error": f"Graph creation failed: {e}"})

    def create_dashboard_graphs(self, df_p2, df_p3, show_p2=True, show_p3=True):
        """
        Create a dashboard with all parameters.

        Args:
            df_p2 (pandas.DataFrame): Data for P2
            df_p3 (pandas.DataFrame): Data for P3
            show_p2 (bool, optional): Whether to show P2 data. Defaults to True.
            show_p3 (bool, optional): Whether to show P3 data. Defaults to True.

        Returns:
            dict: Dictionary of graph JSONs
        """
        try:
            # Define parameters to plot
            parameters = ["temperature", "humidity", "absolute_humidity", "co2", "pressure", "gas_resistance"]

            # Create graphs for each parameter
            graphs = {}
            for parameter in parameters:
                graph_json = self.create_time_series_graph(df_p2, df_p3, parameter, show_p2, show_p3)
                graphs[parameter] = graph_json

            return graphs
        except Exception as e:
            logger.error(f"Error creating dashboard graphs: {e}")
            return {}

    def create_combined_dashboard(self, df_p2, df_p3, show_p2=True, show_p3=True):
        """
        Create a combined dashboard with all parameters in a single figure.

        Args:
            df_p2 (pandas.DataFrame): Data for P2
            df_p3 (pandas.DataFrame): Data for P3
            show_p2 (bool, optional): Whether to show P2 data. Defaults to True.
            show_p3 (bool, optional): Whether to show P3 data. Defaults to True.

        Returns:
            str: JSON representation of the combined dashboard
        """
        try:
            # Check if we have any data to plot
            if (df_p2 is None or df_p2.empty) and (df_p3 is None or df_p3.empty):
                logger.warning("No data available for dashboard")
                return json.dumps({"error": "No data available for dashboard"})

            # Define parameters to plot
            parameters = ["temperature", "humidity", "absolute_humidity", "co2", "pressure", "gas_resistance"]

            # Create a subplot figure with 3x2 grid
            fig = make_subplots(
                rows=3, cols=2,
                subplot_titles=[
                    "Temperature (°C)", "Humidity (%)",
                    "Absolute Humidity (g/m³)", "CO2 (ppm)",
                    "Pressure (hPa)", "Gas Resistance (Ω)"
                ],
                vertical_spacing=0.1,
                horizontal_spacing=0.05
            )

            # Map parameters to subplot positions
            param_positions = {
                "temperature": (1, 1),
                "humidity": (1, 2),
                "absolute_humidity": (2, 1),
                "co2": (2, 2),
                "pressure": (3, 1),
                "gas_resistance": (3, 2)
            }

            # Add traces for each parameter
            for param, (row, col) in param_positions.items():
                # Add P2 data if available and requested
                if show_p2 and df_p2 is not None and not df_p2.empty and param in df_p2.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=df_p2['timestamp'],
                            y=df_p2[param],
                            mode='lines',
                            name=f'P2 {param.capitalize()}',
                            line=dict(color='blue')
                        ),
                        row=row, col=col
                    )

                # Add P3 data if available and requested
                if show_p3 and df_p3 is not None and not df_p3.empty and param in df_p3.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=df_p3['timestamp'],
                            y=df_p3[param],
                            mode='lines',
                            name=f'P3 {param.capitalize()}',
                            line=dict(color='red')
                        ),
                        row=row, col=col
                    )

            # Update layout
            fig.update_layout(
                title="Environmental Data Dashboard",
                height=900,
                width=1200,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )

            # Update all X-axes to be date type
            for i in range(1, 4):
                for j in range(1, 3):
                    fig.update_xaxes(
                        type='date',
                        tickformat='%Y-%m-%d %H:%M',
                        tickangle=-45,
                        row=i, col=j
                    )

            # Convert to JSON
            return fig.to_json()
        except Exception as e:
            logger.error(f"Error creating combined dashboard: {e}")
            return json.dumps({"error": f"Dashboard creation failed: {e}"})

    def create_latest_data_table(self, latest_data):
        """
        Create a table with the latest data.

        Args:
            latest_data (dict): The latest data for all devices

        Returns:
            str: HTML representation of the table
        """
        try:
            # Check if we have any data
            if not latest_data:
                return "<p>No data available</p>"

            # Create table
            html = "<table class='table table-striped'>"
            html += "<thead><tr><th>Parameter</th><th>P2</th><th>P3</th></tr></thead>"
            html += "<tbody>"

            # Define parameters to display
            parameters = [
                ("timestamp", "Timestamp"),
                ("temperature", "Temperature (°C)"),
                ("humidity", "Humidity (%)"),
                ("absolute_humidity", "Absolute Humidity (g/m³)"),
                ("co2", "CO2 (ppm)"),
                ("pressure", "Pressure (hPa)"),
                ("gas_resistance", "Gas Resistance (Ω)")
            ]

            # Add rows for each parameter
            for param, label in parameters:
                html += f"<tr><td>{label}</td>"

                # Add P2 data
                if "P2" in latest_data and param in latest_data["P2"]:
                    html += f"<td>{latest_data['P2'][param]}</td>"
                else:
                    html += "<td>-</td>"

                # Add P3 data
                if "P3" in latest_data and param in latest_data["P3"]:
                    html += f"<td>{latest_data['P3'][param]}</td>"
                else:
                    html += "<td>-</td>"

                html += "</tr>"

            html += "</tbody></table>"
            return html
        except Exception as e:
            logger.error(f"Error creating latest data table: {e}")
            return "<p>Error creating table</p>"

    def create_connection_status_table(self, connection_status):
        """
        Create a table with the connection status.

        Args:
            connection_status (dict): The connection status for all devices

        Returns:
            str: HTML representation of the table
        """
        try:
            # Check if we have any data
            if not connection_status:
                return "<p>No connection status available</p>"

            # Create table
            html = "<table class='table table-striped'>"
            html += "<thead><tr><th>Device</th><th>Status</th><th>Signal Strength</th><th>Noise Level</th><th>SNR</th><th>Ping Time</th></tr></thead>"
            html += "<tbody>"

            # Add rows for each device
            for device in ["P2", "P3"]:
                if device in connection_status:
                    status = connection_status[device]

                    # Determine status class
                    status_class = "success" if status.get("online", False) else "danger"

                    html += f"<tr class='table-{status_class}'>"
                    html += f"<td>{device}</td>"
                    html += f"<td>{'Online' if status.get('online', False) else 'Offline'}</td>"
                    html += f"<td>{status.get('signal_strength', '-')} dBm</td>"
                    html += f"<td>{status.get('noise_level', '-')} dBm</td>"
                    html += f"<td>{status.get('snr', '-')} dB</td>"
                    html += f"<td>{status.get('ping_time', '-')} ms</td>"
                    html += "</tr>"
                else:
                    html += f"<tr class='table-danger'><td>{device}</td><td>Unknown</td><td>-</td><td>-</td><td>-</td><td>-</td></tr>"

            html += "</tbody></table>"
            return html
        except Exception as e:
            logger.error(f"Error creating connection status table: {e}")
            return "<p>Error creating table</p>"

    def generate_graph_data(self, days=1, show_p2=True, show_p3=True):
        """
        Generate structured data for graphs.

        Args:
            days (int, optional): Number of days of data to retrieve. Defaults to 1.
            show_p2 (bool, optional): Whether to include P2 data. Defaults to True.
            show_p3 (bool, optional): Whether to include P3 data. Defaults to True.

        Returns:
            dict: Structured data for graphs
        """
        try:
            # Get historical data
            try:
                # Try relative import first
                from ..data.data_manager import DataManager
                data_manager = DataManager(self.config)
                logger.info("Successfully imported DataManager using relative import")
            except ImportError:
                # Fall back to absolute import if relative import fails
                try:
                    from p1_software_solo405.web_interface.data.data_manager import DataManager
                    data_manager = DataManager(self.config)
                    logger.info("Successfully imported DataManager using absolute import with p1_software_solo405 prefix")
                except ImportError:
                    # Try another absolute import path as a last resort
                    from web_interface.data.data_manager import DataManager
                    data_manager = DataManager(self.config)
                    logger.info("Successfully imported DataManager using absolute import")

            df_p2 = data_manager.get_historical_data("P2", days) if show_p2 else None
            df_p3 = data_manager.get_historical_data("P3", days) if show_p3 else None

            # Check if we have any data
            if (df_p2 is None or df_p2.empty) and (df_p3 is None or df_p3.empty):
                logger.warning("No data available for graphs")
                return {}

            # Define parameters
            parameters = ["temperature", "humidity", "absolute_humidity", "co2", "pressure", "gas_resistance"]

            # Initialize result dictionary
            result = {}

            # Process P2 data if available
            if show_p2 and df_p2 is not None and not df_p2.empty:
                # Convert timestamp to list for JSON serialization
                timestamps = df_p2['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()

                # Create data structure for P2
                p2_data = {
                    'timestamp': timestamps
                }

                # Add data for each parameter
                for param in parameters:
                    if param in df_p2.columns:
                        p2_data[param] = df_p2[param].tolist()

                # Add to result
                result['P2'] = p2_data

            # Process P3 data if available
            if show_p3 and df_p3 is not None and not df_p3.empty:
                # Convert timestamp to list for JSON serialization
                timestamps = df_p3['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()

                # Create data structure for P3
                p3_data = {
                    'timestamp': timestamps
                }

                # Add data for each parameter
                for param in parameters:
                    if param in df_p3.columns:
                        p3_data[param] = df_p3[param].tolist()

                # Add to result
                result['P3'] = p3_data

            return result
        except Exception as e:
            logger.error(f"Error generating graph data: {e}")
            return {}

"""
Graph Generator Module for Web Interface

This module contains functions for generating graphs and visualizations.
"""

import os
import logging
import json
import datetime
import pandas as pd
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

    def create_time_series_graph(self, df_p1, df_p2, df_p3, parameter, show_p1=True, show_p2=True, show_p3=True):
        """
        Create a time series graph for the specified parameter.

        Args:
            df_p1 (pandas.DataFrame): Data for P1
            df_p2 (pandas.DataFrame): Data for P2
            df_p3 (pandas.DataFrame): Data for P3
            parameter (str): The parameter to plot
            show_p1 (bool, optional): Whether to show P1 data. Defaults to True.
            show_p2 (bool, optional): Whether to show P2 data. Defaults to True.
            show_p3 (bool, optional): Whether to show P3 data. Defaults to True.

        Returns:
            str: JSON representation of the graph
        """
        try:
            # Check if we have any data to plot
            if ((df_p1 is None or df_p1.empty) and
                (df_p2 is None or df_p2.empty) and
                (df_p3 is None or df_p3.empty)):
                logger.warning(f"No data available for {parameter}")
                return json.dumps({"error": f"No data available for {parameter}"})

            # Create figure
            fig = go.Figure()

            # Add P1 data if available and requested
            if show_p1 and df_p1 is not None and not df_p1.empty and parameter in df_p1.columns:
                logger.info(f"Adding P1 data for {parameter}: {len(df_p1)} points, range: {df_p1[parameter].min()} - {df_p1[parameter].max()}")
                fig.add_trace(go.Scatter(
                    x=df_p1['timestamp'],
                    y=df_p1[parameter],
                    mode='lines',
                    name=f'P1 {parameter.capitalize()}',
                    line=dict(color='green')
                ))

            # Add P2 data if available and requested
            if show_p2 and df_p2 is not None and not df_p2.empty and parameter in df_p2.columns:
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

            return fig.to_json()
        except Exception as e:
            logger.error(f"Error creating graph for {parameter}: {e}")
            return json.dumps({"error": f"Graph creation failed: {e}"})

    def create_dashboard_graphs(self, df_p1, df_p2, df_p3, show_p1=True, show_p2=True, show_p3=True):
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
                graph_json = self.create_time_series_graph(df_p1, df_p2, df_p3, parameter, show_p1, show_p2, show_p3)
                graphs[parameter] = graph_json

            return graphs
        except Exception as e:
            logger.error(f"Error creating dashboard graphs: {e}")
            return {}

    def create_combined_dashboard(self, df_p1, df_p2, df_p3, show_p1=True, show_p2=True, show_p3=True):
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
                # Add P1 data if available and requested
                if show_p1 and df_p1 is not None and not df_p1.empty and param in df_p1.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=df_p1['timestamp'],
                            y=df_p1[param],
                            mode='lines',
                            name=f'P1 {param.capitalize()}',
                            line=dict(color='green')
                        ),
                        row=row, col=col
                    )

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
            html += "<thead><tr><th>Parameter</th><th>P1</th><th>P2</th><th>P3</th></tr></thead>"
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

                # Add P1 data
                if "P1" in latest_data and param in latest_data["P1"]:
                    html += f"<td>{latest_data['P1'][param]}</td>"
                else:
                    html += "<td>-</td>"

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
            for device in ["P1", "P2", "P3"]:
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

    def generate_graph_data(self, days=1, show_p1=True, show_p2=True, show_p3=True):
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
            # Calculate the cutoff date
            cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
            logger.info(f"Cutoff date for data: {cutoff}")

            def load_latest_fixed_csv(device_id):
                """
                Load the latest fixed CSV file for the specified device.

                Args:
                    device_id (str): The device ID to load data for (P2 or P3)

                Returns:
                    pandas.DataFrame: The loaded data, or None if no data found
                """
                # Determine the appropriate directory for the device
                device_dir = f"RawData_{device_id}"
                folder = os.path.join(self.config["data_dir"], device_dir)
                logger.info(f"Looking for fixed CSVs in: {folder}")

                # Check if the directory exists
                if not os.path.isdir(folder):
                    logger.warning(f"Directory not found: {folder}")
                    return None

                # Find all *_fixed.csv files in the directory
                candidates = [f for f in os.listdir(folder) if f.endswith("_fixed.csv")]
                if not candidates:
                    logger.warning(f"No _fixed.csv files in {folder}")
                    return None

                # Get the latest file based on modification time
                latest_file = max(candidates, key=lambda f: os.path.getmtime(os.path.join(folder, f)))
                logger.info(f"Latest fixed CSV file for {device_id}: {latest_file}")

                try:
                    # Read the CSV file
                    file_path = os.path.join(folder, latest_file)
                    logger.info(f"Reading CSV file: {file_path}")
                    df = pd.read_csv(file_path)
                    logger.info(f"Read {len(df)} rows from {file_path}")

                    if not df.empty:
                        # Convert timestamp to datetime - handle both numeric and string formats
                        if df['timestamp'].dtype == 'int64' or df['timestamp'].dtype == 'float64':
                            logger.info(f"Detected numeric timestamp format for {device_id}")
                            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
                        else:
                            logger.info(f"Detected string timestamp format for {device_id}")
                            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

                        # Drop rows with invalid timestamps
                        df = df.dropna(subset=['timestamp'])
                        logger.info(f"Converted timestamp to datetime for {device_id}, {len(df)} valid rows")

                        # Filter by date
                        df = df[df['timestamp'] > cutoff]
                        logger.info(f"Filtered data by date for {device_id}, {len(df)} rows remaining")

                        return df
                    else:
                        logger.warning(f"CSV file is empty: {file_path}")
                        return None
                except Exception as e:
                    logger.error(f"Error loading {latest_file}: {e}")
                    return None

            # Load data for P1, P2 and P3
            df_p1 = load_latest_fixed_csv("P1") if show_p1 else None
            df_p2 = load_latest_fixed_csv("P2") if show_p2 else None
            df_p3 = load_latest_fixed_csv("P3") if show_p3 else None

            # Check if we have any data
            if ((df_p1 is None or df_p1.empty) and
                (df_p2 is None or df_p2.empty) and
                (df_p3 is None or df_p3.empty)):
                logger.warning("No data available for graphs")
                return {}

            # Define parameters
            parameters = ["temperature", "humidity", "absolute_humidity", "co2", "pressure", "gas_resistance"]

            # Initialize result dictionary
            result = {}

            # Process P1 data if available
            if show_p1 and df_p1 is not None and not df_p1.empty:
                timestamps = df_p1['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
                p1_data = {
                    'timestamp': timestamps
                }
                for param in parameters:
                    if param in df_p1.columns:
                        p1_data[param] = df_p1[param].tolist()
                    else:
                        logger.warning(f"Parameter {param} not found in P1 data")
                        p1_data[param] = []
                result['P1'] = p1_data
                logger.info(f"Added P1 data with {len(timestamps)} points")

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
                    else:
                        logger.warning(f"Parameter {param} not found in P2 data")
                        p2_data[param] = []

                # Add to result
                result['P2'] = p2_data
                logger.info(f"Added P2 data with {len(timestamps)} points")

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
                    else:
                        logger.warning(f"Parameter {param} not found in P3 data")
                        p3_data[param] = []

                # Add to result
                result['P3'] = p3_data
                logger.info(f"Added P3 data with {len(timestamps)} points")

            logger.info(f"Returning graph data with keys: {list(result.keys())}")
            return result
        except Exception as e:
            logger.error(f"Error generating graph data: {e}")
            return {}

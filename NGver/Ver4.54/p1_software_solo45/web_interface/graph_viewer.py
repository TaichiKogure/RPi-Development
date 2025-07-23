#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Environmental Data Visualization Tool
Version: 4.53

This script provides a command-line tool for visualizing environmental data
collected from P2 and P3 sensor nodes. It reads data from CSV files and
generates interactive graphs using Plotly.

Features:
- Read data from CSV files for P2 and P3 sensor nodes
- Filter data by time range (days)
- Generate individual graphs for each parameter
- Create a dashboard with all parameters
- Save graphs to HTML files or display in browser
- Toggle display of P2 and P3 data

Usage:
    python graph_viewer_Ver4.py [options]

Options:
    --p2-path PATH     Path to P2 CSV data file
    --p3-path PATH     Path to P3 CSV data file
    --days DAYS        Number of days of data to display
    --show-p2          Show P2 data (default: True)
    --show-p3          Show P3 data (default: True)
    --output PATH      Output file path (default: None, display in browser)
"""

import os
import sys
import argparse
import logging
import datetime
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/graph_viewer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Default file paths
DEFAULT_P2_PATH = "/var/lib/raspap_solo/data/RawData_P2/P2_fixed.csv"
DEFAULT_P3_PATH = "/var/lib/raspap_solo/data/RawData_P3/P3_fixed.csv"

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Environmental Data Visualization Tool')
    parser.add_argument('--p2-path', type=str, default=DEFAULT_P2_PATH,
                        help=f'Path to P2 CSV data file (default: {DEFAULT_P2_PATH})')
    parser.add_argument('--p3-path', type=str, default=DEFAULT_P3_PATH,
                        help=f'Path to P3 CSV data file (default: {DEFAULT_P3_PATH})')
    parser.add_argument('--days', type=int, default=1,
                        help='Number of days of data to display (default: 1)')
    parser.add_argument('--show-p2', action='store_true', default=True,
                        help='Show P2 data (default: True)')
    parser.add_argument('--show-p3', action='store_true', default=True,
                        help='Show P3 data (default: True)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output file path (default: None, display in browser)')
    return parser.parse_args()

def read_csv_data(csv_path, days=1):
    """Read data from CSV file and process it."""
    # Check if file exists
    if not os.path.exists(csv_path):
        logger.warning(f"CSV file not found: {csv_path}")
        return None

    try:
        # Read CSV file
        logger.info(f"Reading CSV file: {csv_path}")
        df = pd.read_csv(csv_path)

        # Log initial data types and sample data
        logger.info(f"CSV columns and types: {df.dtypes}")
        if not df.empty:
            logger.info(f"Sample data (first row): {df.iloc[0].to_dict()}")

        # Convert timestamp to datetime - simplified approach that handles both numeric and string formats
        if 'timestamp' in df.columns:
            logger.info(f"Original timestamp dtype: {df['timestamp'].dtype}")

            # Check if timestamp is numeric (int64 or float64)
            if df['timestamp'].dtype == 'int64' or df['timestamp'].dtype == 'float64':
                logger.info("Detected numeric timestamp format (seconds since epoch)")
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
            else:
                # Convert to string first to handle any format safely
                logger.info("Detected string timestamp format")
                df['timestamp'] = pd.to_datetime(df['timestamp'].astype(str), errors='coerce')

            logger.info(f"Converted timestamp dtype: {df['timestamp'].dtype}")
            logger.info(f"Timestamp range: {df['timestamp'].min()} to {df['timestamp'].max()}")

        # Drop rows with invalid timestamps
        original_count = len(df)
        df = df.dropna(subset=['timestamp'])
        if len(df) < original_count:
            logger.warning(f"Dropped {original_count - len(df)} rows with invalid timestamps")

        # Convert all numeric columns to proper numeric types
        numeric_columns = ["temperature", "humidity", "pressure", "gas_resistance", "co2", "absolute_humidity"]
        for col in numeric_columns:
            if col in df.columns:
                # Log original data type
                logger.info(f"Column '{col}' original dtype: {df[col].dtype}")

                # Store original values for comparison
                original_values = df[col].copy()

                # Convert to numeric - force conversion to handle any format
                df[col] = pd.to_numeric(df[col], errors='coerce')

                # Check if conversion changed any values or created NaNs
                changed_count = (df[col] != original_values).sum()
                nan_count = df[col].isna().sum()

                logger.info(f"Column '{col}' converted to numeric. Changed values: {changed_count}, NaN values: {nan_count}")
                if not df[col].empty and not df[col].isna().all():
                    logger.info(f"Column '{col}' range: {df[col].min()} to {df[col].max()}")

        # Filter data for the specified time range
        if days > 0:
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
            before_count = len(df)
            df = df[df['timestamp'] >= cutoff_date]
            logger.info(f"Filtered data for last {days} days: {before_count} -> {len(df)} rows")

        # Sort by timestamp
        df = df.sort_values(by='timestamp')

        return df

    except Exception as e:
        logger.error(f"Error reading CSV file {csv_path}: {e}")
        return None

def generate_graph(parameter, df_p2, df_p3, show_p2=True, show_p3=True):
    """Generate a graph for the specified parameter."""
    # Define parameter labels
    label_map = {
        "temperature": "気温 (°C)",
        "humidity": "相対湿度 (%)",
        "absolute_humidity": "絶対湿度 (g/m³)",
        "co2": "CO2濃度 (ppm)",
        "pressure": "気圧 (hPa)",
        "gas_resistance": "ガス抵抗 (Ω)"
    }
    label = label_map.get(parameter, parameter.capitalize())

    # Create figure
    fig = go.Figure()

    # Add P2 data if available
    if show_p2 and df_p2 is not None and not df_p2.empty and parameter in df_p2.columns:
        # Check for valid data (at least 2 unique non-NaN values)
        p2_values = df_p2[parameter].dropna()
        if len(p2_values) > 0 and len(p2_values.unique()) >= 2:
            # Log detailed information about the data being plotted
            min_val = p2_values.min()
            max_val = p2_values.max()
            mean_val = p2_values.mean()
            logger.info(f"Adding P2 data for {parameter}: {len(p2_values)} points, range: {min_val} - {max_val}, mean: {mean_val}")

            # Verify timestamp data is properly formatted
            if not pd.api.types.is_datetime64_any_dtype(df_p2['timestamp']):
                logger.warning(f"P2 timestamp column is not datetime type: {df_p2['timestamp'].dtype}")
                # Try to convert again as a last resort
                df_p2['timestamp'] = pd.to_datetime(df_p2['timestamp'], errors='coerce')
                df_p2 = df_p2.dropna(subset=['timestamp'])
                logger.info(f"Converted P2 timestamps. Remaining rows: {len(df_p2)}")

            # Add trace to the figure
            fig.add_trace(go.Scatter(
                x=df_p2['timestamp'],
                y=df_p2[parameter],
                mode='lines',
                name=f'P2 {label}',
                line=dict(color='blue')
            ))
        else:
            logger.warning(f"P2 data for {parameter} has insufficient unique values: {len(p2_values)} points, {len(p2_values.unique())} unique values")

    # Add P3 data if available
    if show_p3 and df_p3 is not None and not df_p3.empty and parameter in df_p3.columns:
        # Check for valid data (at least 2 unique non-NaN values)
        p3_values = df_p3[parameter].dropna()
        if len(p3_values) > 0 and len(p3_values.unique()) >= 2:
            # Log detailed information about the data being plotted
            min_val = p3_values.min()
            max_val = p3_values.max()
            mean_val = p3_values.mean()
            logger.info(f"Adding P3 data for {parameter}: {len(p3_values)} points, range: {min_val} - {max_val}, mean: {mean_val}")

            # Verify timestamp data is properly formatted
            if not pd.api.types.is_datetime64_any_dtype(df_p3['timestamp']):
                logger.warning(f"P3 timestamp column is not datetime type: {df_p3['timestamp'].dtype}")
                # Try to convert again as a last resort
                df_p3['timestamp'] = pd.to_datetime(df_p3['timestamp'], errors='coerce')
                df_p3 = df_p3.dropna(subset=['timestamp'])
                logger.info(f"Converted P3 timestamps. Remaining rows: {len(df_p3)}")

            # Add trace to the figure
            fig.add_trace(go.Scatter(
                x=df_p3['timestamp'],
                y=df_p3[parameter],
                mode='lines',
                name=f'P3 {label}',
                line=dict(color='red')
            ))
        else:
            logger.warning(f"P3 data for {parameter} has insufficient unique values: {len(p3_values)} points, {len(p3_values.unique())} unique values")

    # Check if we have any traces
    if not fig.data:
        logger.warning(f"No valid data to plot for {parameter}")
        return None

    # Calculate appropriate Y-axis range with padding
    all_y_values = []
    if show_p2 and df_p2 is not None and not df_p2.empty and parameter in df_p2.columns:
        all_y_values.extend(df_p2[parameter].dropna().tolist())
    if show_p3 and df_p3 is not None and not df_p3.empty and parameter in df_p3.columns:
        all_y_values.extend(df_p3[parameter].dropna().tolist())

    if all_y_values:
        min_y = min(all_y_values)
        max_y = max(all_y_values)
        padding = (max_y - min_y) * 0.05  # 5% padding

        # Determine appropriate minimum value based on parameter
        if parameter in ["co2", "gas_resistance", "absolute_humidity"]:
            # These values are never negative
            min_range = max(0, min_y - padding)
        else:
            # Use actual minimum with padding
            min_range = min_y - padding

        # Set Y-axis range
        y_range = [min_range, max_y + padding]
        logger.info(f"Setting Y-axis range for {parameter}: {y_range}")
    else:
        y_range = None

    # Update layout with improved settings
    fig.update_layout(
        title=f"{label}の経時変化",
        xaxis_title="時間",
        yaxis_title=label,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode='closest',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        # Ensure X-axis is properly formatted as a date
        xaxis=dict(
            type='date',
            tickformat='%Y-%m-%d %H:%M',
            tickangle=-45
        )
    )

    # Set Y-axis range if calculated
    if y_range:
        fig.update_yaxes(
            range=y_range,
            autorange=False,
            # Use "tozero" for parameters that should never be negative
            rangemode="tozero" if parameter in ["co2", "gas_resistance", "absolute_humidity"] else "normal"
        )

    return fig

def create_dashboard(df_p2, df_p3, show_p2=True, show_p3=True):
    """Create a dashboard with all parameters."""
    # Define parameters to plot
    parameters = ["temperature", "humidity", "absolute_humidity", "co2", "pressure", "gas_resistance"]

    # Create a subplot figure with 3x2 grid
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=[
            "気温 (°C)", "相対湿度 (%)",
            "絶対湿度 (g/m³)", "CO2濃度 (ppm)",
            "気圧 (hPa)", "ガス抵抗 (Ω)"
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
        # Add P2 data if available
        if show_p2 and df_p2 is not None and not df_p2.empty and param in df_p2.columns:
            p2_values = df_p2[param].dropna()
            if len(p2_values) > 0 and len(p2_values.unique()) >= 2:
                fig.add_trace(
                    go.Scatter(
                        x=df_p2['timestamp'],
                        y=df_p2[param],
                        mode='lines',
                        name=f'P2 {param}',
                        line=dict(color='blue')
                    ),
                    row=row, col=col
                )

        # Add P3 data if available
        if show_p3 and df_p3 is not None and not df_p3.empty and param in df_p3.columns:
            p3_values = df_p3[param].dropna()
            if len(p3_values) > 0 and len(p3_values.unique()) >= 2:
                fig.add_trace(
                    go.Scatter(
                        x=df_p3['timestamp'],
                        y=df_p3[param],
                        mode='lines',
                        name=f'P3 {param}',
                        line=dict(color='red')
                    ),
                    row=row, col=col
                )

        # Calculate appropriate Y-axis range
        all_y_values = []
        if show_p2 and df_p2 is not None and not df_p2.empty and param in df_p2.columns:
            all_y_values.extend(df_p2[param].dropna().tolist())
        if show_p3 and df_p3 is not None and not df_p3.empty and param in df_p3.columns:
            all_y_values.extend(df_p3[param].dropna().tolist())

        if all_y_values:
            min_y = min(all_y_values)
            max_y = max(all_y_values)
            padding = (max_y - min_y) * 0.05  # 5% padding

            # Determine appropriate minimum value based on parameter
            if param in ["co2", "gas_resistance", "absolute_humidity"]:
                # These values are never negative
                min_range = max(0, min_y - padding)
            else:
                # Use actual minimum with padding
                min_range = min_y - padding

            # Set Y-axis range
            y_range = [min_range, max_y + padding]

            # Update Y-axis for this subplot
            fig.update_yaxes(
                range=y_range,
                autorange=False,
                rangemode="tozero" if param in ["co2", "gas_resistance", "absolute_humidity"] else "normal",
                row=row, col=col
            )

    # Update layout
    fig.update_layout(
        title="環境データダッシュボード",
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

    return fig

def main():
    """Main function."""
    # Parse command line arguments
    args = parse_arguments()

    # Read data
    logger.info(f"Reading P2 data from: {args.p2_path}")
    df_p2 = read_csv_data(args.p2_path, args.days) if args.show_p2 else None

    logger.info(f"Reading P3 data from: {args.p3_path}")
    df_p3 = read_csv_data(args.p3_path, args.days) if args.show_p3 else None

    # Check if we have any data
    if (df_p2 is None or df_p2.empty) and (df_p3 is None or df_p3.empty):
        logger.error("No data available for either P2 or P3")
        sys.exit(1)

    # Create dashboard
    logger.info("Creating dashboard")
    dashboard = create_dashboard(df_p2, df_p3, args.show_p2, args.show_p3)

    # Create individual graphs
    parameters = ["temperature", "humidity", "absolute_humidity", "co2", "pressure", "gas_resistance"]
    graphs = {}

    for param in parameters:
        logger.info(f"Creating graph for {param}")
        graph = generate_graph(param, df_p2, df_p3, args.show_p2, args.show_p3)
        if graph:
            graphs[param] = graph

    # Save or display graphs
    if args.output:
        # Save to file
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Save dashboard
        dashboard_path = f"{args.output}_dashboard.html"
        dashboard.write_html(dashboard_path)
        logger.info(f"Dashboard saved to {dashboard_path}")
        
        # Save individual graphs
        for param, graph in graphs.items():
            graph_path = f"{args.output}_{param}.html"
            graph.write_html(graph_path)
            logger.info(f"{param} graph saved to {graph_path}")
    else:
        # Display in browser
        dashboard.show()

if __name__ == "__main__":
    main()
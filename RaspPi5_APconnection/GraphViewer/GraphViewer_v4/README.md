# Environmental Data Visualization Tool (GraphViewer v4)

## Overview
This application provides a web-based dashboard for visualizing environmental data collected from P1, P2, and P3 sensor nodes. It automatically refreshes the data at regular intervals and displays both a comprehensive dashboard and individual parameter graphs. It also allows users to download the CSV data files directly from the web interface.

## Features
- **Auto-Refresh**: Data is automatically updated at configurable intervals (default: 5 minutes)
- **Responsive Design**: Graphs adapt to different screen sizes
- **Separate Update Information**: Latest update information is displayed separately from graphs
- **Multiple Parameters**: Visualizes temperature, humidity, absolute humidity, CO2 concentration, pressure, and gas resistance
- **Multi-Device Support**: Can display data from P1, P2, and P3 sensor nodes
- **CSV Download**: Allows downloading the raw CSV data files directly from the web interface

## Usage
```bash
python auto_graph_viewer_Ver4.py [options]
```

### Options
- `--p1-path PATH`: Path to P1 CSV data file (default: /var/lib/raspap_solo/data/RawData_P1/P1_fixed.csv)
- `--p2-path PATH`: Path to P2 CSV data file (default: /var/lib/raspap_solo/data/RawData_P2/P2_fixed.csv)
- `--p3-path PATH`: Path to P3 CSV data file (default: /var/lib/raspap_solo/data/RawData_P3/P3_fixed.csv)
- `--port PORT`: Port for the web server (default: 8050)
- `--interval MINS`: Refresh interval in minutes (default: 5)
- `--days DAYS`: Number of days of data to display (default: 1)
- `--show-p1`: Show P1 data (default: True)
- `--show-p2`: Show P2 data (default: True)
- `--show-p3`: Show P3 data (default: True)

## Interface
The web interface consists of:
1. **Header**: Title and refresh button
2. **Update Information**: Latest update time and countdown to next update
3. **Status Information**: Data period and displayed devices
4. **Dashboard**: Overview of all environmental parameters
5. **Individual Graphs**: Detailed view of each parameter

## Recent Changes (v3)
- Changed all text to English for better international usability
- Increased font size for explanatory text to improve readability
- Separated latest update information from graphs for clearer presentation
- Enhanced visual styling for better user experience

## Requirements
- Python 3.6+
- Flask
- Pandas
- Plotly
- NumPy

## Installation
1. Ensure Python 3.6+ is installed
2. Install required packages:
   ```bash
   pip install flask pandas plotly numpy
   ```
3. Run the application:
   ```bash
   python auto_graph_viewer_Ver4.py
   ```
4. Open a web browser and navigate to `http://localhost:8050` (or the configured port)

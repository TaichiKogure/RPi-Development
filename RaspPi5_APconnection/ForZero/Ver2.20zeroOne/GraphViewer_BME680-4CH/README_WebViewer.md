# WebViewer - Environmental Data Dashboard

WebViewer is a web application that provides a dashboard for visualizing environmental data collected from P2 and P3 sensor devices. It automatically refreshes the data at configurable intervals and is designed to work with a Raspberry Pi 5 configured as an access point.

## Features

- Displays environmental data from P2 and P3 sensor devices
- Creates interactive graphs for temperature, humidity, absolute humidity, CO2, pressure, and gas resistance
- Automatically refreshes data at configurable intervals
- Accessible via web browser at `http://192.168.0.1/db`
- Responsive design that works on desktop and mobile devices

## Requirements

- Raspberry Pi 5 configured as an access point with IP 192.168.0.1
- Python 3.6 or higher
- Required Python packages:
  - Flask
  - pandas
  - numpy
  - plotly

## Installation

1. Ensure your Raspberry Pi 5 is set up as an access point with IP 192.168.0.1
2. Install required Python packages:

```bash
pip install flask pandas numpy plotly
```

3. Clone or download the repository to your Raspberry Pi 5
4. Navigate to the GraphViewer_v3 directory

## Usage

### Starting the WebViewer

To start the WebViewer with default settings:

```bash
python WebViewer.py
```

This will:
- Read data from the default CSV file paths
- Update graphs every 5 minutes
- Start a web server on port 8080
- Make the dashboard accessible at `http://192.168.0.1:8080/db`

### Command Line Options

The WebViewer supports several command line options:

```
--p2-path PATH    Path to P2 CSV data file (default: /var/lib/raspap_solo/data/RawData_P2/P2_fixed.csv)
--p3-path PATH    Path to P3 CSV data file (default: /var/lib/raspap_solo/data/RawData_P3/P3_fixed.csv)
--port PORT       Port for the web server (default: 8080)
--interval MINS   Refresh interval in minutes (default: 5)
--days DAYS       Number of days of data to display (default: 1)
--show-p2         Show P2 data (default: True)
--show-p3         Show P3 data (default: True)
```

Example with custom settings:

```bash
python WebViewer.py --p2-path /path/to/p2/data.csv --p3-path /path/to/p3/data.csv --port 8080 --interval 10 --days 7
```

This will:
- Read P2 data from `/path/to/p2/data.csv`
- Read P3 data from `/path/to/p3/data.csv`
- Update graphs every 10 minutes
- Display data from the last 7 days
- Start a web server on port 8080
- Make the dashboard accessible at `http://192.168.0.1:8080/db`

### Accessing the Dashboard

1. Connect to the Raspberry Pi 5's WiFi network
2. Open a web browser and navigate to `http://192.168.0.1:8080/db`
3. The dashboard will display with the latest environmental data
4. The page will automatically refresh based on the configured interval

## Dashboard Features

- **Auto-refresh**: The dashboard automatically refreshes at the configured interval
- **Manual refresh**: Click the "Refresh Now" button to manually refresh the data
- **Countdown timer**: Shows the time until the next automatic refresh
- **Dashboard view**: Shows all environmental parameters in a single view
- **Individual graphs**: Detailed graphs for each environmental parameter
- **Interactive graphs**: Hover over data points to see exact values, zoom in/out, etc.

## Troubleshooting

- If the dashboard doesn't load, check that the WebViewer is running on the Raspberry Pi 5
- If no data appears in the graphs, check that the CSV files exist at the specified paths
- Check the `web_viewer.log` file for error messages

## ポート変更について

**注意**: WebViewerはデフォルトでポート8080を使用するように変更されました。これは、ポート80が他のプログラムによって既に使用されていることが多いためです。ダッシュボードにアクセスするには、ブラウザで `http://192.168.0.1:8080/db` にアクセスしてください。

もし別のポートを使用したい場合は、`--port` オプションで指定できます：

```bash
python WebViewer.py --port 3000
```

この場合、ダッシュボードは `http://192.168.0.1:3000/db` でアクセスできます。

## License

This project is open source and available under the [MIT License](LICENSE).

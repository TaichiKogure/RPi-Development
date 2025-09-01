# Raspberry Pi 5 Environmental Data System - Version 4.6

This document explains the structure and usage of the Raspberry Pi 5 Environmental Data System, which has been refactored for better maintainability and extensibility.

## Project Structure

The project has been reorganized to follow a more modular and maintainable structure. The main components are:

### Data Collection Module

The data collection module is responsible for receiving and storing environmental data from P2 and P3 sensor nodes. It has been refactored into the following components:

- **config.py**: Configuration settings for the data collection system
- **main.py**: Main entry point for the data collection system
- **api/**: API server for accessing collected data
  - **routes.py**: API route handlers
  - **server.py**: Flask server setup
- **network/**: Network communication with P2 and P3 devices
  - **server.py**: Socket server for receiving data
- **processing/**: Data processing and validation
  - **calculation.py**: Functions for calculating derived values (e.g., absolute humidity)
  - **validation.py**: Functions for validating received data
- **storage/**: Data storage management
  - **csv_manager.py**: Functions for managing CSV files
  - **data_store.py**: In-memory data storage

### Web Interface Module

The web interface module provides a web-based dashboard for visualizing the collected data. It has been refactored into the following components:

- **config.py**: Configuration settings for the web interface
- **main.py**: Main entry point for the web interface
- **api/**: API for accessing data from the web interface
  - **routes.py**: API route handlers
- **data/**: Data loading and processing
  - **data_manager.py**: Functions for loading and processing data
- **visualization/**: Graph generation
  - **graph_generator.py**: Functions for generating graphs
- **utils/**: Utility functions
  - **helper.py**: Helper functions for formatting data
- **templates/**: HTML templates
  - **index.html**: Main dashboard template
- **static/**: Static files (CSS, JS)
  - **css/style.css**: Custom CSS styles
  - **js/dashboard.js**: Dashboard JavaScript

## Usage Instructions

### Running All Services with start_p1_solo.py (Recommended)

The easiest way to run the entire system is to use the `start_p1_solo.py` script, which starts all necessary services:

1. Access Point setup
2. Data Collection service (for both P2 and P3)
3. Web Interface (with support for both P2 and P3)
4. Connection Monitor (for both P2 and P3)

To run the script, use the following command:

```bash
sudo ~/envmonitor-venv/bin/python3 start_p1_solo.py
```

Note: This script should be run using the Python interpreter from the virtual environment and requires root privileges.

Options:
- `--data-dir DIR`: Directory to store data (default: /var/lib/raspap_solo/data)
- `--web-port PORT`: Port for web interface (default: 80)
- `--api-port PORT`: Port for data API (default: 5001)
- `--monitor-port PORT`: Port for connection monitor API (default: 5002)
- `--monitor-interval SECONDS`: Monitoring interval in seconds (default: 5)
- `--interface INTERFACE`: WiFi interface to monitor (default: wlan0)

The script will:
1. Set up the access point if it's not already running
2. Start the data collection service
3. Start the web interface
4. Start the connection monitor
5. Monitor all services and restart them if they crash

### Running Individual Services (Advanced)

If you need to run individual services separately, you can use the following commands:

#### Running the Data Collection System

To run the data collection system, use the following command:

```bash
python -m p1_software_Zero.data_collection.main [--port PORT] [--data-dir DIR]
```

Or, for backward compatibility:

```bash
python p1_software_Zero/data_collection/P1_data_collector_solo.py [--port PORT] [--data-dir DIR]
```

Options:
- `--port PORT`: Port to listen on (default: 5000)
- `--data-dir DIR`: Data directory (default: /var/lib/raspap_solo/data)

#### Running the Web Interface

To run the web interface, use the following command:

```bash
python -m p1_software_Zero.web_interface.main [--port PORT] [--data-dir DIR] [--debug]
```

Or, for backward compatibility:

```bash
python p1_software_Zero/web_interface/P1_app_solo.py [--port PORT] [--data-dir DIR] [--debug]
```

Options:
- `--port PORT`: Port to listen on (default: 80)
- `--data-dir DIR`: Data directory (default: /var/lib/raspap_solo/data)
- `--debug`: Enable debug mode

### Accessing the Web Interface

Once the web interface is running, you can access it by opening a web browser and navigating to:

```
http://<raspberry-pi-ip>
```

Where `<raspberry-pi-ip>` is the IP address of your Raspberry Pi 5.

## Changes from Previous Version

The main changes from the previous version are:

1. **Modular Structure**: The code has been reorganized into a more modular structure, with each module responsible for a specific functionality.

2. **Absolute Imports**: All imports now use absolute paths, which makes the code more robust and easier to maintain.

3. **Better Separation of Concerns**: The code now follows a better separation of concerns, with each module having a clear responsibility.

4. **Improved Documentation**: The code now has better documentation, with clear explanations of each module's purpose and functionality.

5. **Enhanced Error Handling**: Error handling has been improved throughout the codebase, with better logging and more graceful error recovery.

### Recent Fixes in Ver4.61Debug

1. **Import Error in P1_data_collector_solo.py**: Fixed an issue where P1_data_collector_solo.py would exit with an error code if it failed to import from the refactored modules. The script now adds the parent directory to the Python path before importing, similar to P1_wifi_monitor_solo.py. If the import fails, it now falls back to the original implementation instead of exiting with an error code. This ensures that the script works correctly when executed by start_p1_solo.py, even if the refactored modules are not available.

2. **Improved Integration with start_p1_solo.py**: Enhanced the documentation to emphasize that start_p1_solo.py is the recommended way to run the entire system, as it starts all necessary services and monitors them to ensure they keep running.

## Development Guidelines

When making changes to the codebase, please follow these guidelines:

1. **Maintain the Modular Structure**: Keep the modular structure of the codebase, with each module having a clear responsibility.

2. **Use Absolute Imports**: Use absolute imports for all imports, to ensure the code is robust and maintainable.

3. **Document Your Changes**: Add clear documentation for any changes you make, explaining the purpose and functionality of the changes.

4. **Add Tests**: Add tests for any new functionality or changes to existing functionality.

5. **Follow PEP 8**: Follow the PEP 8 style guide for Python code.

## Troubleshooting

If you encounter any issues, please check the log files:

- Data Collection: `/var/log/data_collector_solo.log`
- Web Interface: `/var/log/web_interface_solo.log`

Common issues:

1. **Data Collection Not Running**: Check if the data collection process is running with `ps aux | grep data_collection`. If it's not running, start it with the command above.

2. **Web Interface Not Accessible**: Check if the web interface process is running with `ps aux | grep web_interface`. If it's not running, start it with the command above.

3. **No Data Displayed**: Check if the data collection process is receiving data from P2 and P3 devices. Check the log file for any errors.

4. **Graphs Not Updating**: Check if the data collection process is storing data correctly. Check the log file for any errors.

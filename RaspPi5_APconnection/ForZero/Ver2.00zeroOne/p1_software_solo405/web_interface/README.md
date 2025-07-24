# Web Interface Module - Ver2.0

## Overview
The Web Interface module runs on the Raspberry Pi 5 (P1) and provides a web interface for visualizing environmental data collected from P2, P3, P4, P5, and P6 devices. In Ver2.0, only BME680 sensors are supported, and CO2 sensors (MH-Z19C) are not supported.

## Directory Structure
The Web Interface module has the following directory structure:

```
web_interface/
├── api/                  # API-related code
│   ├── routes.py         # API route handlers
│   └── __init__.py       # Package initialization file
├── data/                 # Data management code
│   ├── data_manager.py   # Data manager
│   └── __init__.py       # Package initialization file
├── utils/                # Utility functions
│   ├── helper.py         # Helper functions
│   └── __init__.py       # Package initialization file
├── visualization/        # Data visualization code
│   ├── graph_generator.py # Graph generator
│   └── __init__.py       # Package initialization file
├── static/               # Static files (CSS, JavaScript, images)
│   ├── css/              # CSS files
│   ├── js/               # JavaScript files
│   └── img/              # Image files
├── templates/            # HTML templates
├── config.py             # Configuration file
├── main.py               # Main module
├── P1_app_solo.py        # Full-featured web app
├── P1_app_solo_new.py    # Refactored web app
└── P1_app_simple.py      # Simplified web app (reduced resource usage)
```

## Main Program Files

### P1_app_solo.py
**Role**: Full-featured web interface  
**Description**: This file provides a full-featured web interface for visualizing data from P2, P3, P4, P5, and P6 devices. It includes time-series graphs, dashboard, data export functionality, and more. In Ver2.0, CO2 sensor functionality is disabled.  
**Usage Scenario**: Use when advanced data visualization is needed.

```bash
python3 P1_app_solo.py
```

Optionally, you can specify the port and data directory:

```bash
python3 P1_app_solo.py --port 80 --data-dir /path/to/data
```

### P1_app_simple.py
**Role**: Simplified web interface (reduced resource usage)  
**Description**: This file provides a simplified web interface for displaying data from P2, P3, P4, P5, and P6 devices. It reduces resource usage by omitting graph visualization functionality and providing text-based display only. In Ver2.0, CO2 sensor functionality is disabled.  
**Usage Scenario**: Use when you want to minimize resource usage or when text-based display is sufficient.

```bash
python3 P1_app_simple.py
```

### P1_app_solo_new.py
**Role**: Refactored web interface  
**Description**: This file provides a web interface using the refactored module structure. It uses main.py and other modules to implement the web interface in a more organized structure. In Ver2.0, CO2 sensor functionality is disabled.  
**Usage Scenario**: Use when you want to use the latest code structure.

```bash
python3 P1_app_solo_new.py
```

### main.py
**Role**: Main module for the refactored web interface  
**Description**: This file is the main module for the refactored web interface. It defines the WebInterface class and integrates components such as data management, visualization, and API.  
**Usage Scenario**: Not typically used directly, but called from P1_app_solo_new.py.

## Version Information

### Current Version (Ver2.0)
- Supports P2, P3, P4, P5, and P6 devices
- Supports only BME680 sensors (no CO2 sensors)
- Includes both full-featured and simplified web interfaces
- Provides data visualization, export, and connection status monitoring

### Older Versions
- **Ver1.0**: Supported only P4, P5, and P6 devices, included CO2 sensor functionality
- **Ver4.0**: Previous version number before standardization to Ver2.0

## Usage Scenarios

### 1. Starting the Full-Featured Web Interface
To start the full-featured web interface, run P1_app_solo.py:

```bash
python3 P1_app_solo.py
```

This will start a web interface with the following features:
- Time-series graphs of data from P2, P3, P4, P5, and P6 devices
- Dashboard display
- Data export functionality
- Connection status display

### 2. Starting the Simplified Web Interface (Reduced Resource Usage)
To start the simplified web interface with reduced resource usage, run P1_app_simple.py:

```bash
python3 P1_app_simple.py
```

This will start a simplified web interface with the following features:
- Text-based display of data from P2, P3, P4, P5, and P6 devices
- Data export functionality
- Connection status display

### 3. Starting the Refactored Web Interface
To start the refactored web interface, run P1_app_solo_new.py:

```bash
python3 P1_app_solo_new.py
```

This will start a web interface using the refactored module structure.

## Notes
- In Ver2.0, only BME680 sensors are supported, and CO2 sensors (MH-Z19C) are not supported.
- P1_app_simple.py omits graph visualization functionality to reduce resource usage.
- The web interface starts on port 80 by default. To change the port, use the --port option.
- The data directory is /var/lib/raspap_solo/data by default. To change the directory, use the --data-dir option.
- P1_app_solo.py, P1_app_simple.py, and P1_app_solo_new.py typically need to be run with root privileges (sudo).

## For More Information
For more detailed information in Japanese, please refer to the [web_interface_guide_JP.md](web_interface_guide_JP.md) file.
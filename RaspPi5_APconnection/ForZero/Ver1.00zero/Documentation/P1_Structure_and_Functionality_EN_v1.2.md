# P1 Structure and Functionality (Ver1.2)

This document explains the software structure and functionality of P1 (Raspberry Pi Zero 2W). In Ver1.2, the system has been optimized to operate efficiently with the limited resources of the Raspberry Pi Zero 2W.

## Table of Contents

1. [Overview](#overview)
2. [Folder Structure](#folder-structure)
3. [Main Components](#main-components)
   - [Access Point Setup](#access-point-setup)
   - [Data Collection](#data-collection)
   - [Web Interface](#web-interface)
   - [Connection Monitor](#connection-monitor)
4. [Ver1.2 Optimizations](#ver12-optimizations)
5. [Startup Instructions](#startup-instructions)
6. [Troubleshooting](#troubleshooting)

## Overview

P1 (Raspberry Pi Zero 2W) functions as the central hub for the environmental data measurement system. Its main roles are:

- Acting as a WiFi access point for P4, P5, and P6 sensor nodes
- Collecting and storing environmental data from sensor nodes
- Providing a web interface for data visualization
- Monitoring connection quality with sensor nodes

In Ver1.2, the system has been optimized to operate efficiently with the limited resources of the Raspberry Pi Zero 2W. Specifically, rest time has been added between processes, data reception frequency and terminal update frequency have been reduced, and the web interface has been simplified to display text only.

## Folder Structure

The P1 software is organized in the following folder structure:

```
p1_software_solo405/
├── ap_setup/                # Access point configuration
│   └── P1_ap_setup_solo.py  # Access point setup script
├── connection_monitor/      # Connection monitor
│   ├── api/                 # API related
│   ├── measurements/        # Measurement related
│   ├── utils/               # Utilities
│   ├── config.py            # Configuration file
│   ├── main.py              # Main entry point
│   ├── monitor.py           # Monitor implementation
│   └── monitor_v1.2.py      # Optimized monitor implementation (Ver1.2)
├── data_collection/         # Data collection
│   ├── api/                 # API related
│   ├── network/             # Network related
│   ├── processing/          # Data processing
│   ├── storage/             # Data storage
│   ├── config.py            # Configuration file
│   ├── main.py              # Main entry point
│   ├── P1_data_collector_solo.py      # Data collector implementation
│   └── P1_data_collector_solo_v1.2.py # Optimized data collector implementation (Ver1.2)
├── web_interface/           # Web interface
│   ├── api/                 # API related
│   ├── data/                # Data related
│   ├── static/              # Static files
│   ├── templates/           # HTML templates
│   │   ├── dashboard.html   # Dashboard template
│   │   ├── dashboard_text_only.html # Text-only dashboard template (Ver1.2)
│   │   └── index.html       # Index page template
│   ├── utils/               # Utilities
│   ├── visualization/       # Visualization related
│   ├── config.py            # Configuration file
│   ├── main.py              # Main entry point
│   ├── P1_app_simple.py     # Simple web app implementation
│   └── P1_app_simple_v1.2.py # Optimized web app implementation (Ver1.2)
└── start_p1_solo.py         # P1 startup script
```

## Main Components

### Access Point Setup

**Purpose**: Sets up a WiFi access point for P4, P5, and P6 sensor nodes.

**Key Files**:
- `P1_ap_setup_solo.py`: Script to configure the access point

**Functionality**:
- Configuring Raspberry Pi Zero 2W as a WiFi access point
- Setting up DHCP server
- Setting up DNS server
- Configuring IP forwarding

### Data Collection

**Purpose**: Collects and stores environmental data from sensor nodes.

**Key Files**:
- `P1_data_collector_solo.py`: Original data collector implementation
- `P1_data_collector_solo_v1.2.py`: Optimized data collector implementation (Ver1.2)

**Functionality**:
- Receiving data from sensor nodes
- Validating and processing data
- Storing data in CSV files
- Providing API access to data

**Ver1.2 Optimizations**:
- Added rest time between receiving data chunks (100ms)
- Reduced logging frequency (logging only every 5th data point)
- Added rest time in the main server loop
- Implemented rate limiting for API routes
- Added rest time after file operations

### Web Interface

**Purpose**: Provides a web interface for displaying collected data.

**Key Files**:
- `P1_app_simple.py`: Original web app implementation
- `P1_app_simple_v1.2.py`: Optimized web app implementation (Ver1.2)
- `dashboard.html`: Original dashboard template
- `dashboard_text_only.html`: Text-only dashboard template (Ver1.2)

**Functionality**:
- Displaying latest sensor data
- Displaying connection status
- Exporting data
- Displaying historical data

**Ver1.2 Optimizations**:
- Removed graph rendering and simplified to text-only display
- Increased auto-refresh interval from 10 to 30 seconds
- Changed data loading to on-demand (load on button click)
- Removed unnecessary JavaScript library loading

### Connection Monitor

**Purpose**: Monitors connection quality with sensor nodes.

**Key Files**:
- `monitor.py`: Original monitor implementation
- `monitor_v1.2.py`: Optimized monitor implementation (Ver1.2)

**Functionality**:
- Measuring signal strength with sensor nodes
- Measuring noise level
- Measuring ping time
- Monitoring connection status

**Ver1.2 Optimizations**:
- Increased monitoring interval from 5 to 30 seconds
- Reduced logging frequency (logging only every 5th measurement)
- Added rest time between measurements (100ms)
- Reduced history size from 100 to 60
- Reduced ping count from 5 to 3
- Reduced ping timeout from 2 to 1 second

## Ver1.2 Optimizations

In Ver1.2, the following optimizations have been made to operate efficiently with the limited resources of the Raspberry Pi Zero 2W:

1. **Adding Rest Time Between Operations**:
   - Added rest time between receiving data chunks (100ms)
   - Added rest time in main loops
   - Added rest time between measurements
   - Added rest time after file operations

2. **Reducing Data Reception Frequency**:
   - Increased monitoring interval from 5 to 30 seconds
   - Increased web interface auto-refresh interval from 10 to 30 seconds

3. **Reducing Terminal Update Frequency**:
   - Reduced logging frequency (logging only every 5th data point/measurement)

4. **Simplifying Web Interface**:
   - Removed graph rendering and simplified to text-only display
   - Removed unnecessary JavaScript library loading
   - Changed data loading to on-demand

5. **Other Optimizations**:
   - Reduced history size
   - Reduced ping count
   - Reduced ping timeout
   - Implemented rate limiting for API routes

## Startup Instructions

To start P1, run the following command:

```bash
cd /path/to/RaspPi5_APconnection/ForZero/Ver1.00zero
python3 p1_software_solo405/start_p1_solo.py
```

To use the optimized components from Ver1.2, you need to modify the startup script to:

1. Replace `P1_data_collector_solo.py` with `P1_data_collector_solo_v1.2.py`
2. Replace `monitor.py` with `monitor_v1.2.py`
3. Replace `P1_app_simple.py` with `P1_app_simple_v1.2.py`
4. Replace `dashboard.html` with `dashboard_text_only.html`

## Troubleshooting

### Common Issues

1. **P1 Doesn't Start**:
   - Check log files: `/var/log/data_collector_solo.log`, `/var/log/wifi_monitor_solo.log`, `/var/log/web_interface_solo.log`
   - Verify required packages are installed: `pip3 list`
   - Check permissions: try running with `sudo`

2. **No Data Received from Sensor Nodes**:
   - Check if sensor nodes are online: `ping 192.168.0.50` (for P4)
   - Verify access point is correctly configured: `sudo systemctl status hostapd`
   - Check firewall settings: `sudo iptables -L`

3. **Cannot Access Web Interface**:
   - Check if web server is running: `ps aux | grep flask`
   - Verify port is open: `sudo netstat -tulpn | grep 80`
   - Clear browser cache

4. **Connection Monitor Not Working**:
   - Verify required packages are installed: `pip3 list`
   - Check log file: `/var/log/wifi_monitor_solo.log`
   - Check permissions: try running with `sudo`

### Log Files

If you encounter issues, check the following log files:

- Data collection: `/var/log/data_collector_solo.log`
- Connection monitor: `/var/log/wifi_monitor_solo.log`
- Web interface: `/var/log/web_interface_solo.log`

### Support

If you cannot resolve the issue, contact the developer with the following information:

1. Detailed description of the issue
2. Content of relevant log files
3. Raspberry Pi model and version you are using
4. Commands you ran and their output
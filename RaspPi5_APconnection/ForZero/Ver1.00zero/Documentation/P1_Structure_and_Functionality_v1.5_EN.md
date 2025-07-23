# P1 Folder Structure and Functionality Description (Ver1.5)

This document explains the software structure and functionality of P1 (Raspberry Pi Zero 2W). In Ver1.5, the system has been optimized to operate efficiently with the limited resources of the Raspberry Pi Zero 2W, and auto-start functionality and self-diagnostic/recovery mechanisms have been added.

## Table of Contents

1. [Overview](#overview)
2. [Folder Structure](#folder-structure)
3. [Main Components](#main-components)
   - [Access Point Setup](#access-point-setup)
   - [Data Collection](#data-collection)
   - [Web Interface](#web-interface)
   - [Connection Monitor](#connection-monitor)
   - [Startup Script](#startup-script)
4. [New Features in Ver1.5](#new-features-in-ver15)
   - [Auto-start Functionality](#auto-start-functionality)
   - [Self-diagnostic and Recovery Mechanisms](#self-diagnostic-and-recovery-mechanisms)
5. [Optimizations in Ver1.2](#optimizations-in-ver12)
6. [Startup Methods](#startup-methods)
7. [Troubleshooting](#troubleshooting)

## Overview

P1 (Raspberry Pi Zero 2W) functions as the central hub of the environmental data measurement system. Its main roles are as follows:

- Acts as a WiFi access point for P4, P5, and P6 sensor nodes
- Collects and stores environmental data from sensor nodes
- Provides a web interface for data visualization
- Monitors connection quality with sensor nodes

In Ver1.5, in addition to the optimizations from Ver1.2, auto-start functionality and self-diagnostic/recovery mechanisms have been added. This allows the system to automatically start when the Raspberry Pi Zero 2W powers on and to automatically recover if errors occur.

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
├── start_p1_solo.py         # P1 startup script
└── start_p1_solo_v1.5.py    # P1 startup script for Ver1.5 (with auto-start and self-diagnostic features)
```

## Main Components

### Access Point Setup

**Purpose**: Configures the WiFi access point for P4, P5, and P6 sensor nodes.

**Main Files**:
- `P1_ap_setup_solo.py`: Script to configure the access point

**Features**:
- Configures Raspberry Pi Zero 2W as a WiFi access point
- Configures DHCP server
- Configures DNS server
- Configures IP forwarding

### Data Collection

**Purpose**: Collects and stores environmental data from sensor nodes.

**Main Files**:
- `P1_data_collector_solo.py`: Original data collector implementation
- `P1_data_collector_solo_v1.2.py`: Optimized data collector implementation (Ver1.2)

**Features**:
- Receives data from sensor nodes
- Validates and processes data
- Stores data in CSV files
- Provides API access to data

**Optimizations in Ver1.2**:
- Added rest time between data reception chunks (100ms)
- Reduced logging frequency (logs only once every 5 times)
- Added rest time to main server loop
- Implemented rate limiting for API routes
- Added rest time after file operations

### Web Interface

**Purpose**: Provides a web interface for displaying collected data.

**Main Files**:
- `P1_app_simple.py`: Original web app implementation
- `P1_app_simple_v1.2.py`: Optimized web app implementation (Ver1.2)
- `dashboard.html`: Original dashboard template
- `dashboard_text_only.html`: Text-only dashboard template (Ver1.2)

**Features**:
- Displays latest sensor data
- Displays connection status
- Provides data export functionality
- Displays historical data

**Optimizations in Ver1.2**:
- Removed graph rendering and simplified to text-only display
- Increased auto-refresh interval from 10 seconds to 30 seconds
- Changed data loading to on-demand (load on button click)
- Removed unnecessary JavaScript libraries

### Connection Monitor

**Purpose**: Monitors connection quality with sensor nodes.

**Main Files**:
- `monitor.py`: Original monitor implementation
- `monitor_v1.2.py`: Optimized monitor implementation (Ver1.2)

**Features**:
- Measures signal strength with sensor nodes
- Measures noise level
- Measures ping time
- Monitors connection status

**Optimizations in Ver1.2**:
- Increased monitoring interval from 5 seconds to 30 seconds
- Reduced logging frequency (logs only once every 5 times)
- Added rest time between measurements (100ms)
- Reduced history size from 100 to 60
- Reduced ping count from 5 to 3
- Reduced ping timeout from 2 seconds to 1 second

### Startup Script

**Purpose**: Starts and monitors all components.

**Main Files**:
- `start_p1_solo.py`: Original startup script
- `start_p1_solo_v1.5.py`: Startup script for Ver1.5 (with auto-start and self-diagnostic features)

**Features**:
- Sets up access point
- Starts data collection service
- Starts web interface
- Starts connection monitor
- Monitors processes and restarts them if necessary

**Enhancements in Ver1.5**:
- systemd service creation functionality (for auto-start)
- System resource monitoring
- Process restart with exponential backoff
- System reboot capability for persistent errors
- Detailed logging

## New Features in Ver1.5

### Auto-start Functionality

In Ver1.5, functionality has been added to automatically start the system when the Raspberry Pi Zero 2W powers on.

**Main Files**:
- `start_p1_solo_v1.5.py`: Startup script with auto-start functionality

**Features**:
- systemd service creation (with `--create-service` option)
- Automatic execution at system startup
- Startup status logging

**Usage**:
1. Create the systemd service:
   ```bash
   sudo python3 p1_software_solo405/start_p1_solo_v1.5.py --create-service
   ```
2. Verify that the service was created successfully:
   ```bash
   sudo systemctl status p1-environmental-monitor.service
   ```
3. Restart the system to test auto-start:
   ```bash
   sudo reboot
   ```

### Self-diagnostic and Recovery Mechanisms

In Ver1.5, mechanisms for system self-diagnosis and automatic recovery have been added.

**Main Files**:
- `start_p1_solo_v1.5.py`: Startup script with self-diagnostic and recovery mechanisms

**Features**:
- System resource monitoring (memory usage, CPU usage)
- Automatic process restart (data collection, web interface, connection monitor)
- Restart with exponential backoff (gradually increasing restart interval)
- System reboot for persistent errors
- Detailed logging

**Configuration Parameters**:
- `max_restart_attempts`: Maximum number of restart attempts (default: 5)
- `restart_backoff_factor`: Restart interval increase factor (default: 1.5)
- `initial_restart_delay`: Initial delay before first restart (seconds, default: 5)
- `memory_threshold`: Memory usage warning threshold (%, default: 80)
- `cpu_threshold`: CPU usage warning threshold (%, default: 80)
- `system_check_interval`: System resource check interval (seconds, default: 60)
- `process_monitor_interval`: Process monitoring interval (seconds, default: 30)

**Note**: System resource monitoring requires the `psutil` module. If not installed, this feature will be disabled, but process monitoring and automatic restart will continue to function.

## Optimizations in Ver1.2

In Ver1.2, the following optimizations were made to ensure efficient operation with the limited resources of the Raspberry Pi Zero 2W:

1. **Added Rest Time Between Processing**:
   - Added rest time between data reception chunks (100ms)
   - Added rest time to main loops
   - Added rest time between measurements
   - Added rest time after file operations

2. **Reduced Data Reception Frequency**:
   - Increased monitoring interval from 5 seconds to 30 seconds
   - Increased web interface auto-refresh interval from 10 seconds to 30 seconds

3. **Reduced Terminal Update Frequency**:
   - Reduced logging frequency (logs only once every 5 times)

4. **Simplified Web Interface**:
   - Removed graph rendering and simplified to text-only display
   - Removed unnecessary JavaScript libraries
   - Changed data loading to on-demand

5. **Other Optimizations**:
   - Reduced history size
   - Reduced ping count
   - Reduced ping timeout
   - Implemented rate limiting for API routes

## Startup Methods

### Manual Startup

To manually start P1, run the following commands:

```bash
cd /path/to/RaspPi5_APconnection/ForZero/Ver1.00zero
source ~/envmonitor-venv/bin/activate
sudo python3 p1_software_solo405/start_p1_solo_v1.5.py
```

### Auto-start

To configure P1 for auto-start, follow these steps:

1. Create the systemd service:
   ```bash
   cd /path/to/RaspPi5_APconnection/ForZero/Ver1.00zero
   source ~/envmonitor-venv/bin/activate
   sudo python3 p1_software_solo405/start_p1_solo_v1.5.py --create-service
   ```

2. Restart the system:
   ```bash
   sudo reboot
   ```

3. Check the service status:
   ```bash
   sudo systemctl status p1-environmental-monitor.service
   ```

## Troubleshooting

### Common Issues

1. **P1 does not start**:
   - Check the log file: `/var/log/p1_startup_solo_v1.5.log`
   - Verify that required packages are installed: `pip3 list`
   - Check permissions: try running with `sudo`

2. **No data received from sensor nodes**:
   - Verify that sensor nodes are online: `ping 192.168.0.50` (for P4)
   - Check if the access point is correctly configured: `sudo systemctl status hostapd`
   - Check firewall settings: `sudo iptables -L`

3. **Cannot access web interface**:
   - Verify that the web server is running: `ps aux | grep flask`
   - Check if the port is open: `sudo netstat -tulpn | grep 80`
   - Clear browser cache

4. **Connection monitor not working**:
   - Verify that required packages are installed: `pip3 list`
   - Check the log file: `/var/log/wifi_monitor_solo.log`
   - Check permissions: try running with `sudo`

5. **Auto-start not working**:
   - Check the systemd service status: `sudo systemctl status p1-environmental-monitor.service`
   - Check the log file: `/var/log/p1_startup_solo_v1.5.log`
   - Restart the service manually: `sudo systemctl restart p1-environmental-monitor.service`

6. **System resource monitoring not working**:
   - Verify that psutil is installed: `pip3 list | grep psutil`
   - Install psutil: `pip3 install psutil`

### Log Files

If issues occur, check the following log files:

- Startup script: `/var/log/p1_startup_solo_v1.5.log`
- Data collection: `/var/log/data_collector_solo.log`
- Connection monitor: `/var/log/wifi_monitor_solo.log`
- Web interface: `/var/log/web_interface_solo.log`

### Verifying Self-diagnostic and Recovery Mechanisms

To verify that the self-diagnostic and recovery mechanisms are working correctly:

1. Check the process monitoring logs:
   ```bash
   tail -n 100 /var/log/p1_startup_solo_v1.5.log
   ```

2. Check system resource usage (if psutil is installed):
   ```bash
   grep "System resources" /var/log/p1_startup_solo_v1.5.log
   ```

3. Check the automatic process restart history:
   ```bash
   grep "Restarting" /var/log/p1_startup_solo_v1.5.log
   ```

4. Check the system reboot history:
   ```bash
   grep "Rebooting system" /var/log/p1_startup_solo_v1.5.log
   ```

### Support

If issues persist, contact the developer with the following information:

1. Detailed description of the issue
2. Contents of relevant log files
3. Raspberry Pi model and version being used
4. Commands executed and their output
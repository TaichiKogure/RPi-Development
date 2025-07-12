# Raspberry Pi 5 and Pico 2W Standalone Environmental Data Measurement System

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Components](#system-components)
3. [Project Structure](#project-structure)
4. [Key Features](#key-features)
   - [P1 (Raspberry Pi 5) Features](#p1-raspberry-pi-5-features)
   - [P2, P3 (Raspberry Pi Pico 2W) Features](#p2-p3-raspberry-pi-pico-2w-features)
5. [Installation and Setup](#installation-and-setup)
6. [Version Information](#version-information)
7. [Development History](#development-history)
   - [Version 4.6](#version-46)
   - [Version 4.5-4.54](#version-45-454)
   - [Version 4.4-4.45](#version-44-445)
   - [Version 4.31-4.35](#version-431-435)
   - [Version 4.2-4.3](#version-42-43)
   - [Version 4.15-4.19](#version-415-419)
   - [Version 4.1](#version-41)
   - [Version 4.0](#version-40)
   - [Version 3.51](#version-351)
   - [Version 3.5](#version-35)
   - [Version 3.2](#version-32)
   - [Version 3.1](#version-31)
   - [Version 3.0](#version-30)
   - [Version 2.5](#version-25)
   - [Version 2.3](#version-23)
   - [Version 2.2](#version-22)
   - [Version 2.1](#version-21)
   - [Version 2.0](#version-20)
8. [Troubleshooting](#troubleshooting)
9. [Technical Reference](#technical-reference)

## Project Overview
This project implements a standalone environmental data measurement system using a Raspberry Pi 5 (P1) as the central hub and two Raspberry Pi Pico 2W devices (P2, P3) as sensor nodes. The system collects environmental data such as temperature, humidity, atmospheric pressure, gas parameters, and CO2 concentration, then visualizes and stores this data for analysis.

Operation Directory: `G:\RPi-Development\RaspPi5_APconnection`

## System Components
1. **Raspberry Pi 5 (P1)** - Central hub that:
   - Acts as a WiFi access point for P2 and P3
   - Collects and stores environmental data from sensor nodes
   - Provides web interface for data visualization
   - Monitors connection quality with sensor nodes

2. **Raspberry Pi Pico 2W (P2, P3)** - Sensor nodes that:
   - Collect environmental data using BME680 sensors
   - Measure CO2 levels using MH-Z19B sensors
   - Transmit data to P1 via WiFi
   - Auto-restart on errors or connection issues

3. **Sensors**:
   - BME680 - Measures temperature, humidity, atmospheric pressure, and gas parameters
   - MH-Z19B - Measures CO2 concentration

## Project Structure
The project is organized within the RaspPi5_APconnection directory and includes:

```
RaspPi5_APconnection\
├── p1_software\              # Software for Raspberry Pi 5
│   ├── ap_setup\             # Access point configuration
│   ├── data_collection\      # Data collection from P2 and P3
│   ├── web_interface\        # Web UI for data visualization
│   └── connection_monitor\   # WiFi signal monitoring
├── p2_p3_software\           # Software for Pico 2W devices
│   ├── sensor_drivers\       # BME680 and MH-Z19B drivers
│   ├── data_transmission\    # WiFi communication with P1
│   └── error_handling\       # Auto-restart functionality
└── documentation\            # User manuals and guides
    ├── installation\         # Installation instructions
    ├── operation\            # Operation instructions
    └── troubleshooting\      # Troubleshooting guides
```

Note: This structure may be modified or expanded as needed.

## Key Features

### P1 (Raspberry Pi 5) Features
- **Dual WiFi Functionality**:
  - Acts as WiFi access point (AP) for P2 and P3
  - Can connect to internet via USB WiFi dongle
  - Configurable to prioritize AP mode when USB dongle is absent
  - Default AP configuration:
    ```
    interface=wlan0
    dhcp-range=192.168.50.50,192.168.50.150,255.255.255.0,24h
    domain=wlan
    address=/gw.wlan/192.168.50.1
    bogus-priv
    server=8.8.8.8
    server=8.8.4.4
    ```

- **Data Management**:
  - Receives and stores environmental data from P2 and P3
  - Stores data in CSV format with timestamp, temperature, humidity, pressure, gas parameters, and CO2 levels

- **Visualization**:
  - Web UI accessible from smartphones/devices connected to P1's WiFi
  - Time-series graphs of environmental data
  - Real-time display of current readings
  - CSV export functionality for downloaded data

- **Connection Monitoring**:
  - Measures WiFi signal strength, ping times, and noise levels with P2 and P3
  - Updates every 5 seconds (configurable)
  - Helps optimize physical placement of devices
  - Available through both Web UI and VNC interface

### P2, P3 (Raspberry Pi Pico 2W) Features
- **Sensor Integration**:
  - BME680 sensor readings every 30 seconds
  - MH-Z19B CO2 readings every 30 seconds

- **Data Transmission**:
  - Continuous data transmission to P1 via WiFi
  - Unique identification for P2 and P3 devices

- **Reliability**:
  - Automatic restart on sensor errors or data collection failures
  - Automatic WiFi reconnection after restart

## Installation and Setup
Detailed installation guides are provided for:
- Setting up P1 (Raspberry Pi 5) as an access point
- Installing and configuring sensor software on P2 and P3
- Connecting the system components
- Initial system testing and validation

For Python dependencies, a virtual environment is recommended:
```bash
cd ~
python3 -m venv envmonitor-venv
source envmonitor-venv/bin/activate
pip install flask flask-socketio pandas plotly
```

## Version Information
All software components and documentation include version numbers for proper tracking and compatibility management.

## Development History

### Version 4.6
- Reorganized code structure for better maintainability
- Split monolithic files into function-specific modules
- Fixed relative import issues
- Created comprehensive documentation in both Japanese and English

### Version 4.5-4.54
- Integrated Graph_Viewer functionality into P1 module
- Added support for various time ranges in data display
- Implemented graph saving functionality
- Added real-time sensor value display
- Fixed timestamp conversion issues
- Improved CSV path handling

### Version 4.4-4.45
- Created unified startup program for all components
- Standardized file naming with version suffixes
- Fixed JSON serialization issues with NumPy arrays
- Addressed non-ASCII character issues in error messages

### Version 4.31-4.35
- Fixed graph rendering issues
- Implemented fixed filename approach for CSV data
- Improved graph Y-axis scaling
- Updated Plotly.js to newer version
- Enhanced web interface with simplified CSV reading and display

### Version 4.2-4.3
- Fixed BME680 I2C address issues
- Corrected data collection format compatibility with P1
- Fixed timestamp handling in web app to properly convert to datetime
- Implemented automatic data reading from storage directories
- Added dynamic IP address tracking for P2 and P3

### Version 4.15-4.19
- Created diagnostic programs for P3 WiFi and sensor connections
- Added machine.idle() and time.sleep() to prevent blocking of background processes
- Fixed WiFi client initialization issues
- Implemented safer WiFi connection handling with try/except blocks
- Reduced print statements during WiFi connection to prevent USB/REPL issues

### Version 4.1
- Fixed P3 connection timeout issues
- Improved program consistency, file naming, and P1 integration
- Prevented ID conflicts between P2 and P3

### Version 4.0
- Added P3 as a new Pico 2W terminal with same functionality as P2
- Enhanced P1 reception system to handle data from both P2 and P3
- Improved web interface to overlay P2 and P3 graphs
- Modified data storage structure to use RawData_P2 and RawData_P3 directories
- Added absolute humidity calculation based on temperature and humidity data
- Implemented display toggles for P2 and P3 data

### Version 3.51
- Fixed Thonny IDE connection issues with P2_software_solo35
- Addressed WiFi connection failures and USB disconnection problems

### Version 3.5
- Added CO2 sensor (MH-Z19C) to P2
- Updated pin assignments:
  - VCC (red) → VBUS (5V, pin 40)
  - GND (black) → GND (pin 38)
  - TX (green) → GP9 (pin 12)
  - RX (blue) → GP8 (pin 11)
- Implemented 30-second warmup period before measurement
- Modified P1 web app to:
  - Allow customizable Y-axis ranges
  - Add CO2 graph
  - Fix "Loading Graph" issue
  - Display P2 signal strength information

### Version 3.2
- Added retry functionality to wifi_client_solo.py (up to 5 automatic retries)
- Fixed P2_watchdog_solo.py to ensure error logs are properly saved before reset
- Addressed potential conflicts between flash writing and reset timing

### Version 3.1
- Fixed consistency and connection issues between P1 and P2
- Enhanced start_p1_solo.py to display process status on command prompt
- Added startup delay for P2 to prevent network connection errors
- Improved LED indicator functionality to distinguish between different error states

### Version 3.0
- Implemented new P2_software_solo3 based on verified bme680.py module
- Integrated sensor driver with data transmission module

### Version 2.5
- Updated BME680 configuration in P2_software_solo to fix errors:
  - Corrected sensor address to 0x77
  - Enabled heater for gas measurement
  - Improved heater temperature control with range limiting
  - Added default ambient temperature value

### Version 2.3
- Created Raspberry Pi Pico 2W package compatible with Version 2.2
- Modified data transmission, error handling, and sensor drivers to work with P1 solo version

### Version 2.2
- Implemented virtual environment for all Python operations to prevent system environment corruption
- Added installation instructions for required Python packages

### Version 2.1
- Created P2, P3 models based on Version 2.0
- Updated IP configuration to:
  ```
  ap_ip=192.168.0.1
  ap_netmask=255.255.255.0
  ap_dhcp_range_start=192.168.0.50
  ap_dhcp_range_end=192.168.0.150
  ```

### Version 2.0
- Created BME680 solo version with filename_solo program collection
- Created standalone directories: installation_solo, p1_software_solo, P2P3_software_solo
- Developed unified startup script for P1 that handles access point setup, data collection service, web interface, and connection monitoring

## Troubleshooting
Common issues and their solutions:

1. **WiFi Connection Issues**:
   - Check AP configuration on P1
   - Verify P2/P3 are using correct SSID and password
   - Ensure adequate signal strength between devices

2. **Sensor Reading Errors**:
   - Verify I2C connections and addresses
   - Check power supply to sensors
   - Confirm sensor initialization in logs

3. **Data Visualization Problems**:
   - Check CSV file format and existence
   - Verify timestamp conversion is working correctly
   - Ensure web server is running properly

## Technical Reference
For detailed technical information, refer to the documentation directory or specific version documentation.

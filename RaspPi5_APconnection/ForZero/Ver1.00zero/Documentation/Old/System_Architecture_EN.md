# Raspberry Pi 5 and Pico 2W Standalone Environmental Data Measurement System - Architecture Overview

**Version: 1.0.0**

## System Architecture

This document provides an overview of the system architecture for the Raspberry Pi 5 and Pico 2W Standalone Environmental Data Measurement System.

### 1. System Components

The system consists of the following components:

1. **Raspberry Pi 5 (P1)** - Central hub that:
   - Acts as a WiFi access point for P4, P5, and P6
   - Collects and stores environmental data from sensor nodes
   - Provides web interface for data visualization
   - Monitors connection quality with sensor nodes

2. **Raspberry Pi Pico 2W (P4, P5, P6)** - Sensor nodes that:
   - Collect environmental data using BME680 sensors
   - Measure CO2 levels using MH-Z19B sensors
   - Transmit data to P1 via WiFi
   - Auto-restart on errors or connection issues

3. **Sensors**:
   - BME680 - Measures temperature, humidity, atmospheric pressure, and gas parameters
   - MH-Z19B - Measures CO2 concentration

### 2. Software Architecture

#### 2.1 P1 (Raspberry Pi 5) Software

The P1 software is organized into several modules:

1. **Access Point Setup** (`ap_setup`)
   - Configures the Raspberry Pi 5 as a WiFi access point
   - Sets up DHCP server for assigning IP addresses to sensor nodes
   - Manages network interfaces

2. **Data Collection** (`data_collection`)
   - Receives data from sensor nodes via HTTP
   - Validates and processes incoming data
   - Stores data in CSV files
   - Provides API endpoints for accessing data

3. **Web Interface** (`web_interface`)
   - Provides a web-based user interface for data visualization
   - Displays real-time and historical data
   - Allows downloading of data in CSV format
   - Shows connection status of sensor nodes

4. **Connection Monitor** (`connection_monitor`)
   - Monitors WiFi signal strength, ping times, and noise levels
   - Tracks connection quality with sensor nodes
   - Provides API endpoints for connection status

#### 2.2 P4, P5, P6 (Raspberry Pi Pico 2W) Software

The sensor node software is organized into several modules:

1. **Sensor Drivers** (`sensor_drivers`)
   - `bme680.py` - Driver for BME680 sensor
   - `mhz19c.py` - Driver for MH-Z19C CO2 sensor

2. **Data Transmission** (`data_transmission`)
   - `P4_wifi_client_debug.py` / `P5_wifi_client_debug.py` / `P6_wifi_client_debug.py` - WiFi client for connecting to P1
   - `wifi_client.py` - Simplified interface to WiFi client
   - Handles data transmission to P1

3. **Error Handling** (`error_handling`)
   - `P4_watchdog_debug.py` / `P5_watchdog_debug.py` / `P6_watchdog_debug.py` - Watchdog timer for auto-restart
   - `watchdog.py` - Simplified interface to watchdog
   - Logs errors and handles recovery

4. **Main Program** (`main.py`)
   - Initializes sensors, WiFi, and watchdog
   - Collects data from sensors
   - Transmits data to P1
   - Handles error recovery

### 3. Data Flow

1. **Sensor Data Collection**
   - P4, P5, and P6 collect environmental data from BME680 and MH-Z19C sensors
   - Data is collected at regular intervals (default: 30 seconds)

2. **Data Transmission**
   - P4, P5, and P6 connect to P1's WiFi access point
   - Data is transmitted to P1 via HTTP POST requests
   - Each transmission includes device ID, timestamp, and sensor readings

3. **Data Storage**
   - P1 receives data and validates it
   - Data is stored in CSV files, organized by device and date
   - A fixed CSV file is maintained for each device for easy access

4. **Data Visualization**
   - P1's web interface reads data from CSV files
   - Data is displayed as time-series graphs
   - Real-time data is updated automatically
   - Historical data can be viewed and downloaded

### 4. Network Architecture

1. **WiFi Access Point**
   - P1 creates a WiFi network with SSID "RaspberryPi5_AP_Solo"
   - P4, P5, and P6 connect to this network
   - IP addresses are assigned in the range 192.168.0.50 - 192.168.0.150
   - P1's IP address is 192.168.0.1

2. **Internet Connectivity**
   - P1 can connect to the internet via a USB WiFi dongle
   - This allows for dual WiFi functionality:
     - Internal network for sensor nodes
     - External network for internet access

3. **Connection Monitoring**
   - P1 monitors the connection quality with P4, P5, and P6
   - Metrics include signal strength, ping time, and noise level
   - This helps optimize the physical placement of devices

### 5. Error Handling and Recovery

1. **Sensor Node Recovery**
   - P4, P5, and P6 use watchdog timers to detect system freezes
   - Auto-restart on sensor errors or data collection failures
   - Automatic WiFi reconnection after restart

2. **Data Collection Recovery**
   - P1 handles connection drops gracefully
   - Continues operation even if some sensor nodes are offline
   - Logs errors for troubleshooting

### 6. Security Considerations

1. **WiFi Security**
   - WiFi network is secured with WPA2
   - Default password should be changed during setup

2. **Data Security**
   - Data is stored locally on P1
   - No data is transmitted to external servers

### 7. Scalability

The system is designed to be scalable:

- Additional sensor nodes can be added
- Different types of sensors can be integrated
- Data storage and visualization can be extended

### 8. Future Enhancements

Potential future enhancements include:

- Support for additional sensor types
- Advanced data analysis and alerting
- Remote access via VPN
- Cloud integration for data backup and remote monitoring
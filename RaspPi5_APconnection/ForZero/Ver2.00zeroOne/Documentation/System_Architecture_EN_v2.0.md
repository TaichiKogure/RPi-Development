# System Architecture for Environmental Data Measurement System
**Version: 2.0.0 (BME680-only)**

This document describes the architecture of the standalone environmental data measurement system using a Raspberry Pi 5 (P1) as the central hub and Raspberry Pi Pico 2W devices (P2-P6) as sensor nodes. Version 2.0 is designed to work with BME680 sensors only.

## System Overview

The environmental data measurement system is designed to collect, store, and visualize environmental data from multiple sensor nodes. The system consists of:

1. **Raspberry Pi 5 (P1)** - Central hub
2. **Raspberry Pi Pico 2W (P2-P6)** - Sensor nodes
3. **BME680 Sensors** - For measuring temperature, humidity, atmospheric pressure, and gas parameters

## Hardware Architecture

### Raspberry Pi 5 (P1)

The Raspberry Pi 5 serves as the central hub of the system. It:
- Acts as a WiFi access point for the sensor nodes
- Runs the data collection service
- Hosts the web interface for data visualization
- Stores the collected data

### Raspberry Pi Pico 2W (P2-P6)

Each Raspberry Pi Pico 2W serves as a sensor node. It:
- Connects to a BME680 sensor
- Collects environmental data
- Transmits the data to P1 via WiFi
- Auto-restarts on errors or connection issues

### BME680 Sensors

Each BME680 sensor is connected to a Raspberry Pi Pico 2W and measures:
- Temperature
- Humidity
- Atmospheric pressure
- Gas parameters (VOC gas resistance)

### Connectivity

- P1 creates a WiFi access point with SSID "RaspberryPi5_AP_Solo2"
- P2-P6 connect to this access point
- Data is transmitted from P2-P6 to P1 via HTTP requests

## Software Architecture

### P1 (Raspberry Pi 5) Software

The P1 software consists of several components:

1. **Access Point Setup**
   - Located in: `p1_software_solo405/ap_setup/`
   - Configures the Raspberry Pi 5 as a WiFi access point
   - Uses `hostapd` and `dnsmasq` for access point functionality

2. **Data Collection**
   - Located in: `p1_software_solo405/data_collection/`
   - Listens for incoming data from sensor nodes
   - Validates and processes the received data
   - Stores the data in CSV files
   - Calculates derived values (e.g., absolute humidity)
   - Provides an API for accessing the data

3. **Web Interface**
   - Located in: `p1_software_solo405/web_interface/`
   - Provides a web-based dashboard for data visualization
   - Displays current readings from all sensor nodes
   - Shows time series graphs of environmental data
   - Allows exporting data as CSV files

4. **Connection Monitor**
   - Located in: `p1_software_solo405/connection_monitor/`
   - Monitors the connection quality with sensor nodes
   - Measures signal strength, ping time, and noise level
   - Displays connection status in the web interface

5. **Unified Startup Script**
   - Located in: `p1_software_solo405/start_p1_solo.py`
   - Starts all P1 components in the correct order
   - Ensures all services are running properly
   - Provides status information

### P2-P6 (Raspberry Pi Pico 2W) Software

The P2-P6 software consists of several components:

1. **Sensor Drivers**
   - Located in: `sensor_drivers/`
   - Provides interfaces for the BME680 sensor
   - Handles sensor initialization and reading

2. **Data Transmission**
   - Located in: `data_transmission/`
   - Manages WiFi connectivity
   - Formats and transmits data to P1
   - Implements retry logic for failed transmissions

3. **Error Handling**
   - Located in: `error_handling/`
   - Logs errors to a file
   - Implements watchdog functionality
   - Auto-restarts the device on critical errors

4. **Main Program**
   - Located in: `main.py`
   - Initializes all components
   - Coordinates data collection and transmission
   - Handles error conditions

## Data Flow

1. **Data Collection**
   - BME680 sensors collect environmental data (temperature, humidity, pressure, gas resistance)
   - Pico 2W reads data from the sensors at regular intervals (typically every 30 seconds)

2. **Data Transmission**
   - Pico 2W formats the data as JSON
   - Data is transmitted to P1 via HTTP POST request
   - Example data format:
     ```json
     {
       "device_id": "P2",
       "timestamp": "2025-07-23 12:34:56",
       "temperature": 25.6,
       "humidity": 45.2,
       "pressure": 1013.2,
       "gas_resistance": 12345
     }
     ```

3. **Data Processing**
   - P1 receives the data and validates it
   - Absolute humidity is calculated from temperature and humidity
   - Data is stored in CSV files with the following format:
     ```
     timestamp,device_id,temperature,humidity,pressure,gas_resistance,,absolute_humidity
     ```
   - Note the empty field where CO2 data would have been in previous versions

4. **Data Storage**
   - Data is stored in two types of files:
     - Daily files: `{device_id}_{YYYY-MM-DD}.csv`
     - Fixed files: `{device_id}_fixed.csv`
   - Files are stored in device-specific directories:
     - `/var/lib/raspap_solo/data/RawData_P2/`
     - `/var/lib/raspap_solo/data/RawData_P3/`
     - `/var/lib/raspap_solo/data/RawData_P4/`
     - `/var/lib/raspap_solo/data/RawData_P5/`
     - `/var/lib/raspap_solo/data/RawData_P6/`

5. **Data Visualization**
   - Web interface reads data from CSV files
   - Data is displayed as time series graphs
   - Latest readings are shown in a dashboard
   - Connection status is displayed for each sensor node

## Differences from Previous Versions

Version 2.0 differs from previous versions in the following ways:

1. **Removed CO2 Sensor Support**
   - MH-Z19C CO2 sensor initialization and reading code has been commented out
   - CO2 data is no longer collected or transmitted
   - CO2 visualization has been removed from the web interface
   - CSV format maintains compatibility by keeping an empty field where CO2 data would have been

2. **Modified Data Processing**
   - Data validation no longer checks for CO2 values
   - Data storage includes an empty field for CO2 to maintain CSV format compatibility

3. **Modified Web Interface**
   - CO2 graph has been removed from the dashboard
   - CO2 readings have been removed from the latest data display
   - JavaScript code for loading CO2 graphs has been commented out

## Configuration

### P1 Configuration

The P1 configuration is stored in `p1_software_solo405/data_collection/config.py`:

```python
DEFAULT_CONFIG = {
    "data_dir": "/var/lib(FromThonny)/raspap_solo/data",
    "rawdata_p2_dir": "RawData_P2",
    "rawdata_p3_dir": "RawData_P3",
    "rawdata_p4_dir": "RawData_P4",
    "rawdata_p5_dir": "RawData_P5",
    "rawdata_p6_dir": "RawData_P6",
    "listen_port": 5000,
    "api_port": 5000,
    "file_rotation_interval": 86400,  # 24 hours in seconds
    "cleanup_interval": 3600,  # 1 hour in seconds
    "retention_days": 30,
    "log_level": "INFO",
    "debug_mode": False,
    "rest_time": 0.1,  # Added rest time between operations (100ms)
    "log_frequency": 5,  # Log only every 5th data point
    "rate_limit_window": 60,  # Rate limit window in seconds
    "rate_limit_count": 10,  # Maximum number of requests per window
}
```

### P2-P6 Configuration

The P2-P6 configuration is stored in `main.py` on each Pico 2W:

```python
# ===== DEVICE CONFIGURATION =====
DEVICE_ID = "P2"  # Change to P3, P4, P5, or P6 as appropriate
WIFI_SSID = "RaspberryPi5_AP_Solo2"
WIFI_PASSWORD = "raspberry"
SERVER_IP = "192.168.0.2"
SERVER_PORT = 5000
TRANSMISSION_INTERVAL = 30  # Data transmission interval in seconds
```

## Security Considerations

1. **WiFi Security**
   - The WiFi access point is secured with WPA2
   - Default password should be changed in production environments

2. **Data Security**
   - Data is transmitted over local WiFi network only
   - No encryption is used for data transmission
   - System is designed for standalone operation, not internet-connected

3. **Physical Security**
   - Physical access to devices should be restricted
   - SD card encryption can be enabled for additional security

## Limitations

1. **Sensor Limitations**
   - BME680 sensors have limited accuracy
   - Gas resistance values are relative, not absolute
   - Temperature readings may be affected by device heat

2. **Network Limitations**
   - WiFi range is limited
   - Signal strength affects data transmission reliability
   - Maximum of 5 sensor nodes recommended

3. **Storage Limitations**
   - Data is stored on the SD card, which has limited write cycles
   - Long-term data storage should be backed up regularly

## Future Enhancements

Possible future enhancements for the system include:

1. **Additional Sensor Support**
   - Add support for other environmental sensors
   - Implement plug-and-play sensor detection

2. **Enhanced Data Analysis**
   - Add trend analysis and anomaly detection
   - Implement data aggregation for long-term storage

3. **Remote Access**
   - Add secure remote access to the web interface
   - Implement data synchronization with cloud services

4. **Power Management**
   - Implement power-saving modes for sensor nodes
   - Add battery level monitoring for battery-powered nodes
# Raspberry Pi 5 and Pico 2W Standalone Environmental Data Measurement System
# Operation Manual (BME680 Only Mode)
## Version 2.0

## Overview

This document provides instructions for operating the Raspberry Pi 5 and Pico 2W Standalone Environmental Data Measurement System in BME680 Only Mode (Version 2.0). In this version, the system has been modified to work exclusively with BME680 sensors, with CO2 sensor (MH-Z19C) functionality disabled.

## System Components

1. **Raspberry Pi 5 (P1)** - Central hub that:
   - Acts as a WiFi access point for P2-P6
   - Collects and stores environmental data from sensor nodes
   - Provides web interface for data visualization
   - Monitors connection quality with sensor nodes

2. **Raspberry Pi Pico 2W (P2-P6)** - Sensor nodes that:
   - Collect environmental data using BME680 sensors
   - Transmit data to P1 via WiFi
   - Auto-restart on errors or connection issues

3. **Sensors**:
   - BME680 - Measures temperature, humidity, atmospheric pressure, and gas parameters

## Key Features

### P1 (Raspberry Pi 5) Features
- **Dual WiFi Functionality**:
  - Acts as WiFi access point (AP) for P2-P6
  - Can connect to internet via USB WiFi dongle
  - Configurable to prioritize AP mode when USB dongle is absent

- **Data Management**:
  - Receives and stores environmental data from P2-P6
  - Stores data in CSV format with timestamp, temperature, humidity, pressure, gas parameters, and absolute humidity

- **Visualization**:
  - Web UI accessible from smartphones/devices connected to P1's WiFi
  - Time-series graphs of environmental data
  - Real-time display of current readings
  - CSV export functionality for downloaded data

- **Connection Monitoring**:
  - Measures WiFi signal strength, ping times, and noise levels with P2-P6
  - Updates every 5 seconds (configurable)
  - Helps optimize physical placement of devices
  - Available through both Web UI and VNC interface

### P2-P6 (Raspberry Pi Pico 2W) Features
- **Sensor Integration**:
  - BME680 sensor readings every 30 seconds

- **Data Transmission**:
  - Continuous data transmission to P1 via WiFi
  - Unique identification for P2-P6 devices

- **Reliability**:
  - Automatic restart on sensor errors or data collection failures
  - Automatic WiFi reconnection after restart

## Operation Instructions

### Starting the System

1. **Power on P1 (Raspberry Pi 5)**:
   - Connect the power supply to P1
   - Wait for the system to boot up (approximately 1-2 minutes)
   - The access point will be automatically configured

2. **Power on P2-P6 (Raspberry Pi Pico 2W)**:
   - Connect the power supply to each Pico 2W device
   - The devices will automatically connect to P1's WiFi access point
   - LED indicators will show connection status

### Accessing the Web Interface

1. **Connect to P1's WiFi Network**:
   - On your smartphone or computer, connect to the WiFi network "RaspberryPi5_AP_Solo2"
   - Password: "raspberry"

2. **Access the Web Interface**:
   - Open a web browser
   - Navigate to http://192.168.0.2
   - The dashboard will display the latest environmental data and graphs

### Interpreting the Data

The system collects and displays the following environmental parameters:

1. **Temperature** (°C):
   - Ambient temperature measured by the BME680 sensor

2. **Humidity** (%):
   - Relative humidity measured by the BME680 sensor

3. **Absolute Humidity** (g/m³):
   - Calculated from temperature and relative humidity

4. **Pressure** (hPa):
   - Atmospheric pressure measured by the BME680 sensor

5. **Gas Resistance** (Ω):
   - Gas resistance measured by the BME680 sensor, which can indicate air quality

### Using the Dashboard

The dashboard provides several features for data visualization and analysis:

1. **Real-time Data Display**:
   - Current readings from all connected sensors

2. **Time-series Graphs**:
   - Historical data visualization
   - Adjustable time range (1 day, 7 days, etc.)
   - Option to show/hide specific sensors

3. **Connection Status**:
   - Signal strength and quality for each sensor node
   - Ping times and noise levels

4. **Data Export**:
   - Download data as CSV files for further analysis

## Troubleshooting

### P1 (Raspberry Pi 5) Issues

1. **Web Interface Not Accessible**:
   - Verify that you are connected to the correct WiFi network
   - Check that P1 is powered on and the access point is active
   - Try restarting P1

2. **No Data Displayed**:
   - Check that P2-P6 devices are powered on and connected
   - Verify that the data collection service is running on P1
   - Check the connection status in the dashboard

### P2-P6 (Raspberry Pi Pico 2W) Issues

1. **Device Not Connecting to WiFi**:
   - Check that the device is powered on (LED should be blinking)
   - Verify that P1's access point is active
   - Try resetting the device

2. **Sensor Reading Errors**:
   - Check the physical connections to the BME680 sensor
   - Verify that the sensor is properly initialized
   - Try resetting the device

## Maintenance

### Regular Maintenance Tasks

1. **Check System Status**:
   - Regularly monitor the connection status of all devices
   - Verify that data is being collected and stored properly

2. **Update Software**:
   - Check for software updates periodically
   - Follow the update instructions provided with new releases

3. **Backup Data**:
   - Regularly backup the collected data
   - Data is stored in CSV format in the following directory on P1:
     - `/var/lib/raspap_solo/data/RawData_P2/` for P2
     - `/var/lib/raspap_solo/data/RawData_P3/` for P3
     - etc.

## Technical Notes

### BME680 Only Mode

In Version 2.0, the system has been modified to work exclusively with BME680 sensors. The CO2 sensor (MH-Z19C) functionality has been disabled in the software. This change affects the following components:

1. **P1 Data Collection**:
   - CSV files no longer include CO2 data column (empty placeholder is maintained for compatibility)
   - Web visualization does not display CO2 data

2. **P2-P6 Sensor Nodes**:
   - CO2 sensor initialization is disabled
   - CO2 data collection and transmission is disabled

These modifications ensure that the system works properly with BME680 sensors only, while maintaining compatibility with the original code structure.

## Support

For technical support or questions about the system, please contact the system administrator or refer to the documentation provided with the system.

---

*This document is part of the Raspberry Pi 5 and Pico 2W Standalone Environmental Data Measurement System documentation set, Version 2.0.*
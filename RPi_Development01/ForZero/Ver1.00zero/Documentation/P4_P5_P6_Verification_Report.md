# P4, P5, and P6 Verification Report

## Overview
This report summarizes the verification of P4, P5, and P6 sensor nodes and their compatibility with the P1 central hub in the Environmental Data Measurement System. The verification process included checking the software implementation of each sensor node and ensuring consistency across all nodes.

## P1 Configuration
The P1 central hub is properly configured to interact with P4, P5, and P6 sensor nodes. The configuration includes:

- Data directories for P4, P5, and P6 (RawData_P4, RawData_P5, RawData_P6)
- WiFi monitor configuration for all three devices
- A function to ensure that the data directories exist

## P4 Software Implementation

### Main Program (main.py)
- Device ID: "P4"
- WiFi Configuration:
  - SSID: "RaspberryPi5_AP_Solo"
  - Password: "raspberry"
  - Server IP: "192.168.0.1"
  - Server Port: 5000
- Pin Configuration:
  - LED_PIN: "LED"
  - I2C_SDA_PIN: 0
  - I2C_SCL_PIN: 1
  - UART_TX_PIN: 8
  - UART_RX_PIN: 9
- Error Handling:
  - ERROR_LOG_FILE: "/error_log_p4_solo.txt"

### WiFi Client (P4_wifi_client_debug.py)
- WiFiClient class with methods for:
  - Connecting to WiFi network
  - Sending data to server
  - Handling errors
  - Monitoring connection quality
- Default device ID: "P4"

### Sensor Drivers
- BME680 sensor driver (bme680.py)
  - BME680_I2C class for low-level communication
  - BME680 class for simplified interface
  - Methods for reading temperature, humidity, pressure, and gas resistance
- MH-Z19C CO2 sensor driver (mhz19c.py)
  - MHZ19C class for communication
  - Methods for reading CO2 concentration, calibration, and configuration

### Error Handling (P4_watchdog_debug.py)
- Watchdog class for monitoring system health
- Functions for handling errors, syncing files, and resetting the device
- Memory monitoring function

## P5 Software Implementation

### Main Program (main.py)
- Device ID: "P5"
- WiFi Configuration:
  - SSID: "RaspberryPi5_AP_Solo"
  - Password: "raspberry"
  - Server IP: "192.168.0.1"
  - Server Port: 5000
- Pin Configuration:
  - LED_PIN: "LED"
  - I2C_SDA_PIN: 0
  - I2C_SCL_PIN: 1
  - UART_TX_PIN: 8
  - UART_RX_PIN: 9
- Error Handling:
  - ERROR_LOG_FILE: "/error_log_p5_solo.txt"

### WiFi Client (P5_wifi_client_debug.py)
- WiFiClient class with methods for:
  - Connecting to WiFi network
  - Sending data to server
  - Handling errors
  - Monitoring connection quality
- Default device ID: "P5"

### Sensor Drivers
- BME680 sensor driver (bme680.py)
  - BME680_I2C class for low-level communication
  - BME680 class for simplified interface
  - Methods for reading temperature, humidity, pressure, and gas resistance
- MH-Z19C CO2 sensor driver (mhz19c.py)
  - MHZ19C class for communication
  - Methods for reading CO2 concentration, calibration, and configuration

### Error Handling (P5_watchdog_debug.py)
- Watchdog class for monitoring system health
- Functions for handling errors, logging errors, syncing files, and resetting the device
- Error log initialization function

## P6 Software Implementation

### Main Program (main.py)
- Device ID: "P6"
- WiFi Configuration:
  - SSID: "RaspberryPi5_AP_Solo"
  - Password: "raspberry"
  - Server IP: "192.168.0.1"
  - Server Port: 5000
- Pin Configuration:
  - LED_PIN: "LED"
  - I2C_SDA_PIN: 0
  - I2C_SCL_PIN: 1
  - UART_TX_PIN: 8
  - UART_RX_PIN: 9
- Error Handling:
  - ERROR_LOG_FILE: "/error_log_p6_solo.txt"

### WiFi Client (P6_wifi_client_debug.py)
- WiFiClient class with methods for:
  - Connecting to WiFi network
  - Sending data to server
  - Handling errors
  - Monitoring connection quality
- Default device ID: "P6"
- DataTransmitter class for sending data to the server

### Sensor Drivers
- BME680 sensor driver (bme680.py)
  - BME680_I2C class for low-level communication
  - BME680 class for simplified interface
  - Methods for reading temperature, humidity, pressure, and gas resistance
- MH-Z19C CO2 sensor driver (mhz19c.py)
  - MHZ19C class for communication
  - Methods for reading CO2 concentration, calibration, and configuration

### Error Handling (P6_watchdog_debug.py)
- Watchdog class for monitoring system health
- Functions for handling errors, logging errors, syncing files, and resetting the device
- Error log initialization function

## Consistency Across Sensor Nodes

### Device IDs and Server Configurations
All sensor nodes (P4, P5, and P6) have the correct device IDs and server configurations:
- Each node has a unique device ID ("P4", "P5", or "P6")
- All nodes use the same WiFi SSID ("RaspberryPi5_AP_Solo") and password ("raspberry")
- All nodes use the same server IP ("192.168.0.1") and port (5000)

### Sensor Initialization and Data Transmission
All sensor nodes use the same pin configuration for the sensors:
- I2C_SDA_PIN: 0
- I2C_SCL_PIN: 1
- UART_TX_PIN: 8
- UART_RX_PIN: 9

All nodes use the same sensor drivers (bme680.py and mhz19c.py) with the same interface, ensuring consistent data collection and transmission.

### Error Handling and Watchdog Implementations
All sensor nodes have similar error handling and watchdog implementations:
- Each node has a Watchdog class for monitoring system health
- Each node has functions for handling errors, syncing files, and resetting the device
- Each node has a unique error log file path ("/error_log_p4_solo.txt", "/error_log_p5_solo.txt", or "/error_log_p6_solo.txt")

## Conclusion
The verification process confirms that P4, P5, and P6 sensor nodes are properly implemented and configured to work with the P1 central hub. All nodes have the necessary software components for collecting environmental data, transmitting it to P1, and handling errors. The consistency across all nodes ensures reliable operation of the Environmental Data Measurement System.

## Recommendations
1. **Testing**: Conduct thorough testing of the system with all sensor nodes connected to verify proper operation.
2. **Documentation**: Update the system documentation to include information about P4, P5, and P6 sensor nodes.
3. **Monitoring**: Implement a monitoring system to track the performance of all sensor nodes and detect any issues.
4. **Backup**: Create regular backups of the sensor node configurations to ensure quick recovery in case of failure.

## Version Information
- **Report Date**: 2025-07-22
- **System Version**: 1.0.0
- **Compatible Hardware**: Raspberry Pi 5, Raspberry Pi Pico 2W
- **Compatible Sensors**: BME680, MH-Z19B/C
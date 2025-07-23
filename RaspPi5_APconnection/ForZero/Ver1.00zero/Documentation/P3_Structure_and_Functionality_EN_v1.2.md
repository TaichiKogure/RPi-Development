# P3 Structure and Functionality (Ver1.2)

This document explains the software structure and functionality of P3 (Raspberry Pi Pico 2W). P3 functions as a sensor node, collecting environmental data and transmitting it to P1.

## Table of Contents

1. [Overview](#overview)
2. [Folder Structure](#folder-structure)
3. [Main Components](#main-components)
   - [Main Script](#main-script)
   - [Data Transmission](#data-transmission)
   - [Error Handling](#error-handling)
   - [Sensor Drivers](#sensor-drivers)
4. [Operation Flow](#operation-flow)
5. [Troubleshooting](#troubleshooting)

## Overview

P3 (Raspberry Pi Pico 2W) functions as a sensor node in the environmental data measurement system. Its main roles are:

- Measuring temperature, humidity, pressure, and gas resistance using the BME680 sensor
- Measuring CO2 concentration using the MH-Z19C sensor
- Transmitting the measured data to P1 via WiFi
- Automatic restart in case of errors

P3 has a very similar structure to P2, using the same codebase. The main differences are only in configuration values and device ID. P3 is intended to be installed in a different location from P2 and collect environmental data from a different area.

## Folder Structure

The P3 software is organized in the following folder structure:

```
P3_software_debug/
├── data_transmission/           # Data transmission related
│   ├── P2_wifi_client_debug.py  # WiFi client for P2
│   └── P3_wifi_client_debug.py  # WiFi client for P3
├── error_handling/              # Error handling related
│   ├── P2_watchdog_debug.py     # Watchdog for P2
│   └── P3_watchdog_debug.py     # Watchdog for P3
├── sensor_drivers/              # Sensor drivers
│   ├── bme680.py                # BME680 sensor driver
│   └── mhz19c.py                # MH-Z19C sensor driver
└── main.py                      # Main script
```

## Main Components

### Main Script

**File**: `main.py`

**Purpose**: Initializes the system, connects to WiFi, and runs the main loop.

**Key Functions**:
- System initialization (I2C, UART, LED, sensors, WiFi client, watchdog)
- WiFi network connection
- Reading data from sensors
- Transmitting data to P1
- Error handling and automatic restart

**Key Functions**:
- `initialize()`: Initializes the system
- `connect_wifi()`: Connects to the WiFi network
- `main_loop()`: Runs the main loop
- `safe_reset()`: Safely resets the system
- `debug_print()`: Outputs debug messages
- `blink_led()`: Blinks the LED

### Data Transmission

**Folder**: `data_transmission/`

**Key Files**:
- `P3_wifi_client_debug.py`: WiFi client for P3

**Purpose**: Handles data transmission from P3 to P1.

**Key Functions**:
- Connecting to WiFi network
- Transmitting data to P1 server
- Monitoring connection status
- Reconnection handling

**Key Classes**:
- `WiFiClient`: Class that handles WiFi connection and data transmission

**Key Methods**:
- `connect()`: Connects to the WiFi network
- `send_data()`: Sends data to P1
- `disconnect()`: Disconnects from the WiFi network
- `is_connected()`: Checks connection status

### Error Handling

**Folder**: `error_handling/`

**Key Files**:
- `P3_watchdog_debug.py`: Watchdog for P3

**Purpose**: Monitors the system and performs automatic restart.

**Key Functions**:
- Setting up the watchdog timer
- Recording error logs
- Automatic system restart
- LED indication of error states

**Key Classes**:
- `Watchdog`: Class that provides watchdog functionality

**Key Methods**:
- `feed()`: Resets the watchdog timer
- `handle_error()`: Handles errors
- `reset_device()`: Resets the device
- `log_error()`: Records errors in the log

### Sensor Drivers

**Folder**: `sensor_drivers/`

**Key Files**:
- `bme680.py`: BME680 sensor driver
- `mhz19c.py`: MH-Z19C sensor driver

**Purpose**: Handles communication with sensors and data reading.

**BME680 Sensor**:
- Measuring temperature, humidity, pressure, and gas resistance
- I2C communication
- Sensor initialization and configuration
- Data reading and conversion

**MH-Z19C Sensor**:
- Measuring CO2 concentration
- UART communication
- Sensor initialization and configuration
- Data reading and conversion

## Operation Flow

The operation flow of P3 is as follows:

1. **Initialization**:
   - Initializing I2C, UART, and LED
   - Initializing BME680 sensor
   - Initializing MH-Z19C sensor
   - Initializing WiFi client
   - Initializing watchdog

2. **WiFi Connection**:
   - Connecting to the WiFi access point provided by P1
   - Retrying or restarting in case of connection failure

3. **Main Loop**:
   - Reading data from BME680 sensor (temperature, humidity, pressure, gas resistance)
   - Reading data from MH-Z19C sensor (CO2 concentration)
   - Transmitting data to P1
   - Resetting the watchdog timer
   - Waiting for a certain period (30 seconds)
   - Restarting the loop

4. **Error Handling**:
   - Sensor reading error: Recording error log, retrying or restarting
   - WiFi connection error: Attempting reconnection, restarting if failed
   - Data transmission error: Attempting retransmission, reconnecting or restarting if failed
   - Watchdog timeout: Automatic restart

## Troubleshooting

### Common Issues

1. **P3 Doesn't Start**:
   - Check power supply
   - Check USB cable
   - Try a different USB port
   - Reflash the firmware

2. **Cannot Get Sensor Data**:
   - Check sensor connections
   - Check I2C or UART wiring
   - Check sensor power supply
   - Check sensor driver settings

3. **Cannot Connect to WiFi**:
   - Check if P1 is running
   - Check if P1's access point is active
   - Check WiFi settings (SSID, password)
   - Move P3 closer to P1

4. **Data Not Transmitted to P1**:
   - Check WiFi connection
   - Check if P1's data collection service is running
   - Check P1's IP address and port settings
   - Check firewall settings

### Error Codes

You can identify errors by the LED blinking pattern:

- **1 blink**: Initializing
- **2 blinks**: Connecting to WiFi
- **3 blinks**: Sensor error
- **4 blinks**: WiFi connection error
- **5 blinks**: Data transmission error
- **Continuous blinking**: Critical error, restarting

### Log Files

Error logs are stored in the internal flash memory. You can check them by connecting to a PC via USB cable and using tools like Thonny IDE.

### Support

If you cannot resolve the issue, contact the developer with the following information:

1. Error log contents
2. LED blinking pattern
3. Raspberry Pi Pico model and version you are using
4. Sensor model and connection method
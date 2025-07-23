# P5 Folder Structure and Functionality (Ver1.2)

This document explains the software structure and functionality of P5 (Raspberry Pi Pico 2W). P5 functions as a sensor node, collecting environmental data and transmitting it to P1.

## Table of Contents

1. [Overview](#overview)
2. [Folder Structure](#folder-structure)
3. [Main Components](#main-components)
   - [Main Script](#main-script)
   - [Data Transmission](#data-transmission)
   - [Error Handling](#error-handling)
   - [Sensor Drivers](#sensor-drivers)
4. [Operational Flow](#operational-flow)
5. [Troubleshooting](#troubleshooting)

## Overview

P5 (Raspberry Pi Pico 2W) functions as a sensor node in the environmental data measurement system. Its main roles are:

- Measuring temperature, humidity, atmospheric pressure, and gas resistance using the BME680 sensor
- Measuring CO2 concentration using the MH-Z19C sensor
- Transmitting collected data to P1 via WiFi
- Automatic restart in case of errors

P5 has similar functionality to P2, P3, and P4, but adopts a more refined modular structure. Common functionality has been extracted into separate modules, improving code reusability and maintainability.

## Folder Structure

P5's software is organized in the following folder structure:

```
P5_software_debug/
├── data_transmission/           # Data transmission related
│   ├── P5_wifi_client_debug.py  # WiFi client for P5
│   └── wifi_client.py           # Common WiFi client module
├── error_handling/              # Error handling related
│   ├── P5_watchdog_debug.py     # Watchdog for P5
│   └── watchdog.py              # Common watchdog module
├── sensor_drivers/              # Sensor drivers
│   ├── bme680.py                # BME680 sensor driver
│   └── mhz19c.py                # MH-Z19C sensor driver
└── main.py                      # Main script
```

## Main Components

### Main Script

**File**: `main.py`

**Purpose**: Initializes the system, connects to WiFi, and runs the main loop.

**Main Functions**:
- System initialization (I2C, UART, LED, sensors, WiFi client, watchdog)
- WiFi connection
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

**Main Files**:
- `P5_wifi_client_debug.py`: WiFi client for P5
- `wifi_client.py`: Common WiFi client module

**Purpose**: Handles data transmission from P5 to P1.

**Main Functions**:
- Connecting to WiFi network
- Transmitting data to P1 server
- Monitoring connection status
- Reconnection processing

**Module Structure**:
- `wifi_client.py`: Common module providing basic WiFi connection and transmission functionality
- `P5_wifi_client_debug.py`: Implements P5-specific settings and functions, utilizing the common module

**Main Class**:
- `WiFiClient`: Class that handles WiFi connection and data transmission

**Key Methods**:
- `connect()`: Connects to the WiFi network
- `send_data()`: Sends data to P1
- `disconnect()`: Disconnects from the WiFi network
- `is_connected()`: Checks connection status

### Error Handling

**Folder**: `error_handling/`

**Main Files**:
- `P5_watchdog_debug.py`: Watchdog for P5
- `watchdog.py`: Common watchdog module

**Purpose**: Monitors the system and performs automatic restart.

**Main Functions**:
- Setting up the watchdog timer
- Recording error logs
- Automatic system restart
- LED display of error states

**Module Structure**:
- `watchdog.py`: Common module providing basic watchdog functionality
- `P5_watchdog_debug.py`: Implements P5-specific settings and functions, utilizing the common module

**Main Class**:
- `Watchdog`: Class that provides watchdog functionality

**Key Methods**:
- `feed()`: Resets the watchdog timer
- `handle_error()`: Processes errors
- `reset_device()`: Resets the device
- `log_error()`: Records errors in the log

### Sensor Drivers

**Folder**: `sensor_drivers/`

**Main Files**:
- `bme680.py`: BME680 sensor driver
- `mhz19c.py`: MH-Z19C sensor driver

**Purpose**: Communicates with sensors and reads data.

**BME680 Sensor**:
- Measures temperature, humidity, atmospheric pressure, and gas resistance
- I2C communication
- Sensor initialization and configuration
- Reading and converting data

**MH-Z19C Sensor**:
- Measures CO2 concentration
- UART communication
- Sensor initialization and configuration
- Reading and converting data

## Operational Flow

P5's operational flow is as follows:

1. **Initialization**:
   - Initialize I2C, UART, LED
   - Initialize BME680 sensor
   - Initialize MH-Z19C sensor
   - Initialize WiFi client
   - Initialize watchdog

2. **WiFi Connection**:
   - Connect to WiFi access point provided by P1
   - Retry or restart on connection failure

3. **Main Loop**:
   - Read data from BME680 sensor (temperature, humidity, pressure, gas resistance)
   - Read data from MH-Z19C sensor (CO2 concentration)
   - Transmit data to P1
   - Reset watchdog timer
   - Wait for a set time (30 seconds)
   - Restart loop

4. **Error Handling**:
   - Sensor reading error: Record error log, retry or restart
   - WiFi connection error: Attempt reconnection, restart on failure
   - Data transmission error: Attempt retransmission, reconnect or restart on failure
   - Watchdog timeout: Automatic restart

## Troubleshooting

### Common Issues

1. **P5 Won't Start**:
   - Check power supply
   - Check USB cable
   - Try a different USB port
   - Rewrite firmware

2. **Can't Get Sensor Data**:
   - Check sensor connections
   - Check I2C or UART wiring
   - Check sensor power
   - Check sensor driver settings

3. **Can't Connect to WiFi**:
   - Check if P1 is running
   - Check if P1's access point is enabled
   - Check WiFi settings (SSID, password)
   - Move P5 closer to P1

4. **Data Not Being Transmitted to P1**:
   - Check WiFi connection
   - Check if P1's data collection service is running
   - Check P1's IP address and port settings
   - Check firewall settings

### Error Codes

You can identify errors by LED blink patterns:

- **1 blink**: Initializing
- **2 blinks**: Connecting to WiFi
- **3 blinks**: Sensor error
- **4 blinks**: WiFi connection error
- **5 blinks**: Data transmission error
- **Continuous blinking**: Critical error, restarting

### Log Files

Error logs are saved in internal flash memory. You can check them by connecting to a PC via USB cable and using Thonny IDE or similar tools.

### Support

If problems persist, contact the developer with the following information:

1. Error log contents
2. LED blink pattern
3. Model and version of Raspberry Pi Pico being used
4. Sensor model and connection method
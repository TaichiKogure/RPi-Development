# Raspberry Pi Pico 2W Environmental Data System - Solo Version 3

## Overview
This is the Solo Version 3 of the Raspberry Pi Pico 2W (P2) environmental data measurement system. It collects data from a BME680 sensor and transmits it to a Raspberry Pi 5 (P1) server via WiFi.

Version 3.0.0-solo uses the Adafruit BME680 driver that has been confirmed to work reliably with the P2 sensor.

## Features
- BME680 sensor integration for measuring:
  - Temperature (°C)
  - Humidity (%)
  - Atmospheric pressure (hPa)
  - Gas resistance (Ohms)
- WiFi connectivity to the Raspberry Pi 5 access point
- Periodic data transmission to the central server
- Error handling and automatic recovery
- LED status indication

## Directory Structure
```
P2_software_solo3/
├── main.py                  # Main program launcher
├── main_solo.py             # Main program implementation
├── sensor_drivers/          # Sensor driver modules
│   └── bme680.py            # BME680 sensor driver
├── data_transmission/       # Data transmission modules
│   └── wifi_client_solo.py  # WiFi client and data transmitter
└── error_handling/          # Error handling modules
    └── watchdog_solo.py     # Watchdog and error handler
```

## Hardware Requirements
- Raspberry Pi Pico 2W
- BME680 sensor connected via I2C:
  - SDA: GPIO 0
  - SCL: GPIO 1
- Raspberry Pi 5 running as an access point with IP 192.168.0.1

## Software Requirements
- MicroPython for Raspberry Pi Pico W
- Raspberry Pi 5 running the P1_software_solo server

## Installation
1. Flash MicroPython to the Raspberry Pi Pico 2W
2. Copy all files and directories to the Pico's root directory
3. Reset the Pico to start the program

## Configuration
The main configuration parameters are in `main_solo.py`:

- `DEVICE_ID`: Device identifier (default: "P2")
- `WIFI_SSID`: WiFi network SSID (default: "RaspberryPi5_AP_Solo")
- `WIFI_PASSWORD`: WiFi network password (default: "raspberry")
- `SERVER_IP`: Server IP address (default: "192.168.0.1")
- `SERVER_PORT`: Server port (default: 5000)
- `TRANSMISSION_INTERVAL`: Data transmission interval in seconds (default: 30)

## Operation
When powered on, the Pico will:
1. Initialize the BME680 sensor
2. Connect to the WiFi network
3. Start collecting and transmitting data at regular intervals
4. Blink the onboard LED to indicate activity

## Troubleshooting
- If the sensor fails to initialize, the device will restart
- If the WiFi connection fails, the device will restart
- If there are repeated errors, the watchdog will reset the device

## Changes from Previous Versions
### Version 3.0.0-solo
- Uses the Adafruit BME680 driver from OK2bme680Pico
- Directly accesses sensor properties (temperature, humidity, pressure, gas)
- Explicitly enables gas measurements by setting the run_gas bit

### Version 2.0.0-solo
- Used a custom BME680 driver implementation
- Added fixes for sensor address and heater control

## Credits
- Adafruit for the BME680 driver
- Environmental Data System Team
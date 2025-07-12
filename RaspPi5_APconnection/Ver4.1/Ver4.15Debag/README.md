# Raspberry Pi Pico 2W Environmental Monitor Debug Version 4.15

## Overview

This debug version (Ver4.15) is designed to identify and resolve issues with the Raspberry Pi Pico 2W (P3) environmental monitoring system, particularly focusing on WiFi connection problems and USB disconnection loops when using Thonny IDE.

## Key Improvements

1. **Enhanced Thonny Mode**
   - Prevents USB disconnection loops by disabling automatic resets
   - Provides detailed status reporting during WiFi connection
   - Offers offline mode for sensor testing without WiFi

2. **Improved WiFi Connection**
   - Multiple connection strategies (4 different modes)
   - Extended timeouts and retry mechanisms
   - Detailed status reporting with guidance
   - Progressive backoff for connection retries

3. **Better Error Handling**
   - Safe reset procedure with file synchronization
   - Comprehensive error logging
   - Detailed error diagnostics and recommendations
   - Special handling for different error types

4. **Offline Mode**
   - Continues to collect and display sensor data even without WiFi
   - Allows testing of sensors independently of network issues
   - Provides real-time readings from BME680 and MH-Z19C sensors

## Changes Made to Fix USB Disconnection Loop

The main issues addressed in this version were:

1. **USB Disconnection Loop**: When running the program in Thonny IDE, the USB connection would be lost because:
   - The WiFi connection would fail
   - The program would immediately call `machine.reset()`
   - This would reset the Pico, causing the USB connection to be lost
   - Thonny would lose connection to the device

2. **WiFi Connection Drops**: Continuous loops without pauses would prevent the MicroPython system from maintaining WiFi connections and responding to USB serial communications.

The solution implemented includes:

1. **Thonny Mode**:
   - Added a `DEBUG_THONNY_MODE` flag that's enabled by default
   - Modified the `safe_reset()` function to check for Thonny mode and prevent automatic resets
   - Enhanced the WiFi connection process with better error handling and status reporting
   - Implemented an offline mode that continues to run even when WiFi connection fails

2. **Background Processing**:
   - Added `machine.idle()` calls to all continuous loops to allow the system to handle WiFi and USB processing
   - Added short `time.sleep(0.05)` calls after `machine.idle()` to prevent CPU overload
   - This gives the MicroPython system time to maintain WiFi connections and respond to USB serial communications

3. **Improved Debugging**:
   - Added detailed logging and guidance to help troubleshoot connection issues
   - Implemented multiple WiFi connection modes for testing different scenarios

## Configuration Options

The debug settings can be customized in the `main.py` file:

```python
# ===== DEBUG CONFIGURATION =====
DEBUG_ENABLE = True                  # Master switch for debug mode
DEBUG_DISABLE_AUTO_RESET = True      # Disable automatic reset on errors
DEBUG_DISABLE_WATCHDOG = False       # Disable hardware watchdog (use with caution)
DEBUG_WIFI_MODE = 2                  # WiFi connection mode (1-4)
DEBUG_WIFI_TIMEOUT = 90              # WiFi connection timeout in seconds
DEBUG_WIFI_MAX_RETRIES = 5           # Maximum WiFi connection retries
DEBUG_DETAILED_LOGGING = True        # Enable detailed logging
DEBUG_STARTUP_DELAY = 15             # Startup delay in seconds
DEBUG_SENSOR_WARMUP = 30             # Sensor warmup time in seconds
DEBUG_RESET_DELAY = 30               # Delay before reset in seconds
DEBUG_THONNY_MODE = True             # Special mode for Thonny development
```

## WiFi Connection Modes

Four WiFi connection modes are available:

1. **Mode 1**: Normal connection with automatic reset disabled
2. **Mode 2**: Connection with extended timeout and detailed status reporting (recommended)
3. **Mode 3**: Connection with network reset before each attempt
4. **Mode 4**: Connection with progressive backoff and multiple retries

## Usage

1. Open the project in Thonny IDE
2. Connect to the Raspberry Pi Pico W
3. Adjust debug settings if needed
4. Run the program
5. Monitor the detailed logs to identify any issues
6. If WiFi connection fails, the program will continue in offline mode

## Documentation

For detailed instructions in Japanese, please refer to the `manual_ja.md` file.

## Files

- `main.py` - Main program with enhanced debugging
- `data_transmission/P3_wifi_client_debug.py` - WiFi client with improved error handling
- `error_handling/P3_watchdog_debug.py` - Watchdog and error handling with safe reset
- `sensor_drivers/bme680.py` - BME680 sensor driver
- `sensor_drivers/mhz19c.py` - MH-Z19C CO2 sensor driver
- `manual_ja.md` - Japanese manual with detailed instructions
- `README.md` - This file

## Testing

This version has been tested with Thonny IDE and addresses the USB disconnection loop issue. The program now continues to run even when WiFi connection fails, allowing for easier debugging and testing.

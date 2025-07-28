# BME680 Environmental Data Monitor with Auto-Start and Recovery

## Overview

This project implements an environmental data monitoring system using a Raspberry Pi Pico, BME680 sensor, and SSD1306 OLED display. The system measures temperature, humidity, pressure, and gas resistance, and displays this data on the OLED screen along with calculated absolute humidity.

The system is designed to be standalone and resilient, with automatic startup on power-on and robust error recovery mechanisms.

## Features

- **Auto-start on power-on**: The system automatically starts when the Pico is powered on
- **Watchdog timer**: Automatically resets the system if it hangs or becomes unresponsive
- **Error logging**: Records errors and restarts to a log file for troubleshooting
- **Robust error handling**: Gracefully handles sensor errors and other failures
- **Visual feedback**: Uses the onboard LED to indicate system status and errors
- **Data visualization**: Displays environmental data on the OLED screen with a simple animation

## Hardware Requirements

- Raspberry Pi Pico or Pico W
- BME680 environmental sensor
- SSD1306 OLED display (128x64 pixels, SPI interface)
- Jumper wires

## Hardware Connections

### BME680 Sensor (I2C connection)
- VCC → 3.3V (Pin 36)
- GND → GND (Pin 38)
- SCL → GP1 (Pin 2)
- SDA → GP0 (Pin 1)

### SSD1306 OLED Display (SPI connection)
- VCC → 3.3V (Pin 36)
- GND → GND (Pin 38)
- DIN (MOSI) → GP3 (Pin 5)
- CLK (SCK) → GP2 (Pin 4)
- CS → GP6 (Pin 9)
- DC → GP4 (Pin 6)
- RST → GP5 (Pin 7)

## Software Setup

1. Copy the following files to your Raspberry Pi Pico:
   - `boot.py` - Automatically runs on startup and launches the main program
   - `bme680_oled_monitor_updated.py` - Main program
   - `bme680.py` - BME680 sensor driver
   - `ssd1306.py` - SSD1306 OLED display driver

2. Power on the Pico to start the system

## Auto-Start and Recovery Mechanisms

### Auto-Start

The system uses MicroPython's `boot.py` mechanism to automatically start the program when the Pico is powered on. The boot sequence:

1. The Pico runs `boot.py` on power-on
2. `boot.py` imports the main program (`bme680_oled_monitor_updated.py`)
3. The main program initializes and starts monitoring

### Watchdog Timer

A watchdog timer is implemented to automatically reset the system if it hangs or becomes unresponsive:

1. The watchdog is initialized with an 8-second timeout
2. The main program "feeds" the watchdog at critical points in the code
3. If the program hangs and fails to feed the watchdog for 8 seconds, the Pico automatically resets

### Error Logging

The system logs errors and restarts to a file named `error_log.txt`:

1. Each log entry includes a timestamp and error message
2. The log file is automatically managed to prevent it from growing too large
3. Logs can be accessed by connecting to the Pico via USB and using a tool like Thonny

### Error Recovery

The system implements several error recovery mechanisms:

1. **Sensor errors**: If the BME680 sensor returns invalid readings, the system uses the last valid readings
2. **Initialization errors**: If initialization fails, the system attempts to restart
3. **Runtime errors**: If an error occurs during operation, the system logs the error and continues
4. **Critical errors**: If a critical error occurs, the system forces a reset

### Visual Feedback

The onboard LED provides visual feedback about the system status:

1. **Startup**: 3 quick blinks when the system starts
2. **Error**: Rapid blinking (10 blinks) when an error occurs
3. **Restart**: 5 quick blinks when the system restarts
4. **Measurement**: LED turns on during sensor measurement

## Troubleshooting

### System Not Starting

If the system doesn't start:

1. Check power connections
2. Ensure all required files are on the Pico
3. Check the error log by connecting to the Pico via USB

### Sensor Errors

If the sensor readings are incorrect or missing:

1. Check sensor connections
2. Verify the sensor address (0x76 or 0x77)
3. Check the error log for sensor-specific errors

### Display Issues

If the display is not working:

1. Check display connections
2. Verify SPI pin assignments
3. Check the error log for display-specific errors

## Advanced Usage

### Modifying the Watchdog Timeout

The watchdog timeout can be adjusted by changing the parameter in the `init_watchdog` function call:

```python
# Initialize watchdog timer (8 second timeout)
init_watchdog(8000)
```

### Disabling Auto-Start

To disable auto-start, simply rename or delete the `boot.py` file.

### Accessing Logs

To access the error logs:

1. Connect the Pico to a computer via USB
2. Open Thonny or another MicroPython IDE
3. Open the `error_log.txt` file from the Pico's filesystem

## Version History

- **1.5** - Added auto-start and recovery features
- **1.4** - Improved animation with multiple bouncing boxes
- **1.3** - Added absolute humidity calculation
- **1.2** - Enhanced display formatting
- **1.1** - Added animation
- **1.0** - Initial release
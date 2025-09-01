# Connection Monitor Module - Ver2.1

## Overview
This module monitors WiFi connection quality between the Raspberry Pi 5 (P1) and sensor node devices (P2, P3, P4, P5, P6). It measures and displays connection metrics such as signal strength, noise level, signal-to-noise ratio (SNR), and ping time. Ver2.0 supports systems using only BME680 sensors.

## Changes in Ver2.1
- Updated version numbers from "4.0.0-solo" to "2.1.0"
- Updated references to devices to include P2, P3, P4, P5, and P6
- Set monitoring interval to 80 seconds
- Added comprehensive Japanese guide document

## Files
- **P1_wifi_monitor_solo.py**: Main entry point for compatibility with start_p1_solo.py
- **terminal_reporter.py**: Script for running the connection monitor in console mode
- **main.py**: Module containing the main function for setting up and running the connection monitor
- **monitor.py**: Module containing the core WiFiMonitor class for monitoring connections
- **config.py**: Module containing configuration settings
- **utils/console.py**: Module providing console output functions
- **connection_monitor_guide_JP.md**: Japanese guide document explaining the module structure and usage

## Usage
See the Japanese guide document (connection_monitor_guide_JP.md) for detailed usage instructions.

## Note
This module is part of the Raspberry Pi 5 and Pico 2W Standalone Environmental Data Measurement System Ver2.0, which supports only BME680 sensors and does not support CO2 sensors (MH-Z19C).
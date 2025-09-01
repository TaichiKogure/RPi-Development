# Environmental Data Measurement System - Version History

This document provides a comprehensive history of all versions of the Environmental Data Measurement System, including the changes and improvements made in each version.

## Version 1.2 (Current)

**Release Date**: 2025-07-22

### Overview
Version 1.2 focuses on optimizing the P1 software for lighter operation, improving documentation, and simplifying the web interface.

### Key Changes

1. **P1 Software Optimization**
   - Added rest time between operations to reduce CPU load
   - Reduced data reception frequency and terminal update frequency
   - Optimized memory usage in data collection and processing
   - Implemented rate limiting for API routes

2. **Web Interface Simplification**
   - Simplified the web interface to display text information only
   - Removed graph rendering functionality to reduce resource usage
   - Improved response time for data display

3. **Documentation Improvements**
   - Created comprehensive documentation for P1-P6 folder structures and functionality
   - Added detailed explanations of each component's purpose and operation
   - Ensured all documentation includes Ver1.2 numbering
   - Created documentation in both English and Japanese

### Compatibility
- **Hardware**: Raspberry Pi 5, Raspberry Pi Pico 2W
- **Sensors**: BME680, MH-Z19B/C

## Version 1.0.0

**Release Date**: 2025-07-21

### Overview
Version 1.0.0 expanded the system from using P2 and P3 to include P4, P5, and P6 sensor nodes, creating a more comprehensive environmental monitoring network.

### Key Changes

1. **P4, P5, and P6 Software**
   - Created dedicated software directories for P4, P5, and P6 based on the P2 and P3 templates
   - Updated device identification in main.py files (DEVICE_ID = "P4", "P5", "P6")
   - Created device-specific WiFi client implementations (P4_wifi_client_debug.py, P5_wifi_client_debug.py, P6_wifi_client_debug.py)
   - Implemented error handling and watchdog functionality for all new devices

2. **P1 Software Updates**
   - Updated configuration to recognize and collect data from P4, P5, and P6
   - Added data directories for P4, P5, and P6 (RawData_P4, RawData_P5, RawData_P6)
   - Modified data collection logic to handle data from all sensor nodes
   - Updated WiFi monitoring to track connection quality with all devices

3. **Documentation Updates**
   - Updated installation guide to include P4, P5, and P6 setup instructions
   - Expanded operation manual to cover operation of the system with P4, P5, and P6
   - Updated system architecture documentation to reflect the expanded system
   - Maintained consistent version numbering (1.0.0) across all documentation

### Compatibility
- **Hardware**: Raspberry Pi 5, Raspberry Pi Pico 2W
- **Sensors**: BME680, MH-Z19B/C

## Version 0.9.0 (Beta)

**Release Date**: 2025-07-15

### Overview
Version 0.9.0 was the beta release of the Environmental Data Measurement System, featuring the initial implementation of the P1, P2, and P3 components.

### Key Features

1. **P1 (Raspberry Pi 5) Features**
   - Dual WiFi functionality (AP mode for P2/P3 and client mode for internet)
   - Data collection and storage from P2 and P3
   - Web interface for data visualization
   - Connection monitoring for P2 and P3

2. **P2 and P3 (Raspberry Pi Pico 2W) Features**
   - BME680 sensor integration for temperature, humidity, pressure, and gas resistance
   - MH-Z19B/C sensor integration for CO2 concentration
   - WiFi connectivity to P1
   - Automatic error recovery and restart

3. **Initial Documentation**
   - Basic installation guide
   - Operation manual
   - System architecture overview

### Compatibility
- **Hardware**: Raspberry Pi 5, Raspberry Pi Pico 2W
- **Sensors**: BME680, MH-Z19B/C

## Future Development Plans

### Version 1.5 (Planned)
- Raspberry Pi Zero 2W support for P1
- Automatic startup and monitoring scripts
- Self-diagnostic and recovery functionality
- Comprehensive documentation in both English and Japanese

### Version 2.0 (Planned)
- Support for additional sensor types
- Enhanced data visualization and analysis
- Remote management capabilities
- Cloud integration for data storage and access
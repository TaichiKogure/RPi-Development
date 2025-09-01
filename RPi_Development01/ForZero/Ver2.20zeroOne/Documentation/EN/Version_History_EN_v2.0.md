# Version History for Environmental Data Measurement System
**Current Version: 2.0.0 (BME680-only)**

This document provides a history of the versions of the Environmental Data Measurement System, focusing on the changes made in each version.

## Version 2.0.0 (BME680-only) - 2025-07-23

### Major Changes
- **Removed CO2 Sensor Support**: The system now works with BME680 sensors only, without MH-Z19C CO2 sensors.
- **Modified Data Collection**: Data validation and storage have been updated to work without CO2 data.
- **Updated Web Interface**: CO2-related display elements have been removed from the web interface.
- **Comprehensive Documentation**: Added detailed documentation in both English and Japanese.

### Detailed Changes

#### P1 (Raspberry Pi 5) Changes
1. **Data Collection**
   - Removed CO2 from the list of sensor fields in data validation
   - Modified data storage to include an empty field for CO2 to maintain CSV format compatibility
   - Updated absolute humidity calculation to work without CO2 data

2. **Web Interface**
   - Removed CO2 from the parameters list in dashboard graphs
   - Commented out CO2 card in the dashboard template
   - Removed CO2 reading displays for P2 and P3
   - Removed CO2 from JavaScript parameters list
   - Commented out JavaScript code for loading CO2 graphs

#### P2-P6 (Raspberry Pi Pico 2W) Changes
1. **Sensor Initialization**
   - Commented out MH-Z19C CO2 sensor initialization code
   - Set co2_sensor to None
   - Maintained BME680 sensor initialization

2. **Data Transmission**
   - Modified data transmission to exclude CO2 data
   - Commented out MH-Z19C CO2 sensor fallback code
   - Maintained BME680 data collection and transmission

#### Documentation
1. **Installation Guide**
   - Updated to reflect BME680-only setup
   - Removed MH-Z19C CO2 sensor connection instructions
   - Added notes about the system being BME680-only

2. **Operation Manual**
   - Updated to reflect BME680-only operation
   - Removed CO2-related instructions
   - Updated troubleshooting section

3. **System Architecture**
   - Updated to reflect BME680-only architecture
   - Documented the differences from previous versions
   - Explained the data flow without CO2 data

### Compatibility Notes
- CSV file format maintains compatibility with previous versions by keeping an empty field where CO2 data would have been
- Sensor nodes from previous versions need to be updated with the new software to work with this version
- Web interface from previous versions is not compatible with this version

## Version 1.7.0 - 2025-07-15

### Major Changes
- **Expanded Sensor Support**: Added support for P4, P5, and P6 sensor nodes
- **Improved Documentation**: Added comprehensive documentation in both Japanese and English
- **Raspberry Pi Zero 2W Compatibility**: Modified P1 software to work with Raspberry Pi Zero 2W

### Detailed Changes

#### P1 (Raspberry Pi) Changes
1. **Data Collection**
   - Added support for P4, P5, and P6 sensor nodes
   - Modified data storage to handle data from up to 5 sensor nodes
   - Optimized for Raspberry Pi Zero 2W with reduced resource usage

2. **Web Interface**
   - Updated to display data from P4, P5, and P6 sensor nodes
   - Added device selection for graph display
   - Improved performance for Raspberry Pi Zero 2W

#### P2-P6 (Raspberry Pi Pico 2W) Changes
1. **Configuration**
   - Updated to work with the modified P1 software
   - Added device ID configuration for P4, P5, and P6

#### Documentation
1. **Added Japanese Documentation**
   - Created Japanese versions of all documentation
   - Added detailed explanations for beginners

## Version 1.6.0 - 2025-07-10

### Major Changes
- **Updated Network Configuration**: Changed AP settings to use 192.168.0.2 as the IP address
- **Improved Documentation**: Added version numbering to documentation

### Detailed Changes

#### P1 (Raspberry Pi) Changes
1. **Access Point Setup**
   - Changed AP SSID to "RaspberryPi5_AP_Solo2"
   - Changed AP IP address to 192.168.0.2
   - Updated DHCP range

#### P2-P6 (Raspberry Pi Pico 2W) Changes
1. **WiFi Configuration**
   - Updated to connect to the new AP SSID
   - Updated server IP address

## Version 1.5.0 - 2025-07-05

### Major Changes
- **Raspberry Pi Zero 2W Support**: Added support for using Raspberry Pi Zero 2W as P1
- **Auto-start Functionality**: Added scripts for automatic startup on boot
- **Self-diagnostics**: Added self-diagnostic and recovery features

### Detailed Changes

#### P1 (Raspberry Pi) Changes
1. **Startup Scripts**
   - Added scripts for automatic startup on boot
   - Added service monitoring and restart functionality
   - Added self-diagnostic features

2. **Resource Optimization**
   - Reduced resource usage for Raspberry Pi Zero 2W
   - Added rest time between operations
   - Reduced log frequency

## Version 1.2.0 - 2025-07-01

### Major Changes
- **Improved Documentation**: Added detailed documentation for each component
- **Performance Optimization**: Reduced resource usage and added rest time
- **Simplified Web Interface**: Removed graph rendering for better performance

### Detailed Changes

#### P1 (Raspberry Pi) Changes
1. **Resource Optimization**
   - Added rest time between operations
   - Reduced terminal update frequency
   - Reduced data reception frequency

2. **Web Interface**
   - Simplified to text-only information
   - Removed graph rendering for better performance

#### Documentation
1. **Component Documentation**
   - Added detailed documentation for each component
   - Added function explanations in Japanese

## Version 1.0.0 - 2025-06-25

### Major Changes
- **Initial Release**: First version of the Environmental Data Measurement System
- **Multiple Sensor Support**: Support for P2-P6 sensor nodes
- **BME680 and MH-Z19C Sensors**: Support for temperature, humidity, pressure, gas, and CO2 measurements

### Detailed Changes

#### P1 (Raspberry Pi) Changes
1. **Data Collection**
   - Implemented data collection from sensor nodes
   - Added data storage in CSV format
   - Added absolute humidity calculation

2. **Web Interface**
   - Implemented web-based dashboard
   - Added time series graphs
   - Added connection status display

#### P2-P6 (Raspberry Pi Pico 2W) Changes
1. **Sensor Drivers**
   - Implemented BME680 sensor driver
   - Implemented MH-Z19C CO2 sensor driver

2. **Data Transmission**
   - Implemented WiFi connectivity
   - Added data transmission to P1
   - Added error handling and retry logic
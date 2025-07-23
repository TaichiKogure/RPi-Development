# Project Structure Documentation

## Overview

This document provides an overview of the project structure for the Raspberry Pi 5 AP Connection system (Version 4.60). The project is organized into several components, each with its own responsibility in the overall system.

## Main Components

The project is divided into three main components:

1. **p1_software_solo405**: Software for the Raspberry Pi 5 (P1), which acts as the central hub
2. **P2_software_debug**: Software for the Raspberry Pi Pico 2W (P2), which acts as a sensor node
3. **P3_software_debug**: Software for the Raspberry Pi Pico 2W (P3), which acts as another sensor node

## P1 Software Structure

The P1 software is organized into several modules, each with a specific responsibility:

### 1. ap_setup

This module is responsible for setting up the Raspberry Pi 5 as a WiFi access point. It includes:

- **P1_ap_setup_solo.py**: Main script for configuring and managing the access point

### 2. connection_monitor

This module monitors the WiFi connections between P1 and the sensor nodes (P2 and P3). It is organized as follows:

- **P1_wifi_monitor_solo.py**: Main entry point for the connection monitor
- **config.py**: Configuration settings for the connection monitor
- **main.py**: Main functionality for the connection monitor
- **monitor.py**: Core monitoring functionality
- **__init__.py**: Package initialization file

Submodules:
- **api/**: API for accessing connection monitoring data
  - **__init__.py**: Package initialization file
  - **routes.py**: API route definitions
  - **server.py**: API server implementation
- **measurements/**: Functionality for measuring connection quality
  - **ping.py**: Ping measurement implementation
  - **signal_strength.py**: Signal strength measurement implementation
- **utils/**: Utility functions
  - **__init__.py**: Package initialization file
  - **console.py**: Console output utilities

### 3. data_collection

This module collects data from the sensor nodes (P2 and P3). It includes:

- **P1_data_collector_solo.py**: Main script for collecting and storing sensor data

### 4. web_interface

This module provides a web interface for visualizing the collected data. It includes:

- **P1_app_solo.py**: Main script for the web interface

### 5. Root Level

- **start_p1_solo.py**: Main script for starting all P1 services

## P2 and P3 Software Structure

The P2 and P3 software have similar structures, as they both serve as sensor nodes. They include:

- **Sensor drivers**: For reading data from connected sensors
- **Data transmission**: For sending data to P1
- **Error handling**: For handling errors and auto-restarting when necessary

## Module Dependencies

The main dependencies between modules are:

1. **start_p1_solo.py** depends on all other P1 modules, as it starts all services
2. **connection_monitor** depends on the WiFi setup provided by **ap_setup**
3. **data_collection** depends on the WiFi setup provided by **ap_setup**
4. **web_interface** depends on the data collected by **data_collection** and connection status from **connection_monitor**

## Import Structure

The project uses a combination of absolute and relative imports:

- Absolute imports are used when importing from outside the current package
- Relative imports are used when importing from within the same package

For example, in the connection_monitor module:

```python
# Absolute imports (from outside the package)
import os
import sys
import time

# Relative imports (from within the package)
from connection_monitor.config import DEFAULT_CONFIG
from connection_monitor.monitor import WiFiMonitor
```

## Best Practices

When working with this project structure:

1. **Maintain package integrity**: Ensure each module has an `__init__.py` file
2. **Use appropriate imports**: Use absolute imports for clarity, especially when importing across modules
3. **Follow the module boundaries**: Keep functionality within its appropriate module
4. **Update documentation**: When changing the structure, update this documentation
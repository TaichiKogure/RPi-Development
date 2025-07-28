# Import Error Fix for P1_data_collector_solo.py

## Issue Description

The project was experiencing an error when running the `P1_data_collector_solo.py` script:

```
2025-07-07 11:42:17,337 - WARNING - Failed to import refactored modules: No module named 'p1_software_solo405'
2025-07-07 11:42:17,337 - INFO - Falling back to original implementation
Traceback (most recent call last):
  File "/home/pi/RaspPi5_APconnection/Ver4.61Debug/p1_software_solo405/data_collection/P1_data_collector_solo.py", line 592, in <module>
    main()
  File "/home/pi/RaspPi5_APconnection/Ver4.61Debug/p1_software_solo405/data_collection/P1_data_collector_solo.py", line 559, in main
    config = DEFAULT_CONFIG.copy()
             ^^^^^^^^^^^^^^
NameError: name 'DEFAULT_CONFIG' is not defined
```

This error occurred because:
1. The script was trying to import from the refactored modules but couldn't find the `p1_software_solo405` package
2. When the import failed, it tried to use `DEFAULT_CONFIG` without defining a fallback

## Root Cause

There were several issues with the script:

1. **Missing Python Path Configuration**: The script wasn't adding the parent directory to the Python path correctly, so it couldn't find the `p1_software_solo405` package.

2. **No Fallback for Failed Imports**: When the import failed, the script tried to use `DEFAULT_CONFIG` without defining a fallback.

3. **Missing Imports**: The script was using several modules (`threading`, `datetime`, `json`, `csv`, `socket`, `time`) without importing them.

4. **Incomplete Import Error Handling**: The script only tried to import from one location and didn't have a robust fallback mechanism.

## Solution

The solution involved several changes:

1. **Added Missing Imports**:
   ```python
   import threading
   import datetime
   import json
   import csv
   import socket
   import time
   ```

2. **Defined Fallback Configurations**:
   ```python
   # Define fallback configurations in case imports fail
   FALLBACK_DEFAULT_CONFIG = {
       "listen_port": 5000,
       "data_dir": "/var/lib(FromThonny)/raspap_solo/data",
       "rawdata_p2_dir": "RawData_P2",
       "rawdata_p3_dir": "RawData_P3",
       "api_port": 5001,
       "max_file_size_mb": 10,
       "rotation_interval_days": 7,
       "device_timeout_seconds": 120
   }

   FALLBACK_MONITOR_CONFIG = {
       "devices": {
           "P2": {
               "ip": None,
               "mac": None,
               "channel": 6
           },
           "P3": {
               "ip": None,
               "mac": None,
               "channel": 6
           }
       },
       "update_interval": 5,
       "ping_count": 3,
       "ping_timeout": 1
   }
   ```

3. **Improved Import Error Handling**:
   ```python
   # Import from the refactored modules
   try:
       # Try to import from the refactored package structure
       from p1_software_solo405.data_collection.config import DEFAULT_CONFIG, MONITOR_CONFIG
       from p1_software_solo405.data_collection.main import DataCollector, main as refactored_main
       logger.info("Successfully imported refactored modules from p1_software_solo405 package")
       # Use the refactored implementation
       if __name__ == "__main__":
           refactored_main()
           sys.exit(0)
   except ImportError as e:
       logger.warning(f"Failed to import from p1_software_solo405 package: {e}")
       
       # Try to import from relative path
       try:
           from data_collection.config import DEFAULT_CONFIG, MONITOR_CONFIG
           from data_collection.main import DataCollector, main as refactored_main
           logger.info("Successfully imported refactored modules from relative path")
           # Use the refactored implementation
           if __name__ == "__main__":
               refactored_main()
               sys.exit(0)
       except ImportError as e:
           logger.warning(f"Failed to import from relative path: {e}")
           logger.info("Falling back to original implementation")
           # Use fallback configurations
           DEFAULT_CONFIG = FALLBACK_DEFAULT_CONFIG
           MONITOR_CONFIG = FALLBACK_MONITOR_CONFIG
           # Continue with the original implementation below
   ```

4. **Added Robust Import for Flask and WiFiMonitor**:
   ```python
   # Import Flask for API
   try:
       from flask import Flask, jsonify, request
   except ImportError as e:
       logger.error(f"Failed to import Flask: {e}")
       logger.error("Flask is required for the API server. Please install it with 'pip install flask'.")
       sys.exit(1)

   # Try to import WiFiMonitor for dynamic IP tracking
   try:
       from p1_software_solo405.connection_monitor.monitor import WiFiMonitor
   except ImportError:
       try:
           from connection_monitor.monitor import WiFiMonitor
       except ImportError:
           logger.warning("Failed to import WiFiMonitor. Dynamic IP tracking will be disabled.")
           WiFiMonitor = None
   ```

## Testing the Fix

To verify that the fix works:

1. Run the `P1_data_collector_solo.py` script directly:
   ```
   python p1_software_solo405/data_collection/P1_data_collector_solo.py
   ```

2. Check that no errors occur and the script runs as expected.

3. Verify that the script still works when called from `start_p1_solo.py`.

## Best Practices for Python Imports

To avoid similar issues in the future, consider the following best practices:

1. **Always provide fallbacks for imports that might fail**: Define default configurations or alternative implementations that can be used if imports fail.

2. **Add all necessary imports at the top of the file**: Make sure all modules used in the script are imported at the top of the file.

3. **Use try-except blocks for imports that might fail**: This allows the script to handle import errors gracefully.

4. **Add the parent directory to the Python path**: This ensures that the script can find packages in the parent directory.

5. **Use absolute imports when possible**: Absolute imports are more explicit and less prone to errors when the project structure changes.
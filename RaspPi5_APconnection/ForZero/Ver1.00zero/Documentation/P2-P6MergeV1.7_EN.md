# P2-P6 Merge Changelog Ver1.7

## Overview
This update adds functionality to collect, store, and display environmental data from up to five sensor nodes (P2-P6) with a Raspberry Pi Zero 2W (P1) as the central hub. Previous versions only supported two sensor nodes (P2 and P3), but this update adds support for three additional sensor nodes (P4, P5, and P6).

## Changes

### Data Collection Module
1. **CSVManager**
   - Updated to handle data from P4, P5, and P6 in addition to P2 and P3
   - Updated the following methods:
     - `_init_csv_files`: Initialize CSV files for P4, P5, and P6
     - `rotate_csv_files`: Rotate CSV files for P4, P5, and P6
     - `cleanup_old_files`: Clean up old CSV files for P4, P5, and P6
     - `close`: Close CSV files for P4, P5, and P6

2. **Configuration Files**
   - Added `rawdata_p2_dir` and `rawdata_p3_dir` to `config.py`
   - Added P2 and P3 entries to `MONITOR_CONFIG`
   - Updated the `ensure_data_directories` function to create directories for P2 and P3 as well

### Web Interface
1. **Data Retrieval**
   - Updated the `get_historical_data` method to retrieve data for P4, P5, and P6 as well

2. **Graph Creation**
   - Updated the `create_time_series_graph` method:
     - Added `show_p4`, `show_p5`, and `show_p6` parameters to the method signature
     - Added timestamp processing for P4, P5, and P6
     - Added data logging for P4, P5, and P6
     - Added data validation and graph creation for P4, P5, and P6
   - Updated the `create_dashboard_graphs` method:
     - Added `show_p4`, `show_p5`, and `show_p6` parameters to the method signature
     - Updated to pass parameters to `create_time_series_graph`

3. **API Endpoints**
   - Updated the `/dashboard` route:
     - Added retrieval of `show_p4`, `show_p5`, and `show_p6` parameters
     - Updated to pass parameters to the template
   - Updated the `/api/graphs` route:
     - Added retrieval of `show_p4`, `show_p5`, and `show_p6` parameters
     - Updated to pass parameters to `create_dashboard_graphs`
   - Updated the `/api/export/<device_id>` route:
     - Added P4, P5, and P6 to the `device_id` check
   - Updated the `/api/device/<device_id>` route:
     - Added P4, P5, and P6 to the `device_id` check

## Usage
After this update, P1 can collect data from up to five sensor nodes (P2-P6). The web interface allows you to show or hide data from each sensor node individually.

### Sensor Node Configuration
Configure P4, P5, and P6 sensor nodes in the same way as P2 and P3:
1. Set the device ID appropriately ("P4", "P5", or "P6")
2. Set the WiFi SSID to "RaspberryPi5_AP_Solo2"
3. Set the WiFi password to "raspberry"
4. Set the server IP to "192.168.0.2"
5. Set the server port to 5000

### Using the Web Interface
The web interface allows you to:
1. Select which sensor nodes (P2-P6) to display on the dashboard page
2. Select the time period (number of days) of data to display
3. View graphs of each environmental parameter (temperature, humidity, pressure, etc.)
4. Export data from selected sensor nodes as CSV files

## Notes
- To use P4, P5, and P6 sensor nodes, you need to configure each device appropriately and connect them to P1's WiFi network.
- Directories for each sensor node (RawData_P2 through RawData_P6) will be automatically created in P1's data directory (/var/lib/raspap_solo/data).
- Existing P2 and P3 configurations are unchanged, so these devices will continue to work as before.

## Future Plans
- Enhance connection quality monitoring between sensor nodes
- Add data analysis features
- Implement alert functionality
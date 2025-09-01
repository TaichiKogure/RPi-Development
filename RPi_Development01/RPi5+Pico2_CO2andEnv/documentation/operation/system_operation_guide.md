# Environmental Data Measurement System Operation Guide
Version: 2.0.0

This guide provides detailed instructions for operating the Raspberry Pi 5 and Pico 2W environmental data measurement system after installation.

## Table of Contents
1. [System Overview](#system-overview)
2. [Starting the System](#starting-the-system)
3. [Accessing the Web Interface](#accessing-the-web-interface)
4. [Dashboard Overview](#dashboard-overview)
5. [Viewing Real-time Data](#viewing-real-time-data)
6. [Viewing Historical Data](#viewing-historical-data)
7. [Exporting Data](#exporting-data)
8. [Monitoring Connection Quality](#monitoring-connection-quality)
9. [System Maintenance](#system-maintenance)
10. [Power Management](#power-management)
11. [Common Tasks](#common-tasks)

## System Overview
The environmental data measurement system consists of:
- **P1 (Raspberry Pi 5)**: Central hub that acts as a WiFi access point, collects data, and provides a web interface
- **P2 and P3 (Raspberry Pi Pico 2W)**: Sensor nodes that collect environmental data and transmit it to P1
- **Sensors**: BME680 (temperature, humidity, pressure, gas) and MH-Z19B (CO2)

The system operates as follows:
1. P2 and P3 collect environmental data every 30 seconds
2. The data is transmitted to P1 via WiFi
3. P1 stores the data and makes it available through a web interface
4. Users can view real-time and historical data, and export it for analysis

## Starting the System
### Starting P1 (Raspberry Pi 5)
1. Connect the Raspberry Pi 5 to power.
2. The system will boot automatically and start the following services:
   - Access point service (hostapd)
   - DHCP server (dnsmasq)
   - Data collection service
   - Web interface
   - Connection monitor

3. Wait approximately 2 minutes for all services to start.
4. The access point will be available with the SSID "RaspberryPi5_AP" (default).

### Starting P2 and P3 (Raspberry Pi Pico 2W)
1. Connect the Pico 2W devices to power.
2. The devices will boot automatically and run the main.py script.
3. The onboard LED will indicate the status:
   - Rapid blinking: Attempting to connect to WiFi
   - Solid on: Connected to WiFi
   - Occasional blink: Data transmission
   - Pattern of blinks: Error code (see Troubleshooting Guide)

4. The devices will automatically connect to P1's WiFi network and begin transmitting data.

## Accessing the Web Interface
1. Connect your device (smartphone, tablet, or computer) to the "RaspberryPi5_AP" WiFi network.
   - Default password: "raspberry"

2. Open a web browser and navigate to:
   ```
   http://192.168.0.1
   ```

   > Note: If you configured a different IP address during setup, use that instead.

3. The environmental data dashboard should load, showing the current readings from P2 and P3.

4. If you cannot access the dashboard:
   - Verify that you're connected to the correct WiFi network
   - Try accessing the IP address directly
   - Check that all services are running on P1 (see Troubleshooting Guide)

## Dashboard Overview
The dashboard consists of several sections:

### Home Page
- System overview with current status
- Quick view of the latest readings from P2 and P3
- Navigation to detailed dashboards for each device

### Device Dashboards (P2 and P3)
- Current readings panel showing the latest sensor values
- Time-series graphs for each environmental parameter:
  - Temperature (°C)
  - Humidity (%)
  - Pressure (hPa)
  - Gas resistance (Ohms)
  - CO2 level (ppm)
- Data export tools
- Time range selector (1 day, 1 week, 1 month)

### Connection Monitor
- Signal strength indicators for P2 and P3
- Ping times and connection quality metrics
- Historical connection data

## Viewing Real-time Data
1. From the home page, click on either "P2 Dashboard" or "P3 Dashboard" to view detailed data for a specific device.

2. The "Current Readings" panel shows the latest values for:
   - Temperature
   - Humidity
   - Pressure
   - Gas resistance
   - CO2 level

3. The data automatically refreshes every 30 seconds.

4. To manually refresh the data, click the refresh button in your browser.

5. The timestamp of the last update is shown at the bottom of the page.

## Viewing Historical Data
1. From a device dashboard (P2 or P3), use the time range selector buttons to choose the period:
   - 1 Day (default)
   - 1 Week
   - 1 Month

2. The graphs will update to show data for the selected time period.

3. Hover over any point on a graph to see the exact value and timestamp.

4. Use the graph controls to:
   - Zoom in/out
   - Pan left/right
   - Reset the view
   - Download the graph as an image

5. To view a specific parameter in more detail, click on its graph to expand it.

## Exporting Data
1. From a device dashboard (P2 or P3), locate the "Export Data" panel.

2. Select the date range for the data you want to export:
   - Start date
   - End date

3. Click the "Export CSV" button.

4. A CSV file will be downloaded to your device containing all data points within the selected date range.

5. The CSV file includes the following columns:
   - timestamp
   - device_id
   - temperature
   - humidity
   - pressure
   - gas_resistance
   - co2_level

6. You can open this file in spreadsheet software (e.g., Excel, Google Sheets) or data analysis tools for further processing.

## Monitoring Connection Quality
1. From the home page, click on "Connection Monitor" to view the connection quality dashboard.

2. The dashboard shows:
   - Current signal strength for P2 and P3 (in dBm)
   - Signal-to-noise ratio
   - Ping times (in ms)
   - Connection status (online/offline)

3. The signal strength is categorized as:
   - Excellent: -50 dBm or higher
   - Very Good: -50 to -60 dBm
   - Good: -60 to -70 dBm
   - Fair: -70 to -80 dBm
   - Poor: below -80 dBm

4. Historical connection data is shown as graphs, allowing you to identify patterns or issues over time.

5. Use this information to optimize the placement of P2 and P3 devices for the best connection quality.

## System Maintenance
### Checking System Status
1. Connect to the Raspberry Pi 5 via SSH or directly with a keyboard and monitor.

2. Check the status of all services:
   ```bash
   sudo systemctl status hostapd
   sudo systemctl status dnsmasq
   sudo systemctl status data_collector.service
   sudo systemctl status web_interface.service
   sudo systemctl status wifi_monitor.service
   ```

3. Check the system logs for any errors:
   ```bash
   sudo journalctl -u data_collector.service -n 50
   sudo journalctl -u web_interface.service -n 50
   sudo journalctl -u wifi_monitor.service -n 50
   ```

### Restarting Services
If a service is not working correctly, you can restart it:

1. Restart the data collector:
   ```bash
   sudo systemctl restart data_collector.service
   ```

2. Restart the web interface:
   ```bash
   sudo systemctl restart web_interface.service
   ```

3. Restart the connection monitor:
   ```bash
   sudo systemctl restart wifi_monitor.service
   ```

4. Restart the access point:
   ```bash
   sudo systemctl restart hostapd
   sudo systemctl restart dnsmasq
   ```

### Checking Disk Space
1. Check available disk space:
   ```bash
   df -h
   ```

2. If disk space is low, you can remove old data files:
   ```bash
   # List data files by size
   du -h /var/lib(FromThonny)/raspap/data | sort -h

   # Remove old files (example: files older than 30 days)
   find /var/lib(FromThonny)/raspap/data -name "*.csv" -type f -mtime +30 -delete
   ```

### System Updates
1. Update the Raspberry Pi OS:
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```

2. Reboot after updates:
   ```bash
   sudo reboot
   ```

## Power Management
### P1 (Raspberry Pi 5)
- The Raspberry Pi 5 should be connected to a stable power supply at all times.
- If using a battery backup or UPS, ensure it can provide at least 5V/3A.
- To safely shut down the Raspberry Pi 5:
  ```bash
  sudo shutdown -h now
  ```
- Wait for the system to fully shut down before disconnecting power.

### P2 and P3 (Raspberry Pi Pico 2W)
- The Pico 2W devices can be powered via USB or an external power supply.
- For battery-powered operation, consider using a power bank or battery pack with USB output.
- The Pico 2W devices will automatically restart if they encounter errors.
- To manually restart a Pico 2W, disconnect and reconnect the power.

## Common Tasks
### Changing the WiFi Password
1. Connect to the Raspberry Pi 5 via SSH or directly.

2. Run the access point configuration script:
   ```bash
   sudo python3 ~/RPi_Development01/p1_software/ap_setup/ap_setup.py --configure
   ```

3. Follow the prompts to update the password.

4. Reboot the Raspberry Pi 5:
   ```bash
   sudo reboot
   ```

5. Update the configuration on P2 and P3 devices to use the new password.

### Adjusting Data Collection Interval
1. Connect to the Raspberry Pi 5 via SSH or directly.

2. Edit the data collector configuration:
   ```bash
   sudo nano ~/RPi_Development01/p1_software/data_collection/data_collector.py
   ```

3. Locate the `DEFAULT_CONFIG` section and modify the relevant parameters.

4. Save the file and restart the service:
   ```bash
   sudo systemctl restart data_collector.service
   ```

5. For P2 and P3 devices, connect them to your computer and use Thonny to edit the main.py file, adjusting the `TRANSMISSION_INTERVAL` value.

### Backing Up Data
1. Connect to the Raspberry Pi 5 via SSH or directly.

2. Create a backup of the data directory:
   ```bash
   sudo tar -czvf ~/environmental_data_backup_$(date +%Y%m%d).tar.gz /var/lib(FromThonny)/raspap/data
   ```

3. Copy the backup file to another device or storage medium:
   ```bash
   # Example: Copy to a USB drive
   sudo cp ~/environmental_data_backup_*.tar.gz /media/pi/USB_DRIVE/

   # Example: Copy using SCP (from another computer)
   scp pi@192.168.0.1:~/environmental_data_backup_*.tar.gz /path/on/your/computer/
   ```

### Resetting P2 and P3 Devices
If a Pico 2W device is not functioning correctly:

1. Connect the device to your computer using a USB cable.

2. Open Thonny IDE and connect to the device.

3. If the device is responsive, you can run:
   ```python
   import machine
   machine.reset()
   ```

4. If the device is unresponsive, hold the BOOTSEL button while connecting the USB cable, then reinstall the MicroPython firmware and project files.

For more detailed information on specific tasks or troubleshooting, refer to the [Troubleshooting Guide](../troubleshooting/troubleshooting_guide.md).

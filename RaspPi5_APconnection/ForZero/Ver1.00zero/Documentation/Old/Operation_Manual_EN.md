# Raspberry Pi 5 and Pico 2W Standalone Environmental Data Measurement System - Operation Manual

**Version: 1.0.0**

This manual provides instructions for operating the Raspberry Pi 5 and Pico 2W Standalone Environmental Data Measurement System after installation.

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Starting the System](#2-starting-the-system)
3. [Using the Web Interface](#3-using-the-web-interface)
4. [Monitoring Connection Quality](#4-monitoring-connection-quality)
5. [Data Management](#5-data-management)
6. [System Maintenance](#6-system-maintenance)
7. [Troubleshooting](#7-troubleshooting)

## 1. System Overview

The Raspberry Pi 5 and Pico 2W Standalone Environmental Data Measurement System consists of:

- **P1 (Raspberry Pi 5)**: Central hub that acts as a WiFi access point, collects data, and provides a web interface
- **P4, P5, P6 (Raspberry Pi Pico 2W)**: Sensor nodes that collect environmental data and transmit it to P1
- **Sensors**: BME680 (temperature, humidity, pressure, gas) and MH-Z19B (CO2)

The system operates as follows:

1. P1 creates a WiFi access point that P4, P5, and P6 connect to
2. P4, P5, and P6 collect data from their sensors and transmit it to P1
3. P1 stores the data and provides a web interface for visualization
4. P1 monitors the connection quality with P4, P5, and P6

## 2. Starting the System

### 2.1 Starting P1 (Raspberry Pi 5)

1. Power on the Raspberry Pi 5.
2. The system will automatically start the access point and other services if configured to do so.
3. If the services are not started automatically, SSH into the Raspberry Pi 5 and run:
   ```bash
   cd ~/RaspPi5_APconnection/ForZero/Ver1.00zero
   source ~/envmonitor-venv/bin/activate
   sudo python3 p1_software_Zero/start_p1_solo.py
   ```

### 2.2 Starting P4, P5, P6 (Raspberry Pi Pico 2W)

1. Power on each Pico 2W device.
2. The devices will automatically run the `main.py` script, which initializes the sensors, connects to P1's WiFi access point, and starts collecting and transmitting data.
3. The onboard LED will indicate the status:
   - Blinking once: Successful data transmission
   - Blinking twice: Data transmission failure
   - Blinking three times: Error

### 2.3 Verifying System Operation

1. SSH into the Raspberry Pi 5.
2. Check if the access point is active:
   ```bash
   sudo systemctl status hostapd
   sudo systemctl status dnsmasq
   ```
3. Check if the data collection service is running:
   ```bash
   ps aux | grep P1_data_collector_solo.py
   ```
4. Check if the web interface is running:
   ```bash
   ps aux | grep P1_app_solo.py
   ```
5. Check if the connection monitor is running:
   ```bash
   ps aux | grep P1_wifi_monitor_solo.py
   ```

## 3. Using the Web Interface

### 3.1 Accessing the Web Interface

1. Connect a device (smartphone, tablet, laptop) to the P1's WiFi access point (SSID: "RaspberryPi5_AP_Solo").
2. Open a web browser and navigate to `http://192.168.0.1`.
3. The web interface should load, displaying the environmental data from P4, P5, and P6.

### 3.2 Dashboard Overview

The dashboard displays the following information:

- **Latest Data**: Current readings from P4, P5, and P6 sensors
- **Time Series Graphs**: Historical data for temperature, humidity, pressure, gas resistance, and CO2
- **Connection Status**: WiFi signal strength, ping times, and noise levels for P4, P5, and P6

### 3.3 Viewing Historical Data

1. On the dashboard, you can select the time range for the graphs:
   - 1 Day (default)
   - 7 Days
   - 30 Days
   - Custom range

2. You can toggle the display of data from specific devices:
   - P4
   - P5
   - P6

3. You can also select which parameters to display:
   - Temperature
   - Humidity
   - Absolute Humidity (calculated from temperature and humidity)
   - Pressure
   - Gas Resistance
   - CO2 Concentration

### 3.4 Downloading Data

1. On the dashboard, click the "Download Data" button.
2. Select the device(s) and time range for the data you want to download.
3. Click "Download CSV" to download the data in CSV format.

## 4. Monitoring Connection Quality

### 4.1 Using the Web Interface

1. On the dashboard, navigate to the "Connection Status" section.
2. This section displays the following information for each device:
   - Signal Strength (dBm)
   - Ping Time (ms)
   - Noise Level (dBm)
   - Signal-to-Noise Ratio (SNR)
   - Connection Status (Online/Offline)

### 4.2 Using the Command Line

1. SSH into the Raspberry Pi 5.
2. Run the connection monitor status command:
   ```bash
   cd ~/RaspPi5_APconnection/ForZero/Ver1.00zero
   source ~/envmonitor-venv/bin/activate
   sudo python3 p1_software_Zero/connection_monitor/P1_wifi_monitor_solo.py --status
   ```
3. This will display the current connection status for all devices.

### 4.3 Optimizing Device Placement

Use the connection quality information to optimize the placement of P4, P5, and P6:

- Signal Strength: Should be stronger than -70 dBm for reliable connection
- Ping Time: Should be less than 100 ms for good responsiveness
- SNR: Should be greater than 20 dB for good signal quality

## 5. Data Management

### 5.1 Data Storage Structure

Data is stored in the following locations:

- `/var/lib/raspap_solo/data/RawData_P4/`: Data from P4
- `/var/lib/raspap_solo/data/RawData_P5/`: Data from P5
- `/var/lib/raspap_solo/data/RawData_P6/`: Data from P6

Within each directory, data is stored in two types of files:

1. Date-based files: `P4_YYYY-MM-DD.csv`, `P5_YYYY-MM-DD.csv`, `P6_YYYY-MM-DD.csv`
2. Fixed files: `P4_fixed.csv`, `P5_fixed.csv`, `P6_fixed.csv` (contain the most recent data)

### 5.2 Data Backup

To back up the data:

1. SSH into the Raspberry Pi 5.
2. Create a backup directory:
   ```bash
   mkdir -p ~/backups/$(date +%Y-%m-%d)
   ```
3. Copy the data files:
   ```bash
   cp -r /var/lib(FromThonny)/raspap_solo/data/RawData_P4 ~/backups/$(date +%Y-%m-%d)/
   cp -r /var/lib(FromThonny)/raspap_solo/data/RawData_P5 ~/backups/$(date +%Y-%m-%d)/
   cp -r /var/lib(FromThonny)/raspap_solo/data/RawData_P6 ~/backups/$(date +%Y-%m-%d)/
   ```
4. Optionally, compress the backup:
   ```bash
   cd ~/backups
   tar -czvf $(date +%Y-%m-%d).tar.gz $(date +%Y-%m-%d)
   ```
5. Transfer the backup to another device using SCP or other methods.

### 5.3 Data Cleanup

To clean up old data:

1. SSH into the Raspberry Pi 5.
2. Navigate to the data directory:
   ```bash
   cd /var/lib(FromThonny)/raspap_solo/data
   ```
3. List all data files:
   ```bash
   find RawData_P4 RawData_P5 RawData_P6 -name "*.csv" | sort
   ```
4. Remove files older than a certain date (e.g., 90 days):
   ```bash
   find RawData_P4 RawData_P5 RawData_P6 -name "*.csv" -type f -mtime +90 -delete
   ```

## 6. System Maintenance

### 6.1 Updating the System

To update the Raspberry Pi 5 system:

1. SSH into the Raspberry Pi 5.
2. Update the package lists:
   ```bash
   sudo apt update
   ```
3. Upgrade the packages:
   ```bash
   sudo apt upgrade -y
   ```
4. Reboot if necessary:
   ```bash
   sudo reboot
   ```

### 6.2 Updating the Software

To update the environmental monitoring software:

1. SSH into the Raspberry Pi 5.
2. Navigate to the project directory:
   ```bash
   cd ~/RaspPi5_APconnection
   ```
3. Pull the latest changes (if using Git):
   ```bash
   git pull
   ```
4. Alternatively, copy the updated files from your development environment.
5. Restart the services:
   ```bash
   cd ~/RaspPi5_APconnection/ForZero/Ver1.00zero
   source ~/envmonitor-venv/bin/activate
   sudo python3 p1_software_Zero/start_p1_solo.py --restart
   ```

### 6.3 Updating P4, P5, P6 Firmware

To update the firmware on P4, P5, and P6:

1. Connect the Pico 2W to your computer.
2. Open Thonny IDE.
3. Upload the updated files to the Pico 2W.
4. Restart the Pico 2W.

### 6.4 Log Management

The system generates logs in the following locations:

- `/var/log/data_collector_solo.log`: Data collection logs
- `/var/log/web_interface_solo.log`: Web interface logs
- `/var/log/wifi_monitor_solo.log`: Connection monitor logs

To manage logs:

1. SSH into the Raspberry Pi 5.
2. View the logs:
   ```bash
   tail -n 100 /var/log/data_collector_solo.log
   tail -n 100 /var/log/web_interface_solo.log
   tail -n 100 /var/log/wifi_monitor_solo.log
   ```
3. Rotate logs if they become too large:
   ```bash
   sudo logrotate -f /etc/logrotate.d/rsyslog
   ```

## 7. Troubleshooting

### 7.1 P1 (Raspberry Pi 5) Issues

#### Access Point Not Working

1. Check the status of the hostapd and dnsmasq services:
   ```bash
   sudo systemctl status hostapd
   sudo systemctl status dnsmasq
   ```
2. If either service is not running, start it:
   ```bash
   sudo systemctl start hostapd
   sudo systemctl start dnsmasq
   ```
3. If the services fail to start, reconfigure the access point:
   ```bash
   cd ~/RaspPi5_APconnection/ForZero/Ver1.00zero
   source ~/envmonitor-venv/bin/activate
   sudo python3 p1_software_Zero/ap_setup/P1_ap_setup_solo.py --configure
   ```

#### Data Collection Not Working

1. Check if the data collection service is running:
   ```bash
   ps aux | grep P1_data_collector_solo.py
   ```
2. If not running, start it:
   ```bash
   cd ~/RaspPi5_APconnection/ForZero/Ver1.00zero
   source ~/envmonitor-venv/bin/activate
   sudo python3 p1_software_Zero/data_collection/P1_data_collector_solo.py
   ```
3. Check the logs for errors:
   ```bash
   tail -n 100 /var/log/data_collector_solo.log
   ```

#### Web Interface Not Working

1. Check if the web interface is running:
   ```bash
   ps aux | grep P1_app_solo.py
   ```
2. If not running, start it:
   ```bash
   cd ~/RaspPi5_APconnection/ForZero/Ver1.00zero
   source ~/envmonitor-venv/bin/activate
   sudo python3 p1_software_Zero/web_interface/P1_app_solo.py
   ```
3. Check the logs for errors:
   ```bash
   tail -n 100 /var/log/web_interface_solo.log
   ```

### 7.2 P4, P5, P6 (Raspberry Pi Pico 2W) Issues

#### Device Not Connecting to WiFi

1. Check if the device is powered on.
2. Check if the LED is blinking (indicating activity).
3. If the LED is blinking three times repeatedly, there is an error.
4. Connect the device to a computer and use Thonny IDE to check the error messages.
5. Verify that the WiFi credentials in the `main.py` file are correct.
6. Restart the device by pressing the reset button or power cycling.

#### Sensor Reading Errors

1. Connect the device to a computer and use Thonny IDE to check the error messages.
2. Verify that the sensors are properly connected.
3. Check the I2C address for the BME680 sensor (0x76 or 0x77).
4. Check the UART pins for the MH-Z19B sensor.
5. If necessary, update the sensor driver files.

#### Data Transmission Errors

1. Check if P1 is properly set up as an access point.
2. Verify that P4, P5, and P6 are connecting to the correct WiFi network.
3. Check if the server IP and port in the `main.py` file are correct.
4. Reduce the distance between P1 and the sensor nodes.
5. Remove obstacles between P1 and the sensor nodes.

For more detailed troubleshooting, refer to the Troubleshooting Guide.
# Environmental Data Measurement System Troubleshooting Guide
Version: 2.0.0

This guide provides detailed troubleshooting steps for common issues that may arise with the Raspberry Pi 5 and Pico 2W environmental data measurement system.

## Table of Contents
1. [Diagnostic Tools](#diagnostic-tools)
2. [P1 (Raspberry Pi 5) Issues](#p1-raspberry-pi-5-issues)
   - [Boot Problems](#boot-problems)
   - [Access Point Issues](#access-point-issues)
   - [Data Collection Issues](#data-collection-issues)
   - [Web Interface Issues](#web-interface-issues)
   - [Connection Monitor Issues](#connection-monitor-issues)
3. [P2/P3 (Raspberry Pi Pico 2W) Issues](#p2p3-raspberry-pi-pico-2w-issues)
   - [Boot Problems](#pico-boot-problems)
   - [Sensor Issues](#sensor-issues)
   - [WiFi Connection Issues](#wifi-connection-issues)
   - [Data Transmission Issues](#data-transmission-issues)
   - [Error Codes](#error-codes)
4. [System-Wide Issues](#system-wide-issues)
   - [Data Synchronization Issues](#data-synchronization-issues)
   - [Time Synchronization Issues](#time-synchronization-issues)
   - [Performance Issues](#performance-issues)
5. [Recovery Procedures](#recovery-procedures)
   - [P1 Recovery](#p1-recovery)
   - [P2/P3 Recovery](#p2p3-recovery)
   - [Data Recovery](#data-recovery)

## Diagnostic Tools
Before troubleshooting specific issues, it's helpful to use these diagnostic tools to gather information about the system state.

### P1 (Raspberry Pi 5) Diagnostic Tools
1. **System Logs**
   ```bash
   # View system boot logs
   sudo journalctl -b

   # View logs for specific services
   sudo journalctl -u hostapd
   sudo journalctl -u dnsmasq
   sudo journalctl -u data_collector.service
   sudo journalctl -u web_interface.service
   sudo journalctl -u wifi_monitor.service
   ```

2. **Service Status**
   ```bash
   # Check status of all services
   sudo systemctl status hostapd
   sudo systemctl status dnsmasq
   sudo systemctl status data_collector.service
   sudo systemctl status web_interface.service
   sudo systemctl status wifi_monitor.service
   ```

3. **Network Diagnostics**
   ```bash
   # Check network interfaces
   ifconfig

   # Check WiFi status
   iwconfig

   # Check access point status
   sudo iw dev wlan0 info

   # Check connected clients
   sudo iw dev wlan0 station dump
   ```

4. **System Resources**
   ```bash
   # Check CPU and memory usage
   htop

   # Check disk space
   df -h

   # Check temperature
   vcgencmd measure_temp
   ```

### P2/P3 (Raspberry Pi Pico 2W) Diagnostic Tools
1. **Connect to Pico via Thonny IDE**
   - Open Thonny IDE
   - Connect to the Pico 2W
   - Use the REPL console to run diagnostic commands

2. **Basic Diagnostics**
   ```python
   # Check MicroPython version
   import sys
   print(sys.version)

   # Check available modules
   help('modules')

   # Check file system
   import os
   print(os.listdir())

   # Check error log
   with open('/error_log.txt', 'r') as f:
       print(f.read())
   ```

3. **Network Diagnostics**
   ```python
   # Check WiFi status
   import network
   wlan = network.WLAN(network.STA_IF)
   print("Connected:", wlan.isconnected())
   print("Config:", wlan.ifconfig())
   ```

4. **Sensor Diagnostics**
   ```python
   # Test BME680 sensor
   import sys
   sys.path.append('/sensor_drivers')
   import bme680_driver

   try:
       sensor = bme680_driver.BME680Sensor()
       readings = sensor.get_readings()
       print("BME680 readings:", readings)
   except Exception as e:
       print("BME680 error:", e)

   # Test MH-Z19B sensor
   import mhz19b_driver

   try:
       sensor = mhz19b_driver.MHZ19BSensor()
       co2 = sensor.read_co2()
       print("CO2 level:", co2)
   except Exception as e:
       print("MH-Z19B error:", e)
   ```

## P1 (Raspberry Pi 5) Issues
### Boot Problems
1. **Raspberry Pi won't boot (no power LED)**
   - Check power supply (should be 5V/3A or higher)
   - Try a different USB-C cable
   - Check for physical damage to the power port

2. **Raspberry Pi shows red power LED but doesn't boot**
   - Check if the microSD card is properly inserted
   - Try a different microSD card
   - Reinstall the operating system

3. **Raspberry Pi boots but doesn't reach login prompt**
   - Connect a monitor to check for error messages
   - Press Esc to see boot messages
   - Try booting in recovery mode by holding Shift during boot

### Access Point Issues
1. **Access point not appearing in WiFi list**
   - Check if hostapd service is running:
     ```bash
     sudo systemctl status hostapd
     ```
   - Restart the hostapd service:
     ```bash
     sudo systemctl restart hostapd
     ```
   - Check hostapd configuration:
     ```bash
     sudo cat /etc/hostapd/hostapd.conf
     ```
   - Verify that the WiFi interface is up:
     ```bash
     sudo ifconfig wlan0 up
     ```

2. **Cannot connect to access point**
   - Verify the password is correct
   - Check if DHCP server is running:
     ```bash
     sudo systemctl status dnsmasq
     ```
   - Restart the DHCP server:
     ```bash
     sudo systemctl restart dnsmasq
     ```
   - Check for IP address conflicts

3. **Access point disconnects frequently**
   - Check for interference from other WiFi networks
   - Try changing the channel in hostapd.conf
   - Check system temperature (overheating can cause WiFi issues)
   - Update the Raspberry Pi firmware:
     ```bash
     sudo rpi-update
     ```

### Data Collection Issues
1. **Data collector service not running**
   - Check the service status:
     ```bash
     sudo systemctl status data_collector.service
     ```
   - Check the logs for errors:
     ```bash
     sudo journalctl -u data_collector.service -n 100
     ```
   - Restart the service:
     ```bash
     sudo systemctl restart data_collector.service
     ```

2. **Data not being received from P2/P3**
   - Check if P2/P3 devices are connected to the WiFi network:
     ```bash
     sudo iw dev wlan0 station dump
     ```
   - Verify that the data collector is listening on the correct port:
     ```bash
     sudo netstat -tuln | grep 5000
     ```
   - Check firewall settings:
     ```bash
     sudo iptables -L
     ```

3. **Data files not being created**
   - Check permissions on the data directory:
     ```bash
     ls -la /var/lib/raspap/data
     ```
   - Verify that the data directory exists:
     ```bash
     sudo mkdir -p /var/lib/raspap/data
     sudo chown -R pi:pi /var/lib/raspap/data
     ```
   - Check disk space:
     ```bash
     df -h
     ```

### Web Interface Issues
1. **Web interface not accessible**
   - Check if the web interface service is running:
     ```bash
     sudo systemctl status web_interface.service
     ```
   - Check if the service is listening on the correct port:
     ```bash
     sudo netstat -tuln | grep 80
     ```
   - Restart the web interface service:
     ```bash
     sudo systemctl restart web_interface.service
     ```

2. **Web interface shows "No data available"**
   - Check if data files exist:
     ```bash
     ls -la /var/lib/raspap/data
     ```
   - Verify that the data collector is running and receiving data
   - Check the web interface logs for errors:
     ```bash
     sudo journalctl -u web_interface.service -n 100
     ```

3. **Graphs not displaying correctly**
   - Clear your browser cache
   - Try a different browser
   - Check if the required JavaScript libraries are loading (check browser console)
   - Verify that the data format is correct:
     ```bash
     head -n 10 /var/lib/raspap/data/P2_*.csv
     ```

### Connection Monitor Issues
1. **Connection monitor not showing data**
   - Check if the connection monitor service is running:
     ```bash
     sudo systemctl status wifi_monitor.service
     ```
   - Restart the connection monitor service:
     ```bash
     sudo systemctl restart wifi_monitor.service
     ```
   - Check the logs for errors:
     ```bash
     sudo journalctl -u wifi_monitor.service -n 100
     ```

2. **Incorrect signal strength readings**
   - Verify that P2/P3 devices are connected to the WiFi network
   - Check if the correct MAC addresses are being monitored
   - Try moving P2/P3 devices closer to P1 to see if readings improve

## P2/P3 (Raspberry Pi Pico 2W) Issues
### Pico Boot Problems
1. **Pico not powering on (no LED activity)**
   - Try a different USB cable
   - Try a different power source
   - Check for physical damage to the USB port

2. **Pico powers on but doesn't run the program**
   - Connect to Thonny IDE to check for errors
   - Verify that main.py exists on the Pico
   - Check if MicroPython is properly installed

3. **Pico resets repeatedly**
   - Check the error log:
     ```python
     with open('/error_log.txt', 'r') as f:
         print(f.read())
     ```
   - Verify that the watchdog timeout is not too short
   - Check for hardware issues (unstable power supply)

### Sensor Issues
1. **BME680 sensor not detected**
   - Check the I2C connections (SDA and SCL)
   - Verify that the sensor is receiving power (3.3V and GND)
   - Try a different I2C address (0x76 or 0x77):
     ```python
     import sys
     sys.path.append('/sensor_drivers')
     import bme680_driver

     try:
         # Try alternate address
         sensor = bme680_driver.BME680Sensor(address=0x77)
         readings = sensor.get_readings()
         print("BME680 readings:", readings)
     except Exception as e:
         print("BME680 error:", e)
     ```

2. **MH-Z19B sensor not responding**
   - Check the UART connections (TX and RX)
   - Ensure the sensor is receiving 5V power
   - Try a different UART ID or pins:
     ```python
     import sys
     sys.path.append('/sensor_drivers')
     import mhz19b_driver

     try:
         # Try alternate UART configuration
         sensor = mhz19b_driver.MHZ19BSensor(uart_id=0, tx_pin=0, rx_pin=1)
         co2 = sensor.read_co2()
         print("CO2 level:", co2)
     except Exception as e:
         print("MH-Z19B error:", e)
     ```

3. **Sensor readings out of range**
   - Check if the sensor is properly calibrated
   - Verify that the sensor is not exposed to extreme conditions
   - For MH-Z19B, try calibrating the zero point:
     ```python
     import sys
     sys.path.append('/sensor_drivers')
     import mhz19b_driver

     sensor = mhz19b_driver.MHZ19BSensor()
     sensor.calibrate_zero_point()
     ```

### WiFi Connection Issues
1. **Cannot connect to WiFi network**
   - Verify that the SSID and password are correct
   - Check if the Raspberry Pi 5 access point is running
   - Try moving the Pico closer to the access point
   - Check WiFi status:
     ```python
     import network
     wlan = network.WLAN(network.STA_IF)
     wlan.active(True)
     print("Scanning networks:")
     for network in wlan.scan():
         print(network[0].decode(), network[3])
     ```

2. **WiFi connection drops frequently**
   - Check signal strength:
     ```python
     import network
     wlan = network.WLAN(network.STA_IF)
     print("RSSI:", wlan.status('rssi'))
     ```
   - Move the Pico closer to the access point
   - Check for interference from other devices
   - Verify that the power supply is stable

### Data Transmission Issues
1. **Data not being sent to P1**
   - Check if the Pico is connected to WiFi
   - Verify that the server IP and port are correct
   - Test the connection:
     ```python
     import socket

     try:
         s = socket.socket()
         s.connect(('192.168.0.1', 5000))
         s.send(b'{"test": true}')
         response = s.recv(1024)
         print("Response:", response)
         s.close()
     except Exception as e:
         print("Connection error:", e)
     ```

2. **Server rejecting data**
   - Check the data format
   - Verify that all required fields are included
   - Check the data collector logs on P1 for error messages

### Error Codes
The Pico 2W devices use LED blink patterns to indicate error codes:

1. **1 blink**: Sensor error (BME680)
   - Check BME680 connections
   - Verify that the sensor is not damaged
   - Try reinitializing the sensor

2. **2 blinks**: WiFi error
   - Check WiFi credentials
   - Verify that the access point is running
   - Move the Pico closer to the access point

3. **3 blinks**: Memory error
   - Restart the Pico
   - Check for memory leaks in the code
   - Reduce the complexity of the program

4. **4 blinks**: Timeout error
   - Check for slow operations
   - Increase timeout values
   - Verify that the watchdog timeout is sufficient

5. **9 blinks**: Unknown error
   - Check the error log for details
   - Restart the Pico
   - Reinstall the software

## System-Wide Issues
### Data Synchronization Issues
1. **Data timestamps don't match**
   - Check if the Raspberry Pi 5's clock is correct:
     ```bash
     date
     ```
   - Set up NTP for automatic time synchronization:
     ```bash
     sudo apt install -y ntp
     sudo systemctl enable ntp
     sudo systemctl start ntp
     ```
   - Adjust the time manually if needed:
     ```bash
     sudo date -s "YYYY-MM-DD HH:MM:SS"
     ```

2. **Missing data points**
   - Check if P2/P3 devices are consistently connected
   - Verify that the data collection interval is set correctly
   - Check for errors in the data transmission process

### Time Synchronization Issues
1. **System time incorrect**
   - Connect the Raspberry Pi 5 to the internet to use NTP
   - Set up a local NTP server if internet is not available
   - Use a real-time clock (RTC) module for accurate timekeeping

2. **Time drifts over time**
   - Install and configure chrony for better time synchronization:
     ```bash
     sudo apt install -y chrony
     sudo systemctl enable chronyd
     sudo systemctl start chronyd
     ```
   - Add a battery-backed RTC module to the Raspberry Pi 5

### Performance Issues
1. **System running slowly**
   - Check CPU and memory usage:
     ```bash
     htop
     ```
   - Check for processes using excessive resources:
     ```bash
     ps aux --sort=-%cpu | head -10
     ```
   - Check disk I/O:
     ```bash
     iostat -x 1
     ```

2. **Web interface slow to load**
   - Reduce the number of data points displayed in graphs
   - Optimize the data storage format
   - Check network performance between client and server

3. **High CPU temperature**
   - Check the temperature:
     ```bash
     vcgencmd measure_temp
     ```
   - Improve cooling (add heatsinks or a fan)
   - Reduce CPU usage by optimizing services

## Recovery Procedures
### P1 Recovery
1. **Backup Important Data**
   ```bash
   # Create a backup of data files
   sudo tar -czvf ~/data_backup.tar.gz /var/lib/raspap/data

   # Backup configuration files
   sudo tar -czvf ~/config_backup.tar.gz /etc/hostapd /etc/dnsmasq.conf /etc/dhcpcd.conf
   ```

2. **Reinstall Operating System**
   - Download the latest Raspberry Pi OS image
   - Use Raspberry Pi Imager to write the image to the microSD card
   - Boot from the new microSD card

3. **Restore Configuration**
   - Copy the backup files to the Raspberry Pi
   - Extract the configuration files:
     ```bash
     sudo tar -xzvf ~/config_backup.tar.gz -C /
     ```
   - Reinstall required packages and services
   - Restore data files:
     ```bash
     sudo mkdir -p /var/lib/raspap/data
     sudo tar -xzvf ~/data_backup.tar.gz -C /
     ```

### P2/P3 Recovery
1. **Reset to Factory State**
   - Hold the BOOTSEL button while connecting power
   - The Pico will appear as a USB drive
   - Copy the MicroPython UF2 file to the drive

2. **Reinstall Software**
   - Connect to the Pico using Thonny IDE
   - Create the required directories
   - Upload all the project files

3. **Reconfigure Settings**
   - Edit the main.py file to set the correct device ID and WiFi credentials
   - Test the sensors and WiFi connection
   - Verify that data is being transmitted correctly

### Data Recovery
1. **Recover from Backup**
   - Locate the most recent backup
   - Extract the data files:
     ```bash
     sudo tar -xzvf ~/environmental_data_backup_YYYYMMDD.tar.gz -C /tmp
     ```
   - Copy the files to the data directory:
     ```bash
     sudo cp -r /tmp/var/lib/raspap/data/* /var/lib/raspap/data/
     ```

2. **Repair Corrupted CSV Files**
   - Check for corrupted files:
     ```bash
     find /var/lib/raspap/data -name "*.csv" -exec file {} \;
     ```
   - Fix CSV headers if needed:
     ```bash
     for f in /var/lib/raspap/data/*.csv; do
       if ! head -1 "$f" | grep -q "timestamp"; then
         echo "timestamp,device_id,temperature,humidity,pressure,gas_resistance,co2_level" > /tmp/header
         cat "$f" >> /tmp/header
         mv /tmp/header "$f"
       fi
     done
     ```

3. **Merge Data Files**
   - If you have multiple partial data files, you can merge them:
     ```bash
     # First, ensure all files have headers
     for f in /var/lib/raspap/data/P2_*.csv; do
       if ! head -1 "$f" | grep -q "timestamp"; then
         echo "timestamp,device_id,temperature,humidity,pressure,gas_resistance,co2_level" > /tmp/header
         cat "$f" >> /tmp/header
         mv /tmp/header "$f"
       fi
     done

     # Then merge files (skipping headers except for the first file)
     head -1 "$(ls /var/lib/raspap/data/P2_*.csv | head -1)" > /var/lib/raspap/data/P2_merged.csv
     for f in /var/lib/raspap/data/P2_*.csv; do
       tail -n +2 "$f" >> /var/lib/raspap/data/P2_merged.csv
     done

     # Sort by timestamp
     sort -t, -k1,1 /var/lib/raspap/data/P2_merged.csv > /var/lib/raspap/data/P2_sorted.csv
     ```

For additional assistance or if you encounter issues not covered in this guide, please refer to the [Raspberry Pi documentation](https://www.raspberrypi.org/documentation/) or the [MicroPython documentation](https://docs.micropython.org/).

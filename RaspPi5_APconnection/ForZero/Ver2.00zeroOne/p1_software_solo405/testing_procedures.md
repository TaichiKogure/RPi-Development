# Testing Procedures for start_p1_solo.py Ver2.0

This document outlines the testing procedures that should be performed to ensure the modified `start_p1_solo.py` script works correctly with the Ver2.0 requirements.

## Prerequisites

1. Raspberry Pi 5 with Raspberry Pi OS installed
2. Python virtual environment set up at `~/envmonitor-venv/`
3. Required Python packages installed:
   ```bash
   ~/envmonitor-venv/bin/pip install flask pandas psutil
   ```
4. P4, P5, and P6 devices with BME680 sensors configured and operational

## Basic Functionality Tests

### 1. Script Execution Test

```bash
sudo ~/envmonitor-venv/bin/python3 start_p1_solo.py
```

**Expected Results:**
- Script should start without errors
- All services (AP setup, data collection, web interface, connection monitor) should start successfully
- Status message should show "Ver2.0" and mention "BME680 sensors only (no CO2 sensors)"

### 2. Access Point Test

- Check if the access point is running:
  ```bash
  sudo systemctl status hostapd
  ```
- Verify the access point configuration:
  ```bash
  sudo cat /etc/hostapd/hostapd.conf
  ```
- Connect a device to the access point and verify connectivity

**Expected Results:**
- hostapd service should be active
- Access point should be broadcasting with the configured SSID
- Devices should be able to connect to the access point

### 3. Data Collection Test

- Check if the data collection service is running:
  ```bash
  ps aux | grep P1_data_collector_solo.py
  ```
- Verify data is being collected:
  ```bash
  ls -la /var/lib/raspap_solo/data/RawData_P4/
  ls -la /var/lib/raspap_solo/data/RawData_P5/
  ls -la /var/lib/raspap_solo/data/RawData_P6/
  ```
- Examine the CSV files:
  ```bash
  head -n 5 /var/lib/raspap_solo/data/RawData_P4/P4_fixed.csv
  ```

**Expected Results:**
- Data collection process should be running
- CSV files should be created in the appropriate directories
- CSV files should have headers without a "co2" column
- Data should be continuously added to the CSV files

### 4. Web Interface Test

- Check if the web interface is running:
  ```bash
  ps aux | grep P1_app_simple.py
  ```
- Access the web interface in a browser:
  ```
  http://<Raspberry_Pi_IP>:<web_port>
  ```

**Expected Results:**
- Web interface process should be running
- Web interface should be accessible in a browser
- Data from P4, P5, and P6 should be displayed
- No CO2 data should be displayed or mentioned in the interface

### 5. Connection Monitor Test

- Check if the connection monitor is running:
  ```bash
  ps aux | grep P1_wifi_monitor_solo.py
  ```
- Verify connection status is being updated:
  ```bash
  tail -f /var/log/wifi_monitor_solo.log
  ```

**Expected Results:**
- Connection monitor process should be running
- Log should show connection status updates for P4, P5, and P6

## Enhanced Features Tests

### 1. System Resource Monitoring Test

- Check if system resource monitoring is active:
  ```bash
  tail -f /var/log/p1_startup_solo.log | grep "System resources"
  ```

**Expected Results:**
- Log should show periodic updates of memory and CPU usage
- If thresholds are exceeded, warnings should be logged

### 2. Service Restart Test

- Manually kill one of the services:
  ```bash
  sudo kill <PID_of_service>
  ```
- Monitor the restart process:
  ```bash
  tail -f /var/log/p1_startup_solo.log
  ```

**Expected Results:**
- Service should be automatically restarted
- Log should show restart attempt with appropriate delay
- Status message should indicate the service was restarted

### 3. Systemd Service Creation Test

- Create the systemd service:
  ```bash
  sudo ~/envmonitor-venv/bin/python3 start_p1_solo.py --create-service
  ```
- Check if the service was created:
  ```bash
  sudo systemctl status p1-environmental-monitor.service
  ```
- Reboot the system and check if services start automatically:
  ```bash
  sudo reboot
  ```

**Expected Results:**
- Systemd service should be created and enabled
- After reboot, all services should start automatically
- Log should show successful startup

## Data Validation Tests

### 1. BME680 Data Validation

- Send test data from P4, P5, or P6 with valid BME680 readings
- Send test data with invalid BME680 readings (out of range)

**Expected Results:**
- Valid data should be accepted and stored
- Invalid data should be rejected with appropriate error messages

### 2. CO2 Data Handling

- Send test data from P4, P5, or P6 that includes CO2 readings

**Expected Results:**
- Data should be accepted but CO2 readings should be ignored
- CSV files should not contain CO2 data
- No errors should occur due to the presence of CO2 data

## Performance Tests

### 1. Resource Usage Test

- Monitor CPU and memory usage during operation:
  ```bash
  top
  ```
- Check disk usage growth:
  ```bash
  du -sh /var/lib/raspap_solo/data/
  ```

**Expected Results:**
- CPU and memory usage should be reasonable
- Disk usage should grow at an expected rate

### 2. Multiple Device Test

- Connect multiple devices (P4, P5, P6) simultaneously
- Monitor data collection and connection status

**Expected Results:**
- All devices should be able to connect and send data
- System should handle multiple connections without issues

## Error Handling Tests

### 1. Network Interruption Test

- Temporarily disconnect P4, P5, or P6 from the network
- Reconnect the device after a few minutes

**Expected Results:**
- Connection monitor should detect the disconnection
- When reconnected, data collection should resume without issues

### 2. Disk Space Test

- Fill up the disk space to near capacity
- Monitor system behavior

**Expected Results:**
- System should log warnings about low disk space
- Services should continue to function or gracefully degrade

## Conclusion

After completing these tests, the modified `start_p1_solo.py` script should be verified to work correctly with the Ver2.0 requirements, specifically:

1. Supporting only BME680 sensors (no CO2 sensors)
2. Providing enhanced system monitoring and restart mechanisms
3. Offering systemd service creation for auto-starting on boot
4. Including delays between service starts to reduce resource contention

Any issues encountered during testing should be documented and addressed before deploying the script to production environments.
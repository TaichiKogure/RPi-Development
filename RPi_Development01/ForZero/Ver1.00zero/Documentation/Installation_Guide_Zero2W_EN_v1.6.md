# Standalone Environmental Data Measurement System with Raspberry Pi Zero 2W and Pico 2W - Installation Guide

**Version: 1.6.0**

This guide explains the installation and setup procedures for the standalone environmental data measurement system using Raspberry Pi Zero 2W and Pico 2W. In Ver1.6, the system's network configuration has been updated with a new access point SSID and IP address to improve network management and avoid conflicts with other devices.

## Table of Contents

1. [System Requirements](#1-system-requirements)
2. [Hardware Setup](#2-hardware-setup)
3. [P1 (Raspberry Pi Zero 2W) Setup](#3-p1-raspberry-pi-zero-2w-setup)
4. [P4, P5, P6 (Raspberry Pi Pico 2W) Setup](#4-p4-p5-p6-raspberry-pi-pico-2w-setup)
5. [Auto-start Configuration](#5-auto-start-configuration)
6. [System Testing](#6-system-testing)
7. [Troubleshooting](#7-troubleshooting)

## 1. System Requirements

### Hardware Requirements

- 1 × Raspberry Pi Zero 2W (P1)
- 3 × Raspberry Pi Pico 2W (P4, P5, P6)
- 3 × BME680 sensors
- 3 × MH-Z19B CO2 sensors
- Power supplies for all devices
- MicroSD card for Raspberry Pi Zero 2W (16GB or larger)
- USB cables for programming Raspberry Pi Pico 2W
- Jumper wires for sensor connections

### Software Requirements

- Raspberry Pi OS Lite (32-bit recommended) for Raspberry Pi Zero 2W
- MicroPython for Raspberry Pi Pico 2W
- Thonny IDE for programming Raspberry Pi Pico 2W

## 2. Hardware Setup

### 2.1 Raspberry Pi Zero 2W (P1) Hardware Setup

1. Insert the MicroSD card into the Raspberry Pi Zero 2W.
2. Connect the power supply to the Raspberry Pi Zero 2W.
3. Connect a monitor, keyboard, and mouse for initial setup (or use SSH connection).

### 2.2 Raspberry Pi Pico 2W (P4, P5, P6) Hardware Setup

For each Pico 2W (P4, P5, P6), connect the BME680 sensor and MH-Z19B CO2 sensor as follows:

#### BME680 Sensor Connection

| BME680 Pin | Pico 2W Pin |
|------------|-------------|
| VCC        | 3.3V (Pin 36) |
| GND        | GND (Pin 38) |
| SCL        | GP1 (Pin 2) |
| SDA        | GP0 (Pin 1) |

#### MH-Z19B CO2 Sensor Connection

| MH-Z19B Pin | Pico 2W Pin |
|-------------|-------------|
| VCC (Red)   | VBUS (5V, Pin 40) |
| GND (Black) | GND (Pin 38) |
| TX (Green)  | GP9 (Pin 12) |
| RX (Blue)   | GP8 (Pin 11) |

## 3. P1 (Raspberry Pi Zero 2W) Setup

### 3.1 Operating System Installation

1. Download Raspberry Pi Imager from [https://www.raspberrypi.org/software/](https://www.raspberrypi.org/software/).
2. Insert the MicroSD card into your computer.
3. Launch Raspberry Pi Imager.
4. Select "Raspberry Pi OS Lite (32-bit)" as the operating system (to minimize resource usage).
5. Select the MicroSD card as the storage.
6. Click the gear icon to access advanced options:
   - Set hostname to "raspberrypi"
   - Enable SSH
   - Set username and password
   - Configure WiFi (if internet access is needed)
7. Click "Write" to write the OS to the MicroSD card.
8. Insert the MicroSD card into the Raspberry Pi Zero 2W and power it on.

### 3.2 Initial Configuration

1. Connect to the Raspberry Pi Zero 2W via SSH or use a connected monitor and keyboard.
2. Update the system:
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```
3. Install required packages:
   ```bash
   sudo apt install -y python3-pip python3-venv hostapd dnsmasq git
   ```

### 3.3 Python Virtual Environment Setup

1. Create a virtual environment:
   ```bash
   cd ~
   python3 -m venv envmonitor-venv
   source envmonitor-venv/bin/activate
   ```
2. Install required Python packages:
   ```bash
   pip install flask flask-socketio pandas plotly psutil
   ```
   Note: psutil is used for system resource monitoring. The system will still function without it, but resource monitoring will be disabled.

### 3.4 Software Download and Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/RaspPi5_APconnection.git
   cd RPi_Development01
   ```
   
   Or copy the files from your development environment to the Raspberry Pi Zero 2W.

2. Create necessary directories:
   ```bash
   sudo mkdir -p /var/lib(FromThonny)/raspap_solo/data
   sudo mkdir -p /var/lib(FromThonny)/raspap_solo/data/RawData_P4
   sudo mkdir -p /var/lib(FromThonny)/raspap_solo/data/RawData_P5
   sudo mkdir -p /var/lib(FromThonny)/raspap_solo/data/RawData_P6
   sudo mkdir -p /var/lib(FromThonny)/raspap_solo/logs
   sudo mkdir -p /var/log
   ```

3. Set permissions:
   ```bash
   sudo chown -R pi:pi /var/lib(FromThonny)/raspap_solo
   ```

### 3.5 Access Point Configuration

1. Run the setup script to configure the access point:
   ```bash
   cd ~/RPi_Development01/ForZero/Ver1.00zero
   source ~/envmonitor-venv/bin/activate
   sudo python3 p1_software_Zero/ap_setup/P1_ap_setup_solo.py --configure
   ```
   
   Note: In Ver1.6, the access point is configured with the SSID "RaspberryPi5_AP_Solo2" and IP address "192.168.0.2".

2. Restart the Raspberry Pi Zero 2W:
   ```bash
   sudo reboot
   ```

3. After restarting, verify that the access point is active:
   ```bash
   sudo systemctl status hostapd
   sudo systemctl status dnsmasq
   ```

## 4. P4, P5, P6 (Raspberry Pi Pico 2W) Setup

### 4.1 Install MicroPython on Pico 2W

For each Pico 2W (P4, P5, P6):

1. Download the latest MicroPython UF2 file for Raspberry Pi Pico W from [https://micropython.org/download/rp2-pico-w/](https://micropython.org/download/rp2-pico-w/).
2. Press and hold the BOOTSEL button while connecting the Pico 2W to your computer.
3. Release the BOOTSEL button after connecting.
4. The Pico 2W will appear as a USB drive.
5. Copy the downloaded UF2 file to the Pico 2W USB drive.
6. The Pico 2W will automatically restart and install MicroPython.

### 4.2 Install Thonny IDE

1. Download and install Thonny IDE from [https://thonny.org/](https://thonny.org/).
2. Launch Thonny IDE.
3. Go to Tools > Options > Interpreter.
4. Select "MicroPython (Raspberry Pi Pico)" as the interpreter.
5. Select the appropriate COM port for the Pico 2W.

### 4.3 Upload Software to P4

1. Connect the P4 Pico 2W to your computer.
2. In Thonny IDE, create the following directory structure on the Pico 2W:
   - `/sensor_drivers`
   - `/data_transmission`
   - `/error_handling`

3. Upload the following files to the Pico 2W:
   - `main.py` to the root directory
   - `bme680.py` and `mhz19c.py` to the `/sensor_drivers` directory
   - `P4_wifi_client_debug.py` and `wifi_client.py` to the `/data_transmission` directory
   - `P4_watchdog_debug.py` and `watchdog.py` to the `/error_handling` directory

4. Verify that all files have been uploaded correctly.

### 4.4 Upload Software to P5

Repeat the steps in 4.3, but use P5-specific files:
   - `main.py` to the root directory
   - `bme680.py` and `mhz19c.py` to the `/sensor_drivers` directory
   - `P5_wifi_client_debug.py` and `wifi_client.py` to the `/data_transmission` directory
   - `P5_watchdog_debug.py` and `watchdog.py` to the `/error_handling` directory

### 4.5 Upload Software to P6

Repeat the steps in 4.3, but use P6-specific files:
   - `main.py` to the root directory
   - `bme680.py` and `mhz19c.py` to the `/sensor_drivers` directory
   - `P6_wifi_client_debug.py` and `wifi_client.py` to the `/data_transmission` directory
   - `P6_watchdog_debug.py` and `watchdog.py` to the `/error_handling` directory

## 5. Auto-start Configuration

In Ver1.5, functionality has been added to automatically start the system when the Raspberry Pi Zero 2W powers on.

### 5.1 Create systemd Service

1. Connect to the Raspberry Pi Zero 2W via SSH or use a connected monitor and keyboard.
2. Activate the virtual environment:
   ```bash
   source ~/envmonitor-venv/bin/activate
   ```
3. Create the systemd service:
   ```bash
   cd ~/RPi_Development01/ForZero/Ver1.00zero
   sudo python3 p1_software_Zero/NotUse_start_p1_solo_v1.5.py --create-service
   ```
4. Verify that the service was created successfully:
   ```bash
   sudo systemctl status p1-environmental-monitor.service
   ```

### 5.2 Test Auto-start

1. Restart the Raspberry Pi Zero 2W:
   ```bash
   sudo reboot
   ```
2. After restarting, verify that the service started automatically:
   ```bash
   sudo systemctl status p1-environmental-monitor.service
   ```
3. Check the logs to verify that all components started correctly:
   ```bash
   tail -n 100 /var/log/p1_startup_solo_v1.5.log
   ```

## 6. System Testing

### 6.1 Start P1 Services Manually (if auto-start is not configured)

1. Connect to the Raspberry Pi Zero 2W via SSH or use a connected monitor and keyboard.
2. Navigate to the project directory:
   ```bash
   cd ~/RPi_Development01/ForZero/Ver1.00zero
   ```
3. Activate the virtual environment:
   ```bash
   source ~/envmonitor-venv/bin/activate
   ```
4. Start the P1 services:
   ```bash
   sudo python3 p1_software_Zero/NotUse_start_p1_solo_v1.5.py
   ```

### 6.2 Test P4, P5, P6 Connections

1. Power on P4, P5, and P6.
2. Wait for them to connect to P1's access point (SSID: "RaspberryPi5_AP_Solo2").
3. Check the connection status on P1:
   ```bash
   sudo python3 p1_software_Zero/connection_monitor/monitor_v1.2.py --status
   ```

### 6.3 Verify Data Collection

1. Check if data is being collected on P1:
   ```bash
   ls -la /var/lib(FromThonny)/raspap_solo/data/RawData_P4
   ls -la /var/lib(FromThonny)/raspap_solo/data/RawData_P5
   ls -la /var/lib(FromThonny)/raspap_solo/data/RawData_P6
   ```

2. Display the latest data:
   ```bash
   tail -n 10 /var/lib(FromThonny)/raspap_solo/data/RawData_P4/P4_fixed.csv
   tail -n 10 /var/lib(FromThonny)/raspap_solo/data/RawData_P5/P5_fixed.csv
   tail -n 10 /var/lib(FromThonny)/raspap_solo/data/RawData_P6/P6_fixed.csv
   ```

### 6.4 Access Web Interface

1. Open a web browser on a device connected to P1's access point.
2. Navigate to `http://192.168.0.2`.
3. Verify that the web interface loads and displays data from P4, P5, and P6.

## 7. Troubleshooting

### 7.1 P1 Issues

- **Access point not working**
  - Check the status of hostapd and dnsmasq:
    ```bash
    sudo systemctl status hostapd
    sudo systemctl status dnsmasq
    ```
  - Reconfigure the access point:
    ```bash
    sudo python3 p1_software_Zero/ap_setup/P1_ap_setup_solo.py --configure
    ```

- **Data collection not working**
  - Check the data collection service:
    ```bash
    sudo python3 p1_software_Zero/data_collection/P1_data_collector_solo_v1.2.py --status
    ```
  - Check the logs:
    ```bash
    tail -n 100 /var/log/data_collector_solo.log
    ```

- **Web interface not working**
  - Check the web interface service:
    ```bash
    sudo python3 p1_software_Zero/web_interface/P1_app_simple_v1.2.py --status
    ```
  - Check the logs:
    ```bash
    tail -n 100 /var/log/web_interface_solo.log
    ```

- **Auto-start not working**
  - Check the systemd service status:
    ```bash
    sudo systemctl status p1-environmental-monitor.service
    ```
  - Check the logs:
    ```bash
    tail -n 100 /var/log/p1_startup_solo_v1.5.log
    ```
  - Restart the service manually:
    ```bash
    sudo systemctl restart p1-environmental-monitor.service
    ```

### 7.2 P4, P5, P6 Issues

- **WiFi connection issues**
  - Verify that the Pico 2W is connecting to the correct WiFi network (SSID: "RaspberryPi5_AP_Solo2").
  - Check the WiFi credentials in the `main.py` file.
  - Check the LED status:
    - 1 blink: Data transmission successful
    - 2 blinks: Data transmission failed
    - 3 blinks: Error

- **Sensor issues**
  - Check the sensor connections.
  - Verify that the BME680 sensor's I2C address is correct (0x76 or 0x77).
  - Check the UART pins for the MH-Z19B sensor.

### 7.3 Verifying Self-Diagnostic and Recovery Mechanisms

In Ver1.5, self-diagnostic and recovery mechanisms have been added. To verify that these features are working correctly:

1. Check the process monitoring logs:
   ```bash
   tail -n 100 /var/log/p1_startup_solo_v1.5.log
   ```

2. Check system resource usage (if psutil is installed):
   ```bash
   grep "System resources" /var/log/p1_startup_solo_v1.5.log
   ```

3. Check the automatic process restart history:
   ```bash
   grep "Restarting" /var/log/p1_startup_solo_v1.5.log
   ```

4. Check the system reboot history:
   ```bash
   grep "Rebooting system" /var/log/p1_startup_solo_v1.5.log
   ```

For more detailed troubleshooting, refer to the troubleshooting guide.
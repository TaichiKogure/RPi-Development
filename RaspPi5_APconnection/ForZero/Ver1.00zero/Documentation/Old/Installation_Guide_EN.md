# Raspberry Pi 5 and Pico 2W Standalone Environmental Data Measurement System - Installation Guide

**Version: 1.0.0**

This guide provides step-by-step instructions for installing and setting up the Raspberry Pi 5 and Pico 2W Standalone Environmental Data Measurement System.

## Table of Contents

1. [System Requirements](#1-system-requirements)
2. [Hardware Setup](#2-hardware-setup)
3. [P1 (Raspberry Pi 5) Setup](#3-p1-raspberry-pi-5-setup)
4. [P4, P5, P6 (Raspberry Pi Pico 2W) Setup](#4-p4-p5-p6-raspberry-pi-pico-2w-setup)
5. [Testing the System](#5-testing-the-system)
6. [Troubleshooting](#6-troubleshooting)

## 1. System Requirements

### Hardware Requirements

- 1 × Raspberry Pi 5 (P1)
- 3 × Raspberry Pi Pico 2W (P4, P5, P6)
- 3 × BME680 sensors
- 3 × MH-Z19B CO2 sensors
- Power supplies for all devices
- MicroSD card (16GB or larger) for Raspberry Pi 5
- USB cables for programming Raspberry Pi Pico 2W
- Jumper wires for connecting sensors

### Software Requirements

- Raspberry Pi OS (64-bit) for Raspberry Pi 5
- MicroPython for Raspberry Pi Pico 2W
- Thonny IDE for programming Raspberry Pi Pico 2W

## 2. Hardware Setup

### 2.1 Raspberry Pi 5 (P1) Hardware Setup

1. Insert the MicroSD card into the Raspberry Pi 5.
2. Connect the power supply to the Raspberry Pi 5.
3. Connect a monitor, keyboard, and mouse for initial setup.

### 2.2 Raspberry Pi Pico 2W (P4, P5, P6) Hardware Setup

For each Pico 2W, connect the BME680 sensor and MH-Z19B CO2 sensor as follows:

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
| VCC (red)   | VBUS (5V, Pin 40) |
| GND (black) | GND (Pin 38) |
| TX (green)  | GP9 (Pin 12) |
| RX (blue)   | GP8 (Pin 11) |

## 3. P1 (Raspberry Pi 5) Setup

### 3.1 Operating System Installation

1. Download the Raspberry Pi Imager from [https://www.raspberrypi.org/software/](https://www.raspberrypi.org/software/).
2. Insert the MicroSD card into your computer.
3. Launch the Raspberry Pi Imager.
4. Select "Raspberry Pi OS (64-bit)" as the operating system.
5. Select your MicroSD card as the storage.
6. Click on the gear icon to access advanced options:
   - Set hostname to "raspberrypi"
   - Enable SSH
   - Set username and password
   - Configure WiFi (if needed for internet access)
7. Click "Write" to flash the OS to the MicroSD card.
8. Insert the MicroSD card into the Raspberry Pi 5 and power it on.

### 3.2 Initial Configuration

1. Connect to the Raspberry Pi 5 via SSH or use the connected monitor and keyboard.
2. Update the system:
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```
3. Install required packages:
   ```bash
   sudo apt install -y python3-pip python3-venv hostapd dnsmasq git
   ```

### 3.3 Set Up Python Virtual Environment

1. Create a virtual environment:
   ```bash
   cd ~
   python3 -m venv envmonitor-venv
   source envmonitor-venv/bin/activate
   ```
2. Install required Python packages:
   ```bash
   pip install flask flask-socketio pandas plotly
   ```

### 3.4 Download and Install the Software

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/RaspPi5_APconnection.git
   cd RaspPi5_APconnection
   ```
   
   Alternatively, copy the files from your development environment to the Raspberry Pi 5.

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

### 3.5 Configure Access Point

1. Configure the access point by running the setup script:
   ```bash
   cd ~/RaspPi5_APconnection/ForZero/Ver1.00zero
   source ~/envmonitor-venv/bin/activate
   sudo python3 p1_software_Zero/ap_setup/P1_ap_setup_solo.py --configure
   ```

2. Reboot the Raspberry Pi 5:
   ```bash
   sudo reboot
   ```

3. After reboot, verify that the access point is active:
   ```bash
   sudo systemctl status hostapd
   sudo systemctl status dnsmasq
   ```

## 4. P4, P5, P6 (Raspberry Pi Pico 2W) Setup

### 4.1 Install MicroPython on Pico 2W

For each Pico 2W (P4, P5, P6):

1. Download the latest MicroPython UF2 file for Raspberry Pi Pico W from [https://micropython.org/download/rp2-pico-w/](https://micropython.org/download/rp2-pico-w/).
2. Connect the Pico 2W to your computer while holding the BOOTSEL button.
3. Release the BOOTSEL button after connecting.
4. The Pico 2W should appear as a USB drive.
5. Copy the downloaded UF2 file to the Pico 2W USB drive.
6. The Pico 2W will automatically reboot and install MicroPython.

### 4.2 Install Thonny IDE

1. Download and install Thonny IDE from [https://thonny.org/](https://thonny.org/).
2. Launch Thonny IDE.
3. Go to Tools > Options > Interpreter.
4. Select "MicroPython (Raspberry Pi Pico)" as the interpreter.
5. Select the appropriate COM port for your Pico 2W.

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

4. Verify that all files are uploaded correctly.

### 4.4 Upload Software to P5

Repeat the steps from 4.3, but use the P5-specific files:
   - `main.py` to the root directory
   - `bme680.py` and `mhz19c.py` to the `/sensor_drivers` directory
   - `P5_wifi_client_debug.py` and `wifi_client.py` to the `/data_transmission` directory
   - `P5_watchdog_debug.py` and `watchdog.py` to the `/error_handling` directory

### 4.5 Upload Software to P6

Repeat the steps from 4.3, but use the P6-specific files:
   - `main.py` to the root directory
   - `bme680.py` and `mhz19c.py` to the `/sensor_drivers` directory
   - `P6_wifi_client_debug.py` and `wifi_client.py` to the `/data_transmission` directory
   - `P6_watchdog_debug.py` and `watchdog.py` to the `/error_handling` directory

## 5. Testing the System

### 5.1 Start P1 Services

1. SSH into the Raspberry Pi 5 or use the connected monitor and keyboard.
2. Navigate to the project directory:
   ```bash
   cd ~/RaspPi5_APconnection/ForZero/Ver1.00zero
   ```
3. Activate the virtual environment:
   ```bash
   source ~/envmonitor-venv/bin/activate
   ```
4. Start the P1 services:
   ```bash
   sudo python3 p1_software_Zero/start_p1_solo.py
   ```

### 5.2 Test P4, P5, P6 Connectivity

1. Power on P4, P5, and P6.
2. Wait for them to connect to the P1 access point.
3. On P1, check the connection status:
   ```bash
   sudo python3 p1_software_Zero/connection_monitor/P1_wifi_monitor_solo.py --status
   ```

### 5.3 Verify Data Collection

1. On P1, check if data is being collected:
   ```bash
   ls -la /var/lib(FromThonny)/raspap_solo/data/RawData_P4
   ls -la /var/lib(FromThonny)/raspap_solo/data/RawData_P5
   ls -la /var/lib(FromThonny)/raspap_solo/data/RawData_P6
   ```

2. View the latest data:
   ```bash
   tail -n 10 /var/lib(FromThonny)/raspap_solo/data/RawData_P4/P4_fixed.csv
   tail -n 10 /var/lib(FromThonny)/raspap_solo/data/RawData_P5/P5_fixed.csv
   tail -n 10 /var/lib(FromThonny)/raspap_solo/data/RawData_P6/P6_fixed.csv
   ```

### 5.4 Access Web Interface

1. From a device connected to the P1 access point, open a web browser.
2. Navigate to `http://192.168.0.1`.
3. Verify that the web interface loads and displays data from P4, P5, and P6.

## 6. Troubleshooting

### 6.1 P1 Issues

- **Access Point Not Working**
  - Check hostapd and dnsmasq status:
    ```bash
    sudo systemctl status hostapd
    sudo systemctl status dnsmasq
    ```
  - Reconfigure the access point:
    ```bash
    sudo python3 p1_software_Zero/ap_setup/P1_ap_setup_solo.py --configure
    ```

- **Data Collection Not Working**
  - Check the data collection service:
    ```bash
    sudo python3 p1_software_Zero/data_collection/P1_data_collector_solo.py --status
    ```
  - Check the logs:
    ```bash
    tail -n 100 /var/log/data_collector_solo.log
    ```

- **Web Interface Not Working**
  - Check the web interface service:
    ```bash
    sudo python3 p1_software_Zero/web_interface/P1_app_solo.py --status
    ```
  - Check the logs:
    ```bash
    tail -n 100 /var/log/web_interface_solo.log
    ```

### 6.2 P4, P5, P6 Issues

- **WiFi Connection Issues**
  - Check if the Pico 2W is connecting to the correct WiFi network.
  - Verify the WiFi credentials in the `main.py` file.
  - Check the LED status:
    - Blinking once: Successful data transmission
    - Blinking twice: Data transmission failure
    - Blinking three times: Error

- **Sensor Issues**
  - Check the sensor connections.
  - Verify that the I2C address for the BME680 sensor is correct (0x76 or 0x77).
  - Check the UART pins for the MH-Z19B sensor.

For more detailed troubleshooting, refer to the Troubleshooting Guide.
# Raspberry Pi 5 and Pico 2W Standalone Environmental Data Measurement System
# Installation Guide (BME680 Only Mode)
## Version 2.0

## Overview

This document provides instructions for installing and setting up the Raspberry Pi 5 and Pico 2W Standalone Environmental Data Measurement System in BME680 Only Mode (Version 2.0). In this version, the system works exclusively with BME680 sensors, with CO2 sensor (MH-Z19C) functionality disabled.

## Hardware Requirements

### Central Hub (P1)
- Raspberry Pi 5 (any model)
- MicroSD card (16GB or larger recommended)
- Power supply for Raspberry Pi 5
- Optional: USB WiFi dongle (for internet connectivity)

### Sensor Nodes (P2-P6)
- Raspberry Pi Pico 2W (with WiFi capability)
- BME680 environmental sensor
- Micro USB cable for power
- Jumper wires for connecting sensors

## Hardware Setup

### BME680 Sensor Connection to Pico 2W

Connect the BME680 sensor to the Raspberry Pi Pico 2W as follows:

| BME680 Pin | Pico 2W Pin |
|------------|-------------|
| VCC        | 3.3V (Pin 36) |
| GND        | GND (Pin 38) |
| SCL        | GP1 (Pin 2) |
| SDA        | GP0 (Pin 1) |

![BME680 Connection Diagram](../images/bme680_connection.png)

**Note**: The image is for reference only. If the actual image is not available, please refer to the pin connection table above.

## Software Installation

### P1 (Raspberry Pi 5) Setup

1. **Prepare the MicroSD Card**:
   - Download the latest Raspberry Pi OS (Lite or Desktop) from the [Raspberry Pi website](https://www.raspberrypi.org/software/operating-systems/)
   - Use Raspberry Pi Imager or similar tool to write the OS image to the MicroSD card
   - Insert the MicroSD card into the Raspberry Pi 5

2. **Initial Configuration**:
   - Connect the Raspberry Pi 5 to a monitor, keyboard, and power supply
   - Boot the Raspberry Pi and complete the initial setup (set username, password, locale, etc.)
   - Connect to the internet (via Ethernet or WiFi) for the initial setup

3. **Update the System**:
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```

4. **Install Required Packages**:
   ```bash
   sudo apt install -y python3-pip python3-venv hostapd dnsmasq git
   ```

5. **Set Up Virtual Environment**:
   ```bash
   cd ~
   python3 -m venv envmonitor-venv
   source envmonitor-venv/bin/activate
   pip install flask flask-socketio pandas plotly
   ```

6. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/RaspPi5_APconnection.git
   cd RaspPi5_APconnection/Ver2.00zeroOne
   ```

   Or, if you're installing from a local copy:
   ```bash
   cd /path/to/RaspPi5_APconnection/Ver2.00zeroOne
   ```

7. **Configure Access Point**:
   ```bash
   cd p1_software_solo405/ap_setup
   sudo python3 P1_ap_setup_solo.py --configure
   ```

   This will set up the Raspberry Pi 5 as a WiFi access point with the following default settings:
   - SSID: RaspberryPi5_AP_Solo2
   - Password: raspberry
   - IP Address: 192.168.0.2

8. **Create Data Directories**:
   ```bash
   sudo mkdir -p /var/lib/raspap_solo/data
   sudo mkdir -p /var/lib/raspap_solo/data/RawData_P2
   sudo mkdir -p /var/lib/raspap_solo/data/RawData_P3
   sudo mkdir -p /var/lib/raspap_solo/data/RawData_P4
   sudo mkdir -p /var/lib/raspap_solo/data/RawData_P5
   sudo mkdir -p /var/lib/raspap_solo/data/RawData_P6
   sudo chown -R pi:pi /var/lib/raspap_solo
   ```

9. **Set Up Autostart (Optional)**:
   To automatically start the system on boot, add the following to `/etc/rc.local` before the `exit 0` line:
   ```bash
   cd /path/to/RaspPi5_APconnection/Ver2.00zeroOne
   sudo -u pi /home/pi/envmonitor-venv/bin/python3 start_p1_solo.py &
   ```

### P2-P6 (Raspberry Pi Pico 2W) Setup

1. **Install Thonny IDE** on your development computer:
   - Download and install Thonny from [thonny.org](https://thonny.org/)

2. **Prepare the Pico 2W**:
   - Connect the Pico 2W to your computer via USB
   - Open Thonny IDE
   - Go to Tools > Options > Interpreter
   - Select "MicroPython (Raspberry Pi Pico)" as the interpreter
   - Click "Install or update firmware"
   - Follow the instructions to install MicroPython on the Pico 2W

3. **Install Required Libraries**:
   - In Thonny, create a new file and paste the following code:
     ```python
     import network
     import urequests
     import time
     print("Libraries test successful")
     ```
   - Save the file as `test_libraries.py` on the Pico 2W
   - Run the file to verify that the required libraries are available

4. **Upload Sensor Node Software**:
   - In Thonny, go to File > Open
   - Navigate to the `P2_software_debug` directory (or P3, P4, etc. depending on which device you're setting up)
   - Upload all files and directories to the Pico 2W, maintaining the directory structure

5. **Configure the Device ID**:
   - Open the `main.py` file on the Pico 2W
   - Locate the `DEVICE_ID` variable (around line 70)
   - Set it to the appropriate device ID (P2, P3, P4, P5, or P6)
   - Save the file

6. **Configure WiFi Settings**:
   - In the same `main.py` file, verify that the WiFi settings match your P1 configuration:
     ```python
     WIFI_SSID = "RaspberryPi5_AP_Solo2"
     WIFI_PASSWORD = "raspberry"
     SERVER_IP = "192.168.0.2"
     SERVER_PORT = 5000
     ```
   - Save the file

7. **Test the Setup**:
   - With the Pico 2W still connected to your computer, run the `main.py` file in Thonny
   - Verify that the BME680 sensor is detected and initialized
   - Verify that the Pico 2W can connect to the P1's WiFi access point
   - Verify that data is being transmitted to P1

8. **Deploy the Sensor Node**:
   - Disconnect the Pico 2W from your computer
   - Connect it to a power source via Micro USB
   - The Pico 2W will automatically run the `main.py` file on startup

9. **Repeat for Other Sensor Nodes**:
   - Repeat steps 2-8 for each Pico 2W device (P2, P3, P4, P5, P6)

## System Verification

After setting up all components, verify that the system is working correctly:

1. **Check P1 Services**:
   ```bash
   cd /path/to/RaspPi5_APconnection/Ver2.00zeroOne
   python3 start_p1_solo.py --status
   ```

   This should show that all services (access point, data collection, web interface, connection monitor) are running.

2. **Check Data Collection**:
   ```bash
   ls -la /var/lib/raspap_solo/data/RawData_P2/
   ```

   You should see CSV files being created for each sensor node.

3. **Access the Web Interface**:
   - Connect a device (smartphone, tablet, laptop) to the P1's WiFi network
   - Open a web browser and navigate to http://192.168.0.2
   - Verify that the dashboard loads and displays data from the sensor nodes

## Troubleshooting

### P1 (Raspberry Pi 5) Issues

1. **Access Point Not Working**:
   - Check the hostapd and dnsmasq services:
     ```bash
     sudo systemctl status hostapd
     sudo systemctl status dnsmasq
     ```
   - If they're not running, try restarting them:
     ```bash
     sudo systemctl restart hostapd
     sudo systemctl restart dnsmasq
     ```

2. **Data Collection Not Working**:
   - Check if the data collection service is running:
     ```bash
     cd /path/to/RaspPi5_APconnection/Ver2.00zeroOne
     python3 start_p1_solo.py --status
     ```
   - If it's not running, start it manually:
     ```bash
     cd /path/to/RaspPi5_APconnection/Ver2.00zeroOne
     python3 start_p1_solo.py
     ```

3. **Web Interface Not Accessible**:
   - Check if the web interface service is running:
     ```bash
     cd /path/to/RaspPi5_APconnection/Ver2.00zeroOne
     python3 start_p1_solo.py --status
     ```
   - If it's not running, start it manually:
     ```bash
     cd /path/to/RaspPi5_APconnection/Ver2.00zeroOne
     python3 start_p1_solo.py
     ```

### P2-P6 (Raspberry Pi Pico 2W) Issues

1. **BME680 Sensor Not Detected**:
   - Check the physical connections between the Pico 2W and the BME680 sensor
   - Verify that the I2C address is correct (usually 0x76 or 0x77)
   - Try a different BME680 sensor if available

2. **WiFi Connection Issues**:
   - Verify that the Pico 2W is within range of the P1's WiFi access point
   - Check that the WiFi credentials (SSID, password) are correct
   - Try resetting the Pico 2W by disconnecting and reconnecting the power

3. **Data Transmission Issues**:
   - Check that the SERVER_IP and SERVER_PORT settings are correct
   - Verify that the P1's data collection service is running
   - Check for any error messages in the Pico 2W's output (connect it to Thonny for debugging)

## Additional Resources

- [Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/)
- [MicroPython Documentation](https://docs.micropython.org/)
- [BME680 Datasheet](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme680-ds001.pdf)

## Support

For technical support or questions about the system, please contact the system administrator or refer to the documentation provided with the system.

---

*This document is part of the Raspberry Pi 5 and Pico 2W Standalone Environmental Data Measurement System documentation set, Version 2.0.*
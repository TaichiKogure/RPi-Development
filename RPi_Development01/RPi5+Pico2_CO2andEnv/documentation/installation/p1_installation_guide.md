# Raspberry Pi 5 (P1) Installation Guide
Version: 2.0.0

This guide provides step-by-step instructions for setting up the Raspberry Pi 5 (P1) as the central hub for the environmental data measurement system.

## Table of Contents
1. [Hardware Requirements](#hardware-requirements)
2. [Operating System Installation](#operating-system-installation)
3. [Network Configuration](#network-configuration)
4. [Software Installation](#software-installation)
5. [Access Point Setup](#access-point-setup)
6. [Data Collection Service Setup](#data-collection-service-setup)
7. [Web Interface Setup](#web-interface-setup)
8. [Connection Monitor Setup](#connection-monitor-setup)
9. [System Testing](#system-testing)
10. [Troubleshooting](#troubleshooting)

## Hardware Requirements
- Raspberry Pi 5 (4GB or 8GB RAM recommended)
- MicroSD card (32GB or larger recommended)
- Power supply (5V, 5A USB-C)
- USB WiFi dongle (optional, for internet connectivity)
- Ethernet cable (optional, for initial setup)
- Case with cooling (recommended)
- Monitor, keyboard, and mouse (for initial setup)

## Operating System Installation
1. Download the latest Raspberry Pi OS (64-bit) from the [official website](https://www.raspberrypi.org/software/operating-systems/).
2. Use the Raspberry Pi Imager to write the OS to your MicroSD card:
   - Download and install [Raspberry Pi Imager](https://www.raspberrypi.org/software/)
   - Insert your MicroSD card into your computer
   - Open Raspberry Pi Imager
   - Click "CHOOSE OS" and select "Raspberry Pi OS (64-bit)"
   - Click "CHOOSE STORAGE" and select your MicroSD card
   - Click the gear icon (⚙️) to access advanced options
   - Enable SSH, set a username and password, configure WiFi (if needed), and set your locale settings
   - Click "WRITE" and wait for the process to complete

3. Insert the MicroSD card into your Raspberry Pi 5 and power it on.
4. Complete the initial setup process, including:
   - Accepting the license agreement
   - Setting up your user account (if not done in the imager)
   - Connecting to WiFi (if not done in the imager)
   - Updating the system

## Network Configuration
1. Open a terminal window and update your system:
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```

2. Install network utilities:
   ```bash
   sudo apt install -y net-tools wireless-tools bridge-utils
   ```

3. If you're using a USB WiFi dongle for internet connectivity, connect it now.

## Software Installation
1. Install required dependencies:
   ```bash
   sudo apt install -y python3-venv python3-dev git
   ```

2. Set up virtual environment:
   ```bash
   cd ~
   python3 -m venv envmonitor-venv
   source envmonitor-venv/bin/activate
   ```

3. Install required Python packages in the virtual environment:
   ```bash
   pip install flask flask-socketio pandas plotly
   ```

4. Clone the project repository:
   ```bash
   git clone https://github.com/yourusername/RaspPi5_APconnection.git
   cd RPi_Development01
   ```

   > Note: If you don't have the repository on GitHub, you can copy the files manually to the Raspberry Pi.

5. Remember to activate the virtual environment whenever you need to run Python scripts:
   ```bash
   source ~/envmonitor-venv/bin/activate
   ```

## Access Point Setup
1. Navigate to the access point setup directory:
   ```bash
   cd ~/RPi_Development01/p1_software/ap_setup
   ```

2. Make the setup script executable:
   ```bash
   chmod +x ap_setup.py
   ```

3. Run the setup script with sudo privileges:
   ```bash
   sudo python3 ap_setup.py --configure
   ```

4. Follow the on-screen instructions to complete the setup.

5. After the setup completes, reboot your Raspberry Pi:
   ```bash
   sudo reboot
   ```

6. After rebooting, verify that the access point is working:
   ```bash
   sudo python3 ap_setup.py --status
   ```

7. You should see a WiFi network named "RaspberryPi5_AP" (default name) that you can connect to from other devices using the password "raspberry" (default password).

## Data Collection Service Setup
1. Navigate to the data collection directory:
   ```bash
   cd ~/RPi_Development01/p1_software/data_collection
   ```

2. Create a data directory:
   ```bash
   sudo mkdir -p /var/lib(FromThonny)/raspap/data
   sudo chown -R $USER:$USER /var/lib(FromThonny)/raspap/data
   ```

3. Create a systemd service file for the data collector:
   ```bash
   sudo nano /etc/systemd/system/data_collector.service
   ```

4. Add the following content to the file:
   ```
   [Unit]
   Description=Environmental Data Collector
   After=network.target

   [Service]
   ExecStart=/home/pi/envmonitor-venv/bin/python3 /home/pi/RaspPi5_APconnection/p1_software/data_collection/data_collector.py
   WorkingDirectory=/home/pi/RaspPi5_APconnection/p1_software/data_collection
   StandardOutput=inherit
   StandardError=inherit
   Restart=always
   User=pi

   [Install]
   WantedBy=multi-user.target
   ```

   > Note: Replace "pi" with your username if different. The service uses the Python interpreter from the virtual environment.

5. Enable and start the service:
   ```bash
   sudo systemctl enable data_collector.service
   sudo systemctl start data_collector.service
   ```

6. Check the service status:
   ```bash
   sudo systemctl status data_collector.service
   ```

## Web Interface Setup
1. Navigate to the web interface directory:
   ```bash
   cd ~/RPi_Development01/p1_software/web_interface
   ```

2. Create a systemd service file for the web interface:
   ```bash
   sudo nano /etc/systemd/system/web_interface.service
   ```

3. Add the following content to the file:
   ```
   [Unit]
   Description=Environmental Data Web Interface
   After=network.target data_collector.service

   [Service]
   ExecStart=/home/pi/envmonitor-venv/bin/python3 /home/pi/RaspPi5_APconnection/p1_software/web_interface/app.py
   WorkingDirectory=/home/pi/RaspPi5_APconnection/p1_software/web_interface
   StandardOutput=inherit
   StandardError=inherit
   Restart=always
   User=pi

   [Install]
   WantedBy=multi-user.target
   ```

   > Note: Replace "pi" with your username if different. The service uses the Python interpreter from the virtual environment.

4. Enable and start the service:
   ```bash
   sudo systemctl enable web_interface.service
   sudo systemctl start web_interface.service
   ```

5. Check the service status:
   ```bash
   sudo systemctl status web_interface.service
   ```

## Connection Monitor Setup
1. Navigate to the connection monitor directory:
   ```bash
   cd ~/RPi_Development01/p1_software/connection_monitor
   ```

2. Create a systemd service file for the connection monitor:
   ```bash
   sudo nano /etc/systemd/system/wifi_monitor.service
   ```

3. Add the following content to the file:
   ```
   [Unit]
   Description=WiFi Connection Monitor
   After=network.target

   [Service]
   ExecStart=/home/pi/envmonitor-venv/bin/python3 /home/pi/RaspPi5_APconnection/p1_software/connection_monitor/wifi_monitor.py
   WorkingDirectory=/home/pi/RaspPi5_APconnection/p1_software/connection_monitor
   StandardOutput=inherit
   StandardError=inherit
   Restart=always
   User=pi

   [Install]
   WantedBy=multi-user.target
   ```

   > Note: Replace "pi" with your username if different. The service uses the Python interpreter from the virtual environment.

4. Enable and start the service:
   ```bash
   sudo systemctl enable wifi_monitor.service
   sudo systemctl start wifi_monitor.service
   ```

5. Check the service status:
   ```bash
   sudo systemctl status wifi_monitor.service
   ```

## System Testing
1. Connect to the Raspberry Pi 5's WiFi network from another device (e.g., smartphone or laptop).
2. Open a web browser and navigate to `http://192.168.0.1` (or the IP address you configured).
3. You should see the environmental data dashboard.
4. If you have set up P2 and P3 devices, they should connect to the Raspberry Pi 5's WiFi network and start sending data.
5. The dashboard should display the data from P2 and P3 devices.

## Troubleshooting
### Access Point Issues
- If the access point is not working, check the status:
  ```bash
  sudo python3 ~/RPi_Development01/p1_software/ap_setup/ap_setup.py --status
  ```
- Try reconfiguring the access point:
  ```bash
  sudo python3 ~/RPi_Development01/p1_software/ap_setup/ap_setup.py --configure
  ```
- Check the system logs for errors:
  ```bash
  sudo journalctl -u hostapd
  sudo journalctl -u dnsmasq
  ```

### Data Collection Issues
- Check the data collector service status:
  ```bash
  sudo systemctl status data_collector.service
  ```
- Check the data collector logs:
  ```bash
  sudo journalctl -u data_collector.service
  ```
- Verify that the data directory exists and has the correct permissions:
  ```bash
  ls -la /var/lib(FromThonny)/raspap/data
  ```

### Web Interface Issues
- Check the web interface service status:
  ```bash
  sudo systemctl status web_interface.service
  ```
- Check the web interface logs:
  ```bash
  sudo journalctl -u web_interface.service
  ```
- Verify that you can access the web interface from the Raspberry Pi itself:
  ```bash
  curl http://localhost:80
  ```

### Connection Monitor Issues
- Check the connection monitor service status:
  ```bash
  sudo systemctl status wifi_monitor.service
  ```
- Check the connection monitor logs:
  ```bash
  sudo journalctl -u wifi_monitor.service
  ```

### General Issues
- Reboot the Raspberry Pi:
  ```bash
  sudo reboot
  ```
- Check system resources:
  ```bash
  htop
  ```
- Check disk space:
  ```bash
  df -h
  ```
- Check network interfaces:
  ```bash
  ifconfig
  ```
- Check WiFi status:
  ```bash
  iwconfig
  ```

For more detailed troubleshooting, refer to the [Troubleshooting Guide](../troubleshooting/troubleshooting_guide.md).

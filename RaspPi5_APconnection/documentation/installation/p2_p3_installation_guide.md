# Raspberry Pi Pico 2W (P2/P3) Installation Guide
Version: 2.0.0

This guide provides step-by-step instructions for setting up the Raspberry Pi Pico 2W devices (P2 and P3) as sensor nodes for the environmental data measurement system.

## Table of Contents
1. [Hardware Requirements](#hardware-requirements)
2. [MicroPython Installation](#micropython-installation)
3. [Sensor Connection](#sensor-connection)
4. [Software Installation](#software-installation)
5. [Configuration](#configuration)
6. [Testing](#testing)
7. [Deployment](#deployment)
8. [Troubleshooting](#troubleshooting)

## Hardware Requirements
- Raspberry Pi Pico 2W (2 units, one for P2 and one for P3)
- MicroUSB cable for programming
- BME680 environmental sensor (2 units)
- MH-Z19B CO2 sensor (2 units)
- Jumper wires
- Breadboard (optional, for prototyping)
- 3.3V power supply (if not powered via USB)
- Case (optional, for protection)

## MicroPython Installation
1. Download the latest MicroPython firmware for Raspberry Pi Pico W from the [official website](https://micropython.org/download/rp2-pico-w/).

2. Connect your Raspberry Pi Pico 2W to your computer while holding the BOOTSEL button.
   - The Pico should appear as a USB mass storage device named "RPI-RP2".

3. Drag and drop the downloaded MicroPython UF2 file onto the RPI-RP2 drive.
   - The Pico will automatically reboot and disconnect from the computer.
   - It will reconnect as a serial device.

4. Install Thonny IDE (if not already installed):
   - Download and install [Thonny IDE](https://thonny.org/) on your computer.
   - Thonny is available for Windows, macOS, and Linux.

5. Configure Thonny for Raspberry Pi Pico:
   - Open Thonny IDE.
   - Go to "Tools" > "Options" > "Interpreter".
   - Select "MicroPython (Raspberry Pi Pico)" from the dropdown menu.
   - Select the appropriate COM port for your Pico.
   - Click "OK".

6. Verify MicroPython installation:
   - In the Thonny shell (bottom panel), you should see the MicroPython welcome message.
   - Try running a simple command like `print("Hello, World!")` to verify that MicroPython is working.

## Sensor Connection
### BME680 Sensor Connection (I2C)
Connect the BME680 sensor to the Raspberry Pi Pico 2W using the following pin connections:

| BME680 Pin | Pico 2W Pin |
|------------|-------------|
| VCC        | 3.3V (Pin 36) |
| GND        | GND (Pin 38) |
| SCL        | GP1 (Pin 2) |
| SDA        | GP0 (Pin 1) |

### MH-Z19B CO2 Sensor Connection (UART)
Connect the MH-Z19B sensor to the Raspberry Pi Pico 2W using the following pin connections:

| MH-Z19B Pin | Pico 2W Pin |
|-------------|-------------|
| VCC (Red)   | VBUS (5V, Pin 40) |
| GND (Black) | GND (Pin 38) |
| TX (Green)  | GP9 (Pin 12) |
| RX (Blue)   | GP8 (Pin 11) |

> Note: The MH-Z19B requires 5V power, which can be supplied from the VBUS pin on the Pico when it's powered via USB. If you're using an external power supply, make sure it provides 5V for the MH-Z19B.

## Software Installation
1. Create the project directory structure on your Pico 2W:
   - In Thonny, go to "View" > "Files" to open the file browser.
   - Create the following directories:
     - `/sensor_drivers`
     - `/data_transmission`
     - `/error_handling`

2. Download the project files from the repository or copy them from your computer:
   - BME680 driver: `bme680_driver.py`
   - MH-Z19B driver: `mhz19b_driver.py`
   - WiFi client: `wifi_client.py`
   - Watchdog: `watchdog.py`
   - Main script: `main.py`

3. Upload the files to the appropriate directories on your Pico 2W:
   - `/sensor_drivers/bme680_driver.py`
   - `/sensor_drivers/mhz19b_driver.py`
   - `/data_transmission/wifi_client.py`
   - `/error_handling/watchdog.py`
   - `/main.py` (in the root directory)

## Configuration
1. Open the `main.py` file in Thonny.

2. Modify the configuration parameters for your specific setup:
   - Set the device ID to "P2" for the first Pico and "P3" for the second Pico.
   - Configure the WiFi settings to match your Raspberry Pi 5's access point.
   - Adjust the sensor pins if you used different connections.

3. Here's an example configuration for the P2 device:
   ```python
   # Device configuration
   DEVICE_ID = "P2"  # Change to "P3" for the second Pico

   # WiFi configuration
   WIFI_SSID = "RaspberryPi5_AP"
   WIFI_PASSWORD = "raspberry"
   SERVER_IP = "192.168.0.1"
   SERVER_PORT = 5000

   # Sensor pins
   BME680_SCL_PIN = 1
   BME680_SDA_PIN = 0
   MHZ19B_UART_ID = 1
   MHZ19B_TX_PIN = 8
   MHZ19B_RX_PIN = 9

   # Transmission interval (seconds)
   TRANSMISSION_INTERVAL = 30
   ```

4. Save the modified `main.py` file to your Pico 2W.

5. Repeat the process for the second Pico 2W, changing the device ID to "P3".

## Testing
1. With the Pico 2W still connected to your computer, run the `main.py` script in Thonny:
   - Click the "Run" button or press F5.
   - Watch the output in the shell to verify that:
     - The sensors are being detected and read correctly.
     - The Pico can connect to the Raspberry Pi 5's WiFi network.
     - Data is being transmitted successfully.

2. If everything is working correctly, you should see output similar to:
   ```
   Initializing sensors...
   BME680 sensor initialized
   MH-Z19B sensor initialized
   Connecting to WiFi network: RaspberryPi5_AP
   Connected to RaspberryPi5_AP
   IP address: 192.168.900.101
   Starting data transmission...
   Data sent successfully: {'temperature': 25.3, 'humidity': 45.2, 'pressure': 1013.25, 'gas_resistance': 12345, 'co2_level': 450, 'device_id': 'P2'}
   ```

3. Check the Raspberry Pi 5's data collection logs to verify that it's receiving the data:
   ```bash
   sudo journalctl -u data_collector.service -f
   ```

## Deployment
1. Once testing is complete, disconnect the Pico 2W from your computer.

2. For standalone operation, you can power the Pico 2W using:
   - A USB power adapter
   - A battery pack with USB output
   - An external 3.3V power supply connected to the VSYS and GND pins

3. When the Pico 2W powers on, it will automatically run the `main.py` script and start collecting and transmitting data.

4. Place the Pico 2W in its final location, ensuring that:
   - It's within range of the Raspberry Pi 5's WiFi network.
   - The sensors are positioned appropriately for accurate readings.
   - The power supply is stable and reliable.

## Troubleshooting
### Sensor Connection Issues
- **BME680 not detected:**
  - Check the I2C connections (SDA and SCL).
  - Verify that the sensor is receiving power (3.3V and GND).
  - Try a different BME680 sensor if available.

- **MH-Z19B not responding:**
  - Check the UART connections (TX and RX).
  - Ensure the sensor is receiving 5V power.
  - The MH-Z19B needs a warm-up period of about 3 minutes after power-on.

### WiFi Connection Issues
- **Cannot connect to WiFi:**
  - Verify that the Raspberry Pi 5 access point is running.
  - Check the SSID and password in the configuration.
  - Ensure the Pico 2W is within range of the access point.
  - Try resetting both the Pico 2W and the Raspberry Pi 5.

- **Connection drops frequently:**
  - Move the Pico 2W closer to the Raspberry Pi 5.
  - Check for sources of interference.
  - Verify that the power supply is stable.

### Data Transmission Issues
- **Data not being received by the server:**
  - Check that the server IP and port are correct.
  - Verify that the data collector service is running on the Raspberry Pi 5.
  - Check the format of the data being sent.

### General Issues
- **Pico 2W not booting:**
  - Try a different USB cable or power supply.
  - Hold the BOOTSEL button while connecting power to enter bootloader mode, then reinstall MicroPython.

- **Script errors:**
  - Connect the Pico 2W to Thonny and check the error messages.
  - Verify that all required libraries are installed.
  - Check for syntax errors in the code.

- **Watchdog resets:**
  - If the Pico 2W is resetting frequently, check the error log stored on the device.
  - Connect to Thonny and run `import os; print(os.listdir())` to see if an error log file exists.
  - Open and read the error log file to identify the cause of the resets.

For more detailed troubleshooting, refer to the [Troubleshooting Guide](../troubleshooting/troubleshooting_guide.md).

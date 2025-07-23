# -*- coding: utf-8 -*-
"""
WiFi Client for Raspberry Pi Pico 2W - Solo Version 3.2
Version: 3.2.0-solo

This module provides functions to connect the Raspberry Pi Pico 2W to a WiFi network
and transmit BME680 sensor data to the Raspberry Pi 5 server.

Features:
- WiFi connection management
- Automatic reconnection on connection loss
- JSON data formatting for transmission
- Configurable server address and port
- Error handling and diagnostics
- Improved retry mechanism (up to 5 retries)

Requirements:
- MicroPython for Raspberry Pi Pico W
- network and socket libraries
- ujson library

Usage:
    import wifi_client_solo
    client = wifi_client_solo.WiFiClient(ssid="RaspberryPi5_AP_Solo", password="raspberry")
    client.connect()
    client.send_data({"temperature": 25.5, "humidity": 60.2})
"""

import time
import network
import socket
import ujson
import machine
from machine import Pin

# Status LED
LED_PIN = 25  # Onboard LED on Pico W

class WiFiClient:
    """Class to manage WiFi connection and data transmission."""

    def __init__(self, ssid="RaspberryPi5_AP_Solo", password="raspberry", 
                 server_ip="192.168.0.1", server_port=5000, device_id="P2"):
        """Initialize the WiFi client with the given configuration.

        Args:
            ssid (str): WiFi network SSID
            password (str): WiFi network password
            server_ip (str): IP address of the data collection server
            server_port (int): Port of the data collection server
            device_id (str): Device identifier (P2)
        """
        self.ssid = ssid
        self.password = password
        self.server_ip = server_ip
        self.server_port = server_port
        self.device_id = device_id
        self.wlan = network.WLAN(network.STA_IF)
        self.connected = False
        self.led = Pin(LED_PIN, Pin.OUT)

        # Initialize LED
        self.led.off()

    def connect(self, max_retries=10, retry_delay=5):
        """Connect to the WiFi network.

        Args:
            max_retries (int): Maximum number of connection attempts
            retry_delay (int): Delay between retries in seconds

        Returns:
            bool: True if connection successful, False otherwise
        """
        print(f"Connecting to WiFi network: {self.ssid}")

        # Activate WiFi interface
        self.wlan.active(True)

        # Try to connect
        retry_count = 0
        while not self.wlan.isconnected() and retry_count < max_retries:
            try:
                # Blink LED to indicate connection attempt
                self._blink_led(2, 0.2)

                # Connect to WiFi
                self.wlan.connect(self.ssid, self.password)

                # Wait for connection with timeout
                timeout = 0
                while not self.wlan.isconnected() and timeout < 10:
                    self._blink_led(1, 0.1)
                    time.sleep(1)
                    timeout += 1

                if self.wlan.isconnected():
                    break

                retry_count += 1
                print(f"Connection attempt {retry_count} failed. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)

            except Exception as e:
                print(f"Connection error: {e}")
                retry_count += 1
                time.sleep(retry_delay)

        # Check if connected
        if self.wlan.isconnected():
            self.connected = True
            network_info = self.wlan.ifconfig()
            print(f"Connected to {self.ssid}")
            print(f"IP address: {network_info[0]}")

            # Turn on LED to indicate successful connection
            self.led.on()
            return True
        else:
            print(f"Failed to connect to {self.ssid} after {max_retries} attempts")

            # Rapid blink to indicate connection failure
            self._blink_led(10, 0.1)
            return False

    def disconnect(self):
        """Disconnect from the WiFi network."""
        if self.wlan.isconnected():
            self.wlan.disconnect()
            self.connected = False
            print(f"Disconnected from {self.ssid}")

            # Turn off LED to indicate disconnection
            self.led.off()

    def is_connected(self):
        """Check if connected to the WiFi network.

        Returns:
            bool: True if connected, False otherwise
        """
        return self.wlan.isconnected()

    def reconnect_if_needed(self):
        """Reconnect to the WiFi network if the connection is lost.

        Returns:
            bool: True if connected (either already or after reconnection), False otherwise
        """
        if not self.wlan.isconnected():
            print("WiFi connection lost. Reconnecting...")
            self.connected = False
            self.led.off()
            return self.connect()
        return True

    def send_data(self, data, max_retries=5):
        """Send data to the server with retry.

        Args:
            data (dict): Data to send (will be converted to JSON)
            max_retries (int): Number of retry attempts (default: 5)

        Returns:
            bool: True if data sent successfully, False otherwise
        """
        # Check connection and reconnect if needed
        if not self.reconnect_if_needed():
            return False

        data["device_id"] = self.device_id
        json_data = ujson.dumps(data)
        
        # Initialize sock to None
        sock = None
        
        # Retry loop
        for attempt in range(max_retries):
            try:
                print(f"Sending data attempt {attempt + 1}/{max_retries}...")
                
                # Create new socket for each attempt
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                
                # Connect and send data
                sock.connect((self.server_ip, self.server_port))
                sock.send(json_data.encode())
                
                # Wait for response
                response = sock.recv(1024)
                
                # Close socket
                sock.close()
                sock = None
                
                # Process response
                if response:
                    try:
                        response_data = ujson.loads(response.decode())
                        if response_data.get("status") == "success":
                            print(f"Data sent successfully on attempt {attempt + 1}")
                            self._blink_led(1, 0.1)
                            return True
                        else:
                            print(f"Server error: {response_data.get('message', 'Unknown error')}")
                    except Exception as e:
                        print(f"Invalid response from server: {response}, Error: {e}")
                else:
                    print("No response from server")
            
            except Exception as e:
                print(f"[Attempt {attempt + 1}/{max_retries}] Error sending data: {e}")
            
            finally:
                # Ensure socket is closed
                if sock:
                    try:
                        sock.close()
                    except:
                        pass
            
            # If this wasn't the last attempt, wait before retrying
            if attempt < max_retries - 1:
                retry_delay = 2 * (attempt + 1)  # Progressive backoff
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
        
        print(f"All {max_retries} retry attempts failed.")
        return False

    def _blink_led(self, count, duration):
        """Blink the LED.

        Args:
            count (int): Number of blinks
            duration (float): Duration of each blink in seconds
        """
        for _ in range(count):
            self.led.on()
            time.sleep(duration)
            self.led.off()
            time.sleep(duration)

class DataTransmitter:
    """Class to manage sensor data collection and transmission."""

    def __init__(self, wifi_client, transmission_interval=30):
        """Initialize the data transmitter.

        Args:
            wifi_client (WiFiClient): WiFi client for data transmission
            transmission_interval (int): Interval between transmissions in seconds
        """
        self.wifi_client = wifi_client
        self.transmission_interval = transmission_interval
        self.last_transmission_time = 0
        self.sensors = {}

    def add_sensor(self, name, sensor):
        """Add a sensor to the data transmitter.

        Args:
            name (str): Sensor name
            sensor: Sensor object with get_readings() method
        """
        self.sensors[name] = sensor

    def collect_and_send_data(self):
        """Collect data from all sensors and send it to the server.

        Returns:
            bool: True if data sent successfully, False otherwise
        """
        # Check if it's time to transmit
        current_time = time.time()
        if current_time - self.last_transmission_time < self.transmission_interval:
            return True

        # Collect data from all sensors
        data = {}

        for name, sensor in self.sensors.items():
            try:
                if name == "bme680":
                    # For the new bme680 module, we need to access properties directly
                    data.update({
                        "temperature": sensor.temperature,
                        "humidity": sensor.humidity,
                        "pressure": sensor.pressure,
                        "gas_resistance": sensor.gas
                    })
            except Exception as e:
                print(f"Error reading {name} sensor: {e}")

        # Send data if we have any
        if data:
            success = self.wifi_client.send_data(data)
            if success:
                self.last_transmission_time = current_time
                print(f"Data sent successfully: {data}")
            else:
                print("Failed to send data after all retry attempts")
            return success
        else:
            print("No data to send")
            return False

    def run(self, run_once=False):
        """Run the data transmitter.

        Args:
            run_once (bool): If True, run once and return. If False, run continuously.

        Returns:
            bool: True if successful, False otherwise
        """
        # Connect to WiFi
        if not self.wifi_client.is_connected():
            if not self.wifi_client.connect():
                return False

        if run_once:
            # Collect and send data once
            return self.collect_and_send_data()
        else:
            # Run continuously
            try:
                while True:
                    self.collect_and_send_data()
                    time.sleep(1)  # Small delay to prevent CPU overload
            except KeyboardInterrupt:
                print("Data transmission stopped by user")
                return True
            except Exception as e:
                print(f"Error in data transmission: {e}")
                return False

# Example usage
if __name__ == "__main__":
    try:
        # Import sensor drivers
        import sys
        sys.path.append('/sensor_drivers')
        from sensor_drivers.bme680 import BME680_I2C
        from machine import I2C, Pin

        # Initialize I2C
        i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=100000)
        
        # Initialize BME680 sensor
        bme = BME680_I2C(i2c, address=0x77)

        # Initialize WiFi client
        client = WiFiClient(device_id="P2")

        # Initialize data transmitter
        transmitter = DataTransmitter(client)
        transmitter.add_sensor("bme680", bme)

        # Run data transmitter
        print("Starting data transmission...")
        transmitter.run()

    except Exception as e:
        print(f"Error: {e}")

        # Reset the device after a delay if there's an error
        print("Resetting device in 10 seconds...")
        time.sleep(10)
        machine.reset()
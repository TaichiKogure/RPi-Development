#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi Pico 2W WiFi Client for Environmental Monitoring - Solo Version 4.44
Version: 4.44.0-solo

This module provides WiFi connectivity and data transmission functionality for the
Raspberry Pi Pico 2W (P2) environmental monitoring system.

Features:
- WiFi connectivity to P1 server
- Data transmission with retry logic
- Error handling
- LED status indicators

Usage:
    This file should be imported by main.py on the Pico 2W.
"""

import time
import network
import socket
import ujson
import machine
import gc
from machine import Pin

# Constants
LED_PIN = "LED"  # Onboard LED

# Debug levels
DEBUG_NONE = 0    # No debug output
DEBUG_BASIC = 1   # Basic connection information
DEBUG_DETAILED = 2  # Detailed connection steps
DEBUG_VERBOSE = 3  # Very verbose output including all network parameters

class WiFiClient:
    """Class to manage WiFi connection and data transmission."""

    def __init__(self, ssid="RaspberryPi5_AP_Solo", password="raspberry", 
                 server_ip="192.168.0.1", server_port=5000, device_id="P2",
                 debug_level=DEBUG_BASIC):
        """Initialize the WiFi client with the given configuration.

        Args:
            ssid (str): WiFi network SSID
            password (str): WiFi network password
            server_ip (str): IP address of the data collection server
            server_port (int): Port of the data collection server
            device_id (str): Device identifier (P2)
            debug_level (int): Level of debug output (0-3)
        """
        self.ssid = ssid
        self.password = password
        self.server_ip = server_ip
        self.server_port = server_port
        self.device_id = device_id
        self.wlan = network.WLAN(network.STA_IF)
        self.connected = False
        self.led = Pin(LED_PIN, Pin.OUT)
        self.connection_attempts = 0
        self.last_connection_time = 0
        self.debug_level = debug_level

        # Initialize LED
        self.led.off()

        # Print configuration
        self._debug_print(f"WiFi Client initialized for {device_id}", DEBUG_BASIC)
        self._debug_print(f"Server: {server_ip}:{server_port}", DEBUG_BASIC)

    def _debug_print(self, message, level=DEBUG_BASIC):
        """Print debug message if debug level is high enough.

        Args:
            message (str): Message to print
            level (int): Minimum debug level required to print this message
        """
        if self.debug_level >= level:
            print(f"[WiFi] {message}")

        # Allow background processing after printing
        machine.idle()

    def set_debug_level(self, level):
        """Set the debug level.

        Args:
            level (int): Debug level (0-3)
        """
        self.debug_level = level
        self._debug_print(f"Debug level set to {level}", DEBUG_BASIC)

    def connect(self, max_retries=5, retry_delay=5, connection_timeout=45):
        """Connect to the WiFi network with configurable timeout.

        Args:
            max_retries (int): Maximum number of connection attempts
            retry_delay (int): Delay between retries in seconds
            connection_timeout (int): Timeout for each connection attempt in seconds

        Returns:
            bool: True if connection successful, False otherwise
        """
        # Print connection parameters
        self._debug_print(f"Connecting to WiFi network: {self.ssid}", DEBUG_BASIC)
        self._debug_print(f"Connection timeout: {connection_timeout} seconds", DEBUG_BASIC)

        # Record connection attempt
        self.connection_attempts += 1
        self.last_connection_time = time.time()

        # Activate WiFi interface if not already active
        if not self.wlan.active():
            self._debug_print("Activating WiFi interface...", DEBUG_BASIC)
            try:
                self.wlan.active(True)
                time.sleep(1)  # Give it a moment to initialize
                self._debug_print("WiFi interface activated", DEBUG_BASIC)
            except Exception as e:
                self._debug_print(f"Exception during wlan.active(): {e}", DEBUG_BASIC)
                return False
        else:
            self._debug_print("WiFi interface already active", DEBUG_DETAILED)

        # Check if already connected
        if self.wlan.isconnected():
            self._debug_print("Already connected to WiFi", DEBUG_BASIC)
            self.connected = True
            self._print_connection_info()
            return True

        # Try to connect
        retry_count = 0
        while not self.wlan.isconnected() and retry_count < max_retries:
            try:
                # Blink LED to indicate connection attempt
                self._blink_led(2, 0.2)

                # Disconnect first if we're in a weird state
                if retry_count > 0:
                    try:
                        self._debug_print("Disconnecting from any existing connections...", DEBUG_DETAILED)
                        self.wlan.disconnect()
                        time.sleep(1)
                        self._debug_print("Disconnected", DEBUG_DETAILED)
                    except Exception as e:
                        self._debug_print(f"Error during disconnect: {e}", DEBUG_DETAILED)

                # Force garbage collection before connection attempt
                gc.collect()

                # Connect to WiFi - WRAPPED IN TRY/EXCEPT
                self._debug_print(f"Sending connection request to {self.ssid}...", DEBUG_BASIC)
                try:
                    # This is the critical line that needs to be wrapped in try/except
                    self.wlan.connect(self.ssid, self.password)
                    # Allow background processing immediately after connect call
                    machine.idle()
                except Exception as e:
                    self._debug_print(f"Exception during wlan.connect(): {e}", DEBUG_BASIC)
                    retry_count += 1
                    time.sleep(retry_delay)
                    continue

                # Wait for connection with configurable timeout
                timeout = 0
                connection_start = time.time()

                self._debug_print(f"Waiting for connection (timeout: {connection_timeout}s)...", DEBUG_BASIC)

                while not self.wlan.isconnected() and timeout < connection_timeout:
                    # Blink LED to indicate waiting
                    self._blink_led(1, 0.1)

                    # Sleep in smaller increments to be more responsive
                    # Add machine.idle() to allow background processing
                    for _ in range(4):  # 4 x 0.25s = 1s
                        machine.idle()
                        time.sleep(0.25)

                    timeout += 1

                    # Print progress and status less frequently to reduce USB/REPL load
                    if timeout % 5 == 0:
                        self._debug_print(f"Waiting for connection... {timeout}/{connection_timeout} seconds", DEBUG_BASIC)

                # Check if connected
                if self.wlan.isconnected():
                    self._debug_print(f"Connected to {self.ssid} after {timeout} seconds", DEBUG_BASIC)
                    break

                # If we get here, connection timed out
                retry_count += 1
                self._debug_print(f"Connection attempt {retry_count} timed out after {timeout} seconds", DEBUG_BASIC)

                # Progressive backoff
                current_retry_delay = retry_delay * retry_count
                self._debug_print(f"Waiting {current_retry_delay} seconds before next attempt...", DEBUG_BASIC)
                time.sleep(current_retry_delay)

            except Exception as e:
                self._debug_print(f"Connection error: {e}", DEBUG_BASIC)
                retry_count += 1

                # Progressive backoff for exceptions too
                current_retry_delay = retry_delay * retry_count
                self._debug_print(f"Waiting {current_retry_delay} seconds before next attempt...", DEBUG_BASIC)
                time.sleep(current_retry_delay)

        # Check if connected
        if self.wlan.isconnected():
            self.connected = True
            self._print_connection_info()

            # Turn on LED to indicate successful connection
            self.led.on()

            return True
        else:
            self._debug_print(f"Failed to connect to {self.ssid} after {max_retries} attempts", DEBUG_BASIC)

            # Rapid blink to indicate connection failure
            self._blink_led(10, 0.1)

            return False

    def _status_to_string(self, status):
        """Convert WiFi status code to string.

        Args:
            status: The status code from wlan.status()

        Returns:
            str: Human-readable status message
        """
        status_messages = {
            network.STAT_IDLE: "Idle",
            network.STAT_CONNECTING: "Connecting",
            network.STAT_WRONG_PASSWORD: "Wrong password",
            network.STAT_NO_AP_FOUND: "AP not found",
            network.STAT_CONNECT_FAIL: "Connection failed",
            network.STAT_GOT_IP: "Connected"
        }

        return status_messages.get(status, f"Unknown status ({status})")

    def _print_connection_info(self):
        """Print information about the current connection."""
        try:
            network_info = self.wlan.ifconfig()
            self._debug_print(f"Connected to {self.ssid}", DEBUG_BASIC)
            self._debug_print(f"IP address: {network_info[0]}", DEBUG_BASIC)

            # Only print detailed info in verbose mode
            if self.debug_level >= DEBUG_VERBOSE:
                self._debug_print(f"Subnet mask: {network_info[1]}", DEBUG_VERBOSE)
                self._debug_print(f"Gateway: {network_info[2]}", DEBUG_VERBOSE)
                self._debug_print(f"DNS: {network_info[3]}", DEBUG_VERBOSE)

                # Get signal strength
                try:
                    rssi = self.wlan.status('rssi')
                    self._debug_print(f"Signal strength: {rssi} dBm", DEBUG_VERBOSE)
                except:
                    pass
        except Exception as e:
            self._debug_print(f"Error getting connection info: {e}", DEBUG_BASIC)

    def disconnect(self):
        """Disconnect from the WiFi network."""
        if self.wlan.isconnected():
            self._debug_print(f"Disconnecting from {self.ssid}...", DEBUG_BASIC)
            try:
                self.wlan.disconnect()
                self.connected = False
                self._debug_print(f"Disconnected from {self.ssid}", DEBUG_BASIC)
            except Exception as e:
                self._debug_print(f"Error during disconnect: {e}", DEBUG_BASIC)

            # Turn off LED to indicate disconnection
            self.led.off()

    def is_connected(self):
        """Check if connected to the WiFi network.

        Returns:
            bool: True if connected, False otherwise
        """
        try:
            is_connected = self.wlan.isconnected()
        except Exception as e:
            self._debug_print(f"Error checking connection status: {e}", DEBUG_BASIC)
            is_connected = False

        # Update internal state if it doesn't match
        if is_connected != self.connected:
            self.connected = is_connected
            if is_connected:
                self._debug_print("WiFi connection detected", DEBUG_BASIC)
            else:
                self._debug_print("WiFi connection lost", DEBUG_BASIC)
                self.led.off()

        return is_connected

    def reconnect_if_needed(self, connection_timeout=45):
        """Reconnect to the WiFi network if the connection is lost.

        Args:
            connection_timeout (int): Timeout for connection attempt in seconds

        Returns:
            bool: True if connected (either already or after reconnection), False otherwise
        """
        if not self.wlan.isconnected():
            self._debug_print("WiFi connection lost. Reconnecting...", DEBUG_BASIC)
            self.connected = False
            self.led.off()
            return self.connect(max_retries=1, retry_delay=1, connection_timeout=connection_timeout)
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
            self._debug_print("Cannot send data: not connected to WiFi", DEBUG_BASIC)
            return False

        # Add device ID to data
        data["device_id"] = self.device_id
        json_data = ujson.dumps(data)

        # Initialize sock to None
        sock = None

        # Retry loop
        for attempt in range(max_retries):
            try:
                self._debug_print(f"Sending data attempt {attempt + 1}/{max_retries}...", DEBUG_BASIC)

                # Create new socket for each attempt
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)  # 10 seconds timeout

                # Connect and send data
                self._debug_print(f"Connecting to server {self.server_ip}:{self.server_port}...", DEBUG_DETAILED)
                sock.connect((self.server_ip, self.server_port))

                self._debug_print(f"Sending data: {json_data}", DEBUG_DETAILED)
                sock.send(json_data.encode())

                # Wait for response
                self._debug_print("Waiting for response...", DEBUG_DETAILED)
                response = sock.recv(1024)

                # Close socket
                sock.close()
                sock = None

                # Process response
                if response:
                    try:
                        response_data = ujson.loads(response.decode())
                        if response_data.get("status") == "success":
                            self._debug_print(f"Data sent successfully on attempt {attempt + 1}", DEBUG_BASIC)
                            self._blink_led(1, 0.1)
                            return True
                        else:
                            self._debug_print(f"Server error: {response_data.get('message', 'Unknown error')}", DEBUG_BASIC)
                    except Exception as e:
                        self._debug_print(f"Invalid response from server: {response}, Error: {e}", DEBUG_BASIC)
                else:
                    self._debug_print("No response from server", DEBUG_BASIC)

            except Exception as e:
                self._debug_print(f"[Attempt {attempt + 1}/{max_retries}] Error sending data: {e}", DEBUG_BASIC)

            finally:
                # Ensure socket is closed
                if sock:
                    try:
                        sock.close()
                    except:
                        pass

                # Force garbage collection
                gc.collect()
                # Allow background processing
                machine.idle()

            # If this wasn't the last attempt, wait before retrying
            if attempt < max_retries - 1:
                # Progressive backoff
                retry_delay = 2 * (attempt + 1)  # 2s, 4s, 6s, 8s...
                self._debug_print(f"Retrying in {retry_delay} seconds...", DEBUG_BASIC)
                time.sleep(retry_delay)

        self._debug_print(f"All {max_retries} retry attempts failed.", DEBUG_BASIC)
        return False

    def get_signal_strength(self):
        """Get the current WiFi signal strength.

        Returns:
            int: Signal strength in dBm, or None if not connected
        """
        if self.wlan.isconnected():
            try:
                return self.wlan.status('rssi')
            except:
                return None
        return None

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

    def __init__(self, wifi_client, transmission_interval=30, debug_level=DEBUG_BASIC):
        """Initialize the data transmitter.

        Args:
            wifi_client (WiFiClient): WiFi client for data transmission
            transmission_interval (int): Interval between transmissions in seconds
            debug_level (int): Level of debug output (0-3)
        """
        self.wifi_client = wifi_client
        self.transmission_interval = transmission_interval
        self.last_transmission_time = 0
        self.sensors = {}
        self.last_readings = {}  # Store last successful readings
        self.transmission_attempts = 0
        self.successful_transmissions = 0
        self.debug_level = debug_level

    def _debug_print(self, message, level=DEBUG_BASIC):
        """Print debug message if debug level is high enough.

        Args:
            message (str): Message to print
            level (int): Minimum debug level required to print this message
        """
        if self.debug_level >= level:
            print(f"[Data] {message}")

        # Allow background processing after printing
        machine.idle()

    def set_debug_level(self, level):
        """Set the debug level.

        Args:
            level (int): Debug level (0-3)
        """
        self.debug_level = level
        self._debug_print(f"Debug level set to {level}", DEBUG_BASIC)

    def add_sensor(self, name, sensor):
        """Add a sensor to the data transmitter.

        Args:
            name (str): Sensor name
            sensor: Sensor object with get_readings() method
        """
        self.sensors[name] = sensor
        self._debug_print(f"Added sensor: {name}", DEBUG_BASIC)

    def collect_and_send_data(self):
        """Collect data from all sensors and send it to the server.

        Returns:
            bool: True if data sent successfully, False otherwise
        """
        # Check if it's time to transmit
        current_time = time.time()
        time_since_last = current_time - self.last_transmission_time

        # Allow background processing
        machine.idle()

        if time_since_last < self.transmission_interval:
            # Not time yet
            return True

        self._debug_print(f"Time to transmit data (interval: {self.transmission_interval}s)", DEBUG_BASIC)

        # Collect data from all sensors
        data = {}
        sensor_errors = 0

        for name, sensor in self.sensors.items():
            try:
                self._debug_print(f"Reading {name} sensor...", DEBUG_BASIC)

                # Allow background processing
                machine.idle()

                # Use get_readings() method for all sensors
                try:
                    sensor_data = sensor.get_readings()
                    self._debug_print(f"{name} readings: {sensor_data}", DEBUG_BASIC)
                    
                    # Store last successful reading
                    self.last_readings[name] = sensor_data
                    data.update(sensor_data)
                except Exception as e:
                    self._debug_print(f"Error getting {name} readings: {e}", DEBUG_BASIC)
                    sensor_errors += 1
                    
                    # Fallback to direct property access for BME680 if get_readings() fails
                    if name == "bme680":
                        try:
                            sensor_data = {
                                "temperature": sensor.temperature,
                                "humidity": sensor.humidity,
                                "pressure": sensor.pressure,
                                "gas_resistance": sensor.gas
                            }
                            self._debug_print(f"BME680 readings (fallback): {sensor_data}", DEBUG_BASIC)
                            
                            # Store last successful reading
                            self.last_readings[name] = sensor_data
                            data.update(sensor_data)
                        except Exception as e2:
                            self._debug_print(f"Error reading BME680 sensor (fallback): {e2}", DEBUG_BASIC)
                            
                            # Use last successful reading if available
                            if name in self.last_readings:
                                self._debug_print(f"Using last successful {name} reading", DEBUG_BASIC)
                                data.update(self.last_readings[name])
                    
                    # Fallback to direct method for MH-Z19C if get_readings() fails
                    elif name == "mhz19c":
                        try:
                            co2_value = sensor.read_co2()
                            if co2_value > 0:  # Only include valid readings
                                sensor_data = {"co2": co2_value}
                                self._debug_print(f"CO2 reading (fallback): {co2_value}ppm", DEBUG_BASIC)
                                # Store last successful reading
                                self.last_readings[name] = sensor_data
                                data.update(sensor_data)
                            else:
                                self._debug_print(f"Invalid CO2 reading: {co2_value}", DEBUG_BASIC)
                                
                                # Use last successful reading if available
                                if name in self.last_readings:
                                    self._debug_print(f"Using last successful {name} reading", DEBUG_BASIC)
                                    data.update(self.last_readings[name])
                        except Exception as e2:
                            self._debug_print(f"Error reading MH-Z19C sensor (fallback): {e2}", DEBUG_BASIC)
                            
                            # Use last successful reading if available
                            if name in self.last_readings:
                                self._debug_print(f"Using last successful {name} reading", DEBUG_BASIC)
                                data.update(self.last_readings[name])
            except Exception as e:
                self._debug_print(f"Error reading {name} sensor: {e}", DEBUG_BASIC)
                sensor_errors += 1

                # Use last successful reading if available
                if name in self.last_readings:
                    self._debug_print(f"Using last successful {name} reading", DEBUG_BASIC)
                    data.update(self.last_readings[name])

        # Add timestamp and device ID
        data["timestamp"] = current_time
        data["device_id"] = self.wifi_client.device_id

        # Add sensor status
        data["sensor_errors"] = sensor_errors

        # Send data if we have any
        if data:
            self.transmission_attempts += 1
            self._debug_print(f"Sending data (attempt {self.transmission_attempts})...", DEBUG_BASIC)
            success = self.wifi_client.send_data(data)

            if success:
                self.last_transmission_time = current_time
                self.successful_transmissions += 1
                self._debug_print(f"Data sent successfully. Total successful: {self.successful_transmissions}/{self.transmission_attempts}", DEBUG_BASIC)
            else:
                self._debug_print(f"Failed to send data. Success rate: {self.successful_transmissions}/{self.transmission_attempts}", DEBUG_BASIC)

            return success
        else:
            self._debug_print("No data to send", DEBUG_BASIC)
            return False
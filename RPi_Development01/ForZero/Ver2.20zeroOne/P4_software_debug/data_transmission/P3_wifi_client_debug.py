#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi Pico 2W WiFi Client for Environmental Monitoring - Debug Version 4.19
Version: 4.19.0-debug

This module provides WiFi connectivity and data transmission functionality for the
Raspberry Pi Pico 2W (P3) environmental monitoring system.

Features:
- Enhanced debugging options for troubleshooting
- Multiple connection strategies
- Detailed status reporting
- Configurable retry mechanisms
- Network diagnostics
- Data transmission with retry logic
- Improved error handling for Thonny compatibility
- Reduced USB/REPL disconnection issues

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

# File for logging instead of printing
LOG_TO_FILE = False
LOG_FILE = "/wifi_log.txt"

class WiFiClient:
    """Class to manage WiFi connection and data transmission with enhanced debugging."""

    def __init__(self, ssid="RaspberryPi5_AP_Solo", password="raspberry", 
                 server_ip="192.168.0.2", server_port=5000, device_id="P4",
                 debug_level=DEBUG_DETAILED, debug_mode=False):
        """Initialize the WiFi client with the given configuration.

        Args:
            ssid (str): WiFi network SSID
            password (str): WiFi network password
            server_ip (str): IP address of the data collection server
            server_port (int): Port of the data collection server
            device_id (str): Device identifier (P3)
            debug_level (int): Level of debug output (0-3)
            debug_mode (bool): Enable or disable debug mode
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
        self.debug_mode = debug_mode
        self.connection_strategy = "standard"  # Options: standard, aggressive, conservative
        self.auto_reset = True  # Whether to auto-reset on connection failure
        self.log_to_file = LOG_TO_FILE

        # Initialize LED
        self.led.off()

        # Print configuration
        self._debug_print(f"WiFi Client initialized for {device_id} (Debug Version 4.19)", DEBUG_BASIC)
        self._debug_print(f"Server: {server_ip}:{server_port}", DEBUG_BASIC)
        self._debug_print(f"Debug level: {debug_level}", DEBUG_BASIC)
        self._debug_print(f"Debug mode: {debug_mode}", DEBUG_BASIC)

    def _debug_print(self, message, level=DEBUG_BASIC):
        """Print debug message if debug level is high enough.

        Args:
            message (str): Message to print
            level (int): Minimum debug level required to print this message
        """
        if self.debug_level >= level:
            if self.log_to_file:
                try:
                    with open(LOG_FILE, "a") as f:
                        f.write(f"[WiFi Debug] {message}\n")
                except:
                    # Fall back to print if file logging fails
                    print(f"[WiFi Debug] {message}")
            else:
                print(f"[WiFi Debug] {message}")

        # Allow background processing after printing
        machine.idle()

    def set_debug_level(self, level):
        """Set the debug level.

        Args:
            level (int): Debug level (0-3)
        """
        self.debug_level = level
        self._debug_print(f"Debug level set to {level}", DEBUG_BASIC)

    def set_connection_strategy(self, strategy):
        """Set the connection strategy.

        Args:
            strategy (str): Connection strategy (standard, aggressive, conservative)
        """
        valid_strategies = ["standard", "aggressive", "conservative"]
        if strategy not in valid_strategies:
            self._debug_print(f"Invalid strategy: {strategy}. Using standard.", DEBUG_BASIC)
            strategy = "standard"

        self.connection_strategy = strategy
        self._debug_print(f"Connection strategy set to {strategy}", DEBUG_BASIC)

    def set_auto_reset(self, auto_reset):
        """Set whether to auto-reset on connection failure.

        Args:
            auto_reset (bool): Whether to auto-reset
        """
        self.auto_reset = auto_reset
        self._debug_print(f"Auto-reset set to {auto_reset}", DEBUG_BASIC)

    def connect(self, max_retries=10, retry_delay=5, connection_timeout=45, 
                debug_level=None, connection_strategy=None, auto_reset=None):
        """Connect to the WiFi network with configurable timeout and enhanced debugging.

        Args:
            max_retries (int): Maximum number of connection attempts
            retry_delay (int): Delay between retries in seconds
            connection_timeout (int): Timeout for each connection attempt in seconds
            debug_level (int): Override the instance debug level for this connection
            connection_strategy (str): Override the connection strategy for this attempt
            auto_reset (bool): Override the auto-reset setting for this attempt

        Returns:
            bool: True if connection successful, False otherwise
        """
        # Apply overrides if provided
        if debug_level is not None:
            old_debug_level = self.debug_level
            self.set_debug_level(debug_level)

        if connection_strategy is not None:
            old_strategy = self.connection_strategy
            self.set_connection_strategy(connection_strategy)

        if auto_reset is not None:
            old_auto_reset = self.auto_reset
            self.set_auto_reset(auto_reset)

        # Print connection parameters
        self._debug_print(f"Connecting to WiFi network: {self.ssid}", DEBUG_BASIC)
        self._debug_print(f"Connection parameters:", DEBUG_BASIC)
        self._debug_print(f"  Max retries: {max_retries}", DEBUG_BASIC)
        self._debug_print(f"  Retry delay: {retry_delay} seconds", DEBUG_BASIC)
        self._debug_print(f"  Connection timeout: {connection_timeout} seconds", DEBUG_BASIC)
        self._debug_print(f"  Connection strategy: {self.connection_strategy}", DEBUG_BASIC)
        self._debug_print(f"  Auto-reset: {self.auto_reset}", DEBUG_BASIC)

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
            # Minimal connection info to avoid USB/REPL issues
            if self.debug_level >= DEBUG_DETAILED:
                self._print_connection_info()
            return True

        # Adjust parameters based on connection strategy
        if self.connection_strategy == "aggressive":
            self._debug_print("Using aggressive connection strategy", DEBUG_DETAILED)
            # Shorter timeouts, more retries
            connection_timeout = max(15, connection_timeout // 2)
            max_retries = max_retries * 2
            retry_delay = max(1, retry_delay // 2)
        elif self.connection_strategy == "conservative":
            self._debug_print("Using conservative connection strategy", DEBUG_DETAILED)
            # Longer timeouts, fewer retries
            connection_timeout = connection_timeout * 2
            max_retries = max(1, max_retries // 2)
            retry_delay = retry_delay * 2

        self._debug_print(f"Adjusted parameters: timeout={connection_timeout}s, retries={max_retries}, delay={retry_delay}s", DEBUG_DETAILED)

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
                self._debug_print("Running garbage collection...", DEBUG_VERBOSE)
                gc.collect()

                # Print WiFi status before connection attempt
                status = self.wlan.status()
                self._debug_print(f"WiFi status before connection: {self._status_to_string(status)}", DEBUG_DETAILED)

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
                    if timeout % (10 if self.debug_level <= DEBUG_BASIC else 5) == 0:
                        self._debug_print(f"Waiting for connection... {timeout}/{connection_timeout} seconds", DEBUG_BASIC)
                        # Print connection status
                        try:
                            status = self.wlan.status()
                            self._debug_print(f"WiFi status: {self._status_to_string(status)}", DEBUG_BASIC)
                        except Exception as e:
                            self._debug_print(f"Error getting WiFi status: {e}", DEBUG_BASIC)

                        # Print more detailed status in verbose mode - WRAPPED IN TRY/EXCEPT
                        if self.debug_level >= DEBUG_VERBOSE:
                            self._debug_print(f"Raw status code: {status}", DEBUG_VERBOSE)
                            if hasattr(self.wlan, 'scan'):
                                try:
                                    self._debug_print("Scanning for networks...", DEBUG_VERBOSE)
                                    networks = self.wlan.scan()
                                    self._debug_print(f"Networks found: {len(networks)}", DEBUG_VERBOSE)
                                    for net in networks:
                                        ssid = net[0].decode('utf-8', 'ignore') if isinstance(net[0], bytes) else net[0]
                                        self._debug_print(f"  SSID: {ssid}, RSSI: {net[3]}", DEBUG_VERBOSE)
                                except Exception as e:
                                    self._debug_print(f"Error scanning networks: {e}", DEBUG_VERBOSE)

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

            # Minimal connection info to avoid USB/REPL issues
            if self.debug_level >= DEBUG_DETAILED:
                self._print_connection_info()
            else:
                # Just print minimal info
                self._debug_print(f"Connected to {self.ssid}", DEBUG_BASIC)
                try:
                    network_info = self.wlan.ifconfig()
                    self._debug_print(f"IP: {network_info[0]}", DEBUG_BASIC)
                except:
                    pass

            # Turn on LED to indicate successful connection
            self.led.on()

            # Restore overrides if provided
            if debug_level is not None:
                self.set_debug_level(old_debug_level)
            if connection_strategy is not None:
                self.set_connection_strategy(old_strategy)
            if auto_reset is not None:
                self.set_auto_reset(old_auto_reset)

            return True
        else:
            self._debug_print(f"Failed to connect to {self.ssid} after {max_retries} attempts", DEBUG_BASIC)

            # Rapid blink to indicate connection failure
            self._blink_led(10, 0.1)

            # Restore overrides if provided
            if debug_level is not None:
                self.set_debug_level(old_debug_level)
            if connection_strategy is not None:
                self.set_connection_strategy(old_strategy)
            if auto_reset is not None:
                self.set_auto_reset(old_auto_reset)

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

            # Only print detailed info in verbose mode to reduce USB/REPL load
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

                # Print more detailed info in verbose mode
                self._debug_print("Additional connection information:", DEBUG_VERBOSE)
                self._debug_print(f"  Connection attempts: {self.connection_attempts}", DEBUG_VERBOSE)
                self._debug_print(f"  Last connection time: {self.last_connection_time}", DEBUG_VERBOSE)
                self._debug_print(f"  Connection strategy: {self.connection_strategy}", DEBUG_VERBOSE)

                # Try to get MAC address
                try:
                    mac = self.wlan.config('mac')
                    mac_str = ':'.join('{:02x}'.format(b) for b in mac)
                    self._debug_print(f"  MAC address: {mac_str}", DEBUG_VERBOSE)
                except:
                    self._debug_print("  Could not get MAC address", DEBUG_VERBOSE)
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

    def get_connection_info(self):
        """Get detailed information about the current connection.

        Returns:
            dict: Connection information including IP, signal strength, etc.
                  Empty dict if not connected.
        """
        if not self.wlan.isconnected():
            return {
                "connected": False,
                "device_id": self.device_id,
                "connection_attempts": self.connection_attempts,
                "last_connection_time": self.last_connection_time,
                "debug_level": self.debug_level,
                "debug_mode": self.debug_mode,
                "connection_strategy": self.connection_strategy,
                "auto_reset": self.auto_reset
            }

        try:
            network_info = self.wlan.ifconfig()
            rssi = self.get_signal_strength()

            return {
                "connected": True,
                "ssid": self.ssid,
                "ip_address": network_info[0],
                "subnet_mask": network_info[1],
                "gateway": network_info[2],
                "dns_server": network_info[3],
                "signal_strength": rssi,
                "device_id": self.device_id,
                "connection_attempts": self.connection_attempts,
                "last_connection_time": self.last_connection_time,
                "debug_level": self.debug_level,
                "debug_mode": self.debug_mode,
                "connection_strategy": self.connection_strategy,
                "auto_reset": self.auto_reset
            }
        except Exception as e:
            self._debug_print(f"Error getting connection info: {e}", DEBUG_BASIC)
            return {"connected": self.wlan.isconnected(), "device_id": self.device_id}

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

    def run_network_diagnostics(self):
        """Run network diagnostics and print results.

        Returns:
            dict: Diagnostic results
        """
        self._debug_print("Running network diagnostics...", DEBUG_BASIC)

        results = {
            "wifi_active": self.wlan.active(),
            "wifi_connected": self.wlan.isconnected(),
            "connection_attempts": self.connection_attempts
        }

        # Check if connected
        if self.wlan.isconnected():
            try:
                # Get network info
                network_info = self.wlan.ifconfig()
                results["ip_address"] = network_info[0]
                results["subnet_mask"] = network_info[1]
                results["gateway"] = network_info[2]
                results["dns_server"] = network_info[3]

                # Get signal strength
                rssi = self.get_signal_strength()
                results["signal_strength"] = rssi

                # Try to ping the server - WRAPPED IN TRY/EXCEPT
                self._debug_print(f"Testing connection to server {self.server_ip}...", DEBUG_BASIC)
                sock = None
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    start_time = time.time()
                    sock.connect((self.server_ip, self.server_port))
                    ping_time = (time.time() - start_time) * 1000  # ms
                    results["server_ping"] = ping_time
                    results["server_reachable"] = True
                    self._debug_print(f"Server ping: {ping_time:.1f}ms", DEBUG_BASIC)
                except Exception as e:
                    results["server_reachable"] = False
                    results["server_error"] = str(e)
                    self._debug_print(f"Server connection failed: {e}", DEBUG_BASIC)
                finally:
                    if sock:
                        try:
                            sock.close()
                        except:
                            pass
            except Exception as e:
                self._debug_print(f"Error during diagnostics: {e}", DEBUG_BASIC)
                results["error"] = str(e)
        else:
            # Try to scan for networks - WRAPPED IN TRY/EXCEPT
            try:
                if hasattr(self.wlan, 'scan'):
                    self._debug_print("Scanning for networks...", DEBUG_BASIC)
                    # Add a sleep before scan to improve stability
                    time.sleep(1)
                    try:
                        networks = self.wlan.scan()
                        results["networks_found"] = len(networks)
                        results["networks"] = []
                        target_network_found = False
                        target_network_strength = None

                        for net in networks:
                            ssid = net[0].decode('utf-8', 'ignore') if isinstance(net[0], bytes) else net[0]
                            network_info = {
                                "ssid": ssid,
                                "rssi": net[3]
                            }
                            results["networks"].append(network_info)

                            if ssid == self.ssid:
                                target_network_found = True
                                target_network_strength = net[3]

                        results["target_network_found"] = target_network_found
                        results["target_network_strength"] = target_network_strength

                        if target_network_found:
                            self._debug_print(f"Target network '{self.ssid}' found with signal strength {target_network_strength} dBm", DEBUG_BASIC)
                        else:
                            self._debug_print(f"Target network '{self.ssid}' not found", DEBUG_BASIC)
                    except Exception as e:
                        self._debug_print(f"Error during network scan: {e}", DEBUG_BASIC)
                        results["scan_error"] = str(e)
            except Exception as e:
                self._debug_print(f"Error scanning networks: {e}", DEBUG_BASIC)
                results["scan_error"] = str(e)

        # Print summary
        self._debug_print("Network diagnostics complete", DEBUG_BASIC)

        # Add diagnostics summary and automatic decision logic
        if self.debug_mode and self.debug_level >= DEBUG_BASIC:
            print("\nDiagnostics Summary:")
            print(f"WiFi Active: {self.wlan.active()}")
            print(f"Target Network Found: {results.get('target_network_found', False)}")
            print(f"Signal Strength: {results.get('target_network_strength', 'N/A')} dBm")
            proceed = True  # ← debugオプションで変えられるようにする
            if not proceed:
                print("Connection attempt skipped. Continuing without WiFi connection.")
                return False

        return results

    def reduce_cpu_speed(self):
        """Reduce CPU speed to minimize power consumption and improve stability.

        This is one of the emergency measures to try when having connection issues.
        """
        try:
            # Get current frequency
            current_freq = machine.freq()
            self._debug_print(f"Current CPU frequency: {current_freq/1000000}MHz", DEBUG_BASIC)

            # Reduce to 125MHz (default is 133MHz)
            machine.freq(125_000_000)

            new_freq = machine.freq()
            self._debug_print(f"CPU frequency reduced to: {new_freq/1000000}MHz", DEBUG_BASIC)
            return True
        except Exception as e:
            self._debug_print(f"Error reducing CPU frequency: {e}", DEBUG_BASIC)
            return False

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
        self.log_to_file = LOG_TO_FILE

    def _debug_print(self, message, level=DEBUG_BASIC):
        """Print debug message if debug level is high enough.

        Args:
            message (str): Message to print
            level (int): Minimum debug level required to print this message
        """
        if self.debug_level >= level:
            if self.log_to_file:
                try:
                    with open(LOG_FILE, "a") as f:
                        f.write(f"[Data Debug] {message}\n")
                except:
                    # Fall back to print if file logging fails
                    print(f"[Data Debug] {message}")
            else:
                print(f"[Data Debug] {message}")

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
            remaining = self.transmission_interval - time_since_last
            if int(remaining) % 10 == 0:  # Log every 10 seconds
                self._debug_print(f"Next transmission in {int(remaining)} seconds", DEBUG_DETAILED)
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

                if name == "bme680":
                    # For the BME680 sensor, access properties directly
                    try:
                        sensor_data = {
                            "temperature": sensor.temperature,
                            "humidity": sensor.humidity,
                            "pressure": sensor.pressure,
                            "gas_resistance": sensor.gas
                        }
                        self._debug_print(f"BME680 readings: Temp={sensor_data['temperature']}°C, "
                              f"Humidity={sensor_data['humidity']}%, "
                              f"Pressure={sensor_data['pressure']}hPa, "
                              f"Gas={sensor_data['gas_resistance']}Ω", DEBUG_BASIC)

                        # Store last successful reading
                        self.last_readings[name] = sensor_data
                        data.update(sensor_data)
                    except Exception as e:
                        self._debug_print(f"Error reading BME680 sensor: {e}", DEBUG_BASIC)
                        sensor_errors += 1

                        # Use last successful reading if available
                        if name in self.last_readings:
                            self._debug_print(f"Using last successful {name} reading", DEBUG_BASIC)
                            data.update(self.last_readings[name])

                elif name == "mhz19c":
                    # For the MH-Z19C CO2 sensor
                    try:
                        co2_value = sensor.read_co2()
                        if co2_value > 0:  # Only include valid readings
                            sensor_data = {"co2": co2_value}
                            self._debug_print(f"CO2 reading: {co2_value}ppm", DEBUG_BASIC)
                            # Store last successful reading
                            self.last_readings[name] = sensor_data
                            data.update(sensor_data)
                        else:
                            self._debug_print(f"Invalid CO2 reading: {co2_value}", DEBUG_BASIC)
                            sensor_errors += 1

                            # Use last successful reading if available
                            if name in self.last_readings:
                                self._debug_print(f"Using last successful {name} reading", DEBUG_BASIC)
                                data.update(self.last_readings[name])
                    except Exception as e:
                        self._debug_print(f"Error reading MH-Z19C sensor: {e}", DEBUG_BASIC)
                        sensor_errors += 1

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

    def run(self, run_once=False):
        """Run the data transmitter.

        Args:
            run_once (bool): If True, run once and return. If False, run continuously.
        """
        self._debug_print("Starting data transmitter...", DEBUG_BASIC)

        if run_once:
            return self.collect_and_send_data()

        try:
            while True:
                try:
                    # Collect and send data
                    self.collect_and_send_data()

                    # Sleep a bit to prevent tight loop
                    # This is important to allow background WiFi processing
                    machine.idle()
                    time.sleep(1)

                except Exception as e:
                    self._debug_print(f"Error in data transmission loop: {e}", DEBUG_BASIC)
                    time.sleep(5)  # Wait a bit longer after an error
        except KeyboardInterrupt:
            self._debug_print("Data transmitter stopped by user", DEBUG_BASIC)

        return True

# Example usage
if __name__ == "__main__":
    try:
        # Import sensor drivers
        import sys
        sys.path.append('sensor_drivers')
        from bme680 import BME680_I2C
        from mhz19c import MHZ19C
        from machine import I2C, Pin

        # Reduce CPU frequency for better stability
        try:
            original_freq = machine.freq()
            print(f"Original CPU frequency: {original_freq/1000000}MHz")
            machine.freq(125_000_000)
            print(f"Reduced CPU frequency to: {machine.freq()/1000000}MHz")
        except Exception as e:
            print(f"Could not reduce CPU frequency: {e}")

        print("=== P3 WiFi Client Debug Test (Ver 4.19.0) ===")

        # Initialize I2C for BME680
        i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=100000)

        # Initialize BME680 sensor
        bme = BME680_I2C(i2c, address=0x77)

        # Initialize MH-Z19C CO2 sensor
        co2_sensor = MHZ19C(uart_id=1, tx_pin=8, rx_pin=9)

        # Wait for CO2 sensor warmup
        print("Waiting for CO2 sensor warmup...")
        time.sleep(30)

        # Initialize WiFi client with debug level
        client = WiFiClient(device_id="P4", debug_level=DEBUG_DETAILED, debug_mode=True)

        # Run network diagnostics only (emergency measure)
        print("\nRunning network diagnostics (without connection attempt)...")
        diagnostics = client.run_network_diagnostics()

        # Print key diagnostics results
        print("\nDiagnostics Summary:")
        print(f"WiFi Active: {diagnostics.get('wifi_active', False)}")
        if 'networks_found' in diagnostics:
            print(f"Networks Found: {diagnostics.get('networks_found', 0)}")
            print(f"Target Network Found: {diagnostics.get('target_network_found', False)}")
            if diagnostics.get('target_network_found', False):
                print(f"Target Network Strength: {diagnostics.get('target_network_strength', 'Unknown')} dBm")

        # Automatic decision based on diagnostics
        proceed = True  # Always proceed in automated mode

        # Check if target network was found
        if diagnostics.get('target_network_found', False):
            print("\nTarget network found. Proceeding with connection...")
        else:
            print("\nTarget network not found, but proceeding with connection attempt...")

        # Allow background processing
        machine.idle()
        time.sleep(0.5)

        # Try different connection strategies
        print("\nTrying standard connection strategy...")
        client.set_connection_strategy("standard")
        client.set_auto_reset(False)
        if not client.connect():
            print("\nTrying aggressive connection strategy...")
            client.set_connection_strategy("aggressive")
            if not client.connect():
                print("\nTrying conservative connection strategy...")
                client.set_connection_strategy("conservative")
                client.connect()

        # Initialize data transmitter
        transmitter = DataTransmitter(client, debug_level=DEBUG_BASIC)
        transmitter.add_sensor("bme680", bme)
        transmitter.add_sensor("mhz19c", co2_sensor)

        # Run data transmitter
        print("Starting data transmission...")
        transmitter.run()

    except Exception as e:
        print(f"Error: {e}")

        # Reset the device after a delay if there's an error
        print("Resetting device in 20 seconds...")
        time.sleep(20)
        machine.reset()

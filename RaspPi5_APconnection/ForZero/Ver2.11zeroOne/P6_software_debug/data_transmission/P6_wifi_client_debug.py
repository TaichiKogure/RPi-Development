#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi Pico 2W WiFi Client for Environmental Monitoring - Debug Version 4.19
Version: 4.19.0-debug

This module provides WiFi connectivity and data transmission functionality for the
Raspberry Pi Pico 2W (P6) environmental monitoring system.

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
                 server_ip="192.168.0.1", server_port=5000, device_id="P6",
                 debug_level=DEBUG_DETAILED, debug_mode=False):
        """Initialize the WiFi client with the given configuration.

        Args:
            ssid (str): WiFi network SSID
            password (str): WiFi network password
            server_ip (str): IP address of the data collection server
            server_port (int): Port of the data collection server
            device_id (str): Device identifier (P6)
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
        if strategy in ["standard", "aggressive", "conservative"]:
            self.connection_strategy = strategy
            self._debug_print(f"Connection strategy set to {strategy}", DEBUG_BASIC)
        else:
            self._debug_print(f"Invalid connection strategy: {strategy}", DEBUG_BASIC)

    def set_auto_reset(self, enabled):
        """Set whether to auto-reset on connection failure.

        Args:
            enabled (bool): Whether to auto-reset
        """
        self.auto_reset = enabled
        self._debug_print(f"Auto-reset set to {enabled}", DEBUG_BASIC)

    def connect(self, timeout=30, max_retries=5):
        """Connect to WiFi network with the given configuration.

        Args:
            timeout (int): Connection timeout in seconds
            max_retries (int): Maximum number of connection retries

        Returns:
            bool: True if connected, False otherwise
        """
        self._debug_print(f"Connecting to WiFi network: {self.ssid}", DEBUG_BASIC)
        self._debug_print(f"Connection timeout: {timeout} seconds", DEBUG_BASIC)

        # Activate WiFi interface
        self._debug_print("Activating WiFi interface...", DEBUG_DETAILED)
        self.wlan.active(True)
        time.sleep(1)  # Allow time for interface to activate

        # Scan for networks
        self._debug_print("Scanning for networks...", DEBUG_DETAILED)
        try:
            networks = self.wlan.scan()
            if self.debug_level >= DEBUG_DETAILED:
                for network in networks:
                    ssid = network[0].decode('utf-8') if isinstance(network[0], bytes) else network[0]
                    self._debug_print(f"Found network: {ssid}", DEBUG_VERBOSE)
        except Exception as e:
            self._debug_print(f"Error scanning for networks: {e}", DEBUG_BASIC)
            networks = []

        # Check if target network is in range
        target_network_found = False
        target_network_strength = None
        for network in networks:
            ssid = network[0].decode('utf-8') if isinstance(network[0], bytes) else network[0]
            if ssid == self.ssid:
                target_network_found = True
                target_network_strength = network[3]  # RSSI
                self._debug_print(f"Target network found with signal strength: {target_network_strength} dBm", DEBUG_DETAILED)
                break

        if not target_network_found:
            self._debug_print(f"Target network '{self.ssid}' not found", DEBUG_BASIC)
            # Continue anyway, as the network might be hidden or the scan might have missed it

        # Connect to network
        self._debug_print(f"Sending connection request to {self.ssid}...", DEBUG_DETAILED)
        try:
            self.wlan.connect(self.ssid, self.password)
        except Exception as e:
            self._debug_print(f"Error sending connection request: {e}", DEBUG_BASIC)
            return False

        # Wait for connection
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.wlan.isconnected():
                # Get connection info
                ip, subnet, gateway, dns = self.wlan.ifconfig()
                self._debug_print(f"Connected to {self.ssid}", DEBUG_BASIC)
                self._debug_print(f"IP address: {ip}", DEBUG_BASIC)
                
                if self.debug_level >= DEBUG_DETAILED:
                    self._debug_print(f"Subnet mask: {subnet}", DEBUG_DETAILED)
                    self._debug_print(f"Gateway: {gateway}", DEBUG_DETAILED)
                    self._debug_print(f"DNS server: {dns}", DEBUG_DETAILED)
                
                self.connected = True
                self.connection_attempts = 0
                self.last_connection_time = time.time()
                
                # Blink LED to indicate successful connection
                self.led.on()
                time.sleep(0.1)
                self.led.off()
                
                return True
            
            # Check connection status
            status = self.wlan.status()
            if status == network.STAT_CONNECTING:
                self._debug_print("Still connecting...", DEBUG_VERBOSE)
            elif status == network.STAT_WRONG_PASSWORD:
                self._debug_print("Wrong password", DEBUG_BASIC)
                return False
            elif status == network.STAT_NO_AP_FOUND:
                self._debug_print("No access point found", DEBUG_BASIC)
                return False
            elif status == network.STAT_CONNECT_FAIL:
                self._debug_print("Connection failed", DEBUG_BASIC)
                return False
            
            # Allow background processing
            machine.idle()
            time.sleep(0.1)
        
        self._debug_print(f"Connection timeout after {timeout} seconds", DEBUG_BASIC)
        return False

    def disconnect(self):
        """Disconnect from WiFi network."""
        if self.connected:
            self._debug_print("Disconnecting from WiFi...", DEBUG_BASIC)
            self.wlan.disconnect()
            self.wlan.active(False)
            self.connected = False
            self._debug_print("Disconnected", DEBUG_BASIC)
        else:
            self._debug_print("Not connected, nothing to disconnect", DEBUG_DETAILED)

    def reconnect(self, timeout=30):
        """Reconnect to WiFi network.

        Args:
            timeout (int): Connection timeout in seconds

        Returns:
            bool: True if reconnected, False otherwise
        """
        self._debug_print("Reconnecting to WiFi...", DEBUG_BASIC)
        
        # Disconnect first if connected
        if self.connected:
            self.disconnect()
        
        # Wait a moment before reconnecting
        time.sleep(1)
        
        # Try to connect
        return self.connect(timeout=timeout)

    def is_connected(self):
        """Check if connected to WiFi.

        Returns:
            bool: True if connected, False otherwise
        """
        # Update connected status
        self.connected = self.wlan.isconnected()
        return self.connected

    def get_signal_strength(self):
        """Get signal strength in dBm.

        Returns:
            int: Signal strength in dBm or None if not connected
        """
        if not self.is_connected():
            return None
        
        try:
            # This is not standardized across all MicroPython ports
            # Some ports might not have this method
            return self.wlan.status('rssi')
        except:
            self._debug_print("RSSI measurement not supported", DEBUG_DETAILED)
            return None

    def ping_server(self, count=3, timeout=1):
        """Ping the server to check connectivity.

        Args:
            count (int): Number of pings to send
            timeout (int): Timeout for each ping in seconds

        Returns:
            float: Average round-trip time in milliseconds or None if failed
        """
        if not self.is_connected():
            self._debug_print("Not connected to WiFi, cannot ping server", DEBUG_BASIC)
            return None
        
        self._debug_print(f"Pinging server {self.server_ip}...", DEBUG_DETAILED)
        
        # MicroPython doesn't have a built-in ping function
        # We'll use a simple socket connection as a substitute
        total_time = 0
        success_count = 0
        
        for i in range(count):
            try:
                start_time = time.time()
                
                # Create socket
                s = socket.socket()
                s.settimeout(timeout)
                
                # Connect to server
                s.connect((self.server_ip, self.server_port))
                
                # Close socket
                s.close()
                
                # Calculate round-trip time
                rtt = (time.time() - start_time) * 1000  # Convert to milliseconds
                total_time += rtt
                success_count += 1
                
                self._debug_print(f"Ping {i+1}/{count}: {rtt:.2f} ms", DEBUG_VERBOSE)
                
                # Wait a moment before next ping
                time.sleep(0.1)
                
            except Exception as e:
                self._debug_print(f"Ping {i+1}/{count} failed: {e}", DEBUG_DETAILED)
        
        if success_count > 0:
            avg_rtt = total_time / success_count
            self._debug_print(f"Average ping: {avg_rtt:.2f} ms ({success_count}/{count} successful)", DEBUG_DETAILED)
            return avg_rtt
        else:
            self._debug_print(f"All pings failed", DEBUG_BASIC)
            return None

    def send_data(self, data, retries=3):
        """Send data to the server.

        Args:
            data (dict): Data to send
            retries (int): Number of retries if sending fails

        Returns:
            bool: True if data was sent successfully, False otherwise
        """
        if not self.is_connected():
            self._debug_print("Not connected to WiFi, cannot send data", DEBUG_BASIC)
            if self.reconnect():
                self._debug_print("Reconnected to WiFi, continuing with data transmission", DEBUG_BASIC)
            else:
                self._debug_print("Failed to reconnect to WiFi, aborting data transmission", DEBUG_BASIC)
                return False
        
        self._debug_print("Sending data to server...", DEBUG_DETAILED)
        if self.debug_level >= DEBUG_VERBOSE:
            self._debug_print(f"Data: {data}", DEBUG_VERBOSE)
        
        # Convert data to JSON
        try:
            json_data = ujson.dumps(data)
        except Exception as e:
            self._debug_print(f"Error converting data to JSON: {e}", DEBUG_BASIC)
            return False
        
        # Send data
        for attempt in range(retries):
            try:
                # Create socket
                s = socket.socket()
                s.settimeout(5)  # 5 second timeout
                
                # Connect to server
                s.connect((self.server_ip, self.server_port))
                
                # Send data
                s.send(json_data.encode())
                
                # Wait for response
                response = s.recv(1024).decode()
                
                # Close socket
                s.close()
                
                # Check response
                if response:
                    try:
                        response_data = ujson.loads(response)
                        if response_data.get('status') == 'success':
                            self._debug_print("Data sent successfully", DEBUG_BASIC)
                            return True
                        else:
                            self._debug_print(f"Server returned error: {response_data.get('message', 'Unknown error')}", DEBUG_BASIC)
                    except:
                        self._debug_print(f"Invalid response from server: {response}", DEBUG_BASIC)
                else:
                    self._debug_print("No response from server", DEBUG_BASIC)
                
            except Exception as e:
                self._debug_print(f"Error sending data (attempt {attempt+1}/{retries}): {e}", DEBUG_BASIC)
            
            # Wait before retry
            if attempt < retries - 1:
                self._debug_print(f"Retrying in 2 seconds... (attempt {attempt+1}/{retries})", DEBUG_DETAILED)
                time.sleep(2)
        
        self._debug_print(f"Failed to send data after {retries} attempts", DEBUG_BASIC)
        return False

    def run_network_diagnostics(self):
        """Run network diagnostics and return results.

        Returns:
            dict: Diagnostic results
        """
        self._debug_print("Running network diagnostics...", DEBUG_BASIC)
        
        results = {
            "wifi_active": self.wlan.active(),
            "connected": self.is_connected(),
            "target_network_found": False,
            "target_network_strength": None,
            "ip_address": None,
            "gateway": None,
            "dns": None,
            "server_ping": None
        }
        
        # Check if WiFi is active
        if not results["wifi_active"]:
            self._debug_print("WiFi interface is not active", DEBUG_BASIC)
            self.wlan.active(True)
            time.sleep(1)
            results["wifi_active"] = self.wlan.active()
            self._debug_print(f"WiFi interface activated: {results['wifi_active']}", DEBUG_BASIC)
        
        # Scan for networks
        self._debug_print("Scanning for networks...", DEBUG_BASIC)
        try:
            networks = self.wlan.scan()
            for network in networks:
                ssid = network[0].decode('utf-8') if isinstance(network[0], bytes) else network[0]
                if ssid == self.ssid:
                    results["target_network_found"] = True
                    results["target_network_strength"] = network[3]  # RSSI
                    self._debug_print(f"Target network found with signal strength: {results['target_network_strength']} dBm", DEBUG_BASIC)
                    break
            
            if not results["target_network_found"]:
                self._debug_print(f"Target network '{self.ssid}' not found", DEBUG_BASIC)
        except Exception as e:
            self._debug_print(f"Error scanning for networks: {e}", DEBUG_BASIC)
        
        # Check connection status
        if results["connected"]:
            # Get connection info
            ip, subnet, gateway, dns = self.wlan.ifconfig()
            results["ip_address"] = ip
            results["gateway"] = gateway
            results["dns"] = dns
            
            self._debug_print(f"Connected to {self.ssid}", DEBUG_BASIC)
            self._debug_print(f"IP address: {ip}", DEBUG_BASIC)
            self._debug_print(f"Gateway: {gateway}", DEBUG_BASIC)
            self._debug_print(f"DNS server: {dns}", DEBUG_BASIC)
            
            # Ping server
            results["server_ping"] = self.ping_server()
            if results["server_ping"] is not None:
                self._debug_print(f"Server ping: {results['server_ping']:.2f} ms", DEBUG_BASIC)
            else:
                self._debug_print("Server ping failed", DEBUG_BASIC)
        else:
            self._debug_print("Not connected to WiFi", DEBUG_BASIC)
        
        self._debug_print("Network diagnostics complete", DEBUG_BASIC)
        
        # Print summary
        self._debug_print("\nDiagnostics Summary:", DEBUG_BASIC)
        self._debug_print(f"WiFi Active: {results['wifi_active']}", DEBUG_BASIC)
        self._debug_print(f"Target Network Found: {results['target_network_found']}", DEBUG_BASIC)
        self._debug_print(f"Signal Strength: {results['target_network_strength']} dBm", DEBUG_BASIC)
        self._debug_print(f"Connected: {results['connected']}", DEBUG_BASIC)
        if results["connected"]:
            self._debug_print(f"IP Address: {results['ip_address']}", DEBUG_BASIC)
            self._debug_print(f"Server Ping: {results['server_ping']} ms", DEBUG_BASIC)
        
        return results

# Simplified interface for main.py
class DataTransmitter:
    """Simplified interface for data transmission."""
    
    def __init__(self, server_ip="192.168.0.1", server_port=5000, device_id="P6"):
        """Initialize the data transmitter.
        
        Args:
            server_ip (str): Server IP address
            server_port (int): Server port
            device_id (str): Device identifier
        """
        self.client = WiFiClient(
            server_ip=server_ip,
            server_port=server_port,
            device_id=device_id
        )
        self.device_id = device_id
        self.sensors = []
    
    def add_sensor(self, sensor_id):
        """Add a sensor to the data transmitter.
        
        Args:
            sensor_id (str): Sensor identifier
        """
        if sensor_id not in self.sensors:
            self.sensors.append(sensor_id)
    
    def send_data(self, data):
        """Send data to the server.
        
        Args:
            data (dict): Data to send
            
        Returns:
            bool: True if data was sent successfully, False otherwise
        """
        # Ensure device_id is included
        if "device_id" not in data:
            data["device_id"] = self.device_id
        
        return self.client.send_data(data)
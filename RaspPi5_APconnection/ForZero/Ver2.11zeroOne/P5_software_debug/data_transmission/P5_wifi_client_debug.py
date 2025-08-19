#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi Pico 2W WiFi Client for Environmental Monitoring - Debug Version 4.25
Version: 4.25.0-debug

This module provides WiFi connectivity and data transmission functionality for the
Raspberry Pi Pico 2W (P5) environmental monitoring system.

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
                 server_ip="192.168.0.1", server_port=5000, device_id="P5",
                 debug_level=DEBUG_DETAILED, debug_mode=False, connection_timeout=30):
        """Initialize the WiFi client with the given configuration.

        Args:
            ssid (str): WiFi network SSID
            password (str): WiFi network password
            server_ip (str): IP address of the data collection server
            server_port (int): Port of the data collection server
            device_id (str): Device identifier (P5)
            debug_level (int): Level of debug output (0-3)
            debug_mode (bool): Enable or disable debug mode
            connection_timeout (int): Timeout for WiFi connection in seconds
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
        self.connection_timeout = connection_timeout

        # Initialize LED
        self.led.off()

        # Print configuration
        self._debug_print(f"WiFi Client initialized for {device_id} (Debug Version 4.25)", DEBUG_BASIC)
        self._debug_print(f"Server: {server_ip}:{server_port}", DEBUG_BASIC)
        self._debug_print(f"Debug level: {debug_level}", DEBUG_BASIC)
        self._debug_print(f"Debug mode: {debug_mode}", DEBUG_BASIC)
        self._debug_print(f"Connection timeout: {connection_timeout} seconds", DEBUG_BASIC)

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

    def set_auto_reset(self, auto_reset):
        """Set whether to auto-reset on connection failure.

        Args:
            auto_reset (bool): Whether to auto-reset
        """
        self.auto_reset = auto_reset
        self._debug_print(f"Auto-reset set to {auto_reset}", DEBUG_BASIC)

    def activate_wifi(self):
        """Activate the WiFi interface.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self._debug_print("Activating WiFi interface...", DEBUG_BASIC)
            
            # Ensure WiFi is active
            if not self.wlan.active():
                self.wlan.active(True)
                self._debug_print("WiFi interface activated", DEBUG_BASIC)
            else:
                self._debug_print("WiFi interface already active", DEBUG_BASIC)
            
            # Allow time for WiFi to initialize
            time.sleep(1)
            machine.idle()  # Allow background processing
            
            return self.wlan.active()
        except Exception as e:
            self._debug_print(f"Error activating WiFi interface: {e}", DEBUG_BASIC)
            return False

    def deactivate_wifi(self):
        """Deactivate the WiFi interface.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self._debug_print("Deactivating WiFi interface...", DEBUG_BASIC)
            
            # Ensure WiFi is inactive
            if self.wlan.active():
                self.wlan.active(False)
                self._debug_print("WiFi interface deactivated", DEBUG_BASIC)
            else:
                self._debug_print("WiFi interface already inactive", DEBUG_BASIC)
            
            # Allow time for WiFi to deactivate
            time.sleep(1)
            machine.idle()  # Allow background processing
            
            return not self.wlan.active()
        except Exception as e:
            self._debug_print(f"Error deactivating WiFi interface: {e}", DEBUG_BASIC)
            return False

    def scan_networks(self):
        """Scan for available WiFi networks.

        Returns:
            list: List of available networks, or None if scan failed
        """
        try:
            self._debug_print("Scanning for WiFi networks...", DEBUG_BASIC)
            
            # Ensure WiFi is active
            if not self.wlan.active():
                self.wlan.active(True)
                self._debug_print("WiFi interface activated for scan", DEBUG_BASIC)
                time.sleep(1)
                machine.idle()  # Allow background processing
            
            # Scan for networks
            networks = self.wlan.scan()
            
            # Print networks if debug level is high enough
            if self.debug_level >= DEBUG_DETAILED:
                self._debug_print(f"Found {len(networks)} networks:", DEBUG_DETAILED)
                for i, (ssid, bssid, channel, rssi, authmode, hidden) in enumerate(networks):
                    self._debug_print(f"  {i+1}. SSID: {ssid.decode('utf-8')}, Channel: {channel}, RSSI: {rssi} dBm", DEBUG_DETAILED)
            else:
                self._debug_print(f"Found {len(networks)} networks", DEBUG_BASIC)
            
            return networks
        except Exception as e:
            self._debug_print(f"Error scanning for networks: {e}", DEBUG_BASIC)
            return None

    def get_signal_strength(self, ssid=None):
        """Get the signal strength of the specified network.

        Args:
            ssid (str): SSID of the network to check, or None to check the configured SSID

        Returns:
            int: Signal strength in dBm, or None if network not found
        """
        try:
            if ssid is None:
                ssid = self.ssid
            
            self._debug_print(f"Getting signal strength for {ssid}...", DEBUG_DETAILED)
            
            # Scan for networks
            networks = self.scan_networks()
            if networks is None:
                return None
            
            # Find the specified network
            for net_ssid, bssid, channel, rssi, authmode, hidden in networks:
                if net_ssid.decode('utf-8') == ssid:
                    self._debug_print(f"Signal strength for {ssid}: {rssi} dBm", DEBUG_DETAILED)
                    return rssi
            
            self._debug_print(f"Network {ssid} not found", DEBUG_DETAILED)
            return None
        except Exception as e:
            self._debug_print(f"Error getting signal strength: {e}", DEBUG_BASIC)
            return None

    def connect(self):
        """Connect to the configured WiFi network.

        Returns:
            bool: True if connected successfully, False otherwise
        """
        try:
            self._debug_print(f"Connecting to WiFi network: {self.ssid}", DEBUG_BASIC)
            self._debug_print(f"Connection timeout: {self.connection_timeout} seconds", DEBUG_BASIC)
            
            # Ensure WiFi is active
            if not self.activate_wifi():
                self._debug_print("Failed to activate WiFi interface", DEBUG_BASIC)
                return False
            
            # Check if already connected
            if self.wlan.isconnected():
                self._debug_print("Already connected to WiFi", DEBUG_BASIC)
                self.connected = True
                return True
            
            # Connect to network
            self._debug_print("Sending connection request...", DEBUG_DETAILED)
            self.wlan.connect(self.ssid, self.password)
            
            # Wait for connection
            timeout = self.connection_timeout
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
                    
                    # Update connection status
                    self.connected = True
                    self.connection_attempts += 1
                    self.last_connection_time = time.time()
                    
                    # Blink LED to indicate successful connection
                    self.led.on()
                    time.sleep(0.1)
                    self.led.off()
                    
                    return True
                
                # Short sleep with idle to allow background processing
                time.sleep(0.1)
                machine.idle()
                
                # Periodically print status
                if int(time.time() - start_time) % 5 == 0 and self.debug_level >= DEBUG_DETAILED:
                    status = self.wlan.status()
                    status_messages = {
                        network.STAT_IDLE: "Idle",
                        network.STAT_CONNECTING: "Connecting...",
                        network.STAT_WRONG_PASSWORD: "Wrong password",
                        network.STAT_NO_AP_FOUND: "No AP found",
                        network.STAT_CONNECT_FAIL: "Connection failed",
                        network.STAT_GOT_IP: "Connected"
                    }
                    status_message = status_messages.get(status, f"Unknown status: {status}")
                    self._debug_print(f"Connection status: {status_message}", DEBUG_DETAILED)
            
            # Connection timed out
            self._debug_print(f"Connection timed out after {timeout} seconds", DEBUG_BASIC)
            
            # Get status
            status = self.wlan.status()
            status_messages = {
                network.STAT_IDLE: "Idle",
                network.STAT_CONNECTING: "Still connecting",
                network.STAT_WRONG_PASSWORD: "Wrong password",
                network.STAT_NO_AP_FOUND: "No AP found",
                network.STAT_CONNECT_FAIL: "Connection failed",
                network.STAT_GOT_IP: "Connected"
            }
            status_message = status_messages.get(status, f"Unknown status: {status}")
            self._debug_print(f"Final connection status: {status_message}", DEBUG_BASIC)
            
            # Deactivate WiFi to clean up
            self.deactivate_wifi()
            
            return False
        except Exception as e:
            self._debug_print(f"Error connecting to WiFi: {e}", DEBUG_BASIC)
            
            # Deactivate WiFi to clean up
            try:
                self.deactivate_wifi()
            except:
                pass
            
            return False

    def disconnect(self):
        """Disconnect from the WiFi network.

        Returns:
            bool: True if disconnected successfully, False otherwise
        """
        try:
            self._debug_print("Disconnecting from WiFi...", DEBUG_BASIC)
            
            # Check if connected
            if not self.wlan.isconnected():
                self._debug_print("Not connected to WiFi", DEBUG_BASIC)
                self.connected = False
                return True
            
            # Disconnect
            self.wlan.disconnect()
            
            # Wait for disconnection
            timeout = 5
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if not self.wlan.isconnected():
                    self._debug_print("Disconnected from WiFi", DEBUG_BASIC)
                    self.connected = False
                    return True
                
                # Short sleep with idle to allow background processing
                time.sleep(0.1)
                machine.idle()
            
            # Disconnection timed out
            self._debug_print("Disconnection timed out", DEBUG_BASIC)
            
            # Force deactivation
            self.deactivate_wifi()
            self.connected = False
            
            return True
        except Exception as e:
            self._debug_print(f"Error disconnecting from WiFi: {e}", DEBUG_BASIC)
            
            # Force deactivation
            try:
                self.deactivate_wifi()
            except:
                pass
            
            self.connected = False
            
            return False

    def is_connected(self):
        """Check if connected to WiFi.

        Returns:
            bool: True if connected, False otherwise
        """
        try:
            connected = self.wlan.isconnected()
            self.connected = connected
            return connected
        except Exception as e:
            self._debug_print(f"Error checking connection status: {e}", DEBUG_BASIC)
            self.connected = False
            return False

    def get_ip_address(self):
        """Get the IP address.

        Returns:
            str: IP address, or None if not connected
        """
        try:
            if not self.is_connected():
                return None
            
            ip = self.wlan.ifconfig()[0]
            return ip
        except Exception as e:
            self._debug_print(f"Error getting IP address: {e}", DEBUG_BASIC)
            return None

    def get_connection_info(self):
        """Get detailed connection information.

        Returns:
            dict: Connection information, or None if not connected
        """
        try:
            if not self.is_connected():
                return None
            
            ip, subnet, gateway, dns = self.wlan.ifconfig()
            
            info = {
                "ip": ip,
                "subnet": subnet,
                "gateway": gateway,
                "dns": dns,
                "ssid": self.ssid,
                "connected": True,
                "connection_attempts": self.connection_attempts,
                "last_connection_time": self.last_connection_time
            }
            
            return info
        except Exception as e:
            self._debug_print(f"Error getting connection info: {e}", DEBUG_BASIC)
            return None

    def send_data(self, data):
        """Send data to the server.

        Args:
            data (dict): Data to send

        Returns:
            bool: True if data was sent successfully, False otherwise
        """
        try:
            self._debug_print("Sending data to server...", DEBUG_BASIC)
            
            # Check if connected
            if not self.is_connected():
                self._debug_print("Not connected to WiFi, attempting to connect...", DEBUG_BASIC)
                if not self.connect():
                    self._debug_print("Failed to connect to WiFi", DEBUG_BASIC)
                    return False
            
            # Create socket
            self._debug_print(f"Creating socket to {self.server_ip}:{self.server_port}...", DEBUG_DETAILED)
            s = socket.socket()
            
            # Set timeout
            s.settimeout(5)
            
            # Connect to server
            self._debug_print("Connecting to server...", DEBUG_DETAILED)
            s.connect((self.server_ip, self.server_port))
            
            # Convert data to JSON
            json_data = ujson.dumps(data)
            self._debug_print(f"Data: {json_data}", DEBUG_DETAILED)
            
            # Send data
            self._debug_print("Sending data...", DEBUG_DETAILED)
            s.send(json_data.encode())
            
            # Receive response
            self._debug_print("Waiting for response...", DEBUG_DETAILED)
            response = s.recv(1024).decode()
            self._debug_print(f"Response: {response}", DEBUG_DETAILED)
            
            # Close socket
            s.close()
            
            # Check response
            try:
                response_data = ujson.loads(response)
                if response_data.get("status") == "success":
                    self._debug_print("Data sent successfully", DEBUG_BASIC)
                    return True
                else:
                    self._debug_print(f"Server returned error: {response_data.get('message', 'Unknown error')}", DEBUG_BASIC)
                    return False
            except:
                self._debug_print(f"Invalid response from server: {response}", DEBUG_BASIC)
                return False
        except Exception as e:
            self._debug_print(f"Error sending data: {e}", DEBUG_BASIC)
            
            # Close socket if it exists
            try:
                s.close()
            except:
                pass
            
            return False

    def ping_server(self, timeout=1):
        """Ping the server to check connectivity.

        Args:
            timeout (int): Timeout in seconds

        Returns:
            float: Round-trip time in seconds, or None if ping failed
        """
        try:
            self._debug_print(f"Pinging server {self.server_ip}...", DEBUG_BASIC)
            
            # Check if connected
            if not self.is_connected():
                self._debug_print("Not connected to WiFi, attempting to connect...", DEBUG_BASIC)
                if not self.connect():
                    self._debug_print("Failed to connect to WiFi", DEBUG_BASIC)
                    return None
            
            # Create socket
            s = socket.socket()
            
            # Set timeout
            s.settimeout(timeout)
            
            # Start timer
            start_time = time.time()
            
            try:
                # Connect to server
                s.connect((self.server_ip, self.server_port))
                
                # Calculate round-trip time
                rtt = time.time() - start_time
                
                # Close socket
                s.close()
                
                self._debug_print(f"Ping successful, RTT: {rtt:.3f} seconds", DEBUG_BASIC)
                return rtt
            except:
                self._debug_print("Ping failed", DEBUG_BASIC)
                
                # Close socket
                try:
                    s.close()
                except:
                    pass
                
                return None
        except Exception as e:
            self._debug_print(f"Error pinging server: {e}", DEBUG_BASIC)
            return None

    def run_network_diagnostics(self):
        """Run network diagnostics to check connectivity.

        Returns:
            dict: Diagnostic results
        """
        self._debug_print("Running network diagnostics...", DEBUG_BASIC)
        
        results = {}
        
        # Check WiFi interface
        self._debug_print("Checking WiFi interface...", DEBUG_DETAILED)
        wifi_active = self.wlan.active()
        results["wifi_active"] = wifi_active
        self._debug_print(f"WiFi interface active: {wifi_active}", DEBUG_DETAILED)
        
        if not wifi_active:
            self._debug_print("Activating WiFi interface...", DEBUG_DETAILED)
            self.activate_wifi()
            wifi_active = self.wlan.active()
            results["wifi_activated"] = wifi_active
            self._debug_print(f"WiFi interface activated: {wifi_active}", DEBUG_DETAILED)
        
        # Scan for networks
        self._debug_print("Scanning for networks...", DEBUG_DETAILED)
        networks = self.scan_networks()
        results["networks_found"] = len(networks) if networks else 0
        self._debug_print(f"Networks found: {results['networks_found']}", DEBUG_DETAILED)
        
        # Check if target network is available
        target_network_found = False
        target_network_strength = None
        
        if networks:
            for ssid, bssid, channel, rssi, authmode, hidden in networks:
                if ssid.decode('utf-8') == self.ssid:
                    target_network_found = True
                    target_network_strength = rssi
                    break
        
        results["target_network_found"] = target_network_found
        results["target_network_strength"] = target_network_strength
        
        self._debug_print(f"Target network found: {target_network_found}", DEBUG_DETAILED)
        if target_network_found:
            self._debug_print(f"Target network strength: {target_network_strength} dBm", DEBUG_DETAILED)
        
        # Check memory
        gc.collect()
        free_mem = gc.mem_free()
        allocated_mem = gc.mem_alloc()
        total_mem = free_mem + allocated_mem
        mem_percent = (allocated_mem / total_mem) * 100
        
        results["free_memory"] = free_mem
        results["allocated_memory"] = allocated_mem
        results["total_memory"] = total_mem
        results["memory_usage_percent"] = mem_percent
        
        self._debug_print(f"Memory usage: {mem_percent:.1f}% ({allocated_mem}/{total_mem} bytes)", DEBUG_DETAILED)
        
        # Print summary
        self._debug_print("\nDiagnostics Summary:", DEBUG_BASIC)
        self._debug_print(f"WiFi Active: {wifi_active}", DEBUG_BASIC)
        self._debug_print(f"Networks Found: {results['networks_found']}", DEBUG_BASIC)
        self._debug_print(f"Target Network Found: {target_network_found}", DEBUG_BASIC)
        if target_network_found:
            self._debug_print(f"Target Network Strength: {target_network_strength} dBm", DEBUG_BASIC)
        self._debug_print(f"Memory Usage: {mem_percent:.1f}%", DEBUG_BASIC)
        
        return results

    def reset_connection(self):
        """Reset the WiFi connection.

        Returns:
            bool: True if reset was successful, False otherwise
        """
        try:
            self._debug_print("Resetting WiFi connection...", DEBUG_BASIC)
            
            # Disconnect
            self.disconnect()
            
            # Deactivate WiFi
            self.deactivate_wifi()
            
            # Short delay
            time.sleep(1)
            machine.idle()  # Allow background processing
            
            # Activate WiFi
            self.activate_wifi()
            
            # Connect
            return self.connect()
        except Exception as e:
            self._debug_print(f"Error resetting connection: {e}", DEBUG_BASIC)
            return False
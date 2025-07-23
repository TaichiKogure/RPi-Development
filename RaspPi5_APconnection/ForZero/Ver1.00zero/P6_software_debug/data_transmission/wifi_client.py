#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simplified WiFi Client for Raspberry Pi Pico 2W - Debug Version 4.19
Version: 4.19.0-debug

This module provides a simplified interface to the P6_wifi_client_debug module.
It's intended to be imported by main.py on the Pico 2W.
"""

from P6_wifi_client_debug import WiFiClient, DataTransmitter

# These functions are provided for backwards compatibility
def connect_wifi(ssid="RaspberryPi5_AP_Solo", password="raspberry", device_id="P6"):
    """Connect to WiFi network.
    
    Args:
        ssid (str): WiFi network SSID
        password (str): WiFi network password
        device_id (str): Device identifier
        
    Returns:
        WiFiClient: WiFi client object
    """
    client = WiFiClient(ssid=ssid, password=password, device_id=device_id)
    client.connect()
    return client

def send_data(client, data):
    """Send data to server.
    
    Args:
        client (WiFiClient): WiFi client object
        data (dict): Data to send
        
    Returns:
        bool: True if data was sent successfully, False otherwise
    """
    return client.send_data(data)

def disconnect(client):
    """Disconnect from WiFi network.
    
    Args:
        client (WiFiClient): WiFi client object
    """
    client.disconnect()
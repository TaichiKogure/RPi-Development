#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi Pico 2W Main Program - Solo Version
Version: 2.0.0-solo

This is the main program for the Raspberry Pi Pico 2W device (P2)
in the environmental data measurement system (Solo Version). It initializes the BME680 sensor,
establishes WiFi connection, and handles data collection and transmission.

Features:
- BME680 sensor integration for temperature, humidity, pressure, and gas readings
- WiFi connectivity to the Raspberry Pi 5 access point
- Periodic data transmission to the central server
- Error handling and automatic recovery
- LED status indication

Requirements:
- MicroPython for Raspberry Pi Pico W
- BME680 sensor connected as per installation guide
- Raspberry Pi 5 running as an access point

Author: Environmental Data System Team
Date: June 2025
"""

import sys
import time
import machine
from machine import Pin, Timer

# Add module paths
sys.path.append('sensor_drivers')
sys.path.append('data_transmission')
sys.path.append('error_handling')

# Import custom modules
import bme680_driver_solo
import wifi_client_solo
import watchdog_solo

# Configuration
# ============================================================================
# Device configuration
DEVICE_ID = "P2"  # Solo version uses P2

# WiFi configuration
WIFI_SSID = "RaspberryPi5_AP_Solo"
WIFI_PASSWORD = "raspberry"
SERVER_IP = "192.168.0.1"
SERVER_PORT = 5000

# Sensor pins
BME680_SCL_PIN = 1
BME680_SDA_PIN = 0

# Transmission interval (seconds)
TRANSMISSION_INTERVAL = 30

# Status LED
LED_PIN = 25  # Onboard LED on Pico W
# ============================================================================

# Global variables
led = Pin(LED_PIN, Pin.OUT)
wdt = None
client = None
transmitter = None
bme680_sensor = None

def initialize_sensors():
    """Initialize the BME680 sensor."""
    global bme680_sensor

    print("Initializing BME680 sensor...")

    try:
        # Initialize BME680 sensor
        bme680_sensor = bme680_driver_solo.BME680Sensor(
            scl_pin=BME680_SCL_PIN,
            sda_pin=BME680_SDA_PIN
        )
        print("BME680 sensor initialized")

        return True
    except Exception as e:
        print(f"Error initializing BME680 sensor: {e}")
        watchdog_solo.handle_error(e, {"component": "sensor_init"})
        return False

def initialize_wifi():
    """Initialize the WiFi connection."""
    global client, transmitter

    print("Initializing WiFi connection...")

    try:
        # Initialize WiFi client
        client = wifi_client_solo.WiFiClient(
            ssid=WIFI_SSID,
            password=WIFI_PASSWORD,
            server_ip=SERVER_IP,
            server_port=SERVER_PORT,
            device_id=DEVICE_ID
        )

        # Initialize data transmitter
        transmitter = wifi_client_solo.DataTransmitter(
            wifi_client=client,
            transmission_interval=TRANSMISSION_INTERVAL
        )

        # Add sensor to the transmitter
        transmitter.add_sensor("bme680", bme680_sensor)

        # Connect to WiFi
        if client.connect():
            print(f"Connected to {WIFI_SSID}")
            return True
        else:
            print(f"Failed to connect to {WIFI_SSID}")
            return False
    except Exception as e:
        print(f"Error initializing WiFi: {e}")
        watchdog_solo.handle_error(e, {"component": "wifi_init"})
        return False

def collect_and_send_data():
    """Collect data from sensor and send it to the server."""
    global transmitter, wdt

    try:
        # Feed the watchdog
        if wdt:
            wdt.feed()

        # Collect and send data
        success = transmitter.collect_and_send_data()

        # Blink LED to indicate activity
        if success:
            led.on()
            time.sleep(0.1)
            led.off()

        return success
    except Exception as e:
        print(f"Error collecting/sending data: {e}")
        watchdog_solo.handle_error(e, {"component": "data_transmission"})
        return False

def main():
    """Main function."""
    global wdt

    print(f"Starting P2 environmental data collection system (Solo Version)...")
    print(f"Version: 2.0.0-solo")
    print(f"Device ID: {DEVICE_ID}")

    # Initialize watchdog with 8-second timeout
    wdt = watchdog_solo.Watchdog(timeout_ms=8000)

    # Initialize sensors
    if not initialize_sensors():
        print("Failed to initialize BME680 sensor. Restarting...")
        time.sleep(5)
        machine.reset()

    # Initialize WiFi
    if not initialize_wifi():
        print("Failed to initialize WiFi. Restarting...")
        time.sleep(5)
        machine.reset()

    print("Starting data transmission...")

    # Main loop
    while True:
        try:
            # Feed the watchdog
            wdt.feed()

            # Collect and send data
            collect_and_send_data()

            # Sleep for a short time (main loop runs more frequently than transmission)
            time.sleep(1)
        except KeyboardInterrupt:
            print("Program stopped by user")
            break
        except Exception as e:
            print(f"Unexpected error in main loop: {e}")
            watchdog_solo.handle_error(e, {"component": "main_loop"})
            time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Critical error: {e}")
        watchdog_solo.handle_error(e, {"component": "main"})
        # The watchdog will reset the device if it's not fed
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi Pico 2W Main Program - Solo Version 3.0.1
Version: 3.0.1-solo

Modifications:
- Avoid infinite reboot on WiFi connection failure
- Add stable fallback for sensor and WiFi init errors

Author: Environmental Data System Team (Modified)
Date: June 2025
"""

import sys
import time
import machine
from machine import Pin, I2C, Timer

# Add module paths
sys.path.append('sensor_drivers')
sys.path.append('data_transmission')
sys.path.append('error_handling')

# Import custom modules
from bme680 import BME680_I2C
import wifi_client_solo
import watchdog_solo

# Configuration
DEVICE_ID = "P2"
WIFI_SSID = "RaspberryPi5_AP_Solo"
WIFI_PASSWORD = "raspberry"
SERVER_IP = "192.168.0.1"
SERVER_PORT = 5000
BME680_SCL_PIN = 1
BME680_SDA_PIN = 0
TRANSMISSION_INTERVAL = 30
LED_PIN = 25

# Globals
led = Pin(LED_PIN, Pin.OUT)
wdt = None
client = None
transmitter = None
bme680_sensor = None

def initialize_sensors():
    global bme680_sensor

    print("Initializing BME680 sensor...")

    try:
        i2c = I2C(0, scl=Pin(BME680_SCL_PIN), sda=Pin(BME680_SDA_PIN), freq=100000)
        bme680_sensor = BME680_I2C(i2c, address=0x77)

        # Enable gas measurement
        ctrl_gas = bme680_sensor._read_byte(0x71)
        ctrl_gas |= 0x10
        bme680_sensor._write(0x71, [ctrl_gas])

        print("BME680 sensor initialized")

        # Test readings
        temp = bme680_sensor.temperature
        hum = bme680_sensor.humidity
        pres = bme680_sensor.pressure
        gas = bme680_sensor.gas

        print(f"Test readings - Temp: {temp:.2f}°C, Humidity: {hum:.2f}%, Pressure: {pres:.2f}hPa, Gas: {gas} ohms")
        return True

    except Exception as e:
        print(f"Error initializing BME680 sensor: {e}")
        watchdog_solo.handle_error(e, {"component": "sensor_init"})
        return False

def initialize_wifi():
    global client, transmitter

    print("Initializing WiFi connection...")

    try:
        client = wifi_client_solo.WiFiClient(
            ssid=WIFI_SSID,
            password=WIFI_PASSWORD,
            server_ip=SERVER_IP,
            server_port=SERVER_PORT,
            device_id=DEVICE_ID
        )

        transmitter = wifi_client_solo.DataTransmitter(
            wifi_client=client,
            transmission_interval=TRANSMISSION_INTERVAL
        )
        transmitter.add_sensor("bme680", bme680_sensor)

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
    global transmitter, wdt

    try:
        if wdt:
            wdt.feed()

        success = transmitter.collect_and_send_data()

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
    global wdt

    print(f"Starting P2 environmental data collection system (Solo Version 3.0.1)...")
    print(f"Device ID: {DEVICE_ID}")

    wdt = watchdog_solo.Watchdog(timeout_ms=8000)

    # Sensor init
    if not initialize_sensors():
        print("Failed to initialize BME680 sensor. Halting.")
        while True:
            time.sleep(1)  # Stop instead of reset

    # WiFi init
    if not initialize_wifi():
        print("Failed to initialize WiFi. Halting.")
        print("Check if AP is online and SSID is correct.")
        while True:
            time.sleep(1)

    print("Initialization complete. Starting data transmission loop...")

    while True:
        try:
            wdt.feed()
            collect_and_send_data()
            time.sleep(1)
        except KeyboardInterrupt:
            print("Stopped by user.")
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

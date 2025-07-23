#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi Pico 2W Main Program for Environmental Monitoring - Solo Version 3.5
Version: 3.5.0-solo

This is the main program for the Raspberry Pi Pico 2W (P2) that collects data from
BME680 and MH-Z19C sensors and sends it to the Raspberry Pi 5 (P1) server.

Features:
- BME680 sensor for temperature, humidity, pressure, and gas resistance
- MH-Z19C sensor for CO2 concentration
- WiFi connectivity to P1 server
- Error handling and automatic restart
- LED status indicators
- 30-second warm-up period for MH-Z19C sensor

Pin connections:
BME680:
- VCC -> 3.3V (Pin 36)
- GND -> GND (Pin 38)
- SCL -> GP1 (Pin 2)
- SDA -> GP0 (Pin 1)

MH-Z19C:
- VCC (red) -> VBUS (5V, Pin 40)
- GND (black) -> GND (Pin 38)
- TX (green) -> GP9 (Pin 12)
- RX (blue) -> GP8 (Pin 11)

Usage:
    This file should be saved as main.py on the Pico 2W for automatic execution on boot.
"""

import time
import machine
import sys
import gc
from machine import Pin, I2C, UART

# Add sensor_drivers and other directories to path
sys.path.append('sensor_drivers')
sys.path.append('data_transmission')
sys.path.append('error_handling')

# Import sensor drivers
from bme680 import BME680_I2C
from mhz19c import MHZ19C

# Import data transmission module
from P2_wifi_client_solo import WiFiClient, DataTransmitter

# Import error handling module
from P2_watchdog_solo import Watchdog, handle_error

# Status LED
LED_PIN = 25  # Onboard LED on Pico W
led = Pin(LED_PIN, Pin.OUT)

# Configuration
WIFI_SSID = "RaspberryPi5_AP_Solo"
WIFI_PASSWORD = "raspberry"
SERVER_IP = "192.168.0.1"
SERVER_PORT = 5000
DEVICE_ID = "P2"
TRANSMISSION_INTERVAL = 30  # seconds

def blink_led(count=1, duration=0.2):
    """Blink the LED to indicate activity."""
    for _ in range(count):
        led.on()
        time.sleep(duration)
        led.off()
        time.sleep(duration)

def setup():
    """Initialize sensors and WiFi."""
    try:
        print("\n=== Raspberry Pi Pico 2W Environmental Monitor Ver3.5 ===")
        print("Initializing...")
        
        # Initial LED blink to show we're starting
        blink_led(3, 0.1)
        
        # Initialize I2C for BME680
        print("Initializing I2C for BME680...")
        i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=100000)
        
        # Scan I2C bus
        devices = i2c.scan()
        if devices:
            print(f"I2C devices found: {[hex(device) for device in devices]}")
        else:
            print("No I2C devices found!")
        
        # Initialize BME680 sensor
        print("Initializing BME680 sensor...")
        bme = BME680_I2C(i2c, address=0x77)
        
        # Initialize MH-Z19C CO2 sensor
        print("Initializing MH-Z19C CO2 sensor...")
        co2_sensor = MHZ19C(uart_id=1, tx_pin=8, rx_pin=9)
        
        # Initialize WiFi client
        print("Initializing WiFi client...")
        client = WiFiClient(
            ssid=WIFI_SSID,
            password=WIFI_PASSWORD,
            server_ip=SERVER_IP,
            server_port=SERVER_PORT,
            device_id=DEVICE_ID
        )
        
        # Initialize data transmitter
        print("Initializing data transmitter...")
        transmitter = DataTransmitter(client, transmission_interval=TRANSMISSION_INTERVAL)
        transmitter.add_sensor("bme680", bme)
        transmitter.add_sensor("mhz19c", co2_sensor)
        
        # Initialize watchdog
        print("Initializing watchdog...")
        watchdog = Watchdog(timeout_ms=8000)
        
        print("Initialization complete!")
        return bme, co2_sensor, client, transmitter, watchdog
    
    except Exception as e:
        print(f"Error during setup: {e}")
        handle_error(e, {"phase": "setup"})
        # If we can't set up, wait a bit and reset
        time.sleep(5)
        machine.reset()

def main():
    """Main function."""
    try:
        # Set up components
        bme, co2_sensor, client, transmitter, watchdog = setup()
        
        # Connect to WiFi
        print("Connecting to WiFi...")
        if not client.connect():
            print("Failed to connect to WiFi, resetting...")
            time.sleep(5)
            machine.reset()
        
        print("Connected to WiFi!")
        
        # Wait for MH-Z19C warm-up (30 seconds)
        print(f"Waiting for MH-Z19C warm-up ({co2_sensor.warmup_time} seconds)...")
        
        # Blink LED during warm-up
        start_time = time.time()
        while time.time() - start_time < co2_sensor.warmup_time:
            blink_led(1, 0.1)
            time.sleep(1)
            watchdog.feed()
        
        print("MH-Z19C warm-up complete!")
        
        # Main loop
        print("Starting main loop...")
        while True:
            try:
                # Feed the watchdog
                watchdog.feed()
                
                # Collect and send data
                success = transmitter.collect_and_send_data()
                
                # Blink LED to indicate status
                if success:
                    blink_led(1, 0.1)  # Single blink for success
                else:
                    blink_led(2, 0.1)  # Double blink for failure
                
                # Perform garbage collection
                gc.collect()
                
                # Sleep for a short time
                time.sleep(1)
            
            except Exception as e:
                print(f"Error in main loop: {e}")
                handle_error(e, {"phase": "main_loop"})
                # Continue running, don't reset immediately
    
    except KeyboardInterrupt:
        print("Program stopped by user")
    
    except Exception as e:
        print(f"Unhandled error: {e}")
        handle_error(e, {"phase": "unhandled"})
        # Wait a bit before resetting
        time.sleep(5)
        machine.reset()

if __name__ == "__main__":
    # Wait a bit before starting to ensure all hardware is initialized
    time.sleep(5)
    
    # Start the main program
    main()
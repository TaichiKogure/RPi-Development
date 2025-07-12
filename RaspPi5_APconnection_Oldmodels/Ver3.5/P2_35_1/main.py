#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi Pico 2W Main Program for Environmental Monitoring - Solo Version 3.5.1
Version: 3.5.1-solo

This is the main program for the Raspberry Pi Pico 2W (P2) that collects data from
BME680 and MH-Z19C sensors and sends it to the Raspberry Pi 5 (P1) server.

Features:
- BME680 sensor for temperature, humidity, pressure, and gas resistance
- MH-Z19C sensor for CO2 concentration
- WiFi connectivity to P1 server
- Error handling and automatic restart
- LED status indicators
- 30-second warm-up period for MH-Z19C sensor
- Improved WiFi connection handling
- Graceful error recovery

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
from P2_watchdog_solo import Watchdog, handle_error, sync_all_files

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
WIFI_CONNECTION_TIMEOUT = 30  # seconds (increased from 10)
MAX_WIFI_RETRIES = 3  # Maximum number of WiFi connection attempts before reset
RESET_DELAY = 15  # seconds to wait before reset (increased from 5)

def blink_led(count=1, duration=0.2):
    """Blink the LED to indicate activity."""
    for _ in range(count):
        led.on()
        time.sleep(duration)
        led.off()
        time.sleep(duration)

def safe_reset(delay=RESET_DELAY, reason="Unknown"):
    """Safely reset the device after ensuring logs are saved."""
    print(f"Preparing for safe reset in {delay} seconds. Reason: {reason}")
    
    # Blink LED rapidly to indicate imminent reset
    for _ in range(5):
        led.on()
        time.sleep(0.1)
        led.off()
        time.sleep(0.1)
    
    # Ensure all logs and data are saved
    print("Syncing files before reset...")
    sync_all_files()
    
    # Wait for the specified delay to ensure all operations complete
    # and to give Thonny a chance to receive all output
    print(f"Waiting {delay} seconds before reset...")
    for i in range(delay):
        if i % 5 == 0:  # Print status every 5 seconds
            print(f"{delay - i} seconds until reset...")
        time.sleep(1)
        # Blink LED slowly during wait
        if i % 2 == 0:
            led.on()
        else:
            led.off()
    
    # Final message before reset
    print("Performing reset now!")
    led.on()  # LED on for reset
    time.sleep(1)
    
    # Reset the device
    machine.reset()

def setup():
    """Initialize sensors and WiFi."""
    try:
        print("\n=== Raspberry Pi Pico 2W Environmental Monitor Ver3.5.1 ===")
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
        # If we can't set up, wait and reset safely
        safe_reset(reason=f"Setup error: {str(e)}")
        # This line will never be reached due to reset
        return None

def connect_wifi(client, watchdog, max_retries=MAX_WIFI_RETRIES):
    """Connect to WiFi with improved error handling."""
    print("Connecting to WiFi...")
    
    # Set longer connection timeout
    retry_count = 0
    while retry_count < max_retries:
        try:
            # Attempt to connect with increased timeout
            if client.connect(max_retries=1, retry_delay=1, connection_timeout=WIFI_CONNECTION_TIMEOUT):
                print("Connected to WiFi!")
                return True
            
            # If connection failed but didn't raise an exception
            retry_count += 1
            print(f"WiFi connection attempt {retry_count}/{max_retries} failed.")
            
            if retry_count < max_retries:
                # Wait before next attempt, feed watchdog during wait
                wait_time = 10  # seconds
                print(f"Waiting {wait_time} seconds before next attempt...")
                for _ in range(wait_time):
                    watchdog.feed()
                    time.sleep(1)
        
        except Exception as e:
            retry_count += 1
            print(f"WiFi connection error: {e}")
            handle_error(e, {"phase": "wifi_connection", "attempt": retry_count})
            
            if retry_count < max_retries:
                # Wait before next attempt, feed watchdog during wait
                wait_time = 10  # seconds
                print(f"Waiting {wait_time} seconds before next attempt...")
                for _ in range(wait_time):
                    watchdog.feed()
                    time.sleep(1)
    
    # If we've exhausted all retries
    print(f"Failed to connect to WiFi after {max_retries} attempts.")
    return False

def main():
    """Main function."""
    try:
        # Set up components
        components = setup()
        if not components:
            return  # Setup failed and reset was triggered
        
        bme, co2_sensor, client, transmitter, watchdog = components
        
        # Connect to WiFi with improved error handling
        if not connect_wifi(client, watchdog):
            print("WiFi connection failed after all attempts.")
            # Log the error and reset safely
            handle_error(Exception("WiFi connection failed"), {"phase": "wifi_connection"})
            safe_reset(reason="WiFi connection failure")
            return
        
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
        connection_failures = 0
        max_connection_failures = 3
        
        while True:
            try:
                # Feed the watchdog
                watchdog.feed()
                
                # Check WiFi connection and reconnect if needed
                if not client.is_connected():
                    print("WiFi connection lost. Attempting to reconnect...")
                    if not connect_wifi(client, watchdog, max_retries=2):
                        connection_failures += 1
                        print(f"Reconnection failed. Failure count: {connection_failures}/{max_connection_failures}")
                        
                        if connection_failures >= max_connection_failures:
                            print("Too many connection failures. Resetting device...")
                            safe_reset(reason="Repeated WiFi connection failures")
                            return
                        
                        # Wait before continuing the loop
                        time.sleep(5)
                        continue
                    else:
                        # Reset failure counter on successful reconnection
                        connection_failures = 0
                
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
                time.sleep(2)  # Short delay before continuing
    
    except KeyboardInterrupt:
        print("Program stopped by user")
    
    except Exception as e:
        print(f"Unhandled error: {e}")
        handle_error(e, {"phase": "unhandled"})
        # Wait and reset safely
        safe_reset(reason=f"Unhandled error: {str(e)}")

if __name__ == "__main__":
    # Wait a bit before starting to ensure all hardware is initialized
    print("Starting in 5 seconds...")
    time.sleep(5)
    
    # Start the main program
    main()
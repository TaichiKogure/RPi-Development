#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi Pico 2W Main Program for Environmental Monitoring - Solo Version 4.44
Version: 4.44.0-solo

This is the main program for the Raspberry Pi Pico 2W (P3) that collects environmental data
and sends it to the Raspberry Pi 5 (P1) server.

Features:
- BME680 sensor for temperature, humidity, pressure, and gas resistance
- MH-Z19C sensor for CO2 concentration
- WiFi connectivity to P1 server with improved error handling
- Error handling with logging
- LED status indicators
- Automatic restart on errors

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

# ===== DEVICE CONFIGURATION =====
DEVICE_ID = "P3"                     # Device identifier (changed from P2 to P3)
WIFI_SSID = "RaspberryPi5_AP_Solo"   # WiFi network SSID
WIFI_PASSWORD = "raspberry"          # WiFi network password
SERVER_IP = "192.168.0.1"            # Server IP address
SERVER_PORT = 5000                   # Server port
TRANSMISSION_INTERVAL = 30           # Data transmission interval in seconds

# ===== PIN CONFIGURATION =====
LED_PIN = "LED"                      # Onboard LED
I2C_SDA_PIN = 0                      # I2C SDA pin for BME680
I2C_SCL_PIN = 1                      # I2C SCL pin for BME680
UART_TX_PIN = 8                      # UART TX pin for MH-Z19C
UART_RX_PIN = 9                      # UART RX pin for MH-Z19C

# ===== ERROR HANDLING =====
ERROR_LOG_FILE = "/error_log_p3_solo44.txt"  # Error log file path (changed from P2 to P3)

# Initialize LED
led = Pin(LED_PIN, Pin.OUT)

# ===== HELPER FUNCTIONS =====
def blink_led(count=1, duration=0.2):
    """Blink the LED."""
    for _ in range(count):
        led.on()
        time.sleep(duration)
        led.off()
        time.sleep(duration)

def safe_reset(reason="Unknown", delay=3):
    """Safely reset the device after logging the reason and waiting for a delay."""
    print(f"SYSTEM RESET TRIGGERED: {reason}")
    print(f"Resetting in {delay} seconds...")

    # Log the reset reason
    try:
        with open(ERROR_LOG_FILE, "a") as f:
            f.write(f"SYSTEM RESET TRIGGERED: {reason}\n")
            f.write(f"Resetting in {delay} seconds...\n")
    except:
        pass

    # Sync all files to prevent data corruption
    try:
        import os
        os.sync()
    except:
        pass

    # Blink rapidly to indicate reset
    for _ in range(delay * 5):  # 5 blinks per second
        led.on()
        time.sleep(0.1)
        led.off()
        time.sleep(0.1)

    # Final message before reset
    print("RESETTING NOW")

    # Reset the device
    machine.reset()

# ===== INITIALIZATION =====
def initialize():
    """Initialize all components and return them if successful."""
    try:
        # Initialize error logging
        try:
            with open(ERROR_LOG_FILE, "w") as f:
                f.write(f"Error log file initialized: {ERROR_LOG_FILE}\n")
            print(f"Error log file initialized: {ERROR_LOG_FILE}")
        except Exception as e:
            print(f"Warning: Could not initialize error log file: {e}")

        # Startup delay to allow for stable initialization
        print("Starting in 10 seconds...")
        for i in range(10, 0, -1):
            if i == 10 or i == 5 or i <= 3:
                print(f"{i} seconds until start...")
            time.sleep(1)
            # Allow background processing during delay
            machine.idle()
        print()

        # Print header
        print(f"=== Raspberry Pi Pico 2W Environmental Monitor Ver4.44 ({DEVICE_ID}) ===")
        print("Initializing...")

        # Initialize I2C for BME680
        print("Initializing I2C for BME680...")
        try:
            i2c = I2C(0, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=100000)
            devices = [hex(addr) for addr in i2c.scan()]
            print(f"I2C devices found: {devices}")
        except Exception as e:
            print(f"Error initializing I2C: {e}")
            safe_reset(reason=f"I2C initialization error: {str(e)}")
            return None

        # Initialize BME680 sensor
        print("Initializing BME680 sensor...")
        try:
            from bme680 import BME680_I2C
            # Try to auto-detect the correct I2C address
            bme = BME680_I2C(i2c, address=None)  # Auto-detect address
            print("BME680 initialization complete")
        except Exception as e:
            print(f"Error initializing BME680: {e}")
            # Try specific addresses as fallback
            try:
                print("Auto-detection failed. Trying address 0x77...")
                bme = BME680_I2C(i2c, address=0x77)
                print("BME680 initialized with address 0x77")
            except Exception as e1:
                print(f"Failed with address 0x77: {e1}")
                try:
                    print("Trying address 0x76...")
                    bme = BME680_I2C(i2c, address=0x76)
                    print("BME680 initialized with address 0x76")
                except Exception as e2:
                    print(f"Failed with address 0x76: {e2}")
                    safe_reset(reason=f"BME680 initialization error: {str(e)}")
                    return None

        # Initialize MH-Z19C CO2 sensor
        print("Initializing MH-Z19C CO2 sensor...")
        try:
            from mhz19c import MHZ19C
            co2_sensor = MHZ19C(uart_id=1, tx_pin=UART_TX_PIN, rx_pin=UART_RX_PIN)
            print(f"MH-Z19C initialized on UART1 (TX: GP{UART_TX_PIN}, RX: GP{UART_RX_PIN})")

            # Warm up the CO2 sensor
            print("Warming up for 30 seconds...")
            for i in range(30):
                if i % 5 == 0 or i == 29:
                    print(f"Warmup: {i+1}/30 seconds")
                time.sleep(1)
                # Allow background processing during warmup
                machine.idle()
        except Exception as e:
            print(f"Error initializing MH-Z19C: {e}")
            safe_reset(reason=f"MH-Z19C initialization error: {str(e)}")
            return None

        # Initialize WiFi client
        print("Initializing WiFi client...")
        try:
            from P3_wifi_client_solo44 import WiFiClient  # Changed from P2 to P3
            client = WiFiClient(
                ssid=WIFI_SSID,
                password=WIFI_PASSWORD,
                server_ip=SERVER_IP,
                server_port=SERVER_PORT,
                device_id=DEVICE_ID
            )
            print("WiFi client initialized")
        except Exception as e:
            print(f"Error initializing WiFi client: {e}")
            safe_reset(reason=f"WiFi client initialization error: {str(e)}")
            return None

        # Initialize data transmitter if WiFi client is available
        if client:
            print("Initializing data transmitter...")
            try:
                from P3_wifi_client_solo44 import DataTransmitter  # Changed from P2 to P3
                transmitter = DataTransmitter(client, transmission_interval=TRANSMISSION_INTERVAL)
                if bme:
                    transmitter.add_sensor("bme680", bme)
                if co2_sensor:
                    transmitter.add_sensor("mhz19c", co2_sensor)
                print("Data transmitter initialized")
            except Exception as e:
                print(f"Error initializing data transmitter: {e}")
                safe_reset(reason=f"Data transmitter initialization error: {str(e)}")
                return None
        else:
            transmitter = None

        # Initialize watchdog
        print("Initializing watchdog...")
        try:
            from P3_watchdog_solo44 import Watchdog, handle_error  # Changed from P2 to P3
            watchdog = Watchdog(timeout_ms=8000)
            print("Watchdog initialized with 8000ms timeout")
        except Exception as e:
            print(f"Error initializing watchdog: {e}")
            watchdog = None
            # Define fallback error handler if watchdog module is not available
            def handle_error(e, context=None):
                print(f"Error: {e}, Context: {context}")

        print("Initialization complete!")
        return bme, co2_sensor, client, transmitter, watchdog

    except Exception as e:
        print(f"Error during setup: {e}")
        try:
            handle_error(e, {"phase": "setup"})
        except:
            print(f"Could not handle error: {e}")

        # If we can't set up, wait and reset safely
        safe_reset(reason=f"Setup error: {str(e)}")
        # This line will never be reached
        return None

# ===== WIFI CONNECTION FUNCTION =====
def connect_wifi(client, watchdog=None, max_retries=5):
    """Connect to WiFi with improved error handling."""
    if not client:
        print("WiFi client not initialized. Skipping connection.")
        return False

    print("Connecting to WiFi...")
    print(f"SSID: {client.ssid}, Device ID: {client.device_id}")
    print(f"Maximum retries: {max_retries}")

    # Try to connect
    connected = client.connect(max_retries=max_retries)
    
    if connected:
        print(f"Successfully connected to {client.ssid}")
        return True
    else:
        print(f"Failed to connect to {client.ssid}")
        safe_reset(reason="WiFi connection failure")
        return False

# ===== MAIN LOOP =====
def main_loop(bme, co2_sensor, client, transmitter, watchdog):
    """Main program loop."""
    print("Starting main loop...")

    # Connect to WiFi if client is available
    if client:
        connected = connect_wifi(client, watchdog)
        if not connected:
            print("WiFi connection failed. Resetting...")
            safe_reset(reason="WiFi connection failure")

    # Main loop
    last_feed_time = time.time()
    last_print_time = time.time()

    try:
        while True:
            try:
                # Feed watchdog if enabled
                if watchdog:
                    watchdog.feed()
                    last_feed_time = time.time()

                # Transmit data if transmitter is available and connected
                if transmitter and client and client.is_connected():
                    transmitter.collect_and_send_data()

                # Print sensor readings if available (every 10 seconds)
                current_time = time.time()
                if bme and current_time - last_print_time > 10:
                    # Get readings
                    try:
                        bme_readings = bme.get_readings()
                        print(f"Temperature: {bme_readings['temperature']:.1f}°C, Humidity: {bme_readings['humidity']:.1f}%, "
                              f"Pressure: {bme_readings['pressure']:.1f}hPa, Gas: {bme_readings['gas_resistance']:.0f}Ω")
                    except Exception as e:
                        print(f"Error getting BME680 readings: {e}")

                    if co2_sensor:
                        try:
                            co2 = co2_sensor.read_co2()
                            print(f"CO2: {co2}ppm")
                        except Exception as e:
                            print(f"Error reading CO2 sensor: {e}")

                    last_print_time = current_time

                # Sleep with machine.idle() to allow background processing
                machine.idle()
                time.sleep(0.1)

            except Exception as e:
                print(f"Error in main loop: {e}")
                try:
                    handle_error(e, {"phase": "main_loop"})
                except:
                    print(f"Could not handle error: {e}")

                # Reset after error
                safe_reset(reason=f"Main loop error: {str(e)}")

    except KeyboardInterrupt:
        print("Program stopped by user")
        if client:
            client.disconnect()
        return

# ===== MAIN PROGRAM =====
if __name__ == "__main__":
    try:
        # Initialize components
        bme, co2_sensor, client, transmitter, watchdog = initialize()

        # Run main loop
        main_loop(bme, co2_sensor, client, transmitter, watchdog)

    except Exception as e:
        print(f"Fatal error: {e}")
        safe_reset(reason=f"Fatal error: {str(e)}")
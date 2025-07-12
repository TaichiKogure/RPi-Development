#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi Pico 2W Main Program for Environmental Monitoring - Debug Version 4.15
Version: 4.15.0-debug

This is a debug version of the main program for the Raspberry Pi Pico 2W (P3) that helps
identify where errors occur during initialization, sensor connection, and WiFi connection.

Features:
- Enhanced debugging options for troubleshooting
- Configurable automatic reset behavior
- Multiple WiFi connection modes for testing
- Detailed status reporting throughout the process
- BME680 sensor for temperature, humidity, pressure, and gas resistance
- MH-Z19C sensor for CO2 concentration
- WiFi connectivity to P1 server
- Error handling with improved logging
- LED status indicators

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
    Adjust the DEBUG_* settings below to configure the debugging behavior.
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

# ===== DEBUG CONFIGURATION =====
# Set these values to control debugging behavior
DEBUG_ENABLE = True                  # Master switch for debug mode
DEBUG_DISABLE_AUTO_RESET = True      # Disable automatic reset on errors
DEBUG_DISABLE_WATCHDOG = False       # Disable hardware watchdog (use with caution)
DEBUG_WIFI_MODE = 2                  # WiFi connection mode (1-4, see below)
DEBUG_WIFI_TIMEOUT = 30              # WiFi connection timeout in seconds
DEBUG_WIFI_MAX_RETRIES = 5           # Maximum WiFi connection retries
DEBUG_DETAILED_LOGGING = True        # Enable detailed logging
DEBUG_STARTUP_DELAY = 5             # Startup delay in seconds
DEBUG_SENSOR_WARMUP = 3             # Sensor warmup time in seconds
DEBUG_RESET_DELAY = 3               # Delay before reset in seconds
DEBUG_THONNY_MODE = True             # Special mode for Thonny development

# WiFi connection modes:
# 1: Normal connection with automatic reset disabled
# 2: Connection with extended timeout and detailed status reporting
# 3: Connection with network reset before each attempt
# 4: Connection with progressive backoff and multiple retries

# ===== STANDARD CONFIGURATION =====
# Status LED
LED_PIN = 25  # Onboard LED on Pico W
led = Pin(LED_PIN, Pin.OUT)

# Configuration
WIFI_SSID = "RaspberryPi5_AP_Solo"
WIFI_PASSWORD = "raspberry"
SERVER_IP = "192.168.0.1"
SERVER_PORT = 5000
DEVICE_ID = "P3"
TRANSMISSION_INTERVAL = 30  # seconds

# ===== HELPER FUNCTIONS =====
def debug_print(message, level=1):
    """Print debug messages if debug is enabled.

    Args:
        message (str): Message to print
        level (int): Debug level (1-3, higher means more verbose)
    """
    if DEBUG_ENABLE and (level <= 3 or DEBUG_DETAILED_LOGGING):
        print(f"[DEBUG] {message}")

def blink_led(count=1, duration=0.2):
    """Blink the LED to indicate activity."""
    for _ in range(count):
        led.on()
        time.sleep(duration)
        led.off()
        time.sleep(duration)

def safe_reset(delay=DEBUG_RESET_DELAY, reason="Unknown"):
    """Safely reset the device after ensuring logs are saved."""
    print(f"Preparing for safe reset in {delay} seconds. Reason: {reason}")

    # Special handling for Thonny mode
    if DEBUG_THONNY_MODE:
        print("\n===== RESET REQUEST IN THONNY MODE =====")
        print(f"Reset requested. Reason: {reason}")
        print("In Thonny mode, automatic resets are converted to manual resets")
        print("to prevent USB disconnection loops.")
        print("Options:")
        print("1. Continue running (may have limited functionality)")
        print("2. Manually stop and restart the program")
        print("3. Press Ctrl+C to stop the program now")
        print("==========================================\n")

        print("Program will continue running without reset.")
        print("開発中のため自動リセットを停止中。手動で再起動してください。")

        # Return without resetting
        return

    # For non-Thonny mode, proceed with normal reset
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
        if i % 5 == 0 or i <= 3:  # Print status every 5 seconds and final 3 seconds
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

# ===== SETUP FUNCTION =====
def setup():
    """Initialize sensors and WiFi."""
    try:
        print("\n=== Raspberry Pi Pico 2W Environmental Monitor Ver4.15 DEBUG (P3) ===")
        print("Initializing...")

        if DEBUG_ENABLE:
            print("\n----- DEBUG CONFIGURATION -----")
            print(f"Auto Reset: {'Disabled' if DEBUG_DISABLE_AUTO_RESET else 'Enabled'}")
            print(f"Watchdog: {'Disabled' if DEBUG_DISABLE_WATCHDOG else 'Enabled'}")
            print(f"WiFi Mode: {DEBUG_WIFI_MODE}")
            print(f"WiFi Timeout: {DEBUG_WIFI_TIMEOUT} seconds")
            print(f"WiFi Max Retries: {DEBUG_WIFI_MAX_RETRIES}")
            print(f"Detailed Logging: {'Enabled' if DEBUG_DETAILED_LOGGING else 'Disabled'}")
            print("-----------------------------\n")

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
            # Wait and try again before giving up
            print("Waiting 2 seconds and trying again...")
            time.sleep(2)
            devices = i2c.scan()
            if devices:
                print(f"I2C devices found on second attempt: {[hex(device) for device in devices]}")
            else:
                print("Still no I2C devices found. Check connections.")

        # Initialize BME680 sensor
        print("Initializing BME680 sensor...")
        try:
            from bme680 import BME680_I2C
            bme = BME680_I2C(i2c, address=0x77)
            debug_print("BME680 initialization successful", 1)
        except Exception as e:
            print(f"Error initializing BME680: {e}")
            if not DEBUG_DISABLE_AUTO_RESET:
                safe_reset(reason=f"BME680 initialization error: {str(e)}")
            else:
                print("Auto-reset disabled. Continuing without BME680...")
                bme = None

        # Initialize MH-Z19C CO2 sensor
        print("Initializing MH-Z19C CO2 sensor...")
        try:
            from mhz19c import MHZ19C
            co2_sensor = MHZ19C(uart_id=1, tx_pin=8, rx_pin=9)
            debug_print("MH-Z19C initialization successful", 1)
        except Exception as e:
            print(f"Error initializing MH-Z19C: {e}")
            if not DEBUG_DISABLE_AUTO_RESET:
                safe_reset(reason=f"MH-Z19C initialization error: {str(e)}")
            else:
                print("Auto-reset disabled. Continuing without MH-Z19C...")
                co2_sensor = None

        # Initialize WiFi client
        print("Initializing WiFi client...")
        try:
            from P3_wifi_client_debug import WiFiClient, DataTransmitter
            client = WiFiClient(
                ssid=WIFI_SSID,
                password=WIFI_PASSWORD,
                server_ip=SERVER_IP,
                server_port=SERVER_PORT,
                device_id=DEVICE_ID,
                debug_mode=DEBUG_ENABLE,
                debug_level=3 if DEBUG_DETAILED_LOGGING else 1
            )
            debug_print("WiFi client initialization successful", 1)
        except Exception as e:
            print(f"Error initializing WiFi client: {e}")
            if not DEBUG_DISABLE_AUTO_RESET:
                safe_reset(reason=f"WiFi client initialization error: {str(e)}")
            else:
                print("Auto-reset disabled. Continuing without WiFi client...")
                client = None

        # Initialize data transmitter if WiFi client is available
        if client:
            print("Initializing data transmitter...")
            try:
                transmitter = DataTransmitter(client, transmission_interval=TRANSMISSION_INTERVAL)
                if bme:
                    transmitter.add_sensor("bme680", bme)
                if co2_sensor:
                    transmitter.add_sensor("mhz19c", co2_sensor)
                debug_print("Data transmitter initialization successful", 1)
            except Exception as e:
                print(f"Error initializing data transmitter: {e}")
                if not DEBUG_DISABLE_AUTO_RESET:
                    safe_reset(reason=f"Data transmitter initialization error: {str(e)}")
                else:
                    print("Auto-reset disabled. Continuing without data transmitter...")
                    transmitter = None
        else:
            transmitter = None

        # Initialize watchdog if not disabled
        if not DEBUG_DISABLE_WATCHDOG:
            print("Initializing watchdog...")
            try:
                from P3_watchdog_debug import Watchdog, handle_error, sync_all_files
                watchdog = Watchdog(timeout_ms=8000)
                debug_print("Watchdog initialization successful", 1)
            except Exception as e:
                print(f"Error initializing watchdog: {e}")
                watchdog = None
        else:
            print("Watchdog disabled in debug mode")
            from P3_watchdog_debug import handle_error, sync_all_files
            watchdog = None

        print("Initialization complete!")
        return bme, co2_sensor, client, transmitter, watchdog

    except Exception as e:
        print(f"Error during setup: {e}")
        handle_error(e, {"phase": "setup"})

        # If auto-reset is disabled, continue with partial initialization
        if DEBUG_DISABLE_AUTO_RESET:
            print("Auto-reset disabled. Continuing with partial initialization...")
            print("開発中のため自動リセットを停止中。手動で再起動してください。")
            return None, None, None, None, None
        else:
            # If we can't set up, wait and reset safely
            safe_reset(reason=f"Setup error: {str(e)}")
            # This line will never be reached
            return None

# ===== WIFI CONNECTION FUNCTION =====
def connect_wifi(client, watchdog=None, max_retries=DEBUG_WIFI_MAX_RETRIES):
    """Connect to WiFi with improved error handling and detailed logging."""
    if not client:
        print("WiFi client not initialized. Skipping connection.")
        return False

    print("Connecting to WiFi...")
    print(f"SSID: {client.ssid}, Device ID: {client.device_id}")
    print(f"Maximum retries: {max_retries}, Connection timeout: {DEBUG_WIFI_TIMEOUT} seconds")
    print(f"WiFi Mode: {DEBUG_WIFI_MODE}")
    print(f"Thonny Mode: {'Enabled' if DEBUG_THONNY_MODE else 'Disabled'}")

    # Special handling for Thonny mode
    if DEBUG_THONNY_MODE:
        print("\n===== THONNY DEVELOPMENT MODE =====")
        print("* USB connection will be maintained")
        print("* Auto-reset is disabled during WiFi connection")
        print("* Detailed status reporting is enabled")
        print("* Extended timeouts are in effect")
        print("====================================\n")

        # Force auto-reset to be disabled in Thonny mode
        global DEBUG_DISABLE_AUTO_RESET
        if not DEBUG_DISABLE_AUTO_RESET:
            print("Auto-reset automatically disabled in Thonny mode")
            DEBUG_DISABLE_AUTO_RESET = True

    # Different connection strategies based on WiFi mode
    if DEBUG_WIFI_MODE == 1:
        # Mode 1: Normal connection with automatic reset disabled
        debug_print("Using WiFi Mode 1: Normal connection with auto-reset disabled", 1)
        try:
            print("Activating WiFi interface...")
            if client.wlan.active():
                print("WiFi interface already active")
            else:
                client.wlan.active(True)
                print("WiFi interface activated")
                machine.idle()  # Allow WiFi and USB processing
                time.sleep(1)

            print(f"Sending connection request to {WIFI_SSID}...")
            print(f"Current wlan.status() = {client.wlan.status()}")

            # Print status message
            status_messages = {
                0: "STAT_IDLE - Idle",
                1: "STAT_CONNECTING - Connecting",
                2: "STAT_WRONG_PASSWORD - Wrong password",
                3: "STAT_NO_AP_FOUND - AP not found",
                4: "STAT_CONNECT_FAIL - Connection failed",
                5: "STAT_GOT_IP - Connected"
            }
            print(f"Status meaning: {status_messages.get(client.wlan.status(), 'Unknown')}")

            # Connect with detailed status reporting
            if client.connect(max_retries=1, retry_delay=1, connection_timeout=DEBUG_WIFI_TIMEOUT):
                print("Connected to WiFi successfully!")
                blink_led(5, 0.1)
                return True
            else:
                print("WiFi connection failed.")
                return False

        except Exception as e:
            print(f"WiFi connection error: {e}")
            handle_error(e, {"phase": "wifi_connection", "mode": 1})
            return False

    elif DEBUG_WIFI_MODE == 2:
        # Mode 2: Connection with extended timeout and detailed status reporting
        debug_print("Using WiFi Mode 2: Extended timeout with detailed status reporting", 1)
        try:
            # Check if WiFi is already connected
            if client.wlan.isconnected():
                print("WiFi is already connected!")
                network_info = client.wlan.ifconfig()
                print(f"IP address: {network_info[0]}")
                print(f"Subnet mask: {network_info[1]}")
                print(f"Gateway: {network_info[2]}")
                print(f"DNS: {network_info[3]}")
                return True

            print("Activating WiFi interface...")
            if not client.wlan.active():
                client.wlan.active(True)
                print("WiFi interface activated")
                machine.idle()  # Allow WiFi and USB processing
                time.sleep(2)  # Give more time for interface to initialize
            else:
                print("WiFi interface already active")

            # Check current status before connecting
            status = client.wlan.status()
            print(f"Current WiFi status: {status} - {status_messages.get(status, 'Unknown')}")

            # Disconnect first if we're in a weird state
            if status != 0:  # Not IDLE
                print("Disconnecting from any existing connections...")
                try:
                    client.wlan.disconnect()
                    machine.idle()  # Allow WiFi and USB processing
                    time.sleep(2)
                    print("Disconnected")
                except:
                    print("Error during disconnect, continuing anyway")

            print(f"Sending connection request to {WIFI_SSID}...")
            client.wlan.connect(WIFI_SSID, WIFI_PASSWORD)

            # Wait for connection with detailed status reporting
            timeout = 0
            last_status = -1
            connection_phases = {
                0: "Idle",
                1: "Connecting to AP",
                5: "Connected and getting IP"
            }
            current_phase = "Starting connection"

            while not client.wlan.isconnected() and timeout < DEBUG_WIFI_TIMEOUT:
                status = client.wlan.status()

                # Only print status if it changed or every 5 seconds
                if status != last_status or timeout % 5 == 0:
                    print(f"WiFi status: {status} - {status_messages.get(status, 'Unknown')}")
                    last_status = status

                    # Update connection phase
                    if status in connection_phases:
                        if connection_phases[status] != current_phase:
                            current_phase = connection_phases[status]
                            print(f"Connection phase: {current_phase}")

                # Blink LED to indicate waiting
                blink_led(1, 0.1)

                # Sleep in smaller increments to be more responsive
                for _ in range(4):  # 4 x 0.25s = 1s
                    if watchdog:
                        watchdog.feed()
                    machine.idle()  # Allow WiFi and USB processing
                    time.sleep(0.25)

                timeout += 1

                # Print progress every 5 seconds or if status changed
                if timeout % 5 == 0 or status != last_status:
                    print(f"Waiting for connection... {timeout}/{DEBUG_WIFI_TIMEOUT} seconds")

                # Special handling for Thonny mode - more detailed status
                if DEBUG_THONNY_MODE and timeout % 10 == 0:
                    print("\n----- WiFi Connection Status Update -----")
                    print(f"Time elapsed: {timeout} seconds")
                    print(f"Current status: {status} - {status_messages.get(status, 'Unknown')}")
                    print(f"Connection phase: {current_phase}")
                    print(f"Remaining timeout: {DEBUG_WIFI_TIMEOUT - timeout} seconds")

                    # Provide guidance based on status
                    if status == 0:  # IDLE
                        print("Connection not started yet. This is unusual after sending connection request.")
                        print("Recommendation: Wait for status to change or try resetting WiFi interface.")
                    elif status == 1:  # CONNECTING
                        print("Still trying to connect to the access point.")
                        print("Recommendation: Be patient, this can take time.")
                    elif status == 2:  # WRONG_PASSWORD
                        print("Wrong password provided for the access point.")
                        print("Recommendation: Check WIFI_PASSWORD in configuration.")
                    elif status == 3:  # NO_AP_FOUND
                        print("Access point not found.")
                        print("Recommendation: Verify WIFI_SSID and ensure the access point is active.")
                    elif status == 4:  # CONNECT_FAIL
                        print("Connection failed for an unspecified reason.")
                        print("Recommendation: Try again or check access point settings.")
                    print("----------------------------------------\n")

            # Check if connected
            if client.wlan.isconnected():
                print(f"Connected to {WIFI_SSID} after {timeout} seconds")
                network_info = client.wlan.ifconfig()
                print(f"IP address: {network_info[0]}")
                print(f"Subnet mask: {network_info[1]}")
                print(f"Gateway: {network_info[2]}")
                print(f"DNS: {network_info[3]}")

                # Get signal strength if available
                try:
                    rssi = client.wlan.status('rssi')
                    print(f"Signal strength: {rssi} dBm")
                except:
                    pass

                return True
            else:
                print(f"Failed to connect to {WIFI_SSID} after {DEBUG_WIFI_TIMEOUT} seconds")
                print(f"Final status: {client.wlan.status()} - {status_messages.get(client.wlan.status(), 'Unknown')}")

                if DEBUG_THONNY_MODE:
                    print("\n----- WiFi Connection Failure Analysis -----")
                    print("Connection failed after timeout. Possible reasons:")
                    print("1. Access point is not available or out of range")
                    print("2. Incorrect SSID or password")
                    print("3. Access point is not accepting new connections")
                    print("4. Network interface issues on the Pico")
                    print("Recommendation: Check access point status and settings")
                    print("-------------------------------------------\n")

                return False

        except Exception as e:
            print(f"WiFi connection error: {e}")
            handle_error(e, {"phase": "wifi_connection", "mode": 2})

            if DEBUG_THONNY_MODE:
                print("\n----- WiFi Connection Exception -----")
                print(f"Exception: {type(e).__name__}: {str(e)}")
                print("This is an unexpected error during the connection process.")
                print("Recommendation: Check hardware and try again")
                print("-------------------------------------\n")

            return False

    elif DEBUG_WIFI_MODE == 3:
        # Mode 3: Connection with network reset before each attempt
        debug_print("Using WiFi Mode 3: Network reset before each attempt", 1)
        retry_count = 0
        while retry_count < max_retries:
            try:
                # Feed watchdog if available
                if watchdog:
                    watchdog.feed()

                # Reset network interface
                print("Resetting WiFi interface...")
                client.wlan.active(False)
                machine.idle()  # Allow WiFi and USB processing
                time.sleep(2)
                client.wlan.active(True)
                machine.idle()  # Allow WiFi and USB processing
                time.sleep(2)

                print(f"Connection attempt {retry_count + 1}/{max_retries}...")
                print(f"Sending connection request to {WIFI_SSID}...")
                client.wlan.connect(WIFI_SSID, WIFI_PASSWORD)

                # Wait for connection
                timeout = 0
                while not client.wlan.isconnected() and timeout < DEBUG_WIFI_TIMEOUT:
                    status = client.wlan.status()
                    print(f"WiFi status: {status} - {status_messages.get(status, 'Unknown')}")

                    # Feed watchdog if available
                    if watchdog:
                        watchdog.feed()

                    machine.idle()  # Allow WiFi and USB processing
                    time.sleep(1)
                    timeout += 1

                    # Print progress every 5 seconds
                    if timeout % 5 == 0:
                        print(f"Waiting for connection... {timeout}/{DEBUG_WIFI_TIMEOUT} seconds")

                # Check if connected
                if client.wlan.isconnected():
                    print(f"Connected to {WIFI_SSID} after {timeout} seconds")
                    network_info = client.wlan.ifconfig()
                    print(f"IP address: {network_info[0]}")
                    return True

                # If not connected, try again
                retry_count += 1
                print(f"Connection attempt {retry_count} failed. Retrying...")
                machine.idle()  # Allow WiFi and USB processing
                time.sleep(5)

            except Exception as e:
                print(f"WiFi connection error: {e}")
                handle_error(e, {"phase": "wifi_connection", "mode": 3, "attempt": retry_count})
                retry_count += 1
                machine.idle()  # Allow WiFi and USB processing
                time.sleep(5)

        print(f"Failed to connect to {WIFI_SSID} after {max_retries} attempts")
        return False

    elif DEBUG_WIFI_MODE == 4:
        # Mode 4: Connection with progressive backoff and multiple retries
        debug_print("Using WiFi Mode 4: Progressive backoff with multiple retries", 1)
        return client.connect(max_retries=max_retries, retry_delay=5, connection_timeout=DEBUG_WIFI_TIMEOUT)

    else:
        print(f"Invalid WiFi mode: {DEBUG_WIFI_MODE}")
        return False

# ===== MAIN FUNCTION =====
def main():
    """Main function."""
    try:
        # Set up components
        components = setup()
        if not components:
            print("Setup failed. Running in limited mode.")
            bme, co2_sensor, client, transmitter, watchdog = None, None, None, None, None
        else:
            bme, co2_sensor, client, transmitter, watchdog = components

        # Connect to WiFi with improved error handling
        if client:
            if not connect_wifi(client, watchdog):
                print("WiFi connection failed after all attempts.")
                # Log the error but don't reset if auto-reset is disabled
                handle_error(Exception("WiFi connection failed"), {"phase": "wifi_connection"})

                if DEBUG_THONNY_MODE:
                    print("\n===== WiFi CONNECTION FAILURE IN THONNY MODE =====")
                    print("WiFi connection failed, but the program will continue running.")
                    print("Options:")
                    print("1. Continue without WiFi (data will not be transmitted)")
                    print("2. Manually restart the program after checking connections")
                    print("3. Try a different WiFi mode by changing DEBUG_WIFI_MODE")
                    print("4. Check that the access point is active and in range")
                    print("\nThe program will now continue without WiFi connection.")
                    print("You can manually stop and restart the program at any time.")
                    print("================================================\n")

                    # In Thonny mode, we'll continue without WiFi but still collect sensor data
                    print("Continuing in offline mode (sensors active, no data transmission)...")

                elif not DEBUG_DISABLE_AUTO_RESET:
                    safe_reset(reason="WiFi connection failure")
                else:
                    print("Auto-reset disabled. Continuing without WiFi connection.")
                    print("開発中のため自動リセットを停止中。手動で再起動してください。")

                # If we're continuing without WiFi, we'll enter a special offline mode
                if DEBUG_THONNY_MODE or DEBUG_DISABLE_AUTO_RESET:
                    print("\nEntering offline mode...")
                    offline_mode = True

                    # We'll still try to collect sensor data periodically
                    if bme or co2_sensor:
                        print("Sensors available in offline mode:")
                        if bme:
                            print("- BME680 (temperature, humidity, pressure, gas)")
                        if co2_sensor:
                            print("- MH-Z19C (CO2)")

                        # Create a simple loop to read and display sensor data
                        print("\nStarting sensor readings in offline mode...")
                        offline_start_time = time.time()

                        try:
                            while True:
                                # Feed watchdog if available
                                if watchdog:
                                    watchdog.feed()

                                # Read sensor data every 10 seconds
                                current_time = time.time()
                                if current_time - offline_start_time >= 10:
                                    offline_start_time = current_time

                                    print("\n----- Offline Sensor Readings -----")
                                    if bme:
                                        try:
                                            temp = bme.temperature
                                            hum = bme.humidity
                                            pres = bme.pressure
                                            gas = bme.gas
                                            print(f"BME680: Temp={temp:.1f}°C, Humidity={hum:.1f}%, Pressure={pres:.1f}hPa, Gas={gas}Ω")
                                        except Exception as e:
                                            print(f"BME680 read error: {e}")

                                    if co2_sensor:
                                        try:
                                            co2 = co2_sensor.read_co2()
                                            if co2 > 0:
                                                print(f"MH-Z19C: CO2={co2}ppm")
                                            else:
                                                print("MH-Z19C: Waiting for valid reading...")
                                        except Exception as e:
                                            print(f"MH-Z19C read error: {e}")

                                    print("----------------------------------")

                                # Allow background processing and prevent CPU overload
                                machine.idle()  # Allow WiFi and USB processing
                                time.sleep(0.05)  # Short sleep is sufficient

                        except KeyboardInterrupt:
                            print("Offline mode stopped by user")
                            return
                    else:
                        print("No sensors available in offline mode.")
                        while True:
                            if watchdog:
                                watchdog.feed()
                            machine.idle()  # Allow WiFi and USB processing
                            time.sleep(0.05)  # Short sleep is sufficient
                        return
                else:
                    # This should never be reached due to the reset
                    return
        else:
            print("WiFi client not available. Skipping connection.")

        # Wait for MH-Z19C warm-up if sensor is available
        if co2_sensor:
            warmup_time = DEBUG_SENSOR_WARMUP if DEBUG_ENABLE else co2_sensor.warmup_time
            print(f"Warming up for {warmup_time} seconds...")

            # Blink LED during warm-up
            start_time = time.time()
            while time.time() - start_time < warmup_time:
                blink_led(1, 0.1)
                machine.idle()  # Allow WiFi and USB processing
                time.sleep(1)
                if watchdog:
                    watchdog.feed()

                # Print progress every 5 seconds
                elapsed = time.time() - start_time
                if int(elapsed) % 5 == 0 and int(elapsed) > 0:
                    print(f"Warm-up: {int(elapsed)}/{warmup_time} seconds")

            print("MH-Z19C warm-up complete!")
        else:
            print("CO2 sensor not available. Skipping warm-up.")

        # Main loop
        print("Starting main loop...")
        connection_failures = 0
        max_connection_failures = 5

        while True:
            try:
                # Feed the watchdog if available
                if watchdog:
                    watchdog.feed()

                # Check WiFi connection and reconnect if needed
                if client and not client.is_connected():
                    print("WiFi connection lost. Attempting to reconnect...")
                    if not connect_wifi(client, watchdog, max_retries=3):
                        connection_failures += 1
                        print(f"Reconnection failed. Failure count: {connection_failures}/{max_connection_failures}")

                        if connection_failures >= max_connection_failures and not DEBUG_DISABLE_AUTO_RESET:
                            print("Too many connection failures. Resetting device...")
                            safe_reset(reason="Repeated WiFi connection failures")
                            return
                        elif connection_failures >= max_connection_failures:
                            print("Too many connection failures, but auto-reset is disabled.")
                            print("開発中のため自動リセットを停止中。手動で再起動してください。")
                            while True:
                                if watchdog:
                                    watchdog.feed()
                                machine.idle()  # Allow WiFi and USB processing
                                time.sleep(0.05)  # Short sleep is sufficient
                            return

                        # Wait before continuing the loop
                        print("Waiting 10 seconds before continuing...")
                        for i in range(10):
                            if watchdog:
                                watchdog.feed()
                            machine.idle()  # Allow WiFi and USB processing
                            time.sleep(1)
                        continue
                    else:
                        # Reset failure counter on successful reconnection
                        connection_failures = 0

                # Collect and send data if transmitter is available
                if transmitter:
                    success = transmitter.collect_and_send_data()

                    # Blink LED to indicate status
                    if success:
                        blink_led(1, 0.1)  # Single blink for success
                        debug_print("Data collection and transmission successful", 2)
                    else:
                        blink_led(2, 0.1)  # Double blink for failure
                        debug_print("Data collection or transmission failed", 1)
                else:
                    # If no transmitter, just blink LED to show we're alive
                    blink_led(1, 0.1)
                    machine.idle()  # Allow WiFi and USB processing
                    time.sleep(5)

                # Perform garbage collection
                gc.collect()

                # Sleep for a short time and allow background processing
                machine.idle()  # Allow WiFi and USB processing
                time.sleep(0.05)  # Short sleep to prevent CPU overload

            except Exception as e:
                print(f"Error in main loop: {e}")
                handle_error(e, {"phase": "main_loop"})
                # Continue running, don't reset immediately
                machine.idle()  # Allow WiFi and USB processing
                time.sleep(2)  # Short delay before continuing

    except KeyboardInterrupt:
        print("Program stopped by user")

    except Exception as e:
        print(f"Unhandled error: {e}")
        handle_error(e, {"phase": "unhandled"})

        # Wait and reset safely if auto-reset is enabled
        if not DEBUG_DISABLE_AUTO_RESET:
            safe_reset(reason=f"Unhandled error: {str(e)}")
        else:
            print("Auto-reset disabled. Halting execution.")
            print("開発中のため自動リセットを停止中。手動で再起動してください。")
            while True:
                try:
                    if watchdog:
                        watchdog.feed()
                except:
                    pass  # In case watchdog is not defined
                machine.idle()  # Allow WiFi and USB processing
                time.sleep(0.05)  # Short sleep is sufficient

if __name__ == "__main__":
    # Wait before starting to ensure all hardware is initialized
    print(f"Starting in {DEBUG_STARTUP_DELAY} seconds...")
    for i in range(DEBUG_STARTUP_DELAY, 0, -1):
        if i % 5 == 0 or i <= 3:  # Print countdown every 5 seconds and final 3 seconds
            print(f"{i} seconds until start...")
        time.sleep(1)
        # Blink LED occasionally during wait
        if i % 2 == 0:
            led.on()
        else:
            led.off()

    # Start the main program
    main()

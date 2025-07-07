#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi Pico 2W Main Program for Environmental Monitoring - Debug Version 4.19
Version: 4.19.0-debug

This is a debug version of the main program for the Raspberry Pi Pico 2W (P3) that helps
identify and resolve issues with WiFi connection, especially the problem where Thonny
loses the COM port connection during WiFi connection attempts.

Features:
- Enhanced debugging options for troubleshooting
- Configurable automatic reset behavior
- Multiple WiFi connection modes for testing
- Detailed status reporting throughout the process
- BME680 sensor for temperature, humidity, pressure, and gas resistance
- MH-Z19C sensor for CO2 concentration
- WiFi connectivity to P1 server with improved error handling
- Error handling with improved logging
- LED status indicators
- Emergency measures to prevent USB/REPL disconnection

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
DEBUG_STARTUP_DELAY = 10             # Startup delay in seconds
DEBUG_SENSOR_WARMUP = 5              # Sensor warmup time in seconds
DEBUG_RESET_DELAY = 3                # Delay before reset in seconds
DEBUG_THONNY_MODE = True             # Special mode for Thonny development
DEBUG_REDUCE_CPU_SPEED = True        # Reduce CPU speed for better stability
DEBUG_DIAGNOSTICS_ONLY = False       # Run only diagnostics without connection attempt
DEBUG_LOG_TO_FILE = False            # Log to file instead of printing

# ===== DEVICE CONFIGURATION =====
DEVICE_ID = "P3"                     # Device identifier
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
ERROR_LOG_FILE = "/error_log_p3_solo.txt"  # Error log file path

# Initialize LED
led = Pin(LED_PIN, Pin.OUT)

# ===== HELPER FUNCTIONS =====
def debug_print(message, level=1):
    """Print debug message if debug level is high enough."""
    if DEBUG_DETAILED_LOGGING and level <= 2:
        if DEBUG_LOG_TO_FILE:
            try:
                with open(ERROR_LOG_FILE, "a") as f:
                    f.write(f"{message}\n")
            except:
                # Fall back to print if file logging fails
                print(message)
        else:
            print(message)

    # Allow background processing after printing
    machine.idle()

def blink_led(count=1, duration=0.2):
    """Blink the LED."""
    for _ in range(count):
        led.on()
        time.sleep(duration)
        led.off()
        time.sleep(duration)

def safe_reset(reason="Unknown", delay=DEBUG_RESET_DELAY):
    """Safely reset the device after logging the reason and waiting for a delay."""
    print(f"SYSTEM RESET TRIGGERED: {reason}")
    print(f"Resetting in {delay} seconds...")

    # Log the reset reason
    if DEBUG_LOG_TO_FILE:
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

        # Reduce CPU speed if enabled
        if DEBUG_REDUCE_CPU_SPEED:
            try:
                original_freq = machine.freq()
                print(f"Original CPU frequency: {original_freq/1000000}MHz")
                machine.freq(125_000_000)
                print(f"Reduced CPU frequency to: {machine.freq()/1000000}MHz")
            except Exception as e:
                print(f"Could not reduce CPU frequency: {e}")

        # Startup delay to allow for stable initialization
        print(f"Starting in {DEBUG_STARTUP_DELAY} seconds...")
        for i in range(DEBUG_STARTUP_DELAY, 0, -1):
            if i == DEBUG_STARTUP_DELAY or i == 5 or i <= 3:
                print(f"{i} seconds until start...")
            time.sleep(1)
            # Allow background processing during delay
            machine.idle()
        print()

        # Print header
        print(f"=== Raspberry Pi Pico 2W Environmental Monitor Ver4.19 ({DEVICE_ID}) ===")
        print("Initializing...")

        # Initialize I2C for BME680
        print("Initializing I2C for BME680...")
        try:
            i2c = I2C(0, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=100000)
            devices = [hex(addr) for addr in i2c.scan()]
            print(f"I2C devices found: {devices}")
            debug_print(f"I2C initialized on SDA: GP{I2C_SDA_PIN}, SCL: GP{I2C_SCL_PIN}", 2)
        except Exception as e:
            print(f"Error initializing I2C: {e}")
            if not DEBUG_DISABLE_AUTO_RESET:
                safe_reset(reason=f"I2C initialization error: {str(e)}")
            else:
                print("Auto-reset disabled. Continuing without I2C...")
                i2c = None

        # Initialize BME680 sensor
        print("Initializing BME680 sensor...")
        try:
            from bme680 import BME680_I2C
            # Try to auto-detect the correct I2C address
            print("Attempting to auto-detect BME680 address...")
            bme = BME680_I2C(i2c, address=None)  # Auto-detect address
            debug_print("BME680 initialization successful", 1)
        except Exception as e:
            print(f"Error initializing BME680: {e}")
            # Try specific addresses as fallback
            try:
                print("Auto-detection failed. Trying address 0x77...")
                bme = BME680_I2C(i2c, address=0x77)
                debug_print("BME680 initialization successful with address 0x77", 1)
            except Exception as e1:
                print(f"Failed with address 0x77: {e1}")
                try:
                    print("Trying address 0x76...")
                    bme = BME680_I2C(i2c, address=0x76)
                    debug_print("BME680 initialization successful with address 0x76", 1)
                except Exception as e2:
                    print(f"Failed with address 0x76: {e2}")
                    if not DEBUG_DISABLE_AUTO_RESET:
                        safe_reset(reason=f"BME680 initialization error: {str(e)}")
                    else:
                        print("Auto-reset disabled. Continuing without BME680...")
                        bme = None

        # Initialize MH-Z19C CO2 sensor
        print("Initializing MH-Z19C CO2 sensor...")
        try:
            from mhz19c import MHZ19C
            co2_sensor = MHZ19C(uart_id=1, tx_pin=UART_TX_PIN, rx_pin=UART_RX_PIN)
            print(f"MH-Z19C initialized on UART1 (TX: GP{UART_TX_PIN}, RX: GP{UART_RX_PIN})")

            # Warm up the CO2 sensor
            print(f"Warming up for {DEBUG_SENSOR_WARMUP} seconds...")
            for i in range(DEBUG_SENSOR_WARMUP):
                if i % 5 == 0 or i == DEBUG_SENSOR_WARMUP - 1:
                    print(f"Warmup: {i+1}/{DEBUG_SENSOR_WARMUP} seconds")
                time.sleep(1)
                # Allow background processing during warmup
                machine.idle()
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
            try:
                from P3_watchdog_debug import handle_error, sync_all_files
            except:
                # Define fallback error handler if watchdog module is not available
                def handle_error(e, context=None):
                    print(f"Error: {e}, Context: {context}")

                def sync_all_files():
                    try:
                        import os
                        os.sync()
                    except:
                        pass
            watchdog = None

        print("Initialization complete!")
        return bme, co2_sensor, client, transmitter, watchdog

    except Exception as e:
        print(f"Error during setup: {e}")
        try:
            handle_error(e, {"phase": "setup"})
        except:
            print(f"Could not handle error: {e}")

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

    # Run network diagnostics first
    print("\nRunning network diagnostics before connection attempt...")
    diagnostics = client.run_network_diagnostics()

    # Print key diagnostics results
    print("\nDiagnostics Summary:")
    print(f"WiFi Active: {diagnostics.get('wifi_active', False)}")
    if 'networks_found' in diagnostics:
        print(f"Networks Found: {diagnostics.get('networks_found', 0)}")
        print(f"Target Network Found: {diagnostics.get('target_network_found', False)}")
        if diagnostics.get('target_network_found', False):
            print(f"Target Network Strength: {diagnostics.get('target_network_strength', 'Unknown')} dBm")

    # If diagnostics-only mode is enabled, skip connection attempt
    if DEBUG_DIAGNOSTICS_ONLY:
        print("\nDiagnostics-only mode enabled. Skipping connection attempt.")
        return False

    # Automatic decision in Thonny mode
    if DEBUG_THONNY_MODE:
        # Check if target network was found
        proceed = True  # Default to proceed

        if diagnostics.get('target_network_found', False):
            print("\nTarget network found. Proceeding with connection...")
        else:
            print("\nTarget network not found, but proceeding with connection attempt...")

        # Allow background processing
        machine.idle()
        time.sleep(0.5)

        # Check if we should skip connection based on configuration
        if not proceed:
            print("Connection attempt skipped. Continuing without WiFi connection.")
            return False

    # Different connection strategies based on WiFi mode
    if DEBUG_WIFI_MODE == 1:
        # Mode 1: Normal connection with automatic reset disabled
        debug_print("Using WiFi Mode 1: Normal connection with auto-reset disabled", 1)
        try:
            print("Activating WiFi interface...")
            if client.wlan.active():
                print("WiFi interface already active")
            else:
                try:
                    client.wlan.active(True)
                    time.sleep(1)
                    print("WiFi interface activated")
                except Exception as e:
                    print(f"Error activating WiFi interface: {e}")
                    return False

            print(f"Connecting to {client.ssid}...")
            success = client.connect(
                max_retries=max_retries,
                retry_delay=5,
                connection_timeout=DEBUG_WIFI_TIMEOUT,
                auto_reset=False
            )

            if success:
                print(f"Successfully connected to {client.ssid}")
                return True
            else:
                print(f"Failed to connect to {client.ssid}")
                return False

        except Exception as e:
            print(f"Error during WiFi connection: {e}")
            try:
                handle_error(Exception("WiFi connection failed"), {"phase": "wifi_connection"})
            except:
                print(f"Could not handle error: {e}")
            return False

    elif DEBUG_WIFI_MODE == 2:
        # Mode 2: Progressive connection strategies
        debug_print("Using WiFi Mode 2: Progressive connection strategies", 1)
        try:
            # Try standard strategy first
            print("Trying standard connection strategy...")
            client.set_connection_strategy("standard")
            client.set_auto_reset(False)
            success = client.connect(
                max_retries=2,
                retry_delay=5,
                connection_timeout=DEBUG_WIFI_TIMEOUT,
                auto_reset=False
            )

            if success:
                print("Connected with standard strategy")
                return True

            # If standard fails, try aggressive
            print("Trying aggressive connection strategy...")
            client.set_connection_strategy("aggressive")
            success = client.connect(
                max_retries=2,
                retry_delay=2,
                connection_timeout=DEBUG_WIFI_TIMEOUT // 2,
                auto_reset=False
            )

            if success:
                print("Connected with aggressive strategy")
                return True

            # If aggressive fails, try conservative
            print("Trying conservative connection strategy...")
            client.set_connection_strategy("conservative")
            success = client.connect(
                max_retries=1,
                retry_delay=10,
                connection_timeout=DEBUG_WIFI_TIMEOUT * 2,
                auto_reset=False
            )

            if success:
                print("Connected with conservative strategy")
                return True

            print("All connection strategies failed")
            return False

        except Exception as e:
            print(f"Error during WiFi connection: {e}")
            try:
                handle_error(Exception("WiFi connection failed"), {"phase": "wifi_connection"})
            except:
                print(f"Could not handle error: {e}")
            return False

    elif DEBUG_WIFI_MODE == 3:
        # Mode 3: Network diagnostics before connection
        debug_print("Using WiFi Mode 3: Network diagnostics before connection", 1)
        try:
            # Diagnostics already run at the beginning of this function

            # Attempt connection
            print("\nAttempting connection after diagnostics...")
            success = client.connect(
                max_retries=max_retries,
                retry_delay=5,
                connection_timeout=DEBUG_WIFI_TIMEOUT,
                auto_reset=False
            )

            if success:
                print(f"Successfully connected to {client.ssid}")
                return True
            else:
                print(f"Failed to connect to {client.ssid}")
                return False

        except Exception as e:
            print(f"Error during WiFi connection: {e}")
            try:
                handle_error(Exception("WiFi connection failed"), {"phase": "wifi_connection"})
            except:
                print(f"Could not handle error: {e}")
            return False

    elif DEBUG_WIFI_MODE == 4:
        # Mode 4: Manual connection with detailed status reporting
        debug_print("Using WiFi Mode 4: Manual connection with detailed status reporting", 1)
        try:
            # Activate WiFi interface
            print("Activating WiFi interface...")
            if client.wlan.active():
                print("WiFi interface already active")
            else:
                try:
                    client.wlan.active(True)
                    time.sleep(1)
                    print("WiFi interface activated")
                except Exception as e:
                    print(f"Error activating WiFi interface: {e}")
                    return False

            # Connect to WiFi manually
            print(f"Sending connection request to {client.ssid}...")
            try:
                client.wlan.connect(client.ssid, client.password)
                # Allow background processing immediately after connect call
                machine.idle()
            except Exception as e:
                print(f"Exception during wlan.connect(): {e}")
                return False

            # Wait for connection with detailed status reporting
            timeout = 0
            while not client.wlan.isconnected() and timeout < DEBUG_WIFI_TIMEOUT:
                try:
                    status = client.wlan.status()
                    status_str = client._status_to_string(status)
                    print(f"Status: {status_str} ({status}), Waiting {timeout}/{DEBUG_WIFI_TIMEOUT}s")
                except Exception as e:
                    print(f"Error getting WiFi status: {e}")

                # Blink LED to indicate waiting
                blink_led(1, 0.1)

                # Sleep with machine.idle() to allow background processing
                for _ in range(4):  # 4 x 0.25s = 1s
                    machine.idle()
                    time.sleep(0.25)

                timeout += 1

            # Check if connected
            if client.wlan.isconnected():
                print(f"Successfully connected to {client.ssid}")
                client.connected = True
                client._print_connection_info()
                return True
            else:
                print(f"Failed to connect to {client.ssid}")
                return False

        except Exception as e:
            print(f"Error during WiFi connection: {e}")
            try:
                handle_error(Exception("WiFi connection failed"), {"phase": "wifi_connection"})
            except:
                print(f"Could not handle error: {e}")
            return False

    else:
        # Default mode: Simple connection
        debug_print("Using default WiFi connection mode", 1)
        try:
            success = client.connect(
                max_retries=max_retries,
                retry_delay=5,
                connection_timeout=DEBUG_WIFI_TIMEOUT,
                auto_reset=False
            )

            if success:
                print(f"Successfully connected to {client.ssid}")
                return True
            else:
                print(f"Failed to connect to {client.ssid}")
                return False

        except Exception as e:
            print(f"Error during WiFi connection: {e}")
            try:
                handle_error(Exception("WiFi connection failed"), {"phase": "wifi_connection"})
            except:
                print(f"Could not handle error: {e}")
            return False

# ===== MAIN LOOP =====
def main_loop(bme, co2_sensor, client, transmitter, watchdog):
    """Main program loop."""
    print("Starting main loop...")

    # Connect to WiFi if client is available and not in diagnostics-only mode
    if client and not DEBUG_DIAGNOSTICS_ONLY:
        connected = connect_wifi(client, watchdog)
        if not connected:
            print("WiFi connection failed. Continuing without WiFi connection.")
            if not DEBUG_DISABLE_AUTO_RESET and not DEBUG_THONNY_MODE:
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
                    print(f"Temperature: {bme.temperature:.1f}°C, Humidity: {bme.humidity:.1f}%, "
                          f"Pressure: {bme.pressure:.1f}hPa, Gas: {bme.gas:.0f}Ω")

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

                # If auto-reset is enabled, reset after error
                if not DEBUG_DISABLE_AUTO_RESET and not DEBUG_THONNY_MODE:
                    safe_reset(reason=f"Main loop error: {str(e)}")
                else:
                    print("Auto-reset disabled. Continuing after error...")
                    time.sleep(5)  # Wait a bit before continuing

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

        # If auto-reset is enabled, reset after fatal error
        if not DEBUG_DISABLE_AUTO_RESET and not DEBUG_THONNY_MODE:
            safe_reset(reason=f"Fatal error: {str(e)}")
        else:
            print("Auto-reset disabled. Program terminated.")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi Pico 2W Main Program for Environmental Monitoring - Debug Version 4.25
Version: 4.25.0-debug

This is a debug version of the main program for the Raspberry Pi Pico 2W (P6) that helps
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
DEVICE_ID = "P6"                     # Device identifier
WIFI_SSID = "RaspberryPi5_AP_Solo2"  # WiFi network SSID
WIFI_PASSWORD = "raspberry"          # WiFi network password
SERVER_IP = "192.168.0.2"            # Server IP address
SERVER_PORT = 5000                   # Server port
TRANSMISSION_INTERVAL = 30           # Data transmission interval in seconds

# ===== PIN CONFIGURATION =====
LED_PIN = "LED"                      # Onboard LED
I2C_SDA_PIN = 0                      # I2C SDA pin for BME680
I2C_SCL_PIN = 1                      # I2C SCL pin for BME680
UART_TX_PIN = 8                      # UART TX pin for MH-Z19C
UART_RX_PIN = 9                      # UART RX pin for MH-Z19C

# ===== ERROR HANDLING =====
ERROR_LOG_FILE = "/error_log_p6_solo.txt"  # Error log file path

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
    """Safely reset the device with a reason."""
    if DEBUG_DISABLE_AUTO_RESET:
        debug_print(f"Auto-reset disabled. Manual restart required. Reason: {reason}", 1)
        debug_print("Program will continue running but may not function correctly.", 1)
        
        # Blink LED rapidly to indicate error state
        for _ in range(10):
            blink_led(3, 0.1)
            time.sleep(0.5)
            
        # Continue execution (though likely with issues)
        return
    
    debug_print(f"Resetting device in {delay} seconds. Reason: {reason}", 1)
    
    # Blink LED to indicate imminent reset
    for _ in range(delay):
        blink_led(1, 0.2)
        time.sleep(0.8)
    
    debug_print("Performing reset now...", 1)
    
    # Ensure all pending writes are flushed
    if DEBUG_LOG_TO_FILE:
        try:
            with open(ERROR_LOG_FILE, "a") as f:
                f.write(f"RESET: {reason}\n")
        except:
            pass
    
    # Reset the device
    time.sleep(0.5)  # Short delay to ensure message is printed
    machine.reset()

def initialize():
    """Initialize all components and handle errors."""
    global bme, co2_sensor, client, transmitter, watchdog
    
    # Initialize error log file
    if DEBUG_LOG_TO_FILE:
        try:
            with open(ERROR_LOG_FILE, "w") as f:
                f.write("Error log file initialized: " + ERROR_LOG_FILE + "\n")
            debug_print(f"Error log file initialized: {ERROR_LOG_FILE}")
        except Exception as e:
            debug_print(f"Failed to initialize error log file: {e}")
    
    # Add startup delay if enabled
    if DEBUG_STARTUP_DELAY > 0:
        debug_print(f"Starting in {DEBUG_STARTUP_DELAY} seconds...")
        for i in range(DEBUG_STARTUP_DELAY, 0, -1):
            if i % 5 == 0 or i <= 3:
                debug_print(f"{i} seconds until start...")
            time.sleep(1)
            machine.idle()  # Allow background processing
    
    debug_print("\n=== Raspberry Pi Pico 2W Environmental Monitor Ver4.25 (P6) ===")
    debug_print("Initializing...")
    
    # Reduce CPU speed if enabled (can improve stability)
    if DEBUG_REDUCE_CPU_SPEED:
        machine.freq(125_000_000)  # Default is 133 MHz, reduce to 125 MHz
        debug_print(f"CPU frequency set to {machine.freq() / 1_000_000} MHz")
    
    try:
        # Initialize I2C for BME680
        debug_print("Initializing I2C for BME680...")
        i2c = I2C(0, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN))
        devices = [hex(addr) for addr in i2c.scan()]
        debug_print(f"I2C devices found: {devices}")
        
        # Import and initialize BME680 sensor
        debug_print("Initializing BME680 sensor...")
        from bme680 import BME680
        bme = BME680(i2c, address=0x77)
        debug_print("BME680 initialization complete")
        
        # Import and initialize MH-Z19C CO2 sensor
        debug_print("Initializing MH-Z19C CO2 sensor...")
        from mhz19c import MHZ19C
        co2_uart = UART(1, tx=Pin(UART_TX_PIN), rx=Pin(UART_RX_PIN), baudrate=9600)
        co2_sensor = MHZ19C(co2_uart)
        debug_print(f"MH-Z19C initialized on UART1 (TX: GP{UART_TX_PIN}, RX: GP{UART_RX_PIN})")
        
        # Warm up sensors if needed
        if DEBUG_SENSOR_WARMUP > 0:
            debug_print(f"Warming up for {DEBUG_SENSOR_WARMUP} seconds...")
            time.sleep(DEBUG_SENSOR_WARMUP)
        
        # Import and initialize WiFi client
        debug_print("Initializing WiFi client...")
        from wifi_client import WiFiClient
        client = WiFiClient(
            ssid=WIFI_SSID,
            password=WIFI_PASSWORD,
            device_id=DEVICE_ID,
            debug_mode=DEBUG_ENABLE,
            debug_level=2 if DEBUG_DETAILED_LOGGING else 1
        )
        debug_print(f"WiFi Client initialized for {DEVICE_ID}")
        debug_print(f"Server: {SERVER_IP}:{SERVER_PORT}")
        
        # Import and initialize data transmitter
        debug_print("Initializing data transmitter...")
        from data_transmitter import DataTransmitter
        transmitter = DataTransmitter(
            server_ip=SERVER_IP,
            server_port=SERVER_PORT,
            device_id=DEVICE_ID
        )
        transmitter.add_sensor("bme680")
        transmitter.add_sensor("mhz19c")
        debug_print("Data transmitter initialized")
        
        # Initialize watchdog if enabled
        debug_print("Initializing watchdog...")
        if not DEBUG_DISABLE_WATCHDOG:
            from watchdog import Watchdog
            watchdog = Watchdog(timeout_ms=8000)  # 8 second timeout
            debug_print("Watchdog initialized with 8000ms timeout")
        else:
            watchdog = None
            debug_print("Watchdog disabled")
        
        debug_print("Initialization complete!")
        
    except Exception as e:
        handle_error(e, {"phase": "initialization"})
        safe_reset(reason="Initialization failure")
    
    # Sync all files to ensure they're written to flash
    sync_all_files()
    
    return bme, co2_sensor, client, transmitter, watchdog

def handle_error(e, context=None):
    """Handle errors with detailed logging."""
    from error_handler import log_error
    log_error(e, context, ERROR_LOG_FILE, DEBUG_LOG_TO_FILE)

def sync_all_files():
    """Sync all files to ensure they're written to flash."""
    try:
        import os
        os.sync()
        debug_print("Files synced to flash")
    except:
        debug_print("Failed to sync files")

def connect_wifi(client, watchdog=None, max_retries=DEBUG_WIFI_MAX_RETRIES):
    """Connect to WiFi with enhanced error handling and diagnostics."""
    if DEBUG_DIAGNOSTICS_ONLY:
        debug_print("Running in diagnostics-only mode, skipping WiFi connection")
        client.run_network_diagnostics()
        return True
    
    debug_print("Connecting to WiFi...")
    debug_print(f"SSID: {WIFI_SSID}, Device ID: {DEVICE_ID}")
    debug_print(f"Maximum retries: {max_retries}, Connection timeout: {DEBUG_WIFI_TIMEOUT} seconds")
    
    # WiFi connection modes:
    # 1: Standard connection (default)
    # 2: Connection with idle() calls
    # 3: Connection with reduced CPU speed
    # 4: Connection with both idle() and reduced CPU
    
    # Apply mode-specific settings
    original_freq = machine.freq()
    if DEBUG_WIFI_MODE in [3, 4]:
        machine.freq(100_000_000)  # Reduce to 100 MHz during connection
        debug_print(f"Temporarily reduced CPU to {machine.freq() / 1_000_000} MHz for connection")
    
    # Connection loop with retries
    connected = False
    for attempt in range(1, max_retries + 1):
        debug_print(f"Connection attempt {attempt}/{max_retries}...")
        
        # Feed watchdog if enabled
        if watchdog:
            watchdog.feed()
        
        try:
            # Mode-specific connection approach
            if DEBUG_WIFI_MODE == 1:
                # Standard connection
                connected = client.connect(timeout=DEBUG_WIFI_TIMEOUT)
            
            elif DEBUG_WIFI_MODE == 2:
                # Connection with idle() calls
                debug_print("Using connection mode 2: With idle() calls")
                client.wlan.active(True)
                debug_print("Activating WiFi interface...")
                time.sleep(1)
                machine.idle()
                
                debug_print(f"Sending connection request to {WIFI_SSID}...")
                client.wlan.connect(WIFI_SSID, WIFI_PASSWORD)
                
                # Wait for connection with idle() calls
                start_time = time.time()
                while time.time() - start_time < DEBUG_WIFI_TIMEOUT:
                    if client.wlan.status() == 3:  # 3 = connected
                        connected = True
                        break
                    
                    # Feed watchdog if enabled
                    if watchdog:
                        watchdog.feed()
                    
                    # Allow background processing
                    machine.idle()
                    time.sleep(0.1)
                
                # Check if connected
                if connected:
                    debug_print("Connected to WiFi!")
                    debug_print(f"IP address: {client.wlan.ifconfig()[0]}")
                else:
                    debug_print(f"Failed to connect after {DEBUG_WIFI_TIMEOUT} seconds")
            
            elif DEBUG_WIFI_MODE in [3, 4]:
                # Mode 3/4: With reduced CPU and possibly idle()
                debug_print(f"Using connection mode {DEBUG_WIFI_MODE}: With reduced CPU" + 
                           (" and idle() calls" if DEBUG_WIFI_MODE == 4 else ""))
                
                client.wlan.active(True)
                debug_print("Activating WiFi interface...")
                time.sleep(1)
                if DEBUG_WIFI_MODE == 4:
                    machine.idle()
                
                debug_print(f"Sending connection request to {WIFI_SSID}...")
                client.wlan.connect(WIFI_SSID, WIFI_PASSWORD)
                
                # Wait for connection
                start_time = time.time()
                while time.time() - start_time < DEBUG_WIFI_TIMEOUT:
                    if client.wlan.status() == 3:  # 3 = connected
                        connected = True
                        break
                    
                    # Feed watchdog if enabled
                    if watchdog:
                        watchdog.feed()
                    
                    # Allow background processing in mode 4
                    if DEBUG_WIFI_MODE == 4:
                        machine.idle()
                    
                    time.sleep(0.1)
                
                # Check if connected
                if connected:
                    debug_print("Connected to WiFi!")
                    debug_print(f"IP address: {client.wlan.ifconfig()[0]}")
                else:
                    debug_print(f"Failed to connect after {DEBUG_WIFI_TIMEOUT} seconds")
        
        except Exception as e:
            debug_print(f"Exception during connection attempt {attempt}: {e}")
            handle_error(e, {"phase": "wifi_connection", "attempt": attempt})
            
            # Feed watchdog if enabled
            if watchdog:
                watchdog.feed()
            
            # Allow some time before retry
            time.sleep(2)
            machine.idle()
        
        # If connected, break the loop
        if connected:
            break
        
        # Not connected, prepare for retry
        if attempt < max_retries:
            debug_print(f"Retrying in 5 seconds... (Attempt {attempt}/{max_retries})")
            
            # Blink LED to indicate retry
            blink_led(attempt, 0.2)
            
            # Wait before retry with periodic idle() calls
            for _ in range(5):
                time.sleep(1)
                machine.idle()
                if watchdog:
                    watchdog.feed()
    
    # Restore original CPU frequency if changed
    if DEBUG_WIFI_MODE in [3, 4]:
        machine.freq(original_freq)
        debug_print(f"Restored CPU to {machine.freq() / 1_000_000} MHz")
    
    # Handle connection failure
    if not connected:
        debug_print(f"Failed to connect to WiFi after {max_retries} attempts")
        handle_error(Exception("WiFi connection failed"), {"phase": "wifi_connection"})
        
        if DEBUG_THONNY_MODE:
            debug_print("In Thonny mode - not resetting to allow debugging")
            debug_print("Program will continue but data transmission will fail")
            return False
        else:
            safe_reset(reason="WiFi connection failure")
    
    return connected

def main_loop(bme, co2_sensor, client, transmitter, watchdog):
    """Main program loop."""
    debug_print("Starting main loop...")
    
    last_transmission_time = 0
    
    while True:
        try:
            # Feed watchdog if enabled
            if watchdog:
                watchdog.feed()
            
            # Check if it's time to transmit data
            current_time = time.time()
            if current_time - last_transmission_time >= TRANSMISSION_INTERVAL:
                # Collect sensor data
                debug_print("Collecting sensor data...")
                
                # BME680 readings
                temperature = bme.temperature
                humidity = bme.humidity
                pressure = bme.pressure
                gas_resistance = bme.gas_resistance
                
                debug_print(f"Temperature: {temperature:.2f}°C")
                debug_print(f"Humidity: {humidity:.2f}%")
                debug_print(f"Pressure: {pressure:.2f} hPa")
                debug_print(f"Gas resistance: {gas_resistance} Ω")
                
                # CO2 readings
                co2 = co2_sensor.read_co2()
                debug_print(f"CO2: {co2} ppm")
                
                # Prepare data for transmission
                data = {
                    "device_id": DEVICE_ID,
                    "temperature": temperature,
                    "humidity": humidity,
                    "pressure": pressure,
                    "gas_resistance": gas_resistance,
                    "co2": co2
                }
                
                # Transmit data
                debug_print("Transmitting data...")
                success = transmitter.send_data(data)
                
                if success:
                    debug_print("Data transmitted successfully")
                    last_transmission_time = current_time
                    
                    # Blink LED once to indicate successful transmission
                    blink_led(1, 0.1)
                else:
                    debug_print("Failed to transmit data")
                    
                    # Blink LED twice to indicate transmission failure
                    blink_led(2, 0.1)
            
            # Allow some idle time to prevent busy-waiting
            machine.idle()
            time.sleep(1)
            
        except Exception as e:
            handle_error(e, {"phase": "main_loop"})
            
            # Blink LED three times to indicate error
            blink_led(3, 0.1)
            
            # Continue execution after error
            time.sleep(5)

# Main program
if __name__ == "__main__":
    try:
        # Initialize components
        bme, co2_sensor, client, transmitter, watchdog = initialize()
        
        # Connect to WiFi
        if connect_wifi(client, watchdog, DEBUG_WIFI_MAX_RETRIES):
            # Run main loop
            main_loop(bme, co2_sensor, client, transmitter, watchdog)
    except Exception as e:
        handle_error(e, {"phase": "main"})
        safe_reset(reason="Unhandled exception in main")
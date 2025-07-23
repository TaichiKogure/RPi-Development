#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi Pico 2W Main Program for Environmental Monitoring - Debug Version 4.25
Version: 4.25.0-debug

This is a debug version of the main program for the Raspberry Pi Pico 2W (P5) that helps
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
DEVICE_ID = "P5"                     # Device identifier
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
ERROR_LOG_FILE = "/error_log_p5_solo.txt"  # Error log file path

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

        print(f"=== Raspberry Pi Pico 2W Environmental Monitor Ver4.25 (P5) ===")
        print("Initializing...")

        # Initialize I2C for BME680
        print("Initializing I2C for BME680...")
        i2c = I2C(0, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN))
        devices = [hex(addr) for addr in i2c.scan()]
        print(f"I2C devices found: {devices}")

        # Initialize BME680 sensor
        print("Initializing BME680 sensor...")
        from bme680 import BME680
        bme = BME680(i2c=i2c)
        
        # Ver2.00zeroOne: Commented out MH-Z19C CO2 sensor initialization as we're disabling CO2 sensor functionality
        print("CO2 sensor initialization disabled in Ver2.00zeroOne (BME680 only mode)")
        co2_sensor = None
        
        # Original MH-Z19C initialization code (commented out):
        """
        # Initialize MH-Z19C CO2 sensor
        print("Initializing MH-Z19C CO2 sensor...")
        from mhz19c import MHZ19C
        co2_sensor = MHZ19C(uart_id=1, tx_pin=UART_TX_PIN, rx_pin=UART_RX_PIN)
        print(f"MH-Z19C initialized on UART1 (TX: GP{UART_TX_PIN}, RX: GP{UART_RX_PIN})")
        """
        
        # Warm up sensors
        print(f"Warming up for {DEBUG_SENSOR_WARMUP} seconds...")
        time.sleep(DEBUG_SENSOR_WARMUP)
        
        # Initialize WiFi client
        print("Initializing WiFi client...")
        from P5_wifi_client_debug import WiFiClient
        client = WiFiClient(
            ssid=WIFI_SSID,
            password=WIFI_PASSWORD,
            device_id=DEVICE_ID,
            server_ip=SERVER_IP,
            server_port=SERVER_PORT,
            debug_mode=DEBUG_ENABLE,
            debug_level=2 if DEBUG_DETAILED_LOGGING else 1,
            connection_timeout=DEBUG_WIFI_TIMEOUT
        )
        
        # Initialize data transmitter
        print("Initializing data transmitter...")
        class DataTransmitter:
            def __init__(self, client):
                self.client = client
                self.sensors = {}
                
            def add_sensor(self, name, sensor):
                self.sensors[name] = sensor
                
            def collect_and_send_data(self):
                data = {"device_id": DEVICE_ID}
                
                # Collect data from BME680 if available
                if "bme680" in self.sensors:
                    try:
                        bme = self.sensors["bme680"]
                        bme.perform_measurement()
                        data["temperature"] = round(bme.temperature, 5)
                        data["humidity"] = round(bme.humidity, 5)
                        data["pressure"] = round(bme.pressure, 4)
                        data["gas_resistance"] = round(bme.gas_resistance)
                    except Exception as e:
                        handle_error(e, {"phase": "bme680_reading"})
                        return False
                
                # Ver2.00zeroOne: Commented out MH-Z19C data collection as we're disabling CO2 sensor functionality
                # Original MH-Z19C data collection code (commented out):
                """
                # Collect data from MH-Z19C if available
                if "mhz19c" in self.sensors:
                    try:
                        co2_sensor = self.sensors["mhz19c"]
                        co2_value = co2_sensor.read_co2()
                        if co2_value is not None:
                            data["co2"] = co2_value
                    except Exception as e:
                        handle_error(e, {"phase": "mhz19c_reading"})
                        # Continue even if CO2 reading fails
                """
                
                # Send data to server
                try:
                    return self.client.send_data(data)
                except Exception as e:
                    handle_error(e, {"phase": "data_transmission"})
                    return False
        
        transmitter = DataTransmitter(client)
        transmitter.add_sensor("bme680", bme)
        # Ver2.00zeroOne: Commented out MH-Z19C sensor registration as we're disabling CO2 sensor functionality
        # transmitter.add_sensor("mhz19c", co2_sensor)
        
        # Initialize watchdog
        print("Initializing watchdog...")
        if not DEBUG_DISABLE_WATCHDOG:
            from P5_watchdog_debug import Watchdog
            watchdog = Watchdog(timeout_ms=8000)
            print(f"Watchdog initialized with {watchdog.timeout_ms}ms timeout")
        else:
            watchdog = None
            print("Watchdog disabled by debug configuration")
        
        print("Initialization complete!")
        
        # Define error handling function
        def handle_error(e, context=None):
            """Handle errors by logging and potentially resetting."""
            error_msg = f"ERROR: {type(e).__name__}: {e}"
            if context:
                error_msg += f" (Context: {context})"
            print(error_msg)
            
            def sync_all_files():
                """Sync all files to prevent data corruption."""
                try:
                    import os
                    os.sync()
                except:
                    pass
            
            # Log error to file
            if DEBUG_LOG_TO_FILE:
                try:
                    with open(ERROR_LOG_FILE, "a") as f:
                        f.write(f"{error_msg}\n")
                except:
                    pass
            
            # Blink LED to indicate error
            blink_led(3, 0.2)
            
            # Reset if auto-reset is enabled
            if not DEBUG_DISABLE_AUTO_RESET and not DEBUG_THONNY_MODE:
                sync_all_files()
                safe_reset(reason=f"Error: {type(e).__name__}")
        
        return bme, co2_sensor, client, transmitter, watchdog
    
    except Exception as e:
        print(f"Initialization failed: {type(e).__name__}: {e}")
        blink_led(5, 0.2)
        
        if not DEBUG_DISABLE_AUTO_RESET and not DEBUG_THONNY_MODE:
            safe_reset(reason="Initialization failure")
        
        return None, None, None, None, None

# ===== WIFI CONNECTION =====
def connect_wifi(client, watchdog=None, max_retries=DEBUG_WIFI_MAX_RETRIES):
    """Connect to WiFi with the specified client."""
    print("Connecting to WiFi...")
    print(f"SSID: {client.ssid}, Device ID: {client.device_id}")
    print(f"Maximum retries: {max_retries}, Connection timeout: {client.connection_timeout} seconds")
    
    # Different WiFi connection modes for testing
    if DEBUG_WIFI_MODE == 1:
        # Mode 1: Simple connection with minimal processing
        print("Using WiFi Mode 1: Simple connection")
        for attempt in range(1, max_retries + 1):
            print(f"Connection attempt {attempt}/{max_retries}...")
            
            if client.connect():
                print(f"Connected to {client.ssid}")
                print(f"IP address: {client.get_ip_address()}")
                return True
            
            print(f"Connection attempt {attempt} failed")
            if attempt < max_retries:
                print(f"Waiting 5 seconds before retry...")
                for _ in range(5):
                    if watchdog:
                        watchdog.feed()
                    time.sleep(1)
                    machine.idle()  # Allow background processing
        
        print(f"Failed to connect after {max_retries} attempts")
        return False
    
    elif DEBUG_WIFI_MODE == 2:
        # Mode 2: Connection with network diagnostics
        print("Using WiFi Mode 2: Connection with diagnostics")
        
        # Run network diagnostics first
        print("Running network diagnostics...")
        diagnostics = client.run_network_diagnostics()
        
        if DEBUG_DIAGNOSTICS_ONLY:
            print("Diagnostics-only mode enabled, skipping actual connection")
            return False
        
        # Proceed with connection attempts
        for attempt in range(1, max_retries + 1):
            print(f"Connection attempt {attempt}/{max_retries}...")
            
            if client.connect():
                print(f"Connected to {client.ssid}")
                print(f"IP address: {client.get_ip_address()}")
                return True
            
            print(f"Connection attempt {attempt} failed")
            if attempt < max_retries:
                print(f"Waiting 5 seconds before retry...")
                for _ in range(5):
                    if watchdog:
                        watchdog.feed()
                    time.sleep(1)
                    machine.idle()  # Allow background processing
        
        print(f"Failed to connect after {max_retries} attempts")
        return False
    
    elif DEBUG_WIFI_MODE == 3:
        # Mode 3: Gradual connection with extensive idle time
        print("Using WiFi Mode 3: Gradual connection with idle time")
        
        # Initialize WiFi interface
        print("Activating WiFi interface...")
        if not client.activate_wifi():
            print("Failed to activate WiFi interface")
            return False
        
        # Allow time for WiFi initialization
        print("Waiting for WiFi initialization...")
        for _ in range(3):
            if watchdog:
                watchdog.feed()
            time.sleep(1)
            machine.idle()  # Allow background processing
        
        # Scan for networks
        print("Scanning for networks...")
        networks = client.scan_networks()
        if not networks:
            print("No networks found")
            return False
        
        # Check if target network is available
        target_found = False
        for ssid, *_ in networks:
            if ssid.decode('utf-8') == client.ssid:
                target_found = True
                break
        
        if not target_found:
            print(f"Target network {client.ssid} not found")
            return False
        
        print(f"Target network {client.ssid} found, attempting connection...")
        
        # Connect to network with pauses
        for attempt in range(1, max_retries + 1):
            print(f"Connection attempt {attempt}/{max_retries}...")
            
            # Connect with manual steps
            try:
                print("Sending connection request...")
                client.wlan.connect(client.ssid, client.password)
                
                # Wait for connection with frequent idle calls
                timeout = client.connection_timeout
                start_time = time.time()
                
                while time.time() - start_time < timeout:
                    if watchdog:
                        watchdog.feed()
                    
                    if client.wlan.isconnected():
                        print(f"Connected to {client.ssid}")
                        ip = client.wlan.ifconfig()[0]
                        print(f"IP address: {ip}")
                        return True
                    
                    # Short sleep with idle to allow background processing
                    time.sleep(0.1)
                    machine.idle()
                    
                    # Periodically print status
                    if int(time.time() - start_time) % 5 == 0:
                        status = client.wlan.status()
                        print(f"Connection status: {status}")
                
                print(f"Connection timed out after {timeout} seconds")
            except Exception as e:
                print(f"Connection error: {e}")
            
            if attempt < max_retries:
                print(f"Waiting 5 seconds before retry...")
                for _ in range(5):
                    if watchdog:
                        watchdog.feed()
                    time.sleep(1)
                    machine.idle()  # Allow background processing
        
        print(f"Failed to connect after {max_retries} attempts")
        return False
    
    elif DEBUG_WIFI_MODE == 4:
        # Mode 4: Minimal connection with extensive error handling
        print("Using WiFi Mode 4: Minimal connection with error handling")
        
        for attempt in range(1, max_retries + 1):
            print(f"Connection attempt {attempt}/{max_retries}...")
            
            try:
                # Activate WiFi
                if not client.activate_wifi():
                    print("Failed to activate WiFi interface")
                    continue
                
                # Connect with minimal processing
                print(f"Connecting to {client.ssid}...")
                client.wlan.connect(client.ssid, client.password)
                
                # Simple wait loop
                timeout = client.connection_timeout
                start_time = time.time()
                
                while time.time() - start_time < timeout:
                    if watchdog:
                        watchdog.feed()
                    
                    if client.wlan.isconnected():
                        print(f"Connected to {client.ssid}")
                        ip = client.wlan.ifconfig()[0]
                        print(f"IP address: {ip}")
                        return True
                    
                    # Longer sleep to reduce processing
                    time.sleep(1)
                
                print(f"Connection timed out after {timeout} seconds")
            except Exception as e:
                print(f"Connection error: {e}")
            
            # Deactivate WiFi before retry
            try:
                client.wlan.active(False)
                print("WiFi interface deactivated")
            except:
                pass
            
            if attempt < max_retries:
                print(f"Waiting 5 seconds before retry...")
                for _ in range(5):
                    if watchdog:
                        watchdog.feed()
                    time.sleep(1)
        
        print(f"Failed to connect after {max_retries} attempts")
        return False
    
    else:
        print(f"Invalid WiFi mode: {DEBUG_WIFI_MODE}")
        return False

# ===== MAIN LOOP =====
def main_loop(bme, co2_sensor, client, transmitter, watchdog):
    """Main loop for sensor reading and data transmission."""
    print("Starting main loop...")
    
    last_transmission_time = 0
    
    while True:
        try:
            # Feed watchdog
            if watchdog:
                watchdog.feed()
            
            # Check if it's time to transmit data
            current_time = time.time()
            if current_time - last_transmission_time >= TRANSMISSION_INTERVAL:
                print(f"\n=== Data Transmission at {time.time()} ===")
                
                # Collect and send data
                if transmitter.collect_and_send_data():
                    print("Data transmitted successfully")
                    last_transmission_time = current_time
                    
                    # Blink LED to indicate successful transmission
                    blink_led(1, 0.1)
                else:
                    print("Data transmission failed")
                    
                    # Blink LED to indicate transmission failure
                    blink_led(2, 0.2)
            
            # Short sleep to prevent busy waiting
            time.sleep(1)
            
            # Allow background processing
            machine.idle()
            
            # Perform garbage collection to free memory
            gc.collect()
            
        except Exception as e:
            print(f"Error in main loop: {type(e).__name__}: {e}")
            
            # Blink LED to indicate error
            blink_led(3, 0.2)
            
            # Continue loop instead of resetting to improve stability during development
            if DEBUG_THONNY_MODE:
                print("Continuing loop due to Thonny development mode")
                time.sleep(5)
            else:
                safe_reset(reason=f"Main loop error: {type(e).__name__}")

# ===== MAIN PROGRAM =====
if __name__ == "__main__":
    # Initialize components
    bme, co2_sensor, client, transmitter, watchdog = initialize()
    
    if bme is None or client is None or transmitter is None:
        print("Initialization failed, cannot continue")
        if not DEBUG_DISABLE_AUTO_RESET and not DEBUG_THONNY_MODE:
            safe_reset(reason="Initialization failure")
        sys.exit(1)
    
    # Connect to WiFi
    if not connect_wifi(client, watchdog, max_retries=DEBUG_WIFI_MAX_RETRIES):
        print("WiFi connection failed")
        if not DEBUG_DISABLE_AUTO_RESET and not DEBUG_THONNY_MODE:
            safe_reset(reason="WiFi connection failure")
        sys.exit(1)
    
    # Run main loop
    try:
        main_loop(bme, co2_sensor, client, transmitter, watchdog)
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
    except Exception as e:
        print(f"Unhandled exception: {type(e).__name__}: {e}")
        if not DEBUG_DISABLE_AUTO_RESET and not DEBUG_THONNY_MODE:
            safe_reset(reason=f"Unhandled exception: {type(e).__name__}")
    finally:
        # Clean up
        if watchdog:
            watchdog.disable()
        print("Program ended")
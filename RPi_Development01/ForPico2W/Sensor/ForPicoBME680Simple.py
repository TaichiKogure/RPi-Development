"""
ForPicoBME680Simple.py - A simple program to read data from BME680 sensor on Raspberry Pi Pico 2W

This program initializes the BME680 environmental sensor and reads temperature,
humidity, pressure, and gas resistance values every 5 seconds.

Hardware connections:
- BME680 sensor (I2C connection)
  - VCC -> 3.3V (Pin 36)
  - GND -> GND (Pin 38)
  - SCL -> GP1 (Pin 2)
  - SDA -> GP0 (Pin 1)

Author: JetBrains
Version: 1.0
Date: 2025-07-27
"""

import time
import gc
from machine import I2C, Pin
import sys

# Import the BME680 driver
try:
    from bme680 import BME680_I2C
except ImportError:
    print("Error: BME680 driver not found. Make sure bme680.py is in the same directory.")
    sys.exit(1)

# Program information
print("===== BME680 Environmental Data Monitor for Pico 2W =====")
print("Version: 1.0")
print("Reading data from BME680 sensor every 5 seconds")
print("Press Ctrl+C to exit")
print("======================================================")

# LED setup for status indication
led = Pin("LED", Pin.OUT)  # Onboard LED

# Error handling function
def handle_error(e, phase):
    """Handle errors and provide feedback.
    
    Args:
        e: The exception that occurred
        phase: The phase where the error occurred (e.g., "initialization", "reading data")
    
    Returns:
        False to indicate an error occurred
    """
    print(f"Error during {phase}: {e}")
    print("Will retry in 5 seconds...")
    
    # Blink LED rapidly to indicate error
    for _ in range(10):
        led.toggle()
        time.sleep(0.2)
    
    time.sleep(3)  # Additional delay before retry
    return False

# Main function
def main():
    """Main program function."""
    i2c = None
    bme = None
    
    try:
        # Initialize I2C bus
        print("Initializing I2C bus...")
        i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=100000)  # GP1 (SCL), GP0 (SDA)
        
        # Scan for I2C devices
        devices = i2c.scan()
        if not devices:
            print("No I2C devices found. Check connections.")
            return False
        
        print(f"I2C devices found: {[hex(d) for d in devices]}")
        
        # Initialize BME680 sensor
        print("Initializing BME680 sensor...")
        
        # Try with address 0x77 first
        try:
            bme = BME680_I2C(i2c, address=0x77)
            print("BME680 initialized with address 0x77")
        except Exception as e:
            print(f"Failed to initialize with address 0x77: {e}")
            print("Trying with address 0x76...")
            
            # Try with address 0x76
            try:
                bme = BME680_I2C(i2c, address=0x76)
                print("BME680 initialized with address 0x76")
            except Exception as e:
                return handle_error(e, "sensor initialization")
        
        # Wait for sensor to stabilize
        print("Waiting for sensor to stabilize...")
        time.sleep(2)
        print("Initialization complete. Starting data collection...")
        
        # Measurement counter
        count = 0
        
        # Main loop
        while True:
            try:
                # Increment counter
                count += 1
                
                # Turn on LED during measurement
                led.on()
                
                # Get current time
                current_time = time.localtime()
                time_str = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
                    current_time[0], current_time[1], current_time[2],
                    current_time[3], current_time[4], current_time[5]
                )
                
                # Read sensor data
                temperature = bme.temperature
                humidity = bme.humidity
                pressure = bme.pressure
                gas = bme.gas
                
                # Turn off LED after measurement
                led.off()
                
                # Display data
                print(f"[{count}] {time_str}")
                print(f"  Temperature: {temperature:.2f} °C")
                print(f"  Humidity: {humidity:.2f} %")
                print(f"  Pressure: {pressure:.2f} hPa")
                print(f"  Gas Resistance: {gas} Ω")
                print("-" * 40)
                
                # Memory management
                gc.collect()
                
                # Wait for next reading
                time.sleep(5)
                
            except KeyboardInterrupt:
                print("\nProgram terminated by user")
                break
            except Exception as e:
                handle_error(e, "data reading")
        
        return True
    
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
        return True
    except Exception as e:
        return handle_error(e, "initialization")

# Run the program
if __name__ == "__main__":
    while not main():
        print("Restarting program...")
        time.sleep(1)
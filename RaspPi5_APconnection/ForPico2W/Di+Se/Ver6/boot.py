"""
Boot script for Raspberry Pi Pico
This script runs automatically when the Pico powers on.
It will start the BME680 environmental monitor program.

Author: JetBrains
Version: 1.0
Date: 2025-07-27
"""

import time
import machine
import gc

# Print startup message
print("\n" + "="*50)
print("Raspberry Pi Pico Boot Sequence")
print("Starting BME680 Environmental Monitor")
print("="*50 + "\n")

# Give the system a moment to initialize
time.sleep(1)

# Free up memory
gc.collect()

# Import and run the main program
try:
    import bme680_oled_monitor_updated
    print("Main program imported successfully")
except ImportError as e:
    print(f"Error importing main program: {e}")
    print("Please ensure bme680_oled_monitor_updated.py is in the root directory")

# The main program will run automatically after import
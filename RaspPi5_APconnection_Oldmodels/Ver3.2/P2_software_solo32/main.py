# main.py - Auto-start file for Raspberry Pi Pico 2W
# Version 3.2.0-solo

# This file is automatically executed when the Pico 2W starts up.
# It simply imports and runs the main_solo.py program.

import time
import machine
from machine import Pin

# Onboard LED for startup indication
led = Pin(25, Pin.OUT)

# Blink LED to indicate startup
for _ in range(3):
    led.on()
    time.sleep(0.1)
    led.off()
    time.sleep(0.1)

print("Starting P2 Environmental System v3.6.0")
print("Initializing...")

# Wait a moment for system stability
time.sleep(2)

try:
    # Import and run the main program
    import main_solo
    
except Exception as e:
    # Error handling if main_solo.py fails to load
    print(f"Error loading main_solo.py: {e}")
    
    # Indicate error with rapid LED blinking
    for _ in range(10):
        led.on()
        time.sleep(0.1)
        led.off()
        time.sleep(0.1)
    
    # Try to reset after a delay
    print("Resetting in 5 seconds...")
    time.sleep(5)
    machine.reset()
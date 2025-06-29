# -*- coding: utf-8 -*-
"""
BME680 Simple Test Program Launcher for Raspberry Pi Pico 2W
Version: 1.0.0

This is a simple launcher that imports and runs the bme680_test.py program.
When the Pico 2W boots up, it automatically runs this file, which then
launches the main test program.
"""

import time
from machine import Pin

# Status LED
LED_PIN = 25  # Onboard LED on Pico W
led = Pin(LED_PIN, Pin.OUT)

# Blink LED to indicate startup
for _ in range(3):
    led.on()
    time.sleep(0.2)
    led.off()
    time.sleep(0.2)

print("Starting BME680 Simple Test Program...")
print("======================================")

try:
    # Import and run the main test program
    import bme680_test
    bme680_test.main()
except Exception as e:
    # If there's an error, print it and blink the LED rapidly
    print(f"Error: {e}")
    for _ in range(10):
        led.on()
        time.sleep(0.1)
        led.off()
        time.sleep(0.1)
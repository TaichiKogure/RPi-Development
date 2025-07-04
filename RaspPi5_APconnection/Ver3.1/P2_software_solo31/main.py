#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi Pico 2W Main Program Launcher - Solo Version 3
Version: 3.0.0-solo

This is the main launcher for the Raspberry Pi Pico 2W Solo version 3.
It imports and runs the main_solo.py program.

When the Pico boots up, it automatically runs this file, which then
launches the main program.
"""

import sys
import time
import machine

# Print startup message
print("Starting Raspberry Pi Pico 2W Environmental Data System - Solo Version 3")
print("Version: 3.0.0-solo")
print("Initializing...")

try:
    # Import and run the main program
    import main_solo
    main_solo.main()
except Exception as e:
    # If there's an error, print it and reset the device
    print(f"Critical error in main launcher: {e}")
    print("Restarting device in 10 seconds...")
    time.sleep(10)
    machine.reset()
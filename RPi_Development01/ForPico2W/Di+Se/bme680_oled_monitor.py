"""
BME680 Environmental Data Monitor with SSD1306 OLED Display

This program reads data from a BME680 environmental sensor and displays it on a 128x64 OLED display.
The display shows date and time, temperature, humidity, absolute humidity, pressure, and gas resistance.
The text scrolls from right to left for better readability.

Hardware connections:
- BME680 sensor (I2C connection)
  - VCC -> 3.3V (Pin 36)
  - GND -> GND (Pin 38)
  - SCL -> GP1 (Pin 2)
  - SDA -> GP0 (Pin 1)
- SSD1306 OLED display (SPI connection)
  - VCC -> 3.3V (Pin 36)
  - GND -> GND (Pin 38)
  - DIN (MOSI) -> GP3 (Pin 5)
  - CLK (SCK) -> GP2 (Pin 4)
  - CS -> GP6 (Pin 9)
  - DC -> GP4 (Pin 6)
  - RST -> GP5 (Pin 7)

Author: JetBrains
Version: 1.0
Date: 2025-07-27
"""

import time
import math
import gc
from machine import I2C, SPI, Pin
import sys
import framebuf

# Global variables to store last valid sensor readings
last_temperature = 25.0
last_humidity = 50.0
last_pressure = 1013.25
last_gas = 0
last_abs_humidity = 0.0

# Import the BME680 driver and SSD1306 driver
try:
    from bme680 import BME680_I2C
    import ssd1306
except ImportError:
    print("Error: Required drivers not found. Make sure bme680.py and ssd1306.py are available.")
    sys.exit(1)

# Pin definitions
# I2C pins for BME680
I2C_SCL_PIN = 1  # GP1
I2C_SDA_PIN = 0  # GP0

# SPI pins for SSD1306
SPI_ID = 0
SPI_SCK_PIN = 2   # GP2 - CLK
SPI_MOSI_PIN = 3  # GP3 - DIN
SPI_DC_PIN = 4    # GP4 - DC
SPI_RST_PIN = 5   # GP5 - RST
SPI_CS_PIN = 6    # GP6 - CS

# Display dimensions
WIDTH = 128
HEIGHT = 64

# Row heights
TOP_ROW_HEIGHT = 20
MIDDLE_ROW_HEIGHT = 22
BOTTOM_ROW_HEIGHT = 22

# LED setup for status indication
led = Pin("LED", Pin.OUT)  # Onboard LED

# Function to calculate absolute humidity from temperature and relative humidity
def calculate_absolute_humidity(temperature, humidity):
    """
    Calculate absolute humidity from temperature and relative humidity.
    
    Args:
        temperature (float): Temperature in Celsius
        humidity (float): Relative humidity as a percentage (0-100)
        
    Returns:
        float: Absolute humidity in g/m³, rounded to 2 decimal places
    """
    try:
        # Validate inputs
        if temperature is None or humidity is None:
            return None
            
        # Check for valid ranges
        if temperature < -273.15 or humidity < 0 or humidity > 100:
            print(f"Invalid values for absolute humidity calculation: temp={temperature}, humidity={humidity}")
            return None
            
        # Calculate saturation vapor pressure
        # Magnus formula
        saturation_vapor_pressure = 6.112 * math.exp((17.67 * temperature) / (temperature + 243.5))
        
        # Calculate vapor pressure
        vapor_pressure = saturation_vapor_pressure * (humidity / 100.0)
        
        # Calculate absolute humidity
        absolute_humidity = (vapor_pressure * 18.02) / ((273.15 + temperature) * 0.08314)
        
        # Round to 2 decimal places
        return round(absolute_humidity, 2)
        
    except Exception as e:
        print(f"Error calculating absolute humidity: {e}")
        return None

# Function to get current time
def get_time():
    current_time = time.localtime()
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        current_time[0], current_time[1], current_time[2],
        current_time[3], current_time[4], current_time[5]
    )

# Class for scrolling text
class ScrollText:
    def __init__(self, display, text, y, color=1, speed=1):
        """
        Initialize a scrolling text object.
        
        Args:
            display: The SSD1306 display object
            text: The text to scroll
            y: The y-coordinate for the text
            color: The color of the text (1 for white, 0 for black)
            speed: The scrolling speed (pixels per update)
        """
        self.display = display
        self.text = text
        self.y = y
        self.color = color
        self.speed = speed
        self.x = WIDTH  # Start from the right edge
        self._update_text_width()
        
    def _update_text_width(self):
        """Update the text width calculation when text changes."""
        self.text_width = len(self.text) * 8  # Assuming 8 pixels per character
        
    def update(self):
        """Update the scrolling text position and draw it."""
        # If text is empty, don't do anything
        if not self.text:
            return
            
        # Update text width if it might have changed
        self._update_text_width()
        
        # Move text to the left
        self.x -= self.speed
        
        # If the text has scrolled completely off the left edge, reset to the right
        if self.x < -self.text_width:
            self.x = WIDTH
            
        # Draw the text at the current position
        self.display.text(self.text, self.x, self.y, self.color)
        
        # If the text is partially off the right edge, draw the beginning part on the left
        if self.x > 0 and self.x < WIDTH and len(self.text) * 8 > WIDTH:
            # Calculate how much of the text is visible
            visible_width = WIDTH - self.x
            # Calculate how many characters are visible
            visible_chars = visible_width // 8
            # If there are more characters in the text than visible, draw the rest from the beginning
            if visible_chars < len(self.text):
                self.display.text(self.text[:len(self.text)-visible_chars], 0, self.y, self.color)

# Error handling function
def handle_error(e, phase):
    """Handle errors and provide feedback."""
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
    display = None
    
    try:
        # Initialize I2C bus for BME680
        print("Initializing I2C for BME680...")
        i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=100000)
        
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
        
        # Initialize SPI for SSD1306
        print("Initializing SPI for SSD1306...")
        spi = SPI(
            SPI_ID,
            baudrate=10000000,
            polarity=0,
            phase=0,
            sck=Pin(SPI_SCK_PIN),
            mosi=Pin(SPI_MOSI_PIN)
        )
        
        # Initialize display pins
        dc = Pin(SPI_DC_PIN)
        rst = Pin(SPI_RST_PIN)
        cs = Pin(SPI_CS_PIN)
        
        # Initialize display
        print("Initializing SSD1306 display...")
        display = ssd1306.SSD1306_SPI(WIDTH, HEIGHT, spi, dc, rst, cs)
        
        # Set contrast for better visibility
        display.contrast(255)
        
        # Wait for sensor to stabilize
        print("Waiting for sensor to stabilize...")
        time.sleep(2)
        print("Initialization complete. Starting data collection...")
        
        # Create scrolling text objects (outside the loop for better memory efficiency)
        top_scroller = ScrollText(display, "", 5, 1, 2)
        middle_scroller = ScrollText(display, "", 25, 1, 2)
        bottom_scroller = ScrollText(display, "", 45, 1, 2)
        
        # Main loop
        while True:
            try:
                # Turn on LED during measurement
                led.on()
                
                # Get current time
                time_str = get_time()
                
                # Read sensor data (with error checking)
                try:
                    temperature = bme.temperature
                    humidity = bme.humidity
                    pressure = bme.pressure
                    gas = bme.gas
                    
                    # Validate sensor readings
                    if temperature is None or humidity is None or pressure is None or gas is None:
                        print("Warning: One or more sensor readings returned None")
                        # Use previous valid readings if available, or set defaults
                        global last_temperature, last_humidity, last_pressure, last_gas
                        temperature = last_temperature if temperature is None else temperature
                        humidity = last_humidity if humidity is None else humidity
                        pressure = last_pressure if pressure is None else pressure
                        gas = last_gas if gas is None else gas
                    
                    # Store last valid readings
                    last_temperature = temperature
                    last_humidity = humidity
                    last_pressure = pressure
                    last_gas = gas
                except Exception as e:
                    print(f"Error reading sensor data: {e}")
                    # Use last valid readings if available, or set defaults
                    global last_temperature, last_humidity, last_pressure, last_gas
                    temperature = last_temperature
                    humidity = last_humidity
                    pressure = last_pressure
                    gas = last_gas
                
                # Calculate absolute humidity
                abs_humidity = calculate_absolute_humidity(temperature, humidity)
                if abs_humidity is None:
                    global last_abs_humidity
                    abs_humidity = last_abs_humidity
                else:
                    last_abs_humidity = abs_humidity
                
                # Turn off LED after measurement
                led.off()
                
                # Clear the display
                display.fill(0)
                
                # Update text content for each row
                # Top row: Date and time
                top_text = f"Date/Time: {time_str}"
                top_scroller.text = top_text
                
                # Middle row: Temperature, relative humidity, absolute humidity
                middle_text = f"Temp: {temperature:.2f} C  RH: {humidity:.2f} %  AH: {abs_humidity:.2f} g/m3"
                middle_scroller.text = middle_text
                
                # Bottom row: Pressure, gas resistance
                bottom_text = f"Pressure: {pressure:.2f} hPa  Gas: {gas} ohms"
                bottom_scroller.text = bottom_text
                
                # Update and display scrolling text
                top_scroller.update()
                middle_scroller.update()
                bottom_scroller.update()
                
                # Update display
                display.show()
                
                # Print data to console for debugging
                print(f"Time: {time_str}")
                print(f"Temperature: {temperature:.2f} °C")
                print(f"Humidity: {humidity:.2f} %")
                print(f"Absolute Humidity: {abs_humidity:.2f} g/m³")
                print(f"Pressure: {pressure:.2f} hPa")
                print(f"Gas Resistance: {gas} Ω")
                print("-" * 40)
                
                # Memory management
                gc.collect()
                
                # Wait for next update (1 second)
                time.sleep(1)
                
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
    finally:
        # Clean up
        if display:
            try:
                display.fill(0)
                display.show()
                print("Display cleared on exit")
            except Exception as e:
                print(f"Error clearing display: {e}")

# Run the program
if __name__ == "__main__":
    print("===== BME680 Environmental Data Monitor with OLED Display =====")
    print("Version: 1.0")
    print("Press Ctrl+C to exit")
    print("======================================================")
    
    while not main():
        print("Restarting program...")
        time.sleep(1)
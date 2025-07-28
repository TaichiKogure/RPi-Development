"""
BME680 Environmental Data Monitor with SSD1306 OLED Display

This program reads data from a BME680 environmental sensor and displays it on a 128x64 OLED display.
The display shows date and time, temperature, humidity, absolute humidity, pressure, and gas resistance.
All information is displayed in a row-based layout with improved formatting:
- Date and time are displayed with slashes and colons for better readability
- Sensor data is displayed with spaces between values and units
- Each data point is displayed on its own row for better readability
- A simple animation is displayed in the right 30x64 pixel area

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
Version: 1.3
Date: 2025-07-27
"""

import time
import math
import gc
from machine import I2C, SPI, Pin
import sys
import framebuf
import random

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

# Animation area constants
ANIM_X = 98       # Starting X position for animation area
ANIM_WIDTH = 30   # Width of animation area
ANIM_HEIGHT = 64  # Height of animation area

# Display layout constants
ROW_HEIGHT = 9   # Height between rows
ROW_START_Y = 0  # Starting Y position for the first row
X_OFFSET = 0     # X offset for all rows (aligned to left)

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
    # Return date and time with improved formatting (slashes, colons, and spaces)
    return "{:04d}/{:02d}/{:02d} {:02d}:{:02d} {:02d}".format(
        current_time[0], current_time[1], current_time[2],
        current_time[3], current_time[4], current_time[5]
    )

# Function to display text at a specific position
def display_text(display, text, x, y, color=1):
    """
    Display text at a specific position on the screen.
    
    Args:
        display: The SSD1306 display object
        text: The text to display
        x: The x-coordinate for the text
        y: The y-coordinate for the text
        color: The color of the text (1 for white, 0 for black)
    """
    display.text(text, x, y, color)

# Simple animation class for the right side of the display
class BounceAnimation:
    """
    Simple animation class that draws a bouncing ball in the specified area.
    """
    def __init__(self, display, x, width, height):
        self.display = display
        self.x = x
        self.width = width
        self.height = height
        self.ball_x = x + width // 2
        self.ball_y = height // 2
        self.ball_radius = 3
        self.dx = random.choice([-1, 1])
        self.dy = random.choice([-1, 1])
    
    def update(self):
        """Update the animation state and draw the frame."""
        # Clear the animation area
        for y in range(self.height):
            for x in range(self.width):
                self.display.pixel(self.x + x, y, 0)
        
        # Update ball position
        self.ball_x += self.dx
        self.ball_y += self.dy
        
        # Bounce off the walls
        if self.ball_x - self.ball_radius <= self.x or self.ball_x + self.ball_radius >= self.x + self.width:
            self.dx = -self.dx
        if self.ball_y - self.ball_radius <= 0 or self.ball_y + self.ball_radius >= self.height:
            self.dy = -self.dy
        
        # Draw the ball
        self.draw_circle(self.ball_x, self.ball_y, self.ball_radius, 1)
    
    def draw_circle(self, x0, y0, radius, color):
        """Draw a circle using the Bresenham algorithm."""
        x = radius
        y = 0
        err = 0
        
        while x >= y:
            self.display.pixel(x0 + x, y0 + y, color)
            self.display.pixel(x0 + y, y0 + x, color)
            self.display.pixel(x0 - y, y0 + x, color)
            self.display.pixel(x0 - x, y0 + y, color)
            self.display.pixel(x0 - x, y0 - y, color)
            self.display.pixel(x0 - y, y0 - x, color)
            self.display.pixel(x0 + y, y0 - x, color)
            self.display.pixel(x0 + x, y0 - y, color)
            
            y += 1
            if err <= 0:
                err += 2 * y + 1
            if err > 0:
                x -= 1
                err -= 2 * x + 1

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
        
        # Initialize animation
        animation = BounceAnimation(display, ANIM_X, ANIM_WIDTH, ANIM_HEIGHT)
        
        # Wait for sensor to stabilize
        print("Waiting for sensor to stabilize...")
        time.sleep(2)
        print("Initialization complete. Starting data collection...")
        
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
                
                # Split date and time
                date_time = time_str.split(" ")
                
                # Row 1: Date (with slashes)
                display_text(display, date_time[0], X_OFFSET, ROW_START_Y, 1)
                
                # Row 2: Time (with colons and space)
                display_text(display, date_time[1] + " " + date_time[2], X_OFFSET, ROW_START_Y + ROW_HEIGHT, 1)
                
                # Row 3: Temperature (value with unit and space)
                display_text(display, f"{temperature:.1f} C", X_OFFSET, ROW_START_Y + ROW_HEIGHT*2, 1)
                
                # Row 4: Relative humidity (value with unit and space)
                display_text(display, f"{humidity:.1f} %", X_OFFSET, ROW_START_Y + ROW_HEIGHT*3, 1)
                
                # Row 5: Absolute humidity (value with unit and space)
                display_text(display, f"{abs_humidity:.1f} g/m3", X_OFFSET, ROW_START_Y + ROW_HEIGHT*4, 1)
                
                # Row 6: Pressure (value with unit and space)
                display_text(display, f"{pressure:.0f} hPa", X_OFFSET, ROW_START_Y + ROW_HEIGHT*5, 1)
                
                # Row 7: Gas resistance (value with unit and space)
                # Format gas resistance with appropriate units (k or M)
                if gas > 1000000:
                    gas_formatted = f"{gas/1000000:.1f}M"
                elif gas > 1000:
                    gas_formatted = f"{gas/1000:.1f}k"
                else:
                    gas_formatted = f"{gas}"
                display_text(display, f"{gas_formatted} ohm", X_OFFSET, ROW_START_Y + ROW_HEIGHT*6, 1)
                
                # Update and draw animation
                animation.update()
                
                # Draw a vertical line to separate the data and animation areas
                for y in range(HEIGHT):
                    display.pixel(ANIM_X - 1, y, 1)
                
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
    print("Version: 1.3 - Improved Formatting with Animation")
    print("Press Ctrl+C to exit")
    print("======================================================")
    
    while not main():
        print("Restarting program...")
        time.sleep(1)
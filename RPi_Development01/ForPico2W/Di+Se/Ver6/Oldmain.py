"""
BME680 Environmental Data Monitor with SSD1306 OLED Display

This program reads data from a BME680 environmental sensor and displays it on a 128x64 OLED display.
The display shows date and time, temperature, humidity, absolute humidity, pressure, and gas resistance.
All information is displayed in a row-based layout with improved formatting:
- Date and time are displayed with slashes and colons for better readability
- Sensor data is displayed with spaces between values and units
- Each data point is displayed on its own row for better readability
- A simple animation is displayed in the right 36x64 pixel area with 3 bouncing boxes

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
Version: 1.4
Date: 2025-07-27
"""

import time
import math
import gc
from machine import I2C, SPI, Pin, WDT, reset
import sys
import framebuf
import random
import os

# Global variables to store last valid sensor readings
last_temperature = 25.0
last_humidity = 50.0
last_pressure = 1013.25
last_gas = 0
last_abs_humidity = 0.0

# Global variables for system monitoring
restart_count = 0
watchdog = None
LOG_FILE = "error_log.txt"
MAX_LOG_SIZE = 4096  # Maximum log file size in bytes

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

# Animation area constants - Updated to 36x64 pixels
ANIM_X = 92       # Starting X position for animation area (updated)
ANIM_WIDTH = 36   # Width of animation area (updated)
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

# Updated animation class for the right side of the display with multiple bouncing boxes
class BounceAnimation:
    """
    Animation class that draws multiple bouncing boxes in the specified area.
    """
    def __init__(self, display, x, width, height):
        self.display = display
        self.x = x
        self.width = width
        self.height = height
        
        # Create 3 boxes with different positions, sizes, and directions
        self.boxes = []
        for _ in range(3):
            # Random position within the animation area
            box_x = self.x + random.randint(5, self.width - 5)
            box_y = random.randint(5, self.height - 5)
            
            # Random size between 3 and 6 pixels
            box_size = random.randint(3, 6)
            
            # Random direction (either -1 or 1 for both x and y)
            dx = random.choice([-1, 1])
            dy = random.choice([-1, 1])
            
            self.boxes.append({
                'x': box_x,
                'y': box_y,
                'size': box_size,
                'dx': dx,
                'dy': dy
            })
    
    def update(self):
        """Update the animation state and draw the frame."""
        # Clear the animation area
        for y in range(self.height):
            for x in range(self.width):
                self.display.pixel(self.x + x, y, 0)
        
        # Update and draw each box
        for box in self.boxes:
            # Update box position
            box['x'] += box['dx']
            box['y'] += box['dy']
            
            # Bounce off the walls
            half_size = box['size'] // 2
            if box['x'] - half_size <= self.x or box['x'] + half_size >= self.x + self.width:
                box['dx'] = -box['dx']
            if box['y'] - half_size <= 0 or box['y'] + half_size >= self.height:
                box['dy'] = -box['dy']
            
            # Draw the box
            self.draw_box(box['x'], box['y'], box['size'], 1)
    
    def draw_box(self, x, y, size, color):
        """Draw a square box centered at (x, y) with the given size."""
        half_size = size // 2
        
        # Draw the box
        for i in range(-half_size, half_size + 1):
            for j in range(-half_size, half_size + 1):
                # Ensure we're drawing within the animation area
                if (self.x <= x + i < self.x + self.width) and (0 <= y + j < self.height):
                    self.display.pixel(x + i, y + j, color)

# Logging functions
def log_message(message):
    """Write a message to the log file with timestamp."""
    try:
        # Check if log file exists and manage its size
        try:
            if LOG_FILE in os.listdir():
                # If file exists and is too large, truncate it
                if os.stat(LOG_FILE)[6] > MAX_LOG_SIZE:
                    with open(LOG_FILE, "w") as f:
                        f.write(f"Log file truncated at {get_time()}\n")
        except:
            # If error checking file, just continue
            pass
            
        # Append message to log file
        with open(LOG_FILE, "a") as f:
            f.write(f"{get_time()}: {message}\n")
    except Exception as e:
        print(f"Error writing to log file: {e}")

def log_error(e, phase):
    """Log an error with phase information."""
    error_msg = f"Error during {phase}: {e}"
    print(error_msg)
    log_message(error_msg)

def log_restart():
    """Log a system restart."""
    global restart_count
    restart_count += 1
    log_message(f"System restart #{restart_count}")
    print(f"System restart #{restart_count}")

# Error handling function
def handle_error(e, phase):
    """Handle errors and provide feedback."""
    log_error(e, phase)
    print("Will retry in 5 seconds...")
    
    # Blink LED rapidly to indicate error
    for _ in range(10):
        led.toggle()
        time.sleep(0.2)
    
    time.sleep(3)  # Additional delay before retry
    return False

# Initialize watchdog timer
def init_watchdog(timeout_ms=8000):
    """Initialize the watchdog timer with the specified timeout in milliseconds."""
    global watchdog
    try:
        watchdog = WDT(timeout=timeout_ms)
        log_message(f"Watchdog initialized with {timeout_ms}ms timeout")
        print(f"Watchdog initialized with {timeout_ms}ms timeout")
        return True
    except Exception as e:
        log_error(e, "watchdog initialization")
        print("Failed to initialize watchdog timer")
        return False

# Feed the watchdog timer
def feed_watchdog():
    """Feed the watchdog timer to prevent a reset."""
    global watchdog
    if watchdog:
        try:
            watchdog.feed()
        except Exception as e:
            print(f"Error feeding watchdog: {e}")

# Main function
def main():
    """Main program function."""
    global restart_count
    i2c = None
    bme = None
    display = None
    
    try:
        # Log system start
        log_restart()
        
        # Initialize watchdog timer (8 second timeout)
        init_watchdog(8000)
        
        # Initialize I2C bus for BME680
        print("Initializing I2C for BME680...")
        i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=100000)
        
        # Feed watchdog after I2C initialization
        feed_watchdog()
        
        # Scan for I2C devices
        devices = i2c.scan()
        if not devices:
            log_message("No I2C devices found. Check connections.")
            print("No I2C devices found. Check connections.")
            return False
        
        print(f"I2C devices found: {[hex(d) for d in devices]}")
        log_message(f"I2C devices found: {[hex(d) for d in devices]}")
        
        # Feed watchdog after I2C scan
        feed_watchdog()
        
        # Initialize BME680 sensor
        print("Initializing BME680 sensor...")
        
        # Try with address 0x77 first
        try:
            bme = BME680_I2C(i2c, address=0x77)
            print("BME680 initialized with address 0x77")
            log_message("BME680 initialized with address 0x77")
        except Exception as e:
            print(f"Failed to initialize with address 0x77: {e}")
            log_message(f"Failed to initialize with address 0x77: {e}")
            print("Trying with address 0x76...")
            
            # Feed watchdog before trying alternative address
            feed_watchdog()
            
            # Try with address 0x76
            try:
                bme = BME680_I2C(i2c, address=0x76)
                print("BME680 initialized with address 0x76")
                log_message("BME680 initialized with address 0x76")
            except Exception as e:
                return handle_error(e, "sensor initialization")
        
        # Feed watchdog after sensor initialization
        feed_watchdog()
        
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
        
        # Feed watchdog after SPI initialization
        feed_watchdog()
        
        # Initialize display
        print("Initializing SSD1306 display...")
        display = ssd1306.SSD1306_SPI(WIDTH, HEIGHT, spi, dc, rst, cs)
        
        # Set contrast for better visibility
        display.contrast(255)
        
        # Initialize animation with updated dimensions
        animation = BounceAnimation(display, ANIM_X, ANIM_WIDTH, ANIM_HEIGHT)
        
        # Feed watchdog after display initialization
        feed_watchdog()
        
        # Wait for sensor to stabilize
        print("Waiting for sensor to stabilize...")
        time.sleep(2)
        
        # Feed watchdog after waiting
        feed_watchdog()
        
        print("Initialization complete. Starting data collection...")
        log_message("Initialization complete. Starting data collection...")
        
        # Main loop
        while True:
            try:
                # Feed watchdog at the start of each loop iteration
                feed_watchdog()
                
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
                        log_message("Warning: One or more sensor readings returned None")
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
                    log_error(e, "sensor reading")
                    print(f"Error reading sensor data: {e}")
                    # Use last valid readings if available, or set defaults
                    global last_temperature, last_humidity, last_pressure, last_gas
                    temperature = last_temperature
                    humidity = last_humidity
                    pressure = last_pressure
                    gas = last_gas
                
                # Feed watchdog after sensor reading
                feed_watchdog()
                
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
                
                # Feed watchdog before animation update
                feed_watchdog()
                
                # Update and draw animation
                animation.update()
                
                # Draw a vertical line to separate the data and animation areas
                for y in range(HEIGHT):
                    display.pixel(ANIM_X - 1, y, 1)
                
                # Update display
                display.show()
                
                # Feed watchdog after display update
                feed_watchdog()
                
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
                
                # Wait for next update (0.5 seconds instead of 1 second)
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                print("\nProgram terminated by user")
                log_message("Program terminated by user")
                break
            except Exception as e:
                log_error(e, "main loop")
                handle_error(e, "data reading")
        
        return True
    
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
        log_message("Program terminated by user")
        return True
    except Exception as e:
        log_error(e, "initialization")
        return handle_error(e, "initialization")
    finally:
        # Clean up
        if display:
            try:
                display.fill(0)
                display.show()
                print("Display cleared on exit")
                log_message("Display cleared on exit")
            except Exception as e:
                error_msg = f"Error clearing display: {e}"
                print(error_msg)
                log_message(error_msg)

# Run the program
if __name__ == "__main__":
    print("===== BME680 Environmental Data Monitor with OLED Display =====")
    print("Version: 1.5 - Auto-start and Recovery Features")
    print("Press Ctrl+C to exit")
    print("======================================================")
    
    # Initialize the system
    try:
        # Check if we're running from boot.py
        is_auto_start = "boot.py" in os.listdir() and not sys.argv[0].endswith("bme680_oled_monitor_updated.py")
        if is_auto_start:
            print("Auto-start mode detected")
            log_message("Auto-start mode detected")
        
        # Create a startup message on the LED
        for _ in range(3):
            led.on()
            time.sleep(0.1)
            led.off()
            time.sleep(0.1)
        
        # Main program loop with restart capability
        while not main():
            print("Restarting program...")
            log_message("Restarting program due to error")
            time.sleep(1)
            
            # Blink LED to indicate restart
            for _ in range(5):
                led.on()
                time.sleep(0.1)
                led.off()
                time.sleep(0.1)
    
    except Exception as e:
        # Catch any unexpected exceptions at the top level
        error_msg = f"Critical error in main program: {e}"
        print(error_msg)
        try:
            log_message(error_msg)
        except:
            pass
        
        # Force a reset after a delay
        print("System will reset in 5 seconds...")
        time.sleep(5)
        try:
            reset()  # Hard reset the device
        except:
            # If reset fails, enter an infinite loop that will trigger the watchdog
            while True:
                pass
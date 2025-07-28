# BME680 Environmental Data Monitor with OLED Display

## Version 1.3 - Improved Formatting with Animation

This program reads data from a BME680 environmental sensor and displays it on a 128x64 OLED display.
The display shows date and time, temperature, humidity, absolute humidity, pressure, and gas resistance.

## Changes in Version 1.3

The following improvements have been made to enhance readability and visual appeal:

### 1. Improved Date and Time Formatting

- Added slashes (/) between year, month, and day
  - Before: `20250727` 
  - After: `2025/07/27`

- Added colons (:) between hours and minutes
  - Before: `235959` 
  - After: `23:59 59`

- Added a space between minutes and seconds
  - Before: `235959` 
  - After: `23:59 59`

### 2. Improved Measurement Value Formatting

Added spaces between all measurement values and their units:

- Temperature: 
  - Before: `25.0C` 
  - After: `25.0 C`

- Humidity: 
  - Before: `50.0%` 
  - After: `50.0 %`

- Absolute humidity: 
  - Before: `12.5g/m3` 
  - After: `12.5 g/m3`

- Pressure: 
  - Before: `1013hPa` 
  - After: `1013 hPa`

- Gas resistance: 
  - Before: `10.5kohm` 
  - After: `10.5k ohm`

### 3. Added Animation

- Created a 30x64 pixel animation area on the right side of the display
- Implemented a bouncing ball animation
- Added a vertical line to separate the data and animation areas

## Technical Implementation

### Date and Time Formatting

Modified the `get_time()` function to include formatting characters:

```python
def get_time():
    current_time = time.localtime()
    # Return date and time with improved formatting (slashes, colons, and spaces)
    return "{:04d}/{:02d}/{:02d} {:02d}:{:02d} {:02d}".format(
        current_time[0], current_time[1], current_time[2],
        current_time[3], current_time[4], current_time[5]
    )
```

### Animation Implementation

Added a `BounceAnimation` class to handle the animation in the right side of the display:

```python
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
```

## Hardware Connections

### BME680 sensor (I2C connection)
- VCC -> 3.3V (Pin 36)
- GND -> GND (Pin 38)
- SCL -> GP1 (Pin 2)
- SDA -> GP0 (Pin 1)

### SSD1306 OLED display (SPI connection)
- VCC -> 3.3V (Pin 36)
- GND -> GND (Pin 38)
- DIN (MOSI) -> GP3 (Pin 5)
- CLK (SCK) -> GP2 (Pin 4)
- CS -> GP6 (Pin 9)
- DC -> GP4 (Pin 6)
- RST -> GP5 (Pin 7)
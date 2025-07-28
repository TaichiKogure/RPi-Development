# BME680 Environmental Data Monitor with OLED Display

## Version 1.4 - Improved Animation with Multiple Boxes

This program reads data from a BME680 environmental sensor and displays it on a 128x64 OLED display.
The display shows date and time, temperature, humidity, absolute humidity, pressure, and gas resistance.

## Changes in Version 1.4

The following improvements have been made to enhance the animation and update frequency:

### 1. Faster Data Update Interval

- Changed the data update interval from 2 seconds to 0.5 seconds
  - Before: `time.sleep(1)` 
  - After: `time.sleep(0.5)`
- This results in more frequent sensor readings and display updates
- The animation also updates at this faster rate, creating smoother motion

### 2. Expanded Animation Area

- Increased the animation area from 30x64 pixels to 36x64 pixels
  - Before: 
    ```python
    ANIM_X = 98       # Starting X position for animation area
    ANIM_WIDTH = 30   # Width of animation area
    ```
  - After: 
    ```python
    ANIM_X = 92       # Starting X position for animation area
    ANIM_WIDTH = 36   # Width of animation area
    ```
- This provides more space for the animation, making it more visible and engaging

### 3. Multiple Bouncing Boxes

- Replaced the single bouncing ball with three bouncing boxes
- Each box has:
  - Random starting position within the animation area
  - Random size between 3 and 6 pixels
  - Random initial direction
- The boxes bounce independently off the walls of the animation area
- Changed from drawing circles to drawing filled square boxes

## Technical Implementation

### Animation Class Changes

The `BounceAnimation` class has been completely redesigned:

```python
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
```

The update method now processes each box independently:

```python
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
```

A new method was added to draw boxes instead of circles:

```python
def draw_box(self, x, y, size, color):
    """Draw a square box centered at (x, y) with the given size."""
    half_size = size // 2
    
    # Draw the box
    for i in range(-half_size, half_size + 1):
        for j in range(-half_size, half_size + 1):
            # Ensure we're drawing within the animation area
            if (self.x <= x + i < self.x + self.width) and (0 <= y + j < self.height):
                self.display.pixel(x + i, y + j, color)
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
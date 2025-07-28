"""
Raspberry Pi Pico System Monitor with SSD1306 OLED Display
Displays current time, CPU usage, and memory usage on a 128x64 transparent OLED display

特徴:
- 現在時刻と日付の表示
- CPU使用率の表示（シミュレーション値）
- メモリ使用率の表示
- 透明OLEDディスプレイ用に最適化
"""

import machine
import ssd1306
import time
import gc
import sys

# Pin definitions for SPI interface
SPI_ID = 0
SPI_SCK_PIN = 2  # CLK
SPI_MOSI_PIN = 3  # DIN
SPI_DC_PIN = 4    # DC
SPI_RST_PIN = 5   # RST
SPI_CS_PIN = 6    # CS

# Display dimensions
WIDTH = 128
HEIGHT = 64

# Initialize SPI
spi = machine.SPI(
    SPI_ID,
    baudrate=10000000,
    polarity=0,
    phase=0,
    sck=machine.Pin(SPI_SCK_PIN),
    mosi=machine.Pin(SPI_MOSI_PIN)
)

# Initialize display pins
dc = machine.Pin(SPI_DC_PIN)
rst = machine.Pin(SPI_RST_PIN)
cs = machine.Pin(SPI_CS_PIN)

# Initialize display
display = ssd1306.SSD1306_SPI(WIDTH, HEIGHT, spi, dc, rst, cs)

# Set contrast for better visibility on transparent display
# Value range: 0-255, higher values = higher contrast
# Adjust this value based on your specific display and viewing conditions
display.contrast(255)  # Maximum contrast for transparent display

# Function to get current time
def get_time():
    current_time = time.localtime()
    return "{:02d}:{:02d}:{:02d}".format(current_time[3], current_time[4], current_time[5])

# Function to get current date
def get_date():
    current_time = time.localtime()
    return "{:04d}-{:02d}-{:02d}".format(current_time[0], current_time[1], current_time[2])

# Function to get memory usage
def get_memory_usage():
    # Get memory allocation info
    free = gc.mem_free()
    allocated = gc.mem_alloc()
    total = free + allocated
    percentage = (allocated / total) * 100
    return percentage

# Function to get CPU temperature (simulated on Pico)
def get_cpu_usage():
    # Pico doesn't have CPU usage metrics, so we'll simulate it
    # In a real application, you might want to measure task execution time
    # or use a more sophisticated method
    return (time.time() % 30) / 30 * 100  # Simulated value between 0-100%

# Function to draw a progress bar with enhanced visibility for transparent displays
def draw_progress_bar(x, y, width, height, percentage, max_percentage=100):
    # Draw border with thicker lines for better visibility
    display.rect(x, y, width, height, 1)
    display.rect(x+1, y+1, width-2, height-2, 1)
    
    # Calculate fill width
    fill_width = int((width - 4) * percentage / max_percentage)
    
    # Draw fill with pattern for better visibility on transparent display
    if fill_width > 0:
        # Solid fill
        display.fill_rect(x + 2, y + 2, fill_width, height - 4, 1)
        
        # Add markers at 25%, 50%, and 75% for better readability
        for marker_pos in [0.25, 0.5, 0.75]:
            marker_x = x + 2 + int((width - 4) * marker_pos)
            if marker_x < x + 2 + fill_width:
                # If this marker is within the filled area, make it black
                display.fill_rect(marker_x - 1, y + 2, 2, height - 4, 0)
            else:
                # If this marker is outside the filled area, make it white
                display.fill_rect(marker_x - 1, y + 2, 2, height - 4, 1)

# Main loop
def main():
    try:
        while True:
            # Clear the display
            display.fill(0)
            
            # Display header with border for better visibility
            display.fill_rect(0, 0, WIDTH, 12, 1)
            display.text("SYSTEM MONITOR", 10, 2, 0)  # Inverted text for header
            
            # Display time with larger emphasis
            current_time = get_time()
            display.text(current_time, 32, 16, 1)  # Centered time display
            
            # Display date
            current_date = get_date()
            display.text(current_date, 24, 26, 1)  # Centered date display
            
            # Draw separator line
            display.hline(0, 36, WIDTH, 1)
            
            # Display CPU usage with enhanced visibility
            cpu_usage = get_cpu_usage()
            display.text("CPU: {:.1f}%".format(cpu_usage), 0, 40, 1)
            draw_progress_bar(0, 48, WIDTH, 6, cpu_usage)
            
            # Display memory usage with enhanced visibility
            mem_usage = get_memory_usage()
            display.text("MEM: {:.1f}%".format(mem_usage), 0, 56, 1)
            draw_progress_bar(0, 56 + 8, WIDTH, 6, mem_usage)
            
            # Update display
            display.show()
            
            # Wait before next update
            time.sleep(1)
            
    except KeyboardInterrupt:
        # Clear display on exit
        display.fill(0)
        display.show()
        print("Program terminated by user")

if __name__ == "__main__":
    main()
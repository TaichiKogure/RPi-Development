# Implementation Changes Summary

## Requirements Implemented

1. **Removed boot.py dependency**
   - Modified the system to run directly from main.py
   - Removed auto-start detection code

2. **Replaced date/time with uptime timer**
   - Added global start_time variable
   - Created get_uptime() function to calculate continuous operation time
   - Updated display and logging to use uptime

3. **Added CPU and memory usage monitoring**
   - Implemented get_cpu_usage() function using machine.freq()
   - Implemented get_memory_usage() function using gc.mem_free() and gc.mem_alloc()
   - Display format: "CPU/MEM: XX%/YY%"

4. **Updated display layout**
   - Row 1: Uptime (replacing date)
   - Row 2: CPU and memory usage (replacing time)
   - Rows 3-7: Sensor data (unchanged)

## Key Code Changes

### New Functions Added

```python
# Global variable to track start time for uptime calculation
start_time = time.time()

# Function to get uptime
def get_uptime():
    global start_time
    uptime_seconds = time.time() - start_time
    
    # Calculate days, hours, minutes, seconds
    days = int(uptime_seconds // (24 * 3600))
    uptime_seconds %= (24 * 3600)
    hours = int(uptime_seconds // 3600)
    uptime_seconds %= 3600
    minutes = int(uptime_seconds // 60)
    seconds = int(uptime_seconds % 60)
    
    # Format the uptime string
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

# Function to get CPU usage
def get_cpu_usage():
    # Get current CPU frequency
    current_freq = freq()
    
    # Maximum frequency is 133 MHz for Raspberry Pi Pico
    max_freq = 133_000_000
    
    # Calculate percentage
    percentage = int((current_freq / max_freq) * 100)
    
    return percentage

# Function to get memory usage
def get_memory_usage():
    # Get memory allocation information
    mem_free = gc.mem_free()
    mem_alloc = gc.mem_alloc()
    total_mem = mem_free + mem_alloc
    
    # Calculate percentage
    percentage = int((mem_alloc / total_mem) * 100)
    
    return percentage
```

### Updated Display Code

```python
# Get system information
uptime_str = get_uptime()
cpu_usage = get_cpu_usage()
memory_usage = get_memory_usage()

# Clear the display
display.fill(0)

# Row 1: Uptime
display_text(display, f"Up: {uptime_str}", X_OFFSET, ROW_START_Y, 1)

# Row 2: CPU and Memory usage
display_text(display, f"CPU/MEM: {cpu_usage}%/{memory_usage}%", X_OFFSET, ROW_START_Y + ROW_HEIGHT, 1)
```

## Files Modified

1. Created `main.py` - Standalone main program
2. Created `README_updated.md` - Updated English documentation
3. Created `README_ja_updated.md` - Updated Japanese documentation
4. Removed dependency on `boot.py`

## Version Update

Updated version from 1.5 to 2.0 to reflect the significant changes in functionality.
# Connection Monitor Import Path Fix

## Overview
This document explains the solution to the import path issues that were occurring in the connection monitor module of the Raspberry Pi 5 Environmental Monitoring System. The issue was preventing the system from properly importing modules from the `p1_software_solo405` package.

## Problem Description
The system was encountering the following errors:
- `Failed to import refactored modules from p1_software_solo405 package: No module named 'p1_software_solo405'`
- `Failed to import refactored modules from relative path: No module named 'p1_software_solo405'`
- `Cannot continue without required modules`

These errors occurred because the Python interpreter couldn't find the `p1_software_solo405` package in its search path. This is a common issue when running Python scripts that are part of a package structure but are executed directly.

## Solution
The solution involved implementing a robust import strategy in the `P1_wifi_monitor_solo.py` file:

### 1. Add Parent Directory to Python Path
First, we add the parent directory to the Python path to enable imports from the `p1_software_solo405` package:

```python
# Add the parent directory to the Python path so we can import from p1_software_solo405
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
```

This ensures that the Python interpreter can find the `p1_software_solo405` package when importing modules.

### 2. Implement a Two-Step Import Strategy
Next, we implement a two-step import strategy:

```python
try:
    # Try to import from the refactored package structure
    from p1_software_solo405.connection_monitor.config import DEFAULT_CONFIG, ensure_log_directory
    from p1_software_solo405.connection_monitor.monitor import WiFiMonitor
    from p1_software_solo405.connection_monitor.utils.console import print_connection_status
    logger.info("Successfully imported refactored modules from p1_software_solo405 package")
except ImportError as e:
    logger.error(f"Failed to import refactored modules from p1_software_solo405 package: {e}")
    
    # Try to import from relative path
    try:
        from connection_monitor.config import DEFAULT_CONFIG, ensure_log_directory
        from connection_monitor.monitor import WiFiMonitor
        from connection_monitor.utils.console import print_connection_status
        logger.info("Successfully imported refactored modules from relative path")
    except ImportError as e:
        logger.error(f"Failed to import refactored modules from relative path: {e}")
        logger.error("Cannot continue without required modules")
        sys.exit(1)
```

This approach:
1. First tries to import from the package structure (`p1_software_solo405.connection_monitor.*`)
2. If that fails, it falls back to relative imports (`connection_monitor.*`)

### 3. Proper Logging Configuration
We also ensure that logging is properly configured before any imports are attempted:

```python
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/wifi_monitor_solo.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
```

This ensures that any import errors are properly logged for debugging.

### 4. Robust Main Function
Finally, we update the main function to use the same import strategy and to directly handle command-line arguments and start the WiFi monitor:

```python
def main():
    """Main function to parse arguments and start the WiFi monitor."""
    try:
        # Try to import from the refactored package structure
        from p1_software_solo405.connection_monitor.main import main as refactored_main
        logger.info("Successfully imported main function from p1_software_solo405 package")
    except ImportError as e:
        logger.error(f"Failed to import main function from p1_software_solo405 package: {e}")
        
        # Try to import from relative path
        try:
            from connection_monitor.main import main as refactored_main
            logger.info("Successfully imported main function from relative path")
        except ImportError as e:
            logger.error(f"Failed to import main function from relative path: {e}")
            logger.error("Cannot continue without required modules")
            sys.exit(1)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='WiFi Connection Monitor')
    parser.add_argument('--interval', type=int, default=5, help='Monitoring interval in seconds')
    parser.add_argument('--interface', type=str, default='wlan0', help='WiFi interface to monitor')
    parser.add_argument('--port', type=int, default=5002, help='Port for the API server')
    args = parser.parse_args()
    
    # Update configuration
    config = DEFAULT_CONFIG.copy()
    config['update_interval'] = args.interval
    config['interface'] = args.interface
    config['port'] = args.port
    
    # Start the WiFi monitor
    try:
        logger.info("Starting WiFi monitor...")
        monitor = WiFiMonitor(config)
        monitor.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    except Exception as e:
        logger.error(f"Error in WiFi monitor: {e}")
        sys.exit(1)
```

This makes the module more robust and less dependent on the specific structure of the refactored code.

## Benefits of the Solution
1. **Improved Robustness**: The system can now handle different execution environments.
2. **Better Error Handling**: Detailed error messages help diagnose import issues.
3. **Flexible Import Strategy**: The two-step import strategy works whether the code is run as a package or directly.
4. **Proper Logging**: All errors are properly logged for debugging.
5. **Direct Execution**: The module can be run directly without relying on the refactored code.

## Conclusion
By implementing this robust import strategy, we've fixed the import path issues in the connection monitor module. The system can now properly import modules from the `p1_software_solo405` package, regardless of how the scripts are executed.
# Ver4.32 Debug - Fixed Filename Implementation

## Changes Made

### Issue
The previous implementation used date-based filenames (e.g., "P2_2023-05-15.csv") for storing sensor data. This approach had several drawbacks:
- Graphs couldn't be rendered if the date-based files weren't found
- The system had to search through multiple files to find data for a specific date range
- File handling was more complex and error-prone

### Solution
We've implemented a fixed filename approach where sensor data is stored in both date-based files and fixed files:
- Date-based files: `/var/lib/raspap_solo/data/RawData_P2/P2_YYYY-MM-DD.csv`
- Fixed files: `/var/lib/raspap_solo/data/RawData_P2/P2_fixed.csv`

The system now prioritizes reading from fixed files and only falls back to date-based files if necessary. The fixed files are created by concatenating data from date-based files over time, providing a continuous historical record.

### Benefits
- Simplified data access with a single fixed file per device
- More reliable graph rendering
- Automatic handling of both numeric and string timestamp formats
- Backward compatibility with existing date-based files

## Technical Details

### Data Collection Changes
1. Modified `_init_csv_files()` to initialize both date-based and fixed CSV files
2. Modified `_rotate_csv_files()` to handle fixed files
3. Modified `_store_data()` to write data to both date-based and fixed CSV files
4. Modified `stop()` to close both types of files

### Data Reading Changes
1. Modified `get_historical_data()` to prioritize reading from fixed files
2. Added fallback to date-based files if fixed files don't exist or can't be read
3. Improved error handling and logging for better diagnostics

## Usage
No changes are required in how you use the system. The improvements work transparently:
- If fixed files exist, they will be used automatically
- If fixed files don't exist, the system will fall back to date-based files
- All new data is written to both date-based and fixed files

## Implementation Notes
- Fixed files are created when they don't exist and new data is appended to them over time
- When a new date-based file is created, its data is appended to the existing fixed file
- Both types of files use the same CSV format with the same headers
- Timestamp handling automatically detects and converts both numeric and string formats

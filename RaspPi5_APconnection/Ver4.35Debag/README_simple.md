# Ver4.35 - Simplified Web Interface for Environmental Data Visualization

## Overview

This update introduces a simplified web interface for visualizing environmental data collected from P2 and P3 sensor nodes. The new implementation addresses several issues with the previous version:

1. **Graph Scaling Issues**: Graphs no longer start at zero by default, instead using proper Y-axis auto-scaling based on the actual data range
2. **Loading Graph Message**: The "Loading Graph" message is now properly cleared once data is loaded
3. **Connection Status Display**: Real-time connection status for P2 and P3 is now displayed
4. **Simplified Code Structure**: The code has been reorganized for better maintainability and performance

## Key Features

- **Direct Data Reading**: Reads directly from fixed CSV files (`P2_fixed.csv` and `P3_fixed.csv`)
- **Proper Graph Scaling**: Y-axis ranges are automatically set based on the actual data values
- **Toggle Device Data**: Show/hide P2 and P3 data independently
- **Time Range Selection**: View data for different time periods (1 day, 3 days, 7 days, etc.)
- **Auto-refresh**: Automatically update graphs at configurable intervals
- **Data Export**: Export data for specific devices and date ranges
- **Connection Status**: View real-time connection status for P2 and P3 sensor nodes
- **Responsive Design**: Works well on both desktop and mobile devices

## Technical Details

### Data Reading

The new implementation reads data directly from the fixed CSV files:
```
/var/lib/raspap_solo/data/RawData_P2/P2_fixed.csv
/var/lib/raspap_solo/data/RawData_P3/P3_fixed.csv
```

The timestamp handling has been improved to automatically detect and convert both numeric and string timestamp formats:

```python
if df['timestamp'].dtype == 'int64' or df['timestamp'].dtype == 'float64':
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
else:
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
```

### Graph Generation

Graphs are generated using Plotly.js with proper Y-axis auto-scaling:

```python
# Set Y-axis to auto-range
fig.update_yaxes(autorange=True)
```

The code also validates data to ensure there are at least 2 unique non-NaN values for each parameter before attempting to plot:

```python
p2_values = df_p2[parameter].dropna()
if len(p2_values) > 0 and len(p2_values.unique()) >= 2:
    # Add trace to graph
else:
    logger.warning(f"P2 data for {parameter} has insufficient unique values")
```

### Frontend

The frontend uses a single HTML template with embedded JavaScript for interactivity. Key features include:

- Bootstrap 5 for responsive layout
- Plotly.js for interactive graphs
- jQuery for AJAX requests
- Auto-refresh functionality with configurable intervals
- Modal dialog for data export

## Usage

### Running the Application

To run the simplified web interface:

```bash
python3 P1_app_simple.py [--port PORT] [--data-dir DIR] [--debug]
```

Options:
- `--port PORT`: Specify the port to listen on (default: 80)
- `--data-dir DIR`: Specify the directory to read data from (default: /var/lib/raspap_solo/data)
- `--debug`: Enable debug mode

### Using the Dashboard

1. **Toggle Device Data**:
   - Use the checkboxes to show/hide P2 and P3 data

2. **Change Time Range**:
   - Select from 1 day, 3 days, 7 days, 14 days, or 30 days

3. **Auto-refresh**:
   - Choose an auto-refresh interval or turn it off
   - Click "Refresh Now" to manually refresh the data

4. **Export Data**:
   - Click "Export Data" to open the export dialog
   - Select a device (P2, P3, or All)
   - Choose a date range
   - Click "Export" to download the data as a CSV file

## Implementation Notes

This implementation is designed to be a drop-in replacement for the existing web interface. It maintains all the functionality of the previous version while addressing the identified issues.

To switch between the original and simplified versions, you can use the following commands:

```bash
# Use the original version
python3 P1_app_solo.py

# Use the simplified version
python3 P1_app_simple.py
```

Both versions can coexist in the same directory without conflicts.
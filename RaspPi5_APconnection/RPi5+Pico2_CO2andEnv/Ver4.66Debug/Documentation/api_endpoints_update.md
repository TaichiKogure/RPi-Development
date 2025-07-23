# API Endpoints Update

## Overview

This document describes the changes made to address the issue where sensor data was not being updated due to missing API endpoints. The following endpoints were added to the Flask application:

1. `/api/device/<device_id>` - Returns the latest data for a specific device (P2 or P3)
2. `/api/graphs` - Returns CSV data from sensor files with processing

## Implementation Details

### 1. Added `get_latest_device_data` method to `DataManager` class

A new method was added to the `DataManager` class to retrieve the latest data for a specific device:

```python
def get_latest_device_data(self, device_id):
    """
    Get the latest data for the specified device.
    
    Args:
        device_id (str): The device ID to get data for
        
    Returns:
        dict: The latest data for the specified device
    """
    try:
        # Get the latest data for all devices
        all_data = self.get_latest_data()
        
        # Extract the data for the specified device
        if device_id in all_data:
            return all_data[device_id]
        else:
            logger.warning(f"No data found for device {device_id}")
            return None
    except Exception as e:
        logger.error(f"Error getting latest data for device {device_id}: {e}")
        return None
```

This method uses the existing `get_latest_data()` method to retrieve data for all devices and then extracts the data for the specified device.

### 2. Added `/api/device/<device_id>` endpoint to `APIRoutes` class

A new endpoint was added to the `APIRoutes` class to handle requests for device-specific data:

```python
@self.app.route('/api/device/<device_id>', methods=['GET'])
def get_device_data(device_id):
    """Get the latest data for the specified device."""
    try:
        # Get the latest data for the specified device
        data = self.data_manager.get_latest_device_data(device_id.upper())
        if data:
            return jsonify(data)
        else:
            return jsonify({'error': 'Device not found'}), 404
    except Exception as e:
        logger.error(f"Error getting data for device {device_id}: {e}")
        return jsonify({"error": str(e)}), 500
```

This endpoint uses the new `get_latest_device_data` method to retrieve data for the specified device and returns it as JSON. If the device is not found, it returns a 404 error.

### 3. Added `/api/graphs` endpoint to `APIRoutes` class

A new endpoint was added to the `APIRoutes` class to handle requests for graph data:

```python
@self.app.route('/api/graphs', methods=['GET'])
def get_graph_data_csv():
    """Get CSV data for graphs with processing."""
    try:
        # Get query parameters
        days = request.args.get('days', default=1, type=int)
        show_p2 = request.args.get('show_p2', default='true').lower() == 'true'
        show_p3 = request.args.get('show_p3', default='true').lower() == 'true'
        
        result = {}
        
        # Process P2 data if requested
        if show_p2:
            df_p2 = self.data_manager.get_historical_data("P2", days)
            if df_p2 is not None and not df_p2.empty:
                # Convert to JSON structure
                result['P2'] = df_p2.to_json(orient='records', date_format='iso')
        
        # Process P3 data if requested
        if show_p3:
            df_p3 = self.data_manager.get_historical_data("P3", days)
            if df_p3 is not None and not df_p3.empty:
                # Convert to JSON structure
                result['P3'] = df_p3.to_json(orient='records', date_format='iso')
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting graph data CSV: {e}")
        return jsonify({"error": str(e)}), 500
```

This endpoint retrieves historical data for P2 and P3 devices based on the query parameters and returns it as JSON. It includes the following features:

1. CSV data is converted to JSON structure (using pandas' to_json method)
2. Days parameter is used to filter data for the specified number of days
3. show_p2 and show_p3 parameters are used to control which devices' data is included
4. File existence and format checks are handled by the `get_historical_data` method

## Testing

To test these changes, you can use the following curl commands:

```bash
# Get the latest data for P2
curl http://localhost:5000/api/device/P2

# Get the latest data for P3
curl http://localhost:5000/api/device/P3

# Get graph data for the last day
curl http://localhost:5000/api/graphs?days=1&show_p2=true&show_p3=true

# Get graph data for the last 7 days, P2 only
curl http://localhost:5000/api/graphs?days=7&show_p2=true&show_p3=false
```

## Conclusion

These changes should resolve the issue where sensor data was not being updated due to missing API endpoints. The frontend can now access `/api/device/P2` and `/api/device/P3` to retrieve the latest data for each device, and `/api/graphs` to retrieve historical data for graphing.
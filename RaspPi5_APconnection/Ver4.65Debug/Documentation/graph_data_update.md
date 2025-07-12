# Graph Data Update

## Overview

This document describes the changes made to address the issue where sensor data was not being automatically updated and graphs were not being drawn. The following changes were made:

1. Added a `generate_graph_data()` method to the `GraphGenerator` class to process and structure data for graphs
2. Modified the `/api/graphs` endpoint to use the `generate_graph_data()` method
3. Updated the JavaScript function `loadGraphs()` in the dashboard.html template to use the unified `/api/graphs` endpoint
4. Added automatic refresh functionality for graphs

## Implementation Details

### 1. Added `generate_graph_data()` method to `GraphGenerator` class

A new method was added to the `GraphGenerator` class to process and structure data for graphs:

```python
def generate_graph_data(self, days=1, show_p2=True, show_p3=True):
    """
    Generate structured data for graphs.
    
    Args:
        days (int, optional): Number of days of data to retrieve. Defaults to 1.
        show_p2 (bool, optional): Whether to include P2 data. Defaults to True.
        show_p3 (bool, optional): Whether to include P3 data. Defaults to True.
        
    Returns:
        dict: Structured data for graphs
    """
    try:
        # Get historical data
        from web_interface.data.data_manager import DataManager
        data_manager = DataManager(self.config)
        
        df_p2 = data_manager.get_historical_data("P2", days) if show_p2 else None
        df_p3 = data_manager.get_historical_data("P3", days) if show_p3 else None
        
        # Check if we have any data
        if (df_p2 is None or df_p2.empty) and (df_p3 is None or df_p3.empty):
            logger.warning("No data available for graphs")
            return {}
        
        # Define parameters
        parameters = ["temperature", "humidity", "absolute_humidity", "co2", "pressure", "gas_resistance"]
        
        # Initialize result dictionary
        result = {}
        
        # Process P2 data if available
        if show_p2 and df_p2 is not None and not df_p2.empty:
            # Convert timestamp to list for JSON serialization
            timestamps = df_p2['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
            
            # Create data structure for P2
            p2_data = {
                'timestamp': timestamps
            }
            
            # Add data for each parameter
            for param in parameters:
                if param in df_p2.columns:
                    p2_data[param] = df_p2[param].tolist()
            
            # Add to result
            result['P2'] = p2_data
        
        # Process P3 data if available
        if show_p3 and df_p3 is not None and not df_p3.empty:
            # Convert timestamp to list for JSON serialization
            timestamps = df_p3['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
            
            # Create data structure for P3
            p3_data = {
                'timestamp': timestamps
            }
            
            # Add data for each parameter
            for param in parameters:
                if param in df_p3.columns:
                    p3_data[param] = df_p3[param].tolist()
            
            # Add to result
            result['P3'] = p3_data
        
        return result
    except Exception as e:
        logger.error(f"Error generating graph data: {e}")
        return {}
```

This method retrieves historical data for P2 and P3 devices, processes it, and returns it in a structured format that can be used by the frontend to create graphs.

### 2. Modified `/api/graphs` endpoint to use `generate_graph_data()`

The `/api/graphs` endpoint was modified to use the `generate_graph_data()` method:

```python
@self.app.route('/api/graphs', methods=['GET'])
def get_graph_data_csv():
    """Get structured data for graphs using GraphGenerator."""
    try:
        # Get query parameters
        days = request.args.get('days', default=1, type=int)
        show_p2 = request.args.get('show_p2', default='true').lower() == 'true'
        show_p3 = request.args.get('show_p3', default='true').lower() == 'true'

        # Use GraphGenerator to get structured data
        result = self.graph_generator.generate_graph_data(days=days, show_p2=show_p2, show_p3=show_p3)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Graph data generation failed: {e}")
        return jsonify({"error": str(e)}), 500
```

This endpoint now uses the `generate_graph_data()` method to retrieve structured data for graphs and returns it as JSON.

### 3. Updated `loadGraphs()` function in dashboard.html

The JavaScript function `loadGraphs()` in the dashboard.html template was updated to use the unified `/api/graphs` endpoint:

```javascript
// Function to load graphs (updated to hit unified API)
function loadGraphs() {
    const days = $('#days-select').val() || 1;
    const showP2 = $('#show-p2').is(':checked');
    const showP3 = $('#show-p3').is(':checked');
    
    $.get(`/api/graphs?days=${days}&show_p2=${showP2}&show_p3=${showP3}`, function(data) {
        const parameters = [
            { id: 'temperature', name: 'temperature' },
            { id: 'humidity', name: 'humidity' },
            { id: 'absolute-humidity', name: 'absolute_humidity' },
            { id: 'co2', name: 'co2' },
            { id: 'pressure', name: 'pressure' },
            { id: 'gas-resistance', name: 'gas_resistance' }
        ];
        
        parameters.forEach(param => {
            const traces = [];
            
            // Add P2 data if available
            if (data.P2 && data.P2[param.name]) {
                traces.push({
                    x: data.P2.timestamp,
                    y: data.P2[param.name],
                    name: 'P2',
                    mode: 'lines+markers',
                    type: 'scatter',
                    line: { color: 'blue' }
                });
            }
            
            // Add P3 data if available
            if (data.P3 && data.P3[param.name]) {
                traces.push({
                    x: data.P3.timestamp,
                    y: data.P3[param.name],
                    name: 'P3',
                    mode: 'lines+markers',
                    type: 'scatter',
                    line: { color: 'red' }
                });
            }
            
            // Create layout
            const layout = {
                title: param.name.replace('_', ' ').charAt(0).toUpperCase() + param.name.replace('_', ' ').slice(1),
                xaxis: { title: 'Time', type: 'date' },
                yaxis: { title: param.name.replace('_', ' ').charAt(0).toUpperCase() + param.name.replace('_', ' ').slice(1) },
                margin: { l: 50, r: 50, t: 50, b: 50 },
                hovermode: 'closest',
                showlegend: true
            };
            
            // Plot the graph
            Plotly.newPlot(`${param.id}-graph`, traces, layout);
        });
    });
}
```

This function now makes a single AJAX request to `/api/graphs` with the appropriate parameters, processes the response data to create traces for each parameter and device, creates a layout for each graph, and uses Plotly to render the graphs.

### 4. Added automatic refresh functionality for graphs

Automatic refresh functionality was added for graphs by adding the following line to the `$(document).ready()` function:

```javascript
setInterval(loadGraphs, 10000); // Refresh graphs every 10 seconds
```

This ensures that the graphs are automatically updated with the latest data every 10 seconds.

## Testing

To test these changes, you can:

1. Open the dashboard in a web browser
2. Verify that the graphs are displayed correctly
3. Wait for 10 seconds and verify that the graphs are automatically updated with the latest data
4. Change the time range or toggle the P2/P3 checkboxes and verify that the graphs are updated accordingly

## Conclusion

These changes should resolve the issue where sensor data was not being automatically updated and graphs were not being drawn. The graphs are now automatically updated every 10 seconds, and the data is properly structured for display.
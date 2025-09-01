# GraphGenerator Import Fix

## Overview

This document describes the changes made to address the issue where the GraphGenerator class was failing with the error "No module named 'web_interface'" when trying to generate graph data. This error was occurring in the `generate_graph_data()` method when it tried to import the DataManager class.

## Issue Description

The GraphGenerator class was using an absolute import path to import the DataManager class:

```python
from web_interface.data.data_manager import DataManager
```

This import statement assumes that 'web_interface' is in the Python path, which may not be the case depending on how the application is run. This was causing the error:

```
Error generating graph data: No module named 'web_interface'
```

## Solution

The import statement in the `generate_graph_data()` method was modified to handle different import scenarios:

1. First, try a relative import:
   ```python
   from ..data.data_manager import DataManager
   ```

2. If that fails, try an absolute import with the package prefix:
   ```python
   from p1_software_solo405.web_interface.data.data_manager import DataManager
   ```

3. As a last resort, try the original absolute import:
   ```python
   from web_interface.data.data_manager import DataManager
   ```

Each import attempt is wrapped in a try-except block to gracefully handle import errors, and logging statements are added to track which import method succeeds.

## Implementation Details

The following changes were made to the `generate_graph_data()` method in the GraphGenerator class:

```python
# Get historical data
try:
    # Try relative import first
    from ..data.data_manager import DataManager
    data_manager = DataManager(self.config)
    logger.info("Successfully imported DataManager using relative import")
except ImportError:
    # Fall back to absolute import if relative import fails
    try:
        from p1_software_solo405.web_interface.data.data_manager import DataManager
        data_manager = DataManager(self.config)
        logger.info("Successfully imported DataManager using absolute import with p1_software_Zero prefix")
    except ImportError:
        # Try another absolute import path as a last resort
        from web_interface.data.data_manager import DataManager
        data_manager = DataManager(self.config)
        logger.info("Successfully imported DataManager using absolute import")
```

## Testing

To test these changes, you can:

1. Run the web interface and navigate to the dashboard
2. Check the logs to see which import method succeeded
3. Verify that the graphs are displayed correctly

## Conclusion

These changes should resolve the issue where the GraphGenerator class was failing with the error "No module named 'web_interface'" when trying to generate graph data. The modified import statement handles different import scenarios, making the code more robust and less dependent on the specific Python path configuration.
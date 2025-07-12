# Integration of P1_data_collector_solo_new.py with start_p1_solo.py

## Overview
This document explains the integration of the new modular data collection system (`P1_data_collector_solo_new.py`) with the unified startup script (`start_p1_solo.py`). The integration ensures that the startup script correctly launches the new data collection module instead of the deprecated monolithic version.

## Changes Made

### 1. Updated Script Reference
The startup script was updated to reference the new data collection module:

```python
# Old reference
DATA_COLLECTOR_SCRIPT = os.path.join(SCRIPT_DIR, "data_collection", "P1_data_collector_solo.py")

# New reference
DATA_COLLECTOR_SCRIPT = os.path.join(SCRIPT_DIR, "data_collection", "P1_data_collector_solo_new.py")
```

### 2. Enhanced Command Line Arguments
The command to launch the data collection module was enhanced to explicitly include the listen port:

```python
# Old command
cmd = [
    VENV_PYTHON, DATA_COLLECTOR_SCRIPT,
    "--data-dir", config["data_dir"],
    "--api-port", str(config["api_port"])
]

# New command
cmd = [
    VENV_PYTHON, DATA_COLLECTOR_SCRIPT,
    "--data-dir", config["data_dir"],
    "--listen-port", "5000",  # Default listen port for data collector
    "--api-port", str(config["api_port"])
]
```

This makes the integration more explicit and allows for customization of the listen port if needed in the future.

### 3. Updated Version Numbers
The version numbers in status messages were updated to reflect the current version:

```python
# Old version
status_message = "\n===== P1 Services Status (Ver 4.0) =====\n"
print("\n===== Raspberry Pi 5 Environmental Monitor Ver4.0 =====")

# New version
status_message = "\n===== P1 Services Status (Ver 4.62) =====\n"
print("\n===== Raspberry Pi 5 Environmental Monitor Ver4.62 =====")
```

## Verification
The integration was verified by checking:
1. The startup script correctly references the new data collection module
2. The command line arguments passed to the data collection module are correct
3. The data collection module accepts these arguments
4. The version numbers in status messages are up to date

## Benefits of the Integration
1. **Improved Maintainability**: The system now uses the modular data collection module, which is easier to maintain and extend.
2. **Better Error Handling**: The new module has improved error handling and logging.
3. **Enhanced Modularity**: The system is now more modular, with clear separation of concerns.
4. **Up-to-date Version Information**: Status messages now show the correct version number.

## Usage
The integrated system can be used in the same way as before:

```bash
sudo ~/envmonitor-venv/bin/python3 start_p1_solo.py
```

No changes to the usage are required, as the integration is transparent to the user.
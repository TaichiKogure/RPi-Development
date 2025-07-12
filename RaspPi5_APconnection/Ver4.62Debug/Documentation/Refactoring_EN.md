# Data Collection Module Refactoring

## Overview
This document explains the refactoring of the data collection module in the Raspberry Pi 5 Environmental Monitoring System. The refactoring involved moving functionality from a single monolithic file (`P1_data_collector_solo.py`) to a modular structure with separate components organized in subdirectories.

## Changes Made

### 1. Modular Structure
The original monolithic file `P1_data_collector_solo.py` has been replaced with a modular structure:

- **Main Entry Point**: `P1_data_collector_solo_new.py` - A lightweight wrapper that imports and uses the refactored modules
- **Subdirectories**:
  - `api/` - API server and routes for accessing collected data
  - `network/` - Socket server for receiving data from sensor nodes
  - `processing/` - Data validation and calculation functions
  - `storage/` - CSV file management and in-memory data storage

### 2. Component Breakdown

#### API Module (`api/`)
- `server.py` - Flask server setup for the data collection API
- `routes.py` - API route handlers for accessing collected data

#### Network Module (`network/`)
- `server.py` - Socket server for receiving data from sensor nodes

#### Processing Module (`processing/`)
- `calculation.py` - Functions for calculating derived values (e.g., absolute humidity)
- `validation.py` - Functions for validating received data

#### Storage Module (`storage/`)
- `csv_manager.py` - Functions for managing CSV files (creation, rotation, cleanup)
- `data_store.py` - In-memory storage for quick access to the latest data

### 3. Configuration
- `config.py` - Configuration settings and utility functions

### 4. Main Integration
- `main.py` - Integrates all components to collect and store data from sensor nodes

## Benefits of the Refactoring

1. **Improved Maintainability**: Each component has a single responsibility, making the code easier to understand and maintain.
2. **Better Testability**: Components can be tested in isolation, making it easier to write unit tests.
3. **Enhanced Modularity**: Components can be reused or replaced independently.
4. **Clearer Structure**: The code structure now reflects the logical organization of the system.
5. **Easier Collaboration**: Multiple developers can work on different components simultaneously.

## Usage

The new module can be used in the same way as the original:

```bash
python3 P1_data_collector_solo_new.py [--data-dir DIR] [--listen-port PORT] [--api-port PORT]
```

## Implementation Details

### Import Strategy
The module uses a two-step import strategy:
1. First, it tries to import from the package structure (`p1_software_solo405.data_collection.*`)
2. If that fails, it falls back to relative imports (`data_collection.*`)

This ensures the module works both when installed as a package and when run directly.

### Error Handling
The module includes comprehensive error handling:
1. Import errors are caught and logged
2. Startup errors are caught and logged
3. Runtime errors are caught and logged
4. The system shuts down gracefully on errors or keyboard interrupts

### Logging
The module uses Python's logging system to log information, warnings, and errors to both the console and a log file.

## Migration
The original `P1_data_collector_solo.py` file has been deprecated and will be removed in a future update. All functionality has been moved to the new modular structure.
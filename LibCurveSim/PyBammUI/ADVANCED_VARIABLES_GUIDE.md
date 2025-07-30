# Advanced Variables Tab - User Guide

## Overview
The Advanced Variables tab provides a powerful interface for exploring and customizing PyBamm model variables. This feature allows users to:
- Browse all available variables in PyBamm models (DFN, SPM, SPMe)
- Search and filter variables by name or category
- Set custom values for specific variables
- Run simulations with customized variable parameters
- Compare results with different variable configurations

## Features

### 1. Model Selection
- Choose from three PyBamm models:
  - **DFN (Doyle-Fuller-Newman)**: Most detailed electrochemical model
  - **SPM (Single Particle Model)**: Simplified model for faster computation
  - **SPMe (Single Particle Model with Electrolyte)**: Balance between detail and speed

### 2. Variable Browser
- **Search functionality**: Find variables by typing keywords
- **Category filtering**: Filter variables by type (e.g., "Current", "Voltage", "Temperature")
- **Variable list**: Scrollable list showing all available variables
- **Variable count**: Display total number of variables for selected model

### 3. Variable Customization
- **Variable selection**: Click on variables to select them for customization
- **Value input**: Set custom numerical values for selected variables
- **Unit display**: Shows appropriate units for each variable
- **Validation**: Input validation to ensure proper numerical values

### 4. Simulation Controls
- **Parameter integration**: Combines custom variables with standard simulation parameters
- **Simulation execution**: Run simulations with customized variable values
- **Progress tracking**: Visual feedback during simulation execution
- **Error handling**: Graceful handling of simulation errors with informative messages

### 5. Results Visualization
- **Multiple plot types**: 
  - Voltage vs Time
  - Current vs Time
  - Voltage vs Capacity
  - Power vs Time
- **Comparison capability**: Compare results from different variable configurations
- **Interactive plots**: Zoom, pan, and examine data points
- **Export functionality**: Save plots and data for further analysis

## How to Use

### Step 1: Select Model
1. Open the "高度な変数" (Advanced Variables) tab
2. Choose your desired model from the dropdown (DFN, SPM, or SPMe)
3. Click "変数を読み込み" (Load Variables) to populate the variable list

### Step 2: Browse and Search Variables
1. Use the search box to find specific variables (e.g., "voltage", "current", "temperature")
2. Apply category filters to narrow down the variable list
3. Browse through the complete list of available variables

### Step 3: Customize Variables
1. Select variables from the list by clicking on them
2. Enter custom values in the "変数値設定" (Variable Value Settings) section
3. Verify that your values are within reasonable ranges
4. Add multiple variables as needed

### Step 4: Run Simulation
1. Set basic simulation parameters (time, current, etc.) if needed
2. Click "シミュレーション実行" (Run Simulation) to start the simulation
3. Monitor the progress bar and status messages
4. Wait for the simulation to complete

### Step 5: Analyze Results
1. View the generated plots in the visualization area
2. Use the plot controls to change visualization types
3. Compare results with previous simulations
4. Export data or plots if needed

## Variable Categories

The PyBamm models contain variables in several categories:

### Electrical Variables
- Terminal voltage
- Current density
- Electric potential
- Resistance values

### Thermal Variables
- Temperature distributions
- Heat generation rates
- Thermal conductivity

### Chemical Variables
- Concentration profiles
- Reaction rates
- Diffusion coefficients

### Mechanical Variables
- Stress and strain
- Volume changes
- Mechanical properties

### Geometric Variables
- Electrode thicknesses
- Particle sizes
- Porosity values

## Tips and Best Practices

### Variable Selection
- Start with well-known variables like "Terminal voltage [V]" or "Current [A]"
- Use descriptive search terms to find relevant variables
- Check units carefully when setting custom values

### Value Setting
- Use physically reasonable values (e.g., positive values for capacities)
- Consider the typical ranges for battery parameters
- Start with small changes from default values

### Simulation Strategy
- Begin with shorter simulation times when testing new variable configurations
- Compare results with baseline simulations using default values
- Document successful variable combinations for future use

### Troubleshooting
- If simulation fails, check that all custom values are reasonable
- Verify that variable names are correctly spelled
- Try reducing the number of customized variables if errors occur

## Integration with Other Tabs

### Simulation Tab
- Basic parameters set in the Simulation tab are respected
- Advanced variables supplement rather than replace basic parameters
- Results can be compared across different tabs

### Export Tab
- Simulation results from Advanced Variables can be exported
- Data includes both standard and custom variable results
- Export formats support all visualization types

## Technical Notes

### Performance Considerations
- More complex models (DFN) take longer to simulate
- Large numbers of custom variables may increase simulation time
- Consider using SPM for rapid prototyping

### Compatibility
- Works with PyBamm version 23.5 and later
- Requires matplotlib for visualization
- Compatible with all supported operating systems

### Limitations
- Some variables may be read-only or calculated internally
- Extreme values may cause simulation convergence issues
- Not all variable combinations are physically meaningful

## Examples

### Example 1: Custom Voltage Limits
1. Select DFN model
2. Search for "voltage cut-off"
3. Set custom upper and lower voltage limits
4. Run simulation to see effect on capacity

### Example 2: Temperature Study
1. Choose SPMe model
2. Find temperature-related variables
3. Set different ambient temperatures
4. Compare thermal behavior across conditions

### Example 3: Current Profile Analysis
1. Use SPM model for speed
2. Locate current-related variables
3. Set custom current profiles
4. Analyze voltage response characteristics

## Support and Feedback

For questions or issues with the Advanced Variables functionality:
- Check the console output for detailed error messages
- Verify PyBamm installation and version compatibility
- Consult PyBamm documentation for variable descriptions
- Report bugs or feature requests through the project repository

---

*This guide covers the Advanced Variables tab functionality added to the PyBamm UI application. The feature provides powerful customization capabilities while maintaining ease of use for both beginners and advanced users.*
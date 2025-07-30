# Enhanced Advanced Variables Tab - User Guide

## Overview

The Enhanced Advanced Variables Tab provides comprehensive parameter modification capabilities for PyBamm battery simulations. This enhanced version includes visual indicators, custom preset management, validation, error handling, and extended parameter support.

## New Features

### 1. Parameter Modification with Visual Indicators

- **Color-coded parameters**: 
  - 🟡 **Orange background**: Modified parameters
  - 🔴 **Red background**: Parameters with validation errors
  - ⚪ **White background**: Normal parameters

- **Double-click editing**: Double-click any parameter in the list to edit its value
- **Real-time validation**: Parameters are validated as you modify them
- **Original value tracking**: See both current and original values side-by-side

### 2. Custom Preset Management

- **Save custom presets**: Save your modified parameter sets with custom names
- **Load custom presets**: Reload your saved parameter configurations
- **Delete presets**: Remove unwanted custom presets
- **JSON storage**: Presets are stored in `custom_presets.json` for persistence

### 3. Enhanced Parameter Validation

- **Type-specific validation**:
  - **Capacity**: Must be positive, reasonable range (≤ 1000 Ah)
  - **Current**: Reasonable range (≤ 100 A)
  - **Voltage**: Non-negative, reasonable range (≤ 10 V)
  - **Temperature**: Valid range (200-400 K)
  - **Thickness**: Positive values, reasonable range
  - **Porosity/Fractions**: Must be between 0 and 1

- **Consistency checking**:
  - Electrode thickness validation
  - C-rate warnings for high current/capacity ratios
  - Parameter relationship validation

### 4. Extended Current/Charge/Discharge Support

- **Current modes**:
  - 🔋 **Discharge**: Negative current (battery discharging)
  - ⚡ **Charge**: Positive current (battery charging)
  - ⚙️ **Custom**: User-defined current value

- **Automatic parameter updates**: Current settings are automatically applied to simulation parameters

### 5. Enhanced Error Handling

- **Convergence detection**: Automatic detection of simulation convergence issues
- **Detailed error messages**: Clear, actionable error messages in Japanese
- **Parameter reset**: Easy reset to original values when errors occur
- **Validation before simulation**: Pre-simulation parameter validation

### 6. Advanced Visualization

- **Multi-plot layout**: Voltage, current, and capacity plots
- **Model type indication**: Shows which PyBamm model was used
- **Modification indicators**: Plot titles show number of modified parameters
- **Enhanced mock data**: Realistic simulation data for development/testing

### 7. Search and Filtering

- **Parameter search**: Find parameters by name
- **Modified-only filter**: Show only parameters that have been changed
- **Real-time filtering**: Instant results as you type

## How to Use

### Basic Parameter Modification

1. **Load a preset**: Select a preset from the dropdown and click "読み込み" (Load)
2. **Edit parameters**: Double-click any parameter in the list
3. **Enter new value**: Type the new value in the dialog and click "OK"
4. **Visual feedback**: Modified parameters will be highlighted in orange
5. **Validate**: Click "パラメータ検証" (Validate Parameters) to check for errors

### Custom Preset Management

1. **Modify parameters**: Make your desired parameter changes
2. **Save preset**: Click "保存" (Save) and enter a custom name
3. **Load custom preset**: Select your custom preset from the dropdown
4. **Delete preset**: Select a custom preset and click "削除" (Delete)

### Running Simulations

1. **Set simulation time**: Adjust the simulation time (hours)
2. **Choose model**: Select DFN, SPM, or SPMe model
3. **Configure current**: Choose discharge/charge mode and current value
4. **Run simulation**: Click "シミュレーション実行" (Run Simulation)
5. **View results**: Multiple plots will show voltage, current, and capacity

### Error Handling

- **Red parameters**: Fix parameters highlighted in red before running simulations
- **Validation errors**: Use "パラメータ検証" to identify and fix issues
- **Reset parameters**: Use "リセット" to restore original values
- **Convergence errors**: Adjust parameter values if simulation fails to converge

## Parameter Categories

### Critical Parameters
- **Nominal cell capacity [A.h]**: Battery capacity
- **Current function [A]**: Simulation current
- **Ambient temperature [K]**: Operating temperature

### Electrode Parameters
- **Positive/Negative electrode thickness [m]**: Electrode dimensions
- **Positive/Negative electrode porosity**: Electrode porosity (0-1)
- **Positive/Negative electrode conductivity [S/m]**: Electrical conductivity

### Physical Parameters
- **Separator thickness [m]**: Separator dimensions
- **Particle radius [m]**: Active material particle size
- **Electrolyte conductivity [S/m]**: Ionic conductivity

## Error Messages and Solutions

### Common Validation Errors

| Error Message | Solution |
|---------------|----------|
| "容量は正の値である必要があります" | Set capacity to a positive value |
| "温度が低すぎます" | Increase temperature above 200 K |
| "多孔度は0から1の間の値である必要があります" | Set porosity between 0 and 1 |
| "電流値が異常に大きすぎます" | Reduce current to reasonable range |

### Convergence Issues

If simulation fails to converge:
1. Check parameter validation first
2. Reduce current magnitude
3. Adjust electrode thicknesses
4. Reset to known good parameters
5. Try different model type (SPM is more stable)

## File Structure

```
PyBammUI/
├── advanced_variables_tab_enhanced.py    # Enhanced tab implementation
├── custom_presets.json                   # Saved custom presets
├── test_enhanced_advanced_variables.py   # Test script
└── ENHANCED_ADVANCED_VARIABLES_GUIDE.md  # This guide
```

## Technical Details

### Classes

- **AdvancedVariablesTab**: Main enhanced tab class
- **ParameterEditDialog**: Parameter editing dialog
- **MockParameterValues**: Parameter container for development

### Key Methods

- `validate_parameter_value()`: Parameter validation
- `modify_parameter()`: Parameter modification with tracking
- `save_current_preset()`: Custom preset saving
- `check_solution_convergence()`: Simulation convergence checking
- `update_enhanced_plot()`: Multi-plot visualization

## Testing

Run the test script to verify functionality:

```bash
python test_enhanced_advanced_variables.py
```

The test script validates:
- Parameter validation logic
- Mock simulation generation
- Parameter consistency checking
- Dialog functionality

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure all required modules are installed
2. **Preset not saving**: Check file permissions for `custom_presets.json`
3. **Validation too strict**: Adjust validation ranges in `validate_parameter_value()`
4. **Simulation convergence**: Try simpler models (SPM) or adjust parameters

### Debug Mode

Enable debug output by modifying the validation functions to print intermediate values.

## Future Enhancements

Potential future improvements:
- Parameter sensitivity analysis
- Batch parameter modification
- Parameter optimization
- Advanced visualization options
- Export/import of parameter sets

## Support

For issues or questions:
1. Check this guide first
2. Run the test script to verify functionality
3. Check parameter validation messages
4. Review PyBamm documentation for parameter meanings
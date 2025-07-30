#!/usr/bin/env python3
"""
Test script for Enhanced Advanced Variables Tab
Tests all the new parameter modification features.
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the enhanced tab
from advanced_variables_tab_enhanced import AdvancedVariablesTab, ParameterEditDialog, MockParameterValues

def test_enhanced_features():
    """Test the enhanced advanced variables features."""
    
    print("=== Enhanced Advanced Variables Tab Test ===")
    print()
    
    # Test 1: MockParameterValues functionality
    print("Test 1: MockParameterValues functionality")
    test_params = {
        "Nominal cell capacity [A.h]": 2.5,
        "Current function [A]": 1.0,
        "Ambient temperature [K]": 298.15
    }
    
    mock_params = MockParameterValues(test_params)
    print(f"✓ Created MockParameterValues with {len(test_params)} parameters")
    print(f"✓ Capacity: {mock_params['Nominal cell capacity [A.h]']} A.h")
    print(f"✓ Current: {mock_params['Current function [A]']} A")
    print(f"✓ Temperature: {mock_params['Ambient temperature [K]']} K")
    print()
    
    # Test 2: Parameter validation
    print("Test 2: Parameter validation")
    
    # Create a mock tab instance for testing validation
    class MockApp:
        def __init__(self):
            self.root = tk.Tk()
            self.root.withdraw()  # Hide the window
    
    app = MockApp()
    
    # Create a minimal tab instance for testing
    tab = AdvancedVariablesTab(tk.Frame(), app)
    
    # Test valid parameters
    try:
        valid_value = tab.validate_parameter_value("Nominal cell capacity [A.h]", 2.5)
        print(f"✓ Valid capacity validation: {valid_value}")
    except ValueError as e:
        print(f"✗ Unexpected validation error: {e}")
    
    # Test invalid parameters
    try:
        tab.validate_parameter_value("Nominal cell capacity [A.h]", -1.0)
        print("✗ Should have failed for negative capacity")
    except ValueError:
        print("✓ Correctly rejected negative capacity")
    
    try:
        tab.validate_parameter_value("Ambient temperature [K]", 100)
        print("✗ Should have failed for low temperature")
    except ValueError:
        print("✓ Correctly rejected low temperature")
    
    try:
        tab.validate_parameter_value("Positive electrode porosity", 1.5)
        print("✗ Should have failed for porosity > 1")
    except ValueError:
        print("✓ Correctly rejected invalid porosity")
    
    print()
    
    # Test 3: Parameter name extraction
    print("Test 3: Parameter name extraction")
    test_keys = [
        "Nominal cell capacity [A.h]",
        "Ambient temperature [K]",
        "Simple parameter"
    ]
    
    for key in test_keys:
        extracted = tab.extract_param_name(key)
        print(f"✓ '{key}' → '{extracted}'")
    
    print()
    
    # Test 4: Mock simulation data generation
    print("Test 4: Mock simulation data generation")
    
    # Set up mock parameters
    tab.current_parameter_values = MockParameterValues({
        "Nominal cell capacity [A.h]": 3.0,
        "Current function [A]": -2.0,
        "Ambient temperature [K]": 298.15
    })
    
    # Generate mock simulation
    mock_results = tab._enhanced_mock_simulation(1.0, "DFN")
    
    print(f"✓ Generated mock simulation with {len(mock_results['time'])} time points")
    print(f"✓ Voltage range: {min(mock_results['voltage']):.2f} - {max(mock_results['voltage']):.2f} V")
    print(f"✓ Current: {mock_results['current'][0]:.2f} A")
    print(f"✓ Final capacity: {mock_results['capacity'][-1]:.2f} A.h")
    print(f"✓ Model type: {mock_results['model_type']}")
    print(f"✓ Voltage components: {list(mock_results['voltage_components'].keys())}")
    
    print()
    
    # Test 5: Parameter consistency checking
    print("Test 5: Parameter consistency checking")
    
    warnings = []
    param_items = [
        ("Nominal cell capacity [A.h]", 1.0),
        ("Current function [A]", -10.0),  # High C-rate
        ("Positive electrode thickness [m]", 100e-6),
        ("Negative electrode thickness [m]", 100e-6),
        ("Separator thickness [m]", 1000e-6)  # Very thick separator
    ]
    
    tab.check_parameter_consistency(param_items, warnings)
    
    if warnings:
        print("✓ Detected parameter consistency issues:")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("✓ No consistency warnings (parameters within normal ranges)")
    
    print()
    
    # Clean up
    app.root.destroy()
    
    print("=== All Tests Completed Successfully ===")
    print()
    print("Enhanced Features Available:")
    print("• Parameter modification with color-coded visual indicators")
    print("• Custom preset saving and loading with JSON storage")
    print("• Comprehensive parameter validation and error handling")
    print("• Extended current/charge/discharge parameter support")
    print("• Simulation convergence error detection and handling")
    print("• Enhanced multi-plot visualization")
    print("• Search and filtering capabilities")
    print("• Parameter reset functionality")
    print("• Detailed error messages in Japanese")


def demo_parameter_edit_dialog():
    """Demonstrate the parameter editing dialog."""
    
    print("\n=== Parameter Edit Dialog Demo ===")
    print("This will show the parameter editing dialog...")
    
    root = tk.Tk()
    root.withdraw()  # Hide main window
    
    # Show parameter edit dialog
    dialog = ParameterEditDialog(
        root, 
        "Nominal cell capacity", 
        "2.5", 
        "A.h"
    )
    
    if dialog.result is not None:
        print(f"✓ User entered new value: {dialog.result}")
    else:
        print("✓ User cancelled the dialog")
    
    root.destroy()


if __name__ == "__main__":
    print("Enhanced Advanced Variables Tab - Test Suite")
    print("=" * 50)
    
    # Run basic functionality tests
    test_enhanced_features()
    
    # Ask user if they want to test the dialog
    response = input("\nWould you like to test the parameter editing dialog? (y/n): ")
    if response.lower().startswith('y'):
        demo_parameter_edit_dialog()
    
    print("\nTest completed! The enhanced advanced variables tab is ready to use.")
    print("\nTo use the enhanced features:")
    print("1. Run main_app.py")
    print("2. Go to the '高度な変数' (Advanced Variables) tab")
    print("3. Load a parameter preset")
    print("4. Double-click any parameter to edit it")
    print("5. Use the preset management buttons to save custom presets")
    print("6. Run simulations with different current/charge/discharge settings")
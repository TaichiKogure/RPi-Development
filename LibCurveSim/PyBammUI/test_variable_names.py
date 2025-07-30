#!/usr/bin/env python3
"""
Test script to understand PyBamm model variable_names() functionality.
This will help us design the new GUI feature.
"""

try:
    import pybamm
    PYBAMM_AVAILABLE = True
    print("PyBamm is available")
except ImportError:
    PYBAMM_AVAILABLE = False
    print("PyBamm is not available - creating mock data for design purposes")

def test_variable_names():
    """Test what variable_names() returns for different models."""
    
    if not PYBAMM_AVAILABLE:
        # Mock variable names for design purposes
        mock_variables = [
            "Terminal voltage [V]",
            "Current [A]",
            "Discharge capacity [A.h]",
            "Negative electrode potential [V]",
            "Positive electrode potential [V]",
            "Electrolyte concentration [mol.m-3]",
            "Negative particle concentration [mol.m-3]",
            "Positive particle concentration [mol.m-3]",
            "Cell temperature [K]",
            "Negative electrode temperature [K]",
            "Positive electrode temperature [K]",
            "Power [W]",
            "Resistance [Ohm]",
            "Negative electrode SOC",
            "Positive electrode SOC",
            "SOC",
            "Time [s]"
        ]
        print("Mock variable names (for design):")
        for i, var in enumerate(mock_variables):
            print(f"  {i+1:2d}. {var}")
        return mock_variables
    
    # Test with real PyBamm models
    models = {
        'DFN': pybamm.lithium_ion.DFN(),
        'SPM': pybamm.lithium_ion.SPM(),
        'SPMe': pybamm.lithium_ion.SPMe()
    }
    
    all_variables = {}
    
    for model_name, model in models.items():
        print(f"\n=== {model_name} Model Variables ===")
        try:
            variables = model.variable_names()
            all_variables[model_name] = variables
            print(f"Total variables: {len(variables)}")
            print("First 20 variables:")
            for i, var in enumerate(variables[:20]):
                print(f"  {i+1:2d}. {var}")
            if len(variables) > 20:
                print(f"  ... and {len(variables) - 20} more")
        except Exception as e:
            print(f"Error getting variables for {model_name}: {e}")
    
    return all_variables

def test_parameter_values():
    """Test what parameter values are available."""
    
    if not PYBAMM_AVAILABLE:
        print("\nMock parameter values (for design):")
        mock_params = {
            "Nominal cell capacity [A.h]": 2.5,
            "Current function [A]": 1.0,
            "Ambient temperature [K]": 298.15,
            "Voltage cut-off [V]": 3.0,
            "Upper voltage cut-off [V]": 4.2,
            "Negative electrode conductivity [S.m-1]": 100.0,
            "Positive electrode conductivity [S.m-1]": 10.0,
            "Electrolyte conductivity [S.m-1]": 1.0,
            "Negative particle radius [m]": 5.86e-06,
            "Positive particle radius [m]": 5.22e-06
        }
        for param, value in mock_params.items():
            print(f"  {param}: {value}")
        return mock_params
    
    try:
        # Get Chen2020 parameter set
        param_values = pybamm.ParameterValues("Chen2020")
        print(f"\nChen2020 parameter set contains {len(param_values)} parameters")
        
        # Show some key parameters
        key_params = [
            "Nominal cell capacity [A.h]",
            "Current function [A]",
            "Ambient temperature [K]",
            "Voltage cut-off [V]",
            "Upper voltage cut-off [V]"
        ]
        
        print("Key parameters:")
        available_params = {}
        for param in key_params:
            if param in param_values:
                value = param_values[param]
                available_params[param] = value
                print(f"  {param}: {value}")
            else:
                print(f"  {param}: NOT FOUND")
        
        return available_params
        
    except Exception as e:
        print(f"Error getting parameter values: {e}")
        return {}

if __name__ == "__main__":
    print("Testing PyBamm variable_names() functionality...")
    variables = test_variable_names()
    parameters = test_parameter_values()
    
    print(f"\n=== Summary ===")
    if PYBAMM_AVAILABLE:
        print("PyBamm is available - real data collected")
    else:
        print("PyBamm not available - mock data created for design")
    
    print("\nThis information will be used to design the new GUI feature")
    print("that allows users to specify custom variables and values.")
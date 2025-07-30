#!/usr/bin/env python3
"""
Test script to identify available PyBamm parameter presets
"""

try:
    import pybamm
    PYBAMM_AVAILABLE = True
    print("PyBamm is available")
    
    # Common parameter sets that are typically available in PyBamm
    common_presets = [
        "Chen2020",
        "Marquis2019", 
        "Ecker2015",
        "Mohtat2020",
        "Prada2013",
        "Ramadass2004",
        "Ai2020",
        "ORegan2022"
    ]
    
    available_presets = []
    
    for preset in common_presets:
        try:
            param_values = pybamm.ParameterValues(preset)
            available_presets.append(preset)
            print(f"✓ {preset} - Available")
        except Exception as e:
            print(f"✗ {preset} - Not available: {e}")
    
    print(f"\nAvailable parameter presets: {available_presets}")
    
    # Test getting parameter values from Chen2020
    if "Chen2020" in available_presets:
        print("\nTesting Chen2020 parameter values:")
        param_values = pybamm.ParameterValues("Chen2020")
        
        # Get some common parameters
        common_params = [
            "Nominal cell capacity [A.h]",
            "Current function [A]", 
            "Ambient temperature [K]",
            "Number of electrodes connected in parallel to make a cell",
            "Electrode height [m]",
            "Electrode width [m]"
        ]
        
        for param in common_params:
            try:
                value = param_values[param]
                print(f"  {param}: {value}")
            except KeyError:
                print(f"  {param}: Not found")
    
except ImportError:
    print("PyBamm is not available - using mock data")
    PYBAMM_AVAILABLE = False
    
    # Mock available presets for development
    available_presets = [
        "Chen2020",
        "Marquis2019", 
        "Ecker2015",
        "Mohtat2020"
    ]
    
    print(f"Mock available parameter presets: {available_presets}")
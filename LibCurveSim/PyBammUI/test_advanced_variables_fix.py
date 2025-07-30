#!/usr/bin/env python3
"""
Test script to verify that the AdvancedVariablesTab AttributeError is fixed.
This script tests the initialization without starting the full GUI.
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Add the current directory to the path to import the modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_advanced_variables_tab():
    """Test that AdvancedVariablesTab can be initialized without AttributeError."""
    try:
        # Create a root window (but don't show it)
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        # Create a notebook widget
        notebook = ttk.Notebook(root)
        
        # Create a mock app object with minimal required attributes
        class MockApp:
            def __init__(self):
                self.simulator = None
                self.simulation_results = None
                
            def update_status(self, message):
                print(f"Status: {message}")
                
            def show_error(self, title, message):
                print(f"Error - {title}: {message}")
                
            def show_info(self, title, message):
                print(f"Info - {title}: {message}")
        
        mock_app = MockApp()
        
        # Try to import and initialize AdvancedVariablesTab
        from advanced_variables_tab import AdvancedVariablesTab
        
        print("Importing AdvancedVariablesTab... OK")
        
        # This is where the AttributeError was occurring
        advanced_tab = AdvancedVariablesTab(notebook, mock_app)
        
        print("Initializing AdvancedVariablesTab... OK")
        
        # Check that the available_presets attribute exists
        if hasattr(advanced_tab, 'available_presets'):
            print(f"available_presets attribute exists: {advanced_tab.available_presets}")
        else:
            print("ERROR: available_presets attribute is missing!")
            return False
            
        # Clean up
        root.destroy()
        
        print("✓ Test PASSED: AdvancedVariablesTab initializes without AttributeError")
        return True
        
    except AttributeError as e:
        print(f"✗ Test FAILED: AttributeError still exists: {e}")
        return False
    except Exception as e:
        print(f"✗ Test FAILED: Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Testing AdvancedVariablesTab AttributeError fix...")
    print("=" * 50)
    
    success = test_advanced_variables_tab()
    
    print("=" * 50)
    if success:
        print("SUCCESS: The AttributeError has been fixed!")
        sys.exit(0)
    else:
        print("FAILURE: The AttributeError still exists!")
        sys.exit(1)
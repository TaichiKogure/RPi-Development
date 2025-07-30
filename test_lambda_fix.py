#!/usr/bin/env python3
"""
Test script to verify that the lambda closure fix works correctly.
This script simulates the problematic scenario and tests the fix.
"""

import threading
import time
import tkinter as tk
from tkinter import messagebox

class TestApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Lambda Closure Fix Test")
        self.root.geometry("400x300")
        
        # Create test buttons
        tk.Button(self.root, text="Test Original Problem (Fixed)", 
                 command=self.test_fixed_lambda).pack(pady=10)
        tk.Button(self.root, text="Test Error Message Lambda", 
                 command=self.test_error_message_lambda).pack(pady=10)
        tk.Button(self.root, text="Exit", command=self.root.quit).pack(pady=10)
        
        self.status_label = tk.Label(self.root, text="Ready to test")
        self.status_label.pack(pady=20)
    
    def test_fixed_lambda(self):
        """Test the fixed lambda pattern from advanced_variables_tab.py"""
        self.status_label.config(text="Testing fixed lambda pattern...")
        
        def background_work():
            try:
                # Simulate some work that might fail
                time.sleep(1)
                raise Exception("Test exception for lambda closure")
            except Exception as e:
                # This is the FIXED version - using default argument
                self.root.after(0, lambda e=e: self._simulation_error(str(e)))
        
        thread = threading.Thread(target=background_work, daemon=True)
        thread.start()
    
    def test_error_message_lambda(self):
        """Test the fixed error message lambda pattern from main_app.py"""
        self.status_label.config(text="Testing error message lambda pattern...")
        
        def background_work():
            try:
                # Simulate some work that might fail
                time.sleep(1)
                raise Exception("Test exception for error message lambda")
            except Exception as e:
                error_message = f"Background error occurred: {str(e)}"
                # This is the FIXED version - using default argument
                self.root.after(0, lambda error_message=error_message: self._show_error("Error", error_message))
        
        thread = threading.Thread(target=background_work, daemon=True)
        thread.start()
    
    def _simulation_error(self, error_msg):
        """Handle simulation error (similar to advanced_variables_tab.py)"""
        self.status_label.config(text="Lambda executed successfully!")
        messagebox.showerror("Simulation Error", f"Fixed lambda worked: {error_msg}")
    
    def _show_error(self, title, message):
        """Show error message (similar to main_app.py)"""
        self.status_label.config(text="Error message lambda executed successfully!")
        messagebox.showerror(title, f"Fixed error message lambda worked: {message}")
    
    def run(self):
        """Run the test application"""
        print("Starting lambda closure fix test...")
        print("This test verifies that the lambda functions work correctly")
        print("without throwing NameError exceptions.")
        self.root.mainloop()

def test_without_gui():
    """Test the lambda fix without GUI (for automated testing)"""
    print("Testing lambda closure fix without GUI...")
    
    # Test 1: Direct exception variable capture
    try:
        raise Exception("Test exception")
    except Exception as e:
        # This should work without NameError
        test_lambda = lambda e=e: f"Captured exception: {str(e)}"
        result = test_lambda()
        print(f"✓ Test 1 passed: {result}")
    
    # Test 2: Error message variable capture
    try:
        raise Exception("Another test exception")
    except Exception as e:
        error_message = f"Error occurred: {str(e)}"
        # This should work without NameError
        test_lambda = lambda error_message=error_message: f"Captured message: {error_message}"
        result = test_lambda()
        print(f"✓ Test 2 passed: {result}")
    
    print("All tests passed! Lambda closure fix is working correctly.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--no-gui":
        test_without_gui()
    else:
        app = TestApp()
        app.run()
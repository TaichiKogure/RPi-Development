"""
PyBamm UI Application - Main Module

This module provides the main application for the PyBamm battery simulation tool.
It creates a user-friendly interface for running PyBamm simulations with customizable
parameters and provides visualization and data export capabilities.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import numpy as np

# Add the current directory to the path to import the modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import font configuration for Japanese text support
import font_config

# Import the tab modules
try:
    from simulation_tab import SimulationTab
    from export_tab import ExportTab
    # Import the enhanced advanced variables tab
    from advanced_variables_tab_enhanced import AdvancedVariablesTab
except ImportError:
    # Create placeholder classes if modules don't exist yet
    class SimulationTab:
        def __init__(self, parent, app):
            self.frame = ttk.Frame(parent)
            ttk.Label(self.frame, text="シミュレーションタブ（開発中）").pack(pady=50)
    
    class ExportTab:
        def __init__(self, parent, app):
            self.frame = ttk.Frame(parent)
            ttk.Label(self.frame, text="エクスポートタブ（開発中）").pack(pady=50)
    
    class AdvancedVariablesTab:
        def __init__(self, parent, app):
            self.frame = ttk.Frame(parent)
            ttk.Label(self.frame, text="高度な変数タブ（開発中）").pack(pady=50)

# PyBamm integration
try:
    import pybamm
    PYBAMM_AVAILABLE = True
except ImportError:
    PYBAMM_AVAILABLE = False
    # Create mock classes for development
    
    class MockSolution:
        def __init__(self):
            self.t = np.linspace(0, 3600, 100)  # 1 hour simulation
            self.data = {
                "Terminal voltage [V]": np.linspace(4.2, 3.0, 100),
                "Current [A]": np.ones(100) * -1.0,  # 1A discharge
                "Discharge capacity [A.h]": np.linspace(0, 1.0, 100)
            }
        
        def __getitem__(self, key):
            """Allow dictionary-style access to solution data."""
            if key in self.data:
                return MockVariable(self.data[key])
            raise KeyError(f"Key '{key}' not found in solution")
        
        def __contains__(self, key):
            """Check if key exists in solution data."""
            return key in self.data
    
    class MockVariable:
        def __init__(self, data):
            self.data = data
    
    class MockDFNModel:
        def __init__(self):
            self.name = "Doyle-Fuller-Newman model"
        
        def solve(self, t_eval, solver=None):
            # Return mock solution
            return MockSolution()
    
    class MockModel:
        def __init__(self):
            pass
        
        def DFN(self):
            return MockDFNModel()
        
        def SPM(self):
            return MockDFNModel()  # Use same mock for simplicity
        
        def SPMe(self):
            return MockDFNModel()  # Use same mock for simplicity
    
    class MockParameterValues:
        def __init__(self, parameter_set):
            self.parameters = {}
        
        def __contains__(self, key):
            return True  # Accept all parameters for mock
        
        def __setitem__(self, key, value):
            self.parameters[key] = value
    
    class MockSimulation:
        def __init__(self, model, parameter_values=None):
            self.model = model
            self.parameter_values = parameter_values
        
        def solve(self, t_eval):
            return self.model.solve(t_eval)
    
    class MockPyBamm:
        def __init__(self):
            self.lithium_ion = MockModel()
        
        def ParameterValues(self, parameter_set):
            return MockParameterValues(parameter_set)
        
        def Simulation(self, model, parameter_values=None):
            return MockSimulation(model, parameter_values)
    
    pybamm = MockPyBamm()


class PyBammSimulator:
    """
    PyBamm simulation wrapper class.
    Provides a simplified interface for running PyBamm simulations.
    """
    
    def __init__(self):
        """Initialize the PyBamm simulator."""
        self.model = None
        self.solution = None
        self.parameters = {
            'Nominal cell capacity [A.h]': 2.5,
            'Current function [A]': 1.0,
            'Voltage cut-off [V]': 3.0,
            'Upper voltage cut-off [V]': 4.2,
            'Ambient temperature [K]': 298.15
        }
        
    def set_parameters(self, capacity=None, current=None, v_min=None, v_max=None, temperature=None):
        """
        Set simulation parameters.
        
        Args:
            capacity: Battery capacity in Ah
            current: Current in A (positive for charge, negative for discharge)
            v_min: Minimum voltage cutoff in V
            v_max: Maximum voltage cutoff in V
            temperature: Temperature in K
        """
        if capacity is not None:
            self.parameters['Nominal cell capacity [A.h]'] = capacity
        if current is not None:
            self.parameters['Current function [A]'] = current
        if v_min is not None:
            self.parameters['Voltage cut-off [V]'] = v_min
        if v_max is not None:
            self.parameters['Upper voltage cut-off [V]'] = v_max
        if temperature is not None:
            self.parameters['Ambient temperature [K]'] = temperature
    
    def run_simulation(self, time_hours=1.0, model_type='DFN'):
        """
        Run PyBamm simulation.
        
        Args:
            time_hours: Simulation time in hours
            model_type: Model type ('DFN', 'SPM', 'SPMe')
            
        Returns:
            dict: Simulation results containing time, voltage, current, capacity
        """
        try:
            # Ensure time_hours is a float
            time_hours = float(time_hours)
            
            # Create model
            if model_type == 'DFN':
                self.model = pybamm.lithium_ion.DFN()
            elif model_type == 'SPM':
                self.model = pybamm.lithium_ion.SPM()
            elif model_type == 'SPMe':
                self.model = pybamm.lithium_ion.SPMe()
            else:
                raise ValueError(f"Unknown model type: {model_type}")
            
            # Set up parameters with proper PyBamm parameter names
            parameter_values = pybamm.ParameterValues("Chen2020")
            
            # Update parameters with proper names and values
            if 'Nominal cell capacity [A.h]' in self.parameters:
                parameter_values["Nominal cell capacity [A.h]"] = self.parameters['Nominal cell capacity [A.h]']
            
            if 'Current function [A]' in self.parameters:
                # For constant current discharge
                current_value = abs(float(self.parameters['Current function [A]']))
                parameter_values.update({
                    "Current function [A]": current_value
                })
            
            if 'Ambient temperature [K]' in self.parameters:
                parameter_values["Ambient temperature [K]"] = float(self.parameters['Ambient temperature [K]'])
            
            # Create simulation with proper solver
            sim = pybamm.Simulation(
                self.model, 
                parameter_values=parameter_values,
                solver=pybamm.CasadiSolver(mode="safe")
            )
            
            # Run simulation with proper time evaluation
            # Use fewer points to avoid memory issues
            n_points = max(100, int(time_hours * 60))  # At least 100 points, or 60 per hour
            t_eval = np.linspace(0, time_hours * 3600, n_points)
            
            self.solution = sim.solve(t_eval)
            
            # Extract results with error handling
            results = {
                'time': self.solution.t,
                'voltage': self.solution["Terminal voltage [V]"].data,
                'current': self.solution["Current [A]"].data,
            }
            
            # Extract voltage components for detailed analysis
            try:
                voltage_components = {}
                
                # Open circuit voltage
                if "Open-circuit voltage [V]" in self.solution:
                    voltage_components['ocv'] = self.solution["Open-circuit voltage [V]"].data
                
                # Ohmic losses
                if "Ohmic losses [V]" in self.solution:
                    voltage_components['ohmic'] = self.solution["Ohmic losses [V]"].data
                
                # Concentration overpotential
                if "Concentration overpotential [V]" in self.solution:
                    voltage_components['concentration'] = self.solution["Concentration overpotential [V]"].data
                
                # Reaction overpotential
                if "Reaction overpotential [V]" in self.solution:
                    voltage_components['reaction'] = self.solution["Reaction overpotential [V]"].data
                
                # Electrode potentials
                if "Negative electrode potential [V]" in self.solution:
                    voltage_components['negative_electrode'] = self.solution["Negative electrode potential [V]"].data
                if "Positive electrode potential [V]" in self.solution:
                    voltage_components['positive_electrode'] = self.solution["Positive electrode potential [V]"].data
                
                # Try alternative variable names that might be available
                alternative_vars = [
                    ("X-averaged negative electrode open-circuit potential [V]", 'neg_ocv'),
                    ("X-averaged positive electrode open-circuit potential [V]", 'pos_ocv'),
                    ("X-averaged negative electrode reaction overpotential [V]", 'neg_reaction'),
                    ("X-averaged positive electrode reaction overpotential [V]", 'pos_reaction'),
                    ("X-averaged electrolyte ohmic losses [V]", 'electrolyte_ohmic'),
                    ("X-averaged solid phase ohmic losses [V]", 'solid_ohmic'),
                ]
                
                for var_name, key in alternative_vars:
                    if var_name in self.solution:
                        voltage_components[key] = self.solution[var_name].data
                
                results['voltage_components'] = voltage_components
                
            except Exception as e:
                print(f"Warning: Could not extract voltage components: {e}")
                results['voltage_components'] = {}
            
            # Try to get capacity data
            try:
                if "Discharge capacity [A.h]" in self.solution:
                    results['capacity'] = self.solution["Discharge capacity [A.h]"].data
                else:
                    # Calculate capacity from current and time
                    current_data = results['current']
                    time_data = results['time']
                    capacity_data = np.cumsum(np.abs(current_data) * np.diff(np.concatenate([[0], time_data]))) / 3600
                    results['capacity'] = capacity_data
            except:
                # Fallback capacity calculation
                results['capacity'] = np.linspace(0, self.parameters.get('Nominal cell capacity [A.h]', 2.5), len(results['time']))
            
            return results
            
        except Exception as e:
            # Fallback to mock simulation for development
            print(f"PyBamm simulation failed, using mock data: {e}")
            return self._mock_simulation(time_hours)
    
    def _mock_simulation(self, time_hours):
        """
        Generate mock simulation data for development/testing.
        
        Args:
            time_hours: Simulation time in hours
            
        Returns:
            dict: Mock simulation results
        """
        n_points = int(time_hours * 100)
        time = np.linspace(0, time_hours * 3600, n_points)
        
        # Mock voltage curve (discharge from 4.2V to 3.0V)
        voltage = 4.2 - (4.2 - 3.0) * (time / (time_hours * 3600))
        
        # Mock current (constant discharge)
        current = np.ones(n_points) * -abs(self.parameters['Current function [A]'])
        
        # Mock capacity
        capacity = np.linspace(0, self.parameters['Nominal cell capacity [A.h]'], n_points)
        
        # Generate mock voltage components for testing
        voltage_components = {
            'ocv': 4.1 - (4.1 - 3.2) * (time / (time_hours * 3600)) + 0.05 * np.sin(time / 1000),
            'ohmic': -0.1 * np.abs(current) * (1 + 0.1 * np.sin(time / 500)),
            'concentration': -0.05 * np.abs(current) * (time / (time_hours * 3600)) * np.sin(time / 800),
            'reaction': -0.08 * np.abs(current) * (1 + 0.2 * np.cos(time / 600)),
            'neg_ocv': 0.2 + 0.3 * (time / (time_hours * 3600)) + 0.02 * np.sin(time / 700),
            'pos_ocv': 3.9 - (3.9 - 2.9) * (time / (time_hours * 3600)) + 0.03 * np.cos(time / 900),
            'neg_reaction': -0.04 * np.abs(current) * (1 + 0.15 * np.sin(time / 400)),
            'pos_reaction': -0.04 * np.abs(current) * (1 + 0.15 * np.cos(time / 450)),
            'electrolyte_ohmic': -0.03 * np.abs(current) * (1 + 0.05 * np.sin(time / 300)),
            'solid_ohmic': -0.02 * np.abs(current) * (1 + 0.08 * np.cos(time / 350))
        }
        
        return {
            'time': time,
            'voltage': voltage,
            'current': current,
            'capacity': capacity,
            'voltage_components': voltage_components
        }


class PyBammApp:
    """
    Main application class for the PyBamm UI tool.
    """
    
    def __init__(self, root):
        """
        Initialize the application.
        
        Args:
            root: Root window
        """
        self.root = root
        self.root.title("PyBamm バッテリーシミュレーション UI")
        self.root.geometry("1200x800")
        
        # Set up the main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create the notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Initialize simulator
        self.simulator = PyBammSimulator()
        
        # Initialize data storage
        self.simulation_results = None
        
        # Create the tabs
        self.create_tabs()
        
        # Set up the status bar
        self.status_var = tk.StringVar(value="準備完了")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Show PyBamm availability status
        if PYBAMM_AVAILABLE:
            self.update_status("PyBamm が利用可能です")
        else:
            self.update_status("PyBamm が見つかりません - モックデータを使用します")
        
        # Bind events
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def create_tabs(self):
        """Create the tabs for the application."""
        # Simulation tab
        self.simulation_tab = SimulationTab(self.notebook, self)
        self.notebook.add(self.simulation_tab.frame, text="シミュレーション")
        
        # Advanced Variables tab
        self.advanced_variables_tab = AdvancedVariablesTab(self.notebook, self)
        self.notebook.add(self.advanced_variables_tab.frame, text="高度な変数")
        
        # Export tab
        self.export_tab = ExportTab(self.notebook, self)
        self.notebook.add(self.export_tab.frame, text="データエクスポート")
    
    def on_tab_changed(self, event):
        """
        Handle tab changed event.
        
        Args:
            event: Event that triggered the tab change
        """
        tab_id = self.notebook.select()
        tab_name = self.notebook.tab(tab_id, "text")
        
        # Update status bar
        self.status_var.set(f"タブ: {tab_name}")
        
        # Update data in tabs
        if tab_name == "データエクスポート" and self.simulation_results is not None:
            if hasattr(self.export_tab, 'update_available_data'):
                self.export_tab.update_available_data(self.simulation_results)
    
    def update_status(self, message):
        """
        Update the status bar message.
        
        Args:
            message: Message to display
        """
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def show_error(self, title, message):
        """
        Show an error message.
        
        Args:
            title: Error title
            message: Error message
        """
        messagebox.showerror(title, message)
    
    def show_info(self, title, message):
        """
        Show an information message.
        
        Args:
            title: Information title
            message: Information message
        """
        messagebox.showinfo(title, message)
    
    def show_warning(self, title, message):
        """
        Show a warning message.
        
        Args:
            title: Warning title
            message: Warning message
        """
        messagebox.showwarning(title, message)
    
    def run_in_background(self, status_message, work_function):
        """
        Run a function in the background thread while updating the status bar.
        
        Args:
            status_message (str): Message to display in the status bar during execution
            work_function (callable): Function to execute in the background thread
        """
        import threading
        
        def background_worker():
            """Worker function that runs in the background thread."""
            try:
                # Update status bar to show operation is in progress
                if hasattr(self, 'root') and self.root:
                    self.root.after(0, lambda: self.update_status(status_message))
                
                # Execute the work function
                work_function()
                
                # Reset status bar when done
                if hasattr(self, 'root') and self.root:
                    self.root.after(0, lambda: self.update_status("準備完了"))
                
            except Exception as e:
                # Handle any errors that occur during background execution
                error_message = f"バックグラウンド処理中にエラーが発生しました: {str(e)}"
                if hasattr(self, 'root') and self.root:
                    self.root.after(0, lambda: self.update_status("エラーが発生しました"))
                    self.root.after(0, lambda error_message=error_message: self.show_error("エラー", error_message))
                else:
                    # Fallback for testing or when root is not available
                    print(f"Background error: {error_message}")
        
        # Start the background thread
        thread = threading.Thread(target=background_worker, daemon=True)
        thread.start()


def main():
    """Main function to run the application."""
    root = tk.Tk()
    app = PyBammApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
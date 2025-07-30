#!/usr/bin/env python3
"""
Advanced Variables Tab for PyBamm UI - Redesigned for Parameter Presets
Allows users to select parameter presets and run simple simulations.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
import threading
import time

# Import font configuration for Japanese text support
import font_config

# PyBamm integration
try:
    import pybamm
    PYBAMM_AVAILABLE = True
except ImportError:
    PYBAMM_AVAILABLE = False


class AdvancedVariablesTab:
    """Advanced Variables Tab for parameter preset selection and simple simulation."""
    
    def __init__(self, parent, app):
        """
        Initialize the Advanced Variables tab.
        
        Args:
            parent: Parent widget (notebook)
            app: Main application instance
        """
        self.parent = parent
        self.app = app
        self.frame = ttk.Frame(parent)
        
        # Initialize variables
        self.setup_variables()
        
        # Set up the UI
        self.setup_ui()
        
        # Initialize parameter presets
        self.available_presets = self.get_available_presets()
        self.current_parameter_values = None
        self.simulation_results = None
        
        # Load default preset
        if self.available_presets:
            self.preset_var.set(self.available_presets[0])
            self.load_parameter_preset()
        
    def setup_variables(self):
        """Set up tkinter variables for the UI."""
        # Parameter preset selection
        self.preset_var = tk.StringVar(value="Chen2020")
        
        # Simulation settings
        self.time_hours_var = tk.DoubleVar(value=1.0)
        
    def get_available_presets(self):
        """Get list of available parameter presets."""
        if PYBAMM_AVAILABLE:
            # Common parameter sets available in PyBamm
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
                    pybamm.ParameterValues(preset)
                    available_presets.append(preset)
                except:
                    pass
            
            return available_presets if available_presets else ["Chen2020"]
        else:
            # Mock presets for development
            return ["Chen2020", "Marquis2019", "Ecker2015", "Mohtat2020"]
    
    def setup_ui(self):
        """Set up the user interface."""
        # Create main paned window
        main_paned = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel for controls
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        # Right panel for plots
        self.plot_frame = ttk.Frame(main_paned)
        main_paned.add(self.plot_frame, weight=2)
        
        # Set up control panels
        self.setup_preset_selection(left_frame)
        self.setup_parameter_display(left_frame)
        self.setup_simulation_controls(left_frame)
        
        # Set up plot area
        self.setup_plot_area()
        
    def setup_preset_selection(self, parent):
        """Set up parameter preset selection controls."""
        preset_frame = ttk.LabelFrame(parent, text="パラメータプリセット選択", padding=10)
        preset_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Preset selection
        ttk.Label(preset_frame, text="プリセット:").grid(row=0, column=0, sticky=tk.W, pady=2)
        preset_combo = ttk.Combobox(
            preset_frame, textvariable=self.preset_var, width=20,
            values=self.available_presets, state="readonly"
        )
        preset_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        preset_combo.bind('<<ComboboxSelected>>', self.on_preset_changed)
        
        # Load preset button
        load_button = ttk.Button(
            preset_frame, text="プリセット読み込み",
            command=self.load_parameter_preset
        )
        load_button.grid(row=0, column=2, padx=10, pady=2)
        
    def setup_parameter_display(self, parent):
        """Set up parameter values display."""
        display_frame = ttk.LabelFrame(parent, text="パラメータ値 (読み取り専用)", padding=10)
        display_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview for parameter display
        columns = ("Parameter", "Value", "Unit")
        self.param_tree = ttk.Treeview(display_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        self.param_tree.heading("Parameter", text="パラメータ名")
        self.param_tree.heading("Value", text="値")
        self.param_tree.heading("Unit", text="単位")
        
        self.param_tree.column("Parameter", width=300)
        self.param_tree.column("Value", width=100)
        self.param_tree.column("Unit", width=80)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(display_frame, orient=tk.VERTICAL, command=self.param_tree.yview)
        self.param_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.param_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def setup_simulation_controls(self, parent):
        """Set up simulation control panel."""
        sim_frame = ttk.LabelFrame(parent, text="シミュレーション実行", padding=10)
        sim_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Time setting
        ttk.Label(sim_frame, text="シミュレーション時間 (時間):").grid(row=0, column=0, sticky=tk.W, pady=2)
        time_spinbox = ttk.Spinbox(
            sim_frame, textvariable=self.time_hours_var, 
            from_=0.1, to=10.0, increment=0.1, width=10
        )
        time_spinbox.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Run simulation button
        self.run_button = ttk.Button(
            sim_frame, text="シミュレーション実行",
            command=self.run_simulation
        )
        self.run_button.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Clear plot button
        clear_button = ttk.Button(
            sim_frame, text="プロットクリア",
            command=self.clear_plot
        )
        clear_button.grid(row=2, column=0, columnspan=2, pady=5)
        
    def setup_plot_area(self):
        """Set up the plot area."""
        # Create figure and canvas
        self.fig = plt.figure(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        self.toolbar.update()
        
        # Initialize with empty plot
        self.fig.text(0.5, 0.5, "シミュレーション結果がここに表示されます", 
                     ha='center', va='center', fontsize=14)
        self.canvas.draw()
        
    def on_preset_changed(self, event=None):
        """Handle preset selection change."""
        self.load_parameter_preset()
        
    def load_parameter_preset(self):
        """Load the selected parameter preset and display values."""
        preset_name = self.preset_var.get()
        
        try:
            if PYBAMM_AVAILABLE:
                self.current_parameter_values = pybamm.ParameterValues(preset_name)
                self.display_parameter_values()
                messagebox.showinfo("成功", f"パラメータプリセット '{preset_name}' を読み込みました。")
            else:
                # Mock parameter values for development
                self.current_parameter_values = self.get_mock_parameter_values(preset_name)
                self.display_parameter_values()
                messagebox.showinfo("成功", f"モックパラメータプリセット '{preset_name}' を読み込みました。")
                
        except Exception as e:
            messagebox.showerror("エラー", f"パラメータプリセットの読み込みに失敗しました: {str(e)}")
            
    def get_mock_parameter_values(self, preset_name):
        """Get mock parameter values for development."""
        # Mock parameter values based on common PyBamm parameters
        mock_params = {
            "Nominal cell capacity [A.h]": 2.5,
            "Current function [A]": 1.0,
            "Ambient temperature [K]": 298.15,
            "Number of electrodes connected in parallel to make a cell": 1,
            "Electrode height [m]": 0.065,
            "Electrode width [m]": 1.58,
            "Cell cooling surface area [m2]": 0.00531,
            "Cell thermal mass [J/K]": 1000,
            "Total heat transfer coefficient [W/m2.K]": 10,
            "Positive electrode thickness [m]": 75.6e-6,
            "Negative electrode thickness [m]": 85.2e-6,
            "Separator thickness [m]": 12e-6,
            "Positive electrode conductivity [S/m]": 0.18,
            "Negative electrode conductivity [S/m]": 215,
            "Electrolyte conductivity [S/m]": 1.0,
            "Positive electrode porosity": 0.335,
            "Negative electrode porosity": 0.25,
            "Separator porosity": 0.47,
            "Positive electrode active material volume fraction": 0.665,
            "Negative electrode active material volume fraction": 0.75,
            "Positive particle radius [m]": 5.22e-6,
            "Negative particle radius [m]": 5.86e-6
        }
        
        class MockParameterValues:
            def __init__(self, params):
                self.params = params
                
            def items(self):
                return self.params.items()
                
            def __getitem__(self, key):
                return self.params.get(key, "N/A")
                
        return MockParameterValues(mock_params)
        
    def display_parameter_values(self):
        """Display parameter values in the treeview."""
        # Clear existing items
        for item in self.param_tree.get_children():
            self.param_tree.delete(item)
            
        if self.current_parameter_values is None:
            return
            
        # Add parameter values to treeview
        try:
            if PYBAMM_AVAILABLE:
                # For real PyBamm parameter values
                for key, value in self.current_parameter_values.items():
                    # Extract unit from parameter name if present
                    unit = ""
                    if "[" in key and "]" in key:
                        unit = key[key.find("[")+1:key.find("]")]
                        param_name = key[:key.find("[")].strip()
                    else:
                        param_name = key
                        
                    # Format value
                    if isinstance(value, (int, float)):
                        if abs(value) < 1e-3 or abs(value) > 1e3:
                            value_str = f"{value:.2e}"
                        else:
                            value_str = f"{value:.4f}"
                    else:
                        value_str = str(value)
                        
                    self.param_tree.insert("", "end", values=(param_name, value_str, unit))
            else:
                # For mock parameter values
                for key, value in self.current_parameter_values.items():
                    # Extract unit from parameter name if present
                    unit = ""
                    if "[" in key and "]" in key:
                        unit = key[key.find("[")+1:key.find("]")]
                        param_name = key[:key.find("[")].strip()
                    else:
                        param_name = key
                        
                    # Format value
                    if isinstance(value, (int, float)):
                        if abs(value) < 1e-3 or abs(value) > 1e3:
                            value_str = f"{value:.2e}"
                        else:
                            value_str = f"{value:.4f}"
                    else:
                        value_str = str(value)
                        
                    self.param_tree.insert("", "end", values=(param_name, value_str, unit))
                    
        except Exception as e:
            print(f"Error displaying parameter values: {e}")
            
    def run_simulation(self):
        """Run simple PyBamm simulation with selected preset."""
        if self.current_parameter_values is None:
            messagebox.showerror("エラー", "パラメータプリセットを先に読み込んでください。")
            return
            
        try:
            time_hours = self.time_hours_var.get()
            
            if time_hours <= 0:
                messagebox.showerror("エラー", "シミュレーション時間は正の値を入力してください。")
                return
                
            # Disable run button during simulation
            self.run_button.config(state=tk.DISABLED)
            
            # Run simulation in background
            self.app.run_in_background(
                "パラメータプリセットシミュレーション実行中...",
                lambda: self._run_simulation_thread(time_hours)
            )
            
        except tk.TclError:
            messagebox.showerror("エラー", "無効なシミュレーション時間です。")
            
    def _run_simulation_thread(self, time_hours):
        """Run simulation in separate thread."""
        try:
            if PYBAMM_AVAILABLE:
                # Create DFN model
                model = pybamm.lithium_ion.DFN()
                
                # Create simulation with preset parameters
                sim = pybamm.Simulation(model, parameter_values=self.current_parameter_values)
                
                # Solve simulation
                t_eval = np.linspace(0, time_hours * 3600, max(100, int(time_hours * 60)))
                solution = sim.solve(t_eval)
                
                # Extract results
                self.simulation_results = {
                    'time': solution.t,
                    'voltage': solution["Terminal voltage [V]"].data,
                    'current': solution["Current [A]"].data,
                    'solution': solution
                }
                
            else:
                # Mock simulation for development
                self.simulation_results = self._mock_simulation(time_hours)
                
            # Update plot on main thread
            self.app.root.after(0, self.update_plot)
            
            # Enable run button on main thread
            self.app.root.after(0, lambda: self.run_button.config(state=tk.NORMAL))
            
            # Show success message on main thread
            self.app.root.after(0, lambda: messagebox.showinfo(
                "完了", f"{time_hours:.1f}時間のシミュレーションが完了しました。"
            ))
            
        except Exception as e:
            # Enable run button on main thread
            self.app.root.after(0, lambda: self.run_button.config(state=tk.NORMAL))
            
            # Show error message on main thread
            error_msg = f"シミュレーション中にエラーが発生しました: {str(e)}"
            self.app.root.after(0, lambda: messagebox.showerror("エラー", error_msg))
            
    def _mock_simulation(self, time_hours):
        """Generate mock simulation data."""
        n_points = int(time_hours * 100)
        time = np.linspace(0, time_hours * 3600, n_points)
        
        # Mock voltage curve (discharge from 4.2V to 3.0V)
        voltage = 4.2 - (4.2 - 3.0) * (time / (time_hours * 3600))
        
        # Mock current (constant discharge)
        current = np.ones(n_points) * -1.0
        
        return {
            'time': time,
            'voltage': voltage,
            'current': current,
            'solution': None
        }
        
    def update_plot(self):
        """Update plot with simulation results."""
        if self.simulation_results is None:
            return
            
        # Clear figure
        self.fig.clear()
        
        # Create voltage vs time plot
        ax = self.fig.add_subplot(1, 1, 1)
        ax.plot(self.simulation_results['time'] / 3600, self.simulation_results['voltage'], 'b-', linewidth=2)
        ax.set_xlabel('時間 (h)')
        ax.set_ylabel('電圧 (V)')
        ax.set_title(f'電圧 vs 時間 (プリセット: {self.preset_var.get()})')
        ax.grid(True, alpha=0.3)
        
        # Update canvas
        self.fig.tight_layout()
        self.canvas.draw()
        
    def clear_plot(self):
        """Clear the plot."""
        # Clear figure
        self.fig.clear()
        
        # Add message
        self.fig.text(0.5, 0.5, "シミュレーション結果がここに表示されます", 
                     ha='center', va='center', fontsize=14)
        
        # Update canvas
        self.canvas.draw()
        
        # Clear stored results
        self.simulation_results = None
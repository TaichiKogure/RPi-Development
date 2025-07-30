#!/usr/bin/env python3
"""
Advanced Variables Tab for PyBamm UI - Debug Version
Enhanced with comprehensive debugging and error tracking capabilities.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
import threading
import time
import logging
import traceback
from datetime import datetime

# Import font configuration for Japanese text support
import font_config

# PyBamm integration
try:
    import pybamm
    PYBAMM_AVAILABLE = True
except ImportError:
    PYBAMM_AVAILABLE = False

# Setup debug logging
debug_logger = logging.getLogger('AdvancedVariablesDebug')
debug_logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
debug_logger.addHandler(handler)

class AdvancedVariablesTabDebug:
    """Debug version of Advanced Variables Tab with enhanced error tracking."""
    
    def __init__(self, parent, app):
        """Initialize the debug version of advanced variables tab."""
        self.parent = parent
        self.app = app
        self.debug_mode = True
        
        debug_logger.info("=== Initializing Advanced Variables Tab Debug Version ===")
        
        # Initialize variables
        self.setup_variables()
        
        # Create main frame
        self.frame = ttk.Frame(parent)
        
        # Setup UI
        self.setup_ui()
        
        debug_logger.info("Advanced Variables Tab Debug initialized successfully")
    
    def debug_log(self, message, level="INFO"):
        """Enhanced debug logging with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        if level == "ERROR":
            debug_logger.error(f"[{timestamp}] {message}")
        elif level == "WARNING":
            debug_logger.warning(f"[{timestamp}] {message}")
        else:
            debug_logger.info(f"[{timestamp}] {message}")
    
    def inspect_data_type(self, data, var_name="unknown"):
        """Comprehensive data type inspection for debugging."""
        info = {
            'variable_name': var_name,
            'type': type(data).__name__,
            'value': str(data)[:100] + "..." if len(str(data)) > 100 else str(data),
            'is_iterable': hasattr(data, '__iter__') and not isinstance(data, str),
            'is_numpy_array': isinstance(data, np.ndarray),
            'shape': getattr(data, 'shape', 'N/A'),
            'size': getattr(data, 'size', 'N/A'),
            'length': len(data) if hasattr(data, '__len__') and not isinstance(data, str) else 'N/A'
        }
        
        self.debug_log(f"Data inspection for '{var_name}': {info}")
        return info
    
    def setup_variables(self):
        """Initialize all variables with debug logging."""
        self.debug_log("Setting up variables...")
        
        # Model variables
        self.model_type_var = tk.StringVar(value="DFN")
        self.available_variables = []
        self.variables_count = 0
        
        # Variable browser
        self.variable_search_var = tk.StringVar()
        self.selected_variable_var = tk.StringVar()
        
        # Custom variables
        self.custom_variables = {}
        self.variable_value_var = tk.StringVar()
        
        # Simulation controls
        self.time_hours_var = tk.DoubleVar(value=1.0)
        self.plot_variable_var = tk.StringVar(value="Terminal voltage [V]")
        
        # Results
        self.simulation_results = None
        
        self.debug_log("Variables setup completed")
    
    def setup_ui(self):
        """Set up the user interface with debug indicators."""
        self.debug_log("Setting up UI...")
        
        # Create main container with debug indicator
        main_container = ttk.Frame(self.frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Debug mode indicator
        debug_frame = ttk.Frame(main_container)
        debug_frame.pack(fill=tk.X, pady=(0, 5))
        
        debug_label = ttk.Label(
            debug_frame, 
            text="🔍 DEBUG MODE - Enhanced Error Tracking Enabled",
            foreground="red",
            font=('Arial', 10, 'bold')
        )
        debug_label.pack()
        
        # Create left and right panels
        paned_window = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Left panel for controls
        left_panel = ttk.Frame(paned_window)
        paned_window.add(left_panel, weight=1)
        
        # Right panel for plot
        right_panel = ttk.Frame(paned_window)
        paned_window.add(right_panel, weight=2)
        
        # Setup control sections
        self.setup_model_selection(left_panel)
        self.setup_variable_browser(left_panel)
        self.setup_custom_variables(left_panel)
        self.setup_simulation_controls(left_panel)
        
        # Setup plot area
        self.setup_plot_area(right_panel)
        
        self.debug_log("UI setup completed")
    
    def setup_model_selection(self, parent):
        """Set up model selection controls with debug logging."""
        self.debug_log("Setting up model selection...")
        
        model_frame = ttk.LabelFrame(parent, text="モデル選択", padding=10)
        model_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Model type selection
        ttk.Label(model_frame, text="モデル:").grid(row=0, column=0, sticky=tk.W, pady=2)
        model_combo = ttk.Combobox(
            model_frame, textvariable=self.model_type_var,
            values=["DFN", "SPM", "SPMe"], state="readonly", width=15
        )
        model_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        model_combo.bind('<<ComboboxSelected>>', self.on_model_changed)
        
        # Load variables button
        load_button = ttk.Button(
            model_frame, text="変数を読み込み",
            command=self.load_model_variables
        )
        load_button.grid(row=0, column=2, padx=10, pady=2)
        
        # Variables count label
        self.variables_count_label = ttk.Label(model_frame, text="変数: 未読み込み")
        self.variables_count_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=2)
        
        self.debug_log("Model selection setup completed")
    
    def setup_variable_browser(self, parent):
        """Set up variable browser controls with debug logging."""
        self.debug_log("Setting up variable browser...")
        
        browser_frame = ttk.LabelFrame(parent, text="変数ブラウザ (Debug)", padding=10)
        browser_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Search box
        search_frame = ttk.Frame(browser_frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(search_frame, text="検索:").pack(side=tk.LEFT)
        search_entry = ttk.Entry(search_frame, textvariable=self.variable_search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        search_entry.bind('<KeyRelease>', self.on_search_changed)
        
        # Variables listbox with scrollbar
        list_frame = ttk.Frame(browser_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox
        self.variables_listbox = tk.Listbox(
            list_frame, yscrollcommand=scrollbar.set,
            height=15, font=('Consolas', 9)
        )
        self.variables_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.variables_listbox.yview)
        
        # Bind selection event
        self.variables_listbox.bind('<<ListboxSelect>>', self.on_variable_selected)
        
        self.debug_log("Variable browser setup completed")
    
    def setup_custom_variables(self, parent):
        """Set up custom variables controls with debug logging."""
        self.debug_log("Setting up custom variables...")
        
        custom_frame = ttk.LabelFrame(parent, text="カスタム変数 (Debug)", padding=10)
        custom_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Selected variable display
        ttk.Label(custom_frame, text="選択された変数:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.selected_var_label = ttk.Label(custom_frame, text="なし", foreground="gray")
        self.selected_var_label.grid(row=0, column=1, columnspan=2, sticky=tk.W, padx=5, pady=2)
        
        # Value input
        ttk.Label(custom_frame, text="値:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.value_entry = ttk.Entry(custom_frame, textvariable=self.variable_value_var, width=15)
        self.value_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Add button
        add_button = ttk.Button(
            custom_frame, text="追加",
            command=self.add_custom_variable
        )
        add_button.grid(row=1, column=2, padx=5, pady=2)
        
        # Custom variables list
        ttk.Label(custom_frame, text="設定済み変数:").grid(row=2, column=0, sticky=tk.NW, pady=(10, 2))
        
        # Custom variables listbox
        custom_list_frame = ttk.Frame(custom_frame)
        custom_list_frame.grid(row=3, column=0, columnspan=3, sticky=tk.EW, pady=2)
        custom_frame.grid_columnconfigure(0, weight=1)
        
        custom_scrollbar = ttk.Scrollbar(custom_list_frame)
        custom_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.custom_variables_listbox = tk.Listbox(
            custom_list_frame, yscrollcommand=custom_scrollbar.set,
            height=6, font=('Consolas', 8)
        )
        self.custom_variables_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        custom_scrollbar.config(command=self.custom_variables_listbox.yview)
        
        # Remove button
        remove_button = ttk.Button(
            custom_frame, text="削除",
            command=self.remove_custom_variable
        )
        remove_button.grid(row=4, column=0, pady=5)
        
        # Clear all button
        clear_button = ttk.Button(
            custom_frame, text="全削除",
            command=self.clear_custom_variables
        )
        clear_button.grid(row=4, column=1, padx=5, pady=5)
        
        self.debug_log("Custom variables setup completed")
    
    def setup_simulation_controls(self, parent):
        """Set up simulation control buttons with debug logging."""
        self.debug_log("Setting up simulation controls...")
        
        sim_frame = ttk.LabelFrame(parent, text="シミュレーション (Debug)", padding=10)
        sim_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Simulation time
        ttk.Label(sim_frame, text="時間 (時):").grid(row=0, column=0, sticky=tk.W, pady=2)
        time_spinbox = ttk.Spinbox(
            sim_frame, from_=0.1, to=24.0, increment=0.1, width=10,
            textvariable=self.time_hours_var, format="%.1f"
        )
        time_spinbox.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Plot variable selection
        ttk.Label(sim_frame, text="プロット変数:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.plot_var_combo = ttk.Combobox(
            sim_frame, textvariable=self.plot_variable_var, width=20,
            values=["Terminal voltage [V]", "Current [A]", "Discharge capacity [A.h]"],
            state="readonly"
        )
        self.plot_var_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Control buttons
        button_frame = ttk.Frame(sim_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Run simulation button
        self.run_button = ttk.Button(
            button_frame, text="シミュレーション実行 (Debug)",
            command=self.run_simulation
        )
        self.run_button.pack(side=tk.LEFT, padx=5)
        
        # Clear plot button
        clear_button = ttk.Button(
            button_frame, text="プロットクリア",
            command=self.clear_plot
        )
        clear_button.pack(side=tk.LEFT, padx=5)
        
        self.debug_log("Simulation controls setup completed")
    
    def setup_plot_area(self, parent):
        """Set up plot area with debug information."""
        self.debug_log("Setting up plot area...")
        
        plot_frame = ttk.LabelFrame(parent, text="プロット結果 (Debug Mode)", padding=5)
        plot_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create matplotlib figure
        self.fig = plt.figure(figsize=(8, 6))
        self.ax = self.fig.add_subplot(1, 1, 1)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add navigation toolbar
        toolbar = NavigationToolbar2Tk(self.canvas, plot_frame)
        toolbar.update()
        
        # Initial plot setup
        self.clear_plot()
        
        self.debug_log("Plot area setup completed")
    
    def on_model_changed(self, event=None):
        """Handle model type change with debug logging."""
        model_type = self.model_type_var.get()
        self.debug_log(f"Model changed to: {model_type}")
    
    def load_model_variables(self):
        """Load model variables with enhanced debug logging."""
        self.debug_log("Loading model variables...")
        
        model_type = self.model_type_var.get()
        self.debug_log(f"Loading variables for model: {model_type}")
        
        if not PYBAMM_AVAILABLE:
            # Mock variables for development
            self.debug_log("PyBamm not available, using mock variables")
            mock_variables = [
                "Terminal voltage [V]",
                "Current [A]", 
                "Discharge capacity [A.h]",
                "Electrolyte concentration [mol.m-3]",
                "Negative electrode potential [V]",
                "Positive electrode potential [V]",
                "Cell temperature [K]",
                "Negative particle surface concentration [mol.m-3]",
                "Positive particle surface concentration [mol.m-3]"
            ]
            self.available_variables = mock_variables
            self.variables_count = len(mock_variables)
        else:
            try:
                # Create model to get variables
                if model_type == 'DFN':
                    model = pybamm.lithium_ion.DFN()
                elif model_type == 'SPM':
                    model = pybamm.lithium_ion.SPM()
                elif model_type == 'SPMe':
                    model = pybamm.lithium_ion.SPMe()
                else:
                    raise ValueError(f"Unknown model type: {model_type}")
                
                # Get variable names
                self.available_variables = list(model.variable_names())
                self.variables_count = len(self.available_variables)
                
                self.debug_log(f"Loaded {self.variables_count} variables from PyBamm model")
                
            except Exception as e:
                self.debug_log(f"Error loading model variables: {e}", "ERROR")
                messagebox.showerror("エラー", f"モデル変数の読み込みに失敗しました: {e}")
                return
        
        # Update UI
        self.variables_count_label.config(text=f"変数: {self.variables_count}個")
        self.update_variables_list()
        
        # Update plot variable combo
        plot_vars = ["Terminal voltage [V]", "Current [A]", "Discharge capacity [A.h]"]
        available_plot_vars = [var for var in plot_vars if var in self.available_variables]
        self.plot_var_combo['values'] = available_plot_vars
        
        if available_plot_vars:
            self.plot_variable_var.set(available_plot_vars[0])
        
        self.debug_log(f"Model variables loaded successfully: {self.variables_count} variables")
    
    def update_variables_list(self):
        """Update variables listbox with search filter and debug logging."""
        search_term = self.variable_search_var.get().lower()
        
        if search_term:
            filtered_vars = [var for var in self.available_variables if search_term in var.lower()]
            self.debug_log(f"Filtered variables: {len(filtered_vars)} matches for '{search_term}'")
        else:
            filtered_vars = self.available_variables
        
        # Update listbox
        self.variables_listbox.delete(0, tk.END)
        for var in filtered_vars:
            self.variables_listbox.insert(tk.END, var)
    
    def on_search_changed(self, event=None):
        """Handle search term change with debug logging."""
        search_term = self.variable_search_var.get()
        self.debug_log(f"Search term changed: '{search_term}'")
        self.update_variables_list()
    
    def on_variable_selected(self, event=None):
        """Handle variable selection with debug logging."""
        selection = self.variables_listbox.curselection()
        if selection:
            variable = self.variables_listbox.get(selection[0])
            self.selected_variable_var.set(variable)
            self.selected_var_label.config(text=variable, foreground="black")
            self.debug_log(f"Variable selected: '{variable}'")
    
    def add_custom_variable(self):
        """Add a custom variable with enhanced debug logging."""
        variable = self.selected_variable_var.get()
        value_str = self.variable_value_var.get()
        
        self.debug_log(f"Adding custom variable: '{variable}' = '{value_str}'")
        
        if not variable:
            self.debug_log("No variable selected", "WARNING")
            messagebox.showwarning("警告", "変数を選択してください。")
            return
            
        if not value_str:
            self.debug_log("No value entered", "WARNING")
            messagebox.showwarning("警告", "値を入力してください。")
            return
            
        try:
            # Try to convert to float
            value = float(value_str)
            self.debug_log(f"Value converted to float: {value}")
            
            # Add to custom variables
            self.custom_variables[variable] = value
            self.debug_log(f"Custom variable added: {variable} = {value}")
            self.debug_log(f"Total custom variables: {len(self.custom_variables)}")
            
            # Update custom variables listbox
            self.update_custom_variables_list()
            
            # Clear inputs
            self.variable_value_var.set("")
            self.selected_variable_var.set("")
            self.selected_var_label.config(text="なし", foreground="gray")
            
        except ValueError as e:
            self.debug_log(f"Value conversion error: {e}", "ERROR")
            messagebox.showerror("エラー", "数値を入力してください。")
    
    def update_custom_variables_list(self):
        """Update the custom variables listbox with debug logging."""
        self.debug_log("Updating custom variables list...")
        
        self.custom_variables_listbox.delete(0, tk.END)
        for variable, value in self.custom_variables.items():
            display_text = f"{variable}: {value}"
            self.custom_variables_listbox.insert(tk.END, display_text)
            
        self.debug_log(f"Custom variables list updated: {len(self.custom_variables)} items")
    
    def remove_custom_variable(self):
        """Remove selected custom variable with debug logging."""
        selection = self.custom_variables_listbox.curselection()
        if selection:
            # Get variable name from display text
            display_text = self.custom_variables_listbox.get(selection[0])
            variable = display_text.split(":")[0]
            
            self.debug_log(f"Removing custom variable: '{variable}'")
            
            # Remove from custom variables
            if variable in self.custom_variables:
                del self.custom_variables[variable]
                self.update_custom_variables_list()
                self.debug_log(f"Custom variable removed: '{variable}'")
    
    def clear_custom_variables(self):
        """Clear all custom variables with debug logging."""
        count = len(self.custom_variables)
        self.debug_log(f"Clearing all custom variables: {count} items")
        
        self.custom_variables.clear()
        self.update_custom_variables_list()
        
        self.debug_log("All custom variables cleared")
    
    def run_simulation(self):
        """Run simulation with enhanced debug logging and error tracking."""
        self.debug_log("=== STARTING SIMULATION ===")
        
        if not self.custom_variables:
            self.debug_log("No custom variables set", "WARNING")
            messagebox.showwarning("警告", "カスタム変数を設定してください。")
            return
        
        self.debug_log(f"Custom variables: {self.custom_variables}")
        self.debug_log(f"Model type: {self.model_type_var.get()}")
        self.debug_log(f"Simulation time: {self.time_hours_var.get()} hours")
        self.debug_log(f"Plot variable: {self.plot_variable_var.get()}")
        
        # Disable run button
        self.run_button.config(state='disabled', text="実行中... (Debug)")
        
        # Run simulation in background thread
        def run_sim():
            try:
                self.debug_log("Starting simulation in background thread...")
                self.simulation_results = self._run_simulation_with_custom_vars_debug()
                self.debug_log("Simulation completed successfully")
                self.app.root.after(0, self._simulation_complete)
            except Exception as e:
                self.debug_log(f"Simulation error: {e}", "ERROR")
                self.debug_log(f"Traceback: {traceback.format_exc()}", "ERROR")
                self.app.root.after(0, lambda e=e: self._simulation_error(str(e)))
                
        thread = threading.Thread(target=run_sim)
        thread.daemon = True
        thread.start()
        
        self.debug_log("Simulation thread started")
    
    def _run_simulation_with_custom_vars_debug(self):
        """Run simulation with custom variables - Enhanced debug version."""
        self.debug_log("=== SIMULATION EXECUTION DEBUG ===")
        
        model_type = self.model_type_var.get()
        time_hours = self.time_hours_var.get()
        
        self.debug_log(f"Model: {model_type}, Time: {time_hours}h")
        self.debug_log(f"PyBamm available: {PYBAMM_AVAILABLE}")
        
        if not PYBAMM_AVAILABLE:
            self.debug_log("Using mock simulation...")
            # Mock simulation for development
            time.sleep(2)  # Simulate computation time
            n_points = int(time_hours * 100)
            time_data = np.linspace(0, time_hours * 3600, n_points)
            
            self.debug_log(f"Mock simulation: {n_points} time points")
            self.inspect_data_type(time_data, "time_data")
            
            # Generate mock data based on custom variables
            voltage_data = 4.2 - (4.2 - 3.0) * (time_data / (time_hours * 3600))
            current_data = np.ones(n_points) * -1.0
            capacity_data = np.linspace(0, 2.5, n_points)
            
            self.inspect_data_type(voltage_data, "voltage_data")
            self.inspect_data_type(current_data, "current_data")
            self.inspect_data_type(capacity_data, "capacity_data")
            
            # Check if custom variables should override default values
            for var_name, var_value in self.custom_variables.items():
                self.debug_log(f"Processing custom variable: {var_name} = {var_value}")
                self.inspect_data_type(var_value, f"custom_{var_name}")
                
                # Override with custom values if they match known variables
                if var_name == "Current [A]":
                    # This is where the error might occur - creating scalar instead of array
                    if isinstance(var_value, (int, float)):
                        self.debug_log(f"Converting scalar current {var_value} to array")
                        current_data = np.full(n_points, var_value)
                        self.inspect_data_type(current_data, "current_data_custom")
            
            results = {
                'time': time_data,
                'Terminal voltage [V]': voltage_data,
                'Current [A]': current_data,
                'Discharge capacity [A.h]': capacity_data,
                'custom_variables': self.custom_variables.copy()
            }
            
            self.debug_log("Mock simulation results created")
            for key, value in results.items():
                if key != 'custom_variables':
                    self.inspect_data_type(value, f"result_{key}")
            
            return results
        
        # Real PyBamm simulation with enhanced debugging
        try:
            self.debug_log("Creating PyBamm model...")
            
            # Create model
            if model_type == 'DFN':
                model = pybamm.lithium_ion.DFN()
            elif model_type == 'SPM':
                model = pybamm.lithium_ion.SPM()
            elif model_type == 'SPMe':
                model = pybamm.lithium_ion.SPMe()
            else:
                raise ValueError(f"Unknown model type: {model_type}")
            
            self.debug_log(f"Model created: {model_type}")
            
            # Set up parameters
            parameter_values = pybamm.ParameterValues("Chen2020")
            self.debug_log("Parameter values loaded")
            
            # Apply custom variables with detailed logging
            self.debug_log("Applying custom variables to parameters...")
            for variable, value in self.custom_variables.items():
                self.debug_log(f"Checking custom variable: {variable} = {value}")
                self.inspect_data_type(value, f"custom_param_{variable}")
                
                try:
                    # Try to set as parameter if it exists
                    if variable in parameter_values:
                        parameter_values[variable] = value
                        self.debug_log(f"Parameter set: {variable} = {value}")
                    else:
                        self.debug_log(f"Parameter not found in parameter_values: {variable}", "WARNING")
                except Exception as e:
                    self.debug_log(f"Failed to set parameter {variable}: {e}", "WARNING")
            
            # Create and run simulation
            self.debug_log("Creating simulation...")
            sim = pybamm.Simulation(
                model, 
                parameter_values=parameter_values,
                solver=pybamm.CasadiSolver(mode="safe")
            )
            
            # Run simulation
            n_points = max(100, int(time_hours * 60))
            t_eval = np.linspace(0, time_hours * 3600, n_points)
            self.debug_log(f"Running simulation with {n_points} time points...")
            self.inspect_data_type(t_eval, "t_eval")
            
            solution = sim.solve(t_eval)
            self.debug_log("PyBamm simulation completed")
            
            # Extract results with detailed debugging
            self.debug_log("Extracting simulation results...")
            results = {
                'time': solution.t,
                'custom_variables': self.custom_variables.copy()
            }
            
            self.inspect_data_type(solution.t, "solution_time")
            
            # Extract available variables with debugging
            plot_var = self.plot_variable_var.get()
            self.debug_log(f"Extracting plot variable: {plot_var}")
            
            if plot_var in solution:
                var_data = solution[plot_var].data
                self.debug_log(f"Plot variable data extracted: {plot_var}")
                self.inspect_data_type(var_data, f"plot_var_{plot_var}")
                results[plot_var] = var_data
            else:
                self.debug_log(f"Plot variable not found in solution: {plot_var}", "WARNING")
            
            # Try to get common variables
            common_vars = ["Terminal voltage [V]", "Current [A]", "Discharge capacity [A.h]"]
            for var in common_vars:
                if var in solution:
                    var_data = solution[var].data
                    self.debug_log(f"Common variable extracted: {var}")
                    self.inspect_data_type(var_data, f"common_var_{var}")
                    results[var] = var_data
                else:
                    self.debug_log(f"Common variable not found: {var}", "WARNING")
            
            self.debug_log("PyBamm simulation results extracted successfully")
            return results
            
        except Exception as e:
            self.debug_log(f"PyBamm simulation error: {e}", "ERROR")
            self.debug_log(f"Traceback: {traceback.format_exc()}", "ERROR")
            raise Exception(f"シミュレーション実行エラー: {e}")
    
    def _simulation_complete(self):
        """Handle simulation completion with debug logging."""
        self.debug_log("=== SIMULATION COMPLETED ===")
        
        self.run_button.config(state='normal', text="シミュレーション実行 (Debug)")
        
        # Debug simulation results
        if self.simulation_results:
            self.debug_log("Simulation results available:")
            for key, value in self.simulation_results.items():
                if key != 'custom_variables':
                    self.inspect_data_type(value, f"final_result_{key}")
        
        self.update_plot_debug()
        messagebox.showinfo("完了", "シミュレーションが完了しました。")
        
        self.debug_log("Simulation completion handled")
    
    def _simulation_error(self, error_msg):
        """Handle simulation error with debug logging."""
        self.debug_log(f"=== SIMULATION ERROR === {error_msg}", "ERROR")
        
        self.run_button.config(state='normal', text="シミュレーション実行 (Debug)")
        messagebox.showerror("エラー", f"シミュレーションエラー: {error_msg}")
        
        self.debug_log("Simulation error handled")
    
    def update_plot_debug(self):
        """Enhanced debug version of update_plot with comprehensive error tracking."""
        self.debug_log("=== PLOT UPDATE DEBUG ===")
        
        if not self.simulation_results:
            self.debug_log("No simulation results available", "WARNING")
            return
            
        plot_var = self.plot_variable_var.get()
        self.debug_log(f"Plot variable requested: '{plot_var}'")
        
        # Debug simulation results structure
        self.debug_log("Simulation results structure:")
        for key, value in self.simulation_results.items():
            if key != 'custom_variables':
                self.inspect_data_type(value, f"sim_result_{key}")
        
        if plot_var not in self.simulation_results:
            self.debug_log(f"Plot variable '{plot_var}' not found in results", "ERROR")
            available_vars = [k for k in self.simulation_results.keys() if k != 'custom_variables']
            self.debug_log(f"Available variables: {available_vars}")
            messagebox.showwarning("警告", f"変数 '{plot_var}' がシミュレーション結果に含まれていません。\n利用可能な変数: {available_vars}")
            return
            
        # Clear previous plot
        self.debug_log("Clearing previous plot...")
        self.ax.clear()
        
        # Get data with detailed debugging
        time_data = self.simulation_results['time']
        var_data = self.simulation_results[plot_var]
        
        self.debug_log("=== DATA EXTRACTION DEBUG ===")
        self.inspect_data_type(time_data, "time_data")
        self.inspect_data_type(var_data, f"var_data_{plot_var}")
        
        # Enhanced error handling and data type analysis
        try:
            self.debug_log("=== PLOTTING LOGIC DEBUG ===")
            
            # Step 1: Check if var_data is iterable
            is_iterable = hasattr(var_data, '__iter__') and not isinstance(var_data, str)
            self.debug_log(f"var_data is_iterable: {is_iterable}")
            
            if is_iterable:
                self.debug_log("var_data is iterable - checking length compatibility...")
                
                try:
                    var_data_len = len(var_data)
                    time_data_len = len(time_data)
                    self.debug_log(f"var_data length: {var_data_len}")
                    self.debug_log(f"time_data length: {time_data_len}")
                    
                    if var_data_len == time_data_len:
                        self.debug_log("Lengths match - plotting as array data")
                        self.ax.plot(time_data, var_data, 'b-', linewidth=2, label=plot_var)
                        plot_success = True
                        
                    elif var_data_len == 1:
                        self.debug_log("Single element array detected - converting to constant")
                        try:
                            constant_value = var_data[0] if hasattr(var_data, '__getitem__') else float(var_data)
                            self.debug_log(f"Extracted constant value: {constant_value}")
                            self.inspect_data_type(constant_value, "constant_value")
                            
                            var_data_expanded = np.full_like(time_data, constant_value)
                            self.debug_log("Created expanded constant array")
                            self.inspect_data_type(var_data_expanded, "var_data_expanded")
                            
                            self.ax.plot(time_data, var_data_expanded, 'b-', linewidth=2, 
                                       label=f"{plot_var} (定数値: {constant_value})")
                            plot_success = True
                            
                        except Exception as e:
                            self.debug_log(f"Error extracting constant value: {e}", "ERROR")
                            raise
                    else:
                        # Length mismatch error
                        error_msg = f"変数 '{plot_var}' のデータ長 ({var_data_len}) が時間データ長 ({time_data_len}) と一致しません。"
                        self.debug_log(f"Length mismatch: {error_msg}", "ERROR")
                        messagebox.showerror("エラー", error_msg)
                        return
                        
                except Exception as e:
                    self.debug_log(f"Error checking array lengths: {e}", "ERROR")
                    self.debug_log(f"Traceback: {traceback.format_exc()}", "ERROR")
                    raise
                    
            else:
                self.debug_log("var_data is not iterable - treating as scalar")
                
                try:
                    # Convert to scalar value
                    scalar_value = float(var_data)
                    self.debug_log(f"Converted to scalar: {scalar_value}")
                    self.inspect_data_type(scalar_value, "scalar_value")
                    
                    # Create constant array
                    var_data_expanded = np.full_like(time_data, scalar_value)
                    self.debug_log("Created expanded scalar array")
                    self.inspect_data_type(var_data_expanded, "var_data_expanded_scalar")
                    
                    self.ax.plot(time_data, var_data_expanded, 'b-', linewidth=2, 
                               label=f"{plot_var} (定数値: {scalar_value})")
                    plot_success = True
                    
                except (ValueError, TypeError) as e:
                    error_msg = f"変数 '{plot_var}' のデータを数値に変換できません: {var_data} (型: {type(var_data)})"
                    self.debug_log(f"Scalar conversion error: {error_msg}", "ERROR")
                    messagebox.showerror("エラー", error_msg)
                    return
                    
        except Exception as e:
            error_msg = f"プロット中にエラーが発生しました: {str(e)}"
            self.debug_log(f"Plotting error: {error_msg}", "ERROR")
            self.debug_log(f"Error details - Variable: {plot_var}, Data type: {type(var_data)}", "ERROR")
            self.debug_log(f"Traceback: {traceback.format_exc()}", "ERROR")
            
            # Show detailed error information
            detailed_error = f"""プロット中にエラーが発生しました:
エラー: {str(e)}
変数: {plot_var}
データ型: {type(var_data)}
データ値: {str(var_data)[:200]}...
時間データ型: {type(time_data)}
時間データ長: {len(time_data) if hasattr(time_data, '__len__') else 'N/A'}"""
            
            messagebox.showerror("詳細エラー情報", detailed_error)
            return
        
        # Set labels and title with debug info
        self.debug_log("Setting plot labels and title...")
        
        self.ax.set_xlabel("時間 [s]")
        self.ax.set_ylabel(plot_var)
        
        # Enhanced title with debug information
        custom_vars_count = len(self.custom_variables)
        debug_title = f"カスタム変数シミュレーション結果 (Debug)\n({custom_vars_count} 個のカスタム変数)"
        self.ax.set_title(debug_title)
        
        self.ax.grid(True, alpha=0.3)
        self.ax.legend()
        
        # Refresh canvas
        self.debug_log("Refreshing canvas...")
        self.canvas.draw()
        
        self.debug_log("=== PLOT UPDATE COMPLETED SUCCESSFULLY ===")
    
    def clear_plot(self):
        """Clear the plot with debug logging."""
        self.debug_log("Clearing plot...")
        
        self.ax.clear()
        self.ax.set_title("シミュレーション結果 (Debug Mode)")
        self.ax.set_xlabel("時間 [s]")
        self.ax.set_ylabel("値")
        self.ax.grid(True, alpha=0.3)
        
        # Add debug information to empty plot
        self.ax.text(0.5, 0.5, 'Debug Mode\nシミュレーション結果がここに表示されます', 
                    ha='center', va='center', transform=self.ax.transAxes,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.5))
        
        self.canvas.draw()
        self.simulation_results = None
        
        self.debug_log("Plot cleared")


# Test function for the debug version
def test_debug_version():
    """Test function to verify the debug version works correctly."""
    import tkinter as tk
    
    print("=== Testing Advanced Variables Tab Debug Version ===")
    
    # Create test application
    root = tk.Tk()
    root.title("Advanced Variables Debug Test")
    root.geometry("1200x800")
    
    # Mock app object
    class MockApp:
        def __init__(self, root):
            self.root = root
            self.simulation_results = None
    
    app = MockApp(root)
    
    # Create debug tab
    debug_tab = AdvancedVariablesTabDebug(root, app)
    debug_tab.frame.pack(fill=tk.BOTH, expand=True)
    
    print("Debug version created successfully")
    print("Features enabled:")
    print("- Enhanced logging with timestamps")
    print("- Comprehensive data type inspection")
    print("- Step-by-step error tracking")
    print("- Detailed simulation debugging")
    print("- Enhanced plotting with error analysis")
    
    # Start the application
    root.mainloop()

if __name__ == "__main__":
    test_debug_version()
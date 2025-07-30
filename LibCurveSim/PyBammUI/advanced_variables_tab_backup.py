#!/usr/bin/env python3
"""
Advanced Variables Tab for PyBamm UI
Allows users to specify custom variables from model.variable_names() and run simulations.
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
    """Advanced Variables Tab for custom variable specification and simulation."""
    
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
        
        # Initialize model variables cache
        self.model_variables = {}
        self.custom_variables = {}  # Store user-defined variable values
        self.simulation_results = None
        
    def setup_variables(self):
        """Set up tkinter variables for the UI."""
        # Model selection
        self.model_type_var = tk.StringVar(value="DFN")
        
        # Variable selection
        self.selected_variable_var = tk.StringVar()
        self.variable_value_var = tk.StringVar()
        self.variable_search_var = tk.StringVar()
        
        # Simulation settings
        self.time_hours_var = tk.DoubleVar(value=1.0)
        
        # Plot settings
        self.plot_variable_var = tk.StringVar(value="Terminal voltage [V]")
        
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
        self.setup_model_selection(left_frame)
        self.setup_variable_browser(left_frame)
        self.setup_custom_variables(left_frame)
        self.setup_simulation_controls(left_frame)
        
        # Set up plot area
        self.setup_plot_area()
        
    def setup_model_selection(self, parent):
        """Set up model selection controls."""
        model_frame = ttk.LabelFrame(parent, text="モデル選択", padding=10)
        model_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Model type selection
        ttk.Label(model_frame, text="モデルタイプ:").grid(row=0, column=0, sticky=tk.W, pady=2)
        model_combo = ttk.Combobox(
            model_frame, textvariable=self.model_type_var, width=15,
            values=["DFN", "SPM", "SPMe"], state="readonly"
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
        
    def setup_variable_browser(self, parent):
        """Set up variable browser controls."""
        browser_frame = ttk.LabelFrame(parent, text="変数ブラウザ", padding=10)
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
        
    def setup_custom_variables(self, parent):
        """Set up custom variables controls."""
        custom_frame = ttk.LabelFrame(parent, text="カスタム変数", padding=10)
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
        
    def setup_simulation_controls(self, parent):
        """Set up simulation control buttons."""
        sim_frame = ttk.LabelFrame(parent, text="シミュレーション", padding=10)
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
            button_frame, text="シミュレーション実行",
            command=self.run_simulation
        )
        self.run_button.pack(side=tk.LEFT, padx=5)
        
        # Clear plot button
        clear_plot_button = ttk.Button(
            button_frame, text="プロットクリア",
            command=self.clear_plot
        )
        clear_plot_button.pack(side=tk.LEFT, padx=5)
        
    def setup_plot_area(self):
        """Set up the plot area."""
        # Create matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.ax.set_title("シミュレーション結果")
        self.ax.set_xlabel("時間 [s]")
        self.ax.set_ylabel("値")
        self.ax.grid(True, alpha=0.3)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar
        toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        toolbar.update()
        
    def on_model_changed(self, event=None):
        """Handle model type change."""
        self.model_variables = {}
        self.variables_listbox.delete(0, tk.END)
        self.variables_count_label.config(text="変数: 未読み込み")
        
    def load_model_variables(self):
        """Load variables for the selected model."""
        model_type = self.model_type_var.get()
        
        if not PYBAMM_AVAILABLE:
            # Mock variables for development
            mock_variables = [
                "Terminal voltage [V]", "Current [A]", "Discharge capacity [A.h]",
                "Negative electrode potential [V]", "Positive electrode potential [V]",
                "Electrolyte concentration [mol.m-3]", "Cell temperature [K]",
                "Power [W]", "Resistance [Ohm]", "SOC", "Time [s]"
            ]
            self.model_variables[model_type] = mock_variables
            self.update_variables_list()
            self.variables_count_label.config(text=f"変数: {len(mock_variables)} (モック)")
            return
        
        try:
            # Create model
            if model_type == 'DFN':
                model = pybamm.lithium_ion.DFN()
            elif model_type == 'SPM':
                model = pybamm.lithium_ion.SPM()
            elif model_type == 'SPMe':
                model = pybamm.lithium_ion.SPMe()
            else:
                raise ValueError(f"Unknown model type: {model_type}")
            
            # Get variable names
            variables = model.variable_names()
            self.model_variables[model_type] = variables
            
            # Update UI
            self.update_variables_list()
            self.variables_count_label.config(text=f"変数: {len(variables)}")
            
            # Update plot variable combo
            common_plot_vars = [
                "Terminal voltage [V]", "Current [A]", "Discharge capacity [A.h]",
                "Power [W]", "SOC", "Cell temperature [K]"
            ]
            available_plot_vars = [var for var in common_plot_vars if var in variables]
            self.plot_var_combo['values'] = available_plot_vars
            if available_plot_vars:
                self.plot_variable_var.set(available_plot_vars[0])
            
        except Exception as e:
            messagebox.showerror("エラー", f"変数の読み込みに失敗しました: {e}")
            
    def update_variables_list(self):
        """Update the variables listbox."""
        model_type = self.model_type_var.get()
        if model_type not in self.model_variables:
            return
        
        variables = self.model_variables[model_type]
        search_term = self.variable_search_var.get().lower()
        
        # Filter variables based on search term
        if search_term:
            filtered_vars = [var for var in variables if search_term in var.lower()]
        else:
            filtered_vars = variables
        
        # Update listbox
        self.variables_listbox.delete(0, tk.END)
        for var in filtered_vars:
            self.variables_listbox.insert(tk.END, var)
            
    def on_search_changed(self, event=None):
        """Handle search term change."""
        self.update_variables_list()
        
    def on_variable_selected(self, event=None):
        """Handle variable selection."""
        selection = self.variables_listbox.curselection()
        if selection:
            variable = self.variables_listbox.get(selection[0])
            self.selected_variable_var.set(variable)
            self.selected_var_label.config(text=variable, foreground="black")
            
    def add_custom_variable(self):
        """Add a custom variable with its value."""
        variable = self.selected_variable_var.get()
        value_str = self.variable_value_var.get()
        
        if not variable:
            messagebox.showwarning("警告", "変数を選択してください。")
            return
            
        if not value_str:
            messagebox.showwarning("警告", "値を入力してください。")
            return
            
        try:
            # Try to convert to float
            value = float(value_str)
            
            # Add to custom variables
            self.custom_variables[variable] = value
            
            # Update custom variables listbox
            self.update_custom_variables_list()
            
            # Clear inputs
            self.variable_value_var.set("")
            self.selected_variable_var.set("")
            self.selected_var_label.config(text="なし", foreground="gray")
            
        except ValueError:
            messagebox.showerror("エラー", "数値を入力してください。")
            
    def update_custom_variables_list(self):
        """Update the custom variables listbox."""
        self.custom_variables_listbox.delete(0, tk.END)
        for variable, value in self.custom_variables.items():
            display_text = f"{variable}: {value}"
            self.custom_variables_listbox.insert(tk.END, display_text)
            
    def remove_custom_variable(self):
        """Remove selected custom variable."""
        selection = self.custom_variables_listbox.curselection()
        if selection:
            # Get variable name from display text
            display_text = self.custom_variables_listbox.get(selection[0])
            variable = display_text.split(":")[0]
            
            # Remove from custom variables
            if variable in self.custom_variables:
                del self.custom_variables[variable]
                self.update_custom_variables_list()
                
    def clear_custom_variables(self):
        """Clear all custom variables."""
        self.custom_variables.clear()
        self.update_custom_variables_list()
        
    def run_simulation(self):
        """Run simulation with custom variables."""
        if not self.custom_variables:
            messagebox.showwarning("警告", "カスタム変数を設定してください。")
            return
            
        # Disable run button
        self.run_button.config(state='disabled', text="実行中...")
        
        # Run simulation in background thread
        def run_sim():
            try:
                self.simulation_results = self._run_simulation_with_custom_vars()
                self.app.root.after(0, self._simulation_complete)
            except Exception as e:
                self.app.root.after(0, lambda e=e: self._simulation_error(str(e)))
                
        thread = threading.Thread(target=run_sim)
        thread.daemon = True
        thread.start()
        
    def _run_simulation_with_custom_vars(self):
        """Run simulation with custom variables (background thread)."""
        model_type = self.model_type_var.get()
        time_hours = self.time_hours_var.get()
        
        if not PYBAMM_AVAILABLE:
            # Mock simulation for development
            time.sleep(2)  # Simulate computation time
            n_points = int(time_hours * 100)
            time_data = np.linspace(0, time_hours * 3600, n_points)
            
            # Generate mock data based on custom variables
            voltage_data = 4.2 - (4.2 - 3.0) * (time_data / (time_hours * 3600))
            current_data = np.ones(n_points) * -1.0
            capacity_data = np.linspace(0, 2.5, n_points)
            
            return {
                'time': time_data,
                'Terminal voltage [V]': voltage_data,
                'Current [A]': current_data,
                'Discharge capacity [A.h]': capacity_data,
                'custom_variables': self.custom_variables.copy()
            }
        
        try:
            # Create model
            if model_type == 'DFN':
                model = pybamm.lithium_ion.DFN()
            elif model_type == 'SPM':
                model = pybamm.lithium_ion.SPM()
            elif model_type == 'SPMe':
                model = pybamm.lithium_ion.SPMe()
            else:
                raise ValueError(f"Unknown model type: {model_type}")
            
            # Set up parameters
            parameter_values = pybamm.ParameterValues("Chen2020")
            
            # Apply custom variables (this is a simplified approach)
            # In practice, you might need more sophisticated parameter mapping
            for variable, value in self.custom_variables.items():
                try:
                    # Try to set as parameter if it exists
                    if variable in parameter_values:
                        parameter_values[variable] = value
                except:
                    pass  # Skip if parameter cannot be set
            
            # Create and run simulation
            sim = pybamm.Simulation(
                model, 
                parameter_values=parameter_values,
                solver=pybamm.CasadiSolver(mode="safe")
            )
            
            # Run simulation
            n_points = max(100, int(time_hours * 60))
            t_eval = np.linspace(0, time_hours * 3600, n_points)
            solution = sim.solve(t_eval)
            
            # Extract results
            results = {
                'time': solution.t,
                'custom_variables': self.custom_variables.copy()
            }
            
            # Extract available variables
            plot_var = self.plot_variable_var.get()
            if plot_var in solution:
                results[plot_var] = solution[plot_var].data
            
            # Try to get common variables
            common_vars = ["Terminal voltage [V]", "Current [A]", "Discharge capacity [A.h]"]
            for var in common_vars:
                if var in solution:
                    results[var] = solution[var].data
            
            return results
            
        except Exception as e:
            raise Exception(f"シミュレーション実行エラー: {e}")
            
    def _simulation_complete(self):
        """Handle simulation completion."""
        self.run_button.config(state='normal', text="シミュレーション実行")
        self.update_plot()
        messagebox.showinfo("完了", "シミュレーションが完了しました。")
        
    def _simulation_error(self, error_msg):
        """Handle simulation error."""
        self.run_button.config(state='normal', text="シミュレーション実行")
        messagebox.showerror("エラー", f"シミュレーションエラー: {error_msg}")
        
    def update_plot(self):
        """Update the plot with simulation results."""
        if not self.simulation_results:
            return
            
        plot_var = self.plot_variable_var.get()
        if plot_var not in self.simulation_results:
            messagebox.showwarning("警告", f"変数 '{plot_var}' がシミュレーション結果に含まれていません。")
            return
            
        # Clear previous plot
        self.ax.clear()
        
        # Plot data
        time_data = self.simulation_results['time']
        var_data = self.simulation_results[plot_var]
        
        # Handle case where var_data might be a scalar value (fix for "int object is not iterable" error)
        try:
            # Check if var_data is iterable and has the same length as time_data
            if hasattr(var_data, '__iter__') and not isinstance(var_data, str):
                # var_data is iterable (array-like)
                if len(var_data) == len(time_data):
                    self.ax.plot(time_data, var_data, 'b-', linewidth=2, label=plot_var)
                else:
                    # Length mismatch - create constant array
                    if len(var_data) == 1:
                        # Single value array - broadcast to match time_data length
                        constant_value = var_data[0] if hasattr(var_data, '__getitem__') else float(var_data)
                        var_data_expanded = np.full_like(time_data, constant_value)
                        self.ax.plot(time_data, var_data_expanded, 'b-', linewidth=2, label=f"{plot_var} (定数値: {constant_value})")
                    else:
                        # Multiple values but wrong length - show error
                        messagebox.showerror("エラー", f"変数 '{plot_var}' のデータ長 ({len(var_data)}) が時間データ長 ({len(time_data)}) と一致しません。")
                        return
            else:
                # var_data is a scalar value - create constant array
                try:
                    scalar_value = float(var_data)
                    var_data_expanded = np.full_like(time_data, scalar_value)
                    self.ax.plot(time_data, var_data_expanded, 'b-', linewidth=2, label=f"{plot_var} (定数値: {scalar_value})")
                except (ValueError, TypeError):
                    messagebox.showerror("エラー", f"変数 '{plot_var}' のデータを数値に変換できません: {var_data}")
                    return
                    
        except Exception as e:
            messagebox.showerror("エラー", f"プロット中にエラーが発生しました: {str(e)}\n変数: {plot_var}\nデータ型: {type(var_data)}")
            return
        
        # Set labels and title
        self.ax.set_xlabel("時間 [s]")
        self.ax.set_ylabel(plot_var)
        self.ax.set_title(f"カスタム変数シミュレーション結果\n({len(self.custom_variables)} 個のカスタム変数)")
        self.ax.grid(True, alpha=0.3)
        self.ax.legend()
        
        # Refresh canvas
        self.canvas.draw()
        
    def clear_plot(self):
        """Clear the plot."""
        self.ax.clear()
        self.ax.set_title("シミュレーション結果")
        self.ax.set_xlabel("時間 [s]")
        self.ax.set_ylabel("値")
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()
        self.simulation_results = None
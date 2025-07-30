"""
PyBamm Simulation Tab Module

This module provides the simulation tab for the PyBamm UI application.
It allows users to set simulation parameters and run PyBamm simulations.
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


class SimulationTab:
    """
    Class for the PyBamm simulation tab.
    """
    
    def __init__(self, parent, app):
        """
        Initialize the simulation tab.
        
        Args:
            parent: Parent widget
            app: Main application instance
        """
        self.app = app
        self.frame = ttk.Frame(parent)
        
        # Initialize variables for parameters
        self.setup_variables()
        
        # Create the UI
        self.setup_ui()
        
        # Initialize plot
        self.setup_plot_area()
    
    def setup_variables(self):
        """Set up tkinter variables for parameters."""
        # Battery parameters
        self.capacity_var = tk.DoubleVar(value=2.5)  # Ah
        self.current_var = tk.DoubleVar(value=1.0)   # A
        self.temperature_var = tk.DoubleVar(value=25.0)  # °C
        
        # Voltage limits
        self.v_max_var = tk.DoubleVar(value=4.2)  # V
        self.v_min_var = tk.DoubleVar(value=3.0)  # V
        
        # Simulation parameters
        self.time_hours_var = tk.DoubleVar(value=1.0)  # hours
        self.model_type_var = tk.StringVar(value="DFN")
        
        # Plot type
        self.plot_type_var = tk.StringVar(value="voltage_time")
    
    def setup_ui(self):
        """Set up the user interface."""
        # Create main paned window
        main_paned = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel for parameters
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        # Right panel for plots
        self.plot_frame = ttk.Frame(main_paned)
        main_paned.add(self.plot_frame, weight=3)
        
        # Set up parameter controls
        self.setup_parameter_controls(left_frame)
        
        # Set up plot controls
        self.setup_plot_controls()
    
    def setup_parameter_controls(self, parent):
        """Set up parameter input controls."""
        # Main parameters frame
        params_frame = ttk.LabelFrame(parent, text="シミュレーションパラメータ", padding=10)
        params_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Battery parameters
        battery_frame = ttk.LabelFrame(params_frame, text="バッテリーパラメータ", padding=5)
        battery_frame.pack(fill=tk.X, pady=5)
        
        # Capacity
        ttk.Label(battery_frame, text="容量 (Ah):").grid(row=0, column=0, sticky=tk.W, pady=2)
        capacity_spinbox = ttk.Spinbox(
            battery_frame, from_=0.1, to=10.0, increment=0.1, width=10,
            textvariable=self.capacity_var, format="%.1f"
        )
        capacity_spinbox.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Current
        ttk.Label(battery_frame, text="電流 (A):").grid(row=1, column=0, sticky=tk.W, pady=2)
        current_spinbox = ttk.Spinbox(
            battery_frame, from_=-10.0, to=10.0, increment=0.1, width=10,
            textvariable=self.current_var, format="%.1f"
        )
        current_spinbox.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        ttk.Label(battery_frame, text="(負: 放電, 正: 充電)", font=('TkDefaultFont', 8)).grid(row=1, column=2, sticky=tk.W, padx=5)
        
        # Temperature
        ttk.Label(battery_frame, text="温度 (°C):").grid(row=2, column=0, sticky=tk.W, pady=2)
        temp_spinbox = ttk.Spinbox(
            battery_frame, from_=-20.0, to=60.0, increment=1.0, width=10,
            textvariable=self.temperature_var, format="%.1f"
        )
        temp_spinbox.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Voltage limits
        voltage_frame = ttk.LabelFrame(params_frame, text="電圧制限", padding=5)
        voltage_frame.pack(fill=tk.X, pady=5)
        
        # Max voltage
        ttk.Label(voltage_frame, text="最大電圧 (V):").grid(row=0, column=0, sticky=tk.W, pady=2)
        v_max_spinbox = ttk.Spinbox(
            voltage_frame, from_=3.0, to=5.0, increment=0.1, width=10,
            textvariable=self.v_max_var, format="%.1f"
        )
        v_max_spinbox.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Min voltage
        ttk.Label(voltage_frame, text="最小電圧 (V):").grid(row=1, column=0, sticky=tk.W, pady=2)
        v_min_spinbox = ttk.Spinbox(
            voltage_frame, from_=2.0, to=4.0, increment=0.1, width=10,
            textvariable=self.v_min_var, format="%.1f"
        )
        v_min_spinbox.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Simulation parameters
        sim_frame = ttk.LabelFrame(params_frame, text="シミュレーション設定", padding=5)
        sim_frame.pack(fill=tk.X, pady=5)
        
        # Simulation time
        ttk.Label(sim_frame, text="シミュレーション時間 (時間):").grid(row=0, column=0, sticky=tk.W, pady=2)
        time_spinbox = ttk.Spinbox(
            sim_frame, from_=0.1, to=24.0, increment=0.1, width=10,
            textvariable=self.time_hours_var, format="%.1f"
        )
        time_spinbox.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Model type
        ttk.Label(sim_frame, text="モデルタイプ:").grid(row=1, column=0, sticky=tk.W, pady=2)
        model_combo = ttk.Combobox(
            sim_frame, textvariable=self.model_type_var, width=10,
            values=["DFN", "SPM", "SPMe"], state="readonly"
        )
        model_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Control buttons
        button_frame = ttk.Frame(params_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Run simulation button
        self.run_button = ttk.Button(
            button_frame, text="シミュレーション実行",
            command=self.run_simulation
        )
        self.run_button.pack(side=tk.LEFT, padx=5)
        
        # Reset button
        reset_button = ttk.Button(
            button_frame, text="リセット",
            command=self.reset_parameters
        )
        reset_button.pack(side=tk.LEFT, padx=5)
        
        # Clear plot button
        clear_button = ttk.Button(
            button_frame, text="プロットクリア",
            command=self.clear_plot
        )
        clear_button.pack(side=tk.LEFT, padx=5)
    
    def setup_plot_controls(self):
        """Set up plot control area."""
        # Plot control frame
        control_frame = ttk.Frame(self.plot_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Plot type selection
        ttk.Label(control_frame, text="プロットタイプ:").pack(side=tk.LEFT)
        plot_type_combo = ttk.Combobox(
            control_frame, textvariable=self.plot_type_var, width=20,
            values=["voltage_time", "current_time", "voltage_capacity", "power_time", 
                   "voltage_components", "voltage_components_split"],
            state="readonly"
        )
        plot_type_combo.pack(side=tk.LEFT, padx=5)
        plot_type_combo.bind("<<ComboboxSelected>>", self.update_plot)
    
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
    
    def run_simulation(self):
        """Run the PyBamm simulation with the current parameters."""
        try:
            # Get parameters
            capacity = self.capacity_var.get()
            current = self.current_var.get()
            temperature = self.temperature_var.get() + 273.15  # Convert to Kelvin
            v_max = self.v_max_var.get()
            v_min = self.v_min_var.get()
            time_hours = self.time_hours_var.get()
            model_type = self.model_type_var.get()
            
            # Validate parameters
            if capacity <= 0 or time_hours <= 0:
                messagebox.showerror("エラー", "容量とシミュレーション時間は正の値を入力してください。")
                return
            
            if v_max <= v_min:
                messagebox.showerror("エラー", "最大電圧は最小電圧より大きい値を入力してください。")
                return
            
            # Update simulator parameters
            self.app.simulator.set_parameters(
                capacity=capacity,
                current=current,
                v_min=v_min,
                v_max=v_max,
                temperature=temperature
            )
            
            # Disable run button during simulation
            self.run_button.config(state=tk.DISABLED)
            
            # Run simulation in background
            self.app.run_in_background(
                "PyBammシミュレーション実行中...",
                lambda: self._run_simulation_thread(time_hours, model_type)
            )
            
        except tk.TclError:
            messagebox.showerror("エラー", "無効なパラメータ値です。数値を入力してください。")
    
    def _run_simulation_thread(self, time_hours, model_type):
        """
        Run the simulation in a separate thread.
        
        Args:
            time_hours: Simulation time in hours
            model_type: PyBamm model type
        """
        try:
            # Run simulation
            results = self.app.simulator.run_simulation(time_hours, model_type)
            
            # Store results
            self.app.simulation_results = results
            
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
    
    def update_plot(self, event=None):
        """
        Update the plot with the current simulation results.
        
        Args:
            event: Event that triggered the update (optional)
        """
        # Check if we have results
        if self.app.simulation_results is None:
            return
        
        # Clear figure
        self.fig.clear()
        
        # Get plot type
        plot_type = self.plot_type_var.get()
        
        if plot_type == "voltage_time":
            self._plot_voltage_time()
        elif plot_type == "current_time":
            self._plot_current_time()
        elif plot_type == "voltage_capacity":
            self._plot_voltage_capacity()
        elif plot_type == "power_time":
            self._plot_power_time()
        elif plot_type == "voltage_components":
            self._plot_voltage_components()
        elif plot_type == "voltage_components_split":
            self._plot_voltage_components(split_by_electrode=True)
        
        # Update canvas
        self.fig.tight_layout()
        self.canvas.draw()
    
    def _plot_voltage_time(self):
        """Plot voltage vs time."""
        results = self.app.simulation_results
        
        ax = self.fig.add_subplot(1, 1, 1)
        ax.plot(results['time'] / 3600, results['voltage'], 'b-', linewidth=2)
        ax.set_xlabel('時間 (h)')
        ax.set_ylabel('電圧 (V)')
        ax.set_title('電圧 vs 時間')
        ax.grid(True, alpha=0.3)
    
    def _plot_current_time(self):
        """Plot current vs time."""
        results = self.app.simulation_results
        
        ax = self.fig.add_subplot(1, 1, 1)
        ax.plot(results['time'] / 3600, results['current'], 'r-', linewidth=2)
        ax.set_xlabel('時間 (h)')
        ax.set_ylabel('電流 (A)')
        ax.set_title('電流 vs 時間')
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    
    def _plot_voltage_capacity(self):
        """Plot voltage vs capacity."""
        results = self.app.simulation_results
        
        if results['capacity'] is not None:
            ax = self.fig.add_subplot(1, 1, 1)
            ax.plot(results['capacity'], results['voltage'], 'g-', linewidth=2)
            ax.set_xlabel('容量 (Ah)')
            ax.set_ylabel('電圧 (V)')
            ax.set_title('電圧 vs 容量')
            ax.grid(True, alpha=0.3)
        else:
            ax = self.fig.add_subplot(1, 1, 1)
            ax.text(0.5, 0.5, '容量データが利用できません', 
                   ha='center', va='center', transform=ax.transAxes)
    
    def _plot_power_time(self):
        """Plot power vs time."""
        results = self.app.simulation_results
        
        # Calculate power
        power = results['voltage'] * results['current']
        
        ax = self.fig.add_subplot(1, 1, 1)
        ax.plot(results['time'] / 3600, power, 'm-', linewidth=2)
        ax.set_xlabel('時間 (h)')
        ax.set_ylabel('電力 (W)')
        ax.set_title('電力 vs 時間')
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    
    def _plot_voltage_components(self, split_by_electrode=False):
        """
        Plot voltage components showing internal resistance elements.
        
        Args:
            split_by_electrode: If True, split components by electrode
        """
        results = self.app.simulation_results
        
        # Check if voltage components data is available
        if 'voltage_components' not in results or not results['voltage_components']:
            ax = self.fig.add_subplot(1, 1, 1)
            ax.text(0.5, 0.5, '電圧成分データが利用できません\n(PyBammシミュレーションが必要)', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)
            return
        
        voltage_components = results['voltage_components']
        time_hours = results['time'] / 3600
        
        ax = self.fig.add_subplot(1, 1, 1)
        
        # Define colors for different components
        colors = {
            'ocv': '#1f77b4',           # Blue
            'ohmic': '#ff7f0e',         # Orange
            'concentration': '#2ca02c', # Green
            'reaction': '#d62728',      # Red
            'negative_electrode': '#9467bd', # Purple
            'positive_electrode': '#8c564b', # Brown
            'neg_ocv': '#e377c2',       # Pink
            'pos_ocv': '#7f7f7f',       # Gray
            'neg_reaction': '#bcbd22',  # Olive
            'pos_reaction': '#17becf',  # Cyan
            'electrolyte_ohmic': '#ff9896', # Light red
            'solid_ohmic': '#98df8a'    # Light green
        }
        
        # Define Japanese labels for components
        labels = {
            'ocv': '開回路電圧',
            'ohmic': 'オーム損失',
            'concentration': '濃度過電圧',
            'reaction': '反応過電圧',
            'negative_electrode': '負極電位',
            'positive_electrode': '正極電位',
            'neg_ocv': '負極開回路電位',
            'pos_ocv': '正極開回路電位',
            'neg_reaction': '負極反応過電圧',
            'pos_reaction': '正極反応過電圧',
            'electrolyte_ohmic': '電解液オーム損失',
            'solid_ohmic': '固相オーム損失'
        }
        
        if split_by_electrode:
            # Plot components split by electrode
            ax.set_title('電圧成分 (電極別)')
            
            # Group components by electrode
            negative_components = ['negative_electrode', 'neg_ocv', 'neg_reaction']
            positive_components = ['positive_electrode', 'pos_ocv', 'pos_reaction']
            general_components = ['ocv', 'ohmic', 'concentration', 'reaction', 
                                'electrolyte_ohmic', 'solid_ohmic']
            
            # Plot negative electrode components
            for component in negative_components:
                if component in voltage_components:
                    ax.plot(time_hours, voltage_components[component], 
                           color=colors.get(component, 'blue'), 
                           linewidth=2, linestyle='--',
                           label=f'負極: {labels.get(component, component)}')
            
            # Plot positive electrode components
            for component in positive_components:
                if component in voltage_components:
                    ax.plot(time_hours, voltage_components[component], 
                           color=colors.get(component, 'red'), 
                           linewidth=2, linestyle='-.',
                           label=f'正極: {labels.get(component, component)}')
            
            # Plot general components
            for component in general_components:
                if component in voltage_components:
                    ax.plot(time_hours, voltage_components[component], 
                           color=colors.get(component, 'black'), 
                           linewidth=2,
                           label=labels.get(component, component))
        else:
            # Plot all components together
            ax.set_title('電圧成分')
            
            for component, data in voltage_components.items():
                ax.plot(time_hours, data, 
                       color=colors.get(component, 'black'), 
                       linewidth=2,
                       label=labels.get(component, component))
        
        # Add terminal voltage for reference
        ax.plot(time_hours, results['voltage'], 'k-', linewidth=3, 
               label='端子電圧', alpha=0.7)
        
        ax.set_xlabel('時間 (h)')
        ax.set_ylabel('電圧 (V)')
        ax.grid(True, alpha=0.3)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Adjust layout to accommodate legend
        self.fig.subplots_adjust(right=0.75)
    
    def plot_voltage_components(self, split_by_electrode=False):
        """
        Public method to plot voltage components.
        This method can be called from external code.
        
        Args:
            split_by_electrode: If True, split components by electrode
        """
        # Check if we have results
        if self.app.simulation_results is None:
            print("No simulation results available. Please run a simulation first.")
            return
        
        # Clear figure
        self.fig.clear()
        
        # Plot voltage components
        self._plot_voltage_components(split_by_electrode=split_by_electrode)
        
        # Update canvas
        self.fig.tight_layout()
        self.canvas.draw()
    
    def reset_parameters(self):
        """Reset parameters to default values."""
        self.capacity_var.set(2.5)
        self.current_var.set(1.0)
        self.temperature_var.set(25.0)
        self.v_max_var.set(4.2)
        self.v_min_var.set(3.0)
        self.time_hours_var.set(1.0)
        self.model_type_var.set("DFN")
        self.plot_type_var.set("voltage_time")
    
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
        self.app.simulation_results = None
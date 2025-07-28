"""
Simulation Tab Module

This module provides the simulation tab for the battery simulation and analysis tool.
It allows users to set simulation parameters and run simulations.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
import threading
import time


class SimulationTab:
    """
    Class for the simulation tab.
    """
    
    def __init__(self, parent, app):
        """
        Initialize the simulation tab.
        
        Args:
            parent: Parent widget
            app: Main application instance
        """
        self.frame = ttk.Frame(parent)
        self.app = app
        
        # Create frames
        self.setup_frames()
        
        # Create parameter controls
        self.setup_battery_parameters()
        self.setup_degradation_parameters()
        self.setup_simulation_parameters()
        
        # Create simulation controls
        self.setup_simulation_controls()
        
        # Create plot area
        self.setup_plot_area()
    
    def setup_frames(self):
        """Set up the frames for the tab."""
        # Main layout: parameters on left, plot on right
        self.params_frame = ttk.Frame(self.frame, padding=(10, 10))
        self.params_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        self.plot_frame = ttk.Frame(self.frame, padding=(10, 10))
        self.plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Parameter sections
        self.battery_frame = ttk.LabelFrame(self.params_frame, text="電池パラメータ", padding=(10, 5))
        self.battery_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.degradation_frame = ttk.LabelFrame(self.params_frame, text="劣化モデルパラメータ", padding=(10, 5))
        self.degradation_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.simulation_frame = ttk.LabelFrame(self.params_frame, text="シミュレーションパラメータ", padding=(10, 5))
        self.simulation_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.controls_frame = ttk.Frame(self.params_frame, padding=(0, 10))
        self.controls_frame.pack(fill=tk.X)
    
    def setup_battery_parameters(self):
        """Set up the battery parameter controls."""
        # Initial capacity
        ttk.Label(self.battery_frame, text="初期容量 (Ah):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.capacity_var = tk.DoubleVar(value=self.app.simulator.initial_capacity)
        ttk.Entry(self.battery_frame, textvariable=self.capacity_var, width=10).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # Initial resistance
        ttk.Label(self.battery_frame, text="初期内部抵抗 (Ohm):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.resistance_var = tk.DoubleVar(value=self.app.simulator.initial_resistance)
        ttk.Entry(self.battery_frame, textvariable=self.resistance_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=2)
    
    def setup_degradation_parameters(self):
        """Set up the degradation parameter controls."""
        # Capacity fade parameters
        ttk.Label(self.degradation_frame, text="容量劣化パラメータ A:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.capacity_fade_A_var = tk.DoubleVar(value=self.app.simulator.capacity_fade_A)
        ttk.Entry(self.degradation_frame, textvariable=self.capacity_fade_A_var, width=10).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(self.degradation_frame, text="容量劣化パラメータ B:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.capacity_fade_B_var = tk.DoubleVar(value=self.app.simulator.capacity_fade_B)
        ttk.Entry(self.degradation_frame, textvariable=self.capacity_fade_B_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # Resistance growth parameters
        ttk.Label(self.degradation_frame, text="抵抗増加パラメータ C:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.resistance_growth_C_var = tk.DoubleVar(value=self.app.simulator.resistance_growth_C)
        ttk.Entry(self.degradation_frame, textvariable=self.resistance_growth_C_var, width=10).grid(row=2, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(self.degradation_frame, text="抵抗増加パラメータ D:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.resistance_growth_D_var = tk.DoubleVar(value=self.app.simulator.resistance_growth_D)
        ttk.Entry(self.degradation_frame, textvariable=self.resistance_growth_D_var, width=10).grid(row=3, column=1, sticky=tk.W, pady=2)
    
    def setup_simulation_parameters(self):
        """Set up the simulation parameter controls."""
        # Number of cycles
        ttk.Label(self.simulation_frame, text="サイクル数:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.num_cycles_var = tk.IntVar(value=20)
        ttk.Entry(self.simulation_frame, textvariable=self.num_cycles_var, width=10).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # C-rate
        ttk.Label(self.simulation_frame, text="C-レート:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.c_rate_var = tk.DoubleVar(value=self.app.simulator.c_rate)
        ttk.Entry(self.simulation_frame, textvariable=self.c_rate_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # Voltage limits
        ttk.Label(self.simulation_frame, text="最大電圧 (V):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.v_max_var = tk.DoubleVar(value=self.app.simulator.v_max)
        ttk.Entry(self.simulation_frame, textvariable=self.v_max_var, width=10).grid(row=2, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(self.simulation_frame, text="最小電圧 (V):").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.v_min_var = tk.DoubleVar(value=self.app.simulator.v_min)
        ttk.Entry(self.simulation_frame, textvariable=self.v_min_var, width=10).grid(row=3, column=1, sticky=tk.W, pady=2)
        
        # End current ratio
        ttk.Label(self.simulation_frame, text="終止電流比:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.end_current_ratio_var = tk.DoubleVar(value=self.app.simulator.end_current_ratio)
        ttk.Entry(self.simulation_frame, textvariable=self.end_current_ratio_var, width=10).grid(row=4, column=1, sticky=tk.W, pady=2)
        
        # Time step
        ttk.Label(self.simulation_frame, text="時間ステップ (秒):").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.dt_var = tk.DoubleVar(value=self.app.simulator.dt)
        ttk.Entry(self.simulation_frame, textvariable=self.dt_var, width=10).grid(row=5, column=1, sticky=tk.W, pady=2)
    
    def setup_simulation_controls(self):
        """Set up the simulation control buttons."""
        # Run button
        self.run_button = ttk.Button(
            self.controls_frame,
            text="シミュレーション実行",
            command=self.run_simulation
        )
        self.run_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Reset button
        self.reset_button = ttk.Button(
            self.controls_frame,
            text="リセット",
            command=self.reset_parameters
        )
        self.reset_button.pack(side=tk.LEFT)
        
        # Plot selection
        ttk.Label(self.controls_frame, text="表示:").pack(side=tk.LEFT, padx=(10, 5))
        self.plot_type_var = tk.StringVar(value="charge_discharge")
        plot_type_combo = ttk.Combobox(
            self.controls_frame,
            textvariable=self.plot_type_var,
            values=["charge_discharge", "capacity_retention", "resistance_growth"],
            state="readonly",
            width=15
        )
        plot_type_combo.pack(side=tk.LEFT)
        plot_type_combo.bind("<<ComboboxSelected>>", self.update_plot)
    
    def setup_plot_area(self):
        """Set up the plot area."""
        # Create figure and canvas
        self.fig = plt.figure(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        self.toolbar.update()
        
        # Initialize with empty plot
        self.fig.text(0.5, 0.5, "シミュレーション結果がここに表示されます", 
                     ha='center', va='center', fontsize=12)
        self.canvas.draw()
    
    def run_simulation(self):
        """Run the simulation with the current parameters."""
        # Get parameters
        try:
            # Battery parameters
            capacity = self.capacity_var.get()
            resistance = self.resistance_var.get()
            
            # Degradation parameters
            capacity_fade_A = self.capacity_fade_A_var.get()
            capacity_fade_B = self.capacity_fade_B_var.get()
            resistance_growth_C = self.resistance_growth_C_var.get()
            resistance_growth_D = self.resistance_growth_D_var.get()
            
            # Simulation parameters
            num_cycles = self.num_cycles_var.get()
            c_rate = self.c_rate_var.get()
            v_max = self.v_max_var.get()
            v_min = self.v_min_var.get()
            end_current_ratio = self.end_current_ratio_var.get()
            dt = self.dt_var.get()
            
            # Validate parameters
            if capacity <= 0 or resistance <= 0 or num_cycles <= 0 or c_rate <= 0 or dt <= 0:
                messagebox.showerror("エラー", "パラメータは正の値を入力してください。")
                return
            
            # Update simulator parameters
            self.app.simulator.set_battery_parameters(capacity, resistance)
            self.app.simulator.set_degradation_parameters(
                capacity_fade_A, capacity_fade_B,
                resistance_growth_C, resistance_growth_D
            )
            self.app.simulator.set_simulation_parameters(
                c_rate, v_max, v_min, end_current_ratio, dt
            )
            
            # Disable run button during simulation
            self.run_button.config(state=tk.DISABLED)
            
            # Run simulation in background
            self.app.run_in_background(
                "シミュレーション実行中...",
                lambda: self._run_simulation_thread(num_cycles)
            )
            
        except tk.TclError:
            messagebox.showerror("エラー", "無効なパラメータ値です。数値を入力してください。")
    
    def _run_simulation_thread(self, num_cycles):
        """
        Run the simulation in a separate thread.
        
        Args:
            num_cycles: Number of cycles to simulate
        """
        try:
            # Run simulation
            results = self.app.simulator.run_all_cycles(num_cycles)
            
            # Store results
            self.app.simulation_results = results
            
            # Update plot
            self.update_plot()
            
            # Enable run button
            self.run_button.config(state=tk.NORMAL)
            
            # Show success message
            messagebox.showinfo("完了", f"{num_cycles}サイクルのシミュレーションが完了しました。")
            
        except Exception as e:
            # Enable run button
            self.run_button.config(state=tk.NORMAL)
            
            # Show error message
            messagebox.showerror("エラー", f"シミュレーション中にエラーが発生しました: {str(e)}")
    
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
        
        if plot_type == "charge_discharge":
            # Plot charge-discharge curves
            self._plot_charge_discharge_curves()
            
        elif plot_type == "capacity_retention":
            # Plot capacity retention
            self._plot_capacity_retention()
            
        elif plot_type == "resistance_growth":
            # Plot resistance growth
            self._plot_resistance_growth()
        
        # Update canvas
        self.fig.tight_layout()
        self.canvas.draw()
    
    def _plot_charge_discharge_curves(self):
        """Plot charge-discharge curves."""
        # Get results
        results = self.app.simulation_results
        
        # Create subplots
        ax1 = self.fig.add_subplot(1, 2, 1)
        ax2 = self.fig.add_subplot(1, 2, 2)
        
        # Plot charge curves
        for result in results:
            if result['cycle'] % 5 == 0 or result['cycle'] == 1:  # Plot every 5th cycle and the first cycle
                ax1.plot(
                    result['charge']['capacity'],
                    result['charge']['voltage'],
                    label=f"Cycle {result['cycle']}"
                )
        
        ax1.set_xlabel('Capacity (Ah)')
        ax1.set_ylabel('Voltage (V)')
        ax1.set_title('Charge Curves')
        ax1.grid(True)
        ax1.legend()
        
        # Plot discharge curves
        for result in results:
            if result['cycle'] % 5 == 0 or result['cycle'] == 1:  # Plot every 5th cycle and the first cycle
                ax2.plot(
                    result['discharge']['capacity'],
                    result['discharge']['voltage'],
                    label=f"Cycle {result['cycle']}"
                )
        
        ax2.set_xlabel('Discharged Capacity (Ah)')
        ax2.set_ylabel('Voltage (V)')
        ax2.set_title('Discharge Curves')
        ax2.grid(True)
        ax2.legend()
    
    def _plot_capacity_retention(self):
        """Plot capacity retention."""
        # Get results
        results = self.app.simulation_results
        
        # Calculate capacity retention
        retention = self.app.simulator.calculate_capacity_retention(results)
        
        # Create subplot
        ax = self.fig.add_subplot(1, 1, 1)
        
        # Plot capacity retention
        ax.plot(retention['cycles'], retention['retention'], 'o-')
        ax.set_xlabel('Cycle Number')
        ax.set_ylabel('Capacity Retention')
        ax.set_title('Capacity Retention vs Cycle')
        ax.grid(True)
        
        # Set y-axis limits
        ax.set_ylim(0, 1.05)
    
    def _plot_resistance_growth(self):
        """Plot resistance growth."""
        # Get results
        results = self.app.simulation_results
        
        # Extract cycle numbers and resistances
        cycles = [result['cycle'] for result in results]
        resistances = [result['resistance'] for result in results]
        
        # Create subplot
        ax = self.fig.add_subplot(1, 1, 1)
        
        # Plot resistance growth
        ax.plot(cycles, resistances, 'o-')
        ax.set_xlabel('Cycle Number')
        ax.set_ylabel('Internal Resistance (Ohm)')
        ax.set_title('Resistance Growth vs Cycle')
        ax.grid(True)
    
    def reset_parameters(self):
        """Reset parameters to default values."""
        # Battery parameters
        self.capacity_var.set(3.0)
        self.resistance_var.set(0.05)
        
        # Degradation parameters
        self.capacity_fade_A_var.set(0.1)
        self.capacity_fade_B_var.set(0.05)
        self.resistance_growth_C_var.set(0.05)
        self.resistance_growth_D_var.set(1.0)
        
        # Simulation parameters
        self.num_cycles_var.set(20)
        self.c_rate_var.set(0.5)
        self.v_max_var.set(4.1797)
        self.v_min_var.set(3.0519)
        self.end_current_ratio_var.set(0.05)
        self.dt_var.set(1.0)
    
    def reset_plots(self):
        """Reset plots."""
        # Clear figure
        self.fig.clear()
        
        # Add message
        self.fig.text(0.5, 0.5, "シミュレーション結果がここに表示されます", 
                     ha='center', va='center', fontsize=12)
        
        # Update canvas
        self.canvas.draw()
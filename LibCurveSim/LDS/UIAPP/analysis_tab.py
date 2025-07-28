"""
Analysis Tab Module

This module provides the analysis tab for the battery simulation and analysis tool.
It allows users to analyze dQ/dV curves and detect peaks.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
import os
import threading


class AnalysisTab:
    """
    Class for the analysis tab.
    """
    
    def __init__(self, parent, app):
        """
        Initialize the analysis tab.
        
        Args:
            parent: Parent widget
            app: Main application instance
        """
        self.frame = ttk.Frame(parent)
        self.app = app
        
        # Data storage
        self.dqdv_data = None
        self.peak_data = None
        self.retention_data = None
        self.selected_cycle = None
        
        # Create frames
        self.setup_frames()
        
        # Create controls
        self.setup_controls()
        
        # Create plot area
        self.setup_plot_area()
    
    def setup_frames(self):
        """Set up the frames for the tab."""
        # Main layout: controls on left, plot on right
        self.controls_frame = ttk.Frame(self.frame, padding=(10, 10))
        self.controls_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        self.plot_frame = ttk.Frame(self.frame, padding=(10, 10))
        self.plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Control sections
        self.data_frame = ttk.LabelFrame(self.controls_frame, text="データ", padding=(10, 5))
        self.data_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.analysis_frame = ttk.LabelFrame(self.controls_frame, text="解析", padding=(10, 5))
        self.analysis_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.peak_frame = ttk.LabelFrame(self.controls_frame, text="ピーク検出", padding=(10, 5))
        self.peak_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.display_frame = ttk.LabelFrame(self.controls_frame, text="表示", padding=(10, 5))
        self.display_frame.pack(fill=tk.X, pady=(0, 10))
    
    def setup_controls(self):
        """Set up the control widgets."""
        # Data controls
        self.setup_data_controls()
        
        # Analysis controls
        self.setup_analysis_controls()
        
        # Peak detection controls
        self.setup_peak_controls()
        
        # Display controls
        self.setup_display_controls()
    
    def setup_data_controls(self):
        """Set up the data control widgets."""
        # Load data button
        self.load_button = ttk.Button(
            self.data_frame,
            text="データを開く",
            command=self.load_data
        )
        self.load_button.grid(row=0, column=0, sticky=tk.W, pady=2)
        
        # Cycle selection
        ttk.Label(self.data_frame, text="サイクル:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.cycle_var = tk.StringVar()
        self.cycle_combo = ttk.Combobox(
            self.data_frame,
            textvariable=self.cycle_var,
            state="readonly",
            width=10
        )
        self.cycle_combo.grid(row=1, column=1, sticky=tk.W, pady=2)
        self.cycle_combo.bind("<<ComboboxSelected>>", self.on_cycle_selected)
    
    def setup_analysis_controls(self):
        """Set up the analysis control widgets."""
        # Smoothing factor
        ttk.Label(self.analysis_frame, text="スムージング係数:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.smoothing_var = tk.DoubleVar(value=0.01)
        ttk.Entry(self.analysis_frame, textvariable=self.smoothing_var, width=10).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # Recalculate button
        self.recalculate_button = ttk.Button(
            self.analysis_frame,
            text="再計算",
            command=self.recalculate_dqdv
        )
        self.recalculate_button.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)
    
    def setup_peak_controls(self):
        """Set up the peak detection control widgets."""
        # Prominence
        ttk.Label(self.peak_frame, text="顕著さ (prominence):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.prominence_var = tk.DoubleVar(value=0.01)
        ttk.Entry(self.peak_frame, textvariable=self.prominence_var, width=10).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # Width
        ttk.Label(self.peak_frame, text="幅 (width):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.width_var = tk.DoubleVar(value=None)
        width_entry = ttk.Entry(self.peak_frame, textvariable=self.width_var, width=10)
        width_entry.grid(row=1, column=1, sticky=tk.W, pady=2)
        width_entry.delete(0, tk.END)  # Clear the "None" text
        
        # Height
        ttk.Label(self.peak_frame, text="高さ (height):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.height_var = tk.DoubleVar(value=None)
        height_entry = ttk.Entry(self.peak_frame, textvariable=self.height_var, width=10)
        height_entry.grid(row=2, column=1, sticky=tk.W, pady=2)
        height_entry.delete(0, tk.END)  # Clear the "None" text
        
        # Distance
        ttk.Label(self.peak_frame, text="距離 (distance):").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.distance_var = tk.IntVar(value=None)
        distance_entry = ttk.Entry(self.peak_frame, textvariable=self.distance_var, width=10)
        distance_entry.grid(row=3, column=1, sticky=tk.W, pady=2)
        distance_entry.delete(0, tk.END)  # Clear the "None" text
        
        # Voltage range
        ttk.Label(self.peak_frame, text="電圧範囲 (V):").grid(row=4, column=0, sticky=tk.W, pady=2)
        range_frame = ttk.Frame(self.peak_frame)
        range_frame.grid(row=4, column=1, sticky=tk.W, pady=2)
        
        self.v_min_var = tk.DoubleVar(value=3.5)
        ttk.Entry(range_frame, textvariable=self.v_min_var, width=5).pack(side=tk.LEFT)
        
        ttk.Label(range_frame, text="-").pack(side=tk.LEFT, padx=2)
        
        self.v_max_var = tk.DoubleVar(value=4.1)
        ttk.Entry(range_frame, textvariable=self.v_max_var, width=5).pack(side=tk.LEFT)
        
        # Detect peaks button
        self.detect_button = ttk.Button(
            self.peak_frame,
            text="ピーク検出",
            command=self.detect_peaks
        )
        self.detect_button.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=2)
    
    def setup_display_controls(self):
        """Set up the display control widgets."""
        # Plot type
        ttk.Label(self.display_frame, text="表示:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.plot_type_var = tk.StringVar(value="dqdv")
        plot_type_combo = ttk.Combobox(
            self.display_frame,
            textvariable=self.plot_type_var,
            values=["dqdv", "dqdv_peaks", "peak_evolution", "retention"],
            state="readonly",
            width=15
        )
        plot_type_combo.grid(row=0, column=1, sticky=tk.W, pady=2)
        plot_type_combo.bind("<<ComboboxSelected>>", self.update_plot)
        
        # Show all cycles
        self.show_all_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.display_frame,
            text="すべてのサイクルを表示",
            variable=self.show_all_var,
            command=self.update_plot
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)
    
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
        self.fig.text(0.5, 0.5, "dQ/dV曲線がここに表示されます", 
                     ha='center', va='center', fontsize=12)
        self.canvas.draw()
    
    def load_data(self):
        """Load data from a file."""
        file_path = filedialog.askopenfilename(
            title="データファイルを開く",
            filetypes=[("CSVファイル", "*.csv"), ("すべてのファイル", "*.*")]
        )
        
        if file_path:
            # Load data
            self.app.run_in_background(
                f"ファイルを読み込み中: {os.path.basename(file_path)}",
                lambda: self._load_data_thread(file_path)
            )
    
    def _load_data_thread(self, file_path):
        """
        Load data in a separate thread.
        
        Args:
            file_path: Path to the data file
        """
        try:
            # Load data using data processor
            data = self.app.processor.load_csv_file(file_path)
            
            if data is None:
                messagebox.showerror("エラー", f"ファイルを読み込めませんでした: {file_path}")
                return
            
            # Process data based on type
            if data['type'] == 'charge_discharge':
                # Calculate dQ/dV curves
                self.dqdv_data = self.app.processor.process_charge_discharge_data(data['data'])
                
                # Detect peaks
                self.peak_data = self.app.processor.process_dqdv_peaks(
                    self.dqdv_data,
                    prominence=self.prominence_var.get(),
                    v_range=[self.v_min_var.get(), self.v_max_var.get()]
                )
                
                # Update cycle selection
                self._update_cycle_selection()
                
                # Update plot
                self.update_plot()
                
            elif data['type'] == 'dqdv':
                # Store dQ/dV data
                self.dqdv_data = data['data']
                
                # Detect peaks
                self.peak_data = self.app.processor.process_dqdv_peaks(
                    self.dqdv_data,
                    prominence=self.prominence_var.get(),
                    v_range=[self.v_min_var.get(), self.v_max_var.get()]
                )
                
                # Update cycle selection
                self._update_cycle_selection()
                
                # Update plot
                self.update_plot()
                
            elif data['type'] == 'retention':
                # Store retention data
                self.retention_data = data['data']
                
                # Update plot
                self.plot_type_var.set("retention")
                self.update_plot()
                
            else:
                messagebox.showinfo("情報", f"未知のデータ形式です: {data['type']}")
            
        except Exception as e:
            messagebox.showerror("エラー", f"データ読み込み中にエラーが発生しました: {str(e)}")
    
    def _update_cycle_selection(self):
        """Update the cycle selection combobox."""
        if self.dqdv_data is None:
            return
        
        # Get cycle numbers
        cycles = sorted(self.dqdv_data.keys())
        
        # Update combobox
        self.cycle_combo['values'] = cycles
        
        # Select first cycle
        if cycles:
            self.cycle_var.set(cycles[0])
            self.selected_cycle = cycles[0]
    
    def on_cycle_selected(self, event=None):
        """
        Handle cycle selection.
        
        Args:
            event: Event that triggered the selection (optional)
        """
        if self.cycle_var.get():
            self.selected_cycle = int(self.cycle_var.get())
            self.update_plot()
    
    def recalculate_dqdv(self):
        """Recalculate dQ/dV curves with new smoothing factor."""
        if self.app.simulation_results is None and self.dqdv_data is None:
            messagebox.showinfo("情報", "再計算するデータがありません。")
            return
        
        try:
            # Get smoothing factor
            smoothing_factor = self.smoothing_var.get()
            
            # Check if we have simulation results
            if self.app.simulation_results is not None:
                # Extract charge data
                charge_data = {}
                for result in self.app.simulation_results:
                    cycle = result['cycle']
                    charge_data[cycle] = {
                        'capacity': result['charge']['capacity'],
                        'voltage': result['charge']['voltage']
                    }
                
                # Recalculate dQ/dV curves
                self.dqdv_data = self.app.processor.process_charge_discharge_data(
                    charge_data, smoothing_factor=smoothing_factor
                )
                
                # Update cycle selection
                self._update_cycle_selection()
                
                # Detect peaks
                self.detect_peaks()
                
            # Update plot
            self.update_plot()
            
        except tk.TclError:
            messagebox.showerror("エラー", "無効なスムージング係数です。数値を入力してください。")
        except Exception as e:
            messagebox.showerror("エラー", f"再計算中にエラーが発生しました: {str(e)}")
    
    def detect_peaks(self):
        """Detect peaks in dQ/dV curves."""
        if self.dqdv_data is None:
            messagebox.showinfo("情報", "ピーク検出するデータがありません。")
            return
        
        try:
            # Get peak detection parameters
            prominence = self.prominence_var.get()
            
            # Get optional parameters
            width = None
            height = None
            distance = None
            v_range = [self.v_min_var.get(), self.v_max_var.get()]
            
            try:
                width = self.width_var.get()
            except tk.TclError:
                pass
            
            try:
                height = self.height_var.get()
            except tk.TclError:
                pass
            
            try:
                distance = self.distance_var.get()
            except tk.TclError:
                pass
            
            # Detect peaks
            self.peak_data = self.app.processor.process_dqdv_peaks(
                self.dqdv_data,
                prominence=prominence,
                width=width,
                height=height,
                distance=distance,
                v_range=v_range
            )
            
            # Update plot
            self.plot_type_var.set("dqdv_peaks")
            self.update_plot()
            
        except tk.TclError:
            messagebox.showerror("エラー", "無効なパラメータ値です。数値を入力してください。")
        except Exception as e:
            messagebox.showerror("エラー", f"ピーク検出中にエラーが発生しました: {str(e)}")
    
    def update_plot(self, event=None):
        """
        Update the plot with the current data.
        
        Args:
            event: Event that triggered the update (optional)
        """
        # Get plot type
        plot_type = self.plot_type_var.get()
        
        # Clear figure
        self.fig.clear()
        
        if plot_type == "dqdv":
            # Plot dQ/dV curves
            self._plot_dqdv_curves()
            
        elif plot_type == "dqdv_peaks":
            # Plot dQ/dV curves with peaks
            self._plot_dqdv_peaks()
            
        elif plot_type == "peak_evolution":
            # Plot peak evolution
            self._plot_peak_evolution()
            
        elif plot_type == "retention":
            # Plot capacity retention
            self._plot_retention()
        
        # Update canvas
        self.fig.tight_layout()
        self.canvas.draw()
    
    def _plot_dqdv_curves(self):
        """Plot dQ/dV curves."""
        if self.dqdv_data is None:
            self.fig.text(0.5, 0.5, "dQ/dV曲線データがありません", 
                         ha='center', va='center', fontsize=12)
            return
        
        # Create subplot
        ax = self.fig.add_subplot(1, 1, 1)
        
        if self.show_all_var.get():
            # Plot all cycles
            for cycle in sorted(self.dqdv_data.keys()):
                ax.plot(
                    self.dqdv_data[cycle]['voltage'],
                    self.dqdv_data[cycle]['dqdv'],
                    label=f"Cycle {cycle}"
                )
        else:
            # Plot selected cycle
            if self.selected_cycle is not None and self.selected_cycle in self.dqdv_data:
                ax.plot(
                    self.dqdv_data[self.selected_cycle]['voltage'],
                    self.dqdv_data[self.selected_cycle]['dqdv'],
                    label=f"Cycle {self.selected_cycle}"
                )
        
        ax.set_xlabel('Voltage (V)')
        ax.set_ylabel('dQ/dV')
        ax.set_title('dQ/dV Curves')
        ax.grid(True)
        ax.legend()
    
    def _plot_dqdv_peaks(self):
        """Plot dQ/dV curves with peaks."""
        if self.dqdv_data is None or self.peak_data is None:
            self.fig.text(0.5, 0.5, "dQ/dV曲線またはピークデータがありません", 
                         ha='center', va='center', fontsize=12)
            return
        
        # Create subplot
        ax = self.fig.add_subplot(1, 1, 1)
        
        if self.show_all_var.get():
            # Plot all cycles
            for cycle in sorted(self.dqdv_data.keys()):
                # Plot dQ/dV curve
                ax.plot(
                    self.dqdv_data[cycle]['voltage'],
                    self.dqdv_data[cycle]['dqdv'],
                    label=f"Cycle {cycle}"
                )
                
                # Plot peaks
                if cycle in self.peak_data:
                    ax.plot(
                        self.peak_data[cycle]['peak_voltages'],
                        self.peak_data[cycle]['peak_dqdvs'],
                        'o',
                        label=f"Peaks {cycle}"
                    )
        else:
            # Plot selected cycle
            if self.selected_cycle is not None and self.selected_cycle in self.dqdv_data:
                # Plot dQ/dV curve
                ax.plot(
                    self.dqdv_data[self.selected_cycle]['voltage'],
                    self.dqdv_data[self.selected_cycle]['dqdv'],
                    label=f"Cycle {self.selected_cycle}"
                )
                
                # Plot peaks
                if self.selected_cycle in self.peak_data:
                    ax.plot(
                        self.peak_data[self.selected_cycle]['peak_voltages'],
                        self.peak_data[self.selected_cycle]['peak_dqdvs'],
                        'ro',
                        label=f"Peaks {self.selected_cycle}"
                    )
                    
                    # Add peak labels
                    for i, (v, dq) in enumerate(zip(
                        self.peak_data[self.selected_cycle]['peak_voltages'],
                        self.peak_data[self.selected_cycle]['peak_dqdvs']
                    )):
                        ax.text(v, dq, f"{i+1}", fontsize=12)
        
        ax.set_xlabel('Voltage (V)')
        ax.set_ylabel('dQ/dV')
        ax.set_title('dQ/dV Curves with Peaks')
        ax.grid(True)
        ax.legend()
    
    def _plot_peak_evolution(self):
        """Plot peak evolution."""
        if self.peak_data is None:
            self.fig.text(0.5, 0.5, "ピークデータがありません", 
                         ha='center', va='center', fontsize=12)
            return
        
        # Create subplots
        ax1 = self.fig.add_subplot(2, 1, 1)
        ax2 = self.fig.add_subplot(2, 1, 2)
        
        # Get cycle numbers
        cycles = sorted(self.peak_data.keys())
        
        # Collect peak positions and heights for each peak
        peak_positions = {}
        peak_heights = {}
        
        for cycle in cycles:
            for i, (voltage, dqdv) in enumerate(zip(
                self.peak_data[cycle]['peak_voltages'],
                self.peak_data[cycle]['peak_dqdvs']
            )):
                # Initialize if this is a new peak
                if i not in peak_positions:
                    peak_positions[i] = {'cycles': [], 'voltages': []}
                    peak_heights[i] = {'cycles': [], 'heights': []}
                
                # Add data for this cycle
                peak_positions[i]['cycles'].append(cycle)
                peak_positions[i]['voltages'].append(voltage)
                peak_heights[i]['cycles'].append(cycle)
                peak_heights[i]['heights'].append(dqdv)
        
        # Plot peak positions
        for i, data in peak_positions.items():
            ax1.plot(
                data['cycles'],
                data['voltages'],
                'o-',
                label=f"Peak {i+1}"
            )
        
        ax1.set_xlabel('Cycle Number')
        ax1.set_ylabel('Peak Voltage (V)')
        ax1.set_title('Evolution of Peak Positions')
        ax1.grid(True)
        ax1.legend()
        
        # Plot peak heights
        for i, data in peak_heights.items():
            ax2.plot(
                data['cycles'],
                data['heights'],
                'o-',
                label=f"Peak {i+1}"
            )
        
        ax2.set_xlabel('Cycle Number')
        ax2.set_ylabel('Peak Height (dQ/dV)')
        ax2.set_title('Evolution of Peak Heights')
        ax2.grid(True)
        ax2.legend()
    
    def _plot_retention(self):
        """Plot capacity retention."""
        if self.retention_data is None:
            self.fig.text(0.5, 0.5, "容量維持率データがありません", 
                         ha='center', va='center', fontsize=12)
            return
        
        # Create subplot
        ax = self.fig.add_subplot(1, 1, 1)
        
        # Plot capacity retention
        ax.plot(
            self.retention_data['cycles'],
            self.retention_data['retention'],
            'o-'
        )
        
        ax.set_xlabel('Cycle Number')
        ax.set_ylabel('Capacity Retention')
        ax.set_title('Capacity Retention vs Cycle')
        ax.grid(True)
        
        # Set y-axis limits
        ax.set_ylim(0, 1.05)
    
    def update_data(self, dqdv_data, peak_data):
        """
        Update the data.
        
        Args:
            dqdv_data: dQ/dV data
            peak_data: Peak data
        """
        self.dqdv_data = dqdv_data
        self.peak_data = peak_data
        
        # Update cycle selection
        self._update_cycle_selection()
        
        # Update plot
        self.plot_type_var.set("dqdv_peaks")
        self.update_plot()
    
    def update_retention_data(self, retention_data):
        """
        Update the retention data.
        
        Args:
            retention_data: Retention data
        """
        self.retention_data = retention_data
        
        # Update plot
        self.plot_type_var.set("retention")
        self.update_plot()
    
    def reset_plots(self):
        """Reset plots."""
        # Clear figure
        self.fig.clear()
        
        # Add message
        self.fig.text(0.5, 0.5, "dQ/dV曲線がここに表示されます", 
                     ha='center', va='center', fontsize=12)
        
        # Update canvas
        self.canvas.draw()
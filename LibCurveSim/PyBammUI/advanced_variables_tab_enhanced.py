#!/usr/bin/env python3
"""
Enhanced Advanced Variables Tab for PyBamm UI - Parameter Modification System
Allows users to modify parameters with visual indicators, save custom presets, and handle errors.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
import threading
import time
import json
import os
from copy import deepcopy

# Import font configuration for Japanese text support
import font_config

# PyBamm integration
try:
    import pybamm
    PYBAMM_AVAILABLE = True
except ImportError:
    PYBAMM_AVAILABLE = False


class AdvancedVariablesTab:
    """Enhanced Advanced Variables Tab with parameter modification capabilities."""
    
    def __init__(self, parent, app):
        """Initialize the Enhanced Advanced Variables tab."""
        self.parent = parent
        self.app = app
        self.frame = ttk.Frame(parent)
        
        # Initialize variables
        self.setup_variables()
        
        # Initialize parameter management
        self.available_presets = self.get_available_presets()
        self.custom_presets = self.load_custom_presets()
        self.current_parameter_values = None
        self.original_parameter_values = None
        self.modified_parameters = set()
        self.simulation_results = None
        
        # Set up the UI
        self.setup_ui()
        
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
        
        # Parameter modification settings
        self.show_modified_only_var = tk.BooleanVar(value=False)
        
    def get_available_presets(self):
        """Get list of available parameter presets."""
        if PYBAMM_AVAILABLE:
            # Common parameter sets available in PyBamm
            common_presets = [
                "Chen2020", "Marquis2019", "Ecker2015", "Mohtat2020",
                "Prada2013", "Ramadass2004", "Ai2020", "ORegan2022"
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
    
    def load_custom_presets(self):
        """Load custom presets from file."""
        presets_file = os.path.join(os.path.dirname(__file__), "custom_presets.json")
        try:
            if os.path.exists(presets_file):
                with open(presets_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading custom presets: {e}")
            return {}
    
    def save_custom_presets(self):
        """Save custom presets to file."""
        presets_file = os.path.join(os.path.dirname(__file__), "custom_presets.json")
        try:
            with open(presets_file, 'w', encoding='utf-8') as f:
                json.dump(self.custom_presets, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("エラー", f"カスタムプリセットの保存に失敗しました: {str(e)}")
    
    def setup_ui(self):
        """Set up the enhanced user interface."""
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
        self.setup_preset_management(left_frame)
        self.setup_parameter_modification(left_frame)
        self.setup_simulation_controls(left_frame)
        
        # Set up plot area
        self.setup_plot_area()
    
    def setup_preset_management(self, parent):
        """Set up preset management controls."""
        preset_frame = ttk.LabelFrame(parent, text="プリセット管理", padding=10)
        preset_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Preset selection
        ttk.Label(preset_frame, text="プリセット:").grid(row=0, column=0, sticky=tk.W, pady=2)
        
        # Combine built-in and custom presets
        all_presets = self.available_presets + list(self.custom_presets.keys())
        preset_combo = ttk.Combobox(
            preset_frame, textvariable=self.preset_var, width=20,
            values=all_presets, state="readonly"
        )
        preset_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        preset_combo.bind('<<ComboboxSelected>>', self.on_preset_changed)
        
        # Preset management buttons
        button_frame = ttk.Frame(preset_frame)
        button_frame.grid(row=1, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="読み込み", command=self.load_parameter_preset).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="保存", command=self.save_current_preset).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="削除", command=self.delete_custom_preset).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="リセット", command=self.reset_parameters).pack(side=tk.LEFT, padx=2)
        
        # Show modification status
        self.modification_status = ttk.Label(preset_frame, text="変更なし", foreground="green")
        self.modification_status.grid(row=2, column=0, columnspan=3, pady=5)
    
    def setup_parameter_modification(self, parent):
        """Set up parameter modification interface."""
        param_frame = ttk.LabelFrame(parent, text="パラメータ編集", padding=10)
        param_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Filter controls
        filter_frame = ttk.Frame(param_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Checkbutton(
            filter_frame, text="変更されたパラメータのみ表示",
            variable=self.show_modified_only_var,
            command=self.refresh_parameter_display
        ).pack(side=tk.LEFT)
        
        # Search box
        ttk.Label(filter_frame, text="検索:").pack(side=tk.LEFT, padx=(20, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_changed)
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        # Create enhanced treeview for parameter modification
        columns = ("Parameter", "Value", "Unit", "Original")
        self.param_tree = ttk.Treeview(param_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        self.param_tree.heading("Parameter", text="パラメータ名")
        self.param_tree.heading("Value", text="現在値")
        self.param_tree.heading("Unit", text="単位")
        self.param_tree.heading("Original", text="元の値")
        
        self.param_tree.column("Parameter", width=250)
        self.param_tree.column("Value", width=100)
        self.param_tree.column("Unit", width=60)
        self.param_tree.column("Original", width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(param_frame, orient=tk.VERTICAL, command=self.param_tree.yview)
        self.param_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.param_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click for parameter editing
        self.param_tree.bind("<Double-1>", self.on_parameter_double_click)
        
        # Configure tags for color coding
        self.param_tree.tag_configure("modified", background="#FFE4B5")  # Light orange for modified
        self.param_tree.tag_configure("error", background="#FFB6C1")     # Light red for errors
        self.param_tree.tag_configure("normal", background="white")      # Normal background
    
    def setup_simulation_controls(self, parent):
        """Set up enhanced simulation control panel."""
        sim_frame = ttk.LabelFrame(parent, text="シミュレーション実行", padding=10)
        sim_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Time setting
        ttk.Label(sim_frame, text="シミュレーション時間 (時間):").grid(row=0, column=0, sticky=tk.W, pady=2)
        time_spinbox = ttk.Spinbox(
            sim_frame, textvariable=self.time_hours_var, 
            from_=0.1, to=10.0, increment=0.1, width=10
        )
        time_spinbox.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Model selection
        ttk.Label(sim_frame, text="モデル:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.model_var = tk.StringVar(value="DFN")
        model_combo = ttk.Combobox(
            sim_frame, textvariable=self.model_var, width=10,
            values=["DFN", "SPM", "SPMe"], state="readonly"
        )
        model_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Current/Charge/Discharge settings
        current_frame = ttk.LabelFrame(sim_frame, text="電流設定", padding=5)
        current_frame.grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        self.current_mode_var = tk.StringVar(value="discharge")
        ttk.Radiobutton(current_frame, text="放電", variable=self.current_mode_var, value="discharge").grid(row=0, column=0, sticky=tk.W)
        ttk.Radiobutton(current_frame, text="充電", variable=self.current_mode_var, value="charge").grid(row=0, column=1, sticky=tk.W)
        ttk.Radiobutton(current_frame, text="カスタム", variable=self.current_mode_var, value="custom").grid(row=0, column=2, sticky=tk.W)
        
        ttk.Label(current_frame, text="電流値 (A):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.current_value_var = tk.DoubleVar(value=1.0)
        current_spinbox = ttk.Spinbox(
            current_frame, textvariable=self.current_value_var,
            from_=0.1, to=10.0, increment=0.1, width=10
        )
        current_spinbox.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Simulation buttons
        button_frame = ttk.Frame(sim_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        self.run_button = ttk.Button(
            button_frame, text="シミュレーション実行",
            command=self.run_simulation
        )
        self.run_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, text="プロットクリア",
            command=self.clear_plot
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, text="パラメータ検証",
            command=self.validate_parameters
        ).pack(side=tk.LEFT, padx=5)
    
    def setup_plot_area(self):
        """Set up the enhanced plot area."""
        # Create figure and canvas
        self.fig = plt.figure(figsize=(12, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        self.toolbar.update()
        
        # Initialize with empty plot
        self.fig.text(0.5, 0.5, "シミュレーション結果がここに表示されます", 
                     ha='center', va='center', fontsize=14)
        self.canvas.draw()
    
    # Event Handlers
    def on_preset_changed(self, event=None):
        """Handle preset selection change."""
        self.load_parameter_preset()
    
    def on_search_changed(self, *args):
        """Handle search text change."""
        self.refresh_parameter_display()
    
    def on_parameter_double_click(self, event):
        """Handle double-click on parameter for editing."""
        item = self.param_tree.selection()[0] if self.param_tree.selection() else None
        if not item:
            return
        
        # Get parameter information
        values = self.param_tree.item(item, 'values')
        param_name = values[0]
        current_value = values[1]
        unit = values[2]
        original_value = values[3]
        
        # Find full parameter key
        full_param_key = None
        for key in self.current_parameter_values.keys() if hasattr(self.current_parameter_values, 'keys') else self.current_parameter_values.params.keys():
            if self.extract_param_name(key) == param_name:
                full_param_key = key
                break
        
        if not full_param_key:
            messagebox.showerror("エラー", "パラメータが見つかりません。")
            return
        
        # Show parameter editing dialog
        self.edit_parameter(full_param_key, param_name, current_value, unit)
    
    def edit_parameter(self, param_key, param_name, current_value, unit):
        """Show parameter editing dialog."""
        dialog = ParameterEditDialog(self.app.root, param_name, current_value, unit)
        if dialog.result is not None:
            try:
                new_value = self.validate_parameter_value(param_key, dialog.result)
                self.modify_parameter(param_key, new_value)
                self.refresh_parameter_display()
                self.update_modification_status()
            except ValueError as e:
                messagebox.showerror("パラメータエラー", str(e))
    
    def modify_parameter(self, param_key, new_value):
        """Modify a parameter value."""
        if hasattr(self.current_parameter_values, '__setitem__'):
            self.current_parameter_values[param_key] = new_value
        else:
            self.current_parameter_values.params[param_key] = new_value
        
        self.modified_parameters.add(param_key)
    
    def validate_parameter_value(self, param_key, value):
        """Validate parameter value and return converted value."""
        try:
            # Convert to appropriate type
            if isinstance(value, str):
                # Try to convert string to number
                if '.' in value or 'e' in value.lower():
                    converted_value = float(value)
                else:
                    converted_value = int(value)
            else:
                converted_value = float(value)
            
            # Parameter-specific validation
            if "capacity" in param_key.lower():
                if converted_value <= 0:
                    raise ValueError("容量は正の値である必要があります。")
                if converted_value > 1000:
                    raise ValueError("容量が異常に大きすぎます（1000Ah以下にしてください）。")
            
            elif "current" in param_key.lower():
                if abs(converted_value) > 100:
                    raise ValueError("電流値が異常に大きすぎます（100A以下にしてください）。")
            
            elif "voltage" in param_key.lower():
                if converted_value < 0:
                    raise ValueError("電圧は負の値にできません。")
                if converted_value > 10:
                    raise ValueError("電圧が異常に高すぎます（10V以下にしてください）。")
            
            elif "temperature" in param_key.lower():
                if converted_value < 200:  # Kelvin
                    raise ValueError("温度が低すぎます（200K以上にしてください）。")
                if converted_value > 400:  # Kelvin
                    raise ValueError("温度が高すぎます（400K以下にしてください）。")
            
            elif "thickness" in param_key.lower():
                if converted_value <= 0:
                    raise ValueError("厚さは正の値である必要があります。")
                if converted_value > 1:  # 1m
                    raise ValueError("厚さが異常に大きすぎます。")
            
            elif "porosity" in param_key.lower() or "fraction" in param_key.lower():
                if converted_value < 0 or converted_value > 1:
                    raise ValueError("多孔度や体積分率は0から1の間の値である必要があります。")
            
            return converted_value
            
        except (ValueError, TypeError) as e:
            if "could not convert" in str(e):
                raise ValueError("数値を入力してください。")
            raise ValueError(f"パラメータ値が無効です: {str(e)}")
    
    def validate_parameters(self):
        """Validate all current parameters."""
        errors = []
        warnings = []
        
        try:
            if self.current_parameter_values is None:
                messagebox.showerror("エラー", "パラメータが読み込まれていません。")
                return
            
            # Get parameter items
            if hasattr(self.current_parameter_values, 'items'):
                param_items = self.current_parameter_values.items()
            else:
                param_items = self.current_parameter_values.params.items()
            
            for param_key, value in param_items:
                try:
                    self.validate_parameter_value(param_key, value)
                except ValueError as e:
                    errors.append(f"{self.extract_param_name(param_key)}: {str(e)}")
            
            # Check for parameter consistency
            self.check_parameter_consistency(param_items, warnings)
            
            # Show results
            if errors:
                error_msg = "以下のパラメータにエラーがあります:\n\n" + "\n".join(errors)
                messagebox.showerror("パラメータ検証エラー", error_msg)
            elif warnings:
                warning_msg = "以下の警告があります:\n\n" + "\n".join(warnings)
                messagebox.showwarning("パラメータ検証警告", warning_msg)
            else:
                messagebox.showinfo("パラメータ検証", "すべてのパラメータが有効です。")
                
        except Exception as e:
            messagebox.showerror("検証エラー", f"パラメータ検証中にエラーが発生しました: {str(e)}")
    
    def check_parameter_consistency(self, param_items, warnings):
        """Check parameter consistency and add warnings."""
        param_dict = dict(param_items)
        
        # Check electrode thickness consistency
        pos_thickness = param_dict.get("Positive electrode thickness [m]")
        neg_thickness = param_dict.get("Negative electrode thickness [m]")
        sep_thickness = param_dict.get("Separator thickness [m]")
        
        if pos_thickness and neg_thickness and sep_thickness:
            total_thickness = pos_thickness + neg_thickness + sep_thickness
            if total_thickness > 0.001:  # 1mm
                warnings.append("電極の総厚さが1mmを超えています。")
        
        # Check capacity vs current consistency
        capacity = param_dict.get("Nominal cell capacity [A.h]")
        current = param_dict.get("Current function [A]")
        
        if capacity and current:
            c_rate = abs(current) / capacity
            if c_rate > 5:
                warnings.append(f"C-rateが高すぎます ({c_rate:.1f}C)。")
    
    def extract_param_name(self, param_key):
        """Extract parameter name without unit."""
        if "[" in param_key and "]" in param_key:
            return param_key[:param_key.find("[")].strip()
        return param_key
    
    # Parameter Management Methods
    def load_parameter_preset(self):
        """Load the selected parameter preset and display values."""
        preset_name = self.preset_var.get()
        
        try:
            if preset_name in self.custom_presets:
                # Load custom preset
                self.current_parameter_values = self.get_mock_parameter_values_from_dict(self.custom_presets[preset_name])
                self.original_parameter_values = deepcopy(self.current_parameter_values)
                self.modified_parameters.clear()
                self.refresh_parameter_display()
                messagebox.showinfo("成功", f"カスタムプリセット '{preset_name}' を読み込みました。")
                
            elif PYBAMM_AVAILABLE:
                # Load PyBamm preset
                self.current_parameter_values = pybamm.ParameterValues(preset_name)
                self.original_parameter_values = deepcopy(self.current_parameter_values)
                self.modified_parameters.clear()
                self.refresh_parameter_display()
                messagebox.showinfo("成功", f"パラメータプリセット '{preset_name}' を読み込みました。")
                
            else:
                # Mock parameter values for development
                self.current_parameter_values = self.get_mock_parameter_values(preset_name)
                self.original_parameter_values = deepcopy(self.current_parameter_values)
                self.modified_parameters.clear()
                self.refresh_parameter_display()
                messagebox.showinfo("成功", f"モックパラメータプリセット '{preset_name}' を読み込みました。")
                
        except Exception as e:
            messagebox.showerror("エラー", f"パラメータプリセットの読み込みに失敗しました: {str(e)}")
    
    def save_current_preset(self):
        """Save current parameters as a custom preset."""
        if self.current_parameter_values is None:
            messagebox.showerror("エラー", "保存するパラメータがありません。")
            return
        
        # Get preset name from user
        preset_name = simpledialog.askstring(
            "プリセット保存",
            "プリセット名を入力してください:",
            initialvalue=f"Custom_{len(self.custom_presets) + 1}"
        )
        
        if not preset_name:
            return
        
        if preset_name in self.available_presets:
            messagebox.showerror("エラー", "組み込みプリセットと同じ名前は使用できません。")
            return
        
        try:
            # Convert current parameters to dictionary
            if hasattr(self.current_parameter_values, 'items'):
                param_dict = dict(self.current_parameter_values.items())
            else:
                param_dict = dict(self.current_parameter_values.params.items())
            
            # Save to custom presets
            self.custom_presets[preset_name] = param_dict
            self.save_custom_presets()
            
            # Update preset combo box
            all_presets = self.available_presets + list(self.custom_presets.keys())
            preset_combo = None
            for child in self.frame.winfo_children():
                if isinstance(child, ttk.PanedWindow):
                    for subchild in child.winfo_children():
                        if isinstance(subchild, ttk.Frame):
                            for widget in subchild.winfo_children():
                                if isinstance(widget, ttk.LabelFrame) and "プリセット管理" in widget.cget("text"):
                                    for combo_widget in widget.winfo_children():
                                        if isinstance(combo_widget, ttk.Combobox):
                                            preset_combo = combo_widget
                                            break
            
            if preset_combo:
                preset_combo.configure(values=all_presets)
            
            messagebox.showinfo("成功", f"プリセット '{preset_name}' を保存しました。")
            
        except Exception as e:
            messagebox.showerror("エラー", f"プリセットの保存に失敗しました: {str(e)}")
    
    def delete_custom_preset(self):
        """Delete the selected custom preset."""
        preset_name = self.preset_var.get()
        
        if preset_name not in self.custom_presets:
            messagebox.showerror("エラー", "選択されたプリセットはカスタムプリセットではありません。")
            return
        
        if messagebox.askyesno("確認", f"プリセット '{preset_name}' を削除しますか？"):
            try:
                del self.custom_presets[preset_name]
                self.save_custom_presets()
                
                # Update preset combo box
                all_presets = self.available_presets + list(self.custom_presets.keys())
                preset_combo = None
                for child in self.frame.winfo_children():
                    if isinstance(child, ttk.PanedWindow):
                        for subchild in child.winfo_children():
                            if isinstance(subchild, ttk.Frame):
                                for widget in subchild.winfo_children():
                                    if isinstance(widget, ttk.LabelFrame) and "プリセット管理" in widget.cget("text"):
                                        for combo_widget in widget.winfo_children():
                                            if isinstance(combo_widget, ttk.Combobox):
                                                preset_combo = combo_widget
                                                break
                
                if preset_combo:
                    preset_combo.configure(values=all_presets)
                    if all_presets:
                        self.preset_var.set(all_presets[0])
                        self.load_parameter_preset()
                
                messagebox.showinfo("成功", f"プリセット '{preset_name}' を削除しました。")
                
            except Exception as e:
                messagebox.showerror("エラー", f"プリセットの削除に失敗しました: {str(e)}")
    
    def reset_parameters(self):
        """Reset parameters to original values."""
        if self.original_parameter_values is None:
            messagebox.showerror("エラー", "リセットする元のパラメータがありません。")
            return
        
        if messagebox.askyesno("確認", "パラメータを元の値にリセットしますか？"):
            try:
                self.current_parameter_values = deepcopy(self.original_parameter_values)
                self.modified_parameters.clear()
                self.refresh_parameter_display()
                self.update_modification_status()
                messagebox.showinfo("成功", "パラメータをリセットしました。")
                
            except Exception as e:
                messagebox.showerror("エラー", f"パラメータのリセットに失敗しました: {str(e)}")
    
    def update_modification_status(self):
        """Update the modification status display."""
        if self.modified_parameters:
            status_text = f"{len(self.modified_parameters)}個のパラメータが変更されています"
            self.modification_status.configure(text=status_text, foreground="orange")
        else:
            self.modification_status.configure(text="変更なし", foreground="green")
    
    def refresh_parameter_display(self):
        """Refresh the parameter display with current values."""
        # Clear existing items
        for item in self.param_tree.get_children():
            self.param_tree.delete(item)
        
        if self.current_parameter_values is None:
            return
        
        # Get search term
        search_term = self.search_var.get().lower() if hasattr(self, 'search_var') else ""
        show_modified_only = self.show_modified_only_var.get()
        
        try:
            # Get parameter items
            if hasattr(self.current_parameter_values, 'items'):
                param_items = list(self.current_parameter_values.items())
            else:
                param_items = list(self.current_parameter_values.params.items())
            
            # Get original values for comparison
            original_items = {}
            if self.original_parameter_values:
                if hasattr(self.original_parameter_values, 'items'):
                    original_items = dict(self.original_parameter_values.items())
                else:
                    original_items = dict(self.original_parameter_values.params.items())
            
            for param_key, value in param_items:
                # Extract parameter name and unit
                if "[" in param_key and "]" in param_key:
                    unit = param_key[param_key.find("[")+1:param_key.find("]")]
                    param_name = param_key[:param_key.find("[")].strip()
                else:
                    param_name = param_key
                    unit = ""
                
                # Apply search filter
                if search_term and search_term not in param_name.lower():
                    continue
                
                # Apply modified-only filter
                if show_modified_only and param_key not in self.modified_parameters:
                    continue
                
                # Format current value
                if isinstance(value, (int, float)):
                    if abs(value) < 1e-3 or abs(value) > 1e3:
                        value_str = f"{value:.2e}"
                    else:
                        value_str = f"{value:.4f}"
                else:
                    value_str = str(value)
                
                # Format original value
                original_value = original_items.get(param_key, value)
                if isinstance(original_value, (int, float)):
                    if abs(original_value) < 1e-3 or abs(original_value) > 1e3:
                        original_str = f"{original_value:.2e}"
                    else:
                        original_str = f"{original_value:.4f}"
                else:
                    original_str = str(original_value)
                
                # Determine tag for color coding
                tag = "normal"
                if param_key in self.modified_parameters:
                    tag = "modified"
                
                # Try to validate parameter and mark errors
                try:
                    self.validate_parameter_value(param_key, value)
                except ValueError:
                    tag = "error"
                
                # Insert item with appropriate tag
                self.param_tree.insert("", "end", 
                                     values=(param_name, value_str, unit, original_str),
                                     tags=(tag,))
                
        except Exception as e:
            print(f"Error refreshing parameter display: {e}")
    
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
            "Negative particle radius [m]": 5.86e-6,
            "Upper voltage cut-off [V]": 4.2,
            "Lower voltage cut-off [V]": 3.0
        }
        
        return MockParameterValues(mock_params)
    
    def get_mock_parameter_values_from_dict(self, param_dict):
        """Create mock parameter values from dictionary."""
        return MockParameterValues(param_dict)


class MockParameterValues:
    """Mock parameter values class for development."""
    
    def __init__(self, params):
        self.params = params
    
    def items(self):
        return self.params.items()
    
    def keys(self):
        return self.params.keys()
    
    def __getitem__(self, key):
        return self.params.get(key, "N/A")
    
    def __setitem__(self, key, value):
        self.params[key] = value
    
    def __contains__(self, key):
        return key in self.params


class ParameterEditDialog:
    """Dialog for editing parameter values."""
    
    def __init__(self, parent, param_name, current_value, unit):
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"パラメータ編集: {param_name}")
        self.dialog.geometry("400x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Create content
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Parameter info
        ttk.Label(main_frame, text=f"パラメータ: {param_name}", font=("", 12, "bold")).pack(pady=(0, 10))
        if unit:
            ttk.Label(main_frame, text=f"単位: {unit}").pack(pady=(0, 10))
        
        # Current value display
        ttk.Label(main_frame, text=f"現在値: {current_value}").pack(pady=(0, 10))
        
        # New value entry
        ttk.Label(main_frame, text="新しい値:").pack(pady=(0, 5))
        self.value_var = tk.StringVar(value=str(current_value))
        entry = ttk.Entry(main_frame, textvariable=self.value_var, width=30)
        entry.pack(pady=(0, 20))
        entry.focus()
        entry.select_range(0, tk.END)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="キャンセル", command=self.cancel_clicked).pack(side=tk.RIGHT)
        
        # Bind Enter and Escape keys
        self.dialog.bind('<Return>', lambda e: self.ok_clicked())
        self.dialog.bind('<Escape>', lambda e: self.cancel_clicked())
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def ok_clicked(self):
        """Handle OK button click."""
        try:
            value_str = self.value_var.get().strip()
            if not value_str:
                messagebox.showerror("エラー", "値を入力してください。")
                return
            
            # Try to convert to number
            if '.' in value_str or 'e' in value_str.lower():
                self.result = float(value_str)
            else:
                self.result = int(value_str)
            
            self.dialog.destroy()
            
        except ValueError:
            messagebox.showerror("エラー", "有効な数値を入力してください。")
    
    def cancel_clicked(self):
        """Handle Cancel button click."""
        self.result = None
        self.dialog.destroy()


# Add simulation functionality to the main class
def run_simulation(self):
    """Run enhanced PyBamm simulation with current parameters."""
    if self.current_parameter_values is None:
        messagebox.showerror("エラー", "パラメータプリセットを先に読み込んでください。")
        return
    
    # Validate parameters before simulation
    try:
        self.validate_parameters_for_simulation()
    except ValueError as e:
        messagebox.showerror("パラメータエラー", f"シミュレーション実行前にパラメータを修正してください:\n{str(e)}")
        return
    
    try:
        time_hours = self.time_hours_var.get()
        model_type = self.model_var.get()
        current_mode = self.current_mode_var.get()
        current_value = self.current_value_var.get()
        
        if time_hours <= 0:
            messagebox.showerror("エラー", "シミュレーション時間は正の値を入力してください。")
            return
        
        # Apply current settings to parameters
        self.apply_current_settings(current_mode, current_value)
        
        # Disable run button during simulation
        self.run_button.config(state=tk.DISABLED)
        
        # Run simulation in background
        self.app.run_in_background(
            f"拡張パラメータシミュレーション実行中... ({model_type}モデル)",
            lambda: self._run_enhanced_simulation_thread(time_hours, model_type)
        )
        
    except tk.TclError:
        messagebox.showerror("エラー", "無効なシミュレーション設定です。")

def apply_current_settings(self, current_mode, current_value):
    """Apply current/charge/discharge settings to parameters."""
    try:
        if current_mode == "discharge":
            # Negative current for discharge
            final_current = -abs(current_value)
        elif current_mode == "charge":
            # Positive current for charge
            final_current = abs(current_value)
        else:  # custom
            final_current = current_value
        
        # Update current parameter
        current_key = "Current function [A]"
        if hasattr(self.current_parameter_values, '__setitem__'):
            self.current_parameter_values[current_key] = final_current
        else:
            self.current_parameter_values.params[current_key] = final_current
        
        # Mark as modified if different from original
        if self.original_parameter_values:
            if hasattr(self.original_parameter_values, '__getitem__'):
                original_current = self.original_parameter_values[current_key]
            else:
                original_current = self.original_parameter_values.params.get(current_key, 0)
            
            if abs(final_current - original_current) > 1e-6:
                self.modified_parameters.add(current_key)
        
    except Exception as e:
        print(f"Error applying current settings: {e}")

def validate_parameters_for_simulation(self):
    """Validate parameters specifically for simulation execution."""
    errors = []
    
    if self.current_parameter_values is None:
        raise ValueError("パラメータが読み込まれていません。")
    
    # Get parameter items
    if hasattr(self.current_parameter_values, 'items'):
        param_items = dict(self.current_parameter_values.items())
    else:
        param_items = dict(self.current_parameter_values.params.items())
    
    # Critical parameter checks
    capacity = param_items.get("Nominal cell capacity [A.h]")
    if not capacity or capacity <= 0:
        errors.append("容量が設定されていないか無効です。")
    
    current = param_items.get("Current function [A]")
    if current is None:
        errors.append("電流が設定されていません。")
    
    temperature = param_items.get("Ambient temperature [K]")
    if not temperature or temperature < 200 or temperature > 400:
        errors.append("温度が無効な範囲です（200-400K）。")
    
    # Electrode thickness checks
    pos_thickness = param_items.get("Positive electrode thickness [m]")
    neg_thickness = param_items.get("Negative electrode thickness [m]")
    sep_thickness = param_items.get("Separator thickness [m]")
    
    if not all([pos_thickness, neg_thickness, sep_thickness]):
        errors.append("電極厚さが設定されていません。")
    elif any(t <= 0 for t in [pos_thickness, neg_thickness, sep_thickness]):
        errors.append("電極厚さは正の値である必要があります。")
    
    # Porosity checks
    pos_porosity = param_items.get("Positive electrode porosity")
    neg_porosity = param_items.get("Negative electrode porosity")
    sep_porosity = param_items.get("Separator porosity")
    
    if not all([pos_porosity, neg_porosity, sep_porosity]):
        errors.append("多孔度が設定されていません。")
    elif any(p <= 0 or p >= 1 for p in [pos_porosity, neg_porosity, sep_porosity]):
        errors.append("多孔度は0から1の間の値である必要があります。")
    
    if errors:
        raise ValueError("\n".join(errors))

def _run_enhanced_simulation_thread(self, time_hours, model_type):
    """Run enhanced simulation in separate thread with convergence monitoring."""
    try:
        if PYBAMM_AVAILABLE:
            # Create model based on selection
            if model_type == "DFN":
                model = pybamm.lithium_ion.DFN()
            elif model_type == "SPM":
                model = pybamm.lithium_ion.SPM()
            elif model_type == "SPMe":
                model = pybamm.lithium_ion.SPMe()
            else:
                raise ValueError(f"Unknown model type: {model_type}")
            
            # Create simulation with current parameters
            try:
                sim = pybamm.Simulation(
                    model, 
                    parameter_values=self.current_parameter_values,
                    solver=pybamm.CasadiSolver(mode="safe")
                )
            except Exception as e:
                raise ValueError(f"シミュレーション設定エラー: {str(e)}")
            
            # Solve simulation with convergence monitoring
            n_points = max(100, int(time_hours * 60))
            t_eval = np.linspace(0, time_hours * 3600, n_points)
            
            try:
                solution = sim.solve(t_eval)
                
                # Check for convergence issues
                if not self.check_solution_convergence(solution):
                    raise ValueError("シミュレーションが収束しませんでした。パラメータを確認してください。")
                
                # Extract comprehensive results
                self.simulation_results = self.extract_simulation_results(solution, model_type)
                
            except Exception as e:
                if "solver" in str(e).lower() or "convergence" in str(e).lower():
                    raise ValueError(f"シミュレーション収束エラー: パラメータ値を調整してください。\n詳細: {str(e)}")
                else:
                    raise ValueError(f"シミュレーション実行エラー: {str(e)}")
        
        else:
            # Enhanced mock simulation for development
            self.simulation_results = self._enhanced_mock_simulation(time_hours, model_type)
        
        # Update plot on main thread
        self.app.root.after(0, self.update_enhanced_plot)
        
        # Enable run button on main thread
        self.app.root.after(0, lambda: self.run_button.config(state=tk.NORMAL))
        
        # Show success message on main thread
        success_msg = f"{time_hours:.1f}時間の{model_type}シミュレーションが完了しました。"
        if self.modified_parameters:
            success_msg += f"\n{len(self.modified_parameters)}個のパラメータが変更されています。"
        
        self.app.root.after(0, lambda: messagebox.showinfo("完了", success_msg))
        
    except ValueError as e:
        # Handle validation and convergence errors
        self.app.root.after(0, lambda: self.run_button.config(state=tk.NORMAL))
        self.app.root.after(0, lambda: messagebox.showerror("シミュレーションエラー", str(e)))
        
    except Exception as e:
        # Handle unexpected errors
        self.app.root.after(0, lambda: self.run_button.config(state=tk.NORMAL))
        error_msg = f"予期しないエラーが発生しました: {str(e)}\n\nパラメータを確認してリセットを試してください。"
        self.app.root.after(0, lambda: messagebox.showerror("エラー", error_msg))

def check_solution_convergence(self, solution):
    """Check if simulation solution converged properly."""
    try:
        # Check if solution has valid time points
        if len(solution.t) < 10:
            return False
        
        # Check for NaN or infinite values in key variables
        voltage = solution["Terminal voltage [V]"].data
        current = solution["Current [A]"].data
        
        if np.any(np.isnan(voltage)) or np.any(np.isinf(voltage)):
            return False
        
        if np.any(np.isnan(current)) or np.any(np.isinf(current)):
            return False
        
        # Check for reasonable voltage range
        if np.any(voltage < 0) or np.any(voltage > 10):
            return False
        
        # Check for sudden jumps or discontinuities
        voltage_diff = np.diff(voltage)
        if np.any(np.abs(voltage_diff) > 1.0):  # More than 1V jump
            return False
        
        return True
        
    except Exception:
        return False

def extract_simulation_results(self, solution, model_type):
    """Extract comprehensive simulation results."""
    results = {
        'time': solution.t,
        'voltage': solution["Terminal voltage [V]"].data,
        'current': solution["Current [A]"].data,
        'model_type': model_type,
        'solution': solution
    }
    
    # Extract additional variables if available
    try:
        # Capacity data
        if "Discharge capacity [A.h]" in solution:
            results['capacity'] = solution["Discharge capacity [A.h]"].data
        else:
            # Calculate capacity from current and time
            current_data = results['current']
            time_data = results['time']
            capacity_data = np.cumsum(np.abs(current_data) * np.diff(np.concatenate([[0], time_data]))) / 3600
            results['capacity'] = capacity_data
        
        # Temperature data
        if "Cell temperature [K]" in solution:
            results['temperature'] = solution["Cell temperature [K]"].data
        
        # Voltage components for detailed analysis
        voltage_components = {}
        component_vars = [
            ("Open-circuit voltage [V]", 'ocv'),
            ("Ohmic losses [V]", 'ohmic'),
            ("Concentration overpotential [V]", 'concentration'),
            ("Reaction overpotential [V]", 'reaction'),
            ("X-averaged negative electrode open-circuit potential [V]", 'neg_ocv'),
            ("X-averaged positive electrode open-circuit potential [V]", 'pos_ocv'),
        ]
        
        for var_name, key in component_vars:
            if var_name in solution:
                voltage_components[key] = solution[var_name].data
        
        results['voltage_components'] = voltage_components
        
    except Exception as e:
        print(f"Warning: Could not extract additional variables: {e}")
        results['capacity'] = np.linspace(0, 2.5, len(results['time']))
        results['voltage_components'] = {}
    
    return results

def _enhanced_mock_simulation(self, time_hours, model_type):
    """Generate enhanced mock simulation data."""
    n_points = int(time_hours * 100)
    time = np.linspace(0, time_hours * 3600, n_points)
    
    # Get current parameters for realistic mock data
    if hasattr(self.current_parameter_values, 'items'):
        param_dict = dict(self.current_parameter_values.items())
    else:
        param_dict = dict(self.current_parameter_values.params.items())
    
    capacity = param_dict.get("Nominal cell capacity [A.h]", 2.5)
    current_val = param_dict.get("Current function [A]", -1.0)
    temperature = param_dict.get("Ambient temperature [K]", 298.15)
    
    # Generate realistic voltage curve based on current direction
    if current_val < 0:  # Discharge
        voltage = 4.2 - (4.2 - 3.0) * (time / (time_hours * 3600))
        voltage += 0.1 * np.sin(time / 1000) * np.exp(-time / (time_hours * 1800))  # Add some dynamics
    else:  # Charge
        voltage = 3.0 + (4.2 - 3.0) * (time / (time_hours * 3600))
        voltage += 0.05 * np.cos(time / 800) * (1 - np.exp(-time / 1000))
    
    # Current with some variation
    current = np.ones(n_points) * current_val
    current += 0.01 * current_val * np.sin(time / 500)  # Small variations
    
    # Capacity calculation
    capacity_data = np.cumsum(np.abs(current) * np.diff(np.concatenate([[0], time]))) / 3600
    
    # Temperature variation
    temp_data = np.ones(n_points) * temperature
    temp_data += 5 * np.sin(time / 2000) * (np.abs(current) / 2.0)  # Heat generation
    
    # Mock voltage components
    voltage_components = {
        'ocv': voltage + 0.1 + 0.05 * np.sin(time / 1200),
        'ohmic': -0.05 * np.abs(current) * (1 + 0.1 * np.sin(time / 600)),
        'concentration': -0.03 * np.abs(current) * (time / (time_hours * 3600)),
        'reaction': -0.04 * np.abs(current) * (1 + 0.2 * np.cos(time / 800)),
    }
    
    return {
        'time': time,
        'voltage': voltage,
        'current': current,
        'capacity': capacity_data,
        'temperature': temp_data,
        'voltage_components': voltage_components,
        'model_type': model_type,
        'solution': None
    }

def update_enhanced_plot(self):
    """Update plot with enhanced visualization options."""
    if self.simulation_results is None:
        return
    
    # Clear figure
    self.fig.clear()
    
    # Create subplots for comprehensive visualization
    if len(self.simulation_results.get('voltage_components', {})) > 0:
        # Multi-plot layout with voltage components
        gs = self.fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        # Main voltage plot
        ax1 = self.fig.add_subplot(gs[0, :])
        ax1.plot(self.simulation_results['time'] / 3600, self.simulation_results['voltage'], 
                'b-', linewidth=2, label='Terminal Voltage')
        ax1.set_xlabel('時間 (h)')
        ax1.set_ylabel('電圧 (V)')
        ax1.set_title(f'電圧 vs 時間 ({self.simulation_results.get("model_type", "Unknown")}モデル)')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Current plot
        ax2 = self.fig.add_subplot(gs[1, 0])
        ax2.plot(self.simulation_results['time'] / 3600, self.simulation_results['current'], 
                'r-', linewidth=2)
        ax2.set_xlabel('時間 (h)')
        ax2.set_ylabel('電流 (A)')
        ax2.set_title('電流')
        ax2.grid(True, alpha=0.3)
        
        # Capacity plot
        ax3 = self.fig.add_subplot(gs[1, 1])
        ax3.plot(self.simulation_results['time'] / 3600, self.simulation_results['capacity'], 
                'g-', linewidth=2)
        ax3.set_xlabel('時間 (h)')
        ax3.set_ylabel('容量 (A.h)')
        ax3.set_title('容量')
        ax3.grid(True, alpha=0.3)
        
    else:
        # Simple single plot
        ax = self.fig.add_subplot(1, 1, 1)
        ax.plot(self.simulation_results['time'] / 3600, self.simulation_results['voltage'], 
               'b-', linewidth=2)
        ax.set_xlabel('時間 (h)')
        ax.set_ylabel('電圧 (V)')
        
        title = f'電圧 vs 時間 ({self.simulation_results.get("model_type", "Unknown")}モデル)'
        if self.modified_parameters:
            title += f' - {len(self.modified_parameters)}個のパラメータ変更'
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
    
    # Update canvas
    self.fig.tight_layout()
    self.canvas.draw()

def clear_plot(self):
    """Clear the plot and reset simulation results."""
    # Clear figure
    self.fig.clear()
    
    # Add message
    self.fig.text(0.5, 0.5, "シミュレーション結果がここに表示されます\n\nパラメータを編集してシミュレーションを実行してください", 
                 ha='center', va='center', fontsize=12)
    
    # Update canvas
    self.canvas.draw()
    
    # Clear stored results
    self.simulation_results = None

# Add these methods to the AdvancedVariablesTab class
AdvancedVariablesTab.run_simulation = run_simulation
AdvancedVariablesTab.apply_current_settings = apply_current_settings
AdvancedVariablesTab.validate_parameters_for_simulation = validate_parameters_for_simulation
AdvancedVariablesTab._run_enhanced_simulation_thread = _run_enhanced_simulation_thread
AdvancedVariablesTab.check_solution_convergence = check_solution_convergence
AdvancedVariablesTab.extract_simulation_results = extract_simulation_results
AdvancedVariablesTab._enhanced_mock_simulation = _enhanced_mock_simulation
AdvancedVariablesTab.update_enhanced_plot = update_enhanced_plot
AdvancedVariablesTab.clear_plot = clear_plot
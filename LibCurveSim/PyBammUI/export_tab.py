"""
PyBamm Export Tab Module

This module provides the data export tab for the PyBamm UI application.
It allows users to export simulation results to CSV format.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import numpy as np
import os
from datetime import datetime


class ExportTab:
    """
    Class for the data export tab.
    """
    
    def __init__(self, parent, app):
        """
        Initialize the export tab.
        
        Args:
            parent: Parent widget
            app: Main application instance
        """
        self.app = app
        self.frame = ttk.Frame(parent)
        
        # Initialize variables
        self.setup_variables()
        
        # Create the UI
        self.setup_ui()
    
    def setup_variables(self):
        """Set up tkinter variables."""
        # Export options
        self.export_voltage_var = tk.BooleanVar(value=True)
        self.export_current_var = tk.BooleanVar(value=True)
        self.export_capacity_var = tk.BooleanVar(value=True)
        self.export_power_var = tk.BooleanVar(value=True)
        self.export_time_var = tk.BooleanVar(value=True)
        
        # File format
        self.file_format_var = tk.StringVar(value="CSV")
        
        # Output directory
        self.output_dir_var = tk.StringVar(value=os.path.expanduser("~/Desktop"))
        
        # Filename prefix
        self.filename_prefix_var = tk.StringVar(value="pybamm_simulation")
    
    def setup_ui(self):
        """Set up the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="データエクスポート", font=('TkDefaultFont', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="データ状態", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="シミュレーションデータがありません")
        self.status_label.pack()
        
        # Export options frame
        options_frame = ttk.LabelFrame(main_frame, text="エクスポートオプション", padding=10)
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Data selection
        data_frame = ttk.LabelFrame(options_frame, text="エクスポートするデータ", padding=5)
        data_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Checkbutton(data_frame, text="時間データ", variable=self.export_time_var).pack(anchor=tk.W)
        ttk.Checkbutton(data_frame, text="電圧データ", variable=self.export_voltage_var).pack(anchor=tk.W)
        ttk.Checkbutton(data_frame, text="電流データ", variable=self.export_current_var).pack(anchor=tk.W)
        ttk.Checkbutton(data_frame, text="容量データ", variable=self.export_capacity_var).pack(anchor=tk.W)
        ttk.Checkbutton(data_frame, text="電力データ (計算値)", variable=self.export_power_var).pack(anchor=tk.W)
        
        # File format selection
        format_frame = ttk.LabelFrame(options_frame, text="ファイル形式", padding=5)
        format_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Radiobutton(format_frame, text="CSV (カンマ区切り)", variable=self.file_format_var, value="CSV").pack(anchor=tk.W)
        ttk.Radiobutton(format_frame, text="TSV (タブ区切り)", variable=self.file_format_var, value="TSV").pack(anchor=tk.W)
        ttk.Radiobutton(format_frame, text="Excel (.xlsx)", variable=self.file_format_var, value="XLSX").pack(anchor=tk.W)
        
        # Output settings frame
        output_frame = ttk.LabelFrame(options_frame, text="出力設定", padding=5)
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Output directory
        dir_frame = ttk.Frame(output_frame)
        dir_frame.pack(fill=tk.X, pady=2)
        ttk.Label(dir_frame, text="出力ディレクトリ:").pack(anchor=tk.W)
        dir_entry_frame = ttk.Frame(dir_frame)
        dir_entry_frame.pack(fill=tk.X, pady=2)
        ttk.Entry(dir_entry_frame, textvariable=self.output_dir_var, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(dir_entry_frame, text="参照", command=self.browse_directory).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Filename prefix
        prefix_frame = ttk.Frame(output_frame)
        prefix_frame.pack(fill=tk.X, pady=2)
        ttk.Label(prefix_frame, text="ファイル名プレフィックス:").pack(anchor=tk.W)
        ttk.Entry(prefix_frame, textvariable=self.filename_prefix_var, width=30).pack(anchor=tk.W, pady=2)
        
        # Preview frame
        preview_frame = ttk.LabelFrame(main_frame, text="データプレビュー", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create treeview for data preview
        self.setup_preview_area(preview_frame)
        
        # Control buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Export button
        self.export_button = ttk.Button(
            button_frame, text="エクスポート実行",
            command=self.export_data, state=tk.DISABLED
        )
        self.export_button.pack(side=tk.LEFT, padx=5)
        
        # Preview button
        self.preview_button = ttk.Button(
            button_frame, text="プレビュー更新",
            command=self.update_preview, state=tk.DISABLED
        )
        self.preview_button.pack(side=tk.LEFT, padx=5)
        
        # Select all button
        select_all_button = ttk.Button(
            button_frame, text="全選択",
            command=self.select_all_data
        )
        select_all_button.pack(side=tk.LEFT, padx=5)
        
        # Clear selection button
        clear_button = ttk.Button(
            button_frame, text="選択解除",
            command=self.clear_selection
        )
        clear_button.pack(side=tk.LEFT, padx=5)
    
    def setup_preview_area(self, parent):
        """Set up the data preview area."""
        # Create frame for treeview and scrollbars
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview
        self.tree = ttk.Treeview(tree_frame, show='headings', height=10)
        
        # Create scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        
        # Configure treeview scrollbars
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Initial message
        self.tree.insert('', 'end', values=('シミュレーションを実行してデータを生成してください',))
    
    def update_available_data(self, simulation_results):
        """
        Update the available data for export.
        
        Args:
            simulation_results: Dictionary containing simulation results
        """
        if simulation_results is not None:
            self.status_label.config(text="シミュレーションデータが利用可能です")
            self.export_button.config(state=tk.NORMAL)
            self.preview_button.config(state=tk.NORMAL)
            self.update_preview()
        else:
            self.status_label.config(text="シミュレーションデータがありません")
            self.export_button.config(state=tk.DISABLED)
            self.preview_button.config(state=tk.DISABLED)
            self.clear_preview()
    
    def update_preview(self):
        """Update the data preview."""
        if self.app.simulation_results is None:
            self.clear_preview()
            return
        
        # Get selected data
        data_dict = self.get_selected_data()
        
        if not data_dict:
            self.clear_preview()
            return
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Set up columns
        columns = list(data_dict.keys())
        self.tree['columns'] = columns
        
        # Configure column headings and widths
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, minwidth=80)
        
        # Add data rows (show first 100 rows for preview)
        data_length = len(next(iter(data_dict.values())))
        preview_length = min(100, data_length)
        
        for i in range(preview_length):
            values = [f"{data_dict[col][i]:.6f}" if isinstance(data_dict[col][i], (int, float)) 
                     else str(data_dict[col][i]) for col in columns]
            self.tree.insert('', 'end', values=values)
        
        # Add info row if data is truncated
        if data_length > preview_length:
            info_values = [f"... (全{data_length}行中{preview_length}行を表示)" if i == 0 else "..." 
                          for i in range(len(columns))]
            self.tree.insert('', 'end', values=info_values)
    
    def clear_preview(self):
        """Clear the data preview."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree['columns'] = ()
        self.tree.insert('', 'end', values=('シミュレーションを実行してデータを生成してください',))
    
    def get_selected_data(self):
        """
        Get the selected data for export.
        
        Returns:
            dict: Dictionary containing selected data arrays
        """
        if self.app.simulation_results is None:
            return {}
        
        results = self.app.simulation_results
        data_dict = {}
        
        # Add selected data
        if self.export_time_var.get() and 'time' in results:
            data_dict['時間 (s)'] = results['time']
            data_dict['時間 (h)'] = results['time'] / 3600
        
        if self.export_voltage_var.get() and 'voltage' in results:
            data_dict['電圧 (V)'] = results['voltage']
        
        if self.export_current_var.get() and 'current' in results:
            data_dict['電流 (A)'] = results['current']
        
        if self.export_capacity_var.get() and 'capacity' in results and results['capacity'] is not None:
            data_dict['容量 (Ah)'] = results['capacity']
        
        if self.export_power_var.get() and 'voltage' in results and 'current' in results:
            data_dict['電力 (W)'] = results['voltage'] * results['current']
        
        return data_dict
    
    def export_data(self):
        """Export the selected data."""
        try:
            # Get selected data
            data_dict = self.get_selected_data()
            
            if not data_dict:
                messagebox.showwarning("警告", "エクスポートするデータが選択されていません。")
                return
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prefix = self.filename_prefix_var.get() or "pybamm_simulation"
            
            file_format = self.file_format_var.get()
            if file_format == "CSV":
                extension = ".csv"
            elif file_format == "TSV":
                extension = ".tsv"
            elif file_format == "XLSX":
                extension = ".xlsx"
            else:
                extension = ".csv"
            
            filename = f"{prefix}_{timestamp}{extension}"
            filepath = os.path.join(self.output_dir_var.get(), filename)
            
            # Create DataFrame
            df = pd.DataFrame(data_dict)
            
            # Export data
            if file_format == "CSV":
                df.to_csv(filepath, index=False, encoding='utf-8-sig')
            elif file_format == "TSV":
                df.to_csv(filepath, index=False, sep='\t', encoding='utf-8-sig')
            elif file_format == "XLSX":
                df.to_excel(filepath, index=False)
            
            # Show success message
            messagebox.showinfo(
                "エクスポート完了",
                f"データが正常にエクスポートされました。\n\nファイル: {filepath}\n行数: {len(df)}\n列数: {len(df.columns)}"
            )
            
        except Exception as e:
            messagebox.showerror("エラー", f"エクスポート中にエラーが発生しました: {str(e)}")
    
    def browse_directory(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(
            title="出力ディレクトリを選択",
            initialdir=self.output_dir_var.get()
        )
        if directory:
            self.output_dir_var.set(directory)
    
    def select_all_data(self):
        """Select all data types for export."""
        self.export_time_var.set(True)
        self.export_voltage_var.set(True)
        self.export_current_var.set(True)
        self.export_capacity_var.set(True)
        self.export_power_var.set(True)
        self.update_preview()
    
    def clear_selection(self):
        """Clear all data type selections."""
        self.export_time_var.set(False)
        self.export_voltage_var.set(False)
        self.export_current_var.set(False)
        self.export_capacity_var.set(False)
        self.export_power_var.set(False)
        self.update_preview()
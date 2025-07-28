"""
Data Export Tab Module

This module provides the data export tab for the battery simulation and analysis tool.
It allows users to export data to various formats.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import csv
import json
import numpy as np
import pandas as pd
from datetime import datetime


class DataExportTab:
    """
    Class for the data export tab.
    """
    
    def __init__(self, parent, app):
        """
        Initialize the data export tab.
        
        Args:
            parent: Parent widget
            app: Main application instance
        """
        self.frame = ttk.Frame(parent)
        self.app = app
        
        # Data storage
        self.available_data = {}
        
        # Create frames
        self.setup_frames()
        
        # Create controls
        self.setup_controls()
    
    def setup_frames(self):
        """Set up the frames for the tab."""
        # Main layout: controls on left, preview on right
        self.controls_frame = ttk.Frame(self.frame, padding=(10, 10))
        self.controls_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        self.preview_frame = ttk.Frame(self.frame, padding=(10, 10))
        self.preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Control sections
        self.data_frame = ttk.LabelFrame(self.controls_frame, text="データ選択", padding=(10, 5))
        self.data_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.format_frame = ttk.LabelFrame(self.controls_frame, text="出力形式", padding=(10, 5))
        self.format_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.options_frame = ttk.LabelFrame(self.controls_frame, text="オプション", padding=(10, 5))
        self.options_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.export_frame = ttk.LabelFrame(self.controls_frame, text="エクスポート", padding=(10, 5))
        self.export_frame.pack(fill=tk.X, pady=(0, 10))
    
    def setup_controls(self):
        """Set up the control widgets."""
        # Data selection controls
        self.setup_data_controls()
        
        # Format controls
        self.setup_format_controls()
        
        # Options controls
        self.setup_options_controls()
        
        # Export controls
        self.setup_export_controls()
        
        # Preview area
        self.setup_preview_area()
    
    def setup_data_controls(self):
        """Set up the data selection controls."""
        # Data type selection
        ttk.Label(self.data_frame, text="データタイプ:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.data_type_var = tk.StringVar(value="simulation")
        data_type_combo = ttk.Combobox(
            self.data_frame,
            textvariable=self.data_type_var,
            values=["simulation", "dqdv", "peaks", "ml"],
            state="readonly",
            width=15
        )
        data_type_combo.grid(row=0, column=1, sticky=tk.W, pady=2)
        data_type_combo.bind("<<ComboboxSelected>>", self.on_data_type_selected)
        
        # Cycle selection
        ttk.Label(self.data_frame, text="サイクル:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.cycle_var = tk.StringVar(value="all")
        self.cycle_combo = ttk.Combobox(
            self.data_frame,
            textvariable=self.cycle_var,
            values=["all"],
            state="readonly",
            width=15
        )
        self.cycle_combo.grid(row=1, column=1, sticky=tk.W, pady=2)
        self.cycle_combo.bind("<<ComboboxSelected>>", self.update_preview)
        
        # Data info
        self.data_info_var = tk.StringVar(value="データが選択されていません")
        ttk.Label(self.data_frame, textvariable=self.data_info_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=2)
    
    def setup_format_controls(self):
        """Set up the format selection controls."""
        # Format selection
        ttk.Label(self.format_frame, text="形式:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.format_var = tk.StringVar(value="csv")
        format_combo = ttk.Combobox(
            self.format_frame,
            textvariable=self.format_var,
            values=["csv", "json", "excel"],
            state="readonly",
            width=15
        )
        format_combo.grid(row=0, column=1, sticky=tk.W, pady=2)
        format_combo.bind("<<ComboboxSelected>>", self.update_preview)
        
        # Delimiter selection (for CSV)
        ttk.Label(self.format_frame, text="区切り文字:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.delimiter_var = tk.StringVar(value=",")
        delimiter_combo = ttk.Combobox(
            self.format_frame,
            textvariable=self.delimiter_var,
            values=[",", "\t", ";", " "],
            state="readonly",
            width=15
        )
        delimiter_combo.grid(row=1, column=1, sticky=tk.W, pady=2)
        delimiter_combo.bind("<<ComboboxSelected>>", self.update_preview)
    
    def setup_options_controls(self):
        """Set up the options controls."""
        # Include header
        self.header_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.options_frame,
            text="ヘッダーを含める",
            variable=self.header_var,
            command=self.update_preview
        ).grid(row=0, column=0, sticky=tk.W, pady=2)
        
        # Include index
        self.index_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.options_frame,
            text="インデックスを含める",
            variable=self.index_var,
            command=self.update_preview
        ).grid(row=1, column=0, sticky=tk.W, pady=2)
    
    def setup_export_controls(self):
        """Set up the export controls."""
        # Output directory
        ttk.Label(self.export_frame, text="出力先:").grid(row=0, column=0, sticky=tk.W, pady=2)
        
        dir_frame = ttk.Frame(self.export_frame)
        dir_frame.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        self.output_dir_var = tk.StringVar(value="results")
        output_dir_entry = ttk.Entry(dir_frame, textvariable=self.output_dir_var, width=20)
        output_dir_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            dir_frame,
            text="参照",
            command=self.select_output_dir
        ).pack(side=tk.LEFT)
        
        # Filename
        ttk.Label(self.export_frame, text="ファイル名:").grid(row=1, column=0, sticky=tk.W, pady=2)
        
        filename_frame = ttk.Frame(self.export_frame)
        filename_frame.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        self.filename_var = tk.StringVar(value="export")
        ttk.Entry(filename_frame, textvariable=self.filename_var, width=20).pack(side=tk.LEFT, padx=(0, 5))
        
        self.add_timestamp_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            filename_frame,
            text="タイムスタンプ",
            variable=self.add_timestamp_var
        ).pack(side=tk.LEFT)
        
        # Export button
        self.export_button = ttk.Button(
            self.export_frame,
            text="エクスポート",
            command=self.export_data
        )
        self.export_button.grid(row=2, column=0, columnspan=2, pady=5)
    
    def setup_preview_area(self):
        """Set up the preview area."""
        # Preview label
        ttk.Label(self.preview_frame, text="プレビュー:").pack(anchor=tk.W)
        
        # Preview text
        self.preview_text = tk.Text(self.preview_frame, wrap=tk.NONE, width=60, height=20)
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        y_scrollbar = ttk.Scrollbar(self.preview_text, orient=tk.VERTICAL, command=self.preview_text.yview)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        x_scrollbar = ttk.Scrollbar(self.preview_frame, orient=tk.HORIZONTAL, command=self.preview_text.xview)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.preview_text.config(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
    
    def on_data_type_selected(self, event=None):
        """
        Handle data type selection.
        
        Args:
            event: Event that triggered the selection (optional)
        """
        data_type = self.data_type_var.get()
        
        # Update cycle selection based on data type
        self.update_cycle_selection(data_type)
        
        # Update preview
        self.update_preview()
    
    def update_cycle_selection(self, data_type):
        """
        Update cycle selection based on data type.
        
        Args:
            data_type: Selected data type
        """
        cycles = ["all"]
        
        if data_type == "simulation" and self.app.simulation_results is not None:
            cycles.extend([str(result['cycle']) for result in self.app.simulation_results])
        elif data_type == "dqdv" and hasattr(self.app.analysis_tab, 'dqdv_data') and self.app.analysis_tab.dqdv_data is not None:
            cycles.extend([str(cycle) for cycle in sorted(self.app.analysis_tab.dqdv_data.keys())])
        elif data_type == "peaks" and hasattr(self.app.analysis_tab, 'peak_data') and self.app.analysis_tab.peak_data is not None:
            cycles.extend([str(cycle) for cycle in sorted(self.app.analysis_tab.peak_data.keys())])
        
        # Update combobox
        self.cycle_combo['values'] = cycles
        
        # Select "all" if current selection is not in the new values
        if self.cycle_var.get() not in cycles:
            self.cycle_var.set("all")
    
    def update_preview(self, event=None):
        """
        Update the preview.
        
        Args:
            event: Event that triggered the update (optional)
        """
        # Get selected data
        data = self.get_selected_data()
        
        if data is None:
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, "データがありません")
            return
        
        # Convert data to selected format
        preview_text = self.format_data(data)
        
        # Update preview
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(tk.END, preview_text)
    
    def get_selected_data(self):
        """
        Get the selected data.
        
        Returns:
            Selected data or None if no data is available
        """
        data_type = self.data_type_var.get()
        cycle = self.cycle_var.get()
        
        # Convert cycle to int if it's not "all"
        if cycle != "all":
            cycle = int(cycle)
        
        # Get data based on type
        if data_type == "simulation":
            return self.get_simulation_data(cycle)
        elif data_type == "dqdv":
            return self.get_dqdv_data(cycle)
        elif data_type == "peaks":
            return self.get_peak_data(cycle)
        elif data_type == "ml":
            return self.get_ml_data()
        
        return None
    
    def get_simulation_data(self, cycle):
        """
        Get simulation data.
        
        Args:
            cycle: Cycle number or "all"
            
        Returns:
            Simulation data or None if no data is available
        """
        if self.app.simulation_results is None:
            self.data_info_var.set("シミュレーションデータがありません")
            return None
        
        # Update data info
        self.data_info_var.set(f"シミュレーションデータ: {len(self.app.simulation_results)}サイクル")
        
        # Get data for specific cycle
        if cycle != "all":
            for result in self.app.simulation_results:
                if result['cycle'] == cycle:
                    # Create DataFrame for charge data
                    charge_df = pd.DataFrame({
                        'Cycle': cycle,
                        'Type': 'Charge',
                        'SOC': result['charge']['soc'],
                        'Capacity': result['charge']['capacity'],
                        'Voltage': result['charge']['voltage']
                    })
                    
                    # Create DataFrame for discharge data
                    discharge_df = pd.DataFrame({
                        'Cycle': cycle,
                        'Type': 'Discharge',
                        'SOC': result['discharge']['soc'],
                        'Capacity': result['discharge']['capacity'],
                        'Voltage': result['discharge']['voltage']
                    })
                    
                    # Combine DataFrames
                    return pd.concat([charge_df, discharge_df])
            
            # Cycle not found
            self.data_info_var.set(f"サイクル {cycle} が見つかりません")
            return None
        
        # Get data for all cycles
        dfs = []
        
        for result in self.app.simulation_results:
            cycle = result['cycle']
            
            # Create DataFrame for charge data
            charge_df = pd.DataFrame({
                'Cycle': cycle,
                'Type': 'Charge',
                'SOC': result['charge']['soc'],
                'Capacity': result['charge']['capacity'],
                'Voltage': result['charge']['voltage']
            })
            
            # Create DataFrame for discharge data
            discharge_df = pd.DataFrame({
                'Cycle': cycle,
                'Type': 'Discharge',
                'SOC': result['discharge']['soc'],
                'Capacity': result['discharge']['capacity'],
                'Voltage': result['discharge']['voltage']
            })
            
            dfs.append(charge_df)
            dfs.append(discharge_df)
        
        # Combine DataFrames
        return pd.concat(dfs)
    
    def get_dqdv_data(self, cycle):
        """
        Get dQ/dV data.
        
        Args:
            cycle: Cycle number or "all"
            
        Returns:
            dQ/dV data or None if no data is available
        """
        if not hasattr(self.app.analysis_tab, 'dqdv_data') or self.app.analysis_tab.dqdv_data is None:
            self.data_info_var.set("dQ/dVデータがありません")
            return None
        
        dqdv_data = self.app.analysis_tab.dqdv_data
        
        # Update data info
        self.data_info_var.set(f"dQ/dVデータ: {len(dqdv_data)}サイクル")
        
        # Get data for specific cycle
        if cycle != "all":
            if cycle in dqdv_data:
                # Create DataFrame
                return pd.DataFrame({
                    'Cycle': cycle,
                    'Voltage': dqdv_data[cycle]['voltage'],
                    'dQdV': dqdv_data[cycle]['dqdv']
                })
            
            # Cycle not found
            self.data_info_var.set(f"サイクル {cycle} が見つかりません")
            return None
        
        # Get data for all cycles
        dfs = []
        
        for cycle, data in dqdv_data.items():
            # Create DataFrame
            df = pd.DataFrame({
                'Cycle': cycle,
                'Voltage': data['voltage'],
                'dQdV': data['dqdv']
            })
            
            dfs.append(df)
        
        # Combine DataFrames
        return pd.concat(dfs)
    
    def get_peak_data(self, cycle):
        """
        Get peak data.
        
        Args:
            cycle: Cycle number or "all"
            
        Returns:
            Peak data or None if no data is available
        """
        if not hasattr(self.app.analysis_tab, 'peak_data') or self.app.analysis_tab.peak_data is None:
            self.data_info_var.set("ピークデータがありません")
            return None
        
        peak_data = self.app.analysis_tab.peak_data
        
        # Update data info
        self.data_info_var.set(f"ピークデータ: {len(peak_data)}サイクル")
        
        # Get data for specific cycle
        if cycle != "all":
            if cycle in peak_data:
                # Create DataFrame
                return pd.DataFrame({
                    'Cycle': cycle,
                    'Peak_Index': range(len(peak_data[cycle]['peak_voltages'])),
                    'Voltage': peak_data[cycle]['peak_voltages'],
                    'dQdV': peak_data[cycle]['peak_dqdvs'],
                    'Prominence': peak_data[cycle]['prominences'],
                    'Width': peak_data[cycle]['widths']
                })
            
            # Cycle not found
            self.data_info_var.set(f"サイクル {cycle} が見つかりません")
            return None
        
        # Get data for all cycles
        dfs = []
        
        for cycle, data in peak_data.items():
            # Create DataFrame
            df = pd.DataFrame({
                'Cycle': cycle,
                'Peak_Index': range(len(data['peak_voltages'])),
                'Voltage': data['peak_voltages'],
                'dQdV': data['peak_dqdvs'],
                'Prominence': data['prominences'],
                'Width': data['widths']
            })
            
            dfs.append(df)
        
        # Combine DataFrames
        return pd.concat(dfs)
    
    def get_ml_data(self):
        """
        Get machine learning data.
        
        Returns:
            Machine learning data or None if no data is available
        """
        if not hasattr(self.app.ml_tab, 'ml_results') or self.app.ml_tab.ml_results is None:
            self.data_info_var.set("機械学習結果がありません")
            return None
        
        ml_results = self.app.ml_tab.ml_results
        model_type = self.app.ml_tab.selected_model
        
        # Update data info
        self.data_info_var.set(f"機械学習結果: {model_type}")
        
        # Get data based on model type
        if model_type == "pca":
            # Create DataFrame for principal components
            pc_df = pd.DataFrame(
                ml_results['principal_components'],
                columns=[f"PC{i+1}" for i in range(ml_results['principal_components'].shape[1])]
            )
            pc_df['Cycle'] = ml_results['cycle_numbers']
            
            # Create DataFrame for explained variance
            ev_df = pd.DataFrame({
                'Component': range(1, len(ml_results['explained_variance_ratio']) + 1),
                'Explained_Variance_Ratio': ml_results['explained_variance_ratio'],
                'Cumulative_Explained_Variance': np.cumsum(ml_results['explained_variance_ratio'])
            })
            
            # Create DataFrame for loadings
            loadings_df = pd.DataFrame(
                ml_results['loadings'],
                columns=[f"PC{i+1}" for i in range(ml_results['loadings'].shape[1])]
            )
            loadings_df['Voltage'] = ml_results['voltage_grid']
            
            # Combine DataFrames
            return {
                'principal_components': pc_df,
                'explained_variance': ev_df,
                'loadings': loadings_df
            }
            
        elif model_type in ["random_forest", "neural_network", "svr"]:
            # Create DataFrame for predictions
            pred_df = pd.DataFrame({
                'True_Value': ml_results['y_test'],
                'Predicted_Value': ml_results['y_pred_test'],
                'Error': ml_results['y_test'] - ml_results['y_pred_test']
            })
            
            # Create DataFrame for metrics
            metrics_df = pd.DataFrame({
                'Metric': ['MSE', 'MAE', 'R2'],
                'Train': [ml_results['train_mse'], ml_results['train_mae'], ml_results['train_r2']],
                'Test': [ml_results['test_mse'], ml_results['test_mae'], ml_results['test_r2']]
            })
            
            # Create DataFrame for feature importances (Random Forest only)
            if model_type == "random_forest":
                fi_df = pd.DataFrame({
                    'Voltage': ml_results['voltage_grid'],
                    'Feature_Importance': ml_results['feature_importances']
                })
                
                return {
                    'predictions': pred_df,
                    'metrics': metrics_df,
                    'feature_importances': fi_df
                }
            
            return {
                'predictions': pred_df,
                'metrics': metrics_df
            }
            
        elif model_type == "clustering":
            # Create DataFrame for cluster labels
            cluster_df = pd.DataFrame({
                'Cycle': ml_results['cycle_numbers'],
                'Cluster': ml_results['labels']
            })
            
            return {
                'clusters': cluster_df
            }
        
        return None
    
    def format_data(self, data):
        """
        Format data according to selected format.
        
        Args:
            data: Data to format
            
        Returns:
            Formatted data as string
        """
        if data is None:
            return "データがありません"
        
        format_type = self.format_var.get()
        
        # Handle ML data (dictionary of DataFrames)
        if isinstance(data, dict):
            result = []
            
            for name, df in data.items():
                result.append(f"=== {name} ===")
                result.append(self.format_dataframe(df, format_type))
                result.append("")
            
            return "\n".join(result)
        
        # Handle regular DataFrame
        return self.format_dataframe(data, format_type)
    
    def format_dataframe(self, df, format_type):
        """
        Format DataFrame according to selected format.
        
        Args:
            df: DataFrame to format
            format_type: Format type
            
        Returns:
            Formatted DataFrame as string
        """
        if format_type == "csv":
            # Format as CSV
            return df.to_csv(
                sep=self.delimiter_var.get(),
                index=self.index_var.get(),
                header=self.header_var.get()
            )
        elif format_type == "json":
            # Format as JSON
            return df.to_json(orient="records", indent=2)
        elif format_type == "excel":
            # Format as Excel (preview as CSV)
            return "Excel形式はプレビューできません。エクスポート時にExcel形式で保存されます。"
        
        return "未対応の形式です"
    
    def select_output_dir(self):
        """Select output directory."""
        directory = filedialog.askdirectory(
            title="出力先ディレクトリを選択",
            initialdir=self.output_dir_var.get()
        )
        
        if directory:
            self.output_dir_var.set(directory)
    
    def export_data(self):
        """Export data to file."""
        # Get selected data
        data = self.get_selected_data()
        
        if data is None:
            messagebox.showinfo("情報", "エクスポートするデータがありません。")
            return
        
        # Get output directory
        output_dir = self.output_dir_var.get()
        
        # Create directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Get filename
        filename = self.filename_var.get()
        
        # Add timestamp if requested
        if self.add_timestamp_var.get():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename}_{timestamp}"
        
        # Get format
        format_type = self.format_var.get()
        
        # Export data
        try:
            # Handle ML data (dictionary of DataFrames)
            if isinstance(data, dict):
                saved_files = []
                
                for name, df in data.items():
                    # Create filename
                    file_path = os.path.join(output_dir, f"{filename}_{name}")
                    
                    # Export based on format
                    if format_type == "csv":
                        file_path = f"{file_path}.csv"
                        df.to_csv(
                            file_path,
                            sep=self.delimiter_var.get(),
                            index=self.index_var.get(),
                            header=self.header_var.get()
                        )
                    elif format_type == "json":
                        file_path = f"{file_path}.json"
                        df.to_json(file_path, orient="records", indent=2)
                    elif format_type == "excel":
                        file_path = f"{file_path}.xlsx"
                        df.to_excel(file_path, index=self.index_var.get(), header=self.header_var.get())
                    
                    saved_files.append(file_path)
                
                messagebox.showinfo("完了", f"データを {len(saved_files)} ファイルにエクスポートしました。")
                
            else:
                # Create filename
                file_path = os.path.join(output_dir, filename)
                
                # Export based on format
                if format_type == "csv":
                    file_path = f"{file_path}.csv"
                    data.to_csv(
                        file_path,
                        sep=self.delimiter_var.get(),
                        index=self.index_var.get(),
                        header=self.header_var.get()
                    )
                elif format_type == "json":
                    file_path = f"{file_path}.json"
                    data.to_json(file_path, orient="records", indent=2)
                elif format_type == "excel":
                    file_path = f"{file_path}.xlsx"
                    data.to_excel(file_path, index=self.index_var.get(), header=self.header_var.get())
                
                messagebox.showinfo("完了", f"データを {file_path} にエクスポートしました。")
            
        except Exception as e:
            messagebox.showerror("エラー", f"エクスポート中にエラーが発生しました: {str(e)}")
    
    def update_available_data(self, **kwargs):
        """
        Update available data.
        
        Args:
            **kwargs: Available data
        """
        self.available_data = kwargs
        
        # Update data info
        data_types = []
        
        if kwargs.get('simulation_results') is not None:
            data_types.append("simulation")
        
        if kwargs.get('dqdv_data') is not None:
            data_types.append("dqdv")
        
        if kwargs.get('peak_data') is not None:
            data_types.append("peaks")
        
        if kwargs.get('ml_results') is not None:
            data_types.append("ml")
        
        if data_types:
            self.data_info_var.set(f"利用可能なデータ: {', '.join(data_types)}")
        else:
            self.data_info_var.set("データがありません")
        
        # Update cycle selection
        self.update_cycle_selection(self.data_type_var.get())
        
        # Update preview
        self.update_preview()
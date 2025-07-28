"""
Machine Learning Tab Module

This module provides the machine learning tab for the battery simulation and analysis tool.
It allows users to apply machine learning techniques to battery data.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
import os
import threading


class MLTab:
    """
    Class for the machine learning tab.
    """
    
    def __init__(self, parent, app):
        """
        Initialize the machine learning tab.
        
        Args:
            parent: Parent widget
            app: Main application instance
        """
        self.frame = ttk.Frame(parent)
        self.app = app
        
        # Data storage
        self.ml_results = None
        self.selected_model = "pca"
        
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
        
        self.model_frame = ttk.LabelFrame(self.controls_frame, text="モデル", padding=(10, 5))
        self.model_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.params_frame = ttk.LabelFrame(self.controls_frame, text="パラメータ", padding=(10, 5))
        self.params_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.run_frame = ttk.LabelFrame(self.controls_frame, text="実行", padding=(10, 5))
        self.run_frame.pack(fill=tk.X, pady=(0, 10))
    
    def setup_controls(self):
        """Set up the control widgets."""
        # Data controls
        self.setup_data_controls()
        
        # Model controls
        self.setup_model_controls()
        
        # Parameter controls
        self.setup_parameter_controls()
        
        # Run controls
        self.setup_run_controls()
    
    def setup_data_controls(self):
        """Set up the data control widgets."""
        # Load data button
        self.load_button = ttk.Button(
            self.data_frame,
            text="データを開く",
            command=self.load_data
        )
        self.load_button.grid(row=0, column=0, sticky=tk.W, pady=2)
        
        # Data info
        self.data_info_var = tk.StringVar(value="データが読み込まれていません")
        ttk.Label(self.data_frame, textvariable=self.data_info_var).grid(row=1, column=0, sticky=tk.W, pady=2)
    
    def setup_model_controls(self):
        """Set up the model control widgets."""
        # Model selection
        ttk.Label(self.model_frame, text="モデル:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.model_var = tk.StringVar(value="pca")
        model_combo = ttk.Combobox(
            self.model_frame,
            textvariable=self.model_var,
            values=["pca", "random_forest", "clustering", "neural_network", "svr"],
            state="readonly",
            width=15
        )
        model_combo.grid(row=0, column=1, sticky=tk.W, pady=2)
        model_combo.bind("<<ComboboxSelected>>", self.on_model_selected)
    
    def setup_parameter_controls(self):
        """Set up the parameter control widgets."""
        # PCA parameters
        self.pca_frame = ttk.Frame(self.params_frame)
        self.pca_frame.pack(fill=tk.X)
        
        ttk.Label(self.pca_frame, text="主成分数:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.n_components_var = tk.IntVar(value=3)
        ttk.Entry(self.pca_frame, textvariable=self.n_components_var, width=5).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(self.pca_frame, text="標準化:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.scale_data_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.pca_frame, variable=self.scale_data_var).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # Random Forest parameters
        self.rf_frame = ttk.Frame(self.params_frame)
        
        ttk.Label(self.rf_frame, text="テストサイズ:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.test_size_var = tk.DoubleVar(value=0.2)
        ttk.Entry(self.rf_frame, textvariable=self.test_size_var, width=5).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(self.rf_frame, text="木の数:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.n_estimators_var = tk.IntVar(value=100)
        ttk.Entry(self.rf_frame, textvariable=self.n_estimators_var, width=5).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(self.rf_frame, text="最大深さ:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.max_depth_var = tk.IntVar(value=None)
        max_depth_entry = ttk.Entry(self.rf_frame, textvariable=self.max_depth_var, width=5)
        max_depth_entry.grid(row=2, column=1, sticky=tk.W, pady=2)
        max_depth_entry.delete(0, tk.END)  # Clear the "None" text
        
        # Clustering parameters
        self.clustering_frame = ttk.Frame(self.params_frame)
        
        ttk.Label(self.clustering_frame, text="クラスタ数:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.n_clusters_var = tk.IntVar(value=3)
        ttk.Entry(self.clustering_frame, textvariable=self.n_clusters_var, width=5).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(self.clustering_frame, text="手法:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.clustering_method_var = tk.StringVar(value="kmeans")
        method_combo = ttk.Combobox(
            self.clustering_frame,
            textvariable=self.clustering_method_var,
            values=["kmeans", "dbscan"],
            state="readonly",
            width=10
        )
        method_combo.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # Neural Network parameters
        self.nn_frame = ttk.Frame(self.params_frame)
        
        ttk.Label(self.nn_frame, text="隠れ層:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.hidden_layers_var = tk.StringVar(value="64,32")
        ttk.Entry(self.nn_frame, textvariable=self.hidden_layers_var, width=10).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(self.nn_frame, text="ドロップアウト率:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.dropout_rate_var = tk.DoubleVar(value=0.2)
        ttk.Entry(self.nn_frame, textvariable=self.dropout_rate_var, width=5).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(self.nn_frame, text="エポック数:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.epochs_var = tk.IntVar(value=200)
        ttk.Entry(self.nn_frame, textvariable=self.epochs_var, width=5).grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # SVR parameters
        self.svr_frame = ttk.Frame(self.params_frame)
        
        ttk.Label(self.svr_frame, text="カーネル:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.kernel_var = tk.StringVar(value="rbf")
        kernel_combo = ttk.Combobox(
            self.svr_frame,
            textvariable=self.kernel_var,
            values=["linear", "poly", "rbf", "sigmoid"],
            state="readonly",
            width=10
        )
        kernel_combo.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(self.svr_frame, text="C:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.c_var = tk.DoubleVar(value=1.0)
        ttk.Entry(self.svr_frame, textvariable=self.c_var, width=5).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(self.svr_frame, text="Epsilon:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.epsilon_var = tk.DoubleVar(value=0.1)
        ttk.Entry(self.svr_frame, textvariable=self.epsilon_var, width=5).grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # Show only the selected model's parameters
        self.show_selected_model_params()
    
    def setup_run_controls(self):
        """Set up the run control widgets."""
        # Run button
        self.run_button = ttk.Button(
            self.run_frame,
            text="実行",
            command=self.run_ml
        )
        self.run_button.pack(pady=5)
    
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
        self.fig.text(0.5, 0.5, "機械学習結果がここに表示されます", 
                     ha='center', va='center', fontsize=12)
        self.canvas.draw()
    
    def on_model_selected(self, event=None):
        """
        Handle model selection.
        
        Args:
            event: Event that triggered the selection (optional)
        """
        self.selected_model = self.model_var.get()
        self.show_selected_model_params()
    
    def show_selected_model_params(self):
        """Show only the selected model's parameters."""
        # Hide all parameter frames
        self.pca_frame.pack_forget()
        self.rf_frame.pack_forget()
        self.clustering_frame.pack_forget()
        self.nn_frame.pack_forget()
        self.svr_frame.pack_forget()
        
        # Show the selected model's parameters
        if self.selected_model == "pca":
            self.pca_frame.pack(fill=tk.X)
        elif self.selected_model == "random_forest":
            self.rf_frame.pack(fill=tk.X)
        elif self.selected_model == "clustering":
            self.clustering_frame.pack(fill=tk.X)
        elif self.selected_model == "neural_network":
            self.nn_frame.pack(fill=tk.X)
        elif self.selected_model == "svr":
            self.svr_frame.pack(fill=tk.X)
    
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
            if data['type'] == 'dqdv':
                # Store dQ/dV data
                self.dqdv_data = data['data']
                
                # Update data info
                cycles = sorted(self.dqdv_data.keys())
                self.data_info_var.set(f"dQ/dVデータ: {len(cycles)}サイクル")
                
            elif data['type'] == 'charge_discharge':
                # Calculate dQ/dV curves
                self.dqdv_data = self.app.processor.process_charge_discharge_data(data['data'])
                
                # Update data info
                cycles = sorted(self.dqdv_data.keys())
                self.data_info_var.set(f"充放電データから計算: {len(cycles)}サイクル")
                
            else:
                messagebox.showinfo("情報", f"未対応のデータ形式です: {data['type']}")
                return
            
        except Exception as e:
            messagebox.showerror("エラー", f"データ読み込み中にエラーが発生しました: {str(e)}")
    
    def run_ml(self):
        """Run machine learning analysis."""
        if not hasattr(self, 'dqdv_data') or self.dqdv_data is None:
            messagebox.showinfo("情報", "解析するデータがありません。")
            return
        
        # Disable run button during analysis
        self.run_button.config(state=tk.DISABLED)
        
        # Run analysis in background
        self.app.run_in_background(
            "機械学習解析実行中...",
            self._run_ml_thread
        )
    
    def _run_ml_thread(self):
        """Run machine learning analysis in a separate thread."""
        try:
            # Prepare data for ML
            if self.selected_model in ["random_forest", "neural_network", "svr"]:
                # For supervised learning, we need capacity data
                if not hasattr(self.app, 'simulation_results') or self.app.simulation_results is None:
                    messagebox.showinfo("情報", "容量データがありません。シミュレーションを実行してください。")
                    self.run_button.config(state=tk.NORMAL)
                    return
                
                # Extract capacity data
                capacity_data = {result['cycle']: result['capacity'] for result in self.app.simulation_results}
                
                # Prepare data
                ml_data = self.app.analyzer.prepare_data_for_ml(self.dqdv_data, capacity_data)
                
            else:
                # For unsupervised learning, we don't need capacity data
                ml_data = self.app.analyzer.prepare_data_for_ml(self.dqdv_data)
            
            # Run selected model
            if self.selected_model == "pca":
                self.ml_results = self.app.analyzer.perform_pca(
                    n_components=self.n_components_var.get(),
                    scale_data=self.scale_data_var.get()
                )
                
            elif self.selected_model == "random_forest":
                # Get parameters
                test_size = self.test_size_var.get()
                n_estimators = self.n_estimators_var.get()
                
                # Get max_depth (optional)
                try:
                    max_depth = self.max_depth_var.get()
                except tk.TclError:
                    max_depth = None
                
                self.ml_results = self.app.analyzer.train_random_forest(
                    test_size=test_size,
                    n_estimators=n_estimators,
                    max_depth=max_depth
                )
                
            elif self.selected_model == "clustering":
                self.ml_results = self.app.analyzer.perform_clustering(
                    n_clusters=self.n_clusters_var.get(),
                    method=self.clustering_method_var.get(),
                    scale_data=True
                )
                
            elif self.selected_model == "neural_network":
                # Parse hidden layers
                hidden_layers = [int(x) for x in self.hidden_layers_var.get().split(',')]
                
                self.ml_results = self.app.analyzer.train_neural_network(
                    test_size=self.test_size_var.get(),
                    hidden_layers=hidden_layers,
                    dropout_rate=self.dropout_rate_var.get(),
                    epochs=self.epochs_var.get()
                )
                
            elif self.selected_model == "svr":
                self.ml_results = self.app.analyzer.train_svr(
                    test_size=self.test_size_var.get(),
                    kernel=self.kernel_var.get(),
                    C=self.c_var.get(),
                    epsilon=self.epsilon_var.get()
                )
            
            # Update plot
            self.update_plot()
            
            # Enable run button
            self.run_button.config(state=tk.NORMAL)
            
            # Show success message
            messagebox.showinfo("完了", "機械学習解析が完了しました。")
            
        except Exception as e:
            # Enable run button
            self.run_button.config(state=tk.NORMAL)
            
            # Show error message
            messagebox.showerror("エラー", f"機械学習解析中にエラーが発生しました: {str(e)}")
    
    def update_plot(self):
        """Update the plot with the current ML results."""
        if self.ml_results is None:
            return
        
        # Clear figure
        self.fig.clear()
        
        # Plot based on selected model
        if self.selected_model == "pca":
            self._plot_pca_results()
        elif self.selected_model == "random_forest":
            self._plot_random_forest_results()
        elif self.selected_model == "clustering":
            self._plot_clustering_results()
        elif self.selected_model == "neural_network":
            self._plot_neural_network_results()
        elif self.selected_model == "svr":
            self._plot_svr_results()
        
        # Update canvas
        self.fig.tight_layout()
        self.canvas.draw()
    
    def _plot_pca_results(self):
        """Plot PCA results."""
        # Create subplots
        ax1 = self.fig.add_subplot(2, 2, 1)
        ax2 = self.fig.add_subplot(2, 2, 2)
        ax3 = self.fig.add_subplot(2, 2, 3)
        ax4 = self.fig.add_subplot(2, 2, 4)
        
        # Plot explained variance
        explained_variance = self.ml_results['explained_variance_ratio']
        components = np.arange(1, len(explained_variance) + 1)
        
        ax1.bar(components, explained_variance)
        ax1.plot(components, np.cumsum(explained_variance), 'ro-')
        ax1.set_xlabel('Principal Component')
        ax1.set_ylabel('Explained Variance Ratio')
        ax1.set_title('Explained Variance by Component')
        ax1.grid(True)
        
        # Plot first two principal components
        principal_components = self.ml_results['principal_components']
        cycle_numbers = self.ml_results['cycle_numbers']
        
        scatter = ax2.scatter(
            principal_components[:, 0],
            principal_components[:, 1],
            c=cycle_numbers,
            cmap='viridis',
            s=100,
            alpha=0.8
        )
        
        for i, cycle in enumerate(cycle_numbers):
            ax2.text(
                principal_components[i, 0],
                principal_components[i, 1],
                str(cycle),
                fontsize=10
            )
        
        ax2.set_xlabel('Principal Component 1')
        ax2.set_ylabel('Principal Component 2')
        ax2.set_title('PCA: First Two Principal Components')
        ax2.grid(True)
        plt.colorbar(scatter, ax=ax2, label='Cycle Number')
        
        # Plot loadings for PC1
        voltage_grid = self.ml_results['voltage_grid']
        loadings = self.ml_results['loadings']
        
        ax3.plot(voltage_grid, loadings[:, 0])
        ax3.set_xlabel('Voltage (V)')
        ax3.set_ylabel('Loading')
        ax3.set_title('Loadings for Principal Component 1')
        ax3.grid(True)
        
        # Plot loadings for PC2
        ax4.plot(voltage_grid, loadings[:, 1])
        ax4.set_xlabel('Voltage (V)')
        ax4.set_ylabel('Loading')
        ax4.set_title('Loadings for Principal Component 2')
        ax4.grid(True)
    
    def _plot_random_forest_results(self):
        """Plot Random Forest results."""
        # Create subplots
        ax1 = self.fig.add_subplot(2, 1, 1)
        ax2 = self.fig.add_subplot(2, 1, 2)
        
        # Plot feature importances
        feature_importances = self.ml_results['feature_importances']
        voltage_grid = self.ml_results['voltage_grid']
        
        ax1.plot(voltage_grid, feature_importances)
        ax1.set_xlabel('Voltage (V)')
        ax1.set_ylabel('Feature Importance')
        ax1.set_title('Random Forest Feature Importances')
        ax1.grid(True)
        
        # Plot predictions vs actual
        y_test = self.ml_results['y_test']
        y_pred_test = self.ml_results['y_pred_test']
        test_r2 = self.ml_results['test_r2']
        
        ax2.scatter(y_test, y_pred_test)
        ax2.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'k--')
        ax2.set_xlabel('True Capacity (Ah)')
        ax2.set_ylabel('Predicted Capacity (Ah)')
        ax2.set_title(f'Random Forest Predictions (R² = {test_r2:.3f})')
        ax2.grid(True)
    
    def _plot_clustering_results(self):
        """Plot clustering results."""
        # Create subplot
        ax = self.fig.add_subplot(1, 1, 1)
        
        # Get PCA for visualization
        from sklearn.decomposition import PCA
        from sklearn.preprocessing import StandardScaler
        
        # Get data
        X = self.app.analyzer.data['X']
        
        # Standardize data
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Apply PCA for visualization
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)
        
        # Get labels and cycle numbers
        labels = self.ml_results['labels']
        cycle_numbers = self.ml_results['cycle_numbers']
        
        # Plot clusters
        scatter = ax.scatter(
            X_pca[:, 0],
            X_pca[:, 1],
            c=labels,
            cmap='viridis',
            s=100,
            alpha=0.8
        )
        
        # Add cycle numbers as labels
        for i, cycle in enumerate(cycle_numbers):
            ax.text(
                X_pca[i, 0],
                X_pca[i, 1],
                str(cycle),
                fontsize=10
            )
        
        ax.set_xlabel('Principal Component 1')
        ax.set_ylabel('Principal Component 2')
        ax.set_title('Clustering Results (PCA Projection)')
        ax.grid(True)
        plt.colorbar(scatter, ax=ax, label='Cluster')
    
    def _plot_neural_network_results(self):
        """Plot Neural Network results."""
        # Create subplots
        ax1 = self.fig.add_subplot(2, 1, 1)
        ax2 = self.fig.add_subplot(2, 1, 2)
        
        # Plot training history
        history = self.ml_results['history']
        epochs = range(1, len(history['loss']) + 1)
        
        ax1.plot(epochs, history['loss'], 'b-', label='Training Loss')
        ax1.plot(epochs, history['val_loss'], 'r-', label='Validation Loss')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss')
        ax1.set_title('Training and Validation Loss')
        ax1.grid(True)
        ax1.legend()
        
        # Plot predictions vs actual
        y_test = self.ml_results['y_test']
        y_pred_test = self.ml_results['y_pred_test']
        test_r2 = self.ml_results['test_r2']
        
        ax2.scatter(y_test, y_pred_test)
        ax2.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'k--')
        ax2.set_xlabel('True Capacity (Ah)')
        ax2.set_ylabel('Predicted Capacity (Ah)')
        ax2.set_title(f'Neural Network Predictions (R² = {test_r2:.3f})')
        ax2.grid(True)
    
    def _plot_svr_results(self):
        """Plot SVR results."""
        # Create subplot
        ax = self.fig.add_subplot(1, 1, 1)
        
        # Plot predictions vs actual
        y_test = self.ml_results['y_test']
        y_pred_test = self.ml_results['y_pred_test']
        test_r2 = self.ml_results['test_r2']
        
        ax.scatter(y_test, y_pred_test)
        ax.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'k--')
        ax.set_xlabel('True Capacity (Ah)')
        ax.set_ylabel('Predicted Capacity (Ah)')
        ax.set_title(f'SVR Predictions (R² = {test_r2:.3f})')
        ax.grid(True)
    
    def reset_plots(self):
        """Reset plots."""
        # Clear figure
        self.fig.clear()
        
        # Add message
        self.fig.text(0.5, 0.5, "機械学習結果がここに表示されます", 
                     ha='center', va='center', fontsize=12)
        
        # Update canvas
        self.canvas.draw()
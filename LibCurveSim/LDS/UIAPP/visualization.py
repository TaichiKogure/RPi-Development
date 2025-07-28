"""
Visualization Module

This module provides visualization functionality for the battery simulation and analysis tool.
It implements various plotting functions for simulation results, dQ/dV curves, and machine learning results.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.cm as cm
from datetime import datetime
import os


class Visualizer:
    """
    Class for visualization.
    """
    
    def __init__(self):
        """Initialize the visualizer."""
        # Set default plot style
        plt.style.use('seaborn-v0_8-darkgrid')
        
        # Set default figure size
        self.figure_size = (10, 6)
        
        # Set default DPI
        self.dpi = 100
        
        # Set default font size
        self.font_size = 10
        plt.rcParams.update({'font.size': self.font_size})
    
    def set_style(self, style='seaborn-v0_8-darkgrid'):
        """
        Set the plot style.
        
        Args:
            style: Plot style
        """
        plt.style.use(style)
    
    def set_figure_size(self, width, height):
        """
        Set the figure size.
        
        Args:
            width: Figure width in inches
            height: Figure height in inches
        """
        self.figure_size = (width, height)
    
    def set_dpi(self, dpi):
        """
        Set the DPI.
        
        Args:
            dpi: DPI
        """
        self.dpi = dpi
    
    def set_font_size(self, font_size):
        """
        Set the font size.
        
        Args:
            font_size: Font size
        """
        self.font_size = font_size
        plt.rcParams.update({'font.size': font_size})
    
    def create_figure(self, width=None, height=None, dpi=None):
        """
        Create a figure.
        
        Args:
            width: Figure width in inches (default: use instance default)
            height: Figure height in inches (default: use instance default)
            dpi: DPI (default: use instance default)
            
        Returns:
            Figure
        """
        width = width if width is not None else self.figure_size[0]
        height = height if height is not None else self.figure_size[1]
        dpi = dpi if dpi is not None else self.dpi
        
        return Figure(figsize=(width, height), dpi=dpi)
    
    def embed_figure(self, figure, frame):
        """
        Embed a figure in a Tkinter frame.
        
        Args:
            figure: Figure to embed
            frame: Tkinter frame
            
        Returns:
            Canvas
        """
        canvas = FigureCanvasTkAgg(figure, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        
        return canvas
    
    def save_figure(self, figure, filename, dpi=None):
        """
        Save a figure to a file.
        
        Args:
            figure: Figure to save
            filename: Filename
            dpi: DPI (default: use instance default)
        """
        dpi = dpi if dpi is not None else self.dpi
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
        
        figure.savefig(filename, dpi=dpi, bbox_inches='tight')
    
    def plot_charge_curves(self, results, cycles=None, figure=None, ax=None, smoothing=None):
        """
        Plot charge curves.
        
        Args:
            results: Simulation results
            cycles: List of cycles to plot (default: all cycles)
            figure: Figure to plot on (default: create new figure)
            ax: Axes to plot on (default: create new axes)
            smoothing: Smoothing parameter (default: no smoothing)
            
        Returns:
            Figure, Axes
        """
        if figure is None:
            figure = self.create_figure()
        
        if ax is None:
            ax = figure.add_subplot(111)
        
        # Filter cycles if specified
        if cycles is not None:
            results = [result for result in results if result['cycle'] in cycles]
        
        # Plot charge curves
        for result in results:
            cycle = result['cycle']
            capacity = result['charge']['capacity']
            voltage = result['charge']['voltage']
            
            if smoothing is not None:
                # Use the smooth_curve method from simulation_core
                from simulation_core import SimulationCore
                sim_core = SimulationCore()
                capacity, voltage = sim_core.smooth_curve(capacity, voltage, smoothing)
            
            ax.plot(capacity, voltage, label=f"Cycle {cycle}")
        
        ax.set_xlabel('Capacity (Ah)')
        ax.set_ylabel('Voltage (V)')
        ax.set_title('Charge Curves')
        ax.grid(True)
        ax.legend()
        
        return figure, ax
    
    def plot_discharge_curves(self, results, cycles=None, figure=None, ax=None, smoothing=None):
        """
        Plot discharge curves.
        
        Args:
            results: Simulation results
            cycles: List of cycles to plot (default: all cycles)
            figure: Figure to plot on (default: create new figure)
            ax: Axes to plot on (default: create new axes)
            smoothing: Smoothing parameter (default: no smoothing)
            
        Returns:
            Figure, Axes
        """
        if figure is None:
            figure = self.create_figure()
        
        if ax is None:
            ax = figure.add_subplot(111)
        
        # Filter cycles if specified
        if cycles is not None:
            results = [result for result in results if result['cycle'] in cycles]
        
        # Plot discharge curves
        for result in results:
            cycle = result['cycle']
            capacity = result['discharge']['capacity']
            voltage = result['discharge']['voltage']
            
            if smoothing is not None:
                # Use the smooth_curve method from simulation_core
                from simulation_core import SimulationCore
                sim_core = SimulationCore()
                capacity, voltage = sim_core.smooth_curve(capacity, voltage, smoothing)
            
            ax.plot(capacity, voltage, label=f"Cycle {cycle}")
        
        ax.set_xlabel('Capacity (Ah)')
        ax.set_ylabel('Voltage (V)')
        ax.set_title('Discharge Curves')
        ax.grid(True)
        ax.legend()
        
        return figure, ax
    
    def plot_capacity_retention(self, results, figure=None, ax=None):
        """
        Plot capacity retention.
        
        Args:
            results: Simulation results
            figure: Figure to plot on (default: create new figure)
            ax: Axes to plot on (default: create new axes)
            
        Returns:
            Figure, Axes
        """
        if figure is None:
            figure = self.create_figure()
        
        if ax is None:
            ax = figure.add_subplot(111)
        
        # Extract cycle numbers and capacity retention
        cycles = [result['cycle'] for result in results]
        capacity_retention = [result['capacity_retention'] for result in results]
        
        # Plot capacity retention
        ax.plot(cycles, capacity_retention, 'o-')
        
        ax.set_xlabel('Cycle')
        ax.set_ylabel('Capacity Retention')
        ax.set_title('Capacity Retention vs Cycle')
        ax.grid(True)
        
        return figure, ax
    
    def plot_dqdv_curves(self, dqdv_data, cycles=None, figure=None, ax=None):
        """
        Plot dQ/dV curves.
        
        Args:
            dqdv_data: dQ/dV data
            cycles: List of cycles to plot (default: all cycles)
            figure: Figure to plot on (default: create new figure)
            ax: Axes to plot on (default: create new axes)
            
        Returns:
            Figure, Axes
        """
        if figure is None:
            figure = self.create_figure()
        
        if ax is None:
            ax = figure.add_subplot(111)
        
        # Filter cycles if specified
        if cycles is not None:
            dqdv_data = {cycle: data for cycle, data in dqdv_data.items() if cycle in cycles}
        
        # Plot dQ/dV curves
        for cycle, data in dqdv_data.items():
            ax.plot(data['voltage'], data['dqdv'], label=f"Cycle {cycle}")
        
        ax.set_xlabel('Voltage (V)')
        ax.set_ylabel('dQ/dV (Ah/V)')
        ax.set_title('dQ/dV Curves')
        ax.grid(True)
        ax.legend()
        
        return figure, ax
    
    def plot_peaks(self, peak_data, cycles=None, figure=None, ax=None):
        """
        Plot peaks in dQ/dV curves.
        
        Args:
            peak_data: Peak data
            cycles: List of cycles to plot (default: all cycles)
            figure: Figure to plot on (default: create new figure)
            ax: Axes to plot on (default: create new axes)
            
        Returns:
            Figure, Axes
        """
        if figure is None:
            figure = self.create_figure()
        
        if ax is None:
            ax = figure.add_subplot(111)
        
        # Filter cycles if specified
        if cycles is not None:
            peak_data = {cycle: data for cycle, data in peak_data.items() if cycle in cycles}
        
        # Plot peaks
        for cycle, data in peak_data.items():
            if len(data['peak_voltages']) > 0:
                ax.plot(data['peak_voltages'], data['peak_dqdvs'], 'o', label=f"Cycle {cycle}")
        
        ax.set_xlabel('Voltage (V)')
        ax.set_ylabel('dQ/dV (Ah/V)')
        ax.set_title('Detected Peaks')
        ax.grid(True)
        ax.legend()
        
        return figure, ax
    
    def plot_pca_results(self, pca_results, figure=None, ax=None, color_by=None):
        """
        Plot PCA results.
        
        Args:
            pca_results: PCA results
            figure: Figure to plot on (default: create new figure)
            ax: Axes to plot on (default: create new axes)
            color_by: Values to color points by (default: None)
            
        Returns:
            Figure, Axes
        """
        if figure is None:
            figure = self.create_figure()
        
        if ax is None:
            ax = figure.add_subplot(111)
        
        # Extract principal components
        pc1 = pca_results['principal_components'][:, 0]
        pc2 = pca_results['principal_components'][:, 1]
        
        # Plot principal components
        if color_by is not None:
            scatter = ax.scatter(pc1, pc2, c=color_by, cmap='viridis')
            plt.colorbar(scatter, ax=ax, label='Cycle')
        else:
            ax.scatter(pc1, pc2)
        
        ax.set_xlabel('PC1')
        ax.set_ylabel('PC2')
        ax.set_title('PCA Results')
        ax.grid(True)
        
        return figure, ax
    
    def plot_explained_variance(self, pca_results, figure=None, ax=None):
        """
        Plot explained variance from PCA.
        
        Args:
            pca_results: PCA results
            figure: Figure to plot on (default: create new figure)
            ax: Axes to plot on (default: create new axes)
            
        Returns:
            Figure, Axes
        """
        if figure is None:
            figure = self.create_figure()
        
        if ax is None:
            ax = figure.add_subplot(111)
        
        # Extract explained variance ratio
        explained_variance_ratio = pca_results['explained_variance_ratio']
        
        # Calculate cumulative explained variance
        cumulative_explained_variance = np.cumsum(explained_variance_ratio)
        
        # Plot explained variance
        ax.bar(range(1, len(explained_variance_ratio) + 1), explained_variance_ratio, alpha=0.7, label='Individual')
        ax.step(range(1, len(cumulative_explained_variance) + 1), cumulative_explained_variance, where='mid', label='Cumulative')
        
        ax.set_xlabel('Principal Component')
        ax.set_ylabel('Explained Variance Ratio')
        ax.set_title('Explained Variance')
        ax.grid(True)
        ax.legend()
        
        return figure, ax
    
    def plot_loadings(self, pca_results, voltage_grid, figure=None, ax=None):
        """
        Plot PCA loadings.
        
        Args:
            pca_results: PCA results
            voltage_grid: Voltage grid
            figure: Figure to plot on (default: create new figure)
            ax: Axes to plot on (default: create new axes)
            
        Returns:
            Figure, Axes
        """
        if figure is None:
            figure = self.create_figure()
        
        if ax is None:
            ax = figure.add_subplot(111)
        
        # Extract loadings
        loadings = pca_results['loadings']
        
        # Plot loadings
        for i in range(min(3, loadings.shape[1])):
            ax.plot(voltage_grid, loadings[:, i], label=f"PC{i+1}")
        
        ax.set_xlabel('Voltage (V)')
        ax.set_ylabel('Loading')
        ax.set_title('PCA Loadings')
        ax.grid(True)
        ax.legend()
        
        return figure, ax
    
    def plot_regression_results(self, ml_results, figure=None, ax=None):
        """
        Plot regression results.
        
        Args:
            ml_results: Machine learning results
            figure: Figure to plot on (default: create new figure)
            ax: Axes to plot on (default: create new axes)
            
        Returns:
            Figure, Axes
        """
        if figure is None:
            figure = self.create_figure()
        
        if ax is None:
            ax = figure.add_subplot(111)
        
        # Extract true and predicted values
        y_test = ml_results['y_test']
        y_pred_test = ml_results['y_pred_test']
        
        # Calculate metrics
        test_mse = ml_results['test_mse']
        test_mae = ml_results['test_mae']
        test_r2 = ml_results['test_r2']
        
        # Plot true vs predicted values
        ax.scatter(y_test, y_pred_test)
        
        # Plot diagonal line
        min_val = min(min(y_test), min(y_pred_test))
        max_val = max(max(y_test), max(y_pred_test))
        ax.plot([min_val, max_val], [min_val, max_val], 'k--')
        
        ax.set_xlabel('True Value')
        ax.set_ylabel('Predicted Value')
        ax.set_title(f"Regression Results (R² = {test_r2:.4f})")
        ax.grid(True)
        
        # Add metrics as text
        ax.text(0.05, 0.95, f"MSE: {test_mse:.4f}\nMAE: {test_mae:.4f}\nR²: {test_r2:.4f}",
                transform=ax.transAxes, verticalalignment='top')
        
        return figure, ax
    
    def plot_residuals(self, ml_results, figure=None, ax=None):
        """
        Plot residuals from regression.
        
        Args:
            ml_results: Machine learning results
            figure: Figure to plot on (default: create new figure)
            ax: Axes to plot on (default: create new axes)
            
        Returns:
            Figure, Axes
        """
        if figure is None:
            figure = self.create_figure()
        
        if ax is None:
            ax = figure.add_subplot(111)
        
        # Extract true and predicted values
        y_test = ml_results['y_test']
        y_pred_test = ml_results['y_pred_test']
        
        # Calculate residuals
        residuals = y_test - y_pred_test
        
        # Plot residuals
        ax.scatter(y_pred_test, residuals)
        
        # Plot horizontal line at y=0
        ax.axhline(y=0, color='k', linestyle='--')
        
        ax.set_xlabel('Predicted Value')
        ax.set_ylabel('Residual')
        ax.set_title('Residuals')
        ax.grid(True)
        
        return figure, ax
    
    def plot_feature_importance(self, ml_results, voltage_grid, figure=None, ax=None):
        """
        Plot feature importance from Random Forest.
        
        Args:
            ml_results: Machine learning results
            voltage_grid: Voltage grid
            figure: Figure to plot on (default: create new figure)
            ax: Axes to plot on (default: create new axes)
            
        Returns:
            Figure, Axes
        """
        if figure is None:
            figure = self.create_figure()
        
        if ax is None:
            ax = figure.add_subplot(111)
        
        # Extract feature importance
        feature_importances = ml_results['feature_importances']
        
        # Plot feature importance
        ax.plot(voltage_grid, feature_importances)
        
        ax.set_xlabel('Voltage (V)')
        ax.set_ylabel('Feature Importance')
        ax.set_title('Feature Importance')
        ax.grid(True)
        
        return figure, ax
    
    def plot_clustering_results(self, clustering_results, pca_results=None, figure=None, ax=None):
        """
        Plot clustering results.
        
        Args:
            clustering_results: Clustering results
            pca_results: PCA results (default: None)
            figure: Figure to plot on (default: create new figure)
            ax: Axes to plot on (default: create new axes)
            
        Returns:
            Figure, Axes
        """
        if figure is None:
            figure = self.create_figure()
        
        if ax is None:
            ax = figure.add_subplot(111)
        
        # Extract cluster labels
        labels = clustering_results['labels']
        
        # Plot clustering results
        if pca_results is not None:
            # Use PCA results for visualization
            pc1 = pca_results['principal_components'][:, 0]
            pc2 = pca_results['principal_components'][:, 1]
            
            scatter = ax.scatter(pc1, pc2, c=labels, cmap='tab10')
            
            ax.set_xlabel('PC1')
            ax.set_ylabel('PC2')
        else:
            # Just plot labels
            scatter = ax.scatter(range(len(labels)), labels, c=labels, cmap='tab10')
            
            ax.set_xlabel('Sample Index')
            ax.set_ylabel('Cluster')
        
        ax.set_title('Clustering Results')
        ax.grid(True)
        
        # Add legend
        legend1 = ax.legend(*scatter.legend_elements(),
                            loc="upper right", title="Clusters")
        ax.add_artist(legend1)
        
        return figure, ax
    
    def plot_learning_curves(self, history, figure=None, ax=None):
        """
        Plot learning curves from neural network training.
        
        Args:
            history: Training history
            figure: Figure to plot on (default: create new figure)
            ax: Axes to plot on (default: create new axes)
            
        Returns:
            Figure, Axes tuple
        """
        if figure is None:
            figure = self.create_figure()
        
        if ax is None:
            ax1 = figure.add_subplot(121)
            ax2 = figure.add_subplot(122)
        else:
            ax1, ax2 = ax
        
        # Extract history
        history_dict = history.history
        
        # Plot loss
        ax1.plot(history_dict['loss'], label='Training')
        ax1.plot(history_dict['val_loss'], label='Validation')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss')
        ax1.set_title('Loss')
        ax1.grid(True)
        ax1.legend()
        
        # Plot MAE
        ax2.plot(history_dict['mae'], label='Training')
        ax2.plot(history_dict['val_mae'], label='Validation')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('MAE')
        ax2.set_title('Mean Absolute Error')
        ax2.grid(True)
        ax2.legend()
        
        figure.tight_layout()
        
        return figure, (ax1, ax2)
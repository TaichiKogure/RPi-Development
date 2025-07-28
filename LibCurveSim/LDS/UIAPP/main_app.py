"""
Main Application Module

This module provides the main application for the battery simulation and analysis tool.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys

# Add the parent directory to the path to import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the tab modules
from simulation_tab import SimulationTab
from analysis_tab import AnalysisTab
from ml_tab import MLTab
from data_export_tab import DataExportTab


class BatterySimApp:
    """
    Main application class for the battery simulation and analysis tool.
    """
    
    def __init__(self, root):
        """
        Initialize the application.
        
        Args:
            root: Root window
        """
        self.root = root
        self.root.title("リチウムイオン電池シミュレーション・解析ツール")
        self.root.geometry("1200x800")
        
        # Set up the main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create the notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Initialize data storage
        self.simulation_results = None
        
        # Create the tabs
        self.create_tabs()
        
        # Set up the status bar
        self.status_var = tk.StringVar(value="準備完了")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind events
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def create_tabs(self):
        """Create the tabs for the application."""
        # Simulation tab
        self.simulation_tab = SimulationTab(self.notebook, self)
        self.notebook.add(self.simulation_tab.frame, text="シミュレーション")
        
        # Analysis tab
        self.analysis_tab = AnalysisTab(self.notebook, self)
        self.notebook.add(self.analysis_tab.frame, text="解析")
        
        # Machine Learning tab
        self.ml_tab = MLTab(self.notebook, self)
        self.notebook.add(self.ml_tab.frame, text="機械学習")
        
        # Data Export tab
        self.data_export_tab = DataExportTab(self.notebook, self)
        self.notebook.add(self.data_export_tab.frame, text="データエクスポート")
    
    def on_tab_changed(self, event):
        """
        Handle tab changed event.
        
        Args:
            event: Event that triggered the tab change
        """
        tab_id = self.notebook.select()
        tab_name = self.notebook.tab(tab_id, "text")
        
        # Update status bar
        self.status_var.set(f"タブ: {tab_name}")
        
        # Update data in tabs
        if tab_name == "解析" and self.simulation_results is not None:
            self.analysis_tab.update_available_data(simulation_results=self.simulation_results)
        elif tab_name == "機械学習" and hasattr(self.analysis_tab, 'dqdv_data') and self.analysis_tab.dqdv_data is not None:
            self.ml_tab.update_available_data(
                dqdv_data=self.analysis_tab.dqdv_data,
                peak_data=getattr(self.analysis_tab, 'peak_data', None)
            )
        elif tab_name == "データエクスポート":
            self.data_export_tab.update_available_data(
                simulation_results=self.simulation_results,
                dqdv_data=getattr(self.analysis_tab, 'dqdv_data', None),
                peak_data=getattr(self.analysis_tab, 'peak_data', None),
                ml_results=getattr(self.ml_tab, 'ml_results', None)
            )
    
    def update_status(self, message):
        """
        Update the status bar message.
        
        Args:
            message: Message to display
        """
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def show_error(self, title, message):
        """
        Show an error message.
        
        Args:
            title: Error title
            message: Error message
        """
        messagebox.showerror(title, message)
    
    def show_info(self, title, message):
        """
        Show an information message.
        
        Args:
            title: Information title
            message: Information message
        """
        messagebox.showinfo(title, message)
    
    def show_warning(self, title, message):
        """
        Show a warning message.
        
        Args:
            title: Warning title
            message: Warning message
        """
        messagebox.showwarning(title, message)


def main():
    """Main function to run the application."""
    root = tk.Tk()
    app = BatterySimApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
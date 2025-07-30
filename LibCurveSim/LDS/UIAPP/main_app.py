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

# BatterySimulator クラスを追加でインポート
try:
    from simulation_core import BatterySimulator
except ImportError:
    # 最低限のダミークラス（本来はsimulation_core.pyに用意）
    class BatterySimulator:
        def __init__(self, initial_capacity=2.5, initial_resistance=0.05):
            self.initial_capacity = initial_capacity
            self.initial_resistance = initial_resistance

            # 必要なデフォルトパラメータを追加
            self.capacity_fade_A = 1e-6
            self.capacity_fade_B = 0.1
            self.resistance_growth_C = 2e-5
            self.resistance_growth_D = 0.5
            
            # シミュレーションパラメータ（simulation_tab.pyで必要）
            self.c_rate = 1.0  # C-rate (1C = 1時間で満充電)
            self.v_max = 4.2   # 最大電圧 (V) - リチウムイオン電池の一般的な値
            self.v_min = 2.5   # 最小電圧 (V) - リチウムイオン電池の一般的な値
            self.end_current_ratio = 0.05  # 終止電流比 (5%)
            self.dt = 1.0      # 時間ステップ (秒)

        def set_battery_parameters(self, capacity, resistance):
            """Set battery parameters."""
            self.initial_capacity = capacity
            self.initial_resistance = resistance

        def set_degradation_parameters(self, capacity_fade_A, capacity_fade_B, 
                                     resistance_growth_C, resistance_growth_D):
            """Set degradation parameters."""
            self.capacity_fade_A = capacity_fade_A
            self.capacity_fade_B = capacity_fade_B
            self.resistance_growth_C = resistance_growth_C
            self.resistance_growth_D = resistance_growth_D

        def set_simulation_parameters(self, c_rate, v_max, v_min, end_current_ratio, dt):
            """Set simulation parameters."""
            self.c_rate = c_rate
            self.v_max = v_max
            self.v_min = v_min
            self.end_current_ratio = end_current_ratio
            self.dt = dt

        def run_all_cycles(self, num_cycles):
            """Run simulation for all cycles (dummy implementation)."""
            # This is a dummy implementation - replace with actual simulation logic
            import numpy as np
            results = {
                'cycles': list(range(1, num_cycles + 1)),
                'capacity': [self.initial_capacity * (1 - 0.01 * i) for i in range(num_cycles)],
                'resistance': [self.initial_resistance * (1 + 0.005 * i) for i in range(num_cycles)],
                'voltage': [np.linspace(self.v_min, self.v_max, 100) for _ in range(num_cycles)],
                'current': [np.ones(100) * self.c_rate for _ in range(num_cycles)]
            }
            return results

        def calculate_capacity_retention(self, results):
            """Calculate capacity retention from results."""
            if not results or 'capacity' not in results:
                return []
            initial_capacity = results['capacity'][0] if results['capacity'] else self.initial_capacity
            return [cap / initial_capacity * 100 for cap in results['capacity']]


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

        # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        # simulatorオブジェクト（初期パラメータ）を生成して保持
        self.simulator = BatterySimulator(initial_capacity=2.5, initial_resistance=0.05)
        # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

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
        elif tab_name == "機械学習" and hasattr(self.analysis_tab,
                                                'dqdv_data') and self.analysis_tab.dqdv_data is not None:
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

    def run_in_background(self, status_message, work_function):
        """
        Run a function in the background thread while updating the status bar.
        
        This method is used by tab modules to execute long-running operations
        (like simulations, data loading, ML analysis) without blocking the UI.
        
        Args:
            status_message (str): Message to display in the status bar during execution
            work_function (callable): Function to execute in the background thread
        """
        import threading
        
        def background_worker():
            """Worker function that runs in the background thread."""
            try:
                # Update status bar to show operation is in progress
                if hasattr(self, 'root') and self.root:
                    self.root.after(0, lambda: self.update_status(status_message))
                
                # Execute the work function
                work_function()
                
                # Reset status bar when done
                if hasattr(self, 'root') and self.root:
                    self.root.after(0, lambda: self.update_status("準備完了"))
                
            except Exception as e:
                # Handle any errors that occur during background execution
                error_message = f"バックグラウンド処理中にエラーが発生しました: {str(e)}"
                if hasattr(self, 'root') and self.root:
                    self.root.after(0, lambda: self.update_status("エラーが発生しました"))
                    self.root.after(0, lambda error_message=error_message: self.show_error("エラー", error_message))
                else:
                    # Fallback for testing or when root is not available
                    print(f"Background error: {error_message}")
        
        # Start the background thread
        thread = threading.Thread(target=background_worker, daemon=True)
        thread.start()


def main():
    """Main function to run the application."""
    root = tk.Tk()
    app = BatterySimApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
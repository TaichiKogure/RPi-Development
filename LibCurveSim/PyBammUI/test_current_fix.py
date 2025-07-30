#!/usr/bin/env python3
"""
Test script for the "int object is not iterable" fix in AdvancedVariablesTab.
This script tests various scenarios to ensure the fix works correctly.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk

# Mock the advanced_variables_tab module for testing
class MockAdvancedVariablesTab:
    """Mock class to test the plotting fix without full PyBamm setup."""
    
    def __init__(self):
        # Create a simple test window
        self.root = tk.Tk()
        self.root.title("Current Fix Test")
        self.root.geometry("800x600")
        
        # Create matplotlib figure
        self.fig = plt.figure(figsize=(10, 6))
        self.ax = self.fig.add_subplot(1, 1, 1)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, self.root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Test data scenarios
        self.test_scenarios = {
            "scalar_int": {
                "description": "スカラー整数値（元のエラーケース）",
                "time": np.linspace(0, 3600, 100),
                "data": 5  # This would cause "int object is not iterable"
            },
            "scalar_float": {
                "description": "スカラー浮動小数点値",
                "time": np.linspace(0, 3600, 100),
                "data": 5.5
            },
            "single_element_array": {
                "description": "単一要素配列",
                "time": np.linspace(0, 3600, 100),
                "data": np.array([5.0])
            },
            "normal_array": {
                "description": "正常な配列データ",
                "time": np.linspace(0, 3600, 100),
                "data": None  # Will be generated
            },
            "wrong_length_array": {
                "description": "長さが異なる配列",
                "time": np.linspace(0, 3600, 100),
                "data": np.array([1, 2, 3, 4, 5])  # Wrong length
            }
        }
        
        # Generate normal array data
        time_data = self.test_scenarios["normal_array"]["time"]
        self.test_scenarios["normal_array"]["data"] = 4.2 - (4.2 - 3.0) * (time_data / 3600)
        
        # Create test buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        for scenario_name, scenario_data in self.test_scenarios.items():
            btn = ttk.Button(
                button_frame, 
                text=f"テスト: {scenario_data['description']}", 
                command=lambda name=scenario_name: self.test_scenario(name)
            )
            btn.pack(side=tk.LEFT, padx=2)
        
        # Clear button
        ttk.Button(button_frame, text="クリア", command=self.clear_plot).pack(side=tk.RIGHT, padx=2)
        
        # Status label
        self.status_label = ttk.Label(self.root, text="テストシナリオを選択してください")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
    
    def test_scenario(self, scenario_name):
        """Test a specific scenario."""
        scenario = self.test_scenarios[scenario_name]
        self.status_label.config(text=f"テスト中: {scenario['description']}")
        
        # Mock simulation results
        self.simulation_results = {
            'time': scenario['time'],
            'Current [A]': scenario['data']
        }
        
        # Test the fixed update_plot method
        try:
            self.update_plot_fixed('Current [A]')
            self.status_label.config(text=f"✓ 成功: {scenario['description']}")
        except Exception as e:
            self.status_label.config(text=f"✗ エラー: {str(e)}")
            print(f"Error in scenario '{scenario_name}': {e}")
    
    def update_plot_fixed(self, plot_var):
        """Fixed version of update_plot method from AdvancedVariablesTab."""
        if not self.simulation_results:
            return
            
        if plot_var not in self.simulation_results:
            raise ValueError(f"変数 '{plot_var}' がシミュレーション結果に含まれていません。")
            
        # Clear previous plot
        self.ax.clear()
        
        # Plot data
        time_data = self.simulation_results['time']
        var_data = self.simulation_results[plot_var]
        
        # Handle case where var_data might be a scalar value (fix for "int object is not iterable" error)
        try:
            # Check if var_data is iterable and has the same length as time_data
            if hasattr(var_data, '__iter__') and not isinstance(var_data, str):
                # var_data is iterable (array-like)
                if len(var_data) == len(time_data):
                    self.ax.plot(time_data, var_data, 'b-', linewidth=2, label=plot_var)
                else:
                    # Length mismatch - create constant array
                    if len(var_data) == 1:
                        # Single value array - broadcast to match time_data length
                        constant_value = var_data[0] if hasattr(var_data, '__getitem__') else float(var_data)
                        var_data_expanded = np.full_like(time_data, constant_value)
                        self.ax.plot(time_data, var_data_expanded, 'b-', linewidth=2, label=f"{plot_var} (定数値: {constant_value})")
                    else:
                        # Multiple values but wrong length - show error
                        raise ValueError(f"変数 '{plot_var}' のデータ長 ({len(var_data)}) が時間データ長 ({len(time_data)}) と一致しません。")
            else:
                # var_data is a scalar value - create constant array
                try:
                    scalar_value = float(var_data)
                    var_data_expanded = np.full_like(time_data, scalar_value)
                    self.ax.plot(time_data, var_data_expanded, 'b-', linewidth=2, label=f"{plot_var} (定数値: {scalar_value})")
                except (ValueError, TypeError):
                    raise ValueError(f"変数 '{plot_var}' のデータを数値に変換できません: {var_data}")
                    
        except Exception as e:
            raise Exception(f"プロット中にエラーが発生しました: {str(e)}\n変数: {plot_var}\nデータ型: {type(var_data)}")
        
        # Set labels and title
        self.ax.set_xlabel("時間 [s]")
        self.ax.set_ylabel(plot_var)
        self.ax.set_title(f"修正版プロットテスト\n変数: {plot_var}")
        self.ax.grid(True, alpha=0.3)
        self.ax.legend()
        
        # Refresh canvas
        self.canvas.draw()
    
    def clear_plot(self):
        """Clear the plot."""
        self.ax.clear()
        self.ax.set_title("プロットテスト")
        self.ax.set_xlabel("時間 [s]")
        self.ax.set_ylabel("値")
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()
        self.status_label.config(text="プロットをクリアしました")
    
    def run(self):
        """Run the test application."""
        print("Current Fix Test - 電流A設定時のエラー修正テスト")
        print("=" * 50)
        print("このテストは「int object is not iterable」エラーの修正を検証します。")
        print("各ボタンをクリックして異なるデータ型でのプロット動作を確認してください。")
        print("=" * 50)
        self.root.mainloop()

def test_without_gui():
    """Test the fix without GUI (for automated testing)."""
    print("Current Fix Test - 自動テスト")
    print("=" * 40)
    
    # Test scenarios
    test_cases = [
        ("スカラー整数", 5),
        ("スカラー浮動小数点", 5.5),
        ("単一要素配列", np.array([5.0])),
        ("正常な配列", np.linspace(4.2, 3.0, 100))
    ]
    
    time_data = np.linspace(0, 3600, 100)
    
    for test_name, var_data in test_cases:
        try:
            # Test the core logic without matplotlib
            if hasattr(var_data, '__iter__') and not isinstance(var_data, str):
                if len(var_data) == len(time_data):
                    result = "配列データとして正常処理"
                elif len(var_data) == 1:
                    constant_value = var_data[0] if hasattr(var_data, '__getitem__') else float(var_data)
                    result = f"定数値として処理: {constant_value}"
                else:
                    result = f"長さ不一致エラー: {len(var_data)} vs {len(time_data)}"
            else:
                scalar_value = float(var_data)
                result = f"スカラー値として処理: {scalar_value}"
            
            print(f"✓ {test_name}: {result}")
            
        except Exception as e:
            print(f"✗ {test_name}: エラー - {str(e)}")
    
    print("=" * 40)
    print("自動テスト完了")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--no-gui":
        test_without_gui()
    else:
        app = MockAdvancedVariablesTab()
        app.run()
#!/usr/bin/env python3
"""
Test script for voltage components plotting functionality
電圧成分プロット機能のテストスクリプト
"""

import sys
import os
import tkinter as tk
from tkinter import ttk

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main application
from main_app import PyBammApp, PyBammSimulator

def test_voltage_components_functionality():
    """Test the voltage components plotting functionality."""
    print("Testing voltage components plotting functionality...")
    print("電圧成分プロット機能をテストしています...")
    
    # Create a test simulator
    simulator = PyBammSimulator()
    
    # Set test parameters
    simulator.set_parameters(
        capacity=2.5,
        current=1.0,
        v_min=3.0,
        v_max=4.2,
        temperature=298.15
    )
    
    # Run simulation (will use mock data)
    print("Running simulation...")
    print("シミュレーションを実行中...")
    results = simulator.run_simulation(time_hours=1.0, model_type='DFN')
    
    # Check if voltage components are present
    if 'voltage_components' in results:
        print("✓ Voltage components data found in simulation results")
        print("✓ シミュレーション結果に電圧成分データが見つかりました")
        
        components = results['voltage_components']
        print(f"  Available components: {list(components.keys())}")
        print(f"  利用可能な成分: {list(components.keys())}")
        
        # Check data integrity
        time_points = len(results['time'])
        for component, data in components.items():
            if len(data) != time_points:
                print(f"✗ Data length mismatch for {component}: {len(data)} vs {time_points}")
                print(f"✗ {component}のデータ長が不一致: {len(data)} vs {time_points}")
                return False
        
        print("✓ All voltage component data has correct length")
        print("✓ すべての電圧成分データの長さが正しいです")
        
    else:
        print("✗ Voltage components data not found in simulation results")
        print("✗ シミュレーション結果に電圧成分データが見つかりません")
        return False
    
    return True

def test_ui_integration():
    """Test UI integration with voltage components plotting."""
    print("\nTesting UI integration...")
    print("UI統合をテストしています...")
    
    try:
        # Create root window
        root = tk.Tk()
        root.withdraw()  # Hide the window for testing
        
        # Create app instance
        app = PyBammApp(root)
        
        # Check if simulation tab has the new methods
        sim_tab = app.simulation_tab
        
        if hasattr(sim_tab, 'plot_voltage_components'):
            print("✓ plot_voltage_components method found in SimulationTab")
            print("✓ SimulationTabにplot_voltage_componentsメソッドが見つかりました")
        else:
            print("✗ plot_voltage_components method not found")
            print("✗ plot_voltage_componentsメソッドが見つかりません")
            return False
        
        if hasattr(sim_tab, '_plot_voltage_components'):
            print("✓ _plot_voltage_components method found in SimulationTab")
            print("✓ SimulationTabに_plot_voltage_componentsメソッドが見つかりました")
        else:
            print("✗ _plot_voltage_components method not found")
            print("✗ _plot_voltage_componentsメソッドが見つかりません")
            return False
        
        # Check if plot type options include voltage components
        plot_combo = None
        for widget in sim_tab.plot_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Combobox):
                        plot_combo = child
                        break
        
        if plot_combo:
            values = plot_combo['values']
            if 'voltage_components' in values and 'voltage_components_split' in values:
                print("✓ Voltage components options found in plot type dropdown")
                print("✓ プロットタイプドロップダウンに電圧成分オプションが見つかりました")
            else:
                print("✗ Voltage components options not found in dropdown")
                print("✗ ドロップダウンに電圧成分オプションが見つかりません")
                print(f"  Available options: {values}")
                print(f"  利用可能なオプション: {values}")
                return False
        else:
            print("✗ Plot type dropdown not found")
            print("✗ プロットタイプドロップダウンが見つかりません")
            return False
        
        # Clean up
        root.destroy()
        
    except Exception as e:
        print(f"✗ UI integration test failed: {e}")
        print(f"✗ UI統合テストが失敗しました: {e}")
        return False
    
    return True

def test_plotting_functionality():
    """Test the actual plotting functionality."""
    print("\nTesting plotting functionality...")
    print("プロット機能をテストしています...")
    
    try:
        # Create root window
        root = tk.Tk()
        root.withdraw()  # Hide the window for testing
        
        # Create app instance
        app = PyBammApp(root)
        sim_tab = app.simulation_tab
        
        # Run a simulation to get test data
        app.simulator.set_parameters(capacity=2.5, current=1.0, temperature=298.15)
        results = app.simulator.run_simulation(time_hours=0.5, model_type='DFN')
        app.simulation_results = results
        
        # Test basic voltage components plotting
        try:
            sim_tab.plot_voltage_components(split_by_electrode=False)
            print("✓ Basic voltage components plotting works")
            print("✓ 基本電圧成分プロットが動作します")
        except Exception as e:
            print(f"✗ Basic voltage components plotting failed: {e}")
            print(f"✗ 基本電圧成分プロットが失敗しました: {e}")
            return False
        
        # Test electrode-split voltage components plotting
        try:
            sim_tab.plot_voltage_components(split_by_electrode=True)
            print("✓ Electrode-split voltage components plotting works")
            print("✓ 電極別電圧成分プロットが動作します")
        except Exception as e:
            print(f"✗ Electrode-split voltage components plotting failed: {e}")
            print(f"✗ 電極別電圧成分プロットが失敗しました: {e}")
            return False
        
        # Clean up
        root.destroy()
        
    except Exception as e:
        print(f"✗ Plotting functionality test failed: {e}")
        print(f"✗ プロット機能テストが失敗しました: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("Voltage Components Plotting Functionality Test")
    print("電圧成分プロット機能テスト")
    print("=" * 60)
    
    tests = [
        ("Simulation Data Test", "シミュレーションデータテスト", test_voltage_components_functionality),
        ("UI Integration Test", "UI統合テスト", test_ui_integration),
        ("Plotting Functionality Test", "プロット機能テスト", test_plotting_functionality)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name_en, test_name_jp, test_func in tests:
        print(f"\n{test_name_en} / {test_name_jp}")
        print("-" * 40)
        
        try:
            if test_func():
                print(f"✓ {test_name_en} PASSED")
                print(f"✓ {test_name_jp} 合格")
                passed += 1
            else:
                print(f"✗ {test_name_en} FAILED")
                print(f"✗ {test_name_jp} 失敗")
        except Exception as e:
            print(f"✗ {test_name_en} ERROR: {e}")
            print(f"✗ {test_name_jp} エラー: {e}")
    
    print("\n" + "=" * 60)
    print(f"Test Results / テスト結果: {passed}/{total} tests passed")
    print(f"テスト結果: {passed}/{total} テストが合格")
    
    if passed == total:
        print("✓ All tests passed! Voltage components functionality is working correctly.")
        print("✓ すべてのテストが合格しました！電圧成分機能は正常に動作しています。")
        return True
    else:
        print("✗ Some tests failed. Please check the implementation.")
        print("✗ 一部のテストが失敗しました。実装を確認してください。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
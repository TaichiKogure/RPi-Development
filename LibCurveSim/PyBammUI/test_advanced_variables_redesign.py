#!/usr/bin/env python3
"""
Test script for the redesigned Advanced Variables Tab
Tests parameter preset functionality and simple simulation execution.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main application and redesigned tab
from main_app import PyBammApp
from advanced_variables_tab import AdvancedVariablesTab

def test_parameter_presets():
    """Test parameter preset functionality."""
    print("Testing parameter preset functionality...")
    print("パラメータプリセット機能をテストしています...")
    
    # Create a test root window
    root = tk.Tk()
    root.withdraw()  # Hide the window for testing
    
    try:
        # Create a mock app instance
        class MockApp:
            def __init__(self, root):
                self.root = root
                
            def run_in_background(self, message, func):
                """Mock background execution."""
                print(f"Background task: {message}")
                func()
        
        app = MockApp(root)
        
        # Create the advanced variables tab
        notebook = ttk.Notebook(root)
        adv_tab = AdvancedVariablesTab(notebook, app)
        
        # Test preset availability
        presets = adv_tab.get_available_presets()
        if presets:
            print(f"✓ Available presets found: {presets}")
            print(f"✓ 利用可能なプリセットが見つかりました: {presets}")
        else:
            print("✗ No presets available")
            print("✗ 利用可能なプリセットがありません")
            return False
        
        # Test preset loading
        for preset in presets[:2]:  # Test first 2 presets
            print(f"\nTesting preset: {preset}")
            print(f"プリセットをテスト中: {preset}")
            
            adv_tab.preset_var.set(preset)
            try:
                adv_tab.load_parameter_preset()
                
                if adv_tab.current_parameter_values is not None:
                    print(f"✓ Preset '{preset}' loaded successfully")
                    print(f"✓ プリセット '{preset}' の読み込みに成功しました")
                    
                    # Test parameter display
                    adv_tab.display_parameter_values()
                    
                    # Check if parameters are displayed in treeview
                    items = adv_tab.param_tree.get_children()
                    if items:
                        print(f"✓ {len(items)} parameters displayed in treeview")
                        print(f"✓ {len(items)}個のパラメータがツリービューに表示されました")
                        
                        # Show first few parameters
                        for i, item in enumerate(items[:3]):
                            values = adv_tab.param_tree.item(item)['values']
                            print(f"  Parameter {i+1}: {values[0]} = {values[1]} {values[2]}")
                    else:
                        print("✗ No parameters displayed in treeview")
                        print("✗ ツリービューにパラメータが表示されていません")
                        return False
                else:
                    print(f"✗ Failed to load preset '{preset}'")
                    print(f"✗ プリセット '{preset}' の読み込みに失敗しました")
                    return False
                    
            except Exception as e:
                print(f"✗ Error loading preset '{preset}': {e}")
                print(f"✗ プリセット '{preset}' の読み込みエラー: {e}")
                return False
        
        # Clean up
        root.destroy()
        return True
        
    except Exception as e:
        print(f"✗ Parameter preset test failed: {e}")
        print(f"✗ パラメータプリセットテストが失敗しました: {e}")
        root.destroy()
        return False

def test_simulation_functionality():
    """Test simple simulation functionality."""
    print("\nTesting simulation functionality...")
    print("シミュレーション機能をテストしています...")
    
    # Create a test root window
    root = tk.Tk()
    root.withdraw()  # Hide the window for testing
    
    try:
        # Create a mock app instance
        class MockApp:
            def __init__(self, root):
                self.root = root
                
            def run_in_background(self, message, func):
                """Mock background execution."""
                print(f"Background task: {message}")
                try:
                    func()
                    print("✓ Background task completed successfully")
                    print("✓ バックグラウンドタスクが正常に完了しました")
                except Exception as e:
                    print(f"✗ Background task failed: {e}")
                    print(f"✗ バックグラウンドタスクが失敗しました: {e}")
        
        app = MockApp(root)
        
        # Create the advanced variables tab
        notebook = ttk.Notebook(root)
        adv_tab = AdvancedVariablesTab(notebook, app)
        
        # Load a preset first
        presets = adv_tab.get_available_presets()
        if presets:
            adv_tab.preset_var.set(presets[0])
            adv_tab.load_parameter_preset()
        else:
            print("✗ No presets available for simulation test")
            print("✗ シミュレーションテスト用のプリセットがありません")
            return False
        
        # Test simulation execution
        adv_tab.time_hours_var.set(0.5)  # Set short simulation time
        
        print("Running simulation test...")
        print("シミュレーションテストを実行中...")
        
        # Run simulation (this will use mock data if PyBamm is not available)
        adv_tab._run_simulation_thread(0.5)
        
        # Check if simulation results were generated
        if adv_tab.simulation_results is not None:
            results = adv_tab.simulation_results
            print("✓ Simulation completed successfully")
            print("✓ シミュレーションが正常に完了しました")
            
            # Check result structure
            required_keys = ['time', 'voltage', 'current']
            for key in required_keys:
                if key in results:
                    print(f"✓ Result contains '{key}' data: {len(results[key])} points")
                    print(f"✓ 結果に '{key}' データが含まれています: {len(results[key])}点")
                else:
                    print(f"✗ Result missing '{key}' data")
                    print(f"✗ 結果に '{key}' データがありません")
                    return False
            
            # Test plotting
            try:
                adv_tab.update_plot()
                print("✓ Plot updated successfully")
                print("✓ プロットが正常に更新されました")
            except Exception as e:
                print(f"✗ Plot update failed: {e}")
                print(f"✗ プロット更新が失敗しました: {e}")
                return False
                
        else:
            print("✗ Simulation failed to generate results")
            print("✗ シミュレーションが結果を生成できませんでした")
            return False
        
        # Clean up
        root.destroy()
        return True
        
    except Exception as e:
        print(f"✗ Simulation functionality test failed: {e}")
        print(f"✗ シミュレーション機能テストが失敗しました: {e}")
        root.destroy()
        return False

def test_ui_components():
    """Test UI components and layout."""
    print("\nTesting UI components...")
    print("UIコンポーネントをテストしています...")
    
    # Create a test root window
    root = tk.Tk()
    root.withdraw()  # Hide the window for testing
    
    try:
        # Create a mock app instance
        class MockApp:
            def __init__(self, root):
                self.root = root
                
            def run_in_background(self, message, func):
                pass
        
        app = MockApp(root)
        
        # Create the advanced variables tab
        notebook = ttk.Notebook(root)
        adv_tab = AdvancedVariablesTab(notebook, app)
        
        # Check if required UI components exist
        components_to_check = [
            ('preset_var', 'Parameter preset variable'),
            ('time_hours_var', 'Simulation time variable'),
            ('param_tree', 'Parameter display treeview'),
            ('run_button', 'Run simulation button'),
            ('fig', 'Matplotlib figure'),
            ('canvas', 'Matplotlib canvas')
        ]
        
        for attr_name, description in components_to_check:
            if hasattr(adv_tab, attr_name):
                print(f"✓ {description} found")
                print(f"✓ {description}が見つかりました")
            else:
                print(f"✗ {description} missing")
                print(f"✗ {description}がありません")
                return False
        
        # Test preset combobox values
        presets = adv_tab.get_available_presets()
        if presets:
            print(f"✓ Preset combobox has {len(presets)} options")
            print(f"✓ プリセットコンボボックスに{len(presets)}個のオプションがあります")
        else:
            print("✗ Preset combobox has no options")
            print("✗ プリセットコンボボックスにオプションがありません")
            return False
        
        # Clean up
        root.destroy()
        return True
        
    except Exception as e:
        print(f"✗ UI components test failed: {e}")
        print(f"✗ UIコンポーネントテストが失敗しました: {e}")
        root.destroy()
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Advanced Variables Tab Redesign Test")
    print("高度な変数タブ再設計テスト")
    print("=" * 60)
    
    tests = [
        ("Parameter Presets Test", "パラメータプリセットテスト", test_parameter_presets),
        ("Simulation Functionality Test", "シミュレーション機能テスト", test_simulation_functionality),
        ("UI Components Test", "UIコンポーネントテスト", test_ui_components)
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
        print("✓ All tests passed! Advanced Variables Tab redesign is working correctly.")
        print("✓ すべてのテストが合格しました！高度な変数タブの再設計は正常に動作しています。")
        return True
    else:
        print("✗ Some tests failed. Please check the implementation.")
        print("✗ 一部のテストが失敗しました。実装を確認してください。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
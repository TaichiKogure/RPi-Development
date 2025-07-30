# 高度な変数タブ再設計ガイド / Advanced Variables Tab Redesign Guide

## 概要 / Overview

PyBammUIの高度な変数タブが完全に再設計されました。新しい設計では、パラメータプリセット選択と簡単なシミュレーション実行に焦点を当てています。

The Advanced Variables tab in PyBammUI has been completely redesigned. The new design focuses on parameter preset selection and simple simulation execution.

## 新機能 / New Features

### 1. パラメータプリセット選択 / Parameter Preset Selection
- **機能**: 事前定義されたパラメータセット（例：Chen2020）を選択可能
- **Feature**: Select from predefined parameter sets (e.g., Chen2020)
- **利用可能なプリセット**: Chen2020, Marquis2019, Ecker2015, Mohtat2020など
- **Available Presets**: Chen2020, Marquis2019, Ecker2015, Mohtat2020, etc.

### 2. パラメータ値表示 / Parameter Values Display
- **機能**: 選択したプリセットのパラメータ値を読み取り専用で表示
- **Feature**: Display parameter values from selected preset in read-only format
- **表示形式**: パラメータ名、値、単位を表形式で表示
- **Display Format**: Parameter name, value, and unit in tabular format

### 3. 簡単なシミュレーション実行 / Simple Simulation Execution
- **機能**: DFNモデルを使用した簡単なシミュレーション実行
- **Feature**: Simple simulation execution using DFN model
- **ワークフロー**: `model = pybamm.lithium_ion.DFN()` → `sim = pybamm.Simulation(model, parameter_values=parameter_values)` → `sim.solve([0, 3600])` → `sim.plot()`
- **Workflow**: Simple PyBamm simulation workflow as specified

## 使用方法 / Usage Instructions

### ステップ1: パラメータプリセット選択 / Step 1: Select Parameter Preset

1. **プリセット選択**
   - ドロップダウンメニューから利用可能なプリセットを選択
   - Select an available preset from the dropdown menu

2. **プリセット読み込み**
   - 「プリセット読み込み」ボタンをクリック
   - Click the "Load Preset" button

3. **パラメータ確認**
   - 読み取り専用テーブルでパラメータ値を確認
   - Review parameter values in the read-only table

### ステップ2: シミュレーション実行 / Step 2: Run Simulation

1. **シミュレーション時間設定**
   - シミュレーション時間（時間単位）を設定
   - Set simulation time in hours

2. **シミュレーション実行**
   - 「シミュレーション実行」ボタンをクリック
   - Click the "Run Simulation" button

3. **結果確認**
   - 電圧vs時間のグラフが自動的に表示
   - Voltage vs time graph is automatically displayed

## 技術的詳細 / Technical Details

### 対応パラメータプリセット / Supported Parameter Presets

```python
# 利用可能なプリセット例 / Available preset examples
presets = [
    "Chen2020",      # Chen et al. (2020) parameter set
    "Marquis2019",   # Marquis et al. (2019) parameter set
    "Ecker2015",     # Ecker et al. (2015) parameter set
    "Mohtat2020",    # Mohtat et al. (2020) parameter set
    "Prada2013",     # Prada et al. (2013) parameter set
    "Ramadass2004",  # Ramadass et al. (2004) parameter set
    "Ai2020",        # Ai et al. (2020) parameter set
    "ORegan2022"     # O'Regan et al. (2022) parameter set
]
```

### シミュレーションワークフロー / Simulation Workflow

```python
# 実装されたシンプルなワークフロー / Implemented simple workflow
parameter_values = pybamm.ParameterValues("Chen2020")
model = pybamm.lithium_ion.DFN()
sim = pybamm.Simulation(model, parameter_values=parameter_values)
sim.solve([0, 3600])
sim.plot()  # 基本的なプロット機能 / Basic plotting functionality
```

### パラメータ表示形式 / Parameter Display Format

| パラメータ名 / Parameter Name | 値 / Value | 単位 / Unit |
|------------------------------|------------|-------------|
| Nominal cell capacity | 2.5000 | A.h |
| Ambient temperature | 298.15 | K |
| Electrode height | 0.0650 | m |
| Electrode width | 1.5800 | m |

## 変更点 / Changes Made

### 削除された機能 / Removed Features
- ✗ 複雑な変数ブラウジング機能
- ✗ Complex variable browsing functionality
- ✗ カスタム変数定義機能
- ✗ Custom variable definition functionality
- ✗ パラメータ値の手動変更機能
- ✗ Manual parameter value modification

### 追加された機能 / Added Features
- ✓ パラメータプリセット選択機能
- ✓ Parameter preset selection functionality
- ✓ 読み取り専用パラメータ表示
- ✓ Read-only parameter display
- ✓ 簡単なシミュレーション実行
- ✓ Simple simulation execution
- ✓ 基本的なプロット機能
- ✓ Basic plotting functionality

## プログラムからの使用方法 / Programmatic Usage

```python
# 高度な変数タブのインスタンスを取得
# Get advanced variables tab instance
adv_tab = app.advanced_variables_tab

# パラメータプリセットを設定
# Set parameter preset
adv_tab.preset_var.set("Chen2020")
adv_tab.load_parameter_preset()

# シミュレーション時間を設定
# Set simulation time
adv_tab.time_hours_var.set(1.0)

# シミュレーションを実行
# Run simulation
adv_tab.run_simulation()
```

## トラブルシューティング / Troubleshooting

### 「パラメータプリセットを先に読み込んでください」エラー
**Error: "パラメータプリセットを先に読み込んでください"**

**原因 / Cause:**
- パラメータプリセットが読み込まれていない
- Parameter preset has not been loaded

**解決方法 / Solution:**
1. プリセットを選択して「プリセット読み込み」ボタンをクリック
   Select a preset and click "Load Preset" button
2. パラメータ値がテーブルに表示されることを確認
   Verify that parameter values are displayed in the table

### 「シミュレーション中にエラーが発生しました」エラー
**Error: "シミュレーション中にエラーが発生しました"**

**原因 / Cause:**
- PyBammが正しくインストールされていない
- PyBamm is not properly installed
- 無効なシミュレーション時間
- Invalid simulation time

**解決方法 / Solution:**
1. PyBammが正しくインストールされていることを確認
   Ensure PyBamm is properly installed
2. シミュレーション時間が正の値であることを確認
   Verify simulation time is a positive value
3. モックデータでテストする場合は、PyBammなしでも動作します
   For testing with mock data, it works without PyBamm

## 更新履歴 / Change Log

### Version 2.0.0 (Redesign)
- 完全な再設計によりパラメータプリセット機能に焦点
- Complete redesign focusing on parameter preset functionality
- 簡単なシミュレーション実行ワークフローを実装
- Implemented simple simulation execution workflow
- 読み取り専用パラメータ表示機能を追加
- Added read-only parameter display functionality
- 複雑な変数ブラウジング機能を削除
- Removed complex variable browsing functionality
- UIの簡素化と使いやすさの向上
- Simplified UI and improved usability

## 参考文献 / References

- Chen, C. H., et al. (2020). Development of Experimental Techniques for Parameterization of Multi-scale Lithium-ion Battery Models
- Marquis, S. G., et al. (2019). An asymptotic derivation of a single particle model with electrolyte
- Ecker, M., et al. (2015). Parameterization of a Physico-Chemical Model of a Lithium-Ion Battery
- Mohtat, P., et al. (2020). Towards better estimability of electrode-specific state of health
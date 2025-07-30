# 電圧成分プロット機能ガイド / Voltage Components Plotting Guide

## 概要 / Overview

PyBammUIに新しい電圧成分プロット機能が追加されました。この機能により、バッテリーシミュレーション結果の内部抵抗要素を詳細に分析できます。

A new voltage components plotting feature has been added to PyBammUI. This feature allows detailed analysis of internal resistance elements in battery simulation results.

## 機能 / Features

### 1. 基本電圧成分プロット / Basic Voltage Components Plot
- **UI選択**: プロットタイプで「voltage_components」を選択
- **UI Selection**: Select "voltage_components" in plot type dropdown
- **機能**: すべての電圧成分を一つのグラフに表示
- **Function**: Display all voltage components in a single graph

### 2. 電極別電圧成分プロット / Electrode-Split Voltage Components Plot
- **UI選択**: プロットタイプで「voltage_components_split」を選択
- **UI Selection**: Select "voltage_components_split" in plot type dropdown
- **機能**: 電圧成分を電極別（正極・負極）に分けて表示
- **Function**: Display voltage components split by electrode (positive/negative)

## プログラムからの使用方法 / Programmatic Usage

```python
# シミュレーションタブのインスタンスを取得
# Get simulation tab instance
sim_tab = app.simulation_tab

# 基本的な電圧成分プロット
# Basic voltage components plot
sim_tab.plot_voltage_components()

# 電極別電圧成分プロット
# Electrode-split voltage components plot
sim_tab.plot_voltage_components(split_by_electrode=True)
```

## 表示される電圧成分 / Displayed Voltage Components

### 基本成分 / Basic Components
- **開回路電圧 (OCV)**: Open Circuit Voltage
- **オーム損失**: Ohmic Losses
- **濃度過電圧**: Concentration Overpotential
- **反応過電圧**: Reaction Overpotential

### 電極別成分 / Electrode-Specific Components
- **負極電位**: Negative Electrode Potential
- **正極電位**: Positive Electrode Potential
- **負極開回路電位**: Negative Electrode Open Circuit Potential
- **正極開回路電位**: Positive Electrode Open Circuit Potential
- **負極反応過電圧**: Negative Electrode Reaction Overpotential
- **正極反応過電圧**: Positive Electrode Reaction Overpotential

### 詳細成分 / Detailed Components
- **電解液オーム損失**: Electrolyte Ohmic Losses
- **固相オーム損失**: Solid Phase Ohmic Losses

## 使用手順 / Usage Instructions

1. **シミュレーション実行 / Run Simulation**
   - 通常通りパラメータを設定してシミュレーションを実行
   - Set parameters and run simulation as usual

2. **プロットタイプ選択 / Select Plot Type**
   - プロットタイプドロップダウンから以下のいずれかを選択:
   - Select one of the following from the plot type dropdown:
     - `voltage_components`: 基本電圧成分プロット
     - `voltage_components_split`: 電極別電圧成分プロット

3. **結果確認 / View Results**
   - グラフが自動的に更新され、電圧成分が表示されます
   - The graph will automatically update to show voltage components
   - 凡例は右側に表示され、各成分を識別できます
   - Legend is displayed on the right side to identify each component

## 技術的詳細 / Technical Details

### データソース / Data Source
- PyBammシミュレーション結果から電圧成分を抽出
- Voltage components are extracted from PyBamm simulation results
- PyBammが利用できない場合、モックデータを使用
- Mock data is used when PyBamm is not available

### 対応するPyBamm変数 / Supported PyBamm Variables
```python
# 基本変数 / Basic variables
"Open-circuit voltage [V]"
"Ohmic losses [V]"
"Concentration overpotential [V]"
"Reaction overpotential [V]"

# 電極別変数 / Electrode-specific variables
"Negative electrode potential [V]"
"Positive electrode potential [V]"
"X-averaged negative electrode open-circuit potential [V]"
"X-averaged positive electrode open-circuit potential [V]"
"X-averaged negative electrode reaction overpotential [V]"
"X-averaged positive electrode reaction overpotential [V]"

# 詳細変数 / Detailed variables
"X-averaged electrolyte ohmic losses [V]"
"X-averaged solid phase ohmic losses [V]"
```

### カラーコーディング / Color Coding
- 各電圧成分は異なる色で表示されます
- Each voltage component is displayed in a different color
- 電極別表示では、線種も区別されます:
- In electrode-split view, line styles are also differentiated:
  - 負極成分: 破線 (--) / Negative electrode: dashed line
  - 正極成分: 一点鎖線 (-.) / Positive electrode: dash-dot line
  - 一般成分: 実線 (-) / General components: solid line

## トラブルシューティング / Troubleshooting

### 「電圧成分データが利用できません」エラー
**Error: "電圧成分データが利用できません"**

**原因 / Cause:**
- シミュレーションが実行されていない
- Simulation has not been run
- PyBammシミュレーションが失敗し、モックデータに電圧成分が含まれていない
- PyBamm simulation failed and mock data doesn't include voltage components

**解決方法 / Solution:**
1. シミュレーションを再実行してください
   Re-run the simulation
2. PyBammが正しくインストールされていることを確認してください
   Ensure PyBamm is properly installed

### グラフが表示されない
**Graph not displaying**

**解決方法 / Solution:**
1. 他のプロットタイプ（voltage_time等）が正常に表示されるか確認
   Check if other plot types (voltage_time, etc.) display correctly
2. シミュレーション結果が正常に生成されているか確認
   Verify that simulation results are generated correctly

## 更新履歴 / Change Log

### Version 1.0.0
- 基本的な電圧成分プロット機能を追加
- Added basic voltage components plotting functionality
- 電極別表示機能を追加
- Added electrode-split display functionality
- PyBammシミュレーション結果からの電圧成分抽出機能を追加
- Added voltage component extraction from PyBamm simulation results
- モックデータでのテスト機能を追加
- Added testing functionality with mock data
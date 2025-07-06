# Ver4.35 - Simplified Web Interface for Environmental Data Visualization

[日本語版はこちら](#ver435---環境データ可視化のためのシンプル化されたwebインターフェース)

## Overview

This update introduces a simplified web interface for visualizing environmental data collected from P2 and P3 sensor nodes. The new implementation addresses several issues with the previous version:

1. **Graph Scaling Issues**: Graphs no longer start at zero by default, instead using proper Y-axis auto-scaling based on the actual data range
2. **Loading Graph Message**: The "Loading Graph" message is now properly cleared once data is loaded
3. **Connection Status Display**: Real-time connection status for P2 and P3 is now displayed
4. **Simplified Code Structure**: The code has been reorganized for better maintainability and performance

## Key Features

- **Direct Data Reading**: Reads directly from fixed CSV files (`P2_fixed.csv` and `P3_fixed.csv`)
- **Proper Graph Scaling**: Y-axis ranges are automatically set based on the actual data values
- **Toggle Device Data**: Show/hide P2 and P3 data independently
- **Time Range Selection**: View data for different time periods (1 day, 3 days, 7 days, etc.)
- **Auto-refresh**: Automatically update graphs at configurable intervals
- **Data Export**: Export data for specific devices and date ranges
- **Connection Status**: View real-time connection status for P2 and P3 sensor nodes
- **Responsive Design**: Works well on both desktop and mobile devices

## Technical Details

### Data Reading

The new implementation reads data directly from the fixed CSV files:
```
/var/lib/raspap_solo/data/RawData_P2/P2_fixed.csv
/var/lib/raspap_solo/data/RawData_P3/P3_fixed.csv
```

The timestamp handling has been improved to automatically detect and convert both numeric and string timestamp formats:

```python
if df['timestamp'].dtype == 'int64' or df['timestamp'].dtype == 'float64':
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
else:
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
```

### Graph Generation

Graphs are generated using Plotly.js with proper Y-axis auto-scaling:

```python
# Set Y-axis to auto-range
fig.update_yaxes(autorange=True)
```

The code also validates data to ensure there are at least 2 unique non-NaN values for each parameter before attempting to plot:

```python
p2_values = df_p2[parameter].dropna()
if len(p2_values) > 0 and len(p2_values.unique()) >= 2:
    # Add trace to graph
else:
    logger.warning(f"P2 data for {parameter} has insufficient unique values")
```

### Frontend

The frontend uses a single HTML template with embedded JavaScript for interactivity. Key features include:

- Bootstrap 5 for responsive layout
- Plotly.js for interactive graphs
- jQuery for AJAX requests
- Auto-refresh functionality with configurable intervals
- Modal dialog for data export

## Usage

### Running the Application

To run the simplified web interface:

```bash
python3 P1_app_simple.py [--port PORT] [--data-dir DIR] [--debug]
```

Options:
- `--port PORT`: Specify the port to listen on (default: 80)
- `--data-dir DIR`: Specify the directory to read data from (default: /var/lib/raspap_solo/data)
- `--debug`: Enable debug mode

### Using the Dashboard

1. **Toggle Device Data**:
   - Use the checkboxes to show/hide P2 and P3 data

2. **Change Time Range**:
   - Select from 1 day, 3 days, 7 days, 14 days, or 30 days

3. **Auto-refresh**:
   - Choose an auto-refresh interval or turn it off
   - Click "Refresh Now" to manually refresh the data

4. **Export Data**:
   - Click "Export Data" to open the export dialog
   - Select a device (P2, P3, or All)
   - Choose a date range
   - Click "Export" to download the data as a CSV file

## Implementation Notes

This implementation is designed to be a drop-in replacement for the existing web interface. It maintains all the functionality of the previous version while addressing the identified issues.

To switch between the original and simplified versions, you can use the following commands:

```bash
# Use the original version
python3 P1_app_solo.py

# Use the simplified version
python3 P1_app_simple.py
```

Both versions can coexist in the same directory without conflicts.

---

# Ver4.35 - 環境データ可視化のためのシンプル化されたWebインターフェース

[English version above](#ver435---simplified-web-interface-for-environmental-data-visualization)

## 概要

この更新では、P2およびP3センサーノードから収集された環境データを可視化するためのシンプル化されたWebインターフェースを導入しています。新しい実装は、以前のバージョンのいくつかの問題に対処しています：

1. **グラフスケーリングの問題**: グラフはデフォルトで0から始まらなくなり、代わりに実際のデータ範囲に基づいて適切なY軸の自動スケーリングを使用します
2. **「Loading Graph」メッセージの問題**: データが読み込まれると「Loading Graph」メッセージが適切にクリアされるようになりました
3. **接続状態の表示**: P2とP3のリアルタイム接続状態が表示されるようになりました
4. **コード構造の簡素化**: コードが保守性とパフォーマンスを向上させるために再編成されました

## 主な機能

- **直接データ読み取り**: 固定CSVファイル（`P2_fixed.csv`および`P3_fixed.csv`）から直接読み取ります
- **適切なグラフスケーリング**: Y軸の範囲は実際のデータ値に基づいて自動的に設定されます
- **デバイスデータの切り替え**: P2とP3のデータを個別に表示/非表示にできます
- **時間範囲の選択**: 異なる時間期間（1日、3日、7日など）のデータを表示できます
- **自動更新**: 設定可能な間隔でグラフを自動的に更新します
- **データエクスポート**: 特定のデバイスと日付範囲のデータをエクスポートできます
- **接続状態**: P2とP3センサーノードのリアルタイム接続状態を表示します
- **レスポンシブデザイン**: デスクトップとモバイルデバイスの両方で適切に動作します

## 技術的詳細

### データ読み取り

新しい実装は固定CSVファイルから直接データを読み取ります：
```
/var/lib/raspap_solo/data/RawData_P2/P2_fixed.csv
/var/lib/raspap_solo/data/RawData_P3/P3_fixed.csv
```

タイムスタンプの処理が改善され、数値形式と文字列形式の両方のタイムスタンプを自動的に検出して変換できるようになりました：

```python
if df['timestamp'].dtype == 'int64' or df['timestamp'].dtype == 'float64':
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
else:
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
```

### グラフ生成

グラフは適切なY軸の自動スケーリングを使用してPlotly.jsで生成されます：

```python
# Y軸を自動範囲に設定
fig.update_yaxes(autorange=True)
```

また、プロットを試みる前に、各パラメータに少なくとも2つの一意の非NaN値があることを確認するためのデータ検証も行います：

```python
p2_values = df_p2[parameter].dropna()
if len(p2_values) > 0 and len(p2_values.unique()) >= 2:
    # グラフにトレースを追加
else:
    logger.warning(f"P2 data for {parameter} has insufficient unique values")
```

### フロントエンド

フロントエンドはインタラクティブ性のための組み込みJavaScriptを持つ単一のHTMLテンプレートを使用しています。主な機能は以下の通りです：

- レスポンシブレイアウトのためのBootstrap 5
- インタラクティブグラフのためのPlotly.js
- AJAXリクエストのためのjQuery
- 設定可能な間隔での自動更新機能
- データエクスポート用のモーダルダイアログ

## 使用方法

### アプリケーションの実行

シンプル化されたWebインターフェースを実行するには：

```bash
python3 P1_app_simple.py [--port PORT] [--data-dir DIR] [--debug]
```

オプション：
- `--port PORT`: リッスンするポートを指定（デフォルト：80）
- `--data-dir DIR`: データを読み取るディレクトリを指定（デフォルト：/var/lib/raspap_solo/data）
- `--debug`: デバッグモードを有効にする

### ダッシュボードの使用

1. **デバイスデータの切り替え**：
   - チェックボックスを使用してP2とP3のデータを表示/非表示にします

2. **時間範囲の変更**：
   - 1日、3日、7日、14日、または30日から選択します

3. **自動更新**：
   - 自動更新の間隔を選択するか、オフにします
   - 「Refresh Now」をクリックしてデータを手動で更新します

4. **データのエクスポート**：
   - 「Export Data」をクリックしてエクスポートダイアログを開きます
   - デバイス（P2、P3、またはAll）を選択します
   - 日付範囲を選択します
   - 「Export」をクリックしてデータをCSVファイルとしてダウンロードします

## 実装に関する注意

この実装は、既存のWebインターフェースのドロップイン置き換えとして設計されています。以前のバージョンのすべての機能を維持しながら、特定された問題に対処しています。

オリジナルバージョンとシンプル化されたバージョンを切り替えるには、次のコマンドを使用できます：

```bash
# オリジナルバージョンを使用
python3 P1_app_solo.py

# シンプル化されたバージョンを使用
python3 P1_app_simple.py
```

両方のバージョンは競合することなく同じディレクトリに共存できます。
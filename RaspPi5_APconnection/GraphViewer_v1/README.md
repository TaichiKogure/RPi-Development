# GraphViewer_v1 - 環境データ可視化ツール

このツールは、P2およびP3デバイスから収集された環境データをCSVファイルから読み込み、Plotlyを使用してインタラクティブなグラフを生成します。

## 機能

- P2およびP3デバイスのデータを同時に表示
- 温度、湿度、絶対湿度、CO2濃度、気圧、ガス抵抗の時系列グラフ
- すべてのパラメータを一つのダッシュボードに表示
- 各パラメータに適した軸スケールの自動調整
- データの日数フィルタリング
- グラフのHTML形式での保存

## 必要条件

- Python 3.6以上
- 以下のPythonパッケージ:
  - pandas
  - plotly
  - numpy

インストール方法:

```bash
pip install pandas plotly numpy
```

## 使用方法

### 基本的な使用方法

```bash
python graph_viewer_Ver3.py
```

これにより、デフォルトのパスからP2とP3のデータを読み込み、ブラウザでダッシュボードを表示します。

### コマンドラインオプション

```bash
python graph_viewer_Ver3.py [--p2-path PATH] [--p3-path PATH] [--days DAYS] [--output PATH]
```

オプション:
- `--p2-path PATH`: P2のCSVデータファイルのパス（デフォルト: /var/lib/raspap_solo/data/RawData_P2/P2_fixed.csv）
- `--p3-path PATH`: P3のCSVデータファイルのパス（デフォルト: /var/lib/raspap_solo/data/RawData_P3/P3_fixed.csv）
- `--days DAYS`: 表示するデータの日数（デフォルト: 1）
- `--show-p2`: P2のデータを表示（デフォルト: 有効）
- `--show-p3`: P3のデータを表示（デフォルト: 有効）
- `--output PATH`: グラフを保存するファイルパス（指定しない場合はブラウザで表示）

### 例

1. 過去7日間のデータを表示:

```bash
python graph_viewer_Ver3.py --days 7
```

2. カスタムパスからデータを読み込み:

```bash
python graph_viewer_Ver3.py --p2-path "C:\data\p2_data.csv" --p3-path "C:\data\p3_data.csv"
```

3. P2のデータのみを表示:

```bash
python graph_viewer_Ver3.py --show-p2 --show-p3 False
```

4. グラフをHTMLファイルとして保存:

```bash
python graph_viewer_Ver3.py --output "C:\reports\environmental_data.html"
```

## データ形式

このツールは以下の形式のCSVファイルを読み込みます:

```
timestamp,device_id,temperature,humidity,pressure,gas_resistance,co2,absolute_humidity
2025-07-05 22:22:56,P2,26.92492,67.85529,997.9535,10065,678,17.39
2025-07-05 22:23:14,P2,26.86281,67.72371,997.9338,10055,682,17.3
...
```

タイムスタンプは文字列形式（例: "2025-07-05 22:22:56"）またはUNIXタイムスタンプ（秒単位）として認識されます。

## トラブルシューティング

### データが表示されない場合

1. CSVファイルが存在することを確認してください
2. CSVファイルのフォーマットが正しいことを確認してください
3. ログファイル（graph_viewer.log）を確認して詳細なエラーメッセージを確認してください

### グラフの軸スケールが適切でない場合

データの範囲が極端に広い場合や、異常値が含まれている場合、軸スケールが適切に設定されないことがあります。その場合は、CSVファイルを確認して異常値を除去してください。

## ログ

スクリプトの実行中のログは `graph_viewer.log` ファイルに保存されます。問題が発生した場合は、このファイルを確認してください。
# 環境データ可視化ツール

このリポジトリには、P2およびP3デバイスから収集された環境データを可視化するための2つのツールが含まれています：

1. **graph_viewer2.py** - 基本的なグラフ可視化ツール
2. **auto_graph_viewer.py** - 自動更新機能付きグラフ可視化ツール

どちらのツールも、CSVファイルからデータを読み込み、Plotlyを使用してインタラクティブなグラフを生成します。

## 目次

- [共通の機能](#共通の機能)
- [必要条件](#必要条件)
- [基本的なグラフ可視化ツール (graph_viewer2.py)](#基本的なグラフ可視化ツール-graph_viewer2py)
- [自動更新機能付きグラフ可視化ツール (auto_graph_viewer.py)](#自動更新機能付きグラフ可視化ツール-auto_graph_viewerpy)
- [データ形式](#データ形式)
- [トラブルシューティング](#トラブルシューティング)

## 共通の機能

両方のツールに共通する機能：

- P2およびP3デバイスのデータを同時に表示
- 温度、湿度、絶対湿度、CO2濃度、気圧、ガス抵抗の時系列グラフ
- すべてのパラメータを一つのダッシュボードに表示
- 各パラメータに適した軸スケールの自動調整
- データの日数フィルタリング

## 必要条件

### 基本的なグラフ可視化ツール (graph_viewer2.py)

- Python 3.6以上
- 以下のPythonパッケージ:
  - pandas
  - plotly
  - numpy

インストール方法:

```bash
pip install pandas plotly numpy
```

### 自動更新機能付きグラフ可視化ツール (auto_graph_viewer.py)

- Python 3.6以上
- 以下のPythonパッケージ:
  - pandas
  - plotly
  - numpy
  - flask

インストール方法:

```bash
pip install pandas plotly numpy flask
```

## 基本的なグラフ可視化ツール (graph_viewer2.py)

このツールは、CSVファイルからデータを読み込み、HTMLファイルとしてグラフを生成します。グラフを更新するには、スクリプトを再実行する必要があります。

### 使用方法

#### 基本的な使用方法

```bash
python graph_viewer_Ver4.py
```

これにより、デフォルトのパスからP2とP3のデータを読み込み、ブラウザでダッシュボードを表示します。

#### コマンドラインオプション

```bash
python graph_viewer_Ver4.py [--p2-path PATH] [--p3-path PATH] [--days DAYS] [--output PATH]
```

オプション:
- `--p2-path PATH`: P2のCSVデータファイルのパス（デフォルト: /var/lib/raspap_solo/data/RawData_P2/P2_fixed.csv）
- `--p3-path PATH`: P3のCSVデータファイルのパス（デフォルト: /var/lib/raspap_solo/data/RawData_P3/P3_fixed.csv）
- `--days DAYS`: 表示するデータの日数（デフォルト: 1）
- `--show-p2`: P2のデータを表示（デフォルト: 有効）
- `--show-p3`: P3のデータを表示（デフォルト: 有効）
- `--output PATH`: グラフを保存するファイルパス（指定しない場合はブラウザで表示）

#### 例

1. 過去7日間のデータを表示:

```bash
python graph_viewer_Ver4.py --days 7
```

2. カスタムパスからデータを読み込み:

```bash
python graph_viewer_Ver4.py --p2-path "C:\data\p2_data.csv" --p3-path "C:\data\p3_data.csv"
```

3. P2のデータのみを表示:

```bash
python graph_viewer_Ver4.py --show-p2 --show-p3 False
```

4. グラフをHTMLファイルとして保存:

```bash
python graph_viewer_Ver4.py --output "C:\reports\environmental_data.html"
```

## 自動更新機能付きグラフ可視化ツール (auto_graph_viewer.py)

このツールは、基本的なグラフ可視化ツールの機能に加えて、以下の新機能を提供します：

- **自動データ更新**: 5分ごと（設定可能）にデータを自動的に再読み込み
- **ブラウザ自動更新**: 新しいデータが利用可能になると自動的にブラウザを更新
- **Webインターフェース**: データをブラウザで簡単に閲覧できるWebサーバー
- **カウントダウンタイマー**: 次回の更新までの時間を表示
- **手動更新ボタン**: いつでも手動でデータを更新可能

### 使用方法

#### 基本的な使用方法

```bash
python auto_graph_viewer_Ver4.py
```

これにより、デフォルトのパスからP2とP3のデータを読み込み、Webサーバーが起動します。ブラウザで `http://localhost:8050` にアクセスすると、ダッシュボードが表示されます。データは5分ごとに自動的に更新されます。

#### コマンドラインオプション

```bash
python auto_graph_viewer_Ver4.py [--p2-path PATH] [--p3-path PATH] [--port PORT] [--interval MINS] [--days DAYS]
```

オプション:
- `--p2-path PATH`: P2のCSVデータファイルのパス（デフォルト: /var/lib/raspap_solo/data/RawData_P2/P2_fixed.csv）
- `--p3-path PATH`: P3のCSVデータファイルのパス（デフォルト: /var/lib/raspap_solo/data/RawData_P3/P3_fixed.csv）
- `--port PORT`: Webサーバーのポート番号（デフォルト: 8050）
- `--interval MINS`: データ更新間隔（分）（デフォルト: 5）
- `--days DAYS`: 表示するデータの日数（デフォルト: 1）
- `--show-p2`: P2のデータを表示（デフォルト: 有効）
- `--show-p3`: P3のデータを表示（デフォルト: 有効）

#### 例

1. 更新間隔を10分に設定:

```bash
python auto_graph_viewer_Ver4.py --interval 10
```

2. 過去7日間のデータを表示:

```bash
python auto_graph_viewer_Ver4.py --days 7
```

3. カスタムポートでWebサーバーを起動:

```bash
python auto_graph_viewer_Ver4.py --port 5000
```

### Webインターフェースの使用方法

Webインターフェースには以下の機能があります:

1. **ダッシュボード**: すべてのパラメータ（気温、湿度、絶対湿度、CO2濃度、気圧、ガス抵抗）を一つの画面で表示
2. **個別グラフ**: 各パラメータの詳細グラフを個別に表示
3. **ステータス情報**: 最終更新時刻、次回更新までのカウントダウン、表示データの期間などを表示
4. **手動更新ボタン**: クリックするとデータを即時更新

ブラウザは設定された間隔（デフォルト: 5分）で自動的に更新されますが、「今すぐ更新」ボタンをクリックすることでいつでも手動で更新できます。

### バックグラウンドでの実行方法

長時間実行する場合は、以下のようにバックグラウンドで実行することをお勧めします:

#### Linuxの場合:

```bash
nohup python auto_graph_viewer_Ver4.py > auto_graph_viewer.out 2>&1 &
```

#### Windowsの場合:

```bash
start /b python auto_graph_viewer_Ver4.py > auto_graph_viewer.out 2>&1
```

## データ形式

両方のツールは以下の形式のCSVファイルを読み込みます:

```
timestamp,device_id,temperature,humidity,pressure,gas_resistance,co2,absolute_humidity
2025-07-05 22:22:56,P2,26.92492,67.85529,997.9535,10065,678,17.39
2025-07-05 22:23:14,P2,26.86281,67.72371,997.9338,10055,682,17.3
...
```

タイムスタンプは文字列形式（例: "2025-07-05 22:22:56"）またはUNIXタイムスタンプ（秒単位）として認識されます。

## トラブルシューティング

### 基本的なグラフ可視化ツール (graph_viewer2.py)

#### データが表示されない場合

1. CSVファイルが存在することを確認してください
2. CSVファイルのフォーマットが正しいことを確認してください
3. ログファイル（graph_viewer.log）を確認してください

#### グラフの軸スケールが適切でない場合

データの範囲が極端に広い場合や、異常値が含まれている場合、軸スケールが適切に設定されないことがあります。その場合は、CSVファイルを確認して異常値を除去してください。

### 自動更新機能付きグラフ可視化ツール (auto_graph_viewer.py)

#### Webサーバーが起動しない場合

1. 指定したポートが他のアプリケーションで使用されていないか確認してください
2. `--port` オプションで別のポート番号を指定してみてください
3. ログファイル（auto_graph_viewer.log）を確認してください

#### データが表示されない場合

1. CSVファイルが存在することを確認してください
2. CSVファイルのフォーマットが正しいことを確認してください
3. ログファイル（auto_graph_viewer.log）を確認してください

#### 自動更新が機能しない場合

1. ブラウザのキャッシュをクリアしてみてください
2. ブラウザの開発者ツールでエラーがないか確認してください
3. スクリプトが正常に実行されているか確認してください

## ログ

- 基本的なグラフ可視化ツール (graph_viewer2.py) のログは `graph_viewer.log` ファイルに保存されます。
- 自動更新機能付きグラフ可視化ツール (auto_graph_viewer.py) のログは `auto_graph_viewer.log` ファイルに保存されます。

問題が発生した場合は、これらのログファイルを確認してください。
# 自動更新機能付き環境データ可視化ツール

このツールは、P2およびP3デバイスから収集された環境データをCSVファイルから読み込み、Plotlyを使用してインタラクティブなグラフを生成します。さらに、データを定期的に自動更新し、ブラウザでリアルタイムに表示します。

## 新機能

- **自動データ更新**: 5分ごと（設定可能）にデータを自動的に再読み込み
- **ブラウザ自動更新**: 新しいデータが利用可能になると自動的にブラウザを更新
- **Webインターフェース**: データをブラウザで簡単に閲覧できるWebサーバー
- **カウントダウンタイマー**: 次回の更新までの時間を表示
- **手動更新ボタン**: いつでも手動でデータを更新可能

## 必要条件

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

## 使用方法

### 基本的な使用方法

```bash
python auto_graph_viewer_Ver4.py
```

これにより、デフォルトのパスからP2とP3のデータを読み込み、Webサーバーが起動します。ブラウザで `http://localhost:8050` にアクセスすると、ダッシュボードが表示されます。データは5分ごとに自動的に更新されます。

### コマンドラインオプション

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

### 例

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

4. カスタムパスからデータを読み込み:

```bash
python auto_graph_viewer_Ver4.py --p2-path "C:\data\p2_data.csv" --p3-path "C:\data\p3_data.csv"
```

5. P2のデータのみを表示:

```bash
python auto_graph_viewer_Ver4.py --show-p2 --show-p3 False
```

## Webインターフェースの使用方法

Webインターフェースには以下の機能があります:

1. **ダッシュボード**: すべてのパラメータ（気温、湿度、絶対湿度、CO2濃度、気圧、ガス抵抗）を一つの画面で表示
2. **個別グラフ**: 各パラメータの詳細グラフを個別に表示
3. **ステータス情報**: 最終更新時刻、次回更新までのカウントダウン、表示データの期間などを表示
4. **手動更新ボタン**: クリックするとデータを即時更新

ブラウザは設定された間隔（デフォルト: 5分）で自動的に更新されますが、「今すぐ更新」ボタンをクリックすることでいつでも手動で更新できます。

## バックグラウンドでの実行方法

長時間実行する場合は、以下のようにバックグラウンドで実行することをお勧めします:

### Linuxの場合:

```bash
nohup python auto_graph_viewer_Ver4.py > auto_graph_viewer.out 2>&1 &
```

### Windowsの場合:

```bash
start /b python auto_graph_viewer_Ver4.py > auto_graph_viewer.out 2>&1
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

### Webサーバーが起動しない場合

1. 指定したポートが他のアプリケーションで使用されていないか確認してください
2. `--port` オプションで別のポート番号を指定してみてください
3. ログファイル（auto_graph_viewer.log）を確認してください

### データが表示されない場合

1. CSVファイルが存在することを確認してください
2. CSVファイルのフォーマットが正しいことを確認してください
3. ログファイル（auto_graph_viewer.log）を確認してください

### 自動更新が機能しない場合

1. ブラウザのキャッシュをクリアしてみてください
2. ブラウザの開発者ツールでエラーがないか確認してください
3. スクリプトが正常に実行されているか確認してください

## ログ

スクリプトの実行中のログは `auto_graph_viewer.log` ファイルに保存されます。問題が発生した場合は、このファイルを確認してください。
# Raspberry Pi 5 環境データ測定システム ソロバージョン 操作ガイド

## バージョン情報
- ドキュメントバージョン: 1.0.0
- ソフトウェアバージョン: 1.0.0-solo

## 概要
このガイドでは、Raspberry Pi 5（P1）とBME680センサーを搭載した単一のRaspberry Pi Pico 2W（P2）を使用した環境データ測定システム（ソロバージョン）の操作方法を説明します。

## システム構成
ソロバージョンのシステムは以下のコンポーネントで構成されています：

1. **Raspberry Pi 5（P1）** - 中央ハブとして機能し、以下を行います：
   - P2デバイス用のWiFiアクセスポイントとして機能
   - P2から環境データを収集・保存
   - データ可視化用のWebインターフェースを提供
   - P2との接続品質をモニタリング

2. **Raspberry Pi Pico 2W（P2）** - センサーノードとして機能し、以下を行います：
   - BME680センサーを使用して環境データを収集
   - WiFi経由でP1にデータを送信
   - エラーや接続問題が発生した場合に自動再起動

3. **センサー**:
   - BME680 - 温度、湿度、大気圧、ガスパラメータを測定

## システムの起動と停止

### システムの起動
システムが自動起動するように設定されている場合、Raspberry Pi 5の電源を入れるだけで全サービスが起動します。

手動で起動する場合は、以下のコマンドを実行します：

```bash
cd /path/to/RaspPi5_APconnection/p1_software_solo
sudo python3 start_p1_solo.py
```

### システムの停止
システムを停止するには、以下のいずれかの方法を使用します：

1. 統合スタートアップスクリプトを実行しているターミナルで `Ctrl+C` を押す
2. 以下のコマンドでプロセスを終了する：
   ```bash
   sudo pkill -f start_p1_solo.py
   ```

## Webインターフェースの使用方法

### アクセス方法
1. P2デバイスをRaspberry Pi 5のアクセスポイント（SSID: RaspberryPi5_AP_Solo）に接続します
2. WebブラウザでRaspberry Pi 5のIPアドレス（デフォルトは192.168.0.1）にアクセスします

### ホーム画面
ホーム画面では、P2デバイスから収集された最新の環境データの概要が表示されます：
- 温度（°C）
- 湿度（%）
- 気圧（hPa）
- ガス抵抗値（Ω）

「View Dashboard」ボタンをクリックすると、詳細なダッシュボードが表示されます。

### ダッシュボード画面
ダッシュボード画面では、以下の情報が表示されます：

1. **現在の測定値**:
   - 温度（°C）
   - 湿度（%）
   - 気圧（hPa）
   - ガス抵抗値（Ω）
   - 最終更新時刻

2. **時系列グラフ**:
   - 温度グラフ
   - 湿度グラフ
   - 気圧グラフ
   - ガス抵抗値グラフ

3. **データエクスポート**:
   - 開始日と終了日を選択してCSVファイルとしてデータをエクスポート可能

### 表示期間の変更
ダッシュボード上部のボタンを使用して、表示するデータの期間を変更できます：
- 1日（デフォルト）
- 1週間
- 1ヶ月

## 接続モニターの使用方法

### APIアクセス
接続モニターは、P2デバイスとの接続品質に関する情報を提供するAPIを公開しています：

1. **最新の接続データを取得**:
   ```
   http://192.168.0.1:5002/api/connection/latest
   ```

2. **P2デバイスの最新データを取得**:
   ```
   http://192.168.0.1:5002/api/connection/device/P2
   ```

3. **P2デバイスの接続履歴を取得**:
   ```
   http://192.168.0.1:5002/api/connection/history/P2
   ```

   オプションで履歴の件数を制限できます：
   ```
   http://192.168.0.1:5002/api/connection/history/P2?limit=10
   ```

### 接続品質の解釈
接続モニターは以下の情報を提供します：

1. **信号強度（dBm）**:
   - -50 dBm以上: 優秀
   - -60 dBm以上: 非常に良い
   - -70 dBm以上: 良い
   - -80 dBm以上: 普通
   - -80 dBm未満: 不良

2. **ノイズレベル（dBm）**:
   - 一般的に-90 dBm以下が理想的

3. **信号対雑音比（SNR）（dB）**:
   - 信号強度とノイズレベルの差
   - 20 dB以上が推奨

4. **Ping時間（ms）**:
   - 低いほど良い（10 ms未満が理想的）

## データの解釈

### 温度
- 通常の室内環境: 18°C～25°C
- 快適範囲: 20°C～22°C

### 湿度
- 通常の室内環境: 30%～60%
- 快適範囲: 40%～50%
- 60%以上: 湿度が高い（カビの発生リスクあり）
- 30%未満: 湿度が低い（乾燥による不快感）

### 気圧
- 標準大気圧: 1013.25 hPa
- 高気圧: 1013 hPa以上（一般的に晴天）
- 低気圧: 1013 hPa未満（一般的に曇りや雨）

### ガス抵抗値
- 高い値: 空気が清浄
- 低い値: 揮発性有機化合物（VOC）などの汚染物質が存在

## トラブルシューティング

### P2デバイスがデータを送信していない
1. P2デバイスがRaspberry Pi 5のアクセスポイントに接続されていることを確認します
2. P2デバイスが正常に動作していることを確認します（電源、センサー接続など）
3. 接続モニターを使用して、P2デバイスとの接続品質を確認します

### Webインターフェースにアクセスできない
1. Raspberry Pi 5のIPアドレスが正しいことを確認します（デフォルトは192.168.0.1）
2. Webインターフェースサービスが実行中であることを確認します：
   ```bash
   ps aux | grep app_solo.py
   ```
3. ログを確認します：
   ```bash
   sudo cat /var/log/web_interface_solo.log
   ```

### データが古い、または更新されない
1. データ収集サービスが実行中であることを確認します：
   ```bash
   ps aux | grep data_collector_solo.py
   ```
2. ログを確認します：
   ```bash
   sudo cat /var/log/data_collector_solo.log
   ```
3. P2デバイスが正常にデータを送信していることを確認します

### グラフが表示されない
1. ブラウザのJavaScriptが有効になっていることを確認します
2. ブラウザのコンソールでエラーを確認します（F12キーを押してデベロッパーツールを開く）
3. データが存在することを確認します（CSVファイルを確認）：
   ```bash
   ls -la /var/lib/raspap_solo/data
   ```

## メンテナンス

### ログファイルの確認
各コンポーネントのログファイルは以下の場所にあります：
- アクセスポイント設定: `/var/log/ap_setup_solo.log`
- データ収集サービス: `/var/log/data_collector_solo.log`
- Webインターフェース: `/var/log/web_interface_solo.log`
- 接続モニター: `/var/log/wifi_monitor_solo.log`
- 統合スタートアップスクリプト: `/var/log/p1_startup_solo.log`

### データファイルの管理
環境データは以下の場所に保存されます：
```
/var/lib/raspap_solo/data/P2_YYYY-MM-DD.csv
```

古いデータファイルは自動的に管理されますが、手動でクリーンアップする場合は以下のコマンドを使用します：
```bash
find /var/lib/raspap_solo/data -name "P2_*.csv" -mtime +30 -delete
```
（この例では、30日以上前のファイルを削除します）

### システムの更新
システムを更新するには、最新のコードをダウンロードし、サービスを再起動します：
```bash
cd /path/to/RaspPi5_APconnection
git pull
sudo pkill -f start_p1_solo.py
cd p1_software_solo
source ~/envmonitor-venv/bin/activate
sudo ~/envmonitor-venv/bin/python3 start_p1_solo.py
```

## 高度な設定

### アクセスポイントの設定変更
アクセスポイントの設定（SSID、パスワードなど）を変更するには：
```bash
cd /path/to/RaspPi5_APconnection/p1_software_solo/ap_setup
source ~/envmonitor-venv/bin/activate
sudo ~/envmonitor-venv/bin/python3 ap_setup_solo.py --configure
```

### データ収集間隔の変更
P2デバイス側でデータ収集間隔を変更する必要があります。P2のコードを修正し、再デプロイしてください。

### Webインターフェースのポート変更
Webインターフェースのポートを変更するには：
```bash
cd /path/to/RaspPi5_APconnection/p1_software_solo
source ~/envmonitor-venv/bin/activate
sudo ~/envmonitor-venv/bin/python3 start_p1_solo.py --web-port 8080
```

### 接続モニターの間隔変更
接続モニターの監視間隔を変更するには：
```bash
cd /path/to/RaspPi5_APconnection/p1_software_solo
source ~/envmonitor-venv/bin/activate
sudo ~/envmonitor-venv/bin/python3 start_p1_solo.py --monitor-interval 10
```

## 付録

### データファイル形式
CSVファイルには以下の列があります：
- timestamp: データ収集時のタイムスタンプ（YYYY-MM-DD HH:MM:SS形式）
- device_id: デバイスID（P2）
- temperature: 温度（°C）
- humidity: 湿度（%）
- pressure: 気圧（hPa）
- gas_resistance: ガス抵抗値（Ω）

### APIエンドポイント一覧

#### データ収集API（ポート5001）
- `/api/latest`: すべてのデバイスの最新データを取得
- `/api/device/P2`: P2デバイスの最新データを取得
- `/api/graphs/P2`: P2デバイスのグラフデータを取得
- `/api/export/P2`: P2デバイスのデータをCSVとしてエクスポート

#### 接続モニターAPI（ポート5002）
- `/api/connection/latest`: すべてのデバイスの最新接続データを取得
- `/api/connection/device/P2`: P2デバイスの最新接続データを取得
- `/api/connection/history/P2`: P2デバイスの接続履歴を取得

## 更新履歴
- 1.0.0 (2025-06-30): 初回リリース

# Raspberry Pi Pico 2W Environmental Monitor Ver3.5.1

このディレクトリには、Raspberry Pi Pico 2W環境モニターのバージョン3.5.1のソースコードが含まれています。このバージョンでは、WiFi接続の問題と機器のリセット処理に関する改善が行われています。

## 主な変更点

### 1. WiFi接続の改善

- **接続タイムアウトの延長**: WiFi接続のタイムアウトを10秒から30秒に延長しました。これにより、接続の確立に十分な時間が確保されます。
- **接続状態の詳細なログ出力**: 接続プロセス中に5秒ごとに進捗状況を表示するようにしました。
- **再接続ロジックの改善**: 接続失敗時の再試行ロジックを改善し、最大3回まで再試行するようにしました。

### 2. リセット処理の改善

- **安全なリセット機能**: `safe_reset()`関数を追加し、リセット前にすべてのログとデータが保存されるようにしました。
- **リセット前の待機時間延長**: リセット前の待機時間を5秒から15秒に延長しました。これにより、Thonnyなどの開発環境がUSB接続の切断を適切に処理できるようになります。
- **リセットカウントダウン表示**: リセット前にカウントダウンを表示し、ユーザーに進行状況を知らせるようにしました。

### 3. エラー処理の改善

- **エラーログの拡張**: エラーログの最大保存数を10から20に増やし、より多くの履歴を保持できるようにしました。
- **ファイル同期処理の強化**: リセット前のファイル同期処理を強化し、データ損失のリスクを低減しました。
- **接続エラーの詳細な分類**: WiFi接続エラーをより詳細に分類し、適切な対応ができるようにしました。

## ファイル構成

- **main.py**: メインプログラム（WiFi接続とリセット処理の改善）
- **data_transmission/P2_wifi_client_solo.py**: WiFiクライアントモジュール（接続タイムアウトの設定可能化）
- **error_handling/P2_watchdog_solo.py**: エラー処理とウォッチドッグモジュール（安全なリセット処理）
- **sensor_drivers/bme680.py**: BME680センサードライバ
- **sensor_drivers/mhz19c.py**: MH-Z19C CO2センサードライバ

## 使用方法

1. すべてのファイルをRaspberry Pi Pico 2Wにコピーします。
2. Pico 2Wを再起動すると、改善されたWiFi接続とエラー処理で動作します。

## 注意事項

- WiFi接続に問題がある場合は、`main.py`の`WIFI_CONNECTION_TIMEOUT`と`MAX_WIFI_RETRIES`の値を調整してください。
- リセット前の待機時間を変更する場合は、`RESET_DELAY`の値を調整してください。

## 既知の問題

- 非常に不安定なWiFi環境では、接続の確立に時間がかかる場合があります。その場合は`WIFI_CONNECTION_TIMEOUT`の値を増やしてください。
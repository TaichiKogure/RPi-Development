# Raspberry Pi 環境モニタリングシステム Ver4.1 マニュアル

## 概要

このシステムは、Raspberry Pi 5（P1）をセンターハブとして、Raspberry Pi Pico 2W（P2およびP3）をセンサーノードとして使用する環境モニタリングシステムです。システムは温度、湿度、気圧、ガス抵抗値、CO2濃度などの環境データを収集し、可視化して分析のために保存します。

Ver4.1では、特にP3のWiFi接続タイムアウト問題に対する改善が実施されています。

## システム構成

1. **Raspberry Pi 5 (P1)**
   - P2およびP3のWiFiアクセスポイントとして機能
   - センサーノードからの環境データを収集・保存
   - データ可視化用のWebインターフェースを提供
   - センサーノードとの接続品質をモニタリング

2. **Raspberry Pi Pico 2W (P2, P3)**
   - BME680センサーで温度、湿度、気圧、ガス抵抗値を測定
   - MH-Z19CセンサーでCO2濃度を測定
   - WiFi経由でデータをP1に送信
   - エラー発生時や接続問題時に自動再起動

## Ver4.1での主な改善点

### P3の接続タイムアウト問題の解決

Ver4.0では、P3をThonny IDEで実行した際に、WiFi接続中にタイムアウトが発生し、デバイスがリセットされてThonnyとの接続が切断される問題がありました。Ver4.1では以下の改善を実施しています：

1. **起動時の遅延増加**
   - 初期起動遅延を5秒から10秒に増加し、ハードウェアが完全に初期化される時間を確保

2. **WiFi接続処理の改善**
   - 接続タイムアウトを30秒から45秒に延長
   - 最大再試行回数を3回から5回に増加
   - 再試行間の待機時間を段階的に増加（プログレッシブバックオフ）
   - 接続プロセス中の詳細なログ出力
   - WiFiステータスコードの表示機能追加（接続問題の診断に役立つ）

3. **リセット処理の改善**
   - リセット前の遅延を15秒から20秒に増加し、Thonnyがすべての出力を受信する時間を確保
   - リセット前のファイル同期処理を強化
   - リセットカウントダウン中の詳細なステータス表示
   - **開発モード用の自動リセット無効化機能**（Thonnyでの開発時に便利）

4. **エラー処理の強化**
   - より詳細なエラー分類と記録
   - エラー発生時の回復処理の改善
   - ウォッチドッグの給餌（feed）頻度の増加
   - エラー発生時に自動リセットせず、手動再起動を促すオプション

5. **センサードライバの改善**
   - BME680およびMH-Z19Cセンサードライバのエラー処理強化
   - 読み取り失敗時のリトライメカニズム追加
   - センサー状態のモニタリング機能追加

## インストール方法

### P1（Raspberry Pi 5）のセットアップ

1. Raspberry Pi 5に最新のRaspberry Pi OSをインストールします。

2. 仮想環境を作成し、必要なパッケージをインストールします：
   ```bash
   cd ~
   python3 -m venv envmonitor-venv
   source envmonitor-venv/bin/activate
   pip install flask flask-socketio pandas plotly
   ```

3. Ver4.1のファイルをRaspberry Pi 5の適切なディレクトリにコピーします。

4. アクセスポイントを設定します：
   ```bash
   sudo apt-get update
   sudo apt-get install -y dnsmasq hostapd
   ```

5. `p1_software_solo41/ap_setup/P1_ap_setup_solo.py`を実行してアクセスポイントを設定します：
   ```bash
   cd ~/RPi_Development01/Ver4.1/p1_software_solo41/ap_setup
   sudo python P1_ap_setup_solo.py
   ```

### P3（Raspberry Pi Pico 2W）のセットアップ

1. Raspberry Pi Pico 2WにMicroPythonファームウェアをインストールします。

2. ThonnyなどのIDEを使用して、Ver4.1のP3_software_solo41ディレクトリ内のすべてのファイルをPico 2Wにコピーします。

3. ファイル構造が以下のようになっていることを確認します：
   ```
   /main.py
   /data_transmission/P3_wifi_client_solo.py
   /error_handling/P3_watchdog_solo.py
   /sensor_drivers/bme680.py
   /sensor_drivers/mhz19c.py
   ```

4. BME680センサーとMH-Z19Cセンサーを正しくPico 2Wに接続します。

## 使用方法

### P1（Raspberry Pi 5）の起動

1. 仮想環境を有効化します：
   ```bash
   source ~/envmonitor-venv/bin/activate
   ```

2. 一括起動スクリプトを実行します：
   ```bash
   cd ~/RPi_Development01/Ver4.1/p1_software_solo41
   python start_p1_solo.py
   ```

3. 起動スクリプトは以下のサービスを順番に起動します：
   - アクセスポイント設定
   - データ収集サービス
   - Webインターフェース
   - 接続モニター

4. 各サービスの起動状態がコマンドプロンプトに表示されます。

### P3（Raspberry Pi Pico 2W）の起動

1. Pico 2Wに電源を接続すると、自動的に`main.py`が実行されます。

2. 起動時に以下の処理が行われます：
   - 10秒間の初期化待機
   - BME680センサーの初期化
   - MH-Z19Cセンサーの初期化
   - MH-Z19Cセンサーの30秒間のウォームアップ
   - WiFi接続（最大5回の再試行）
   - データ送信の開始

3. LEDの点滅パターンで動作状態を確認できます：
   - 単一の点滅：正常動作
   - 二重の点滅：データ送信失敗
   - 高速連続点滅：エラー発生またはリセット準備中

### Webインターフェースへのアクセス

1. スマートフォンやPCをRaspberry Pi 5のアクセスポイント（SSID: RaspberryPi5_AP_Solo）に接続します。

2. ブラウザで`http://192.168.0.1:5000`にアクセスします。

3. Webインターフェースでは以下の機能が利用できます：
   - P2およびP3からの環境データのリアルタイムグラフ表示
   - P2/P3の表示切り替え
   - データのCSVエクスポート
   - 接続状態の確認

## トラブルシューティング

### P3の接続問題

1. **Thonnyでの接続が切断される場合**
   - Ver4.1では接続タイムアウト処理が改善されていますが、それでも問題が発生する場合は、以下の対策を試してください：

     a. **自動リセットの無効化**：
     `main.py`の以下の行をコメントアウトして、自動リセットを無効化します：
     ```python
     # safe_reset(reason="WiFi connection failure")  # Commented out for Thonny development
     print("開発中のため自動リセットを停止中。手動で再起動してください。")
     while True:
         time.sleep(1)
         watchdog.feed()  # Keep feeding watchdog to prevent hardware reset
     ```

     b. **接続タイムアウトの延長**：
     `main.py`の`WIFI_CONNECTION_TIMEOUT`の値を45秒以上に増やしてみてください。

     c. **再試行回数の増加**：
     `main.py`の`MAX_WIFI_RETRIES`の値を5以上に増やしてみてください。

2. **WiFi接続が確立できない場合**
   - P1のアクセスポイントが正しく設定されているか確認してください。
   - P3とP1の距離を近づけてみてください。
   - WiFiステータスコードを確認してください（接続中に表示されます）：
     - `STAT_IDLE` (0): アイドル状態
     - `STAT_CONNECTING` (1): 接続中
     - `STAT_WRONG_PASSWORD` (2): パスワードが間違っている
     - `STAT_NO_AP_FOUND` (3): アクセスポイントが見つからない
     - `STAT_CONNECT_FAIL` (4): 接続失敗
     - `STAT_GOT_IP` (5): 接続成功（IPアドレス取得）
   - P3を再起動してみてください。

3. **センサーが検出されない場合**
   - 配線を確認してください。
   - I2Cアドレスが正しいか確認してください（BME680は通常0x77または0x76）。
   - I2Cバスのスキャン結果を確認してください（起動時に表示されます）。

### P1の問題

1. **アクセスポイントが起動しない場合**
   - `sudo systemctl status hostapd`と`sudo systemctl status dnsmasq`を実行して、サービスの状態を確認してください。
   - 必要に応じて`sudo systemctl restart hostapd`と`sudo systemctl restart dnsmasq`を実行してください。

2. **Webインターフェースにアクセスできない場合**
   - `ps aux | grep python`を実行して、Webアプリケーションが実行されているか確認してください。
   - `p1_software_solo41/web_interface/P1_app_solo.py`を手動で実行してエラーメッセージを確認してください。

## 変更履歴

### Ver4.1.1（2023年8月）
- P3のThonny開発時の接続問題に対する追加対策
- 自動リセット機能を一時的に無効化するオプションを追加
- WiFiステータスコードの詳細表示機能を追加
- エラー発生時に手動再起動を促すメッセージを追加
- トラブルシューティングガイドを拡充

### Ver4.1（2023年7月）
- P3のWiFi接続タイムアウト問題を解決
- 起動時の遅延を増加（5秒→10秒）
- WiFi接続タイムアウトを延長（30秒→45秒）
- 最大WiFi再試行回数を増加（3回→5回）
- リセット前の遅延を増加（15秒→20秒）
- エラー処理とログ記録を強化
- センサードライバのエラー処理を改善

### Ver4.0（2023年6月）
- P3（3台目のPico 2W）を追加
- P1でP2とP3の両方からデータを受信できるよう改良
- WebインターフェースでP2とP3のグラフを重ね書き可能に
- 絶対湿度の計算と表示機能を追加

### Ver3.5（2023年5月）
- MH-Z19C CO2センサーをP2に追加
- Webアプリのグラフ表示を改善
- グラフの縦軸範囲を調整可能に
- CO2グラフを追加

## 連絡先

問題や質問がある場合は、プロジェクト管理者にお問い合わせください。

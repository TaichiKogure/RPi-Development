# 環境データ測定システムトラブルシューティングガイド
バージョン: 2.0.0

このガイドでは、Raspberry Pi 5とPico 2W環境データ測定システムで発生する可能性のある一般的な問題に対する詳細なトラブルシューティング手順を提供します。

## 目次
1. [診断ツール](#診断ツール)
2. [P1（Raspberry Pi 5）の問題](#p1raspberry-pi-5の問題)
   - [起動の問題](#起動の問題)
   - [アクセスポイントの問題](#アクセスポイントの問題)
   - [データ収集の問題](#データ収集の問題)
   - [Webインターフェースの問題](#webインターフェースの問題)
   - [接続モニターの問題](#接続モニターの問題)
3. [P2/P3（Raspberry Pi Pico 2W）の問題](#p2p3raspberry-pi-pico-2wの問題)
   - [起動の問題](#pico起動の問題)
   - [センサーの問題](#センサーの問題)
   - [WiFi接続の問題](#wifi接続の問題)
   - [データ送信の問題](#データ送信の問題)
   - [エラーコード](#エラーコード)
4. [システム全体の問題](#システム全体の問題)
   - [データ同期の問題](#データ同期の問題)
   - [時刻同期の問題](#時刻同期の問題)
   - [パフォーマンスの問題](#パフォーマンスの問題)
5. [復旧手順](#復旧手順)
   - [P1の復旧](#p1の復旧)
   - [P2/P3の復旧](#p2p3の復旧)
   - [データの復旧](#データの復旧)

## 診断ツール
特定の問題のトラブルシューティングを行う前に、これらの診断ツールを使用してシステムの状態に関する情報を収集すると役立ちます。

### P1（Raspberry Pi 5）診断ツール
1. **システムログ**
   ```bash
   # システム起動ログを表示
   sudo journalctl -b

   # 特定のサービスのログを表示
   sudo journalctl -u hostapd
   sudo journalctl -u dnsmasq
   sudo journalctl -u data_collector.service
   sudo journalctl -u web_interface.service
   sudo journalctl -u wifi_monitor.service
   ```

2. **サービスステータス**
   ```bash
   # すべてのサービスのステータスを確認
   sudo systemctl status hostapd
   sudo systemctl status dnsmasq
   sudo systemctl status data_collector.service
   sudo systemctl status web_interface.service
   sudo systemctl status wifi_monitor.service
   ```

3. **ネットワーク診断**
   ```bash
   # ネットワークインターフェースを確認
   ifconfig

   # WiFiステータスを確認
   iwconfig

   # アクセスポイントのステータスを確認
   sudo iw dev wlan0 info

   # 接続されているクライアントを確認
   sudo iw dev wlan0 station dump
   ```

4. **システムリソース**
   ```bash
   # CPUとメモリ使用率を確認
   htop

   # ディスク容量を確認
   df -h

   # 温度を確認
   vcgencmd measure_temp
   ```

### P2/P3（Raspberry Pi Pico 2W）診断ツール
1. **Thonny IDEを介してPicoに接続**
   - Thonny IDEを開く
   - Pico 2Wに接続
   - REPLコンソールを使用して診断コマンドを実行

2. **基本診断**
   ```python
   # MicroPythonバージョンを確認
   import sys
   print(sys.version)

   # 利用可能なモジュールを確認
   help('modules')

   # ファイルシステムを確認
   import os
   print(os.listdir())

   # エラーログを確認
   with open('/error_log.txt', 'r') as f:
       print(f.read())
   ```

3. **ネットワーク診断**
   ```python
   # WiFiステータスを確認
   import network
   wlan = network.WLAN(network.STA_IF)
   print("接続状態:", wlan.isconnected())
   print("設定:", wlan.ifconfig())
   ```

4. **センサー診断**
   ```python
   # BME680センサーをテスト
   import sys
   sys.path.append('/sensor_drivers')
   import bme680_driver

   try:
       sensor = bme680_driver.BME680Sensor()
       readings = sensor.get_readings()
       print("BME680の読み取り値:", readings)
   except Exception as e:
       print("BME680エラー:", e)

   # MH-Z19Bセンサーをテスト
   import mhz19b_driver

   try:
       sensor = mhz19b_driver.MHZ19BSensor()
       co2 = sensor.read_co2()
       print("CO2レベル:", co2)
   except Exception as e:
       print("MH-Z19Bエラー:", e)
   ```

## P1（Raspberry Pi 5）の問題
### 起動の問題
1. **Raspberry Piが起動しない（電源LEDが点灯しない）**
   - 電源を確認（5V/3A以上が必要）
   - 別のUSB-Cケーブルを試す
   - 電源ポートの物理的な損傷を確認

2. **Raspberry Piの赤い電源LEDは点灯するが起動しない**
   - microSDカードが正しく挿入されているか確認
   - 別のmicroSDカードを試す
   - オペレーティングシステムを再インストール

3. **Raspberry Piは起動するがログインプロンプトに到達しない**
   - モニターを接続してエラーメッセージを確認
   - Escキーを押して起動メッセージを表示
   - 起動時にShiftキーを押し続けてリカバリーモードで起動を試みる

### アクセスポイントの問題
1. **アクセスポイントがWiFiリストに表示されない**
   - hostapdサービスが実行されているか確認：
     ```bash
     sudo systemctl status hostapd
     ```
   - hostapdサービスを再起動：
     ```bash
     sudo systemctl restart hostapd
     ```
   - hostapd設定を確認：
     ```bash
     sudo cat /etc/hostapd/hostapd.conf
     ```
   - WiFiインターフェースが起動しているか確認：
     ```bash
     sudo ifconfig wlan0 up
     ```

2. **アクセスポイントに接続できない**
   - パスワードが正しいことを確認
   - DHCPサーバーが実行されているか確認：
     ```bash
     sudo systemctl status dnsmasq
     ```
   - DHCPサーバーを再起動：
     ```bash
     sudo systemctl restart dnsmasq
     ```
   - IPアドレスの競合を確認

3. **アクセスポイントが頻繁に切断される**
   - 他のWiFiネットワークからの干渉を確認
   - hostapd.confでチャンネルを変更してみる
   - システム温度を確認（過熱するとWiFiに問題が発生する可能性がある）
   - Raspberry Piファームウェアを更新：
     ```bash
     sudo rpi-update
     ```

### データ収集の問題
1. **データコレクターサービスが実行されていない**
   - サービスのステータスを確認：
     ```bash
     sudo systemctl status data_collector.service
     ```
   - エラーログを確認：
     ```bash
     sudo journalctl -u data_collector.service -n 100
     ```
   - サービスを再起動：
     ```bash
     sudo systemctl restart data_collector.service
     ```

2. **P2/P3からデータが受信されない**
   - P2/P3デバイスがWiFiネットワークに接続されているか確認：
     ```bash
     sudo iw dev wlan0 station dump
     ```
   - データコレクターが正しいポートでリッスンしているか確認：
     ```bash
     sudo netstat -tuln | grep 5000
     ```
   - ファイアウォール設定を確認：
     ```bash
     sudo iptables -L
     ```

3. **データファイルが作成されない**
   - データディレクトリの権限を確認：
     ```bash
     ls -la /var/lib(FromThonny)/raspap/data
     ```
   - データディレクトリが存在することを確認：
     ```bash
     sudo mkdir -p /var/lib(FromThonny)/raspap/data
     sudo chown -R pi:pi /var/lib(FromThonny)/raspap/data
     ```
   - ディスク容量を確認：
     ```bash
     df -h
     ```

### Webインターフェースの問題
1. **Webインターフェースにアクセスできない**
   - Webインターフェースサービスが実行されているか確認：
     ```bash
     sudo systemctl status web_interface.service
     ```
   - サービスが正しいポートでリッスンしているか確認：
     ```bash
     sudo netstat -tuln | grep 80
     ```
   - Webインターフェースサービスを再起動：
     ```bash
     sudo systemctl restart web_interface.service
     ```

2. **Webインターフェースに「データがありません」と表示される**
   - データファイルが存在するか確認：
     ```bash
     ls -la /var/lib(FromThonny)/raspap/data
     ```
   - データコレクターが実行されデータを受信していることを確認
   - Webインターフェースのエラーログを確認：
     ```bash
     sudo journalctl -u web_interface.service -n 100
     ```

3. **グラフが正しく表示されない**
   - ブラウザのキャッシュをクリア
   - 別のブラウザを試す
   - 必要なJavaScriptライブラリが読み込まれているか確認（ブラウザコンソールを確認）
   - データ形式が正しいことを確認：
     ```bash
     head -n 10 /var/lib(FromThonny)/raspap/data/P2_*.csv
     ```

### 接続モニターの問題
1. **接続モニターがデータを表示しない**
   - 接続モニターサービスが実行されているか確認：
     ```bash
     sudo systemctl status wifi_monitor.service
     ```
   - 接続モニターサービスを再起動：
     ```bash
     sudo systemctl restart wifi_monitor.service
     ```
   - エラーログを確認：
     ```bash
     sudo journalctl -u wifi_monitor.service -n 100
     ```

2. **信号強度の読み取りが不正確**
   - P2/P3デバイスがWiFiネットワークに接続されていることを確認
   - 正しいMACアドレスがモニタリングされているか確認
   - P2/P3デバイスをP1に近づけて、読み取り値が改善するか確認

## P2/P3（Raspberry Pi Pico 2W）の問題
### Pico起動の問題
1. **Picoの電源が入らない（LEDが点灯しない）**
   - 別のUSBケーブルを試す
   - 別の電源を試す
   - USBポートの物理的な損傷を確認

2. **Picoの電源は入るがプログラムが実行されない**
   - Thonny IDEに接続してエラーを確認
   - main.pyがPicoに存在することを確認
   - MicroPythonが正しくインストールされているか確認

3. **Picoが繰り返しリセットされる**
   - エラーログを確認：
     ```python
     with open('/error_log.txt', 'r') as f:
         print(f.read())
     ```
   - ウォッチドッグのタイムアウトが短すぎないことを確認
   - ハードウェアの問題（不安定な電源供給）を確認

### センサーの問題
1. **BME680センサーが検出されない**
   - I2C接続（SDAとSCL）を確認
   - センサーに電源（3.3VとGND）が供給されていることを確認
   - 別のI2Cアドレス（0x76または0x77）を試す：
     ```python
     import sys
     sys.path.append('/sensor_drivers')
     import bme680_driver

     try:
         # 代替アドレスを試す
         sensor = bme680_driver.BME680Sensor(address=0x77)
         readings = sensor.get_readings()
         print("BME680の読み取り値:", readings)
     except Exception as e:
         print("BME680エラー:", e)
     ```

2. **MH-Z19Bセンサーが応答しない**
   - UART接続（TXとRX）を確認
   - センサーに5V電源が供給されていることを確認
   - 別のUART IDまたはピンを試す：
     ```python
     import sys
     sys.path.append('/sensor_drivers')
     import mhz19b_driver

     try:
         # 代替UART設定を試す
         sensor = mhz19b_driver.MHZ19BSensor(uart_id=0, tx_pin=0, rx_pin=1)
         co2 = sensor.read_co2()
         print("CO2レベル:", co2)
     except Exception as e:
         print("MH-Z19Bエラー:", e)
     ```

3. **センサーの読み取り値が範囲外**
   - センサーが適切に校正されているか確認
   - センサーが極端な条件にさらされていないことを確認
   - MH-Z19Bの場合、ゼロポイントの校正を試す：
     ```python
     import sys
     sys.path.append('/sensor_drivers')
     import mhz19b_driver

     sensor = mhz19b_driver.MHZ19BSensor()
     sensor.calibrate_zero_point()
     ```

### WiFi接続の問題
1. **WiFiネットワークに接続できない**
   - SSIDとパスワードが正しいことを確認
   - Raspberry Pi 5のアクセスポイントが実行されているか確認
   - Picoをアクセスポイントに近づけてみる
   - WiFiステータスを確認：
     ```python
     import network
     wlan = network.WLAN(network.STA_IF)
     wlan.active(True)
     print("ネットワークのスキャン:")
     for network in wlan.scan():
         print(network[0].decode(), network[3])
     ```

2. **WiFi接続が頻繁に切断される**
   - 信号強度を確認：
     ```python
     import network
     wlan = network.WLAN(network.STA_IF)
     print("RSSI:", wlan.status('rssi'))
     ```
   - Picoをアクセスポイントに近づける
   - 他のデバイスからの干渉を確認
   - 電源が安定していることを確認

### データ送信の問題
1. **P1にデータが送信されない**
   - PicoがWiFiに接続されているか確認
   - サーバーのIPとポートが正しいことを確認
   - 接続をテスト：
     ```python
     import socket

     try:
         s = socket.socket()
         s.connect(('192.168.0.1', 5000))
         s.send(b'{"test": true}')
         response = s.recv(1024)
         print("応答:", response)
         s.close()
     except Exception as e:
         print("接続エラー:", e)
     ```

2. **サーバーがデータを拒否する**
   - データ形式を確認
   - 必要なフィールドがすべて含まれていることを確認
   - P1のデータコレクターログでエラーメッセージを確認

### エラーコード
Pico 2WデバイスはLEDの点滅パターンを使用してエラーコードを示します：

1. **1回点滅**: センサーエラー（BME680）
   - BME680の接続を確認
   - センサーが損傷していないことを確認
   - センサーの再初期化を試みる

2. **2回点滅**: WiFiエラー
   - WiFi認証情報を確認
   - アクセスポイントが実行されていることを確認
   - Picoをアクセスポイントに近づける

3. **3回点滅**: メモリエラー
   - Picoを再起動
   - コード内のメモリリークを確認
   - プログラムの複雑さを減らす

4. **4回点滅**: タイムアウトエラー
   - 遅い操作を確認
   - タイムアウト値を増やす
   - ウォッチドッグのタイムアウトが十分であることを確認

5. **9回点滅**: 不明なエラー
   - 詳細についてエラーログを確認
   - Picoを再起動
   - ソフトウェアを再インストール

## システム全体の問題
### データ同期の問題
1. **データのタイムスタンプが一致しない**
   - Raspberry Pi 5の時計が正しいか確認：
     ```bash
     date
     ```
   - 自動時刻同期のためにNTPを設定：
     ```bash
     sudo apt install -y ntp
     sudo systemctl enable ntp
     sudo systemctl start ntp
     ```
   - 必要に応じて時刻を手動で調整：
     ```bash
     sudo date -s "YYYY-MM-DD HH:MM:SS"
     ```

2. **データポイントの欠落**
   - P2/P3デバイスが一貫して接続されているか確認
   - データ収集間隔が正しく設定されているか確認
   - データ送信プロセスのエラーを確認

### 時刻同期の問題
1. **システム時刻が不正確**
   - NTPを使用するためにRaspberry Pi 5をインターネットに接続
   - インターネットが利用できない場合はローカルNTPサーバーを設定
   - 正確な時刻管理のためにリアルタイムクロック（RTC）モジュールを使用

2. **時間が徐々にずれる**
   - より良い時刻同期のためにchronyをインストールして設定：
     ```bash
     sudo apt install -y chrony
     sudo systemctl enable chronyd
     sudo systemctl start chronyd
     ```
   - Raspberry Pi 5にバッテリーバックアップ付きRTCモジュールを追加

### パフォーマンスの問題
1. **システムの動作が遅い**
   - CPUとメモリ使用率を確認：
     ```bash
     htop
     ```
   - 過剰なリソースを使用しているプロセスを確認：
     ```bash
     ps aux --sort=-%cpu | head -10
     ```
   - ディスクI/Oを確認：
     ```bash
     iostat -x 1
     ```

2. **Webインターフェースの読み込みが遅い**
   - グラフに表示されるデータポイントの数を減らす
   - データストレージ形式を最適化
   - クライアントとサーバー間のネットワークパフォーマンスを確認

3. **CPU温度が高い**
   - 温度を確認：
     ```bash
     vcgencmd measure_temp
     ```
   - 冷却を改善（ヒートシンクやファンを追加）
   - サービスを最適化してCPU使用率を減らす

## 復旧手順
### P1の復旧
1. **重要なデータのバックアップ**
   ```bash
   # データファイルのバックアップを作成
   sudo tar -czvf ~/data_backup.tar.gz /var/lib(FromThonny)/raspap/data

   # 設定ファイルのバックアップ
   sudo tar -czvf ~/config_backup.tar.gz /etc/hostapd /etc/dnsmasq.conf /etc/dhcpcd.conf
   ```

2. **オペレーティングシステムの再インストール**
   - 最新のRaspberry Pi OSイメージをダウンロード
   - Raspberry Pi Imagerを使用してイメージをmicroSDカードに書き込み
   - 新しいmicroSDカードから起動

3. **設定の復元**
   - バックアップファイルをRaspberry Piにコピー
   - 設定ファイルを展開：
     ```bash
     sudo tar -xzvf ~/config_backup.tar.gz -C /
     ```
   - 必要なパッケージとサービスを再インストール
   - データファイルを復元：
     ```bash
     sudo mkdir -p /var/lib(FromThonny)/raspap/data
     sudo tar -xzvf ~/data_backup.tar.gz -C /
     ```

### P2/P3の復旧
1. **工場出荷状態にリセット**
   - 電源を接続しながらBOOTSELボタンを押し続ける
   - PicoはUSBドライブとして表示される
   - MicroPython UF2ファイルをドライブにコピー

2. **ソフトウェアの再インストール**
   - Thonny IDEを使用してPicoに接続
   - 必要なディレクトリを作成
   - すべてのプロジェクトファイルをアップロード

3. **設定の再構成**
   - main.pyファイルを編集して、正しいデバイスIDとWiFi認証情報を設定
   - センサーとWiFi接続をテスト
   - データが正しく送信されていることを確認

### データの復旧
1. **バックアップからの復旧**
   - 最新のバックアップを見つける
   - データファイルを展開：
     ```bash
     sudo tar -xzvf ~/environmental_data_backup_YYYYMMDD.tar.gz -C /tmp
     ```
   - ファイルをデータディレクトリにコピー：
     ```bash
     sudo cp -r /tmp/var/lib(FromThonny)/raspap/data/* /var/lib(FromThonny)/raspap/data/
     ```

2. **破損したCSVファイルの修復**
   - 破損したファイルを確認：
     ```bash
     find /var/lib(FromThonny)/raspap/data -name "*.csv" -exec file {} \;
     ```
   - 必要に応じてCSVヘッダーを修正：
     ```bash
     for f in /var/lib(FromThonny)/raspap/data/*.csv; do
       if ! head -1 "$f" | grep -q "timestamp"; then
         echo "timestamp,device_id,temperature,humidity,pressure,gas_resistance,co2_level" > /tmp/header
         cat "$f" >> /tmp/header
         mv /tmp/header "$f"
       fi
     done
     ```

3. **データファイルの結合**
   - 複数の部分的なデータファイルがある場合、それらを結合できます：
     ```bash
     # まず、すべてのファイルにヘッダーがあることを確認
     for f in /var/lib(FromThonny)/raspap/data/P2_*.csv; do
       if ! head -1 "$f" | grep -q "timestamp"; then
         echo "timestamp,device_id,temperature,humidity,pressure,gas_resistance,co2_level" > /tmp/header
         cat "$f" >> /tmp/header
         mv /tmp/header "$f"
       fi
     done

     # 次に、ファイルを結合（最初のファイル以外のヘッダーをスキップ）
     head -1 "$(ls /var/lib(FromThonny)/raspap/data/P2_*.csv | head -1)" > /var/lib(FromThonny)/raspap/data/P2_merged.csv
     for f in /var/lib(FromThonny)/raspap/data/P2_*.csv; do
       tail -n +2 "$f" >> /var/lib(FromThonny)/raspap/data/P2_merged.csv
     done

     # タイムスタンプでソート
     sort -t, -k1,1 /var/lib(FromThonny)/raspap/data/P2_merged.csv > /var/lib(FromThonny)/raspap/data/P2_sorted.csv
     ```

このガイドで扱われていない問題が発生した場合や追加の支援が必要な場合は、[Raspberry Piのドキュメント](https://www.raspberrypi.org/documentation/)や[MicroPythonのドキュメント](https://docs.micropython.org/)を参照してください。

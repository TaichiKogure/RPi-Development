# Raspberry Pi Pico 2W 環境モニタリングシステム Ver4.20 デバッグ版

## 概要
このプロジェクトは、Raspberry Pi 5（P1）をセンターハブとし、Raspberry Pi Pico 2W（P2、P3）をセンサーノードとして使用する環境データ測定システムです。システムは温度、湿度、気圧、ガスパラメータ、CO2濃度などの環境データを収集し、可視化して分析のために保存します。

## Ver4.20での主な改善点
1. **BME680センサーのI2Cアドレス自動検出機能**
   - 0x76と0x77の両方のアドレスを自動的に検出し、正しいアドレスを使用
   - センサーが存在しない場合でもデタラメな値を返さないよう改善
   
2. **CO2センサー（MH-Z19C）の安定動作**
   - 起動時の初期化プロセスを改善
   - データ取得の信頼性向上
   
3. **WiFi接続の安定性向上**
   - 接続処理の例外処理を強化
   - バックグラウンド処理の最適化
   
4. **P1データ収集形式との互換性確保**
   - Ver4.0のP1データ収集形式に合わせたデータ送信

## 緊急対応マニュアル

### BME680センサーの問題と対応

#### 問題: I2Cアドレスの誤り
BME680センサーは0x76または0x77のI2Cアドレスを持ちますが、初期化時に間違ったアドレスを指定すると、センサーが実装されていても「デタラメな値」が返ることがあります。

#### 応急処置
1. **自動検出機能の使用**
   - Ver4.20では、BME680センサーのアドレスを自動検出する機能を実装しています
   - `main.py`の初期化部分で`address=None`を指定することで自動検出が有効になります

2. **手動での確認と設定**
   - 自動検出が失敗する場合は、以下の手順で手動確認できます:
   ```python
   import machine
   from machine import I2C, Pin
   i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=100000)
   devices = i2c.scan()
   print([hex(addr) for addr in devices])
   ```
   - 検出されたアドレスを確認し、`main.py`の`bme = BME680_I2C(i2c, address=0x76)`または`bme = BME680_I2C(i2c, address=0x77)`の部分を修正します

3. **センサー接続の物理的確認**
   - センサーの配線（VCC、GND、SCL、SDA）が正しく接続されているか確認します
   - 接続が緩んでいないか、ピンが曲がっていないか確認します

### CO2センサー（MH-Z19C）の問題と対応

#### 問題: センサーからのデータ取得失敗
CO2センサーが正しく初期化されていても、データが取得できない場合があります。

#### 応急処置
1. **ウォームアップ時間の確保**
   - CO2センサーは起動後、安定したデータを提供するまでに30秒以上のウォームアップ時間が必要です
   - `main.py`の`DEBUG_SENSOR_WARMUP`の値を増やすことで、ウォームアップ時間を延長できます

2. **UARTピン設定の確認**
   - CO2センサーは以下のピン接続を使用しています:
     - VCC（赤）→ VBUS（5V、ピン40）
     - GND（黒）→ GND（ピン38）
     - TX（緑）→ GP9（ピン12）
     - RX（青）→ GP8（ピン11）
   - `main.py`の`UART_TX_PIN`と`UART_RX_PIN`の値が正しいか確認します

3. **センサーの手動テスト**
   - 以下のコードでセンサーを直接テストできます:
   ```python
   from machine import UART, Pin
   import time
   
   uart = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))
   
   # CO2読み取りコマンド
   cmd = b'\xFF\x01\x86\x00\x00\x00\x00\x00\x79'
   
   # 送信
   uart.write(cmd)
   time.sleep(1)
   
   # 応答読み取り
   if uart.any():
       resp = uart.read(9)
       print(resp.hex())
       if len(resp) >= 9:
           co2 = (resp[2] << 8) | resp[3]
           print(f"CO2: {co2} ppm")
   ```

### WiFi接続の問題と対応

#### 問題: 接続失敗やThonnyでの接続切断
WiFi接続処理中にUSB接続が切断され、Thonnyが応答しなくなることがあります。

#### 応急処置
1. **デバッグモードでの実行**
   - `main.py`の`DEBUG_DISABLE_AUTO_RESET = True`に設定することで、接続失敗時の自動リセットを無効化できます
   - `DEBUG_WIFI_MAX_RETRIES`の値を小さくすることで、接続試行回数を減らせます

2. **接続タイムアウトの調整**
   - `connect_wifi()`関数の`max_retries`と`connection_timeout`パラメータを調整します
   - 例: `connect_wifi(client, max_retries=3, connection_timeout=30)`

3. **CPUスピードの削減**
   - `DEBUG_REDUCE_CPU_SPEED = True`に設定することで、CPUスピードを下げて安定性を向上させることができます

4. **WiFiクライアントの診断実行**
   - `client.run_network_diagnostics()`を実行して、WiFiネットワークの状態を診断できます

### データ送信の問題と対応

#### 問題: P1へのデータ送信失敗
センサーデータの取得に成功しても、P1へのデータ送信に失敗することがあります。

#### 応急処置
1. **P1のIPアドレスとポートの確認**
   - `main.py`の`SERVER_IP`と`SERVER_PORT`の値が正しいか確認します
   - デフォルト設定: `SERVER_IP = "192.168.0.1"`, `SERVER_PORT = 5000`

2. **送信リトライ回数の増加**
   - `client.send_data(data, max_retries=10)`のように、リトライ回数を増やすことができます

3. **P1側のデータ収集サービスの確認**
   - P1側でデータ収集サービスが実行されているか確認します
   - P1で`sudo systemctl status p1_data_collector_solo.service`を実行して状態を確認します

4. **手動でのデータ送信テスト**
   - 以下のコードで手動データ送信テストを実行できます:
   ```python
   import socket
   import ujson
   
   # テストデータ
   test_data = {
       "device_id": "P3",
       "temperature": 25.0,
       "humidity": 50.0,
       "pressure": 1013.25,
       "gas_resistance": 10000,
       "co2": 450
   }
   
   # 送信
   sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   sock.settimeout(10)
   sock.connect(("192.168.0.1", 5000))
   sock.send(ujson.dumps(test_data).encode())
   response = sock.recv(1024)
   sock.close()
   print(response)
   ```

## インストール方法

### P3（Raspberry Pi Pico 2W）へのインストール
1. Thonnyを起動し、Pico 2Wを接続します
2. 以下のファイルをPico 2Wにコピーします:
   - `main.py`
   - `sensor_drivers/bme680.py`
   - `sensor_drivers/mhz19c.py`
   - `data_transmission/P3_wifi_client_debug.py`
   - `error_handling/P3_watchdog_debug.py`
3. Pico 2Wをリセットして実行します

## トラブルシューティング

### エラーログの確認
- エラーログは`/error_log_p3_solo.txt`に保存されます
- Thonnyでこのファイルを開いて内容を確認できます

### LEDインジケーター
- **点灯**: WiFi接続成功
- **1回点滅**: データ送信成功
- **2回点滅**: WiFi接続試行中
- **10回速い点滅**: WiFi接続失敗
- **交互点滅**: センサーエラー

### 一般的な問題と解決策
1. **起動時にフリーズする**
   - Pico 2Wをリセットして再試行します
   - `DEBUG_STARTUP_DELAY`の値を増やして起動時間を延長します

2. **センサー値が異常**
   - センサーの接続を確認します
   - Pico 2Wをリセットして再試行します
   - センサードライバーの初期化パラメータを確認します

3. **WiFi接続が不安定**
   - P1（Raspberry Pi 5）とP3の距離を近づけます
   - 障害物を取り除きます
   - P1のアクセスポイント設定を確認します

## 連絡先
問題が解決しない場合は、システム管理者にお問い合わせください。
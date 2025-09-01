# Raspberry Pi Pico 2W (P2/P3) インストールガイド
バージョン: 2.0.0

このガイドでは、環境データ測定システムのセンサーノードとしてRaspberry Pi Pico 2Wデバイス（P2およびP3）をセットアップするための手順を説明します。

## 目次
1. [ハードウェア要件](#ハードウェア要件)
2. [MicroPythonのインストール](#micropythonのインストール)
3. [センサーの接続](#センサーの接続)
4. [ソフトウェアのインストール](#ソフトウェアのインストール)
5. [設定](#設定)
6. [テスト](#テスト)
7. [デプロイメント](#デプロイメント)
8. [トラブルシューティング](#トラブルシューティング)

## ハードウェア要件
- Raspberry Pi Pico 2W（2台、P2用とP3用）
- プログラミング用MicroUSBケーブル
- BME680環境センサー（2台）
- MH-Z19B CO2センサー（2台）
- ジャンパーワイヤー
- ブレッドボード（オプション、プロトタイピング用）
- 3.3V電源（USBから電源供給しない場合）
- ケース（オプション、保護用）

## MicroPythonのインストール
1. [公式ウェブサイト](https://micropython.org/download/rp2-pico-w/)から最新のMicroPythonファームウェアをダウンロードします。

2. BOOTSELボタンを押しながらRaspberry Pi Pico 2Wをコンピュータに接続します。
   - Picoは「RPI-RP2」という名前のUSBマスストレージデバイスとして表示されるはずです。

3. ダウンロードしたMicroPython UF2ファイルをRPI-RP2ドライブにドラッグ＆ドロップします。
   - Picoは自動的に再起動し、コンピュータから切断されます。
   - その後、シリアルデバイスとして再接続されます。

4. Thonny IDE（まだインストールされていない場合）をインストールします：
   - [Thonny IDE](https://thonny.org/)をコンピュータにダウンロードしてインストールします。
   - ThonnyはWindows、macOS、Linuxで利用できます。

5. ThonnyをRaspberry Pi Pico用に設定します：
   - Thonny IDEを開きます。
   - 「ツール」>「オプション」>「インタープリター」に移動します。
   - ドロップダウンメニューから「MicroPython（Raspberry Pi Pico）」を選択します。
   - Pico用の適切なCOMポートを選択します。
   - 「OK」をクリックします。

6. MicroPythonのインストールを確認します：
   - Thonnyシェル（下部パネル）にMicroPythonのウェルカムメッセージが表示されるはずです。
   - `print("Hello, World!")`のような簡単なコマンドを実行して、MicroPythonが動作していることを確認します。

## センサーの接続
### BME680センサーの接続（I2C）
BME680センサーを以下のピン接続を使用してRaspberry Pi Pico 2Wに接続します：

| BME680ピン | Pico 2Wピン |
|------------|-------------|
| VCC        | 3.3V（ピン36） |
| GND        | GND（ピン38） |
| SCL        | GP1（ピン2） |
| SDA        | GP0（ピン1） |

### MH-Z19B CO2センサーの接続（UART）
MH-Z19Bセンサーを以下のピン接続を使用してRaspberry Pi Pico 2Wに接続します：

| MH-Z19Bピン | Pico 2Wピン |
|-------------|-------------|
| VCC（赤）   | VBUS（5V、ピン40） |
| GND（黒）   | GND（ピン38） |
| TX（緑）    | GP9（ピン12） |
| RX（青）    | GP8（ピン11） |

> 注：MH-Z19Bは5V電源が必要です。PicoがUSB経由で電源供給されている場合は、VBUSピンから5Vを供給できます。外部電源を使用する場合は、MH-Z19B用に5Vを供給していることを確認してください。

## ソフトウェアのインストール
1. Pico 2Wにプロジェクトのディレクトリ構造を作成します：
   - Thonnyで「表示」>「ファイル」を選択してファイルブラウザを開きます。
   - 以下のディレクトリを作成します：
     - `/sensor_drivers`
     - `/data_transmission`
     - `/error_handling`

2. リポジトリからプロジェクトファイルをダウンロードするか、コンピュータからコピーします：
   - BME680ドライバー：`bme680_driver.py`
   - MH-Z19Bドライバー：`mhz19b_driver.py`
   - WiFiクライアント：`wifi_client.py`
   - ウォッチドッグ：`watchdog.py`
   - メインスクリプト：`main.py`

3. ファイルをPico 2Wの適切なディレクトリにアップロードします：
   - `/sensor_drivers/bme680_driver.py`
   - `/sensor_drivers/mhz19b_driver.py`
   - `/data_transmission/wifi_client.py`
   - `/error_handling/watchdog.py`
   - `/main.py`（ルートディレクトリに）

## 設定
1. Thonnyで`main.py`ファイルを開きます。

2. 特定のセットアップに合わせて設定パラメータを変更します：
   - 最初のPicoのデバイスIDを「P2」に、2番目のPicoのデバイスIDを「P3」に設定します。
   - WiFi設定をRaspberry Pi 5のアクセスポイントに合わせて設定します。
   - 異なる接続を使用した場合は、センサーピンを調整します。

3. P2デバイスの設定例：
   ```python
   # デバイス設定
   DEVICE_ID = "P2"  # 2番目のPicoの場合は"P3"に変更

   # WiFi設定
   WIFI_SSID = "RaspberryPi5_AP"
   WIFI_PASSWORD = "raspberry"
   SERVER_IP = "192.168.0.1"
   SERVER_PORT = 5000

   # センサーピン
   BME680_SCL_PIN = 1
   BME680_SDA_PIN = 0
   MHZ19B_UART_ID = 1
   MHZ19B_TX_PIN = 8
   MHZ19B_RX_PIN = 9

   # 送信間隔（秒）
   TRANSMISSION_INTERVAL = 30
   ```

4. 変更した`main.py`ファイルをPico 2Wに保存します。

5. 2番目のPico 2Wについても同じプロセスを繰り返し、デバイスIDを「P3」に変更します。

## テスト
1. Pico 2Wがまだコンピュータに接続されている状態で、Thonnyで`main.py`スクリプトを実行します：
   - 「実行」ボタンをクリックするか、F5キーを押します。
   - シェルの出力を監視して、以下を確認します：
     - センサーが正しく検出され、読み取られていること。
     - PicoがRaspberry Pi 5のWiFiネットワークに接続できること。
     - データが正常に送信されていること。

2. すべてが正常に動作している場合、次のような出力が表示されるはずです：
   ```
   Initializing sensors...
   BME680 sensor initialized
   MH-Z19B sensor initialized
   Connecting to WiFi network: RaspberryPi5_AP
   Connected to RaspberryPi5_AP
   IP address: 192.168.900.101
   Starting data transmission...
   Data sent successfully: {'temperature': 25.3, 'humidity': 45.2, 'pressure': 1013.25, 'gas_resistance': 12345, 'co2_level': 450, 'device_id': 'P2'}
   ```

3. Raspberry Pi 5のデータ収集ログを確認して、データが受信されていることを確認します：
   ```bash
   sudo journalctl -u data_collector.service -f
   ```

## デプロイメント
1. テストが完了したら、Pico 2Wをコンピュータから切断します。

2. スタンドアロン操作のために、Pico 2Wに以下の方法で電源を供給できます：
   - USB電源アダプター
   - USB出力付きバッテリーパック
   - VSYSとGNDピンに接続された外部3.3V電源

3. Pico 2Wの電源が入ると、自動的に`main.py`スクリプトを実行し、データの収集と送信を開始します。

4. Pico 2Wを最終的な場所に配置し、以下を確認します：
   - Raspberry Pi 5のWiFiネットワークの範囲内にあること。
   - センサーが正確な読み取りのために適切に配置されていること。
   - 電源が安定して信頼性があること。

## トラブルシューティング
### センサー接続の問題
- **BME680が検出されない：**
  - I2C接続（SDAとSCL）を確認します。
  - センサーに電源（3.3VとGND）が供給されていることを確認します。
  - 可能であれば別のBME680センサーを試してみてください。

- **MH-Z19Bが応答しない：**
  - UART接続（TXとRX）を確認します。
  - センサーに5V電源が供給されていることを確認します。
  - MH-Z19Bは電源投入後約3分間のウォームアップ期間が必要です。

### WiFi接続の問題
- **WiFiに接続できない：**
  - Raspberry Pi 5のアクセスポイントが動作していることを確認します。
  - 設定のSSIDとパスワードを確認します。
  - Pico 2Wがアクセスポイントの範囲内にあることを確認します。
  - Pico 2WとRaspberry Pi 5の両方をリセットしてみてください。

- **接続が頻繁に切断される：**
  - Pico 2WをRaspberry Pi 5の近くに移動します。
  - 干渉源を確認します。
  - 電源が安定していることを確認します。

### データ送信の問題
- **サーバーがデータを受信していない：**
  - サーバーのIPとポートが正しいことを確認します。
  - Raspberry Pi 5でデータコレクターサービスが実行されていることを確認します。
  - 送信されるデータの形式を確認します。

### 一般的な問題
- **Pico 2Wが起動しない：**
  - 別のUSBケーブルまたは電源を試してみてください。
  - BOOTSELボタンを押しながら電源を接続してブートローダーモードに入り、MicroPythonを再インストールします。

- **スクリプトエラー：**
  - Pico 2WをThonnyに接続し、エラーメッセージを確認します。
  - 必要なライブラリがすべてインストールされていることを確認します。
  - コードの構文エラーを確認します。

- **ウォッチドッグリセット：**
  - Pico 2Wが頻繁にリセットされる場合は、デバイスに保存されているエラーログを確認します。
  - Thonnyに接続し、`import os; print(os.listdir())`を実行してエラーログファイルが存在するかどうかを確認します。
  - エラーログファイルを開いて読み、リセットの原因を特定します。

より詳細なトラブルシューティングについては、[トラブルシューティングガイド](../troubleshooting/troubleshooting_guide_ja.md)を参照してください。

# Raspberry Pi Pico 2W BME680センサー利用マニュアル

## 概要

このプロジェクトは、Raspberry Pi Pico 2WとBME680環境センサーを使用して、温度、湿度、気圧、およびガス抵抗値を測定するためのものです。MicroPythonを使用して実装されており、5秒ごとにセンサーからデータを読み取り、表示します。

**バージョン**: 1.0  
**作成日**: 2025-07-27

## 必要なハードウェア

- Raspberry Pi Pico 2W
- BME680環境センサー（I2C接続）
- ジャンパーワイヤー
- USBケーブル（Pico 2Wとコンピュータを接続するため）

## 配線方法

BME680センサーをRaspberry Pi Pico 2Wに接続するには、以下の配線を行ってください：

| BME680ピン | Pico 2Wピン |
|------------|-------------|
| VCC        | 3.3V (Pin 36) |
| GND        | GND (Pin 38) |
| SCL        | GP1 (Pin 2) |
| SDA        | GP0 (Pin 1) |

![配線図](https://example.com/wiring_diagram.png)

**注意**: BME680センサーのI2Cアドレスは通常0x77または0x76です。プログラムは両方のアドレスを自動的に試行します。

## ソフトウェアのインストール

### 1. Thonnyのインストール

まだThonnyがインストールされていない場合は、[Thonnyの公式サイト](https://thonny.org/)からダウンロードしてインストールしてください。

### 2. Pico 2WにMicroPythonをインストール

1. Raspberry Pi Pico 2WをUSBケーブルでコンピュータに接続します。
2. BOOTSELボタンを押しながらPico 2Wを接続すると、ストレージデバイスとして認識されます。
3. [MicroPython公式サイト](https://micropython.org/download/rp2-pico-w/)から最新のMicroPythonファームウェア（.uf2ファイル）をダウンロードします。
4. ダウンロードしたファームウェアファイルをPico 2Wにドラッグ＆ドロップします。
5. Pico 2Wが自動的に再起動し、MicroPythonが実行可能になります。

### 3. プログラムファイルの転送

1. Thonnyを起動します。
2. 右下のインタープリタ選択で「MicroPython (Raspberry Pi Pico)」を選択します。
3. `bme680.py`と`ForPicoBME680Simple.py`の2つのファイルをThonnyで開きます。
4. 各ファイルを開いた状態で、「ファイル」→「保存」を選択し、「Raspberry Pi Pico」を選択して保存します。
5. 両方のファイルがPico 2Wに保存されていることを確認してください。

## プログラムの実行

1. Thonnyで`ForPicoBME680Simple.py`を開きます。
2. 「実行」ボタンをクリックするか、F5キーを押してプログラムを実行します。
3. Thonnyのシェルウィンドウに初期化情報とセンサーデータが表示されます。
4. プログラムを停止するには、「停止」ボタンをクリックするか、Ctrl+Cを押します。

## プログラムの動作

プログラムが正常に実行されると、以下のような情報が表示されます：

```
===== BME680 Environmental Data Monitor for Pico 2W =====
Version: 1.0
Reading data from BME680 sensor every 5 seconds
Press Ctrl+C to exit
======================================================
Initializing I2C bus...
I2C devices found: ['0x77']
Initializing BME680 sensor...
BME680 initialized with address 0x77
Waiting for sensor to stabilize...
Initialization complete. Starting data collection...
[1] 2025-07-27 16:30:00
  Temperature: 25.32 °C
  Humidity: 45.67 %
  Pressure: 1013.25 hPa
  Gas Resistance: 12345 Ω
----------------------------------------
```

プログラムは5秒ごとにセンサーからデータを読み取り、表示します。測定中はPico 2Wのオンボード LEDが点灯します。

## 自動起動の設定

Pico 2Wが電源に接続されたときに自動的にプログラムを実行するには：

1. `ForPicoBME680Simple.py`を`main.py`という名前でPico 2Wに保存します。
2. Pico 2Wを再起動すると、自動的にプログラムが実行されます。

## トラブルシューティング

### I2Cデバイスが見つからない場合

```
No I2C devices found. Check connections.
```

このエラーが表示される場合：

1. BME680センサーとPico 2Wの接続を確認してください。
2. 配線が正しいことを確認してください（特にSCLとSDAの接続）。
3. センサーに電源が供給されていることを確認してください（VCCとGND）。

### センサーの初期化に失敗する場合

```
Failed to initialize with address 0x77: ...
Trying with address 0x76...
Failed to initialize with address 0x76: ...
```

このエラーが表示される場合：

1. センサーのI2Cアドレスが0x77または0x76であることを確認してください。
2. センサーが正常に動作していることを確認してください。
3. I2Cバスに他のデバイスがないことを確認してください。

### データ読み取りエラー

```
Error during data reading: ...
```

このエラーが表示される場合：

1. センサーの接続が安定していることを確認してください。
2. Pico 2Wを再起動してみてください。
3. センサーが正常に動作していることを確認してください。

## LEDステータスインジケーター

- **点灯**: 測定中
- **高速点滅**: エラーが発生し、再試行中

## プログラムのカスタマイズ

### 測定間隔の変更

測定間隔を変更するには、`ForPicoBME680Simple.py`の以下の行を編集します：

```python
# 5秒から10秒に変更する例
time.sleep(10)
```

### デバッグモードの有効化

より詳細な情報を表示するには、`bme680.py`の初期化部分を編集します：

```python
# デバッグを有効にする
bme = BME680_I2C(i2c, address=0x77, debug=True)
```

## 技術的な詳細

### BME680センサーについて

BME680は、温度、湿度、気圧、およびガス（空気質）を測定できる環境センサーです。I2Cインターフェースを使用して通信します。

- 温度測定範囲: -40〜85°C
- 湿度測定範囲: 0〜100%
- 気圧測定範囲: 300〜1100 hPa
- ガス測定: 空気中の揮発性有機化合物（VOC）を検出

### Raspberry Pi Pico 2Wについて

Raspberry Pi Pico 2Wは、RP2040マイクロコントローラーを搭載した小型のマイクロコントローラーボードで、Wi-Fi接続機能を備えています。

- デュアルコアARM Cortex M0+プロセッサ（最大133MHz）
- 264KB RAM
- 2MB フラッシュメモリ
- Wi-Fi 802.11n
- Bluetooth 5.2

## 参考資料

- [Raspberry Pi Pico 2W 公式ドキュメント](https://www.raspberrypi.com/documentation/microcontrollers/raspberry-pi-pico.html)
- [MicroPython 公式ドキュメント](https://docs.micropython.org/)
- [BME680 データシート](https://www.bosch-sensortec.com/products/environmental-sensors/gas-sensors/bme680/)

## ライセンス

このプロジェクトは、MITライセンスの下で公開されています。詳細については、LICENSEファイルを参照してください。

## 作者

JetBrains

## 更新履歴

- **1.0** (2025-07-27): 初回リリース
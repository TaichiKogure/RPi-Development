# Raspberry Pi Pico 2W Solo Version (P2_software_solo2)

## 概要 (Overview)
このパッケージは、Raspberry Pi Pico 2W (P2) 用のソロバージョンソフトウェアです。BME680センサーを使用して環境データ（温度、湿度、気圧、ガス抵抗）を測定し、Raspberry Pi 5 (P1) に送信します。このバージョンでは、BME680センサードライバーが改良され、より正確なガス測定が可能になりました。

This package contains the Solo version software for Raspberry Pi Pico 2W (P2). It measures environmental data (temperature, humidity, pressure, gas resistance) using a BME680 sensor and transmits it to the Raspberry Pi 5 (P1). This version includes improvements to the BME680 sensor driver for more accurate gas measurements.

## バージョン (Version)
2.0.1-solo

## 機能 (Features)
- BME680センサーによる環境データの測定
- 改良されたガス測定機能（ヒーター制御の最適化）
- WiFi経由でのP1への定期的なデータ送信
- エラー処理と自動リカバリー機能
- LEDによるステータス表示

- Environmental data measurement using BME680 sensor
- Improved gas measurement with optimized heater control
- Periodic data transmission to P1 via WiFi
- Error handling and automatic recovery
- LED status indication

## 主な改良点 (Key Improvements)
- BME680センサーのアドレスを0x77に変更（一部のセンサーモジュールに対応）
- ガス測定用のヒーターを有効にする設定を追加
- ヒーターの温度制御を改良（0〜255の範囲に制限）
- 周囲温度（ambient temperature）のデフォルト値を設定

- Changed BME680 sensor address to 0x77 (compatible with some sensor modules)
- Added configuration to enable heater for gas measurement
- Improved heater temperature control (limited to 0-255 range)
- Set default value for ambient temperature

## ディレクトリ構造 (Directory Structure)
```
P2_software_solo2/
├── data_transmission/       # データ送信モジュール
│   └── wifi_client_solo.py  # WiFiクライアント
├── error_handling/          # エラー処理モジュール
│   └── watchdog_solo.py     # ウォッチドッグタイマーと自動リカバリー
├── sensor_drivers/          # センサードライバーモジュール
│   └── bme680_driver_solo.py # 改良されたBME680センサードライバー
├── main.py                  # メインランチャー
├── main_solo.py             # メインプログラム
└── README.md                # このファイル
```

## 設定 (Configuration)
主な設定は `main_solo.py` ファイルで行います：

The main configuration is done in the `main_solo.py` file:

```python
# Device configuration
DEVICE_ID = "P2"  # Solo version uses P2

# WiFi configuration
WIFI_SSID = "RaspberryPi5_AP_Solo"
WIFI_PASSWORD = "raspberry"
SERVER_IP = "192.168.0.1"
SERVER_PORT = 5000

# Sensor pins
BME680_SCL_PIN = 1
BME680_SDA_PIN = 0

# Transmission interval (seconds)
TRANSMISSION_INTERVAL = 30
```

## インストール方法 (Installation)
1. Raspberry Pi Pico 2WにMicroPythonをインストールします
2. このディレクトリの内容をPico 2Wのルートディレクトリにコピーします
3. Pico 2Wを再起動すると、自動的にプログラムが実行されます

1. Install MicroPython on the Raspberry Pi Pico 2W
2. Copy the contents of this directory to the root directory of the Pico 2W
3. Restart the Pico 2W, and the program will run automatically

## 接続方法 (Connection)
BME680センサーは以下のように接続します：

Connect the BME680 sensor as follows:

- BME680 VCC → Pico 2W 3.3V
- BME680 GND → Pico 2W GND
- BME680 SCL → Pico 2W GP1 (SCL_PIN)
- BME680 SDA → Pico 2W GP0 (SDA_PIN)

## P1との互換性 (Compatibility with P1)
このソフトウェアは、P1_software_soloパッケージと互換性があります。P1のIPアドレスは192.168.0.1に設定されています。

This software is compatible with the P1_software_solo package. The P1 IP address is set to 192.168.0.1.

## エラー処理 (Error Handling)
エラーが発生した場合、以下の動作を行います：
1. エラーログに記録
2. LEDでエラーコードを点滅表示
3. 一定回数エラーが発生した場合、デバイスを自動的に再起動

In case of errors, the system will:
1. Log the error
2. Blink the LED to indicate the error code
3. Automatically restart the device if errors occur a certain number of times

## LEDステータス表示 (LED Status Indication)
- 起動時：LEDが点灯
- データ送信成功時：LEDが短く点滅
- エラー発生時：エラーコードに応じた回数の点滅
- リセット前：素早く5回点滅

- At startup: LED turns on
- When data is sent successfully: LED blinks briefly
- When an error occurs: LED blinks according to the error code
- Before reset: LED blinks rapidly 5 times

## エラーコード (Error Codes)
- 1回点滅：センサーエラー
- 2回点滅：WiFiエラー
- 3回点滅：メモリエラー
- 4回点滅：タイムアウトエラー
- 9回点滅：不明なエラー

- 1 blink: Sensor error
- 2 blinks: WiFi error
- 3 blinks: Memory error
- 4 blinks: Timeout error
- 9 blinks: Unknown error

## テスト (Testing)
テスト用のスクリプト `test_solo.py` が含まれています。このスクリプトは、ハードウェアをモックして、ソフトウェアの動作をシミュレートします。

A test script `test_solo.py` is included. This script mocks the hardware to simulate the behavior of the software.

## 注意事項 (Notes)
- このソフトウェアは、P1_software_soloパッケージと組み合わせて使用することを前提としています
- P1のIPアドレスが変更された場合は、`main_solo.py`の`SERVER_IP`を更新する必要があります
- BME680センサーのアドレスが0x76の場合は、`sensor_drivers/bme680_driver_solo.py`の`__init__`メソッドのアドレスパラメータを変更してください

- This software is designed to be used in combination with the P1_software_solo package
- If the P1 IP address is changed, the `SERVER_IP` in `main_solo.py` needs to be updated
- If your BME680 sensor has an address of 0x76, change the address parameter in the `__init__` method of `sensor_drivers/bme680_driver_solo.py`
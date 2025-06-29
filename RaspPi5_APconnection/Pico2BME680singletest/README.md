# BME680 Simple Test Program for Raspberry Pi Pico 2W

## 概要 (Overview)
このプログラムは、Raspberry Pi Pico 2WとBME680センサーを使用して、環境データ（温度、湿度、気圧、ガス抵抗）を測定し、Thonnyコンソールに表示する最もシンプルなテストプログラムです。WiFi機能は使用せず、センサーの動作確認のみを目的としています。

This program is the simplest test program for measuring environmental data (temperature, humidity, pressure, gas resistance) using a Raspberry Pi Pico 2W and BME680 sensor, and displaying it in the Thonny console. It does not use WiFi functionality and is intended only for verifying sensor operation.

## 機能 (Features)
- BME680センサーの初期化
- 温度、湿度、気圧、ガス抵抗の測定
- 測定データのThonnyコンソールへの表示
- LEDによる動作状態の表示

- BME680 sensor initialization
- Temperature, humidity, pressure, and gas resistance measurement
- Display of measurement data in the Thonny console
- LED indication of operation status

## 必要条件 (Requirements)
- Raspberry Pi Pico 2W
- BME680センサー
- MicroPython（Pico 2W用）
- Thonny IDE

## 接続方法 (Connection)
BME680センサーは以下のように接続します：

Connect the BME680 sensor as follows:

- BME680 VCC → Pico 2W 3.3V
- BME680 GND → Pico 2W GND
- BME680 SCL → Pico 2W GP1
- BME680 SDA → Pico 2W GP0

## 使用方法 (Usage)
1. Raspberry Pi Pico 2WにMicroPythonをインストールします
2. Thonny IDEを開き、Pico 2Wに接続します
3. `bme680_test.py`ファイルをPico 2Wにコピーします
4. プログラムを実行すると、センサーからのデータがThonnyコンソールに表示されます
5. Ctrl+Cを押すと、プログラムが停止します

1. Install MicroPython on the Raspberry Pi Pico 2W
2. Open Thonny IDE and connect to the Pico 2W
3. Copy the `bme680_test.py` file to the Pico 2W
4. Run the program, and sensor data will be displayed in the Thonny console
5. Press Ctrl+C to stop the program

## 出力例 (Example Output)
```
BME680 Simple Test Program for Raspberry Pi Pico 2W
==================================================
Initializing BME680 sensor...
BME680 sensor initialized successfully!

Reading sensor data continuously. Press Ctrl+C to stop.
--------------------------------------------------

BME680 Sensor Readings:
Temperature: 25.21 °C
Pressure: 1013.25 hPa
Humidity: 45.70 %
Gas Resistance: 12500.00 Ohms
```

## 注意事項 (Notes)
- このプログラムはWiFi機能を使用しないシンプルなテストプログラムです
- センサーの初期化に失敗した場合は、接続を確認してください
- ガス抵抗の測定には数分かかる場合があります

- This is a simple test program that does not use WiFi functionality
- If sensor initialization fails, check the connections
- Gas resistance measurement may take a few minutes to stabilize
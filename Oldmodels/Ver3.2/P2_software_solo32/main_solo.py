#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main_solo.py - Version 3.5.0-solo
- Wi-Fi RSSI表示対応
- センサー異常時LED3回点滅通知追加
- CYW43安定化、LED通知、エラー処理強化
- 送信リトライ機能強化（最大5回）
- エラー時ログ保存機能強化
"""

import sys
import time
import machine
import _thread
import network
from machine import Pin, I2C, Timer

sys.path.append('sensor_drivers')
sys.path.append('data_transmission')
sys.path.append('error_handling')

from bme680 import BME680_I2C
from P2_wifi_client_solo import WiFiClient, DataTransmitter
from P2_watchdog_solo import Watchdog, handle_error

# 設定
DEVICE_ID = "P2"
WIFI_SSID = "RaspberryPi5_AP_Solo"
WIFI_PASSWORD = "raspberry"
SERVER_IP = "192.168.0.1"
SERVER_PORT = 5000
TRANSMISSION_INTERVAL = 30
BME680_SCL_PIN = 1
BME680_SDA_PIN = 0
LED_PIN = 25

# グローバル
try:
    led = machine.Pin("LED", machine.Pin.OUT)
except (ValueError, OSError):
    # 特定の例外だけキャッチする
    led = machine.Pin(25, machine.Pin.OUT)  # Fallback

try:
    led_timer = Timer(-1)  # Timer IDを指定する例。環境に応じて変更
except Exception as e:
    # Timer初期化失敗時の処理（ログ出力や再試行など）
    led_timer = None
    print("Timer initialization failed:", e)

wdt = None
client = None
transmitter = None
bme680_sensor = None
wifi_connected = False
error_blink_count = 0
sensor_error = False
wifi_error = False


# ===== LED制御 =====
# LED状態の定義
# 1. WiFi接続中: 200ms間隔で点滅
# 2. WiFi未接続: 1000ms間隔で点滅
# 3. データ送信時: 短い点灯（200ms）
# 4. WiFiエラー: 2回連続点滅を繰り返す
# 5. センサーエラー: 3回連続点滅を繰り返す
# 6. 両方エラー: 4回連続点滅を繰り返す

def start_led_blink(interval_ms):
    """一定間隔でLEDを点滅させる"""
    def toggle_led(timer):
        led.toggle()
    led_timer.deinit()  # 既存のタイマーを停止
    led_timer.init(period=interval_ms, mode=Timer.PERIODIC, callback=toggle_led)

def stop_led_blink():
    """LEDの点滅を停止し、消灯する"""
    led_timer.deinit()
    led.off()

def led_status_wifi_disconnected():
    """WiFi未接続状態を表示（1秒間隔でゆっくり点滅）"""
    stop_led_blink()
    start_led_blink(1000)

def led_status_wifi_connected():
    """WiFi接続状態を表示（200ms間隔で速く点滅）"""
    stop_led_blink()
    start_led_blink(200)

def led_status_data_transmission():
    """データ送信を表示（一瞬点灯）"""
    current_state = led.value()  # 現在のLED状態を保存
    stop_led_blink()
    led.on()
    time.sleep_ms(200)
    led.off()

    # 元の状態に戻す
    if wifi_connected:
        start_led_blink(200)
    else:
        start_led_blink(1000)

def led_status_wifi_error():
    """WiFiエラーを表示（2回点滅パターン）"""
    def wifi_error_pattern(timer):
        global error_blink_count
        if error_blink_count < 2:
            led.toggle()
            error_blink_count += 1
        elif error_blink_count < 4:
            led.off()
            error_blink_count += 1
        else:
            error_blink_count = 0

    global error_blink_count
    error_blink_count = 0
    stop_led_blink()
    led_timer.init(period=200, mode=Timer.PERIODIC, callback=wifi_error_pattern)

def led_status_sensor_error():
    """センサーエラーを表示（3回点滅パターン）"""
    def sensor_error_pattern(timer):
        global error_blink_count
        if error_blink_count < 3:
            led.toggle()
            error_blink_count += 1
        elif error_blink_count < 6:
            led.off()
            error_blink_count += 1
        else:
            error_blink_count = 0

    global error_blink_count
    error_blink_count = 0
    stop_led_blink()
    led_timer.init(period=200, mode=Timer.PERIODIC, callback=sensor_error_pattern)

def led_status_combined_error():
    """WiFiとセンサーの両方のエラーを表示（4回点滅パターン）"""
    def combined_error_pattern(timer):
        global error_blink_count
        if error_blink_count < 4:
            led.toggle()
            error_blink_count += 1
        elif error_blink_count < 8:
            led.off()
            error_blink_count += 1
        else:
            error_blink_count = 0

    global error_blink_count
    error_blink_count = 0
    stop_led_blink()
    led_timer.init(period=200, mode=Timer.PERIODIC, callback=combined_error_pattern)

# ===== センサー初期化 =====
def initialize_sensors():
    global bme680_sensor, sensor_error
    print("Initializing BME680 sensor...")
    try:
        i2c = I2C(0, scl=Pin(BME680_SCL_PIN), sda=Pin(BME680_SDA_PIN), freq=100000)
        bme680_sensor = BME680_I2C(i2c, address=0x77)

        ctrl_gas = bme680_sensor._read_byte(0x71)
        ctrl_gas |= 0x10
        bme680_sensor._write(0x71, [ctrl_gas])

        print("BME680 sensor initialized")
        print(f"Temp: {bme680_sensor.temperature:.2f}°C, Humidity: {bme680_sensor.humidity:.2f}%, "
              f"Pressure: {bme680_sensor.pressure:.2f}hPa, Gas: {bme680_sensor.gas} ohms")
        sensor_error = False
        return True
    except Exception as e:
        print(f"Sensor init error: {e}")
        handle_error(e, {"component": "sensor_init"})
        sensor_error = True
        led_status_sensor_error()
        return False

# ===== Wi-Fi初期化 =====
def delayed_wifi_init():
    global client, transmitter, wifi_connected, wifi_error

    try:
        print("Delaying Wi-Fi init for stability...")
        print("Waiting 8 seconds for system stabilization...")
        time.sleep(8)  # Increased from 5 to 8 seconds for better stability

        wlan = network.WLAN(network.STA_IF)
        wlan.active(False)
        time.sleep(1)
        wlan.active(True)
        time.sleep(2)

        client = WiFiClient(
            ssid=WIFI_SSID,
            password=WIFI_PASSWORD,
            server_ip=SERVER_IP,
            server_port=SERVER_PORT,
            device_id=DEVICE_ID
        )

        transmitter = DataTransmitter(
            wifi_client=client,
            transmission_interval=TRANSMISSION_INTERVAL
        )
        transmitter.add_sensor("bme680", bme680_sensor)

        led_status_wifi_disconnected()

        for attempt in range(3):
            print(f"Connecting to Wi-Fi (try {attempt+1}/3)...")
            wlan.active(True)
            if client.connect():
                print("Wi-Fi connected.")
                wifi_connected = True
                wifi_error = False
                rssi = wlan.status('rssi')
                print(f"📶 RSSI: {rssi} dBm")

                # LEDステータス表示の更新
                if sensor_error:
                    led_status_combined_error()  # センサーエラーもある場合は複合エラー
                else:
                    led_status_wifi_connected()  # 正常接続
                return
            else:
                print("Connect failed. Retry in 5 sec...")
                time.sleep(5)

        print("Wi-Fi connection failed.")
        wifi_connected = False
        wifi_error = True

        # LEDステータス表示の更新
        if sensor_error:
            led_status_combined_error()  # センサーエラーもある場合は複合エラー
        else:
            led_status_wifi_error()  # WiFiエラーのみ

    except Exception as e:
        print(f"Wi-Fi init error: {e}")
        wifi_error = True

        # LEDステータス表示の更新
        if sensor_error:
            led_status_combined_error()  # センサーエラーもある場合は複合エラー
        else:
            led_status_wifi_error()  # WiFiエラーのみ

        handle_error(e, {"component": "wifi_init"})

# ===== データ送信 =====
def collect_and_send_data():
    global transmitter, wdt, sensor_error, wifi_error
    try:
        if wdt:
            wdt.feed()

        if transmitter is None:
            print("Wi-Fi not ready. Skipping send.")
            wifi_error = True

            # LEDステータス表示の更新
            if sensor_error:
                led_status_combined_error()
            else:
                led_status_wifi_error()

            return False

        # センサーデータ取得と送信を試みる
        try:
            success = transmitter.collect_and_send_data()

            if success:
                # 送信成功
                led_status_data_transmission()
                wifi_error = False
                return True
            else:
                # 送信失敗
                print("Data transmission failed after all retry attempts")
                wifi_error = True

                # LEDステータス表示の更新
                if sensor_error:
                    led_status_combined_error()
                else:
                    led_status_wifi_error()

                return False

        except Exception as e:
            # センサーエラーの可能性
            print(f"Sensor or transmission error: {e}")

            if "BME680" in str(e) or "I2C" in str(e):
                # センサー関連のエラー
                sensor_error = True

                # LEDステータス表示の更新
                if wifi_error:
                    led_status_combined_error()
                else:
                    led_status_sensor_error()
            else:
                # 通信関連のエラー
                wifi_error = True

                # LEDステータス表示の更新
                if sensor_error:
                    led_status_combined_error()
                else:
                    led_status_wifi_error()

            return False

    except Exception as e:
        print(f"Data send error: {e}")
        handle_error(e, {"component": "data_transmission"})

        # 一般的なエラー（WiFiエラーとして扱う）
        wifi_error = True

        # LEDステータス表示の更新
        if sensor_error:
            led_status_combined_error()
        else:
            led_status_wifi_error()

        return False

# ===== メイン関数 =====
def main():
    global wdt, sensor_error, wifi_error

    print("Starting P2 Environmental System v3.6.0")
    print(f"Device ID: {DEVICE_ID}")
    print("Waiting 3 sec for stabilization...")
    time.sleep(3)

    wdt = Watchdog(timeout_ms=10000)

    # センサー初期化
    if not initialize_sensors():
        print("Sensor error. Setting LED to sensor error mode.")
        sensor_error = True
        led_status_sensor_error()
        # センサーエラーでも継続して動作する（WiFi接続は試みる）
    else:
        print("Sensor initialized successfully.")
        sensor_error = False

    # WiFi初期化（別スレッドで実行）
    _thread.start_new_thread(delayed_wifi_init, ())

    print("Main loop start.")
    while True:
        try:
            # データ収集と送信
            result = collect_and_send_data()

            # エラー状態の表示
            if sensor_error and wifi_error:
                print("Status: Both sensor and WiFi have errors")
            elif sensor_error:
                print("Status: Sensor error, WiFi OK")
            elif wifi_error:
                print("Status: WiFi error, Sensor OK")
            elif result:
                print("Status: All systems normal, data sent successfully")
            else:
                print("Status: Data transmission failed")

            time.sleep(2)
        except KeyboardInterrupt:
            print("Stopped by user.")
            stop_led_blink()
            break
        except Exception as e:
            print(f"Loop error: {e}")
            handle_error(e, {"component": "main_loop"})

            # 一般的なエラー（両方のエラーとして扱う）
            sensor_error = True
            wifi_error = True
            led_status_combined_error()

            time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Critical error: {e}")
        handle_error(e, {"component": "main"})
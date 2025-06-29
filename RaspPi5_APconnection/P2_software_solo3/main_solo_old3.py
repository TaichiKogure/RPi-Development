#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi Pico 2W Main Program - Solo Version 3.2.0
- LED通知機能付き：Wi-Fi接続状態と送信ステータスを可視化
"""

import sys
import time
import machine
import _thread
from machine import Pin, I2C, Timer

# パス設定
sys.path.append('sensor_drivers')
sys.path.append('data_transmission')
sys.path.append('error_handling')

from bme680 import BME680_I2C
import wifi_client_solo
import watchdog_solo

# 設定値
DEVICE_ID = "P2"
WIFI_SSID = "RaspberryPi5_AP_Solo"
WIFI_PASSWORD = "raspberry"
SERVER_IP = "192.168.0.1"
SERVER_PORT = 5000
BME680_SCL_PIN = 1
BME680_SDA_PIN = 0
TRANSMISSION_INTERVAL = 30
LED_PIN = 25

# グローバル変数
led = Pin(LED_PIN, Pin.OUT)
wdt = None
client = None
transmitter = None
bme680_sensor = None
wifi_connected = False
led_timer = Timer()

# LED状態管理
def start_led_blink(interval_ms):
    def toggle_led(timer):
        led.toggle()
    led_timer.init(period=interval_ms, mode=Timer.PERIODIC, callback=toggle_led)

def stop_led_blink():
    led_timer.deinit()
    led.off()

def led_status_wifi_disconnected():
    stop_led_blink()
    start_led_blink(1000)  # 1秒間隔：未接続

def led_status_wifi_connected():
    stop_led_blink()
    start_led_blink(200)  # 0.2秒間隔：接続中

def led_flash_once(duration=200):
    stop_led_blink()
    led.on()
    time.sleep_ms(duration)
    led.off()
    if wifi_connected:
        start_led_blink(200)
    else:
        start_led_blink(1000)

def initialize_sensors():
    global bme680_sensor
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
        return True
    except Exception as e:
        print(f"Error initializing BME680 sensor: {e}")
        watchdog_solo.handle_error(e, {"component": "sensor_init"})
        return False

def delayed_wifi_init():
    global client, transmitter, wifi_connected

    try:
        print("Waiting 5 seconds before starting WiFi...")
        time.sleep(5)

        client = wifi_client_solo.WiFiClient(
            ssid=WIFI_SSID,
            password=WIFI_PASSWORD,
            server_ip=SERVER_IP,
            server_port=SERVER_PORT,
            device_id=DEVICE_ID
        )

        transmitter = wifi_client_solo.DataTransmitter(
            wifi_client=client,
            transmission_interval=TRANSMISSION_INTERVAL
        )
        transmitter.add_sensor("bme680", bme680_sensor)

        led_status_wifi_disconnected()

        for attempt in range(3):
            print(f"Connecting to {WIFI_SSID} (attempt {attempt+1}/3)...")
            if client.connect():
                print(f"Connected to {WIFI_SSID}")
                wifi_connected = True
                led_status_wifi_connected()
                return
            else:
                print("Retrying in 5 seconds...")
                time.sleep(5)

        print("Failed to connect to WiFi.")
        wifi_connected = False
        led_status_wifi_disconnected()

    except Exception as e:
        print(f"Error initializing WiFi: {e}")
        watchdog_solo.handle_error(e, {"component": "wifi_init"})

def collect_and_send_data():
    global transmitter, wdt
    try:
        if wdt:
            wdt.feed()

        if transmitter is None:
            print("WiFi not yet initialized. Skipping transmission.")
            return False

        success = transmitter.collect_and_send_data()

        if success:
            led_flash_once()  # 短く点灯（データ送信確認）

        return success

    except Exception as e:
        print(f"Error during data send: {e}")
        watchdog_solo.handle_error(e, {"component": "data_transmission"})
        return False

def main():
    global wdt

    print("Starting P2 Environmental System v3.2.0")
    print(f"Device ID: {DEVICE_ID}")

    print("Stabilizing before sensor init...")
    time.sleep(3)

    wdt = watchdog_solo.Watchdog(timeout_ms=10000)

    if not initialize_sensors():
        print("Sensor init failed. Halting.")
        while True:
            time.sleep(1)

    # WiFiを非同期で初期化
    _thread.start_new_thread(delayed_wifi_init, ())

    print("Entering main loop...")

    while True:
        try:
            collect_and_send_data()
            time.sleep(2)
        except KeyboardInterrupt:
            print("Stopped by user.")
            stop_led_blink()
            break
        except Exception as e:
            print(f"Unexpected error in main loop: {e}")
            watchdog_solo.handle_error(e, {"component": "main_loop"})
            time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Critical error at top-level: {e}")
        watchdog_solo.handle_error(e, {"component": "main"})

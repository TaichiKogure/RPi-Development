#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main_solo.py - Version 3.4.0-solo
- Wi-Fi RSSI表示対応
- センサー異常時LED3回点滅通知追加
- CYW43安定化、LED通知、エラー処理強化
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
import wifi_client_solo
import watchdog_solo

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
led = Pin(LED_PIN, Pin.OUT)
led_timer = Timer()
wdt = None
client = None
transmitter = None
bme680_sensor = None
wifi_connected = False

# ===== LED制御 =====
def start_led_blink(interval_ms):
    def toggle_led(timer):
        led.toggle()
    led_timer.init(period=interval_ms, mode=Timer.PERIODIC, callback=toggle_led)

def stop_led_blink():
    led_timer.deinit()
    led.off()

def led_status_wifi_disconnected():
    stop_led_blink()
    start_led_blink(1000)

def led_status_wifi_connected():
    stop_led_blink()
    start_led_blink(200)

def led_flash_once(duration=200):
    stop_led_blink()
    led.on()
    time.sleep_ms(duration)
    led.off()
    if wifi_connected:
        start_led_blink(200)
    else:
        start_led_blink(1000)

def led_flash_error(times=3, interval=500):
    for _ in range(times):
        led.on()
        time.sleep_ms(interval)
        led.off()
        time.sleep_ms(interval)

# ===== センサー初期化 =====
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
        print(f"Sensor init error: {e}")
        watchdog_solo.handle_error(e, {"component": "sensor_init"})
        return False

# ===== Wi-Fi初期化 =====
def delayed_wifi_init():
    global client, transmitter, wifi_connected

    try:
        print("Delaying Wi-Fi init for stability...")
        time.sleep(5)

        wlan = network.WLAN(network.STA_IF)
        wlan.active(False)
        time.sleep(1)
        wlan.active(True)
        time.sleep(2)

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
            print(f"Connecting to Wi-Fi (try {attempt+1}/3)...")
            wlan.active(True)
            if client.connect():
                print("Wi-Fi connected.")
                wifi_connected = True
                rssi = wlan.status('rssi')
                print(f"📶 RSSI: {rssi} dBm")
                led_status_wifi_connected()
                return
            else:
                print("Connect failed. Retry in 5 sec...")
                time.sleep(5)

        print("Wi-Fi connection failed.")
        wifi_connected = False
        led_status_wifi_disconnected()

    except Exception as e:
        print(f"Wi-Fi init error: {e}")
        watchdog_solo.handle_error(e, {"component": "wifi_init"})

# ===== データ送信 =====
def collect_and_send_data():
    global transmitter, wdt
    try:
        if wdt:
            wdt.feed()

        if transmitter is None:
            print("Wi-Fi not ready. Skipping send.")
            return False

        success = transmitter.collect_and_send_data()
        if success:
            led_flash_once()

        return success
    except Exception as e:
        print(f"Data send error: {e}")
        watchdog_solo.handle_error(e, {"component": "data_transmission"})
        return False

# ===== メイン関数 =====
def main():
    global wdt

    print("Starting P2 Environmental System v3.4.0")
    print(f"Device ID: {DEVICE_ID}")
    print("Waiting 3 sec for stabilization...")
    time.sleep(3)

    wdt = watchdog_solo.Watchdog(timeout_ms=10000)

    if not initialize_sensors():
        print("Sensor error. Flashing LED 3 times and halt.")
        led_flash_error(3, 500)
        while True:
            time.sleep(1)

    _thread.start_new_thread(delayed_wifi_init, ())

    print("Main loop start.")
    while True:
        try:
            collect_and_send_data()
            time.sleep(2)
        except KeyboardInterrupt:
            print("Stopped by user.")
            stop_led_blink()
            break
        except Exception as e:
            print(f"Loop error: {e}")
            watchdog_solo.handle_error(e, {"component": "main_loop"})
            time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Critical error: {e}")
        watchdog_solo.handle_error(e, {"component": "main"})

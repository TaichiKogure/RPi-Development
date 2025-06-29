from RaspPi5_APconnection.Pico2BME680singletest.OK2bme680Pico.bme680 import BME680_I2C  # 必要なクラスをインポート
from machine import I2C, Pin
import time

# I2Cバスを初期化
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=100000)  # scl: GPIO1, sda: GPIO0
print("I2C scan result:", i2c.scan())  # センサーが見つかるか確認

# BME680オブジェクトを初期化
bme = BME680_I2C(i2c, address=0x77)  # アドレスを必要に応じて指定 (0x76 か 0x77)
time.sleep(1)  # 初期化待機

# 無限ループでデータを取得・表示
while True:
    print(
        "Temp:{:.3g}C, Humidity:{:.3g}%, Pressure:{:.5g}hPa, Gas:{}".format(
            bme.temperature,
            bme.humidity,
            bme.pressure,
            bme.gas
        )
    )
    time.sleep(3)  # 3秒待機
"""
BME680forZ_ver1.0.py - BME680センサーからのデータを5秒ごとに読み取るプログラム

このプログラムは、BME680環境センサーから温度、湿度、気圧、ガス抵抗値のデータを
5秒ごとに読み取り、表示します。

接続方法:
- BME680センサー (I2C接続)
  - VCC -> 3.3V
  - GND -> GND
  - SCL -> GPIO 1 (Pin 2)
  - SDA -> GPIO 0 (Pin 1)

作成日: 2025-07-26
バージョン: 1.0
"""

from bme680 import BME680_I2C  # BME680センサードライバをインポート
from machine import I2C, Pin
import time
import gc

# プログラム情報を表示
print("===== BME680 環境データ測定プログラム Ver.1.0 =====")
print("5秒ごとにBME680センサーからデータを読み取ります")
print("Ctrl+Cで終了できます")
print("================================================")

# エラーハンドリング関数
def handle_error(e, phase):
    """エラーを処理し、情報を表示する"""
    print(f"エラーが発生しました ({phase}): {e}")
    print("5秒後に再試行します...")
    time.sleep(5)
    return False

# メイン処理
def main():
    i2c = None
    bme = None
    
    try:
        # I2Cバスを初期化
        print("I2Cバスを初期化しています...")
        i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=100000)  # SCL: GPIO1, SDA: GPIO0
        
        # I2Cデバイスをスキャン
        devices = i2c.scan()
        if not devices:
            print("I2Cデバイスが見つかりません。接続を確認してください。")
            return False
        
        print(f"I2Cデバイスが見つかりました: {[hex(d) for d in devices]}")
        
        # BME680センサーを初期化
        print("BME680センサーを初期化しています...")
        
        # まず0x77アドレスで試す
        try:
            bme = BME680_I2C(i2c, address=0x77)
            print("BME680センサーを0x77アドレスで初期化しました")
        except Exception as e:
            print(f"0x77アドレスでの初期化に失敗しました: {e}")
            print("0x76アドレスで試行します...")
            
            # 0x76アドレスで試す
            try:
                bme = BME680_I2C(i2c, address=0x76)
                print("BME680センサーを0x76アドレスで初期化しました")
            except Exception as e:
                return handle_error(e, "センサー初期化")
        
        # 初期化待機
        time.sleep(1)
        print("初期化完了。データ取得を開始します...")
        
        # 測定回数カウンター
        count = 0
        
        # メインループ
        while True:
            try:
                # 測定回数を増加
                count += 1
                
                # 現在時刻を取得
                current_time = time.localtime()
                time_str = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
                    current_time[0], current_time[1], current_time[2],
                    current_time[3], current_time[4], current_time[5]
                )
                
                # センサーからデータを読み取り
                temp = bme.temperature
                hum = bme.humidity
                pres = bme.pressure
                gas = bme.gas
                
                # データを表示
                print(f"[{count}] {time_str}")
                print(f"  温度: {temp:.2f} °C")
                print(f"  湿度: {hum:.2f} %")
                print(f"  気圧: {pres:.2f} hPa")
                print(f"  ガス抵抗: {gas} Ω")
                print("-" * 40)
                
                # メモリ管理
                gc.collect()
                
                # 5秒待機
                time.sleep(5)
                
            except KeyboardInterrupt:
                print("\nプログラムを終了します")
                break
            except Exception as e:
                handle_error(e, "データ読み取り")
        
        return True
    
    except KeyboardInterrupt:
        print("\nプログラムを終了します")
        return True
    except Exception as e:
        return handle_error(e, "初期化")

# プログラム実行
if __name__ == "__main__":
    while not main():
        print("プログラムを再起動します...")
        time.sleep(1)
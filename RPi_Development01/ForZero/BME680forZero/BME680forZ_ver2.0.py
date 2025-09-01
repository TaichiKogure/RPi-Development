"""
BME680forZ_ver2.0.py - BME680センサーからのデータを5秒ごとに読み取るプログラム (標準Python版)

このプログラムは、BME680環境センサーから温度、湿度、気圧、ガス抵抗値のデータを
5秒ごとに読み取り、表示します。

接続方法 (Raspberry Pi):
- BME680センサー (I2C接続)
  - VCC -> 3.3V
  - GND -> GND
  - SCL -> SCL (GPIO 3, Pin 5)
  - SDA -> SDA (GPIO 2, Pin 3)

作成日: 2025-07-26
バージョン: 2.0
"""

import time
import datetime
import board
import busio
import adafruit_bme680
import sys

# プログラム情報を表示
print("===== BME680 環境データ測定プログラム Ver.2.0 (標準Python版) =====")
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
    bme680 = None
    
    try:
        # I2Cバスを初期化
        print("I2Cバスを初期化しています...")
        i2c = busio.I2C(board.SCL, board.SDA)
        
        # BME680センサーを初期化
        print("BME680センサーを初期化しています...")
        
        # まず0x77アドレスで試す
        try:
            bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c, address=0x77)
            print("BME680センサーを0x77アドレスで初期化しました")
        except Exception as e:
            print(f"0x77アドレスでの初期化に失敗しました: {e}")
            print("0x76アドレスで試行します...")
            
            # 0x76アドレスで試す
            try:
                bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c, address=0x76)
                print("BME680センサーを0x76アドレスで初期化しました")
            except Exception as e:
                return handle_error(e, "センサー初期化")
        
        # 海面気圧の設定（高度計算用、必要に応じて調整）
        bme680.sea_level_pressure = 1013.25
        
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
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # センサーからデータを読み取り
                temp = bme680.temperature
                hum = bme680.relative_humidity
                pres = bme680.pressure
                gas = bme680.gas
                
                # データを表示
                print(f"[{count}] {current_time}")
                print(f"  温度: {temp:.2f} °C")
                print(f"  湿度: {hum:.2f} %")
                print(f"  気圧: {pres:.2f} hPa")
                print(f"  ガス抵抗: {gas} Ω")
                print("-" * 40)
                
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
    finally:
        # リソースのクリーンアップ（必要に応じて）
        pass

# プログラム実行
if __name__ == "__main__":
    while not main():
        print("プログラムを再起動します...")
        time.sleep(1)
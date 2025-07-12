"""
データ読み取りモジュール for P1_app_simple44.py
Version: 4.40
"""

import os
import logging
import datetime
import pandas as pd

# ロガーの設定
logger = logging.getLogger(__name__)

# デフォルト設定
DEFAULT_CONFIG = {
    "data_dir": "/var/lib/raspap_solo/data",
    "rawdata_p2_dir": "RawData_P2",
    "rawdata_p3_dir": "RawData_P3"
}

def read_csv_data(device_id, days=1, config=None):
    """指定されたデバイスと時間範囲のCSVファイルからデータを読み取ります。"""
    # 設定の初期化
    if config is None:
        config = DEFAULT_CONFIG
    
    # ファイルパスの定義
    if device_id == "P2":
        csv_path = os.path.join(config["data_dir"], config["rawdata_p2_dir"], "P2_fixed.csv")
    elif device_id == "P3":
        csv_path = os.path.join(config["data_dir"], config["rawdata_p3_dir"], "P3_fixed.csv")
    else:
        logger.error(f"無効なデバイスID: {device_id}")
        return None
    
    # ファイルの存在確認
    if not os.path.exists(csv_path):
        logger.warning(f"CSVファイルが見つかりません: {csv_path}")
        return None
    
    try:
        # CSVファイルの読み取り
        df = pd.read_csv(csv_path)
        
        # タイムスタンプをdatetimeに変換
        if 'timestamp' in df.columns:
            if df['timestamp'].dtype == 'int64' or df['timestamp'].dtype == 'float64':
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
            else:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
        # 無効なタイムスタンプを持つ行を削除
        df = df.dropna(subset=['timestamp'])
        
        # 指定された時間範囲のデータをフィルタリング
        if days > 0:
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
            df = df[df['timestamp'] >= cutoff_date]
        
        # タイムスタンプでソート
        df = df.sort_values(by='timestamp')
        
        return df
    
    except Exception as e:
        logger.error(f"CSVファイル {csv_path} の読み取り中にエラーが発生しました: {e}")
        return None

def get_latest_data(device_id, config=None):
    """指定されたデバイスの最新のデータを取得します。"""
    df = read_csv_data(device_id, days=1, config=config)
    if df is None or df.empty:
        return None
    
    # 最新の行を取得
    latest_row = df.iloc[-1].to_dict()
    
    # タイムスタンプを文字列に変換
    if 'timestamp' in latest_row and isinstance(latest_row['timestamp'], pd.Timestamp):
        latest_row['timestamp'] = latest_row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
    
    return latest_row

def calculate_absolute_humidity(temperature, humidity):
    """温度と相対湿度から絶対湿度を計算します。"""
    if temperature is None or humidity is None:
        return None
    
    try:
        temperature = float(temperature)
        humidity = float(humidity)
        
        # 飽和水蒸気圧の計算 (Magnus formula)
        saturation_vapor_pressure = 6.1078 * 10.0**(7.5 * temperature / (237.3 + temperature))
        
        # 実際の水蒸気圧
        actual_vapor_pressure = saturation_vapor_pressure * humidity / 100.0
        
        # 絶対湿度の計算 (g/m³)
        absolute_humidity = 216.7 * actual_vapor_pressure / (273.15 + temperature)
        
        return round(absolute_humidity, 2)
    
    except Exception as e:
        logger.error(f"絶対湿度の計算中にエラーが発生しました: {e}")
        return None
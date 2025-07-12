"""
データ処理モジュール for P1_data_collector_solo44.py
Version: 4.40
"""

import logging
import math

# ロガーの設定
logger = logging.getLogger(__name__)

def calculate_absolute_humidity(temperature, humidity):
    """温度と相対湿度から絶対湿度を計算します。
    
    Args:
        temperature (float): 温度（摂氏）
        humidity (float): 相対湿度（%）
        
    Returns:
        float: 絶対湿度（g/m³）、または計算できない場合はNone
    """
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

def validate_data(data):
    """センサーノードから受信したデータを検証します。
    
    Args:
        data (dict): 検証するデータ
        
    Returns:
        tuple: (検証結果 (bool), エラーメッセージ (str) または None)
    """
    # 必須フィールドの確認
    required_fields = ["device_id", "timestamp"]
    for field in required_fields:
        if field not in data:
            return False, f"必須フィールドがありません: {field}"
    
    # デバイスIDの確認
    if data["device_id"] not in ["P2", "P3"]:
        return False, f"無効なデバイスID: {data['device_id']}"
    
    # タイムスタンプの確認
    try:
        timestamp = int(data["timestamp"])
        if timestamp <= 0:
            return False, f"無効なタイムスタンプ: {timestamp}"
    except (ValueError, TypeError):
        return False, f"タイムスタンプが整数ではありません: {data['timestamp']}"
    
    # センサーデータの確認
    sensor_fields = ["temperature", "humidity", "pressure", "gas_resistance", "co2"]
    for field in sensor_fields:
        if field in data and data[field] is not None:
            try:
                value = float(data[field])
                
                # 値の範囲チェック
                if field == "temperature" and (value < -40 or value > 85):
                    logger.warning(f"温度が範囲外です: {value}°C")
                elif field == "humidity" and (value < 0 or value > 100):
                    logger.warning(f"湿度が範囲外です: {value}%")
                elif field == "pressure" and (value < 300 or value > 1100):
                    logger.warning(f"気圧が範囲外です: {value}hPa")
                elif field == "co2" and (value < 0 or value > 10000):
                    logger.warning(f"CO2濃度が範囲外です: {value}ppm")
            except (ValueError, TypeError):
                logger.warning(f"センサーデータが数値ではありません: {field}={data[field]}")
    
    # 絶対湿度の計算
    if "temperature" in data and "humidity" in data and data["temperature"] is not None and data["humidity"] is not None:
        data["absolute_humidity"] = calculate_absolute_humidity(data["temperature"], data["humidity"])
    
    return True, None

def process_data(data):
    """センサーノードから受信したデータを処理します。
    
    Args:
        data (dict): 処理するデータ
        
    Returns:
        dict: 処理されたデータ、または検証に失敗した場合はNone
    """
    # データの検証
    valid, error = validate_data(data)
    if not valid:
        logger.error(f"データ検証に失敗しました: {error}")
        return None
    
    # データの処理
    processed_data = data.copy()
    
    # 絶対湿度の計算（まだ計算されていない場合）
    if "absolute_humidity" not in processed_data and "temperature" in processed_data and "humidity" in processed_data:
        processed_data["absolute_humidity"] = calculate_absolute_humidity(
            processed_data["temperature"], processed_data["humidity"]
        )
    
    return processed_data
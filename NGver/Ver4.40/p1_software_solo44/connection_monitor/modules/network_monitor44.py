"""
ネットワークモニタリングモジュール for P1_wifi_monitor_solo44.py
Version: 4.40
"""

import subprocess
import re
import logging
import socket
import time

# ロガーの設定
logger = logging.getLogger(__name__)

def get_signal_strength(device_id, config):
    """指定されたデバイスの信号強度を取得します。
    
    Args:
        device_id (str): デバイスID（"P2"または"P3"）
        config (dict): 設定情報
        
    Returns:
        tuple: (信号強度 (dBm), 成功したかどうか (bool))
    """
    if device_id not in config["devices"]:
        logger.error(f"無効なデバイスID: {device_id}")
        return None, False
    
    device_info = config["devices"][device_id]
    ip_address = device_info.get("ip")
    
    if not ip_address:
        logger.error(f"{device_id}のIPアドレスが設定されていません")
        return None, False
    
    # MACアドレスの解決（まだ解決されていない場合）
    if not device_info.get("mac"):
        try:
            # ARPテーブルからMACアドレスを取得
            arp_output = subprocess.check_output(["arp", "-n", ip_address], universal_newlines=True)
            mac_match = re.search(r"([0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})", arp_output)
            
            if mac_match:
                device_info["mac"] = mac_match.group(1)
                logger.info(f"{device_id}のMACアドレスを解決しました: {device_info['mac']}")
            else:
                # Pingを送信してARPテーブルを更新
                subprocess.call(["ping", "-c", "1", "-W", "1", ip_address], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # 再度ARPテーブルを確認
                arp_output = subprocess.check_output(["arp", "-n", ip_address], universal_newlines=True)
                mac_match = re.search(r"([0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})", arp_output)
                
                if mac_match:
                    device_info["mac"] = mac_match.group(1)
                    logger.info(f"{device_id}のMACアドレスを解決しました: {device_info['mac']}")
                else:
                    logger.warning(f"{device_id}のMACアドレスを解決できませんでした")
                    return None, False
        
        except Exception as e:
            logger.error(f"MACアドレスの解決中にエラーが発生しました: {e}")
            return None, False
    
    # 信号強度の取得
    try:
        # iwconfigコマンドを使用して信号強度を取得
        iwconfig_output = subprocess.check_output(
            ["iwconfig", config["interface"]], 
            universal_newlines=True, 
            stderr=subprocess.STDOUT
        )
        
        # 信号強度の正規表現パターン
        signal_pattern = r"Signal level=(-\d+) dBm"
        
        # 信号強度の抽出
        signal_match = re.search(signal_pattern, iwconfig_output)
        if signal_match:
            signal_strength = int(signal_match.group(1))
            logger.debug(f"{device_id}の信号強度: {signal_strength} dBm")
            return signal_strength, True
        else:
            logger.warning(f"{device_id}の信号強度を取得できませんでした")
            return None, False
    
    except Exception as e:
        logger.error(f"信号強度の取得中にエラーが発生しました: {e}")
        return None, False

def get_noise_level(config):
    """ノイズレベルを取得します。
    
    Args:
        config (dict): 設定情報
        
    Returns:
        tuple: (ノイズレベル (dBm), 成功したかどうか (bool))
    """
    try:
        # iwconfigコマンドを使用してノイズレベルを取得
        iwconfig_output = subprocess.check_output(
            ["iwconfig", config["interface"]], 
            universal_newlines=True, 
            stderr=subprocess.STDOUT
        )
        
        # ノイズレベルの正規表現パターン
        noise_pattern = r"Noise level=(-\d+) dBm"
        
        # ノイズレベルの抽出
        noise_match = re.search(noise_pattern, iwconfig_output)
        if noise_match:
            noise_level = int(noise_match.group(1))
            logger.debug(f"ノイズレベル: {noise_level} dBm")
            return noise_level, True
        else:
            # 一部のWiFiドライバーはノイズレベルを報告しないため、デフォルト値を使用
            default_noise = -95
            logger.debug(f"ノイズレベルを取得できませんでした。デフォルト値を使用: {default_noise} dBm")
            return default_noise, True
    
    except Exception as e:
        logger.error(f"ノイズレベルの取得中にエラーが発生しました: {e}")
        return None, False

def measure_ping(device_id, config):
    """指定されたデバイスへのPing時間を測定します。
    
    Args:
        device_id (str): デバイスID（"P2"または"P3"）
        config (dict): 設定情報
        
    Returns:
        tuple: (Ping時間 (ms), 成功したかどうか (bool))
    """
    if device_id not in config["devices"]:
        logger.error(f"無効なデバイスID: {device_id}")
        return None, False
    
    device_info = config["devices"][device_id]
    ip_address = device_info.get("ip")
    
    if not ip_address:
        logger.error(f"{device_id}のIPアドレスが設定されていません")
        return None, False
    
    try:
        # pingコマンドを使用してPing時間を測定
        ping_output = subprocess.check_output(
            ["ping", "-c", "3", "-W", "1", ip_address], 
            universal_newlines=True, 
            stderr=subprocess.STDOUT
        )
        
        # Ping時間の正規表現パターン
        ping_pattern = r"min/avg/max/mdev = [\d.]+/([\d.]+)/[\d.]+/[\d.]+ ms"
        
        # Ping時間の抽出
        ping_match = re.search(ping_pattern, ping_output)
        if ping_match:
            ping_time = float(ping_match.group(1))
            logger.debug(f"{device_id}へのPing時間: {ping_time} ms")
            return ping_time, True
        else:
            logger.warning(f"{device_id}へのPing時間を取得できませんでした")
            return None, False
    
    except subprocess.CalledProcessError:
        logger.warning(f"{device_id}へのPingが失敗しました")
        return None, False
    
    except Exception as e:
        logger.error(f"Ping時間の測定中にエラーが発生しました: {e}")
        return None, False

def check_device_online(device_id, config):
    """指定されたデバイスがオンラインかどうかを確認します。
    
    Args:
        device_id (str): デバイスID（"P2"または"P3"）
        config (dict): 設定情報
        
    Returns:
        bool: デバイスがオンラインの場合はTrue、それ以外の場合はFalse
    """
    if device_id not in config["devices"]:
        logger.error(f"無効なデバイスID: {device_id}")
        return False
    
    device_info = config["devices"][device_id]
    ip_address = device_info.get("ip")
    
    if not ip_address:
        logger.error(f"{device_id}のIPアドレスが設定されていません")
        return False
    
    try:
        # pingコマンドを使用してデバイスがオンラインかどうかを確認
        result = subprocess.call(
            ["ping", "-c", "1", "-W", "1", ip_address], 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        
        return result == 0
    
    except Exception as e:
        logger.error(f"デバイスのオンライン状態の確認中にエラーが発生しました: {e}")
        return False
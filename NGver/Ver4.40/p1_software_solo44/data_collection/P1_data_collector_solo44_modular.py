#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi 5 Environmental Data Collector - Modular Version
Version: 4.40.0-solo

This module collects environmental data from P2 and P3 sensor nodes and stores it in CSV files.
It also provides an API for accessing the collected data.

Features:
- Socket server for receiving data from P2 and P3 sensor nodes
- Data validation and processing
- CSV file storage with daily rotation
- API for accessing the latest data
- Automatic cleanup of old data files

Requirements:
- Python 3.7+
- Flask for the API server
- Pandas for data manipulation

Usage:
    python3 P1_data_collector_solo44_modular.py [--port PORT] [--data-dir DIR]
"""

import os
import sys
import time
import json
import socket
import argparse
import threading
import logging
import datetime
import math
from pathlib import Path

# モジュールのインポート
from modules import CSVManager, process_data, SocketServer, APIServer

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/data_collector_solo44_modular.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# デフォルト設定
DEFAULT_CONFIG = {
    "listen_port": 5000,
    "data_dir": "/var/lib(FromThonny)/raspap_solo/data",
    "rawdata_p2_dir": "RawData_P2",
    "rawdata_p3_dir": "RawData_P3",
    "api_port": 5001,
    "max_file_size_mb": 10,
    "rotation_interval_days": 7,
    "device_timeout_seconds": 120
}

# WiFiモニターの設定（利用可能な場合）
MONITOR_CONFIG = {
    "devices": {
        "P2": {"ip": "192.168.0.50", "mac": None},
        "P3": {"ip": "192.168.0.51", "mac": None}
    }
}

# WiFiモニターのインポート（利用可能な場合）
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'connection_monitor'))
    from P1_wifi_monitor_solo44 import WiFiMonitor
except ImportError:
    logger.warning("WiFiモニターモジュールをインポートできませんでした。動的IP追跡は無効になります。")
    WiFiMonitor = None

class DataCollector:
    """センサーノードから環境データを収集して保存するクラス。"""
    
    def __init__(self, config=None):
        """指定された設定でデータコレクターを初期化します。"""
        self.config = config or DEFAULT_CONFIG.copy()
        self.devices = {}  # デバイス情報を保存
        self.last_data = {}  # 各デバイスの最後に受信したデータを保存
        self.lock = threading.Lock()  # スレッドセーフな操作のためのロック
        
        # CSVマネージャーの初期化
        self.csv_manager = CSVManager(self.config)
        
        # WiFiモニターの初期化（動的IP追跡用）
        self.wifi_monitor = None
        if WiFiMonitor is not None:
            try:
                self.wifi_monitor = WiFiMonitor(MONITOR_CONFIG.copy())
                logger.info("動的IP追跡用のWiFiモニターが初期化されました")
            except Exception as e:
                logger.error(f"WiFiモニターの初期化に失敗しました: {e}")
        
        # ソケットサーバーの初期化
        self.socket_server = SocketServer(self.config, self._handle_data)
        
        # APIサーバーの初期化
        self.api_server = APIServer(self.config, self._get_latest_data)
        
        # 実行フラグ
        self.running = False
        
        # クリーンアップスレッド
        self.cleanup_thread = None
    
    def _handle_data(self, data, addr):
        """センサーノードから受信したデータを処理します。
        
        Args:
            data (dict): 処理するデータ
            addr (tuple): 送信元アドレス (host, port)
        """
        # データの処理
        processed_data = process_data(data)
        if processed_data is None:
            logger.error(f"データ処理に失敗しました: {data}")
            return
        
        # デバイスIDの取得
        device_id = processed_data.get("device_id")
        if device_id not in ["P2", "P3"]:
            logger.error(f"無効なデバイスID: {device_id}")
            return
        
        # 送信元IPアドレスの記録
        sender_ip = addr[0]
        logger.debug(f"{device_id}からのデータを受信しました（送信元IP: {sender_ip}）")
        
        # WiFiモニターの更新（利用可能な場合）
        if self.wifi_monitor and hasattr(self.wifi_monitor, "update_device_ip"):
            self.wifi_monitor.update_device_ip(device_id, sender_ip)
        
        # データの保存
        with self.lock:
            # 最後に受信したデータを更新
            self.last_data[device_id] = processed_data
            
            # CSVファイルに書き込む
            self.csv_manager.write_data(processed_data)
            
            logger.info(f"{device_id}からのデータを保存しました")
    
    def _get_latest_data(self):
        """最新のデータを取得します。
        
        Returns:
            dict: 各デバイスの最新データ
        """
        with self.lock:
            return self.last_data.copy()
    
    def _cleanup_routine(self):
        """古いCSVファイルをクリーンアップするルーチン。"""
        while self.running:
            try:
                # 日付が変わったらCSVファイルをローテーション
                current_date = datetime.datetime.now().strftime("%Y-%m-%d")
                if getattr(self, "_last_rotation_date", None) != current_date:
                    self.csv_manager.rotate_csv_files()
                    self._last_rotation_date = current_date
                
                # 古いファイルのクリーンアップ
                self.csv_manager.cleanup_old_files()
            
            except Exception as e:
                logger.error(f"クリーンアップルーチン中にエラーが発生しました: {e}")
            
            # 1時間ごとにチェック
            time.sleep(3600)
    
    def start(self):
        """データコレクターを開始します。"""
        with self.lock:
            if self.running:
                logger.warning("データコレクターはすでに実行中です")
                return False
            
            try:
                # 実行フラグを設定
                self.running = True
                
                # ソケットサーバーを開始
                if not self.socket_server.start():
                    logger.error("ソケットサーバーの開始に失敗しました")
                    self.running = False
                    return False
                
                # APIサーバーを開始
                if not self.api_server.start():
                    logger.error("APIサーバーの開始に失敗しました")
                    self.socket_server.stop()
                    self.running = False
                    return False
                
                # クリーンアップスレッドを開始
                self.cleanup_thread = threading.Thread(target=self._cleanup_routine)
                self.cleanup_thread.daemon = True
                self.cleanup_thread.start()
                
                logger.info("データコレクターが開始されました")
                return True
            
            except Exception as e:
                logger.error(f"データコレクターの開始中にエラーが発生しました: {e}")
                self.running = False
                return False
    
    def stop(self):
        """データコレクターを停止します。"""
        with self.lock:
            if not self.running:
                logger.warning("データコレクターはすでに停止しています")
                return False
            
            try:
                # 実行フラグをクリア
                self.running = False
                
                # ソケットサーバーを停止
                self.socket_server.stop()
                
                # APIサーバーを停止
                self.api_server.stop()
                
                # CSVファイルを閉じる
                self.csv_manager.close()
                
                # クリーンアップスレッドが終了するのを待つ
                if self.cleanup_thread and self.cleanup_thread.is_alive():
                    self.cleanup_thread.join(timeout=5.0)
                
                logger.info("データコレクターが停止しました")
                return True
            
            except Exception as e:
                logger.error(f"データコレクターの停止中にエラーが発生しました: {e}")
                return False

def main():
    """メイン関数：データコレクターを実行します。"""
    parser = argparse.ArgumentParser(description='Environmental Data Collector - Modular Version')
    parser.add_argument('--port', type=int, default=DEFAULT_CONFIG["listen_port"],
                        help=f'Listen port for sensor data (default: {DEFAULT_CONFIG["listen_port"]})')
    parser.add_argument('--api-port', type=int, default=DEFAULT_CONFIG["api_port"],
                        help=f'Port for API server (default: {DEFAULT_CONFIG["api_port"]})')
    parser.add_argument('--data-dir', type=str, default=DEFAULT_CONFIG["data_dir"],
                        help=f'Directory to store data (default: {DEFAULT_CONFIG["data_dir"]})')
    
    args = parser.parse_args()
    
    # 設定の更新
    config = DEFAULT_CONFIG.copy()
    config["listen_port"] = args.port
    config["api_port"] = args.api_port
    config["data_dir"] = args.data_dir
    
    # データコレクターの初期化と開始
    collector = DataCollector(config)
    if not collector.start():
        logger.error("データコレクターの開始に失敗しました")
        sys.exit(1)
    
    # メインスレッドを維持
    try:
        logger.info(f"データコレクターがポート {config['listen_port']} で実行中です")
        logger.info(f"APIサーバーがポート {config['api_port']} で実行中です")
        logger.info("終了するには Ctrl+C を押してください")
        
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("キーボード割り込みを受信しました。終了します...")
    
    finally:
        # データコレクターを停止
        collector.stop()

if __name__ == "__main__":
    main()
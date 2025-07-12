"""
APIサーバーモジュール for P1_wifi_monitor_solo44.py
Version: 4.40
"""

import logging
import threading
import json
from flask import Flask, jsonify, request

# ロガーの設定
logger = logging.getLogger(__name__)

class APIServer:
    """WiFiモニターのAPIサーバー。"""
    
    def __init__(self, config, data_provider):
        """指定された設定でAPIサーバーを初期化します。
        
        Args:
            config (dict): サーバー設定
            data_provider (callable): 最新のデータを提供するコールバック関数
        """
        self.config = config
        self.data_provider = data_provider
        self.app = Flask(__name__)
        self.thread = None
        self.running = False
        self.lock = threading.Lock()
        
        # APIルートの設定
        self._setup_api_routes()
    
    def _setup_api_routes(self):
        """APIルートを設定します。"""
        
        @self.app.route('/api/wifi/status')
        def get_latest_data():
            """最新のWiFi接続状態データを取得します。"""
            if self.data_provider:
                latest_data = self.data_provider()
                return jsonify(latest_data)
            return jsonify({"error": "データプロバイダーが設定されていません"})
        
        @self.app.route('/api/wifi/device/<device_id>')
        def get_device_data(device_id):
            """特定のデバイスの最新WiFi接続状態を取得します。"""
            if device_id not in ["P2", "P3"]:
                return jsonify({"error": "無効なデバイスID"}), 400
            
            if self.data_provider:
                all_data = self.data_provider()
                if device_id in all_data:
                    return jsonify(all_data[device_id])
                return jsonify({"error": f"{device_id}のデータがありません"}), 404
            
            return jsonify({"error": "データプロバイダーが設定されていません"}), 500
        
        @self.app.route('/api/wifi/history/<device_id>')
        def get_device_history(device_id):
            """特定のデバイスのWiFi接続履歴を取得します。"""
            if device_id not in ["P2", "P3"]:
                return jsonify({"error": "無効なデバイスID"}), 400
            
            # 履歴データの取得（実装されていない場合はダミーデータを返す）
            history_data = {
                "device_id": device_id,
                "history": [
                    {
                        "timestamp": "2023-01-01T00:00:00",
                        "signal_strength": -65,
                        "ping_ms": 12,
                        "noise": -95
                    },
                    {
                        "timestamp": "2023-01-01T00:05:00",
                        "signal_strength": -67,
                        "ping_ms": 15,
                        "noise": -95
                    }
                ]
            }
            
            return jsonify(history_data)
    
    def start(self):
        """APIサーバーを開始します。"""
        with self.lock:
            if self.running:
                logger.warning("APIサーバーはすでに実行中です")
                return False
            
            try:
                # サーバーの実行フラグを設定
                self.running = True
                
                # サーバースレッドの開始
                self.thread = threading.Thread(target=self._run_api)
                self.thread.daemon = True
                self.thread.start()
                
                logger.info(f"APIサーバーがポート {self.config['monitor_port']} で開始されました")
                return True
            
            except Exception as e:
                logger.error(f"APIサーバーの開始中にエラーが発生しました: {e}")
                self.running = False
                return False
    
    def stop(self):
        """APIサーバーを停止します。"""
        with self.lock:
            if not self.running:
                logger.warning("APIサーバーはすでに停止しています")
                return False
            
            try:
                # サーバーの実行フラグをクリア
                self.running = False
                
                # サーバースレッドが終了するのを待つ
                # 注意: Flaskサーバーは通常、シグナルで停止するため、
                # ここでは完全な停止は保証されません
                if self.thread and self.thread.is_alive():
                    self.thread.join(timeout=5.0)
                
                logger.info("APIサーバーが停止しました")
                return True
            
            except Exception as e:
                logger.error(f"APIサーバーの停止中にエラーが発生しました: {e}")
                return False
    
    def _run_api(self):
        """APIサーバーを実行します。"""
        try:
            self.app.run(
                host='0.0.0.0',
                port=self.config["monitor_port"],
                debug=False,
                use_reloader=False,
                threaded=True
            )
        except Exception as e:
            logger.error(f"APIサーバーの実行中にエラーが発生しました: {e}")
            with self.lock:
                self.running = False
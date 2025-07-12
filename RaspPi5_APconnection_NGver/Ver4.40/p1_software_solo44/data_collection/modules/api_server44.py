"""
APIサーバーモジュール for P1_data_collector_solo44.py
Version: 4.40
"""

import logging
import threading
import pandas as pd
import os
from flask import Flask, jsonify, request

# ロガーの設定
logger = logging.getLogger(__name__)

class APIServer:
    """データ収集サービスのAPIサーバー。"""
    
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
        
        @self.app.route('/api/data/latest')
        def get_latest_data():
            """最新のセンサーデータを取得します。"""
            if self.data_provider:
                latest_data = self.data_provider()
                return jsonify(latest_data)
            return jsonify({"error": "データプロバイダーが設定されていません"})
        
        @self.app.route('/api/data/device/<device_id>')
        def get_device_data(device_id):
            """特定のデバイスの最新データを取得します。"""
            if device_id not in ["P2", "P3"]:
                return jsonify({"error": "無効なデバイスID"}), 400
            
            if self.data_provider:
                all_data = self.data_provider()
                if device_id in all_data:
                    return jsonify(all_data[device_id])
                return jsonify({"error": f"{device_id}のデータがありません"}), 404
            
            return jsonify({"error": "データプロバイダーが設定されていません"}), 500
        
        @self.app.route('/api/data/csv/<device_id>')
        def get_csv_data(device_id):
            """特定のデバイスのCSVデータを取得します。"""
            if device_id not in ["P2", "P3"]:
                return jsonify({"error": "無効なデバイスID"}), 400
            
            try:
                # 適切なディレクトリを決定
                device_dir = self.config["rawdata_p2_dir"] if device_id == "P2" else self.config["rawdata_p3_dir"]
                csv_path = os.path.join(self.config["data_dir"], device_dir, f"{device_id}_fixed.csv")
                
                # ファイルの存在を確認
                if not os.path.exists(csv_path):
                    return jsonify({"error": f"{device_id}のCSVデータがありません"}), 404
                
                # CSVファイルを読み込む
                df = pd.read_csv(csv_path)
                
                # JSONに変換して返す
                return jsonify(df.to_dict(orient='records'))
            
            except Exception as e:
                logger.error(f"CSVデータの取得中にエラーが発生しました: {e}")
                return jsonify({"error": f"CSVデータの取得中にエラーが発生しました: {str(e)}"}), 500
    
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
                
                logger.info(f"APIサーバーがポート {self.config['api_port']} で開始されました")
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
                port=self.config["api_port"],
                debug=False,
                use_reloader=False,
                threaded=True
            )
        except Exception as e:
            logger.error(f"APIサーバーの実行中にエラーが発生しました: {e}")
            with self.lock:
                self.running = False
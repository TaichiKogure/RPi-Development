"""
ソケットサーバーモジュール for P1_data_collector_solo44.py
Version: 4.40
"""

import socket
import json
import logging
import threading
import time

# ロガーの設定
logger = logging.getLogger(__name__)

class SocketServer:
    """センサーノードからデータを受信するためのソケットサーバー。"""
    
    def __init__(self, config, data_handler):
        """指定された設定でソケットサーバーを初期化します。
        
        Args:
            config (dict): サーバー設定
            data_handler (callable): 受信したデータを処理するコールバック関数
        """
        self.config = config
        self.data_handler = data_handler
        self.server_socket = None
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
    
    def start(self):
        """ソケットサーバーを開始します。"""
        with self.lock:
            if self.running:
                logger.warning("ソケットサーバーはすでに実行中です")
                return False
            
            try:
                # サーバーソケットの作成
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.server_socket.bind(('0.0.0.0', self.config["listen_port"]))
                self.server_socket.listen(5)
                self.server_socket.settimeout(1.0)  # 1秒のタイムアウトを設定
                
                # サーバーの実行フラグを設定
                self.running = True
                
                # サーバースレッドの開始
                self.thread = threading.Thread(target=self._run_server)
                self.thread.daemon = True
                self.thread.start()
                
                logger.info(f"ソケットサーバーがポート {self.config['listen_port']} で開始されました")
                return True
            
            except Exception as e:
                logger.error(f"ソケットサーバーの開始中にエラーが発生しました: {e}")
                if self.server_socket:
                    self.server_socket.close()
                    self.server_socket = None
                self.running = False
                return False
    
    def stop(self):
        """ソケットサーバーを停止します。"""
        with self.lock:
            if not self.running:
                logger.warning("ソケットサーバーはすでに停止しています")
                return False
            
            try:
                # サーバーの実行フラグをクリア
                self.running = False
                
                # サーバーソケットを閉じる
                if self.server_socket:
                    self.server_socket.close()
                    self.server_socket = None
                
                # サーバースレッドが終了するのを待つ
                if self.thread and self.thread.is_alive():
                    self.thread.join(timeout=5.0)
                
                logger.info("ソケットサーバーが停止しました")
                return True
            
            except Exception as e:
                logger.error(f"ソケットサーバーの停止中にエラーが発生しました: {e}")
                return False
    
    def _run_server(self):
        """サーバーのメインループを実行します。"""
        logger.info("ソケットサーバーのメインループを開始します")
        
        while self.running:
            try:
                # クライアント接続の受け入れ
                try:
                    client_socket, addr = self.server_socket.accept()
                    logger.info(f"クライアント接続を受け入れました: {addr}")
                    
                    # クライアント処理スレッドの開始
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                
                except socket.timeout:
                    # タイムアウトは正常な動作
                    continue
                
                except Exception as e:
                    if self.running:  # サーバーが実行中の場合のみエラーをログに記録
                        logger.error(f"クライアント接続の受け入れ中にエラーが発生しました: {e}")
                    continue
            
            except Exception as e:
                if self.running:  # サーバーが実行中の場合のみエラーをログに記録
                    logger.error(f"サーバーループでエラーが発生しました: {e}")
                time.sleep(1.0)  # エラー後に少し待機
        
        logger.info("ソケットサーバーのメインループを終了します")
    
    def _handle_client(self, client_socket, addr):
        """クライアント接続を処理します。
        
        Args:
            client_socket (socket.socket): クライアントソケット
            addr (tuple): クライアントアドレス (host, port)
        """
        try:
            # ソケットのタイムアウトを設定
            client_socket.settimeout(5.0)
            
            # データの受信
            data = b""
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                data += chunk
                
                # JSONの終端を検出
                if b"}" in chunk:
                    break
            
            # データが空でない場合は処理
            if data:
                try:
                    # JSONデータのデコード
                    json_data = json.loads(data.decode('utf-8'))
                    logger.debug(f"受信したデータ: {json_data}")
                    
                    # データハンドラーの呼び出し
                    if self.data_handler:
                        self.data_handler(json_data, addr)
                    
                    # 応答の送信
                    response = {"status": "ok", "message": "データを受信しました"}
                    client_socket.sendall(json.dumps(response).encode('utf-8'))
                
                except json.JSONDecodeError as e:
                    logger.error(f"JSONデコードエラー: {e}, データ: {data}")
                    response = {"status": "error", "message": "無効なJSONデータ"}
                    client_socket.sendall(json.dumps(response).encode('utf-8'))
                
                except Exception as e:
                    logger.error(f"データ処理中にエラーが発生しました: {e}")
                    response = {"status": "error", "message": f"データ処理エラー: {str(e)}"}
                    client_socket.sendall(json.dumps(response).encode('utf-8'))
        
        except socket.timeout:
            logger.warning(f"クライアント {addr} との通信がタイムアウトしました")
        
        except Exception as e:
            logger.error(f"クライアント {addr} の処理中にエラーが発生しました: {e}")
        
        finally:
            # クライアントソケットを閉じる
            try:
                client_socket.close()
            except:
                pass
            
            logger.debug(f"クライアント {addr} との接続を閉じました")
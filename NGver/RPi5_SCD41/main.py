#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCD41 環境データ測定システム メインスクリプト
Version: 1.0.0

このスクリプトは、SCD41センサーからのデータ収集とグラフ表示を一括で開始します。
データ収集は別プロセスで実行され、グラフ表示はメインプロセスで実行されます。

使用方法:
    python3 main.py [--data-dir DIR] [--interval SECONDS] [--days DAYS] [--refresh-interval SECONDS]
"""

import os
import sys
import argparse
import logging
import time
import subprocess
import signal
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scd41_main.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SCD41System:
    """SCD41環境データ測定システムの管理クラス"""
    
    def __init__(self, config=None):
        """システムの初期化"""
        self.config = config or {
            "data_dir": "data",
            "interval": 30,  # データ収集間隔（秒）
            "days": 1,  # グラフ表示日数
            "refresh_interval": 60,  # グラフ更新間隔（秒）
            "device_id": "SCD41"
        }
        
        # データディレクトリの作成
        os.makedirs(self.config["data_dir"], exist_ok=True)
        
        # データ収集プロセス
        self.collector_process = None
        
        # 終了フラグ
        self.running = False
    
    def start_data_collector(self):
        """データ収集プロセスの開始"""
        try:
            # データ収集スクリプトのパス
            collector_script = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "data_collection",
                "scd41_data_collector.py"
            )
            
            # コマンドライン引数の構築
            cmd = [
                sys.executable,
                collector_script,
                "--data-dir", self.config["data_dir"],
                "--interval", str(self.config["interval"]),
                "--device-id", self.config["device_id"]
            ]
            
            # プロセスの開始
            self.collector_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            logger.info(f"データ収集プロセスを開始しました (PID: {self.collector_process.pid})")
            
            # 標準出力と標準エラー出力の監視スレッド
            def monitor_output(pipe, is_error):
                prefix = "ERROR" if is_error else "INFO"
                for line in pipe:
                    logger.info(f"[Collector {prefix}] {line.strip()}")
            
            # 標準出力の監視スレッド
            stdout_thread = threading.Thread(
                target=monitor_output,
                args=(self.collector_process.stdout, False),
                daemon=True
            )
            stdout_thread.start()
            
            # 標準エラー出力の監視スレッド
            stderr_thread = threading.Thread(
                target=monitor_output,
                args=(self.collector_process.stderr, True),
                daemon=True
            )
            stderr_thread.start()
            
            return True
        except Exception as e:
            logger.error(f"データ収集プロセスの開始に失敗しました: {e}")
            return False
    
    def start_graph_viewer(self):
        """グラフビューアの開始"""
        try:
            # グラフビューアスクリプトのパス
            viewer_script = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "visualization",
                "scd41_graph_viewer.py"
            )
            
            # コマンドライン引数の構築
            cmd = [
                sys.executable,
                viewer_script,
                "--data-dir", self.config["data_dir"],
                "--days", str(self.config["days"]),
                "--refresh-interval", str(self.config["refresh_interval"]),
                "--device-id", self.config["device_id"]
            ]
            
            logger.info(f"グラフビューアを開始します: {' '.join(cmd)}")
            
            # プロセスの開始（ブロッキング）
            subprocess.run(cmd)
            
            return True
        except Exception as e:
            logger.error(f"グラフビューアの開始に失敗しました: {e}")
            return False
    
    def start(self):
        """システムの開始"""
        if not self.running:
            self.running = True
            
            # データ収集プロセスの開始
            if not self.start_data_collector():
                logger.error("データ収集プロセスの開始に失敗したため、システムを終了します")
                self.stop()
                return False
            
            # 少し待機してデータ収集が開始されるのを待つ
            time.sleep(2)
            
            # グラフビューアの開始
            self.start_graph_viewer()
            
            # グラフビューアが終了したらシステムも終了
            self.stop()
            
            return True
        
        return False
    
    def stop(self):
        """システムの停止"""
        if self.running:
            self.running = False
            
            # データ収集プロセスの停止
            if self.collector_process:
                logger.info("データ収集プロセスを停止しています...")
                try:
                    self.collector_process.terminate()
                    self.collector_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("データ収集プロセスが応答しないため、強制終了します")
                    self.collector_process.kill()
                
                logger.info("データ収集プロセスを停止しました")
                self.collector_process = None
            
            logger.info("システムを停止しました")
            
            return True
        
        return False

def signal_handler(sig, frame):
    """シグナルハンドラ"""
    logger.info(f"シグナル {sig} を受信しました、システムを停止します...")
    if 'system' in globals():
        system.stop()
    sys.exit(0)

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='SCD41環境データ測定システム')
    parser.add_argument('--data-dir', type=str, default='data', help='データ保存ディレクトリ')
    parser.add_argument('--interval', type=int, default=30, help='データ収集間隔（秒）')
    parser.add_argument('--days', type=int, default=1, help='グラフ表示日数')
    parser.add_argument('--refresh-interval', type=int, default=60, help='グラフ更新間隔（秒）')
    parser.add_argument('--device-id', type=str, default='SCD41', help='デバイスID')
    args = parser.parse_args()
    
    # 設定の作成
    config = {
        "data_dir": args.data_dir,
        "interval": args.interval,
        "days": args.days,
        "refresh_interval": args.refresh_interval,
        "device_id": args.device_id
    }
    
    # シグナルハンドラの登録
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # システムの作成と開始
    global system
    system = SCD41System(config)
    
    try:
        logger.info("SCD41環境データ測定システムを開始します...")
        system.start()
    except Exception as e:
        logger.error(f"システム実行中にエラーが発生しました: {e}")
        system.stop()
        sys.exit(1)

if __name__ == "__main__":
    main()
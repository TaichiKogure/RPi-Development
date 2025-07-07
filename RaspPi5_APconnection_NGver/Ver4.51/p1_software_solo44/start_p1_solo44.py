#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi 5 Unified Startup Script for Solo Version 4.44
Version: 4.44.0-solo

このスクリプトは、Raspberry Pi 5 (P1) のソロバージョン用に必要なすべてのサービスを起動します:
1. アクセスポイントのセットアップ
2. データ収集サービス (P2とP3の両方に対応)
3. Webインターフェース (P2とP3の両方に対応)
4. 接続モニター (P2とP3の両方に対応)

このスクリプトはシステム起動時に実行され、すべてのサービスが稼働していることを確認します。

使用方法:
    sudo ~/envmonitor-venv/bin/python3 start_p1_solo44.py

注意: このスクリプトは仮想環境のPythonインタープリターを使用して実行する必要があります。
"""

import os
import sys
import time
import subprocess
import argparse
import logging
import threading
import signal
import atexit

# 仮想環境のPythonインタープリターへのパス
VENV_PYTHON = "/home/pi/envmonitor-venv/bin/python3"

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/p1_startup_solo44.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# サービススクリプトへのパス
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AP_SETUP_SCRIPT = os.path.join(SCRIPT_DIR, "ap_setup", "P1_ap_setup_solo44.py")
DATA_COLLECTOR_SCRIPT = os.path.join(SCRIPT_DIR, "data_collection", "P1_data_collector_solo44.py")
WEB_INTERFACE_SCRIPT = os.path.join(SCRIPT_DIR, "web_interface", "P1_app_simple44.py")
CONNECTION_MONITOR_SCRIPT = os.path.join(SCRIPT_DIR, "connection_monitor", "P1_wifi_monitor_solo44.py")

# デフォルト設定
DEFAULT_CONFIG = {
    "data_dir": "/var/lib/raspap_solo/data",
    "rawdata_p2_dir": "RawData_P2",
    "rawdata_p3_dir": "RawData_P3",
    "web_port": 80,
    "api_port": 5001,
    "monitor_port": 5002,
    "monitor_interval": 5,  # 秒
    "interface": "wlan0",
    "ap_ssid": "RaspberryPi5_AP_Solo",
    "ap_ip": "192.168.0.1"
}

# プロセスオブジェクトを格納するグローバル変数
processes = {}

def check_root():
    """スクリプトがroot権限で実行されているか確認します。"""
    if os.geteuid() != 0:
        logger.error("このスクリプトはroot権限で実行する必要があります (sudo)")
        sys.exit(1)

def run_ap_setup():
    """アクセスポイントセットアップスクリプトを実行します。"""
    logger.info("アクセスポイントのセットアップを開始しています...")

    try:
        # まず、APが既に設定されているか確認
        result = subprocess.run(
            [VENV_PYTHON, AP_SETUP_SCRIPT, "--status"],
            capture_output=True,
            text=True
        )

        if "Access point is running correctly" in result.stdout:
            logger.info("アクセスポイントは既に設定され、実行中です")
            return True

        # アクセスポイントを設定して有効化
        logger.info("アクセスポイントを設定しています...")
        subprocess.run([VENV_PYTHON, AP_SETUP_SCRIPT, "--configure"], check=True)

        logger.info("アクセスポイントを有効化しています...")
        subprocess.run([VENV_PYTHON, AP_SETUP_SCRIPT, "--enable"], check=True)

        logger.info("アクセスポイントのセットアップが正常に完了しました")
        return True
    except subprocess.SubprocessError as e:
        logger.error(f"アクセスポイントのセットアップに失敗しました: {e}")
        return False

def start_data_collector(config):
    """データ収集サービスを開始します。"""
    logger.info("データ収集サービスを開始しています...")

    try:
        # 引数付きのコマンドを作成
        cmd = [
            VENV_PYTHON, DATA_COLLECTOR_SCRIPT,
            "--data-dir", config["data_dir"],
            "--api-port", str(config["api_port"])
        ]

        # プロセスを開始
        process = subprocess.Popen(cmd)
        processes["data_collector"] = process

        logger.info(f"データ収集サービスが開始されました (PID: {process.pid})")
        
        # データディレクトリが存在することを確認
        os.makedirs(os.path.join(config["data_dir"], config["rawdata_p2_dir"]), exist_ok=True)
        os.makedirs(os.path.join(config["data_dir"], config["rawdata_p3_dir"]), exist_ok=True)
        logger.info(f"P2とP3用のデータディレクトリが存在することを確認しました")
        
        return True
    except Exception as e:
        logger.error(f"データ収集サービスの開始に失敗しました: {e}")
        return False

def start_web_interface(config):
    """Webインターフェースを開始します。"""
    logger.info("Webインターフェースを開始しています...")

    try:
        # 引数付きのコマンドを作成
        cmd = [
            VENV_PYTHON, WEB_INTERFACE_SCRIPT,
            "--port", str(config["web_port"]),
            "--data-dir", config["data_dir"]
        ]

        # プロセスを開始
        process = subprocess.Popen(cmd)
        processes["web_interface"] = process

        logger.info(f"Webインターフェースがポート {config['web_port']} で開始されました (PID: {process.pid})")
        return True
    except Exception as e:
        logger.error(f"Webインターフェースの開始に失敗しました: {e}")
        return False

def start_connection_monitor(config):
    """接続モニターを開始します。"""
    logger.info("接続モニターを開始しています...")

    try:
        # 引数付きのコマンドを作成
        cmd = [
            VENV_PYTHON, CONNECTION_MONITOR_SCRIPT,
            "--interval", str(config["monitor_interval"]),
            "--interface", config["interface"]
        ]

        # プロセスを開始
        process = subprocess.Popen(cmd)
        processes["connection_monitor"] = process

        logger.info(f"接続モニターが開始されました (PID: {process.pid})")
        return True
    except Exception as e:
        logger.error(f"接続モニターの開始に失敗しました: {e}")
        return False

def cleanup():
    """終了時にプロセスをクリーンアップします。"""
    logger.info("プロセスをクリーンアップしています...")

    for name, process in processes.items():
        if process.poll() is None:  # プロセスがまだ実行中
            logger.info(f"{name} を終了しています (PID: {process.pid})...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning(f"{name} が正常に終了しませんでした、強制終了します...")
                process.kill()

def signal_handler(sig, frame):
    """シグナル（例：SIGINT、SIGTERM）を処理します。"""
    logger.info(f"シグナル {sig} を受信しました、シャットダウンします...")
    cleanup()
    sys.exit(0)

def monitor_processes():
    """実行中のプロセスを監視し、クラッシュした場合は再起動します。"""
    while True:
        status_message = "\n===== P1 サービスステータス (Ver 4.44) =====\n"
        all_services_ok = True

        for name, process in list(processes.items()):
            if process.poll() is None:  # プロセスが実行中
                status = "✓ 正常稼働中"
                status_message += f"{name}: {status} (PID: {process.pid})\n"
            else:  # プロセスが終了している
                status = "✗ 停止中"
                status_message += f"{name}: {status} (終了コード: {process.returncode})\n"
                all_services_ok = False
                logger.warning(f"{name} が予期せず終了しました (終了コード: {process.returncode})、再起動しています...")

                # 名前に基づいてプロセスを再起動
                if name == "data_collector":
                    start_data_collector(DEFAULT_CONFIG)
                elif name == "web_interface":
                    start_web_interface(DEFAULT_CONFIG)
                elif name == "connection_monitor":
                    start_connection_monitor(DEFAULT_CONFIG)

        # 全体的なステータスを追加
        if all_services_ok:
            status_message += "\n全サービスが正常に稼働しています。\n"
        else:
            status_message += "\n一部のサービスに問題があります。再起動を試みています。\n"

        status_message += "=============================\n"

        # ステータスをコンソールに表示
        print(status_message)

        # 10秒ごとにチェック
        time.sleep(10)

def main():
    """すべてのサービスを開始するメイン関数。"""
    parser = argparse.ArgumentParser(description="Raspberry Pi 5 Unified Startup Script for Solo Version 4.44")
    parser.add_argument("--data-dir", type=str, default=DEFAULT_CONFIG["data_dir"],
                        help=f"データを保存するディレクトリ (デフォルト: {DEFAULT_CONFIG['data_dir']})")
    parser.add_argument("--web-port", type=int, default=DEFAULT_CONFIG["web_port"],
                        help=f"Webインターフェース用ポート (デフォルト: {DEFAULT_CONFIG['web_port']})")
    parser.add_argument("--api-port", type=int, default=DEFAULT_CONFIG["api_port"],
                        help=f"データAPI用ポート (デフォルト: {DEFAULT_CONFIG['api_port']})")
    parser.add_argument("--monitor-port", type=int, default=DEFAULT_CONFIG["monitor_port"],
                        help=f"接続モニターAPI用ポート (デフォルト: {DEFAULT_CONFIG['monitor_port']})")
    parser.add_argument("--monitor-interval", type=int, default=DEFAULT_CONFIG["monitor_interval"],
                        help=f"監視間隔（秒） (デフォルト: {DEFAULT_CONFIG['monitor_interval']})")
    parser.add_argument("--interface", type=str, default=DEFAULT_CONFIG["interface"],
                        help=f"監視するWiFiインターフェース (デフォルト: {DEFAULT_CONFIG['interface']})")

    args = parser.parse_args()

    # コマンドライン引数で設定を更新
    config = DEFAULT_CONFIG.copy()
    config["data_dir"] = args.data_dir
    config["web_port"] = args.web_port
    config["api_port"] = args.api_port
    config["monitor_port"] = args.monitor_port
    config["monitor_interval"] = args.monitor_interval
    config["interface"] = args.interface

    # root権限で実行されているか確認
    check_root()

    # シグナルハンドラとクリーンアップ関数を登録
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup)

    # アクセスポイントのセットアップを実行
    if not run_ap_setup():
        logger.error("アクセスポイントのセットアップに失敗しました、終了します")
        sys.exit(1)

    # サービスを開始
    if not start_data_collector(config):
        logger.error("データ収集サービスの開始に失敗しました、終了します")
        sys.exit(1)

    if not start_web_interface(config):
        logger.error("Webインターフェースの開始に失敗しました、終了します")
        sys.exit(1)

    if not start_connection_monitor(config):
        logger.error("接続モニターの開始に失敗しました、終了します")
        sys.exit(1)

    logger.info("すべてのサービスが正常に開始されました")
    print("\n===== Raspberry Pi 5 環境モニター Ver4.44 =====")
    print("すべてのサービスが正常に開始されました！")
    print(f"- アクセスポイント: SSID={DEFAULT_CONFIG['ap_ssid']}, IP={DEFAULT_CONFIG['ap_ip']}")
    print(f"- Webインターフェース: http://{DEFAULT_CONFIG['ap_ip']}:{config['web_port']}")
    print(f"- データAPI: http://{DEFAULT_CONFIG['ap_ip']}:{config['api_port']}")
    print(f"- 接続モニターAPI: http://{DEFAULT_CONFIG['ap_ip']}:{config['monitor_port']}")
    print("- P2とP3のデータディレクトリが作成され、準備完了")
    print("====================================================\n")

    # 別スレッドでプロセスモニターを開始
    monitor_thread = threading.Thread(target=monitor_processes)
    monitor_thread.daemon = True
    monitor_thread.start()

    # メインスレッドを維持
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("キーボード割り込みを受信しました、シャットダウンします...")
        cleanup()
        sys.exit(0)

if __name__ == "__main__":
    main()
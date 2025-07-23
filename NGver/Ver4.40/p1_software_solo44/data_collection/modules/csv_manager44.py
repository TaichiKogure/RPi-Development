"""
CSVファイル管理モジュール for P1_data_collector_solo44.py
Version: 4.40
"""

import os
import csv
import logging
import datetime
import threading

# ロガーの設定
logger = logging.getLogger(__name__)

class CSVManager:
    """環境データを保存するためのCSVファイルを管理するクラス。"""
    
    def __init__(self, config):
        """指定された設定でCSVマネージャーを初期化します。"""
        self.config = config
        self.csv_files = {}
        self.csv_writers = {}
        self.fixed_csv_files = {}
        self.fixed_csv_writers = {}
        self.lock = threading.Lock()
        
        # データディレクトリの存在を確認
        os.makedirs(self.config["data_dir"], exist_ok=True)
        os.makedirs(os.path.join(self.config["data_dir"], self.config["rawdata_p2_dir"]), exist_ok=True)
        os.makedirs(os.path.join(self.config["data_dir"], self.config["rawdata_p3_dir"]), exist_ok=True)
        
        # CSVファイルの初期化
        self.init_csv_files()
    
    def init_csv_files(self):
        """データ保存用のCSVファイルを初期化します。"""
        with self.lock:
            # 今日の日付を取得
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            
            for device in ["P2", "P3"]:
                # 各デバイスに適切なディレクトリを決定
                device_dir = self.config["rawdata_p2_dir"] if device == "P2" else self.config["rawdata_p3_dir"]
                
                # 日付ベースのCSVファイル
                csv_path = os.path.join(self.config["data_dir"], device_dir, f"{device}_{today}.csv")
                file_exists = os.path.exists(csv_path)
                
                # ファイルを開いてライターを作成
                self.csv_files[device] = open(csv_path, 'a', newline='')
                self.csv_writers[device] = csv.writer(self.csv_files[device])
                
                # ファイルが新しい場合はヘッダーを書き込む
                if not file_exists:
                    self.csv_writers[device].writerow([
                        "timestamp", "device_id", "temperature", "humidity", 
                        "pressure", "gas_resistance", "co2", "absolute_humidity"
                    ])
                    self.csv_files[device].flush()
                
                # 固定CSVファイル
                fixed_csv_path = os.path.join(self.config["data_dir"], device_dir, f"{device}_fixed.csv")
                fixed_file_exists = os.path.exists(fixed_csv_path)
                
                # 固定ファイルを開いてライターを作成
                self.fixed_csv_files[device] = open(fixed_csv_path, 'a', newline='')
                self.fixed_csv_writers[device] = csv.writer(self.fixed_csv_files[device])
                
                # 固定ファイルが新しい場合はヘッダーを書き込む
                if not fixed_file_exists:
                    self.fixed_csv_writers[device].writerow([
                        "timestamp", "device_id", "temperature", "humidity", 
                        "pressure", "gas_resistance", "co2", "absolute_humidity"
                    ])
                    self.fixed_csv_files[device].flush()
            
            logger.info(f"CSVファイルが今日（{today}）と固定ファイル用に初期化されました")
    
    def rotate_csv_files(self):
        """日付またはサイズに基づいてCSVファイルをローテーションします。"""
        with self.lock:
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            
            for device in ["P2", "P3"]:
                # 現在の日付ベースのファイルを閉じる
                self.csv_files[device].close()
                
                # 各デバイスに適切なディレクトリを決定
                device_dir = self.config["rawdata_p2_dir"] if device == "P2" else self.config["rawdata_p3_dir"]
                
                # 今日の新しいファイルを作成
                csv_path = os.path.join(self.config["data_dir"], device_dir, f"{device}_{today}.csv")
                file_exists = os.path.exists(csv_path)
                
                self.csv_files[device] = open(csv_path, 'a', newline='')
                self.csv_writers[device] = csv.writer(self.csv_files[device])
                
                # ファイルが新しい場合はヘッダーを書き込む
                if not file_exists:
                    self.csv_writers[device].writerow([
                        "timestamp", "device_id", "temperature", "humidity", 
                        "pressure", "gas_resistance", "co2", "absolute_humidity"
                    ])
                    self.csv_files[device].flush()
            
            logger.info(f"CSVファイルが今日（{today}）用にローテーションされました")
    
    def cleanup_old_files(self):
        """古いCSVファイルをクリーンアップします。"""
        with self.lock:
            # 保持期間を超えたファイルを削除
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=self.config["rotation_interval_days"])
            cutoff_str = cutoff_date.strftime("%Y-%m-%d")
            
            for device in ["P2", "P3"]:
                # 各デバイスに適切なディレクトリを決定
                device_dir = self.config["rawdata_p2_dir"] if device == "P2" else self.config["rawdata_p3_dir"]
                dir_path = os.path.join(self.config["data_dir"], device_dir)
                
                # ディレクトリ内のファイルをチェック
                for filename in os.listdir(dir_path):
                    if not filename.startswith(device + "_") or not filename.endswith(".csv"):
                        continue
                    
                    # 固定ファイルはスキップ
                    if filename == f"{device}_fixed.csv":
                        continue
                    
                    # ファイル名から日付を抽出
                    try:
                        file_date = filename.split("_")[1].split(".")[0]
                        if file_date < cutoff_str:
                            file_path = os.path.join(dir_path, filename)
                            os.remove(file_path)
                            logger.info(f"古いCSVファイルを削除しました: {file_path}")
                    except (IndexError, ValueError) as e:
                        logger.warning(f"ファイル名の解析中にエラーが発生しました: {filename}, {e}")
    
    def write_data(self, data):
        """データをCSVファイルに書き込みます。"""
        with self.lock:
            device_id = data.get("device_id")
            if device_id not in ["P2", "P3"]:
                logger.error(f"無効なデバイスID: {device_id}")
                return False
            
            # データ行を作成
            row = [
                data.get("timestamp", int(datetime.datetime.now().timestamp())),
                device_id,
                data.get("temperature", ""),
                data.get("humidity", ""),
                data.get("pressure", ""),
                data.get("gas_resistance", ""),
                data.get("co2", ""),
                data.get("absolute_humidity", "")
            ]
            
            # 日付ベースのCSVファイルに書き込む
            self.csv_writers[device_id].writerow(row)
            self.csv_files[device_id].flush()
            
            # 固定CSVファイルに書き込む
            # 固定ファイルを一度クリアして最新のデータのみを保持
            self.fixed_csv_files[device_id].close()
            device_dir = self.config["rawdata_p2_dir"] if device_id == "P2" else self.config["rawdata_p3_dir"]
            fixed_csv_path = os.path.join(self.config["data_dir"], device_dir, f"{device_id}_fixed.csv")
            
            # 新しい固定ファイルを作成
            self.fixed_csv_files[device_id] = open(fixed_csv_path, 'w', newline='')
            self.fixed_csv_writers[device_id] = csv.writer(self.fixed_csv_files[device_id])
            
            # ヘッダーを書き込む
            self.fixed_csv_writers[device_id].writerow([
                "timestamp", "device_id", "temperature", "humidity", 
                "pressure", "gas_resistance", "co2", "absolute_humidity"
            ])
            
            # データを書き込む
            self.fixed_csv_writers[device_id].writerow(row)
            self.fixed_csv_files[device_id].flush()
            
            return True
    
    def close(self):
        """すべてのCSVファイルを閉じます。"""
        with self.lock:
            for device in ["P2", "P3"]:
                if device in self.csv_files:
                    self.csv_files[device].close()
                if device in self.fixed_csv_files:
                    self.fixed_csv_files[device].close()
            
            logger.info("すべてのCSVファイルが閉じられました")
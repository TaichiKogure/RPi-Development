# P1_data_collector_solo.pyのインポートエラー修正

## 問題の説明

プロジェクトで`P1_data_collector_solo.py`スクリプトを実行する際に次のエラーが発生していました：

```
2025-07-07 11:42:17,337 - WARNING - Failed to import refactored modules: No module named 'p1_software_solo405'
2025-07-07 11:42:17,337 - INFO - Falling back to original implementation
Traceback (most recent call last):
  File "/home/pi/RaspPi5_APconnection/Ver4.61Debug/p1_software_solo405/data_collection/P1_data_collector_solo.py", line 592, in <module>
    main()
  File "/home/pi/RaspPi5_APconnection/Ver4.61Debug/p1_software_solo405/data_collection/P1_data_collector_solo.py", line 559, in main
    config = DEFAULT_CONFIG.copy()
             ^^^^^^^^^^^^^^
NameError: name 'DEFAULT_CONFIG' is not defined
```

このエラーが発生した理由：
1. スクリプトがリファクタリングされたモジュールからインポートしようとしましたが、`p1_software_solo405`パッケージが見つかりませんでした
2. インポートが失敗した際に、フォールバック（代替）の定義なしに`DEFAULT_CONFIG`を使用しようとしました

## 根本原因

スクリプトにはいくつかの問題がありました：

1. **Pythonパスの設定が不足**：スクリプトは親ディレクトリをPythonパスに正しく追加していなかったため、`p1_software_solo405`パッケージを見つけることができませんでした。

2. **インポート失敗時のフォールバックがない**：インポートが失敗した際に、フォールバックを定義せずに`DEFAULT_CONFIG`を使用しようとしました。

3. **必要なインポートの不足**：スクリプトは複数のモジュール（`threading`、`datetime`、`json`、`csv`、`socket`、`time`）をインポートせずに使用していました。

4. **不完全なインポートエラー処理**：スクリプトは1つの場所からのみインポートを試み、堅牢なフォールバックメカニズムがありませんでした。

## 解決策

解決策はいくつかの変更を含みます：

1. **不足しているインポートの追加**：
   ```python
   import threading
   import datetime
   import json
   import csv
   import socket
   import time
   ```

2. **フォールバック設定の定義**：
   ```python
   # インポートが失敗した場合のフォールバック設定を定義
   FALLBACK_DEFAULT_CONFIG = {
       "listen_port": 5000,
       "data_dir": "/var/lib/raspap_solo/data",
       "rawdata_p2_dir": "RawData_P2",
       "rawdata_p3_dir": "RawData_P3",
       "api_port": 5001,
       "max_file_size_mb": 10,
       "rotation_interval_days": 7,
       "device_timeout_seconds": 120
   }

   FALLBACK_MONITOR_CONFIG = {
       "devices": {
           "P2": {
               "ip": None,
               "mac": None,
               "channel": 6
           },
           "P3": {
               "ip": None,
               "mac": None,
               "channel": 6
           }
       },
       "update_interval": 5,
       "ping_count": 3,
       "ping_timeout": 1
   }
   ```

3. **インポートエラー処理の改善**：
   ```python
   # リファクタリングされたモジュールからインポート
   try:
       # リファクタリングされたパッケージ構造からインポートを試みる
       from p1_software_solo405.data_collection.config import DEFAULT_CONFIG, MONITOR_CONFIG
       from p1_software_solo405.data_collection.main import DataCollector, main as refactored_main
       logger.info("Successfully imported refactored modules from p1_software_solo405 package")
       # リファクタリングされた実装を使用
       if __name__ == "__main__":
           refactored_main()
           sys.exit(0)
   except ImportError as e:
       logger.warning(f"Failed to import from p1_software_solo405 package: {e}")
       
       # 相対パスからのインポートを試みる
       try:
           from data_collection.config import DEFAULT_CONFIG, MONITOR_CONFIG
           from data_collection.main import DataCollector, main as refactored_main
           logger.info("Successfully imported refactored modules from relative path")
           # リファクタリングされた実装を使用
           if __name__ == "__main__":
               refactored_main()
               sys.exit(0)
       except ImportError as e:
           logger.warning(f"Failed to import from relative path: {e}")
           logger.info("Falling back to original implementation")
           # フォールバック設定を使用
           DEFAULT_CONFIG = FALLBACK_DEFAULT_CONFIG
           MONITOR_CONFIG = FALLBACK_MONITOR_CONFIG
           # 以下、元の実装を続行
   ```

4. **FlaskとWiFiMonitorの堅牢なインポート**：
   ```python
   # API用のFlaskをインポート
   try:
       from flask import Flask, jsonify, request
   except ImportError as e:
       logger.error(f"Failed to import Flask: {e}")
       logger.error("Flask is required for the API server. Please install it with 'pip install flask'.")
       sys.exit(1)

   # 動的IP追跡用のWiFiMonitorをインポート
   try:
       from p1_software_solo405.connection_monitor.monitor import WiFiMonitor
   except ImportError:
       try:
           from connection_monitor.monitor import WiFiMonitor
       except ImportError:
           logger.warning("Failed to import WiFiMonitor. Dynamic IP tracking will be disabled.")
           WiFiMonitor = None
   ```

## 修正のテスト

修正が機能することを確認するには：

1. `P1_data_collector_solo.py`スクリプトを直接実行します：
   ```
   python p1_software_solo405/data_collection/P1_data_collector_solo.py
   ```

2. エラーが発生せず、スクリプトが期待通りに実行されることを確認します。

3. `start_p1_solo.py`から呼び出した場合もスクリプトが機能することを確認します。

## Pythonインポートのベストプラクティス

今後同様の問題を避けるために、以下のベストプラクティスを検討してください：

1. **失敗する可能性のあるインポートには常にフォールバックを提供する**：インポートが失敗した場合に使用できるデフォルト設定や代替実装を定義します。

2. **必要なすべてのインポートをファイルの先頭に追加する**：スクリプトで使用されるすべてのモジュールがファイルの先頭でインポートされていることを確認します。

3. **失敗する可能性のあるインポートにはtry-exceptブロックを使用する**：これにより、スクリプトはインポートエラーを適切に処理できます。

4. **親ディレクトリをPythonパスに追加する**：これにより、スクリプトが親ディレクトリ内のパッケージを見つけることができます。

5. **可能な限り絶対インポートを使用する**：絶対インポートはより明示的であり、プロジェクト構造が変更された場合にエラーが発生しにくくなります。
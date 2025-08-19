# 接続モニターのインポートパス問題の修正

## 概要
このドキュメントでは、Raspberry Pi 5環境モニタリングシステムの接続モニターモジュールで発生していたインポートパスの問題に対する解決策を説明します。この問題により、システムが`p1_software_solo405`パッケージからモジュールを正しくインポートできなくなっていました。

## 問題の説明
システムは以下のようなエラーに遭遇していました：
- `Failed to import refactored modules from p1_software_solo405 package: No module named 'p1_software_solo405'`
- `Failed to import refactored modules from relative path: No module named 'p1_software_solo405'`
- `Cannot continue without required modules`

これらのエラーは、Pythonインタープリタが検索パスで`p1_software_solo405`パッケージを見つけられなかったために発生しました。これは、パッケージ構造の一部であるPythonスクリプトを直接実行する場合によく発生する問題です。

## 解決策
解決策は、`P1_wifi_monitor_solo.py`ファイルに堅牢なインポート戦略を実装することでした：

### 1. 親ディレクトリをPythonパスに追加
まず、`p1_software_solo405`パッケージからのインポートを可能にするために、親ディレクトリをPythonパスに追加します：

```python
# p1_software_solo405からインポートできるように親ディレクトリをPythonパスに追加
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
```

これにより、Pythonインタープリタがモジュールをインポートする際に`p1_software_solo405`パッケージを見つけることができます。

### 2. 二段階インポート戦略の実装
次に、二段階インポート戦略を実装します：

```python
try:
    # リファクタリングされたパッケージ構造からのインポートを試みる
    from p1_software_solo405.connection_monitor.config import DEFAULT_CONFIG, ensure_log_directory
    from p1_software_solo405.connection_monitor.monitor import WiFiMonitor
    from p1_software_solo405.connection_monitor.utils.console import print_connection_status
    logger.info("Successfully imported refactored modules from p1_software_Zero package")
except ImportError as e:
    logger.error(f"Failed to import refactored modules from p1_software_Zero package: {e}")
    
    # 相対パスからのインポートを試みる
    try:
        from connection_monitor.config import DEFAULT_CONFIG, ensure_log_directory
        from connection_monitor.monitor import WiFiMonitor
        from connection_monitor.utils.console import print_connection_status
        logger.info("Successfully imported refactored modules from relative path")
    except ImportError as e:
        logger.error(f"Failed to import refactored modules from relative path: {e}")
        logger.error("Cannot continue without required modules")
        sys.exit(1)
```

このアプローチは：
1. まず、パッケージ構造（`p1_software_solo405.connection_monitor.*`）からのインポートを試みます
2. それが失敗した場合、相対インポート（`connection_monitor.*`）にフォールバックします

### 3. 適切なロギング設定
また、インポートが試みられる前にロギングが適切に設定されていることを確認します：

```python
# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/wifi_monitor_solo.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
```

これにより、インポートエラーがデバッグのために適切にログに記録されます。

### 4. 堅牢なメイン関数
最後に、同じインポート戦略を使用し、コマンドライン引数を直接処理してWiFiモニターを起動するようにメイン関数を更新します：

```python
def main():
    """WiFiモニターを解析して起動するためのメイン関数。"""
    try:
        # リファクタリングされたパッケージ構造からのインポートを試みる
        from p1_software_solo405.connection_monitor.main import main as refactored_main
        logger.info("Successfully imported main function from p1_software_Zero package")
    except ImportError as e:
        logger.error(f"Failed to import main function from p1_software_Zero package: {e}")
        
        # 相対パスからのインポートを試みる
        try:
            from connection_monitor.main import main as refactored_main
            logger.info("Successfully imported main function from relative path")
        except ImportError as e:
            logger.error(f"Failed to import main function from relative path: {e}")
            logger.error("Cannot continue without required modules")
            sys.exit(1)
    
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='WiFi接続モニター')
    parser.add_argument('--interval', type=int, default=5, help='モニタリング間隔（秒）')
    parser.add_argument('--interface', type=str, default='wlan0', help='モニタリングするWiFiインターフェース')
    parser.add_argument('--port', type=int, default=5002, help='APIサーバーのポート')
    args = parser.parse_args()
    
    # 設定の更新
    config = DEFAULT_CONFIG.copy()
    config['update_interval'] = args.interval
    config['interface'] = args.interface
    config['port'] = args.port
    
    # WiFiモニターの起動
    try:
        logger.info("WiFiモニターを起動しています...")
        monitor = WiFiMonitor(config)
        monitor.run()
    except KeyboardInterrupt:
        logger.info("キーボード割り込みを受信しました、シャットダウンします...")
    except Exception as e:
        logger.error(f"WiFiモニターでエラーが発生しました: {e}")
        sys.exit(1)
```

これにより、モジュールはより堅牢になり、リファクタリングされたコードの特定の構造に依存しなくなります。

## 解決策の利点
1. **堅牢性の向上**：システムが異なる実行環境を処理できるようになりました。
2. **エラー処理の改善**：詳細なエラーメッセージがインポートの問題を診断するのに役立ちます。
3. **柔軟なインポート戦略**：二段階インポート戦略は、コードがパッケージとして実行されるか直接実行されるかに関わらず機能します。
4. **適切なロギング**：すべてのエラーがデバッグのために適切にログに記録されます。
5. **直接実行**：モジュールはリファクタリングされたコードに依存せずに直接実行できます。

## 結論
この堅牢なインポート戦略を実装することで、接続モニターモジュールのインポートパスの問題を修正しました。システムは、スクリプトがどのように実行されるかに関わらず、`p1_software_solo405`パッケージからモジュールを適切にインポートできるようになりました。
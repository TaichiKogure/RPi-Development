# インポートエラー修正ドキュメント

## 問題の説明

プロジェクトでは、`P1_wifi_monitor_solo.py`スクリプトを直接実行すると、以下のようなインポートエラーが発生していました：

```
ImportError: attempted relative import with no known parent package
```

このエラーは、スクリプトが相対インポート（例：`from .config import DEFAULT_CONFIG`）を使用していたが、パッケージの一部としてではなくスタンドアロンスクリプトとして実行されていたために発生しました。

## 根本原因

Pythonでは、相対インポート（ドット`.`で始まるもの）は、モジュールがパッケージの一部であり、インポートされている場合にのみ使用できます。モジュールが直接実行されている場合は使用できません。

Pythonファイルが直接実行される場合（例：`python filename.py`）、それは「メイン」モジュールとして扱われ、親パッケージを持たないため、相対インポートを解決できません。

`P1_wifi_monitor_solo.py`での具体的な問題のあるインポートは以下の通りでした：

```python
from .config import DEFAULT_CONFIG, ensure_log_directory
from .monitor import WiFiMonitor
from .utils.console import print_connection_status
from .main import main as refactored_main
```

## 解決策

解決策には2つの重要な変更が含まれています：

1. **相対インポートを絶対インポートに変更**：
   ```python
   from connection_monitor.config import DEFAULT_CONFIG, ensure_log_directory
   from connection_monitor.monitor import WiFiMonitor
   from connection_monitor.utils.console import print_connection_status
   from connection_monitor.main import main as refactored_main
   ```

2. **親ディレクトリがPythonパスに含まれるようにするコードを追加**：
   ```python
   # connection_monitorからインポートできるように親ディレクトリをPythonパスに追加
   parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
   if parent_dir not in sys.path:
       sys.path.insert(0, parent_dir)
   ```

これにより、`P1_wifi_monitor_solo.py`が直接実行されたとき、Pythonが`connection_monitor`パッケージを見つけることができるようになります。

## Pythonインポートのベストプラクティス

将来同様の問題を避けるために、以下のベストプラクティスを検討してください：

1. **可能な限り絶対インポートを使用する**：絶対インポートはより明示的であり、プロジェクト構造が変更されたときにエラーが発生しにくくなります。

2. **コードを適切なPythonパッケージとして整理する**：Pythonモジュールを含む各ディレクトリに`__init__.py`ファイルがあることを確認してください。

3. **適切なPythonパッケージ構造を使用することを検討する**：プロジェクトがライブラリとしてインストールまたは使用されることを意図している場合は、setup.pyファイルを使用し、開発モードでインストールすることを検討してください。

4. **スクリプトを直接実行するとき、Pythonパスが正しく設定されていることを確認する**：これは、解決策に示されているように親ディレクトリを`sys.path`に追加するか、`PYTHONPATH`環境変数を使用することで行うことができます。

5. **パッケージ内のモジュールを実行するときは`-m`フラグを使用する**：例えば、`python package/module.py`の代わりに`python -m package.module`を使用します。

## 修正のテスト

修正が機能することを確認するには：

1. `P1_wifi_monitor_solo.py`スクリプトを直接実行します：
   ```
   python p1_software_solo405/connection_monitor/P1_wifi_monitor_solo.py
   ```

2. インポートエラーが発生せず、スクリプトが期待通りに実行されることを確認します。

3. スクリプトが`start_p1_solo.py`から呼び出されたときにも正常に動作することを確認します。
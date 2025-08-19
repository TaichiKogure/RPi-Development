# P1_app_solo.py から P1_app_solo_new.py への移行ガイド

## 概要

このドキュメントでは、`P1_app_solo.py` から `P1_app_solo_new.py` への移行に関する変更点と実装の詳細について説明します。この移行は、コードの保守性と拡張性を向上させるために行われました。

## 変更内容

### 1. start_p1_solo.py の変更

`start_p1_solo.py` ファイルの以下の行を変更しました：

```python
# 変更前
WEB_INTERFACE_SCRIPT = os.path.join(SCRIPT_DIR, "web_interface", "P1_app_solo.py")

# 変更後
WEB_INTERFACE_SCRIPT = os.path.join(SCRIPT_DIR, "web_interface", "P1_app_solo_new.py")
```

この変更により、システム起動時に `P1_app_solo_new.py` が実行されるようになります。

### 2. P1_app_solo_new.py のインポートパスの問題の解決

`P1_app_solo_new.py` のインポート部分を以下のように変更しました：

```python
# Import from the refactored modules
try:
    # First try to import using the package name
    try:
        from p1_software_solo405.web_interface.main import WebInterface, main as refactored_main
        from p1_software_solo405.web_interface.config import DEFAULT_CONFIG
        logger.info("Successfully imported refactored modules from p1_software_Zero package")
    except ImportError as e:
        logger.warning(f"Failed to import refactored modules from p1_software_Zero package: {e}")
        
        # Try to import using relative path
        try:
            import sys
            import os
            # Add the parent directory to the Python path
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from web_interface.main import WebInterface, main as refactored_main
            from web_interface.config import DEFAULT_CONFIG
            logger.info("Successfully imported refactored modules from relative path")
        except ImportError as e:
            logger.error(f"Failed to import refactored modules from relative path: {e}")
            raise
    
except ImportError as e:
    logger.error(f"Cannot continue without required modules: {e}")
    sys.exit(1)
```

この変更により、以下の2つの方法でモジュールをインポートしようとします：
1. まず、`p1_software_solo405.web_interface.main` のようにパッケージ名を使用してインポートを試みます。
2. それが失敗した場合、親ディレクトリをPythonパスに追加し、`web_interface.main` のように相対パスを使用してインポートを試みます。

### 3. P1_app_solo_new.py のコマンドライン引数処理の修正

`P1_app_solo_new.py` の `main()` 関数を以下のように変更しました：

```python
def main():
    """Main entry point for the web interface."""
    parser = argparse.ArgumentParser(description='Web Interface')
    parser.add_argument('--port', type=int, help='Port to listen on')
    parser.add_argument('--data-dir', type=str, help='Data directory')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    # Create a list of arguments to pass to refactored_main
    refactored_args = []
    if args.port:
        refactored_args.extend(['--port', str(args.port)])
    if args.data_dir:
        refactored_args.extend(['--data-dir', args.data_dir])
    if args.debug:
        refactored_args.append('--debug')
    
    # Update sys.argv to include the parsed arguments
    sys.argv = [sys.argv[0]] + refactored_args
    
    # Call the refactored main function with the updated arguments
    logger.info(f"Calling refactored_main with arguments: {refactored_args}")
    refactored_main()
```

この変更により、`start_p1_solo.py` から渡されるコマンドライン引数（特に `--port` と `--data-dir`）が `P1_app_solo_new.py` で正しく処理され、`refactored_main()` に渡されるようになります。

## 移行手順

1. 上記の変更を実装します。
2. 開発環境で `P1_app_solo_new.py` を使用してテストを行い、すべての機能が正常に動作することを確認します。
3. 本番環境の一部のシステムで `P1_app_solo_new.py` を使用し、実際の運用条件下でのパフォーマンスと安定性を評価します。
4. 問題がなければ、すべてのシステムを `P1_app_solo_new.py` に移行します。
5. 移行後も、しばらくの間は `P1_app_solo.py` を保持し、必要に応じて元に戻せるようにします。

## 注意事項

- この移行により、ウェブインターフェースの動作や外観に微妙な変化が生じる可能性があります。
- 問題が発生した場合は、`start_p1_solo.py` の `WEB_INTERFACE_SCRIPT` を元の `P1_app_solo.py` に戻すことで、以前の実装に戻すことができます。

# Migration Guide from P1_app_solo.py to P1_app_solo_new.py

## Overview

This document explains the changes and implementation details for migrating from `P1_app_solo.py` to `P1_app_solo_new.py`. This migration was performed to improve code maintainability and extensibility.

## Changes Made

### 1. Changes to start_p1_solo.py

The following line in the `start_p1_solo.py` file was changed:

```python
# Before
WEB_INTERFACE_SCRIPT = os.path.join(SCRIPT_DIR, "web_interface", "P1_app_solo.py")

# After
WEB_INTERFACE_SCRIPT = os.path.join(SCRIPT_DIR, "web_interface", "P1_app_solo_new.py")
```

With this change, `P1_app_solo_new.py` will be executed at system startup.

### 2. Resolving Import Path Issues in P1_app_solo_new.py

The import section of `P1_app_solo_new.py` was changed as follows:

```python
# Import from the refactored modules
try:
    # First try to import using the package name
    try:
        from p1_software_solo405.web_interface.main import WebInterface, main as refactored_main
        from p1_software_solo405.web_interface.config import DEFAULT_CONFIG
        logger.info("Successfully imported refactored modules from p1_software_Zero package")
    except ImportError as e:
        logger.warning(f"Failed to import refactored modules from p1_software_Zero package: {e}")
        
        # Try to import using relative path
        try:
            import sys
            import os
            # Add the parent directory to the Python path
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from web_interface.main import WebInterface, main as refactored_main
            from web_interface.config import DEFAULT_CONFIG
            logger.info("Successfully imported refactored modules from relative path")
        except ImportError as e:
            logger.error(f"Failed to import refactored modules from relative path: {e}")
            raise
    
except ImportError as e:
    logger.error(f"Cannot continue without required modules: {e}")
    sys.exit(1)
```

With this change, the code attempts to import modules in two ways:
1. First, it tries to import using the package name, like `p1_software_solo405.web_interface.main`.
2. If that fails, it adds the parent directory to the Python path and tries to import using a relative path, like `web_interface.main`.

### 3. Fixing Command Line Argument Handling in P1_app_solo_new.py

The `main()` function in `P1_app_solo_new.py` was changed as follows:

```python
def main():
    """Main entry point for the web interface."""
    parser = argparse.ArgumentParser(description='Web Interface')
    parser.add_argument('--port', type=int, help='Port to listen on')
    parser.add_argument('--data-dir', type=str, help='Data directory')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    # Create a list of arguments to pass to refactored_main
    refactored_args = []
    if args.port:
        refactored_args.extend(['--port', str(args.port)])
    if args.data_dir:
        refactored_args.extend(['--data-dir', args.data_dir])
    if args.debug:
        refactored_args.append('--debug')
    
    # Update sys.argv to include the parsed arguments
    sys.argv = [sys.argv[0]] + refactored_args
    
    # Call the refactored main function with the updated arguments
    logger.info(f"Calling refactored_main with arguments: {refactored_args}")
    refactored_main()
```

With this change, command line arguments passed from `start_p1_solo.py` (especially `--port` and `--data-dir`) will be properly processed in `P1_app_solo_new.py` and passed to `refactored_main()`.

## Migration Procedure

1. Implement the changes described above.
2. Test using `P1_app_solo_new.py` in a development environment to ensure all functionality works correctly.
3. Use `P1_app_solo_new.py` on a subset of production systems to evaluate performance and stability under actual operating conditions.
4. If there are no issues, migrate all systems to `P1_app_solo_new.py`.
5. Keep `P1_app_solo.py` for a while after migration, so you can revert if necessary.

## Notes

- This migration may result in subtle changes in the behavior or appearance of the web interface.
- If problems occur, you can revert to the previous implementation by changing the `WEB_INTERFACE_SCRIPT` in `start_p1_solo.py` back to `P1_app_solo.py`.
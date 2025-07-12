# P1_data_collector_solo_new.pyとstart_p1_solo.pyの統合

## 概要
このドキュメントでは、新しいモジュラーデータ収集システム（`P1_data_collector_solo_new.py`）と統合起動スクリプト（`start_p1_solo.py`）の統合について説明します。この統合により、起動スクリプトが非推奨の単一ファイル版の代わりに、新しいデータ収集モジュールを正しく起動することが保証されます。

## 変更点

### 1. スクリプト参照の更新
起動スクリプトが新しいデータ収集モジュールを参照するように更新されました：

```python
# 古い参照
DATA_COLLECTOR_SCRIPT = os.path.join(SCRIPT_DIR, "data_collection", "P1_data_collector_solo.py")

# 新しい参照
DATA_COLLECTOR_SCRIPT = os.path.join(SCRIPT_DIR, "data_collection", "P1_data_collector_solo_new.py")
```

### 2. コマンドライン引数の強化
データ収集モジュールを起動するコマンドが、リッスンポートを明示的に含むように強化されました：

```python
# 古いコマンド
cmd = [
    VENV_PYTHON, DATA_COLLECTOR_SCRIPT,
    "--data-dir", config["data_dir"],
    "--api-port", str(config["api_port"])
]

# 新しいコマンド
cmd = [
    VENV_PYTHON, DATA_COLLECTOR_SCRIPT,
    "--data-dir", config["data_dir"],
    "--listen-port", "5000",  # データコレクターのデフォルトリッスンポート
    "--api-port", str(config["api_port"])
]
```

これにより、統合がより明示的になり、将来必要に応じてリッスンポートをカスタマイズできるようになります。

### 3. バージョン番号の更新
ステータスメッセージのバージョン番号が現在のバージョンを反映するように更新されました：

```python
# 古いバージョン
status_message = "\n===== P1 Services Status (Ver 4.0) =====\n"
print("\n===== Raspberry Pi 5 Environmental Monitor Ver4.0 =====")

# 新しいバージョン
status_message = "\n===== P1 Services Status (Ver 4.62) =====\n"
print("\n===== Raspberry Pi 5 Environmental Monitor Ver4.62 =====")
```

## 検証
統合は以下の点を確認することで検証されました：
1. 起動スクリプトが新しいデータ収集モジュールを正しく参照している
2. データ収集モジュールに渡されるコマンドライン引数が正しい
3. データ収集モジュールがこれらの引数を受け入れる
4. ステータスメッセージのバージョン番号が最新である

## 統合の利点
1. **保守性の向上**：システムは保守と拡張が容易なモジュラーデータ収集モジュールを使用するようになりました。
2. **エラー処理の改善**：新しいモジュールはエラー処理とロギングが改善されています。
3. **モジュール性の強化**：システムはより明確な関心の分離を持つモジュラーになりました。
4. **最新のバージョン情報**：ステータスメッセージに正しいバージョン番号が表示されるようになりました。

## 使用方法
統合されたシステムは以前と同じ方法で使用できます：

```bash
sudo ~/envmonitor-venv/bin/python3 start_p1_solo.py
```

統合はユーザーに対して透過的であるため、使用方法に変更は必要ありません。
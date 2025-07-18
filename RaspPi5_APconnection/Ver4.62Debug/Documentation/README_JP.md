# Raspberry Pi 5 環境データシステム - バージョン4.6

このドキュメントでは、保守性と拡張性を向上させるためにリファクタリングされたRaspberry Pi 5環境データシステムの構造と使用方法について説明します。

## プロジェクト構造

プロジェクトは、より模块化され保守しやすい構造に再編成されました。主要なコンポーネントは以下の通りです：

### データ収集モジュール

データ収集モジュールは、P2およびP3センサーノードから環境データを受信して保存する役割を担っています。以下のコンポーネントにリファクタリングされました：

- **config.py**: データ収集システムの設定
- **main.py**: データ収集システムのメインエントリーポイント
- **api/**: 収集したデータにアクセスするためのAPIサーバー
  - **routes.py**: APIルートハンドラ
  - **server.py**: Flaskサーバーのセットアップ
- **network/**: P2およびP3デバイスとのネットワーク通信
  - **server.py**: データを受信するためのソケットサーバー
- **processing/**: データ処理と検証
  - **calculation.py**: 派生値（例：絶対湿度）を計算するための関数
  - **validation.py**: 受信したデータを検証するための関数
- **storage/**: データストレージ管理
  - **csv_manager.py**: CSVファイルを管理するための関数
  - **data_store.py**: メモリ内データストレージ

### Webインターフェースモジュール

Webインターフェースモジュールは、収集したデータを視覚化するためのWebベースのダッシュボードを提供します。以下のコンポーネントにリファクタリングされました：

- **config.py**: Webインターフェースの設定
- **main.py**: Webインターフェースのメインエントリーポイント
- **api/**: WebインターフェースからデータにアクセスするためのAPI
  - **routes.py**: APIルートハンドラ
- **data/**: データの読み込みと処理
  - **data_manager.py**: データを読み込んで処理するための関数
- **visualization/**: グラフ生成
  - **graph_generator.py**: グラフを生成するための関数
- **utils/**: ユーティリティ関数
  - **helper.py**: データをフォーマットするためのヘルパー関数
- **templates/**: HTMLテンプレート
  - **index.html**: メインダッシュボードテンプレート
- **static/**: 静的ファイル（CSS、JS）
  - **css/style.css**: カスタムCSSスタイル
  - **js/dashboard.js**: ダッシュボードJavaScript

## 使用方法

### start_p1_solo.pyを使用したすべてのサービスの実行（推奨）

システム全体を実行する最も簡単な方法は、`start_p1_solo.py`スクリプトを使用することです。このスクリプトは、以下のすべての必要なサービスを起動します：

1. アクセスポイントのセットアップ
2. データ収集サービス（P2とP3の両方用）
3. Webインターフェース（P2とP3の両方をサポート）
4. 接続モニター（P2とP3の両方用）

スクリプトを実行するには、以下のコマンドを使用します：

```bash
sudo ~/envmonitor-venv/bin/python3 start_p1_solo.py
```

注意：このスクリプトは、仮想環境のPythonインタープリターを使用して実行する必要があり、root権限が必要です。

オプション：
- `--data-dir DIR`: データを保存するディレクトリ（デフォルト：/var/lib/raspap_solo/data）
- `--web-port PORT`: Webインターフェース用のポート（デフォルト：80）
- `--api-port PORT`: データAPI用のポート（デフォルト：5001）
- `--monitor-port PORT`: 接続モニターAPI用のポート（デフォルト：5002）
- `--monitor-interval SECONDS`: モニタリング間隔（秒単位）（デフォルト：5）
- `--interface INTERFACE`: モニタリングするWiFiインターフェース（デフォルト：wlan0）

このスクリプトは以下を行います：
1. アクセスポイントがまだ実行されていない場合は、セットアップします
2. データ収集サービスを起動します
3. Webインターフェースを起動します
4. 接続モニターを起動します
5. すべてのサービスをモニタリングし、クラッシュした場合は再起動します

### 個別サービスの実行（上級者向け）

個別のサービスを別々に実行する必要がある場合は、以下のコマンドを使用できます：

#### データ収集システムの実行

データ収集システムを実行するには、以下のコマンドを使用します：

```bash
python -m p1_software_solo405.data_collection.main [--port PORT] [--data-dir DIR]
```

または、後方互換性のために：

```bash
python p1_software_solo405/data_collection/P1_data_collector_solo.py [--port PORT] [--data-dir DIR]
```

オプション：
- `--port PORT`: リッスンするポート（デフォルト：5000）
- `--data-dir DIR`: データディレクトリ（デフォルト：/var/lib/raspap_solo/data）

#### Webインターフェースの実行

Webインターフェースを実行するには、以下のコマンドを使用します：

```bash
python -m p1_software_solo405.web_interface.main [--port PORT] [--data-dir DIR] [--debug]
```

または、後方互換性のために：

```bash
python p1_software_solo405/web_interface/P1_app_solo.py [--port PORT] [--data-dir DIR] [--debug]
```

オプション：
- `--port PORT`: リッスンするポート（デフォルト：80）
- `--data-dir DIR`: データディレクトリ（デフォルト：/var/lib/raspap_solo/data）
- `--debug`: デバッグモードを有効にする

### Webインターフェースへのアクセス

Webインターフェースが実行されたら、Webブラウザを開いて以下のURLにアクセスします：

```
http://<raspberry-pi-ip>
```

ここで、`<raspberry-pi-ip>`はRaspberry Pi 5のIPアドレスです。

## 前のバージョンからの変更点

前のバージョンからの主な変更点は以下の通りです：

1. **モジュール構造**: コードはより模块化された構造に再編成され、各モジュールが特定の機能を担当するようになりました。

2. **絶対インポート**: すべてのインポートは絶対パスを使用するようになり、コードがより堅牢で保守しやすくなりました。

3. **関心の分離の向上**: コードは関心の分離が向上し、各モジュールが明確な責任を持つようになりました。

4. **ドキュメントの改善**: コードには、各モジュールの目的と機能を明確に説明する、より良いドキュメントが含まれるようになりました。

5. **エラー処理の強化**: コードベース全体でエラー処理が改善され、より良いロギングとより優雅なエラー回復が可能になりました。

## 開発ガイドライン

コードベースに変更を加える際は、以下のガイドラインに従ってください：

1. **モジュール構造の維持**: コードベースのモジュール構造を維持し、各モジュールが明確な責任を持つようにしてください。

2. **絶対インポートの使用**: すべてのインポートに絶対インポートを使用して、コードが堅牢で保守しやすいことを確認してください。

3. **変更の文書化**: 行った変更に対して明確なドキュメントを追加し、変更の目的と機能を説明してください。

4. **テストの追加**: 新しい機能や既存の機能への変更に対してテストを追加してください。

5. **PEP 8の遵守**: Pythonコードの PEP 8 スタイルガイドに従ってください。

## トラブルシューティング

問題が発生した場合は、以下のログファイルを確認してください：

- データ収集: `/var/log/data_collector_solo.log`
- Webインターフェース: `/var/log/web_interface_solo.log`

一般的な問題：

1. **データ収集が実行されていない**: `ps aux | grep data_collection`でデータ収集プロセスが実行されているか確認してください。実行されていない場合は、上記のコマンドで起動してください。

2. **Webインターフェースにアクセスできない**: `ps aux | grep web_interface`でWebインターフェースプロセスが実行されているか確認してください。実行されていない場合は、上記のコマンドで起動してください。

3. **データが表示されない**: データ収集プロセスがP2およびP3デバイスからデータを受信しているか確認してください。エラーがないかログファイルを確認してください。

4. **グラフが更新されない**: データ収集プロセスがデータを正しく保存しているか確認してください。エラーがないかログファイルを確認してください。

# Web Interface モジュールガイド

## 概要
Web Interfaceモジュールは、Raspberry Pi 5（P1）上で動作し、P2、P3、P4、P5、P6デバイスから収集された環境データを可視化するためのウェブインターフェースを提供します。Ver2.0では、BME680センサーのみをサポートし、CO2センサー（MH-Z19C）はサポートしていません。

## ディレクトリ構造
Web Interfaceモジュールは以下のディレクトリ構造で構成されています：

```
web_interface/
├── api/                  # API関連のコード
│   ├── routes.py         # APIルートハンドラ
│   └── __init__.py       # パッケージ初期化ファイル
├── data/                 # データ管理コード
│   ├── data_manager.py   # データマネージャ
│   └── __init__.py       # パッケージ初期化ファイル
├── utils/                # ユーティリティ関数
│   ├── helper.py         # ヘルパー関数
│   └── __init__.py       # パッケージ初期化ファイル
├── visualization/        # データ可視化コード
│   ├── graph_generator.py # グラフジェネレータ
│   └── __init__.py       # パッケージ初期化ファイル
├── static/               # 静的ファイル（CSS、JavaScript、画像）
│   ├── css/              # CSSファイル
│   ├── js/               # JavaScriptファイル
│   └── img/              # 画像ファイル
├── templates/            # HTMLテンプレート
├── config.py             # 設定ファイル
├── main.py               # メインモジュール
├── P1_app_solo.py        # フル機能ウェブアプリ
├── P1_app_solo_new.py    # リファクタリングされたウェブアプリ
└── P1_app_simple.py      # 簡易ウェブアプリ（リソース使用量削減）
```

## メインプログラムファイル

### P1_app_solo.py
**役割**: フル機能ウェブインターフェース  
**説明**: このファイルは、P2、P3、P4、P5、P6デバイスからのデータを可視化するためのフル機能ウェブインターフェースを提供します。時系列グラフ、ダッシュボード、データエクスポート機能などが含まれています。Ver2.0では、CO2センサー機能は無効化されています。  
**使用シーン**: 高度なデータ可視化が必要な場合に使用します。

```bash
python3 P1_app_solo.py
```

オプションで、ポートとデータディレクトリを指定することもできます：

```bash
python3 P1_app_solo.py --port 80 --data-dir /path/to/data
```

### P1_app_simple.py
**役割**: 簡易ウェブインターフェース（リソース使用量削減）  
**説明**: このファイルは、P2、P3、P4、P5、P6デバイスからのデータを表示するための簡易ウェブインターフェースを提供します。グラフ可視化機能を省略し、テキストベースの表示のみを提供することでリソース使用量を削減しています。Ver2.0では、CO2センサー機能は無効化されています。  
**使用シーン**: リソース使用量を最小限に抑えたい場合や、テキストベースの表示で十分な場合に使用します。

```bash
python3 P1_app_simple.py
```

### P1_app_solo_new.py
**役割**: リファクタリングされたウェブインターフェース  
**説明**: このファイルは、リファクタリングされたモジュール構造を使用してウェブインターフェースを提供します。main.pyや他のモジュールを使用して、より整理された構造でウェブインターフェースを実装しています。Ver2.0では、CO2センサー機能は無効化されています。  
**使用シーン**: 最新のコード構造を使用したい場合に使用します。

```bash
python3 P1_app_solo_new.py
```

### main.py
**役割**: リファクタリングされたウェブインターフェースのメインモジュール  
**説明**: このファイルは、リファクタリングされたウェブインターフェースのメインモジュールです。WebInterfaceクラスを定義し、データ管理、可視化、APIなどのコンポーネントを統合しています。  
**使用シーン**: 通常は直接使用せず、P1_app_solo_new.pyから呼び出されます。

## サブディレクトリとファイル

### api/
API関連のコードを含むディレクトリです。

#### routes.py
**役割**: APIルートハンドラ  
**説明**: このファイルは、ウェブインターフェースのAPIエンドポイントを定義します。データの取得、グラフの生成、接続状態の取得などの機能を提供します。  
**使用シーン**: APIサーバーを起動する際に使用されます。

### data/
データ管理コードを含むディレクトリです。

#### data_manager.py
**役割**: データマネージャ  
**説明**: このファイルは、P2、P3、P4、P5、P6デバイスからのデータを管理するためのクラスを定義します。CSVファイルからのデータ読み込み、最新データの取得、データの変換などの機能を提供します。  
**使用シーン**: データを管理する際に使用されます。

### utils/
ユーティリティ関数を含むディレクトリです。

#### helper.py
**役割**: ヘルパー関数  
**説明**: このファイルは、ウェブインターフェース全体で使用されるヘルパー関数を提供します。日付の変換、ファイルの操作、文字列の処理などの機能を提供します。  
**使用シーン**: 様々な場所で使用されます。

### visualization/
データ可視化コードを含むディレクトリです。

#### graph_generator.py
**役割**: グラフジェネレータ  
**説明**: このファイルは、P2、P3、P4、P5、P6デバイスからのデータを可視化するためのグラフを生成するクラスを定義します。時系列グラフ、ダッシュボード、エクスポート機能などを提供します。  
**使用シーン**: データを可視化する際に使用されます。

### config.py
**役割**: 設定ファイル  
**説明**: このファイルは、ウェブインターフェースの設定を定義します。ポート、データディレクトリ、リフレッシュ間隔などの設定が含まれています。  
**使用シーン**: システム全体の設定を変更する際に使用されます。

## バージョン情報

### 現在のバージョン（Ver2.0）
- P2、P3、P4、P5、P6デバイスをサポート
- BME680センサーのみをサポート（CO2センサーはサポートしない）
- フル機能と簡易ウェブインターフェースの両方を含む
- データ可視化、エクスポート、接続状態監視を提供

### 旧バージョン
- **Ver1.0**: P4、P5、P6デバイスのみをサポート、CO2センサー機能を含む
- **Ver4.0**: Ver2.0への標準化前の以前のバージョン番号

## 使用シナリオ

### 1. フル機能ウェブインターフェースの起動
フル機能ウェブインターフェースを起動するには、P1_app_solo.pyを実行します：

```bash
python3 P1_app_solo.py
```

これにより、以下の機能を持つウェブインターフェースが起動します：
- P2、P3、P4、P5、P6デバイスからのデータの時系列グラフ
- ダッシュボード表示
- データエクスポート機能
- 接続状態表示

### 2. 簡易ウェブインターフェースの起動（リソース使用量削減）
リソース使用量を削減した簡易ウェブインターフェースを起動するには、P1_app_simple.pyを実行します：

```bash
python3 P1_app_simple.py
```

これにより、以下の機能を持つ簡易ウェブインターフェースが起動します：
- P2、P3、P4、P5、P6デバイスからのデータのテキストベース表示
- データエクスポート機能
- 接続状態表示

### 3. リファクタリングされたウェブインターフェースの起動
リファクタリングされたウェブインターフェースを起動するには、P1_app_solo_new.pyを実行します：

```bash
python3 P1_app_solo_new.py
```

これにより、リファクタリングされたモジュール構造を使用したウェブインターフェースが起動します。

## 注意事項
- Ver2.0では、BME680センサーのみをサポートし、CO2センサー（MH-Z19C）はサポートしていません。
- P1_app_simple.pyは、グラフ可視化機能を省略することでリソース使用量を削減しています。
- ウェブインターフェースは、デフォルトでポート80で起動します。ポートを変更するには、--portオプションを使用します。
- データディレクトリは、デフォルトで/var/lib/raspap_solo/dataです。ディレクトリを変更するには、--data-dirオプションを使用します。
- P1_app_solo.py、P1_app_simple.py、P1_app_solo_new.pyは、通常はroot権限（sudo）で実行する必要があります。
- テンプレートディレクトリには、HTMLテンプレートが含まれています。これらのテンプレートは、ウェブインターフェースのレンダリングに使用されます。
- 静的ディレクトリには、CSS、JavaScript、画像などの静的ファイルが含まれています。これらのファイルは、ウェブインターフェースのスタイルと機能に使用されます。
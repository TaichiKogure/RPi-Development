# インストールガイド

このドキュメントでは、リチウムイオン電池シミュレーション・解析ツールのインストール方法を説明します。

## 必要条件

- Python 3.6以上
- pip（Pythonパッケージマネージャー）

## インストール方法

### 方法1: 開発者向けインストール

このアプリケーションを開発目的でインストールする場合は、以下の手順に従ってください。

1. リポジトリをクローンまたはダウンロードします。

```bash
git clone https://github.com/your-username/battery-sim-analyzer.git
cd battery-sim-analyzer
```

2. 必要なパッケージをインストールします。

```bash
pip install -r requirements.txt
```

3. アプリケーションを実行します。

```bash
python main_app.py
```

### 方法2: ユーザー向けインストール

このアプリケーションを通常のユーザーとしてインストールする場合は、以下の手順に従ってください。

1. リポジトリをクローンまたはダウンロードします。

```bash
git clone https://github.com/your-username/battery-sim-analyzer.git
cd battery-sim-analyzer
```

2. パッケージをインストールします。

```bash
pip install .
```

3. アプリケーションを実行します。

```bash
battery-sim-analyzer
```

## TensorFlowのインストールに関する注意

TensorFlowは機械学習タブのニューラルネットワーク機能を使用する場合にのみ必要です。TensorFlowのインストールは、プラットフォームによって異なる場合があります。

### Windows

```bash
pip install tensorflow
```

### macOS (Intel)

```bash
pip install tensorflow
```

### macOS (Apple Silicon)

```bash
pip install tensorflow-macos
```

### Linux

```bash
pip install tensorflow
```

## トラブルシューティング

### インストール時のエラー

- **「ModuleNotFoundError: No module named 'xxx'」エラー**:
  
  必要なパッケージがインストールされていません。以下のコマンドを実行してください。
  
  ```bash
  pip install xxx
  ```

- **TensorFlowのインストールエラー**:
  
  TensorFlowのインストールに問題がある場合は、[TensorFlowの公式ドキュメント](https://www.tensorflow.org/install)を参照してください。

### 実行時のエラー

- **「ImportError: DLL load failed」エラー (Windows)**:
  
  Visual C++ Redistributableがインストールされていない可能性があります。[Microsoft Visual C++ Redistributable](https://support.microsoft.com/en-us/help/2977003/the-latest-supported-visual-c-downloads)をインストールしてください。

- **「OMP: Error #15: Initializing libiomp5.dylib」エラー (macOS)**:
  
  以下の環境変数を設定してください。
  
  ```bash
  export KMP_DUPLICATE_LIB_OK=TRUE
  ```

## 追加情報

詳細な使用方法については、[ユーザーガイド](user_guide_ja.md)を参照してください。
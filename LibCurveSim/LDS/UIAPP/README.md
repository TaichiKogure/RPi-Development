# リチウムイオン電池シミュレーション・解析ツール

## 概要

このアプリケーションは、リチウムイオン電池の充放電サイクルと経時劣化をシミュレーションし、そのデータを解析するための総合的なツールです。dQ/dV（微分容量）曲線の計算と可視化、ピーク検出、機械学習による劣化パターンの分析と予測など、多様な機能を提供します。

## 主な機能

- **シミュレーション**: リチウムイオン電池の充放電サイクルと経時劣化をシミュレーション
- **解析**: dQ/dV曲線の計算とピーク検出
- **機械学習**: 劣化パターンの分析と予測
- **データエクスポート**: 各種データの様々な形式でのエクスポート

## 必要条件

- Python 3.6以上
- 以下のPythonパッケージ：
  - numpy
  - matplotlib
  - scipy
  - pandas
  - scikit-learn
  - tensorflow（機械学習機能を使用する場合）

## インストール方法

1. 必要なパッケージをインストールします：

```bash
pip install numpy matplotlib scipy pandas scikit-learn
pip install tensorflow  # 機械学習機能を使用する場合
```

2. リポジトリをクローンまたはダウンロードします。

## 使用方法

1. コマンドラインで、アプリケーションのディレクトリに移動します：

```bash
cd path/to/LibCurveSim/LDS/UIAPP
```

2. アプリケーションを起動します：

```bash
python main_app.py
```

3. アプリケーションが起動し、メインウィンドウが表示されます。

詳細な使用方法については、[ユーザーガイド](user_guide_ja.md)を参照してください。

## プロジェクト構造

```
UIAPP/
├── main_app.py                # メインアプリケーション
├── simulation_tab.py          # シミュレーションタブ
├── analysis_tab.py            # 解析タブ
├── ml_tab.py                  # 機械学習タブ
├── data_export_tab.py         # データエクスポートタブ
├── simulation_core.py         # シミュレーション機能のコア
├── data_processor.py          # データ処理機能
├── ml_analyzer.py             # 機械学習分析機能
├── visualization.py           # 可視化機能
├── user_guide_ja.md           # 日本語ユーザーガイド
└── README.md                  # このファイル
```

## モジュールの説明

### main_app.py

メインアプリケーションを提供します。タブ付きインターフェースを作成し、各タブを統合します。

### simulation_tab.py

シミュレーションタブのUIを提供します。パラメータ設定、シミュレーション実行、結果の可視化機能を含みます。

### analysis_tab.py

解析タブのUIを提供します。dQ/dV曲線の計算、ピーク検出、結果の可視化機能を含みます。

### ml_tab.py

機械学習タブのUIを提供します。モデル選択、パラメータ設定、学習と評価、結果の可視化機能を含みます。

### data_export_tab.py

データエクスポートタブのUIを提供します。データ選択、形式選択、エクスポート機能を含みます。

### simulation_core.py

シミュレーション機能のコアを提供します。リチウムイオン電池の充放電サイクルと経時劣化のシミュレーションを行います。

### data_processor.py

データ処理機能を提供します。dQ/dV曲線の計算、ピーク検出、データの前処理を行います。

### ml_analyzer.py

機械学習分析機能を提供します。PCA、ランダムフォレスト、クラスタリング、ニューラルネットワーク、SVRなどのモデルを実装しています。

### visualization.py

可視化機能を提供します。各種グラフの作成と表示を行います。

## 開発者向け情報

### 新しいモデルの追加

新しい機械学習モデルを追加するには、以下の手順に従ってください：

1. `ml_analyzer.py`に新しいモデルのクラスを追加します。
2. `ml_tab.py`に新しいモデルのUIを追加します。
3. 必要に応じて、`visualization.py`に新しいモデルの可視化機能を追加します。

### データ形式の拡張

新しいデータ形式をサポートするには、以下の手順に従ってください：

1. `data_processor.py`に新しいデータ形式の読み込み機能を追加します。
2. 必要に応じて、`data_export_tab.py`に新しいデータ形式のエクスポート機能を追加します。

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細については、LICENSEファイルを参照してください。

## 謝辞

このプロジェクトは、リチウムイオン電池のシミュレーションと解析に関する以下の研究に基づいています：

- Severson, K. A., et al. (2019). Data-driven prediction of battery cycle life before capacity degradation. *Nature Energy*, 4(5), 383-391.
- Zhang, Y., et al. (2020). Identifying degradation patterns of lithium ion batteries from impedance spectroscopy using machine learning. *Nature Communications*, 11(1), 1-6.
- Attia, P. M., et al. (2020). Closed-loop optimization of fast-charging protocols for batteries with machine learning. *Nature*, 578(7795), 397-402.
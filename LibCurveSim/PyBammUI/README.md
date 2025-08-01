# PyBamm UI Application

PyBamm（Python Battery Mathematical Modelling）のためのユーザーフレンドリーなGUIアプリケーションです。

## 概要

このアプリケーションは、PyBammライブラリの強力なバッテリーシミュレーション機能を、直感的なグラフィカルユーザーインターフェースで利用できるようにします。研究者、エンジニア、学生が簡単にバッテリーシミュレーションを実行し、結果を可視化・エクスポートできます。

## 主な機能

### シミュレーション機能
- **パラメータ設定**: 容量、電流、温度、電圧制限の設定
- **モデル選択**: DFN、SPM、SPMeモデルから選択
- **リアルタイム可視化**: 電圧、電流、電力、容量のグラフ表示
- **バックグラウンド実行**: UIをブロックしない非同期シミュレーション

### データエクスポート機能
- **複数形式対応**: CSV、TSV、Excel形式でのエクスポート
- **データ選択**: 時間、電圧、電流、容量、電力データの選択的エクスポート
- **プレビュー機能**: エクスポート前のデータ確認
- **自動ファイル名生成**: タイムスタンプ付きファイル名

## インストール

### 必要要件
- Python 3.8以上
- PyBamm 23.5以上

### インストール手順

1. **リポジトリのクローン**
   ```bash
   git clone <repository-url>
   cd PyBammUI
   ```

2. **依存関係のインストール**
   ```bash
   pip install -r requirements.txt
   ```

3. **PyBammのインストール（オプション）**
   ```bash
   pip install pybamm
   ```
   
   注意: PyBammがインストールされていない場合、アプリケーションはモックデータを使用して動作します。

## 使用方法

### アプリケーションの起動
```bash
python main_app.py
```

### 基本的な使用手順

1. **シミュレーションタブ**
   - パラメータを設定（容量、電流、温度など）
   - モデルタイプを選択（DFN推奨）
   - 「シミュレーション実行」ボタンをクリック
   - 結果がグラフに表示されます

2. **データエクスポートタブ**
   - シミュレーション実行後、このタブに移動
   - エクスポートするデータを選択
   - ファイル形式を選択
   - 出力ディレクトリを指定
   - 「エクスポート実行」ボタンをクリック

### パラメータ説明

#### バッテリーパラメータ
- **容量 (Ah)**: バッテリーの公称容量
- **電流 (A)**: 充電/放電電流（負の値で放電、正の値で充電）
- **温度 (°C)**: 動作温度

#### 電圧制限
- **最大電圧 (V)**: 充電終止電圧
- **最小電圧 (V)**: 放電終止電圧

#### シミュレーション設定
- **シミュレーション時間 (時間)**: 計算する時間範囲
- **モデルタイプ**: 使用する電気化学モデル

### モデルの選択指針

- **DFN (Doyle-Fuller-Newman)**: 最も詳細で正確、計算時間は長い
- **SPMe (Single Particle Model with Electrolyte)**: バランスの取れた精度と速度
- **SPM (Single Particle Model)**: 高速だが簡略化されたモデル

## ファイル構成

```
PyBammUI/
├── main_app.py              # メインアプリケーション
├── simulation_tab.py        # シミュレーションタブ
├── export_tab.py           # エクスポートタブ
├── requirements.txt        # 依存関係
├── setup.py               # セットアップスクリプト
├── README.md              # このファイル
└── PyBamm分析レポート.md    # PyBamm分析ドキュメント
```

## 開発者向け情報

### アーキテクチャ
- **メインアプリケーション**: `PyBammApp`クラスがアプリケーション全体を管理
- **シミュレーター**: `PyBammSimulator`クラスがPyBammとの統合を担当
- **タブベースUI**: 機能ごとに分離されたタブ構成
- **非同期処理**: バックグラウンドでのシミュレーション実行

### 拡張方法

新しいタブを追加する場合：

1. 新しいタブクラスを作成
2. `main_app.py`の`create_tabs()`メソッドに追加
3. 必要に応じて`on_tab_changed()`メソッドを更新

### カスタムモデルの追加

PyBammのカスタムモデルを使用する場合：

1. `PyBammSimulator.run_simulation()`メソッドを拡張
2. 新しいモデルタイプを`simulation_tab.py`のコンボボックスに追加

## トラブルシューティング

### よくある問題

1. **PyBammがインストールされていない**
   - 症状: "PyBamm が見つかりません - モックデータを使用します"
   - 解決策: `pip install pybamm`でPyBammをインストール

2. **シミュレーションが遅い**
   - 症状: DFNモデルで計算時間が長い
   - 解決策: SPMeまたはSPMモデルを使用、シミュレーション時間を短縮

3. **グラフが表示されない**
   - 症状: シミュレーション後にグラフが空白
   - 解決策: パラメータ値を確認、エラーメッセージを確認

4. **エクスポートできない**
   - 症状: エクスポートボタンが無効
   - 解決策: 先にシミュレーションを実行

### ログの確認

アプリケーションはコンソールにログを出力します。問題が発生した場合は、コンソール出力を確認してください。

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

バグレポート、機能要求、プルリクエストを歓迎します。

## 関連リンク

- [PyBamm公式サイト](https://pybamm.org/)
- [PyBammドキュメント](https://pybamm.readthedocs.io/)
- [PyBamm GitHub](https://github.com/pybamm-team/PyBaMM)

## 更新履歴

### Version 1.0.0
- 初回リリース
- 基本的なシミュレーション機能
- CSV/TSV/Excelエクスポート機能
- DFN/SPM/SPMeモデル対応
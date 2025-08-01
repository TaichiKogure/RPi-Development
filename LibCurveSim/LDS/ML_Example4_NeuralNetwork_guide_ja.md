# 機械学習例4: ニューラルネットワークを用いた電池容量予測

## 概要
このプログラム（ML_Example4_NeuralNetwork.py）は、リチウムイオン電池のdQ/dV（微分容量）曲線データを入力として、ディープラーニングの一種であるニューラルネットワークを用いて電池の容量維持率を予測するモデルを構築します。これにより、電池の劣化状態を診断し、将来の容量低下を予測することが可能になります。

## ニューラルネットワークとは
ニューラルネットワークは、人間の脳の神経細胞（ニューロン）の働きを模倣した機械学習モデルです。複数の層（レイヤー）に配置されたニューロンが相互に接続され、入力データから出力を生成します。

### ニューラルネットワークの基本構造
1. **入力層**: 特徴量（この場合はdQ/dV曲線の各電圧ポイントでの値）を受け取る
2. **隠れ層**: 入力から特徴を抽出し、複雑なパターンを学習する
3. **出力層**: 予測値（この場合は容量維持率）を生成する

### 本プログラムで実装されているニューラルネットワーク
このプログラムでは、以下の特徴を持つフィードフォワード型ニューラルネットワークを実装しています：

- **アーキテクチャ**: 入力層 → 隠れ層（64ユニット） → ドロップアウト層 → 隠れ層（32ユニット） → ドロップアウト層 → 出力層（1ユニット）
- **活性化関数**: ReLU（Rectified Linear Unit）
- **ドロップアウト**: 過学習を防ぐためのランダムなニューロンの無効化（確率0.2）
- **最適化アルゴリズム**: Adam（Adaptive Moment Estimation）
- **損失関数**: 平均二乗誤差（MSE）
- **評価指標**: 平均絶対誤差（MAE）

## dQ/dV曲線からの容量予測の意義

dQ/dV曲線は電池内部の電気化学反応に関する豊富な情報を含んでおり、劣化状態を反映します。ニューラルネットワークを用いることで、以下のような利点があります：

1. **非線形関係の学習**: dQ/dV曲線と容量維持率の間の複雑な非線形関係を学習可能
2. **特徴抽出の自動化**: 手動で特徴を設計する必要がなく、重要な特徴を自動的に抽出
3. **高い予測精度**: 十分なデータがあれば、従来の手法よりも高い精度で容量予測が可能
4. **早期劣化検出**: 初期のサイクルのdQ/dV曲線から将来の劣化傾向を予測可能

## プログラムの機能

このプログラムは以下の機能を提供します：

1. **データ読み込みと前処理**:
   - 複数のサイクルのdQ/dV曲線データをCSVファイルから読み込み
   - 容量維持率データをCSVファイルから読み込み
   - 共通の電圧グリッドへの補間
   - データの標準化
   
2. **ニューラルネットワークの構築と学習**:
   - 多層ニューラルネットワークの構築
   - 訓練データとテストデータへの分割
   - 早期停止（Early Stopping）によるモデルの過学習防止
   - モデルチェックポイントによる最良モデルの保存
   
3. **モデル評価**:
   - 平均絶対誤差（MAE）
   - 二乗平均平方根誤差（RMSE）
   - 決定係数（R²）
   
4. **結果の可視化**:
   - 学習曲線（損失とMAEの推移）
   - 予測値と実際の値の比較
   - 残差プロット
   - 特徴重要度の可視化
   
5. **結果の保存**:
   - 学習済みモデルの保存
   - モデルのアーキテクチャとハイパーパラメータの保存
   - 予測結果の保存

## 使用方法

### 前提条件
- Python 3.6以上
- 必要なライブラリ: numpy, matplotlib, scipy, tensorflow, sklearn, pandas（オプション）

### インストール
```
pip install numpy matplotlib scipy tensorflow scikit-learn
pip install pandas  # オプション
```

### 実行手順
1. まず、以下のプログラムを実行してデータを生成します：
   - LibDegradationSim03_DD.py: dQ/dVデータを生成
   - LibDegradationSim03_Cret_V2.py: 容量維持率データを生成
   
2. ML_Example4_NeuralNetwork.pyを実行します：
   ```
   python ML_Example4_NeuralNetwork.py
   ```
   
3. プログラムは自動的に以下の処理を行います：
   - `results`ディレクトリ内のdQ/dVデータファイルと容量維持率ファイルを検索
   - 複数の容量維持率ファイルが見つかった場合は、使用するファイルを選択するよう促します
   - データを読み込み、前処理を行います
   - ニューラルネットワークモデルを構築し、学習します
   - モデルを評価し、結果を可視化します
   - モデルと結果を`ml_results`ディレクトリに保存します

## 出力の解釈

### 学習曲線
学習曲線は、エポック（学習の繰り返し回数）に対する損失とMAEの推移を示します。訓練データと検証データの両方の曲線が表示され、モデルの学習状況と過学習の有無を確認できます。理想的には、両方の曲線が収束し、大きな乖離がないことが望ましいです。

### 予測値と実際の値の比較
このプロットでは、横軸に実際の容量維持率、縦軸に予測された容量維持率がプロットされます。点が対角線（y=x）に近いほど、予測が正確であることを示します。また、MAE、RMSE、R²の値も表示され、モデルの性能を定量的に評価できます。

### 残差プロット
残差（実際の値 - 予測値）のプロットは、モデルの予測誤差のパターンを示します。理想的には、残差はランダムに分布し、明確なパターンを示さないはずです。パターンが見られる場合は、モデルが捉えていない関係性が存在する可能性があります。

### 特徴重要度
このプロットでは、各電圧ポイントでのdQ/dV値がモデルの予測にどれだけ寄与しているかを示します。重要度が高い電圧領域は、容量維持率の予測において特に重要な情報を含んでいると考えられます。これにより、電池劣化のメカニズムに関する洞察が得られる可能性があります。

## 学術的背景

ニューラルネットワークを用いた電池の劣化予測は、以下のような研究で報告されています：

1. Severson, K. A., Attia, P. M., Jin, N., Perkins, N., Jiang, B., Yang, Z., ... & Braatz, R. D. (2019). Data-driven prediction of battery cycle life before capacity degradation. *Nature Energy*, 4(5), 383-391.

2. Zhang, Y., Tang, Q., Zhang, Y., Wang, J., Stimming, U., & Lee, A. A. (2020). Identifying degradation patterns of lithium ion batteries from impedance spectroscopy using machine learning. *Nature Communications*, 11(1), 1-6.

3. Attia, P. M., Grover, A., Jin, N., Severson, K. A., Markov, T. M., Liao, Y. H., ... & Braatz, R. D. (2020). Closed-loop optimization of fast-charging protocols for batteries with machine learning. *Nature*, 578(7795), 397-402.

これらの研究では、機械学習手法を用いて電池の劣化パターンを分析し、寿命予測の精度向上が報告されています。特に、初期サイクルのデータから長期的な劣化傾向を予測する手法が注目されています。

## 応用例

このプログラムで構築されたニューラルネットワークモデルは、以下のような応用に利用できます：

1. **電池の健全性評価**: 現在のdQ/dV曲線から容量維持率を推定し、電池の健全性を評価
2. **残存寿命予測**: 現在の劣化状態から将来の容量低下を予測し、残存寿命を推定
3. **早期不良検出**: 通常とは異なる劣化パターンを示す電池を早期に検出
4. **製造品質管理**: 製造直後の電池のdQ/dV曲線から、将来の性能を予測し、品質管理に活用
5. **充放電プロトコルの最適化**: 異なる充放電条件下での劣化予測に基づき、寿命を延ばすための最適な使用条件を特定

## ハイパーパラメータの調整

ニューラルネットワークの性能は、ハイパーパラメータの選択に大きく依存します。本プログラムでは以下のハイパーパラメータを設定できます：

- **隠れ層のユニット数**: デフォルトは[64, 32]で、2つの隠れ層を持ち、それぞれ64ユニットと32ユニットを持ちます
- **ドロップアウト率**: デフォルトは0.2で、各ドロップアウト層で20%のニューロンがランダムに無効化されます
- **学習率**: デフォルトは0.001で、最適化アルゴリズム（Adam）の学習率を制御します
- **バッチサイズ**: デフォルトは16で、一度に処理するサンプル数を指定します
- **エポック数**: デフォルトは200で、訓練データ全体を処理する最大回数を指定します
- **早期停止の忍耐値**: デフォルトは30で、検証損失が改善しなくなってから何エポック待つかを指定します

これらのパラメータは、データセットの特性や予測タスクの複雑さに応じて調整することで、モデルの性能を向上させることができます。

## 注意事項

- ニューラルネットワークの学習には十分な量のデータが必要です。サンプル数（サイクル数）が少ない場合は、過学習のリスクが高まります。
- 学習データとテストデータの分布が大きく異なる場合、モデルの汎化性能が低下する可能性があります。
- ハイパーパラメータの選択は試行錯誤が必要な場合があります。データセットに応じて最適な値を探索することをお勧めします。
- 特徴重要度の解釈には注意が必要です。ニューラルネットワークは複雑な非線形関係を学習するため、単純な重要度だけでは捉えられない相互作用が存在する可能性があります。
- モデルの予測精度は、入力データの品質に大きく依存します。ノイズの多いデータや欠損値が多いデータでは、予測精度が低下する可能性があります。
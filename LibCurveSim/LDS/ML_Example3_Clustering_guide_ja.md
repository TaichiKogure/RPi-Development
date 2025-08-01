# 機械学習例3: クラスタリングによる電池劣化パターンの分析

## 概要
このプログラム（ML_Example3_Clustering.py）は、リチウムイオン電池のdQ/dV（微分容量）曲線データに対して複数のクラスタリングアルゴリズムを適用し、異なるサイクル間の劣化パターンを識別します。これにより、電池の劣化過程における異なる段階や劣化メカニズムを特定することができます。

## クラスタリングとは
クラスタリングは、データポイントを類似性に基づいてグループ（クラスタ）に分類する教師なし学習手法です。類似したdQ/dV曲線は同じクラスタに分類され、異なるパターンを持つ曲線は別のクラスタに分類されます。

### 本プログラムで実装されているクラスタリングアルゴリズム

#### 1. K-means クラスタリング
K-means は最も一般的なクラスタリングアルゴリズムの一つで、データポイントをK個のクラスタに分割します。

**仕組み**:
1. K個のクラスタ中心（セントロイド）をランダムに初期化
2. 各データポイントを最も近いセントロイドのクラスタに割り当て
3. 各クラスタのセントロイドを、そのクラスタに属するデータポイントの平均として再計算
4. クラスタの割り当てが変化しなくなるまで2と3を繰り返す

**特徴**:
- 球形のクラスタを見つけるのに適している
- クラスタ数Kを事前に指定する必要がある
- 初期セントロイドの選択に依存する

#### 2. DBSCAN クラスタリング
DBSCAN（Density-Based Spatial Clustering of Applications with Noise）は、密度ベースのクラスタリングアルゴリズムで、任意の形状のクラスタを検出できます。

**仕組み**:
1. 各データポイントの近傍（半径εの範囲内）にある点の数を計算
2. 近傍に十分な数（min_samples以上）の点がある場合、そのポイントをコアポイントとする
3. コアポイントから到達可能なすべてのポイントを同じクラスタに割り当て
4. どのクラスタにも属さないポイントをノイズとして扱う

**特徴**:
- クラスタ数を事前に指定する必要がない
- 任意の形状のクラスタを検出できる
- ノイズポイントを識別できる
- 密度の異なるクラスタの検出が難しい

#### 3. 階層的クラスタリング
階層的クラスタリングは、データポイント間の距離に基づいて階層的なクラスタ構造を構築します。

**仕組み**:
1. 各データポイントを個別のクラスタとして開始
2. 最も近い2つのクラスタを統合
3. 目的のクラスタ数になるまで2を繰り返す

**特徴**:
- クラスタの階層構造を提供
- 様々な距離計算方法（リンケージ）を選択可能
- 計算コストが高い（特に大規模データセット）

## クラスタリングの評価指標

### シルエットスコア
シルエットスコアは、クラスタリングの品質を評価する指標で、-1から1の範囲の値をとります。

- **1に近い値**: データポイントが適切なクラスタに割り当てられている
- **0に近い値**: データポイントが複数のクラスタの境界付近にある
- **-1に近い値**: データポイントが誤ったクラスタに割り当てられている可能性がある

### エルボー法
エルボー法は、K-meansクラスタリングの最適なクラスタ数Kを決定するための方法です。クラスタ数Kを変化させながらイナーシャ（クラスタ内の二乗距離の合計）をプロットし、イナーシャの減少率が急激に変化する「エルボー（肘）」ポイントを最適なKとします。

## dQ/dV曲線へのクラスタリング適用の意義

dQ/dV曲線のクラスタリングにより、以下のような知見が得られます：

1. **劣化段階の特定**: 異なるサイクル段階で異なるクラスタが形成される場合、それは劣化過程における異なる段階を示している可能性があります
2. **劣化メカニズムの分類**: 異なるクラスタは異なる劣化メカニズム（SEI形成、リチウム喪失、活物質の劣化など）に対応している可能性があります
3. **異常検出**: 大多数のサイクルとは異なるクラスタに分類されるサイクルは、異常な劣化パターンを示している可能性があります
4. **寿命予測**: クラスタの遷移パターンを分析することで、将来の劣化傾向を予測できる可能性があります

## プログラムの機能

このプログラムは以下の機能を提供します：

1. **データ読み込みと前処理**:
   - 複数のサイクルのdQ/dVデータをCSVファイルから読み込み
   - 共通の電圧グリッドへの補間
   - サイクル番号に基づくデータの並べ替え
   
2. **最適クラスタ数の決定**:
   - エルボー法によるイナーシャの計算
   - シルエットスコアの計算
   - 最適クラスタ数の自動決定
   
3. **複数のクラスタリングアルゴリズムの適用**:
   - K-meansクラスタリング
   - DBSCANクラスタリング（複数のεパラメータを試行）
   - 階層的クラスタリング
   
4. **結果の可視化**:
   - クラスタごとに色分けされたdQ/dV曲線
   - サイクル番号に対するクラスタ割り当て
   - PCAを用いた2次元空間でのクラスタ可視化
   - K-meansのクラスタセントロイド
   
5. **結果の保存**:
   - 各サイクルのクラスタ割り当てをCSVファイルに保存

## 使用方法

### 前提条件
- Python 3.6以上
- 必要なライブラリ: numpy, matplotlib, scipy, sklearn, pandas（オプション）

### インストール
```
pip install numpy matplotlib scipy scikit-learn
pip install pandas  # オプション
```

### 実行手順
1. まず、LibDegradationSim03_DD.pyを実行してdQ/dVデータを生成します
2. ML_Example3_Clustering.pyを実行します：
   ```
   python ML_Example3_Clustering.py
   ```
3. プログラムは自動的に以下の処理を行います：
   - `results`ディレクトリ内のdQ/dVデータファイルを検索
   - データを読み込み、前処理を行います
   - 最適なクラスタ数を決定します
   - 3種類のクラスタリングアルゴリズムを適用します
   - 結果を可視化し、CSVファイルに保存します
4. 結果は`ml_results`ディレクトリに保存されます

## 出力の解釈

### 最適クラスタ数の決定
エルボー法とシルエットスコアのプロットは、最適なクラスタ数を決定するための情報を提供します。エルボー法では「肘」の位置、シルエットスコアでは最大値を示すポイントが最適なクラスタ数の候補となります。

### クラスタごとに色分けされたdQ/dV曲線
このプロットでは、同じクラスタに属するdQ/dV曲線が同じ色で表示されます。これにより、異なるクラスタ間のdQ/dV曲線の形状の違いを視覚的に確認できます。

### サイクル番号に対するクラスタ割り当て
このプロットでは、横軸にサイクル番号、縦軸にクラスタ番号がプロットされます。これにより、サイクルの進行に伴うクラスタの変化パターンを確認できます。連続したサイクルが同じクラスタに属している場合、その期間は類似した劣化パターンを示していると考えられます。

### PCAを用いた2次元空間でのクラスタ可視化
このプロットでは、高次元のdQ/dVデータを2次元に圧縮し、クラスタごとに色分けして表示します。クラスタが2次元空間で明確に分離している場合、クラスタリングが効果的に機能していることを示します。

### K-meansのクラスタセントロイド
このプロットでは、K-meansクラスタリングで得られた各クラスタの中心（セントロイド）のdQ/dV曲線が表示されます。これらは各クラスタの「代表的な」dQ/dV曲線と見なすことができ、異なるクラスタ間の特徴の違いを理解するのに役立ちます。

## 学術的背景

リチウムイオン電池の劣化パターン分析におけるクラスタリングの応用は、以下のような研究で報告されています：

1. Severson, K. A., Attia, P. M., Jin, N., Perkins, N., Jiang, B., Yang, Z., ... & Braatz, R. D. (2019). Data-driven prediction of battery cycle life before capacity degradation. *Nature Energy*, 4(5), 383-391.

2. Dubarry, M., Truchot, C., & Liaw, B. Y. (2012). Synthesize battery degradation modes via a diagnostic and classification tool. *Journal of Power Sources*, 219, 204-216.

3. Birkl, C. R., Roberts, M. R., McTurk, E., Bruce, P. G., & Howey, D. A. (2017). Degradation diagnostics for lithium ion cells. *Journal of Power Sources*, 341, 373-386.

これらの研究では、クラスタリング手法を用いて電池の劣化パターンを分類し、異なる劣化メカニズムの特定や寿命予測の精度向上が報告されています。

## 応用例

このプログラムで特定された劣化パターンのクラスタは、以下のような応用に利用できます：

1. **劣化メカニズムの特定**: 異なるクラスタの特徴を分析することで、支配的な劣化メカニズムを特定
2. **異常検出**: 大多数のサイクルとは異なるクラスタに分類されるサイクルを検出し、異常な劣化を早期に発見
3. **寿命予測モデルの改良**: クラスタ情報を特徴量として使用することで、より精度の高い寿命予測モデルを構築
4. **使用条件の最適化**: 特定のクラスタパターンと使用条件（温度、充放電レートなど）の関係を分析し、電池寿命を延ばすための最適な使用条件を特定

## 注意事項

- クラスタリング結果は、データの前処理（特に補間やスケーリング）に大きく依存します。異なる前処理方法を試すことで、結果が変わる可能性があります。
- K-meansクラスタリングは初期セントロイドの選択に依存するため、実行するたびに結果が若干異なる可能性があります。
- DBSCANクラスタリングはεとmin_samplesパラメータの選択に敏感です。最適なパラメータはデータセットによって異なります。
- クラスタリング結果の解釈には、電気化学的知識と組み合わせることが重要です。クラスタの違いが実際の劣化メカニズムの違いを反映しているかを検証する必要があります。
- サンプル数（サイクル数）が少ない場合、クラスタリング結果の信頼性が低下する可能性があります。
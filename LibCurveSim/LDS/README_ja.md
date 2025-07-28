# リチウムイオン電池シミュレーションツール - 機能拡張版

## 概要
このプロジェクトでは、リチウムイオン電池の充放電サイクルと経時劣化をシミュレーションするためのツールを拡張しました。元のプログラム（LibDegradationSim03.py）をベースに、以下の機能を追加しました：

1. パラメータ範囲の任意指定
2. 劣化率データのCSV出力
3. テストモードと容量維持率モードの統合
4. dQ/dV曲線の計算と可視化
5. dQ/dV曲線のピーク検出と解析

これらの機能により、リチウムイオン電池の特性と劣化挙動をより詳細に分析できるようになりました。

## プログラム一覧

### 基本プログラム
- **LibDegradationSim03.py**
  - 基本的なリチウムイオン電池の充放電サイクルと劣化シミュレーション
  - 容量低下と内部抵抗の増加を考慮したモデル
  - 充電曲線（CC-CV）と放電曲線の生成

### 拡張プログラム
1. **LibDegradationSim03_test_V2.py**
   - パラメータの影響を視覚的に理解するためのテストツール
   - パラメータの範囲を任意で指定可能
   - 容量劣化、抵抗増加、充放電曲線のパラメータテスト

2. **LibDegradationSim03_Cret_V2.py**
   - サイクル数に対する容量維持率を可視化
   - 劣化率データ（容量劣化率、抵抗増加率、維持率劣化率）のCSV出力
   - 充放電曲線と容量維持率を同時に表示

3. **LibDegradationSim03_TestCret.py**
   - テストモードと容量維持率モードを統合
   - すべてのパラメータの範囲を任意で指定可能
   - 劣化曲線および容量維持率を算出

4. **LibDegradationSim03_DD.py**
   - 充放電曲線からdQ/dV曲線を計算
   - dQ/dV曲線の可視化
   - dQ/dVデータのCSV出力

5. **LibDegradationSim03_DDA.py**
   - dQ/dV曲線のピーク検出
   - 検出感度や検出領域を任意で指定可能
   - ピークデータ（電圧、dQ/dV値、顕著さ、幅）のCSV出力

## 使用方法

### LibDegradationSim03_test_V2.py
パラメータの範囲を任意で指定してテストを実行します。

```
python LibDegradationSim03_test_V2.py
```

1. テストモードを選択（容量劣化、抵抗増加、充放電曲線）
2. パラメータの範囲をカスタマイズするかどうかを選択
3. 範囲の最小値、最大値、分割数を指定
4. テスト結果のグラフを確認
5. 必要に応じてCSVファイルに保存

### LibDegradationSim03_Cret_V2.py
容量維持率と劣化率データを計算して可視化します。

```
python LibDegradationSim03_Cret_V2.py
```

1. 電池の基本パラメータを入力
2. 劣化モデルのパラメータを入力
3. シミュレーションのパラメータを入力
4. 結果のグラフを確認（充電曲線、放電曲線、容量、維持率、劣化率）
5. 必要に応じてCSVファイルに保存

### LibDegradationSim03_TestCret.py
テストモードと容量維持率モードを統合したプログラムです。

```
python LibDegradationSim03_TestCret.py
```

1. モードを選択（パラメータテスト or サイクルシミュレーション）
2. 各モードに応じたパラメータを入力
3. 結果のグラフを確認
4. 必要に応じてCSVファイルに保存

### LibDegradationSim03_DD.py
充放電曲線からdQ/dV曲線を計算して可視化します。

```
python LibDegradationSim03_DD.py
```

1. 解析するCSVファイルを選択
2. スムージング係数を指定
3. 容量-電圧曲線も表示するかどうかを選択
4. dQ/dV曲線のグラフを確認
5. 必要に応じてdQ/dVデータをCSVファイルに保存

### LibDegradationSim03_DDA.py
dQ/dV曲線のピークを検出して可視化します。

```
python LibDegradationSim03_DDA.py
```

1. 解析するdQ/dVファイルを選択
2. ピーク検出パラメータを指定
   - ピークの顕著さ（prominence）
   - ピークの幅（width）
   - ピークの高さ（height）
   - ピーク間の最小距離（distance）
   - 電圧範囲
3. ピーク検出結果のグラフを確認
4. 必要に応じてピークデータをCSVファイルに保存

## データフロー
1. **LibDegradationSim03_test_V2.py** または **LibDegradationSim03_Cret_V2.py** または **LibDegradationSim03_TestCret.py** を実行して充放電曲線データを生成
2. **LibDegradationSim03_DD.py** を実行して充放電曲線からdQ/dV曲線を計算
3. **LibDegradationSim03_DDA.py** を実行してdQ/dV曲線のピークを検出

## 注意事項
- **pandas** モジュールがインストールされていると、より高度なデータ処理が可能になります。インストールされていない場合は基本的なCSV処理が使用されます。
- dQ/dV曲線の計算とピーク検出には、十分なデータポイントが必要です。シミュレーションの時間ステップ（dt）を小さくすると、より詳細なデータが得られます。
- ピーク検出のパラメータは、データの特性に応じて調整する必要があります。特に「prominence」（顕著さ）は重要なパラメータです。

## 依存ライブラリ
- numpy
- matplotlib
- scipy
- pandas (オプション)

## インストール方法
```
pip install numpy matplotlib scipy
pip install pandas  # オプション
```
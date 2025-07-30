# 高度な変数タブ - 変数ブラウザ使用方法とトラブルシューティングガイド

## 概要

PyBamm UIアプリケーションの「高度な変数」タブは、バッテリーシミュレーションにおいて**カスタム変数**を設定し、その影響を解析するための機能です。本ドキュメントでは、変数ブラウザの使用方法、基本設定値との違い、および「int object is not iterable」エラーの対策について詳しく説明します。

## 変数ブラウザの基本概念

### 1. 基本設定値 vs カスタム変数

#### 基本設定値（デフォルト設定）
- **定義**: PyBammモデルに予め組み込まれているパラメータ値
- **特徴**: 
  - Chen2020パラメータセットなどの標準的な値
  - 一般的なリチウムイオン電池の特性を反映
  - シミュレーション実行時に自動的に適用される
- **使用場面**: 標準的なバッテリー特性を解析したい場合

#### カスタム変数
- **定義**: ユーザーが変数ブラウザから選択し、独自の値を設定した変数
- **特徴**:
  - 基本設定値を上書きする
  - 特定の条件や実験データに基づいた値を設定可能
  - シミュレーション結果に直接影響する
- **使用場面**: 特定の電池仕様や実験条件を再現したい場合

### 2. 変数の種類と特性

#### 時系列変数（配列データ）
- **例**: Terminal voltage [V], Discharge capacity [A.h]
- **特性**: 時間とともに変化する値の配列
- **データ形式**: numpy配列 `[値1, 値2, 値3, ...]`
- **プロット**: 時系列グラフとして表示

#### 定数変数（スカラーデータ）
- **例**: Current [A]（一定電流放電時）
- **特性**: シミュレーション中一定の値
- **データ形式**: 単一の数値 `5.0`
- **プロット**: 水平線として表示

## 変数ブラウザの使用方法

### Step 1: モデル選択と変数読み込み

```
1. 「モデル選択」セクションでモデルタイプを選択
   - DFN (Doyle-Fuller-Newman): 最も詳細なモデル
   - SPM (Single Particle Model): 簡略化モデル
   - SPMe (Single Particle Model with Electrolyte): 中間的なモデル

2. 「変数を読み込み」ボタンをクリック
   - 選択したモデルで利用可能な変数がリストに表示される
   - 変数数が「変数: XX個」として表示される
```

### Step 2: 変数の検索と選択

```
1. 検索ボックスを使用して変数を絞り込み
   - 例: "current" と入力すると電流関連の変数のみ表示
   - 大文字小文字は区別されない

2. 変数リストから目的の変数をクリック
   - 選択された変数が「選択された変数」欄に表示される
   - 例: "Current [A]"
```

### Step 3: カスタム変数の追加

```
1. 「値」欄に数値を入力
   - 例: 電流値として "5" を入力（5A放電を意味）
   - 小数点も使用可能: "2.5"

2. 「追加」ボタンをクリック
   - カスタム変数が「設定済み変数」リストに追加される
   - 表示形式: "Current [A]: 5.0"

3. 必要に応じて複数の変数を設定
   - 異なる変数に対して上記手順を繰り返す
```

### Step 4: シミュレーション実行

```
1. 「時間 (時)」を設定（デフォルト: 1.0時間）

2. 「プロット変数」を選択
   - シミュレーション結果として表示したい変数を選択
   - 通常は "Terminal voltage [V]" または "Current [A]"

3. 「シミュレーション実行」ボタンをクリック
   - バックグラウンドでシミュレーションが実行される
   - 完了後、結果がグラフに表示される
```

## データ型と処理の詳細

### 1. 配列データの処理

```python
# 例: 電圧データ（時系列）
voltage_data = [4.2, 4.1, 4.0, 3.9, 3.8, ...]  # 100個の値
time_data = [0, 36, 72, 108, 144, ...]          # 対応する時間

# プロット処理
plt.plot(time_data, voltage_data)  # 正常に描画される
```

### 2. スカラーデータの処理

```python
# 例: 電流データ（定数）
current_value = 5.0  # 単一の値

# 問題のあるプロット処理（修正前）
plt.plot(time_data, current_value)  # エラー: "int object is not iterable"

# 修正されたプロット処理（修正後）
current_array = np.full_like(time_data, current_value)  # [5.0, 5.0, 5.0, ...]
plt.plot(time_data, current_array)  # 正常に描画される
```

## エラーの種類と対策

### 1. "int object is not iterable" エラー

#### 発生原因
- カスタム変数として設定した値がスカラー（単一数値）
- プロット処理で配列データを期待しているが、スカラー値が渡される

#### 対策（修正済み）
```python
# 修正されたプロット処理
if hasattr(var_data, '__iter__') and not isinstance(var_data, str):
    # 配列データの場合
    if len(var_data) == len(time_data):
        ax.plot(time_data, var_data, 'b-', linewidth=2, label=plot_var)
    elif len(var_data) == 1:
        # 単一要素配列を定数として展開
        constant_value = var_data[0]
        var_data_expanded = np.full_like(time_data, constant_value)
        ax.plot(time_data, var_data_expanded, 'b-', linewidth=2, 
               label=f"{plot_var} (定数値: {constant_value})")
else:
    # スカラー値の場合
    scalar_value = float(var_data)
    var_data_expanded = np.full_like(time_data, scalar_value)
    ax.plot(time_data, var_data_expanded, 'b-', linewidth=2, 
           label=f"{plot_var} (定数値: {scalar_value})")
```

### 2. その他の一般的なエラー

#### 変数が見つからないエラー
```
エラーメッセージ: "変数 'XXX' がシミュレーション結果に含まれていません"

原因:
- 選択したプロット変数がシミュレーション結果に含まれていない
- モデルタイプによって利用可能な変数が異なる

対策:
1. 利用可能な変数を確認する
2. 適切なプロット変数を選択する
3. モデルタイプを変更してみる
```

#### 数値変換エラー
```
エラーメッセージ: "数値を入力してください"

原因:
- 「値」欄に数値以外の文字が入力されている

対策:
1. 数値のみを入力する（例: 5, 2.5, -1.0）
2. 単位は含めない（"5A" ではなく "5"）
```

## デバッグ機能の使用方法

### デバッグ版の起動

```python
# デバッグ版を使用する場合
from advanced_variables_tab_debug import AdvancedVariablesTabDebug

# 通常版の代わりにデバッグ版を使用
debug_tab = AdvancedVariablesTabDebug(parent, app)
```

### デバッグ情報の確認

デバッグ版では以下の詳細情報が出力されます：

```
=== SIMULATION EXECUTION DEBUG ===
Model: DFN, Time: 1.0h
PyBamm available: False
Using mock simulation...
Mock simulation: 100 time points
Data inspection for 'time_data': {'variable_name': 'time_data', 'type': 'ndarray', 'shape': (100,), 'length': 100}
Processing custom variable: Current [A] = 5.0
Data inspection for 'custom_Current [A]': {'variable_name': 'custom_Current [A]', 'type': 'float', 'length': 'N/A'}
Converting scalar current 5.0 to array
Data inspection for 'current_data_custom': {'variable_name': 'current_data_custom', 'type': 'ndarray', 'shape': (100,), 'length': 100}
```

## 実用的な使用例

### 例1: 一定電流放電の解析

```
目的: 5A一定電流での放電特性を解析

手順:
1. モデル: DFN を選択
2. 変数ブラウザで "Current [A]" を選択
3. 値: "5" を入力して追加
4. プロット変数: "Terminal voltage [V]" を選択
5. シミュレーション実行

結果:
- 5A一定電流での電圧変化が表示される
- 電流は水平線（定数値: 5.0）として表示される
```

### 例2: 複数パラメータの同時変更

```
目的: 電流と温度を同時に変更して影響を確認

手順:
1. "Current [A]": "3" を追加
2. "Cell temperature [K]": "298" を追加（25°C）
3. プロット変数を適宜選択
4. シミュレーション実行

結果:
- 設定した条件でのシミュレーション結果が表示される
- 複数のカスタム変数の影響が反映される
```

## トラブルシューティング手順

### Step 1: エラーメッセージの確認

```
1. エラーダイアログの内容を詳しく読む
2. エラーの種類を特定する：
   - データ型エラー（"not iterable"）
   - 変数不存在エラー
   - 数値変換エラー
   - シミュレーション実行エラー
```

### Step 2: デバッグ版の使用

```
1. デバッグ版を起動する
2. 同じ操作を実行する
3. コンソール出力を確認する
4. データ型や値の詳細情報を分析する
```

### Step 3: 段階的な問題の切り分け

```
1. 最小限の設定でテスト
   - カスタム変数を1つだけ設定
   - 簡単な値（例: 1, 2, 5）を使用

2. モデルタイプを変更してテスト
   - DFN → SPM → SPMe の順で試す

3. 異なる変数でテスト
   - Current [A] 以外の変数も試す
```

### Step 4: 問題の報告

問題が解決しない場合、以下の情報を含めて報告してください：

```
1. エラーメッセージの全文
2. 使用したカスタム変数と値
3. 選択したモデルタイプ
4. デバッグ版の出力（可能な場合）
5. 再現手順
```

## まとめ

高度な変数タブの変数ブラウザは、PyBammシミュレーションにおいて柔軟なパラメータ設定を可能にする強力な機能です。基本設定値とカスタム変数の違いを理解し、適切な使用方法を身につけることで、より詳細で実用的なバッテリー解析が可能になります。

「int object is not iterable」エラーは修正済みですが、デバッグ版を使用することで、より詳細な問題分析と解決が可能です。本ドキュメントを参考に、効果的なシミュレーション解析を実施してください。
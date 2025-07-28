# リチウムイオン電池シミュレーション・解析ツール 拡張マニュアル

## 目次

1. [はじめに](#はじめに)
2. [現在のアプリケーション構造](#現在のアプリケーション構造)
3. [拡張の可能性](#拡張の可能性)
4. [拡張時の注意点](#拡張時の注意点)
5. [拡張例](#拡張例)

## はじめに

このマニュアルは、リチウムイオン電池シミュレーション・解析ツールを拡張または修正したい開発者向けに作成されました。アプリケーションの構造、拡張の可能性、および拡張時の注意点について説明します。

## 現在のアプリケーション構造

アプリケーションは、モジュール化された設計に基づいており、以下の主要なコンポーネントで構成されています：

### コアモジュール

| ファイル名 | 説明 | 主な機能 |
|------------|------|----------|
| simulation_core.py | シミュレーション機能のコア | 電池モデル、充放電シミュレーション、劣化モデル |
| data_processor.py | データ処理機能 | dQ/dV計算、ピーク検出、データ前処理 |
| ml_analyzer.py | 機械学習分析機能 | PCA、ランダムフォレスト、クラスタリング、ニューラルネットワーク、SVR |
| visualization.py | 可視化機能 | グラフ生成、プロット設定、結果表示 |

### UIモジュール

| ファイル名 | 説明 | 主な機能 |
|------------|------|----------|
| main_app.py | メインアプリケーション | タブ管理、データ共有、イベント処理 |
| simulation_tab.py | シミュレーションタブUI | パラメータ設定、シミュレーション実行、結果表示 |
| analysis_tab.py | 解析タブUI | データ読み込み、dQ/dV計算、ピーク検出 |
| ml_tab.py | 機械学習タブUI | モデル選択、パラメータ設定、学習実行 |
| data_export_tab.py | データエクスポートタブUI | データ選択、形式選択、エクスポート実行 |

### 補助ファイル

| ファイル名 | 説明 |
|------------|------|
| setup.py | インストールスクリプト |
| test_core_functionality.py | コア機能のテスト |
| check_files.py | ファイル構成チェック |

### データフロー

1. ユーザーがシミュレーションパラメータを設定
2. simulation_core.pyがシミュレーションを実行し、結果を生成
3. 結果はmain_app.pyを通じて他のタブと共有
4. analysis_tab.pyがdata_processor.pyを使用してdQ/dV曲線を計算
5. ml_tab.pyがml_analyzer.pyを使用して機械学習分析を実行
6. visualization.pyがすべてのタブで結果を可視化
7. data_export_tab.pyが結果をエクスポート

## 拡張の可能性

アプリケーションは、以下の領域で拡張可能です：

### 1. 新しい電池モデルの追加

simulation_core.pyを拡張して、異なるタイプの電池（例：LFP、NMC、NCA）や異なる劣化メカニズムをサポートできます。

```python
# simulation_core.pyに新しい電池モデルを追加する例
def ocv_from_soc_lfp(self, soc):
    """LFP電池のSOCからOCVを計算する関数"""
    # LFP電池のOCV-SOCテーブル
    ocv_table_lfp = [3.2, 3.3, 3.3, 3.3, 3.3, 3.3, 3.3, 3.3, 3.3, 3.4, 3.5]
    soc_points = np.linspace(0, 1, len(ocv_table_lfp))
    
    # 補間関数を作成
    interp_func = interp1d(soc_points, ocv_table_lfp, kind='cubic', bounds_error=False, fill_value="extrapolate")
    
    return interp_func(soc)
```

### 2. 新しい機械学習モデルの追加

ml_analyzer.pyを拡張して、新しい機械学習モデル（例：XGBoost、LSTM）を追加できます。

```python
# ml_analyzer.pyに新しい機械学習モデルを追加する例
def run_xgboost(self, X, y, n_estimators=100, learning_rate=0.1, max_depth=3, test_size=0.2, random_state=None):
    """XGBoostモデルを実行する関数"""
    from xgboost import XGBRegressor
    
    # データを訓練セットとテストセットに分割
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)
    
    # モデルを作成
    model = XGBRegressor(n_estimators=n_estimators, learning_rate=learning_rate, max_depth=max_depth)
    
    # モデルを訓練
    model.fit(X_train, y_train)
    
    # 予測
    y_pred = model.predict(X_test)
    
    # 評価指標を計算
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    # 結果を返す
    return {
        'model': model,
        'X_train': X_train,
        'X_test': X_test,
        'y_train': y_train,
        'y_test': y_test,
        'y_pred': y_pred,
        'mse': mse,
        'mae': mae,
        'r2': r2,
        'feature_importance': model.feature_importances_
    }
```

### 3. 新しいデータ形式のサポート

data_processor.pyを拡張して、新しいデータ形式（例：HDF5、SQLite）をサポートできます。

```python
# data_processor.pyに新しいデータ形式のサポートを追加する例
def load_hdf5_data(self, file_path):
    """HDF5ファイルからデータを読み込む関数"""
    import h5py
    
    with h5py.File(file_path, 'r') as f:
        cycles = list(f.keys())
        data = {}
        
        for cycle in cycles:
            cycle_data = f[cycle]
            data[cycle] = {
                'voltage': np.array(cycle_data['voltage']),
                'capacity': np.array(cycle_data['capacity']),
                'current': np.array(cycle_data['current']),
                'time': np.array(cycle_data['time'])
            }
    
    return data
```

### 4. 新しい可視化機能の追加

visualization.pyを拡張して、新しい可視化機能（例：3Dプロット、インタラクティブグラフ）を追加できます。

```python
# visualization.pyに新しい可視化機能を追加する例
def plot_3d_capacity_voltage_cycle(self, results, figure=None, ax=None):
    """容量、電圧、サイクルの3Dプロットを作成する関数"""
    from mpl_toolkits.mplot3d import Axes3D
    
    if figure is None:
        figure = self.create_figure()
    
    if ax is None:
        ax = figure.add_subplot(111, projection='3d')
    
    cycles = []
    voltages = []
    capacities = []
    
    for cycle, data in results['discharge'].items():
        for v, c in zip(data['voltage'], data['capacity']):
            cycles.append(int(cycle))
            voltages.append(v)
            capacities.append(c)
    
    scatter = ax.scatter(voltages, capacities, cycles, c=cycles, cmap='viridis')
    
    ax.set_xlabel('電圧 (V)')
    ax.set_ylabel('容量 (Ah)')
    ax.set_zlabel('サイクル')
    ax.set_title('容量-電圧-サイクルの3D関係')
    
    figure.colorbar(scatter, ax=ax, label='サイクル')
    
    return figure, ax
```

### 5. 新しいタブの追加

新しいタブ（例：比較タブ、レポートタブ）を追加して、機能を拡張できます。

```python
# comparison_tab.pyという新しいタブを追加する例
class ComparisonTab:
    """比較タブのクラス"""
    
    def __init__(self, parent, app):
        """比較タブを初期化する"""
        self.frame = ttk.Frame(parent)
        self.app = app
        
        # データストレージ
        self.datasets = {}
        
        # フレームを設定
        self.setup_frames()
        
        # コントロールを設定
        self.setup_controls()
        
        # プロットエリアを設定
        self.setup_plot_area()
    
    # 以下、必要なメソッドを実装
```

## 拡張時の注意点

アプリケーションを拡張する際は、以下の点に注意してください：

### 1. モジュール間の依存関係

- コアモジュールは他のコアモジュールに依存しないようにする
- UIモジュールはコアモジュールに依存するが、他のUIモジュールには直接依存しない
- データの共有はmain_app.pyを通じて行う

### 2. インターフェースの一貫性

- 新しい機能を追加する際は、既存の関数やクラスのインターフェースと一貫性を保つ
- パラメータの命名規則や戻り値の形式を統一する
- ドキュメントを更新して、新しい機能の使用方法を説明する

### 3. エラーハンドリング

- すべての新しい機能に適切なエラーハンドリングを実装する
- ユーザーフレンドリーなエラーメッセージを提供する
- 例外をキャッチして適切に処理する

```python
# エラーハンドリングの例
def load_data(self, file_path):
    """データを読み込む関数"""
    try:
        # データを読み込む処理
        return data
    except FileNotFoundError:
        self.app.show_error("ファイルエラー", f"ファイル '{file_path}' が見つかりません。")
        return None
    except Exception as e:
        self.app.show_error("読み込みエラー", f"データの読み込み中にエラーが発生しました: {str(e)}")
        return None
```

### 4. パフォーマンスの考慮

- 大量のデータを処理する場合は、メモリ使用量に注意する
- 計算集約的な処理は別スレッドで実行する
- キャッシュ機構を使用して、計算結果を再利用する

```python
# スレッドを使用したパフォーマンス最適化の例
def run_simulation(self):
    """シミュレーションを実行する関数"""
    # パラメータを取得
    num_cycles = int(self.cycle_var.get())
    
    # プログレスバーを初期化
    self.progress_var.set(0)
    
    # 別スレッドでシミュレーションを実行
    self.simulation_thread = threading.Thread(
        target=self._run_simulation_thread,
        args=(num_cycles,)
    )
    self.simulation_thread.daemon = True
    self.simulation_thread.start()
```

### 5. テスト

- 新しい機能にはユニットテストを追加する
- 既存のテストが新しい機能と互換性があることを確認する
- エッジケースをテストする

```python
# テストの例
def test_new_battery_model(self):
    """新しい電池モデルをテストする関数"""
    sim = SimulationCore()
    sim.set_battery_params(2.5, 1.0, 0.1)
    
    # 通常のOCV-SOC関数をテスト
    ocv1 = sim.ocv_from_soc(0.5)
    
    # 新しいLFP電池のOCV-SOC関数をテスト
    ocv2 = sim.ocv_from_soc_lfp(0.5)
    
    # 結果を検証
    self.assertIsNotNone(ocv1)
    self.assertIsNotNone(ocv2)
    self.assertNotEqual(ocv1, ocv2)
```

## 拡張例

以下に、アプリケーションを拡張するいくつかの具体的な例を示します：

### 例1: 温度依存性モデルの追加

電池の性能は温度に大きく依存します。温度依存性を考慮したモデルを追加することで、より現実的なシミュレーションが可能になります。

1. simulation_core.pyに温度パラメータと温度依存性関数を追加
2. simulation_tab.pyに温度設定のUIを追加
3. visualization.pyに温度依存性を可視化する機能を追加

### 例2: バッチ処理機能の追加

複数のシミュレーションを一括で実行する機能を追加することで、パラメータスイープや感度分析が容易になります。

1. 新しいbatch_processor.pyモジュールを作成
2. main_app.pyにバッチ処理のメニュー項目を追加
3. 結果を比較するための新しい可視化機能を追加

### 例3: データベース統合

シミュレーション結果をデータベースに保存する機能を追加することで、大量のデータを効率的に管理できます。

1. 新しいdatabase_manager.pyモジュールを作成
2. data_export_tab.pyにデータベースエクスポート機能を追加
3. データベースからデータを読み込む機能を追加

### 例4: Webインターフェースの追加

Webインターフェースを追加することで、ブラウザからアプリケーションにアクセスできるようになります。

1. Flaskなどを使用してWebサーバーを実装
2. RESTful APIを作成してコア機能にアクセス
3. ブラウザベースのUIを実装

これらの拡張例は、アプリケーションの基本構造を維持しながら、新しい機能を追加する方法を示しています。モジュール化された設計により、特定の部分を変更せずに他の部分を拡張できます。
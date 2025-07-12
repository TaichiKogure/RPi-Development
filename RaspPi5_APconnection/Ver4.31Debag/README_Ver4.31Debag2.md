# Ver4.31 デバッグ2 - グラフ描画とデータロギングの改善

## 修正内容

### 問題点
1. グラフのスケールやプロットが毎回「0スタート」になる問題
   - Y軸の範囲指定を動的に設定していても、`fig.add_trace(...)`が実際に値を受け取れていない可能性がありました。

2. データの範囲が明確に表示されない
   - データの範囲（最小値、最大値）がログに出力されていないため、問題の診断が困難でした。

3. 過去のデータがキャッシュされて最新のデータが表示されない
   - `get_historical_data()`メソッドでキャッシュが使用されていたため、最新のデータが表示されない場合がありました。

### 修正点

1. `get_historical_data()`メソッドの改善
   - キャッシュを無効化し、常にファイルから最新のデータを読み込むように修正
   - ファイル読み込み時のログを追加して、どのファイルが読み込まれているかを明確に表示

2. データ範囲のログ出力
   - P2とP3のデータ範囲（タイムスタンプの最小値と最大値、パラメータの最小値と最大値）をログに出力
   - これにより、グラフが正しく描画されない原因を特定しやすくなりました

## 技術的な詳細

### 1. キャッシュの無効化

```python
def get_historical_data(self, device_id, days=1):
    # ...
    force_reload = True  # 常にファイルを再読み込み
    
    # キャッシュが有効で、まだ有効期限内の場合のみキャッシュを使用
    if not force_reload and self.data_cache[device_id] is not None:
        # ...
```

### 2. ファイル読み込みのログ追加

```python
file_path = os.path.join(full_dir, f"{device_id}_{date_str}.csv")
if os.path.exists(file_path):
    logger.info(f"Reading historical data for {device_id} from file: {file_path}")
    try:
        df = pd.read_csv(file_path)
        # ...
```

### 3. データ範囲のログ出力

```python
# データ範囲のログ出力
if df_p2 is not None and not df_p2.empty and parameter in df_p2.columns:
    logger.info(f"P2[{parameter}] from {df_p2['timestamp'].min()} to {df_p2['timestamp'].max()} range: {df_p2[parameter].min()} – {df_p2[parameter].max()}")

if df_p3 is not None and not df_p3.empty and parameter in df_p3.columns:
    logger.info(f"P3[{parameter}] from {df_p3['timestamp'].min()} to {df_p3['timestamp'].max()} range: {df_p3[parameter].min()} – {df_p3[parameter].max()}")
```

## 使用方法

この修正により、以下の改善が期待できます：

1. グラフが常に最新のデータを表示するようになります
2. ログファイル（`/var/log/web_interface_solo.log`）にデータの範囲が出力されるため、問題の診断が容易になります
3. どのファイルからデータが読み込まれているかがログに表示されるため、データソースの問題を特定しやすくなります

UIの日数選択（"1 Day" → "7 Day" → "1 Day"）を切り替えることで、キャッシュが再読み込みされ、最新のデータが表示されるようになります。
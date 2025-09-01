# Ver4.25.5 Debug - 修正内容

## 概要
このバージョンでは、P1データ収集と描画システムに関する以下の問題を修正しました：

1. **タイムスタンプの変換問題**：
   - タイムスタンプ列が文字列のままでdatetimeに変換されていない問題を修正
   - `pd.to_datetime()`を使用して強制的に変換し、無効な値を処理

2. **P2とP3のグラフが同じになる問題**：
   - データキャッシュの問題を修正
   - キャッシュデータのコピーを返すように変更し、元のデータが変更されないようにした

3. **接続ステータスが表示されない問題**：
   - 接続モニターAPIとの連携を修正
   - APIエンドポイントを直接呼び出すように変更

## 詳細な修正内容

### 1. タイムスタンプの変換問題

`get_historical_data`関数内のタイムスタンプ変換処理を強化しました：

```python
# 変更前
combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])

# 変更後
combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'], errors='coerce')
combined_df = combined_df.dropna(subset=['timestamp'])
```

この変更により：
- `errors='coerce'`パラメータを追加して、変換できない値をNaTに設定
- 無効なタイムスタンプを持つ行を削除して、グラフ描画時のエラーを防止

### 2. P2とP3のグラフが同じになる問題

データキャッシュの処理を改善しました：

```python
# 変更前
self.data_cache[device_id] = (datetime.datetime.now(), combined_df)
return combined_df

# 変更後
self.data_cache[device_id] = (datetime.datetime.now(), combined_df.copy())
return combined_df.copy()
```

この変更により：
- キャッシュに保存するデータのコピーを作成し、元のデータが変更されないようにした
- キャッシュからデータを取得する際もコピーを返すようにした

また、デバッグログを追加して問題の診断を容易にしました：

```python
logger.info(f"Getting historical data for {device_id}, days={days}")
logger.info(f"Using cached data for {device_id}, {len(df)} rows")
logger.info(f"Caching data for {device_id}, {len(combined_df)} rows")
```

### 3. 接続ステータスが表示されない問題

接続ステータスAPIエンドポイントを修正しました：

```python
# 変更前
@app.route('/api/connection/status')
def get_connection_status():
    """API endpoint to get the connection status."""
    return jsonify(visualizer.get_connection_status())

# 変更後
@app.route('/api/connection/status')
def get_connection_status():
    """API endpoint to get the connection status."""
    try:
        # Try to get connection status from the API
        response = requests.get(f"{visualizer.config['monitor_api_url']}/api/connection/latest", timeout=2)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            logger.warning(f"Failed to get connection status: {response.status_code}")
            return jsonify({})
    except Exception as e:
        logger.error(f"Error getting connection status: {e}")
        return jsonify({})
```

この変更により：
- 接続モニターAPIを直接呼び出すようになり、接続ステータス情報が正しく取得されるようになった
- エラーハンドリングを強化して、APIが利用できない場合でも適切に対応

## 追加したデバッグログ

グラフ作成プロセスの診断を容易にするために、以下のデバッグログを追加しました：

```python
logger.info(f"Creating time series graph for {parameter}, days={days}, show_p2={show_p2}, show_p3={show_p3}")
logger.info(f"P2 data: {df_p2 is not None and not df_p2.empty}, P3 data: {df_p3 is not None and not df_p3.empty}")
logger.info(f"Adding P2 data for {parameter}, {len(df_p2)} rows, timestamp type: {type(df_p2['timestamp'].iloc[0])}")
```

これにより、データの取得状況やタイムスタンプの型などを確認できるようになりました。

## 注意事項

- これらの修正は、P1のWebインターフェイスのみに適用されています
- 接続モニターAPIが正しく動作していることを確認してください
- データディレクトリ構造（RawData_P2、RawData_P3）が正しく設定されていることを確認してください
# Ver4.3 デバッグ - 修正内容

## 概要
このバージョンでは、P1データ収集と描画システムに関する以下の問題を修正しました：

1. **タイムスタンプの変換問題**：
   - タイムスタンプ列が文字列のままでdatetimeに変換されていない問題を修正
   - `pd.to_datetime()`を使用して強制的に変換し、無効な値を処理
   - 数値型（Unix秒）と文字列型のタイムスタンプを自動的に検出して適切に変換

2. **グラフ更新の改善**：
   - グラフの更新間隔を30秒から10秒に短縮
   - グラフが自動的に更新されるように修正

3. **過去データの読み込み改善**：
   - /var/lib/raspap_solo/data/RawData_P2および/var/lib/raspap_solo/data/RawData_P3からの過去データを効率的に読み込み
   - 日付ごとのCSVファイルを自動的に検出して処理
   - Webアプリ起動時に過去のデータを含めたグラフを表示

4. **P2とP3のIPアドレスの動的追跡**：
   - センサーデータ受信時に送信元IPアドレスを記録
   - WiFiモニターの設定を自動的に更新
   - MACアドレスの再解決を強制して接続品質の監視を改善

5. **グラフのY軸スケーリング問題の修正**：
   - Y軸が0-100に固定されてしまう問題を修正
   - パラメータの実際の値に基づいて適切なY軸範囲を自動設定
   - データ点が少ない場合や一定値の場合の適切な処理

## 詳細な修正内容

### 1. タイムスタンプの変換問題

CSVファイルのタイムスタンプ列がUnix秒形式または文字列形式で保存されている可能性があるため、データ型を自動的に検出して適切な変換方法を選択するように修正しました：

```python
# get_historical_data関数内の修正
# タイムスタンプのデータ型を確認して適切な変換方法を選択
if df['timestamp'].dtype == 'int64' or df['timestamp'].dtype == 'float64':
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
else:
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

# create_time_series_graph関数内の修正
if df_p2 is not None and not df_p2.empty and 'timestamp' in df_p2.columns:
    # タイムスタンプのデータ型を確認して適切な変換方法を選択
    if df_p2['timestamp'].dtype == 'int64' or df_p2['timestamp'].dtype == 'float64':
        df_p2['timestamp'] = pd.to_datetime(df_p2['timestamp'], unit='s', errors='coerce')
    else:
        df_p2['timestamp'] = pd.to_datetime(df_p2['timestamp'], errors='coerce')
    df_p2 = df_p2.dropna(subset=['timestamp'])

if df_p3 is not None and not df_p3.empty and 'timestamp' in df_p3.columns:
    # タイムスタンプのデータ型を確認して適切な変換方法を選択
    if df_p3['timestamp'].dtype == 'int64' or df_p3['timestamp'].dtype == 'float64':
        df_p3['timestamp'] = pd.to_datetime(df_p3['timestamp'], unit='s', errors='coerce')
    else:
        df_p3['timestamp'] = pd.to_datetime(df_p3['timestamp'], errors='coerce')
    df_p3 = df_p3.dropna(subset=['timestamp'])
```

この変更により：
- Unix秒形式のタイムスタンプが正確にdatetime型に変換される
- キャッシュから取得したデータのタイムスタンプも確実に変換される
- 無効なタイムスタンプを持つ行が削除され、グラフ描画時のエラーを防止

### 2. グラフ更新の改善

更新間隔を短縮し、グラフも自動更新するように変更しました：

```python
# 変更前（DEFAULT_CONFIG内）
"refresh_interval": 30,  # seconds

# 変更後
"refresh_interval": 10,  # seconds
```

```javascript
// 変更前（JavaScript）
setInterval(function() {
    updateCurrentReadings();
    updateConnectionStatus();
}, {{ refresh_interval * 1000 }});

// 変更後
setInterval(function() {
    updateCurrentReadings();
    updateConnectionStatus();
    loadGraphs();  // グラフも10秒ごとに更新
}, {{ refresh_interval * 1000 }});
```

この変更により：
- 10秒ごとに最新のデータが読み込まれる
- グラフが10秒ごとに自動的に更新される

### 3. 過去データの読み込み改善

`get_historical_data`メソッドを改良し、過去のCSVファイルからデータを効率的に読み込めるようにしました。また、データディレクトリのパスを明示的に指定するように変更しました：

```python
def get_historical_data(self, device_id, days):
    import pandas as pd
    import datetime
    import os

    if device_id not in ["P2", "P3"]:
        return None

    # 明示的にデータディレクトリを指定
    if device_id == "P2":
        full_dir = "/var/lib/raspap_solo/data/RawData_P2"
    else:  # P3
        full_dir = "/var/lib/raspap_solo/data/RawData_P3"
    if not os.path.exists(full_dir):
        return None

    end_date = datetime.datetime.now().date()
    date_list = [(end_date - datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]

    frames = []
    for date_str in date_list:
        file_path = os.path.join(full_dir, f"{device_id}_{date_str}.csv")
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
                df = df.dropna(subset=['timestamp'])
                frames.append(df)
            except Exception as e:
                logger.error(f"Failed to read CSV {file_path}: {e}")

    if not frames:
        return None

    df_all = pd.concat(frames, ignore_index=True)
    df_all.sort_values(by='timestamp', inplace=True)
    return df_all
```

この変更により：
- 指定した日数分の過去データを効率的に読み込める
- 日付ごとに保存されたCSVファイルを自動的に検出して読み込む
- タイムスタンプの変換と無効なデータの除外を確実に行う
- Webアプリ起動時に過去のデータを含めたグラフが表示される
- データディレクトリのパスが明示的に指定されるため、設定ファイルに依存せず確実にデータを読み込める

### 4. P2とP3のIPアドレスの動的追跡

P2とP3のIPアドレスを動的に追跡するための機能を追加しました：

```python
# WiFiMonitorクラスに追加したメソッド
def update_device_ip(self, device_id, new_ip):
    if device_id not in self.config['devices']:
        logger.warning(f"Unknown device ID {device_id} - cannot update IP")
        return

    old_ip = self.config['devices'][device_id]['ip']
    if old_ip != new_ip:
        logger.info(f"Updating {device_id} IP: {old_ip} -> {new_ip}")
        self.config['devices'][device_id]['ip'] = new_ip
        self.config['devices'][device_id]['mac'] = None  # force MAC re-resolution
```

```python
# DataCollectorクラスの_handle_client()メソッド内に追加した処理
sender_ip = addr[0]  # 送信元IPアドレスを取得

# WiFiモニターが利用可能な場合、IPアドレスを更新
if self.wifi_monitor is not None and "device_id" in json_data:
    try:
        self.wifi_monitor.update_device_ip(json_data["device_id"], sender_ip)
        logger.info(f"Updated {json_data['device_id']} IP to {sender_ip} in WiFi monitor")
    except Exception as e:
        logger.error(f"Failed to update device IP in WiFi monitor: {e}")
```

この変更により：
- P2とP3のIPアドレスが変更された場合でも自動的に追跡される
- WiFiモニターが常に正しいIPアドレスを使用して接続品質を監視できる
- MACアドレスの再解決が強制されるため、接続情報が常に最新の状態に保たれる

## 使用方法

1. アプリケーションを起動すると、自動的にRawData_P2とRawData_P3ディレクトリからデータが読み込まれます
2. データは10秒ごとに自動的に更新されます
3. グラフには最新のデータが表示されます
4. P2とP3からデータを受信すると、自動的にIPアドレスが追跡され、WiFiモニターの設定が更新されます
5. Connection Statusページでは、常に最新のIPアドレスを使用して接続品質が表示されます

### 5. グラフのY軸スケーリング問題の修正

グラフのY軸が0-100に固定されてしまう問題を修正するため、パラメータの実際の値に基づいて適切なY軸範囲を自動設定するように変更しました：

```python
# create_time_series_graph関数内の修正
# 有効なデータポイントの確認（少なくとも2つの異なる非NaN値が必要）
p2_valid = False
p3_valid = False
y_min = None
y_max = None

# P2データの検証
if show_p2 and df_p2 is not None and not df_p2.empty and parameter in df_p2.columns:
    # 少なくとも2つの異なる非NaN値があるか確認
    p2_unique = df_p2[parameter].dropna().unique()
    if len(p2_unique) >= 2:
        p2_valid = True
        # Y軸スケーリングのための最小/最大値を更新
        p2_min = df_p2[parameter].min()
        p2_max = df_p2[parameter].max()
        y_min = p2_min if y_min is None else min(y_min, p2_min)
        y_max = p2_max if y_max is None else max(y_max, p2_max)

        # グラフにP2データを追加
        # ...

# P3データの検証も同様に実施
# ...

# Y軸範囲の設定
yaxis_config = {}

# 有効な最小/最大値がある場合、Y軸範囲を設定
if y_min is not None and y_max is not None:
    # 見栄えを良くするために小さなパディング（5%）を追加
    y_range = y_max - y_min
    padding = y_range * 0.05 if y_range > 0 else 1
    yaxis_config['range'] = [y_min - padding, y_max + padding]
else:
    # フォールバックとして自動範囲を使用
    yaxis_config['autorange'] = True
    yaxis_config['rangemode'] = 'normal'
```

この変更により：
- パラメータの実際の値に基づいて適切なY軸範囲が自動的に設定される
- データ点が少ない場合や一定値の場合は適切に処理される
- 各パラメータの特性に合わせたスケールでグラフが表示される
- 見栄えを良くするために適切なパディングが追加される

## 注意事項

- RawData_P2とRawData_P3ディレクトリが存在し、適切なCSVファイルが含まれていることを確認してください
- CSVファイルのタイムスタンプ列は適切な形式（YYYY-MM-DD HH:MM:SS）である必要があります
- アプリケーションを終了する際は、Ctrl+Cを使用して適切に終了してください
- P2とP3のIPアドレスが変更された場合、最初のデータ受信時に自動的に更新されます
- WiFiモニターとデータコレクターの両方が正常に起動していることを確認してください

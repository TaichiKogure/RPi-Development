# Flask10X API 仕様（日本語）

最終更新日: 2025-08-24
対象バージョン: Flask10X Steps 1–9 実装版

本書は、Flask10X の REST API エンドポイントの仕様、ペイロードスキーマ、レスポンス、エラーコード、サンプルを記述します。

---

## 1. 共通事項

- ベースURL: `http://<サーバIP>:8888`
- Content-Type: `application/json`
- すべての POST は JSON ペイロードが必須（`get_json(silent=True)` で受理）
- バリデーション失敗時は 400（JSON で詳細）

---

## 2. ヘルス / メトリクス / 履歴

### 2.1 GET /healthz
- 常に 200 を返し、`{"status":"ok"}` を返却

### 2.2 GET /metrics
- 例:
```json
{
  "queue_length": 12,
  "queue_warn_threshold": 4000,
  "write_success_total": 12345,
  "write_error_total": 2,
  "last_received": {
    "data": "2025-08-24 09:00:12",
    "data2": "2025-08-24 09:00:11",
    "data3": null,
    "data4": "2025-08-24 08:59:09"
  },
  "inactivity_seconds": {
    "data": 3,
    "data2": 4,
    "data3": null,
    "data4": 66
  },
  "inactivity_warn_threshold_sec": 120
}
```

### 2.3 GET /history
- 直近の受信履歴を簡易 HTML テーブルで表示（最大 `HISTORY_MAX` 件）

### 2.4 GET /history/json
- 上記と同等の内容を JSON 配列で返却

---

## 3. データ受信エンドポイント

すべての /data* エンドポイントは、
- 受信 → バリデーション → 正規化 → CSV 書き込みジョブをキューへ投入 → 即座に 200 と `{"status": "enqueued"}` を返します。
- キュー満杯時は 503 と `{"status":"queued_failed"}`

### 3.1 POST /data

- 用途: 単純な圧力・温度
- CSV: PicodataX.csv
- 列: `[current_time, Pressure, Tempereture]`

リクエストスキーマ:
```json
{
  "pressure": "1013hPa",
  "temperature": "25.1C"
}
```

成功レスポンス:
```json
{"status":"enqueued"}
```

### 3.2 POST /data2

- 用途: CO2・BME680 系
- CSV: BedRoomEnv.csv
- 列: `[current_time, CO2, Tempereture, Humidity, Pressure, GasResistance]`

スキーマ:
```json
{
  "co2": 650,
  "temperature": 25.3,
  "humidity": 52.1,
  "pressure": "1012.8hPa",
  "gas_res": 8500
}
```

### 3.3 POST /data3

- 用途: 屋外環境
- CSV: OutsideEnv.csv
- 列: `[current_time, Temperature-outside, Humidity-outside, Pressure-outside, GasResistance-outside]`

スキーマ:
```json
{
  "temperature": 30.2,
  "humidity": 40.0,
  "pressure": 1008.2,
  "gas_res": 12345
}
```

### 3.4 POST /data4

- 用途: 複合センサ（CO2, MQ-2, DS18B20, DHT11）
- CSV: LR_env.csv
- 列: `[current_time, CO2, AnalogValue, Voltage, Temperature_DS18B20, Temperature_DHT11, Humidity_DHT11]`

スキーマ:
```json
{
  "mh_z19": {"co2": 700},
  "mq_2": {"analog_value": 123, "voltage": 1.20},
  "ds18b20": {"temperature": 24.8},
  "dht11": {"temperature": 25.1, "humidity": 51.0}
}
```

---

## 4. エラー応答

- 400 Bad Request（バリデーション失敗）
```json
{
  "error": "validation failed",
  "details": {
    "pressure": "below minimum 0",  
    "dht11.humidity": "above maximum 100"
  }
}
```
- 503 Service Unavailable（キュー満杯）
```json
{"status":"queued_failed"}
```
- 500 Internal Server Error（予期せぬ例外）
```json
{"error":"internal server error"}
```

---

## 5. 単位と正規化

- 数値は、`_to_number()` により単位・記号を除去して float 化します
  - 例: "1013hPa" → 1013.0, "25C" → 25.0
- 数値の最小/最大レンジはスキーマでチェック

---

以上が API 仕様の概要です。運用・メトリクスの詳細は「04_ログとメトリクス_JP.md」を参照してください。
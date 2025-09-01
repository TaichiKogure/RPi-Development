# Graph11X Web ビューア（インタラクティブ版）

本ドキュメントは、Graph11X の堅牢な前処理（列名正規化・日時パーサ・単位除去・外れ値検知・絶対湿度計算・ダウンサンプリング）をそのまま活かしつつ、Webブラウザ上で Plotly によりインタラクティブにグラフを表示できる軽量 Web アプリ（Flask）について説明します。

- 実装ファイル: `HomeRaspMod/ModVer_GraphViewer/Graph11X_Web.py`
- 依存: `Graph11X.py`（同フォルダ）
- 目的: 軸レンジ（Y軸）の任意指定、データ量の軽量化（最大点数 `max_points` による可変ダウンサンプリング）、データセット表示のON/OFF、集計方法（平均/中央値/最小/最大）の切替えなどを、Web UI 上の操作で即時反映させる。

## 1. 構成と動作
- Flask サーバが `/` で Web UI（HTML）を返し、以下の API を提供します。
  - `GET /api/parameters`: 表示可能なパラメータ一覧を返します（例: temperature, humidity, absolute_humidity, co2, pressure, gas_resistance）。
  - `GET /api/graph`: 指定パラメータ・期間（日数）・最大点数・集計方法・表示対象デバイス・Y軸範囲に応じて、Plotly 図の JSON を返します。
- サーバ側は Graph11X の関数を利用して CSV 読込・正規化・絶対湿度の導出・ダウンサンプリングを実施します。
- クライアント（ブラウザ）は Plotly 2.x を利用して描画します。軸レンジはドラッグでのズーム・パンに加え、コントロールの Y min / Y max 入力で固定指定できます。

## 2. 必要要件
- Python 3.8+
- 依存モジュール（仮想環境推奨）
  - Flask
  - pandas
  - numpy
  - plotly

```
python -m venv venv
venv/Scripts/activate  # Windows
# または source venv/bin/activate  # Linux / macOS
pip install flask pandas numpy plotly
```

## 3. 起動方法
```
cd G:\RPi-Development\HomeRaspMod\ModVer_GraphViewer
python Graph11X_Web.py
# 既定ポート: 8088 で起動（環境変数 GRAPH11X_WEB_PORT で変更可）
```
ブラウザで `http://<サーバIP>:8088/` にアクセスしてください。

## 4. UI の使い方
- Parameter: 表示パラメータの選択（temperature / humidity / absolute_humidity / co2 / pressure / gas_resistance など）。
- Datasets: 表示対象データセットのON/OFF（BedRoom / Outside / Pico / DiningRoom / Desk）。
- Days: 直近 N 日分のデータに絞り込み（整数）。
- Max points: ダウンサンプリングの上限点数。値を小さくすると通信・描画が軽くなります（例: 1000 / 2000 / 5000）。
- Aggregation: ダウンサンプリング時の集計方法（mean/median/min/max）。
- Y min / Y max: Y軸範囲の固定（空欄のままにすると自動レンジ）。
- Update: 上記の設定でグラフを更新します。

Plotlyの標準操作（ドラッグでズーム、ダブルクリックでリセット、凡例クリックで系列の一時非表示）にも対応しています。

## 5. データソースについて
`Graph11X.py` の `DATA_FILES` / `REQUIRED_COLS` を利用します。既存の CSV ファイル（ベッドルーム/屋外/ピコ/ダイニング/BME680）のパスが設定されています。必要に応じて `Graph11X.py` 内の定義を編集してください。

Graph11X の前処理パイプラインにより、以下が自動的に適用されます：
- 列名の正規化（別名吸収・コリジョン回避・ログ出力）
- 日時パースの寛容化（全角→半角、`/`→`-`、`Z`/タイムゾーン対応、UNIX秒/ミリ秒）
- 数値列の単位・記号除去（°C, %, hPa, ppm, Ω/kΩ→×1000, カンマ除去、NA表現統一）
- 列ごとの異常レンジ検知（例: humidity<0 or >100）
- 絶対湿度の自動導出（温度×湿度のペアを優先順に探索）
- 差分読込キャッシュと毎回の再正規化適用

## 6. 軽量化（データ量の調整）
- `Max points` でブラウザへ返す点数上限を調整できます。期間（Days）が長い場合は点数が増えがちですが、上限を下げることで自動的に時間解像度が粗く（例: 数十秒〜数分単位）なり、描画が軽くなります。
- `Aggregation` で集計方法を切り替えることで、ノイズ特性やピークの見え方を調整できます（例: max でピーク強調、median で外れ値に頑健）。

## 7. トラブルシュート
- グラフが表示されない/空：
  - `Graph11X.py` の `DATA_FILES` のパスが正しいか確認
  - 必要列（REQUIRED_COLS）の実在、日付列の形式（current_time 等）
  - サーバ側コンソールログにエラーが出ていないか確認
- JSON化でエラー：NumPy配列を含むと Flask の `jsonify` が失敗します。本アプリでは `to_dict()` の出力に対して再帰的に `list` 化しています。
- パフォーマンス：`Days` を短く、`Max points` を小さくして試してください。

## 8. カスタマイズ
- 既定ポート変更：`GRAPH11X_WEB_PORT` 環境変数で上書き
- 既定のデータパス・列：`Graph11X.py` の `DATA_FILES` / `REQUIRED_COLS` を編集
- 既定の点数上限・集計：`Graph11X.py` の `MAX_POINTS` / `AGG_METHOD` を編集（ただし Web 側からも上書き可）

## 9. セキュリティ注意
本アプリはローカル利用を想定したミニマルな開発用サーバです。外部公開時はリバースプロキシ・認証・TLS 等の導入を検討してください。

---
最終更新: 2025-08-24

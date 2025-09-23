# 会議室向け CO2 ピーク検出・人数推定ツール（OffceAnalysisVer4）

本ツールは `G:\RPi-Development\EnvDataAnl\OfficeENVData` に保存された P1/P2/P3 の CSV を読み込み、
特に会議室（P2 8名程度、P3 30名程度）を対象に CO2 の上昇イベント（会議と想定）を自動検出し、
ピーク時刻・上昇時間・上昇速度（ppm/分）を算出、複数モデルで同時に「推定参加人数」を出力します。
さらに、CO2 ピークが 1000ppm を超えた会議の割合（%）を集計します。

- P1: オフィス（参考出力に含めることが可能）
- P2: 小会議室（最大 ~8 名）
- P3: 大会議室（最大 ~30 名）

## 主な機能
- CSV ロード（Ver1/2/3 と同形式）：`P1_fixed Office.csv`, `P2_fixed Office.csv`, `P3_fixed Office.csv`
- 頑健なタイムスタンプ変換（UNIX 秒 or 文字列）と数値化
- CO2 スムージング（中央値ローリング、既定 5 サンプル）と勾配（ppm/分）算出
- イベント検出（開始/終了しきい値＋勾配条件、短いギャップの結合）
- 各イベントの特性量：開始/終了、ピーク時刻/値、上昇時間（start→peak）、上昇速度（ppm/分）
- 人数推定（複数モデル）
  - Heuristic（経験的）：勾配の高パーセンタイルを満席相当に較正
  - Mass-balance（物質収支）：n ≈ slope*V/q（換気 ACH による補正係数つき）
  - Band（帯域）：勾配レンジ → 充足率帯（0–10%, 10–30%, ...）
- 1000ppm 超会議の割合（P2/P3 別）
- 図出力：CO2 時系列にイベント区間とピーク線を重畳

## 出力物（`OffceAnalysisVer4/output` 配下）
- `events_P2_v4.csv`, `events_P3_v4.csv`（必要に応じて `events_P1_v4.csv`）
  - 列例：`start, end, duration_min, peak_time, peak_co2, start_co2, end_co2, rise_time_min, rise_rate_ppm_min, est_people_heuristic, est_people_mass, est_people_band, device_id`
- `summary_co2_events_v4.json`
  - 1000ppm 超会議の割合（%）、デバイス別中央値（上昇速度/上昇時間/ピーク/人数）など
- 図：`ts_co2_events_P2_v4.png`, `ts_co2_events_P3_v4.png`

## 使い方（PowerShell）
```
cd G:\RPi-Development\EnvDataAnl\OfficeENVData\OffceAnalysisVer4
python office_analysis_v4.py
```
オプション：観測期間や検出・推定パラメータを調整
```
python office_analysis_v4.py \
  --days 90 \
  --start-th 750 --end-th 680 --min-slope 2.0 \
  --smooth 5 --calib-high-pct 0.95 \
  --p2-volume 120 --p3-volume 250 --ach 1.5 --q-per-person 0.004 \
  --include-p1
```

### 主な引数（既定値）
- `--days`: 直近 N 日に限定（未指定なら全期間）
- `--start-th`: 会議開始判定の CO2 しきい値（ppm、既定 750）
- `--end-th`: 会議終了判定の CO2 しきい値（ppm、既定 680）
- `--min-slope`: 上昇中とみなす最少勾配（ppm/分、既定 2.0）
- `--smooth`: CO2 の中央値ローリング窓（サンプル数、既定 5）
- `--calib-high-pct`: Heuristic 較正用の勾配パーセンタイル（0–1、既定 0.95）
- `--p2-volume`, `--p3-volume`: 会議室体積（m³）
- `--ach`: 換気回数（Air Changes per Hour）
- `--q-per-person`: 1 人あたり CO2 発生量（m³/分、0.004–0.005 目安）
- `--include-p1`: 参考として P1 も出力に含める

## 人数推定モデルの考え方
- Heuristic：
  - 同一デバイス内の勾配分布の高パーセンタイル（例：95%tile）を満席（P2=8, P3=30）に対応づけ、勾配比で人数を比例推定
  - データ駆動で手軽に相対比較が可能
- Mass-balance：
  - dC/dt ≈ (G/V)*1e6 より G ≈ slope*V/1e6（m³/分）
  - 人あたり発生量 q を仮定し n ≈ G/q と推定
  - 換気（ACH）による上昇鈍化を単純な補正係数で反映（開放/機械換気の違い等は別途調整）
- Band：
  - 管理画面等で大まかな混雑度として表示したい場合に有用（0–10%/10–30%/…）

## 1000ppm 超会議の割合
- デバイスごとに検出イベントのピーク CO2 を集計し、`peak_co2 >= 1000` の割合（%）を算出
- 出力は `summary_co2_events_v4.json` の `pct_meetings_peak_over_1000ppm` に含まれます

## 解析チップス
- サンプリング間隔が粗い場合は `--smooth` を増やすと検出が安定します
- 偽陽性が多い場合：`--start-th` を上げる、`--min-slope` を上げる、`--end-th` をやや下げる
- 会議が分断される場合：`detect_events()` 内の `gap_close_min` を大きくする（コード内で調整可）
- Mass-balance の体積や ACH は施設の仕様に合わせて調整してください

## 前提条件 / 入力フォーマット
- CSV は Ver1/2/3 と同様の構成を想定（列名は自動マッピング）。最低限 `timestamp`, `co2` が必要です。
- `timestamp` は UNIX 秒（数値）または文字列（ISO 等）に対応。変換失敗行は自動除外します。

## トラブルシューティング
- イベントが出ない：
  - CO2 列が存在するか、NaN ばかりでないか確認
  - しきい値や勾配条件が厳しすぎないか（`--start-th`, `--min-slope` を下げる）
- 人数が大きすぎる/小さすぎる：
  - Heuristic の `--calib-high-pct` を調整
  - Mass-balance の体積/ACH/q を見直す
- グラフが真っ直ぐ：
  - スムージング過多の可能性（`--smooth` を小さく）

## ライセンス
社内利用を想定。外部公開時は別途ご相談ください。

# 会議室占有率ヒートマップ生成ツール（Ver4 追加モジュール）

本ツールは Ver4（CO2 ピーク検出・人数推定）で用いたロジックを基に、P2（小会議室）と P3（大会議室）の「占有人数」のヒートマップを作成します。
縦軸を日付、横軸を時刻（0–23 時）、色で推定人数を表現します。人数の推定は「立ち上がり勾配（ppm/分）」に加えて「ピークの高さ」と「立ち上がり所要時間」による補正を施し、短時間で急上昇・高ピークの会議は人数が多いと推定、緩やかな上昇や低ピークは少人数と推定します。

- 対象ディレクトリ（既定）：`G:\RPi-Development\EnvDataAnl\OfficeENVData`
- 入力ファイル：
  - `P2_fixed Office.csv`
  - `P3_fixed Office.csv`
- 出力（`OffceAnalysisVer4/output` 配下）：
  - `occupancy_pivot_mean_P2_v4.csv`, `occupancy_pivot_max_P2_v4.csv`
  - `occupancy_pivot_mean_P3_v4.csv`, `occupancy_pivot_max_P3_v4.csv`
  - `heatmap_occupancy_mean_P2_v4.png`, `heatmap_occupancy_max_P2_v4.png`
  - `heatmap_occupancy_mean_P3_v4.png`, `heatmap_occupancy_max_P3_v4.png`
  - `summary_occupancy_heatmap_v4.json`

## 使い方（PowerShell）
```
cd G:\RPi-Development\EnvDataAnl\OfficeENVData\OffceAnalysisVer4
python office_occupancy_heatmap_v4.py
```
オプションの例：
```
python office_occupancy_heatmap_v4.py \
  --days 120 \
  --start-th 750 --end-th 680 --min-slope 2.0 \
  --smooth 5 \
  --p2-volume 120 --p3-volume 250 --ach 1.5 --q-per-person 0.004 \
  --method mean --cmap magma --dpi 150
```

## 推定アルゴリズムの概要
1. CO2 をメディアンで平滑化（既定: 窓幅 5 サンプル）。
2. 平滑化 CO2 から時刻差分で "slope_ppm_per_min"（ppm/分）を算出。
3. 上昇イベントを検出（開始しきい値、終了しきい値、最小勾配、短いギャップの結合）。
4. 各イベントについて、開始→ピークまでの上昇勾配から「人数の基礎推定」を計算：
   - 質量収支近似：`n_mass ≈ slope * Volume / 1e6 / q_per_person`（ACH による緩和係数を適用）
   - ヒューリスティック：装置ごとに高パーセンタイル勾配を満員（容量）に対応付けた比例マッピング
   - `n_base = 0.6*n_mass + 0.4*n_heur` を容量でクリップ
5. 補正（本ツールの追加点）：
   - ピーク高さ補正：`peak_delta_ppm = peak - start` に応じて最大 +50%（400ppm あたり +100%/4 を目安）。
   - 立ち上がり時間補正：基準 20 分に対し、短時間（<20分）は最大 +30%、長時間は最小 0.7 倍。
   - 最終人数推定：`est_corrected = clip(n_base * peak_corr * dur_corr, 0, capacity)`
6. 補正後の人数をイベント継続時間にわたり 1 分粒度で時系列に展開。
7. 日付×時刻で平均（mean）・最大（max）に集計し、CSV とヒートマップ PNG を出力。

## 主なパラメータ
- `--start-th / --end-th` … CO2 の開始/終了しきい値（ppm）。
- `--min-slope` … 上昇イベントとみなす最小勾配（ppm/分）。
- `--smooth` … 平滑化窓（サンプル数）。
- `--p2-volume / --p3-volume` … 部屋体積（m³）。
- `--ach` … 換気回数（回/時）。スロープ観測値を弱める補正に使用。
- `--q-per-person` … 1 人あたり CO2 発生量（m³/分）。デフォルト 0.004（= 4 L/分）。
- `--method` … カラーマップの基準（mean または max）。両方の図と CSV は常に保存されます。

## 容量（上限）の扱い
- 既定容量：P2=8 名、P3=30 名。推定値は [0, 容量] にクリップされます。

## トラブルシュート
- 「No occupancy could be computed」：期間内に上昇イベントが検出されなかった可能性。
  - `--days` を広げる、`--start-th` を下げる、`--min-slope` を下げる等でご調整ください。
- 出力が真っ白：CSV にデータがない、または検出されたイベントが極端に少ない可能性。
- 体積・換気・発生量は実環境に合わせて調整すると推定精度が向上します。

## 依存関係
```
pip install pandas numpy matplotlib seaborn
```

## ライセンス
社内利用を想定。外部公開時は別途ご相談ください。

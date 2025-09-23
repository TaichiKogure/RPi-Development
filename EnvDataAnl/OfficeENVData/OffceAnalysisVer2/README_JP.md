# オフィス環境データ詳細解析ツール（OffceAnalysisVer2）

本ツールは Ver1 を拡張し、温度・絶対湿度・CO2 濃度に特化した詳細解析を実施します。日中/夜間、月別、週別、時刻別など多面的に統計を算出し、ヒートマップ・ヒストグラム・時系列・箱ひげ/バイオリン・散布図・相関行列など 10 種類以上の可視化を自動生成します。

- 対象ディレクトリ（既定）：`G:\RPi-Development\EnvDataAnl\OfficeENVData`
- 入力ファイル（既定）：
  - `P1_fixed Office.csv`
  - `P2_fixed Office.csv`
  - `P3_fixed Office.csv`
- 出力ディレクトリ：`OffceAnalysisVer2/output`

## 主な機能
1. タイムスタンプの自動判定（UNIX秒/文字列）と数値列の強制変換
2. 絶対湿度の自動計算（温度・相対湿度から算出）
3. 時間特徴量の付与：日付/時/曜日/週/月、日中・夜間フラグ（開始時刻は可変）
4. 統計出力（CSV/JSON）：
   - overall（全体統計）
   - day/night（日中・夜間）
   - hourly（時間別）
   - weekday（曜日別）
   - weekly（週別）
   - monthly（月別）
   - 高値期間（指標別の上位パーセンタイル）
5. 可視化（PNG）：
   - 時系列＋移動平均（各指標）
   - ヒストグラム＋KDE（各指標）
   - 日中/夜間の箱ひげ＋バイオリン
   - 曜日×時刻ヒートマップ
   - 日付×時刻ヒートマップ
   - 週別/⽉別の推移
   - 相関ヒートマップ（デバイス別）
   - 温度×絶対湿度（CO2 カラー）散布図
   - 高値時間帯ヒートマップ（上位パーセンタイル）

## インストール要件
- Python 3.9 以上を推奨
- 必要パッケージ：`pandas`, `numpy`, `matplotlib`, `seaborn`

```
pip install pandas numpy matplotlib seaborn
```

## 使い方（PowerShell）
```
cd G:\RPi-Development\EnvDataAnl\OfficeENVData\OffceAnalysisVer2
python office_analysis_v2.py
```
オプション：直近 N 日に限定、日中開始時刻、上位パーセンタイルを調整
```
python office_analysis_v2.py \
  --base-dir "G:\\RPi-Development\\EnvDataAnl\\OfficeENVData" \
  --days 90 \
  --day-start 6 \
  --p-high-pct 0.9
```

## 出力物（例）
- `summary_overall_v2.json` … 全体メタ情報＋統計
- `stats_day_night_v2.csv` … 日中/夜間の統計
- `stats_hourly_v2.csv` … 時間別統計
- `stats_weekday_v2.csv` … 曜日別統計
- `stats_weekly_v2.csv` … 週別統計
- `stats_monthly_v2.csv` … 月別統計
- `high_periods_*.csv` … 指標別の高値期間（上位パーセンタイル）
- 可視化 PNG（各種）
  - `timeseries_temperature_with_rolling_v2.png`
  - `timeseries_absolute_humidity_with_rolling_v2.png`
  - `timeseries_co2_with_rolling_v2.png`
  - `dist_*_hist_kde_v2.png`
  - `daynight_*_violin_box_v2.png`
  - `heatmap_*_weekday_hour_v2.png`, `heatmap_*_date_hour_v2.png`
  - `monthly_*_bar_v2.png`, `weekly_*_line_v2.png`, `weekday_*_line_v2.png`
  - `corr_P1_v2.png` など（デバイス別）
  - `scatter_temp_abs_col_co2_v2.png`
  - `high_*_date_hour_*_v2.png`

## 解析の見どころ
- 温度・絶対湿度・CO2 の高値時間帯をヒートマップで直感的に把握
- 日中/夜間の差や曜日/時刻別のプロファイルから運用改善のヒントを抽出
- 相関を見ることで、換気/空調/発熱源などの影響関係を仮説化

## よくある質問
- ファイルが見つからない：入力 CSV のファイル名/パスを確認してください（スペース含む）。
- タイムスタンプが不正：CSV の timestamp 列が数値（UNIX秒）か文字列かをご確認ください。ツール側で自動判定します。
- 絶対湿度が NaN：温度・相対湿度のどちらかが欠損している可能性があります。

## ライセンス
社内利用を想定。外部公開時は別途ご相談ください。

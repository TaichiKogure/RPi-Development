# 環境データ総合解析ツール（4センサー対応）

本ツールは、`G:\RPi-Development\EnvDataAnl` に保存された 4 系統（P1, P2, P3, P4）のセンサーデータ（CSV）を自動検出し、以下の観点で総合解析を行います。

- 時系列の推移（デバイス別）
- 時間帯別プロファイル（24 時間の平均推移）
- 昼夜別の分布比較（6:00–18:00 を「昼」と定義）
- 相関行列（デバイス別・項目間の相関）
- ローリング平均によるトレンド可視化
- 欠測率（項目別のデバイスごとの充足率）

解析結果の図（PNG）と集計テーブル（CSV）は `EnvDataAnl/output` 配下に保存され、`summary.json` にサマリが出力されます。

---

## 1. 対象データの前提
- フォルダ: `G:\RPi-Development\EnvDataAnl`
- 想定ファイル名例:
  - `P1_fixed 2.csv`, `P2_fixed 2.csv`, `P3_fixed 2.csv`, `P4_fixed.csv`
  - 日付付きファイル（例: `P2_2025-09-21.csv`）にも対応します。
- CSV の列名は自動正規化します。以下のような表記ゆれに対応:
  - 時刻: `timestamp`, `time`, `日時`, `date`, `datetime`, `ts` など
  - 温度: `temperature`, `temp`, `気温`, `氣温`, `temp_c` など
  - 湿度: `humidity`, `rh`, `湿度`
  - 気圧: `pressure`, `press`, `気圧`
  - Gas: `gas_resistance`, `gas`, `gas_res`, `gas_ohm` など
  - CO2: `co2`, `co2_ppm`, `co₂` など
- `device_id` 列がない場合は、ファイル名から `P1/P2/P3/P4` を推定し補完します。
- `timestamp` は数値（UNIX 秒）でも文字列でも自動判別して日時に変換します。

---

## 2. 使い方（基本）
仮想環境（推奨）で以下のパッケージをインストールしてください。

```
pip install pandas numpy matplotlib seaborn plotly
```

実行:

```
cd G:\RPi-Development\EnvDataAnl
python env_analyzer.py                 # カレントフォルダを自動スキャン
python env_analyzer.py --days 3        # 直近3日分のみ解析
python env_analyzer.py --tz Asia/Tokyo # タイムゾーン指定（任意）
```

特定ファイルに限定して解析したい場合:

```
python env_analyzer.py --files "P1_fixed 2.csv" "P2_fixed 2.csv"
```

実行後、`EnvDataAnl/output` に解析結果が生成されます。

---

## 3. 出力内容
- 図（PNG）
  - `timeseries_<param>.png` … `temperature`, `humidity`, `pressure`, `gas_resistance`, `co2` の時系列
  - `hourly_profile_<param>.png` … 1 日の時間別平均プロファイル
  - `daynight_hist_<param>.png` … 昼/夜の分布比較（ヒストグラム + KDE）
  - `corr_<device>.png` … デバイス別の相関行列ヒートマップ
- テーブル（CSV）
  - `completeness_by_device.csv` … 項目ごとの非欠損率（0〜1）
  - `hourly_stats.csv` … 時間別の `count/mean/std/min/max`
  - `daynight_stats.csv` … 昼夜別の `count/mean/std/min/max`
  - `rolling_trends_sample.csv` … ローリング平均と外れ値判定サンプル（先頭 2000 行）
- サマリ（JSON）
  - `summary.json` … 生成物一覧、対象期間、デバイス一覧など

---

## 4. 解析手法の概要
- 時系列可視化: センサー値の変動やドリフトを直感的に把握。
- 時間帯別プロファイル: 1 日の周期性（生活/空調/日射の影響）を把握。
- 昼夜別分布: 温度や CO2 の昼夜差（活動度・換気・外気温）を比較。
- 相関行列: パラメータ間の関係性（例: 温度と絶対湿度/気圧/Gas/CO2 など）。
- ローリング平均: 短期ノイズを平滑化し、緩やかなトレンドを確認。
- 外れ値検出（Z スコア）: 設定値から大きく逸脱した値をフラグ化。

昼夜の定義は単純化のため「6:00–18:00 を昼」としています。厳密な日の出/日の入りで分けたい場合は、
`astral` 等のライブラリで拡張可能です。

---

## 5. 列名と時刻の自動補正ロジック
- 列名: よくある表記ゆれを正規化し、内部では英語の固定名で扱います。
- `timestamp`:
  - 数値 → UNIX 秒として解釈
  - 文字列 → `pd.to_datetime(..., errors='coerce')` でパース
  - すべて失敗した場合は 10 桁の数字（UNIX 秒）を抽出して再試行
- 欠損行は解析前に除外します。

---

## 6. 解析のカスタマイズ
- 解析対象期間: `--days` で指定（0=全期間）
- タイムゾーン: `--tz` で指定（例: `Asia/Tokyo`）
- 昼夜境界: コード中の `add_time_features()` の `is_daytime` 条件を変更してください。
- ローリング窓幅: `rolling_trends(..., window=30)` の `window` を変更
- 外れ値しきい値: `detect_outliers_zscore(..., z_thresh=3.5)` を変更

---

## 7. トラブルシューティング
- CSV が検出されない
  - ファイル名先頭が `P1`/`P2`/`P3`/`P4` で始まるか確認してください。
  - 拡張子が `.csv` であることを確認。
- グラフが真っ白/値が出ない
  - `timestamp` が正しく変換できていない可能性。CSV の `timestamp` 列の形式を確認。
  - 値が文字列の場合は数値に変換できず `NaN` になります。列名・区切り・小数点を確認。
- 日本語ファイル名・空白を含むファイル名
  - 本ツールは OS のファイルパスとして扱うため、基本的に問題ありません。`--files` 指定時は引用符で囲んでください。

---

## 8. 解析ガイド（考察の視点）
- 温度の昼夜差が大きい場合 → 断熱/空調/日射の影響を検討。
- CO2 のピークが特定時間に集中 → 人の活動・換気タイミングと関連。
- Gas 抵抗（VOC 指標）の上昇 → 換気不足や調理/清掃等のイベント検知の糸口。
- 相関が強い組み合わせ → 物理的関係（例: 温度と飽和水蒸気量）や、同一要因による共変動の可能性。
- 週次パターン（曜日別）を見る → 生活サイクルや業務スケジュールの影響。

---

## 9. ライセンス/注意
- 本ツールは解析補助です。センサーの校正状態や設置環境に依存して結果が変わる点にご留意ください。
- 医療・安全管理等の用途では、必ず適切な計測機器や手順による確認を行ってください。

---

## 10. 開発メモ
- コード: `EnvDataAnl/env_analyzer.py`
- 出力: `EnvDataAnl/output/`
- 依存: `pandas`, `numpy`, `matplotlib`, `seaborn`

### Ver2（ノイズ平滑化＋補完版）について
- 新しい解析スクリプト: `EnvDataAnl/env_analyzer_v2.py`
- 追加機能:
  - 欠測の時間補間（`interpolate(method='time')`）で空白を補完
  - ローリング平均（移動平均）でノイズを平滑化（デフォルト15サンプル）
  - 残差のローリング標準偏差/中央値絶対偏差（MAD）でノイズ量を定量化し、時間推移を追跡
  - 各センサ（P1〜P4）を同一グラフで比較可能なスムージング済みパネル図を出力
- 出力先: `EnvDataAnl/output_v2/`
- 代表的な出力
  - `timeseries_<param>_smoothed_v2.png`（スムージング時系列）
  - `noise_timeseries_<param>_v2.png`（ノイズ推移）
  - `unified_smoothed_panel_v2.png`（P1〜P4の一元比較）
  - `noise_hourly_stats_v2.csv`, `noise_daynight_stats_v2.csv`（ノイズ統計）
  - `completeness_after_interp_v2.csv`（補完後の充足率）
- 使い方の例:
```
cd G:\RPi-Development\EnvDataAnl
python env_analyzer_v2.py --days 7 --tz Asia/Tokyo --resample "1T" --smooth-window 15 --noise-window 60
```
  - `--resample` は等間隔化（例: 1分）を有効化します。省略時は元のサンプリングのまま処理します。

### 日本語フォントに関する注意（重要）
Matplotlib の既定フォント（DejaVu Sans など）は日本語グリフを十分に持たないため、日本語タイトルや注記を含む図を作成する際に「Missing glyph」警告が大量に出る場合があります。本ツールでは `env_analyzer.py` および `env_analyzer_v2.py` のインポート時に、日本語対応フォント（例: Noto Sans CJK JP / IPAexGothic / 游ゴシック / MS ゴシック / メイリオ）を自動検出して `rcParams["font.family"]` を切り替える処理を追加済みです。該当フォントがシステムに存在すれば警告は解消します。

- Windows での推奨: メイリオ（Meiryo）/ 游ゴシック（Yu Gothic）は標準で入っています。
- Raspberry Pi / Linux での推奨: `sudo apt install fonts-noto-cjk` または `sudo apt install fonts-ipafont-gothic`
- それでも警告が出る場合: 日本語フォントのインストール後に再実行してください。もしくは図中の日本語を英語へ置き換えてください。

改善案（将来）:
- 日の出/日の入りベースの昼夜判定（`astral` 利用）
- 欠測補間やドリフト補正、センサー間のキャリブレーション
- 週次/月次の季節性分解（`statsmodels` の STL 分解など）

# オフィス環境データ ヒートマップ特化解析（OffceAnalysisVer3）

本ツールは Ver1/Ver2 を補完し、P1/P2/P3 各デバイスごと・各パラメータの「日付 × 時刻」ヒートマップを詳細に出力します。
日付方向のラベルは小さめにし、長期間のデータでも俯瞰できるよう図の縦サイズを自動調整します。

- 対象ディレクトリ（既定）：`G:\RPi-Development\EnvDataAnl\OfficeENVData`
- 入力ファイル（既定）：
  - `P1_fixed Office.csv`
  - `P2_fixed Office.csv`
  - `P3_fixed Office.csv`
- 出力先：`OffceAnalysisVer3/output`

## 主な機能
- タイムスタンプの自動判定（UNIX秒/文字列）
- 数値列の強制変換（温度/湿度/気圧/ガス抵抗/CO2/絶対湿度）
- 絶対湿度の自動計算（温度・相対湿度から算出、欠損補完）
- 直近 N 日に限定するフィルタ（任意）
- デバイス×パラメータごとに、`X=時刻(0-23)`, `Y=日付`, `色=平均値` のヒートマップPNGを出力
- 日付方向のラベルを小さめ（fontsize=6）に設定、日数に応じて図の高さを自動拡大

## 使い方（PowerShell）
```
cd G:\RPi-Development\EnvDataAnl\OfficeENVData\OffceAnalysisVer3
python office_analysis_v3.py
```
オプション：
```
python office_analysis_v3.py \
  --days 60 \
  --params temperature absolute_humidity co2 \
  --cmap "turbo" \
  --vmin 0 --vmax 2000 \
  --dpi 150
```

- `--days`: 直近N日だけ解析（省略時は全期間）
- `--params`: 出力するパラメータを指定（既定は利用可能な全パラメータ）
- `--cmap`: カラーマップ（`viridis`, `magma`, `turbo` など）
- `--vmin`, `--vmax`: カラースケールの固定（省略時は自動）
- `--dpi`: 画像解像度

## 出力される図の例
- `heatmap_temperature_date_hour_P1_v3.png`
- `heatmap_absolute_humidity_date_hour_P2_v3.png`
- `heatmap_co2_date_hour_P3_v3.png`
  など、デバイス×パラメータごとのPNGが `OffceAnalysisVer3/output` に保存されます。

## 入力ファイルの前提
CSV の列名は自動マッピングされます（例：`Temp`, `氣温`, `温度` → `temperature`）。
タイムスタンプ列は数値（UNIX秒）または文字列に対応します。変換できない行は自動的に除外します。

## 注意点
- 1日に複数サンプルがある場合、同じ「日付×時刻」マスは平均で集計されます。
- 長期データでは図が縦に長くなるため、ビューアで拡大して確認してください。
- カラースケールを固定したい場合は `--vmin/--vmax` を併用してください。

## 依存パッケージ
```
pip install pandas numpy matplotlib seaborn
```

## トラブルシュート
- 「ファイルが見つからない」: 入力CSVのパスとファイル名（スペース含む）をご確認ください。
- 「真っ白な図」: 該当パラメータが存在しない、もしくは該当期間にデータがない可能性があります。
- 「目盛りが重なる」: 長期間の場合は図が長くなりますが、保存画像を拡大表示してご確認ください。

## ライセンス
社内利用を想定。外部公開時は別途ご相談ください。

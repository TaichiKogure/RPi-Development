# オフィス環境データ解析ツール（OffceAnalysisVer1）

本ツールは `G:\RPi-Development\EnvDataAnl\OfficeENVData` に保存された 3 拠点（P1, P2, P3）の CSV を読み込み、
湿度と CO2 を中心に以下の解析を行います。

- 日中（6:00–18:00）/ 夜間（18:00–6:00）の比較（平均・分散・最小・最大）
- 曜日別の平均プロファイル（各デバイス別）
- 時系列トレンド（生データ＋30サンプル移動平均）
- 欠損や異常値は自動的に除外（NaT/NaNの行を除去、数値は強制変換）

出力は同フォルダ配下の `OffceAnalysisVer1/output` に PNG と CSV、サマリ JSON として保存されます。

## 想定する入力ファイル
- `G:\RPi-Development\EnvDataAnl\OfficeENVData\P1_fixed Office.csv`
- `G:\RPi-Development\EnvDataAnl\OfficeENVData\P2_fixed Office.csv`
- `G:\RPi-Development\EnvDataAnl\OfficeENVData\P3_fixed Office.csv`

※ 上記ファイルの一部が存在しない場合は、そのデバイスをスキップして解析を継続します。

## 実行方法（PowerShell）
```
cd G:\RPi-Development\EnvDataAnl\OfficeENVData\OffceAnalysisVer1
python office_analysis_v1.py
```
オプション：直近 N 日に限定する場合
```
python office_analysis_v1.py --days 30
```
別のデータディレクトリを明示する場合
```
python office_analysis_v1.py --base-dir "G:\\RPi-Development\\EnvDataAnl\\OfficeENVData"
```

## 出力物
- `day_night_summary.csv` … デバイス・日付・日中/夜間ごとの統計（湿度/CO2）
- `weekday_summary.csv` … デバイス・曜日ごとの統計（湿度/CO2）
- `day_vs_night_means.png` … 日中/夜間平均比較プロット
- `weekday_profiles.png` … 曜日別平均プロファイル
- `timeseries_humidity_with_rolling.png` … 湿度の生波形＋30サンプル移動平均
- `timeseries_co2_with_rolling.png` … CO2 の生波形＋30サンプル移動平均
- `summary_office_v1.json` … サマリメタ情報（使用ファイル、列、統計など）

## 欠損・異常値の扱い
- タイムスタンプは数値（UNIX秒）もしくは文字列（ISO形式等）を自動判定して `datetime` に変換し、
  変換できない行は除外します。
- 数値列（humidity, co2, temperature, pressure, gas_resistance, absolute_humidity）は `to_numeric(errors='coerce')` により
  変換し、NaN の行は各集計の計算時に自動的に除外されます。

## 注意点
- グラフではデバイス別（P1/P2/P3）に色分けして重ね描きします。
- 日中/夜間の閾値（6:00/18:00）はコード内 `add_time_flags` で定義しています。必要に応じて調整してください。
- サンプル間隔が不定な場合でも 30サンプル移動平均は「サンプル数基準」です。時間基準にしたい場合はロジックを変更してください。

## トラブルシューティング
- 「ファイルが見つからない」警告が出る: 対象 CSV の存在とパス、拡張子、ファイル名のスペースを確認してください。
- タイムスタンプが 2000年や1970年付近になる: 入力の timestamp 列が数値（UNIX秒）か文字列かを確認。コードは自動判定ですが、
  桁や時区間違いがある場合は事前に整形してください。
- 図が真っ直ぐな線になる: すべて同一値（または欠損）になっていないか、列名のマッピングが正しいかを確認してください。

## ライセンス
本ディレクトリ配下のスクリプトは社内利用を想定しています。外部公開時は別途ご相談ください。

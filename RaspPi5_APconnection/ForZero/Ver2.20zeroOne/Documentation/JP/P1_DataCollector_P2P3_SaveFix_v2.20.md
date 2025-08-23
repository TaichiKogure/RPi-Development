# P1 データ収集: P2/P3 のCSV保存不具合 修正ノート（Ver2.20zeroOne）

本ドキュメントは、P4 のみ CSV に保存され、P2/P3 のデータが保存されない不具合に対する修正内容と確認手順をまとめたものです。

対象: G:\\RPi-Development\\RaspPi5_APconnection\\ForZero\\Ver2.20zeroOne\\p1_softwareNoWebMonitor

変更日: 2025-08-23

---

## 不具合の概要
- 現行のデータ収集モジュールが P4/P5/P6 のみを対象に初期化・保存しており、P2/P3 に対する CSV ファイルの初期化・保存処理が実行されていませんでした。
- API 側でも device_id の許容が P4/P5/P6 に限定されており、P2/P3 の取得が 400/404 になる問題がありました。

---

## 修正ポイント（コード）
対象ファイル:
- p1_softwareNoWebMonitor/data_collection/P1_data_collector_solo.py

主な修正内容:
1. Fallback 設定の拡張
   - FALLBACK_DEFAULT_CONFIG に以下を追加:
     - rawdata_p2_dir = "RawData_P2"
     - rawdata_p3_dir = "RawData_P3"
   - FALLBACK_MONITOR_CONFIG に P2 / P3 を追加。

2. ディレクトリ作成の拡張
   - __init__ 内のディレクトリ作成で、P2/P3 (および既存 P4/5/6) の RawData ディレクトリを自動作成するループに変更。

3. CSV 初期化・ローテーションの拡張
   - _init_csv_files() と _rotate_csv_files() の対象デバイスを ["P2","P3","P4","P5","P6"] に拡張。
   - device_id → RawData_XX のディレクトリ選択ロジックに P2/P3 を追加。

4. バリデーション・API 許容デバイスの拡張
   - _validate_data() の device_id 許容を ["P2","P3","P4","P5","P6"] に拡張。
   - API ルート（/api/data/device/<device_id>、/api/data/csv/<device_id>）の device_id 許容を同様に拡張。

5. ログ強化（早期検知）
   - _store_data() で保存成功時に、日付ファイルと固定ファイルの **実際の保存先パス** を 1 行で出力:
     - 例: `Saved P2 -> date_csv: /var/lib(FromThonny)/raspap_solo/data/RawData_P2/P2_2025-08-23.csv | fixed_csv: .../P2_fixed.csv`

---

## 修正後の動作仕様
- 受信 JSON に含まれる `device_id` が P2/P3/P4/P5/P6 のいずれかであれば、対応するディレクトリ配下に以下 2 種の CSV に追記されます。
  - 日付ファイル: RawData_XX/XX_YYYY-MM-DD.csv
  - 固定ファイル: RawData_XX/XX_fixed.csv
- 絶対湿度（absolute_humidity）は P1 側で温湿度から計算されて追記されます。
- API での最新値取得:
  - /api/data/latest … 全デバイスの最新値
  - /api/data/device/P2 など … 指定デバイスの最新値
  - /api/data/csv/P2 など … 当日 CSV のフルパスを返却

---

## 設定値の確認
- DEFAULT_CONFIG/FALLBACK_DEFAULT_CONFIG の主なキー
  - data_dir: `/var/lib(FromThonny)/raspap_solo/data`
  - rawdata_p2_dir: `RawData_P2`
  - rawdata_p3_dir: `RawData_P3`
  - rawdata_p4_dir: `RawData_P4`
  - （必要に応じて rawdata_p5_dir / rawdata_p6_dir）

注意:
- 実行時に refactored 版（p1_software_solo405）を import できる環境では、そちらが有効になります。今回の修正は **fallback 実装** 側です。NoWebMonitor 構成で本ファイルが直接起動される場合は本修正が有効になります。

---

## 動作確認チェックリスト
1. プロセス確認
   - 起動しているデータ収集スクリプトが `p1_softwareNoWebMonitor/data_collection/P1_data_collector_solo.py` であることを確認。
2. ディレクトリ確認
   - 以下が存在し、書き込み可能であること:
     - `/var/lib(FromThonny)/raspap_solo/data/RawData_P2`
     - `/var/lib(FromThonny)/raspap_solo/data/RawData_P3`
3. 受信ログ確認
   - 受信時に `Received data: {...}` が出力され、`Saved P2 -> date_csv: ... | fixed_csv: ...` の行が出ること。
4. CSV 内容確認
   - `RawData_P2/P2_YYYY-MM-DD.csv` と `P2_fixed.csv` に追記されていること。
   - 同様に P3 も保存されること。
5. API 確認（任意）
   - `http://<P1のIP>:5001/api/data/device/P2` が 200 で JSON を返すこと。

---

## 既知の注意点
- 本モジュールは Ver2.0 系（BME680 のみ）前提のため、CO2 列の扱いは無効化しています。CO2 センサ付構成では別系の実装を使用してください。
- `p1_software_solo405` が導入済み環境では、import の成功により refactored 実装にフォールフォワードすることがあります。その場合は refactored 側で P2/P3 の保存対応がなされているかを別途確認してください。

---

## 変更履歴
- 2025-08-23: 初版作成（P2/P3 保存対応、ログ強化、API 許容拡張）

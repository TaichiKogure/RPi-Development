# P1 BME680 リーダー 操作マニュアル（Ver2.11 / ZeroOne 系）

本ドキュメントは、P1（Raspberry Pi 5/Zero2W 等）に直結した BME680 センサーを定期的に読み取り、CSV へ保存するユーティリティ「p1_bme680_reader.py」の使い方をまとめた日本語マニュアルです。

対象ファイル:
- ForZero/Ver2.11zeroOne/p1_software_Zero/data_collection/p1_bme680_reader.py

データ保存先（デフォルト）:
- /var/lib(FromThonny)/raspap_solo/data/RawData_P1/P1_fixed.csv
- /var/lib(FromThonny)/raspap_solo/data/RawData_P1/P1_YYYY-MM-DD.csv

CSV ヘッダ:
- timestamp, device_id, temperature, humidity, pressure, gas_resistance, co2, absolute_humidity
  - 備考: P1 は co2 を空欄（空文字）で出力し、P2/P3 と同一スキーマ互換を維持します。

---

## 1. ハードウェア接続（I2C）
- BME680 VCC → 3.3V
- BME680 GND → GND
- BME680 SCL → GPIO3 (SCL, 物理ピン5)
- BME680 SDA → GPIO2 (SDA, 物理ピン3)
- I2C アドレスは 0x77 → 0x76 の順で自動検出します（どちらかで動作すればOK）。

## 2. OS 側の準備
1) I2C を有効化
- sudo raspi-config → Interface Options → I2C を有効 → 再起動

2) 推奨: 仮想環境
- python3 -m venv ~/envmonitor-venv
- source ~/envmonitor-venv/bin/activate

3) 必要パッケージのインストール
- pip install smbus2
- （Web 連携を使う場合）pip install flask pandas plotly requests

## 3. データディレクトリの作成
- 既定パス: /var/lib(FromThonny)/raspap_solo/data/RawData_P1
- 初回起動時に自動作成されます。権限で失敗する場合は事前に以下を実施：
  - sudo mkdir -p /var/lib(FromThonny)/raspap_solo/data/RawData_P1
  - sudo chown -R pi:pi /var/lib(FromThonny)/raspap_solo

## 4. 起動方法（手動）
- 仮想環境を有効化した状態で以下を実行：

```
cd ~/RaspPi5_APconnection/ForZero/Ver2.11zeroOne
python3 p1_software_Zero/data_collection/p1_bme680_reader.py --interval 10
```

オプション:
- --interval N  測定・保存間隔（秒）。既定 10 秒。
- --data-dir PATH  データ保存ベースディレクトリ（既定: /var/lib(FromThonny)/raspap_solo/data）

ログ例:
```
INFO - BME680 initialized at 0x77
INFO - Starting P1 BME680 reader loop
INFO - P1 wrote: T=27.12C RH=52.34% AH=12.45g/m3 P=1003.25hPa Gas=10523Ω
```

## 5. 取得データ項目
- temperature: 摂氏（°C）
- humidity: 相対湿度（%）
- pressure: 気圧（hPa）
- gas_resistance: ガス抵抗（Ω）
- absolute_humidity: 絶対湿度（g/m³）
  - 計算式（概略）: マグナス式による飽和水蒸気圧からの近似で算出（ソース内 calc_absolute_humidity 参照）

注意: 本リーダーは簡易換算（簡略ドライバ）を用いており、絶対精度が必要な用途では BME680 純正の校正・補正アルゴリズムを実装したフルドライバの導入を検討してください。

## 6. Web 表示との連携（任意）
- 本 CSV は P1 の Web インターフェース（/api/graphs）に取り込めるよう構成（RawData_P1 配下）になっています。
- 既存の Web/UI モジュールが P1 を含めて参照・描画する設定になっていれば、グラフに P1 系列（P1 温湿度/気圧/ガス/絶対湿度）を重ね描きできます。

## 7. トラブルシューティング
- 起動時に「smbus2 が無い」→ 仮想環境で `pip install smbus2` を実行
- 「BME680 not found」→ 配線/I2C 有効化/アドレス(0x76/0x77)を確認
- 「measurement timeout」→ I2C 結線や電源の安定性を確認
- CSV が生成されない → ディレクトリ権限と存在確認、`--data-dir` 指定の有無を確認

## 8. 自動起動（参考）
- システム起動時に常駐させたい場合は、systemd サービス化が有効です。
- 環境に応じて ExecStart・User・WorkingDirectory を調整してください。

例: /etc/systemd/system/p1-bme680-reader.service
```
[Unit]
Description=P1 BME680 Reader (Ver2.11)
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/RaspPi5_APconnection/ForZero/Ver2.11zeroOne
ExecStart=/home/pi/envmonitor-venv/bin/python3 p1_software_Zero/data_collection/p1_bme680_reader.py --interval 10
Restart=always

[Install]
WantedBy=multi-user.target
```
- 有効化手順:
```
sudo systemctl daemon-reload
sudo systemctl enable p1-bme680-reader
sudo systemctl start p1-bme680-reader
sudo systemctl status p1-bme680-reader
```

## 9. 既知の制限と今後の拡張
- 簡易ドライバのため、値は概算です（長期安定性/絶対精度は限定的）
- より正確な補正が必要な場合は、Boschのリファレンスドライバや実績ある実装を統合してください
- Web 側で P1 表示を有効化するには、/api/graphs が P1 を含むよう設定/実装されている必要があります

---
本マニュアルは Ver2.11 用です。システム全体のインストール方法は、同フォルダの「Installation_Guide_JP_v2.11.md」も参照してください。
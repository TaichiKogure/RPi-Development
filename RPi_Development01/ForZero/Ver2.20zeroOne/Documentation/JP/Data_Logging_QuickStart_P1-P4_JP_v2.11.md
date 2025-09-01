# P1–P4 センサー データロギング かんたん運用ガイド（Ver2.11 / ZeroOne 系）

本ドキュメントは、P1（Raspberry Pi 5/Zero2W）および P2〜P4（Raspberry Pi Pico 2W）を用いて環境データを記録・可視化するための「起動から確認まで」の作業手順をまとめた初心者向けガイドです。

関連ドキュメント（参考）：
- Installation_Guide_JP_v2.11.md（インストール）
- System_Architecture_JP_v2.11.md（システム構成）
- P1_BME680_Reader_Manual_JP_v2.11.md（P1内蔵BME680）

作業フォルダ（Windows 側の保存場所）：
- G:\RPi-Development\RaspPi5_APconnection\ForZero\Ver2.11zeroOne

データ保存先（P1 側、既定）：
- /var/lib(FromThonny)/raspap_solo/data/RawData_P1
- /var/lib(FromThonny)/raspap_solo/data/RawData_P2
- /var/lib(FromThonny)/raspap_solo/data/RawData_P3
- /var/lib(FromThonny)/raspap_solo/data/RawData_P4

CSV 例（共通ヘッダ）：
- timestamp, device_id, temperature, humidity, pressure, gas_resistance, co2, absolute_humidity
- 備考: P1 は co2 列を空欄（空文字）で出力しフォーマット互換を維持。

---

## 1. 準備（初回のみ）
1) OS 側設定（P1）
- I2C を有効化：`sudo raspi-config` → Interface Options → I2C → 有効 → 再起動

2) 仮想環境の作成（P1）
```
python3 -m venv ~/envmonitor-venv
source ~/envmonitor-venv/bin/activate
```

3) 必要パッケージのインストール（P1 仮想環境内）
```
pip install flask pandas plotly requests smbus2
```

4) データ保存ディレクトリの作成（必要に応じて）
```
sudo mkdir -p /var/lib(FromThonny)/raspap_solo/data/RawData_{P1,P2,P3,P4}
sudo chown -R pi:pi /var/lib(FromThonny)/raspap_solo
```

---

## 2. ハードウェア接続の要点
- P1（Raspberry Pi 5/Zero2W）に BME680 を I2C 接続：
  - VCC→3.3V, GND→GND, SCL→GPIO3(ピン5), SDA→GPIO2(ピン3)
  - I2C アドレスは 0x77 → 0x76 の順で自動検出
- P2〜P4（Raspberry Pi Pico 2W）には各 BME680（および必要に応じ CO2 センサ）を既存ガイドに従って配線

---

## 3. 起動手順（毎回）
以下は最小構成の手動起動例です。自動起動（systemd）は 7 章を参照。

1) 仮想環境を有効化（P1）
```
source ~/envmonitor-venv/bin/activate
```

2) P1 内蔵 BME680 のロガーを起動（任意・併用推奨）
```
cd ~/RaspPi5_APconnection/ForZero/Ver2.11zeroOne
python3 p1_software_Zero/data_collection/p1_bme680_reader.py --interval 10
```
- 成功ログ例：
```
INFO - BME680 initialized at 0x77
INFO - Starting P1 BME680 reader loop
INFO - P1 wrote: T=27.12C RH=52.34% AH=12.45g/m3 P=1003.25hPa Gas=10523Ω
```

3) P2〜P4 センサノードの起動
- Pico 2W 側のプログラムを起動／自動起動に設定（各ノードの既存手順に従う）
- P1 の AP（アクセスポイント）へ接続され、データが TCP/HTTP 等で P1 へ送達される構成を前提

4) P1 のデータ収集（既存の data_collector が起動済みであること）
- 本 Ver 系では、データ収集の詳細は既存の起動スクリプト／サービスに準拠してください

5) Web インターフェース（表示）
- 既存の Web UI（Flask）を起動済みにする
- 同一ネットワークからブラウザで P1 の IP（例： http://192.168.0.1 や P1 のホスト IP）へアクセス
- /api/graphs またはダッシュボード画面で P1〜P4 の系列が見えることを確認

---

## 4. 動作確認（チェックリスト）
- データファイル生成の確認：
  - P1: /var/lib(FromThonny)/raspap_solo/data/RawData_P1/P1_fixed.csv
  - P2: /var/lib(FromThonny)/raspap_solo/data/RawData_P2/P2_fixed.csv
  - P3: /var/lib(FromThonny)/raspap_solo/data/RawData_P3/P3_fixed.csv
  - P4: /var/lib(FromThonny)/raspap_solo/data/RawData_P4/P4_fixed.csv
- CSV の timestamp が現在時刻に更新され続ける
- Web UI で最新値／グラフが表示される
- 接続モニター（あれば）：P2〜P4 が online であること

---

## 5. データ保存先一覧
- 固定ファイル（最新を上書き追記）：
  - RawData_P1/P1_fixed.csv
  - RawData_P2/P2_fixed.csv
  - RawData_P3/P3_fixed.csv
  - RawData_P4/P4_fixed.csv
- 日別ローテーション：
  - RawData_Pn/Pn_YYYY-MM-DD.csv（n=1..4）

---

## 6. よくある質問／トラブル対処
- BME680 が初期化失敗：配線・I2C 有効化・アドレス（0x76/0x77）を再確認
- CSV が作られない：/var/lib(FromThonny)/raspap_solo/data 配下の権限とフォルダの有無
- Web に P1〜P4 が出ない：/api/graphs のレスポンス内容、固定 CSV の更新確認
- 値が異常：電源安定性、センサー初期化順、簡易ドライバの限界（高精度が必要な場合はフルドライバ導入）

---

## 7. 自動起動（参考例）
P1 内蔵 BME680 ロガー（systemd サービス例）
```
# /etc/systemd/system/p1-bme680-reader.service
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
有効化：
```
sudo systemctl daemon-reload
sudo systemctl enable p1-bme680-reader
sudo systemctl start p1-bme680-reader
sudo systemctl status p1-bme680-reader
```

その他（data_collector / web_interface / connection_monitor）も同様にサービス化し、依存関係（After= / Wants=）を適宜設定してください。

---

## 8. 付録：チェックコマンド例（P1）
- プロセス稼働確認：`ps aux | grep python`
- ポート確認（Flask 等）：`ss -tunlp | grep :80` など
- ログ参照：各モジュールのログファイル／`journalctl -u <service>`

以上。
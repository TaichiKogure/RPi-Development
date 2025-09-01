# Raspberry Pi Zero 2W ポータブル環境モニタ Ver.1 使い方ガイド

本書は PortableZero2Wmodule Ver.1 のインストールから起動、自動起動設定、CSVの仕様、トラブルシュートまでをまとめたガイドです。

対応ハード:
- Raspberry Pi Zero 2W
- BME680（I2C）
- MH-Z19 / B / C（UART）

ドライバ前提:
- BME680 は G:\\RPi-Development\\OK2bme\\bme680.py（OK2bme ドライバ）を使用します。Pi 側に同等の `bme680.py` を配置してください。

---
## 1. ディレクトリ構成（抜粋）
```
PortableZero2Wmodule/
├── portable_zero2w_main_v1.py      # 実行エントリ
├── sensors/
│   ├── bme680_reader_v1.py         # BME680 リーダ
│   └── mhz19_reader_v1.py          # MH-Z19 リーダ
├── utils/
│   ├── calculations_v1.py          # 絶対湿度/不快指数/汚染指数
│   └── csv_logger_v1.py            # CSVロガー（日次/トータル）
├── requirements.txt                # 追加Pythonパッケージ
├── README_接続手順_v1_JP.md       # 配線ガイド
└── README_使い方_v1_JP.md          # 本書
```

---
## 2. 事前準備（Raspberry Pi 側）
1) I2C/UART を有効化（詳細は「README_接続手順_v1_JP.md」参照）
2) BME680 ドライバを配置:
   - 例: `/home/pi/OK2bme/bme680.py`
   - 環境変数 `OK2BME_PATH=/home/pi/OK2bme` を設定してもOK
3) 追加パッケージ（pyserial）をインストール（任意で仮想環境推奨）
   ```bash
   # 必要に応じて
   sudo apt-get update
   sudo apt-get install -y python3-venv

   # 仮想環境（推奨）
   cd ~/PortableZero2Wmodule
   python3 -m venv envmonitor-venv
   source envmonitor-venv/bin/activate
   pip install -r requirements.txt
   ```

---
## 3. 実行方法（手動）
```bash
cd ~/PortableZero2Wmodule
# 仮想環境を使用する場合
source envmonitor-venv/bin/activate

# 例: 10秒間隔、BME680アドレス0x77、データ出力 /var/lib/envmon/data、MH-Z19ウォームアップ30秒
sudo mkdir -p /var/lib/envmon/data
sudo chown -R $USER:$USER /var/lib/envmon
python3 portable_zero2w_main_v1.py \
  --interval 10 \
  --i2c-addr 0x77 \
  --data-dir /var/lib/envmon/data \
  --warmup 30 \
  --print-every 1
```
起動後、端末には最新の測定値や内部状態が 10 秒毎に表示されます。

オプション一覧:
- `--interval <sec>` 測定間隔（秒）
- `--i2c-addr 0x76|0x77` BME680 の I2C アドレス
- `--data-dir <path>` CSV 出力ディレクトリ（`daily/` と `total.csv` が作成されます）
- `--warmup <sec>` MH-Z19 のウォームアップ秒数
- `--print-every <N>` N サンプル毎にコンソール表示

---
## 4. CSV 出力仕様
出力先:
- 日次: `<data-dir>/daily/YYYY-MM-DD.csv`
- 積算: `<data-dir>/total.csv`（サイズ閾値超過時、`total_YYYYmmdd_HHMMSS.csv` にローテーション）

列（ヘッダ）:
- `timestamp_iso` ISO日時（秒精度）
- `timestamp_epoch` UNIX秒
- `temperature_c` 気温[℃]
- `humidity_percent` 相対湿度[%]
- `absolute_humidity_gm3` 絶対湿度[g/m^3]
- `pressure_hpa` 気圧[hPa]
- `gas_resistance_ohm` ガス抵抗[Ω]
- `pollution_index` ガス抵抗由来の汚染指数[0–100]（大きいほど汚染）
- `pollution_level` 汚染レベル（very_good/good/moderate/poor/very_poor）
- `co2_ppm` CO2濃度[ppm]
- `discomfort_index` 不快指数（Thom式）
- `bme680_ok` BME680 読み取り状態
- `mhz19_ok` MH-Z19 読み取り状態

---
## 5. 内部計算の概要
- 絶対湿度: Magnus式＋気体定数近似で算出
- 不快指数（Thom）: `DI = T - 0.55*(1 - RH/100)*(T - 14.5)`
- 汚染指数: BME680 のガス抵抗を 5kΩ（悪）〜200kΩ（良）に正規化した簡易指標

---
## 6. 自動回復と冗長性
- BME680/MH-Z19 それぞれ別個に再初期化・再接続を実施
- 失敗時は指数バックオフ（最大60秒）でリトライ
- MH-Z19 はシリアルポートを毎回監視し、異常時はクローズ→再オープン
- メモリ節約: 測定→計算→CSV 追記のみ。大きなバッファは保持しません

---
## 7. 自動起動（systemd）
`/etc/systemd/system/portable-zero2w.service` を作成:
```ini
[Unit]
Description=Portable Zero2W Environmental Monitor Ver.1
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
# 仮想環境を使用する場合
ExecStart=/bin/bash -lc 'cd /home/pi/PortableZero2Wmodule && \
  source envmonitor-venv/bin/activate && \
  python3 portable_zero2w_main_v1.py --interval 10 --i2c-addr 0x77 --data-dir /var/lib/envmon/data --warmup 30 --print-every 1'
Restart=always
RestartSec=5
User=pi
WorkingDirectory=/home/pi/PortableZero2Wmodule

[Install]
WantedBy=multi-user.target
```
有効化:
```bash
sudo systemctl daemon-reload
sudo systemctl enable portable-zero2w.service
sudo systemctl start portable-zero2w.service
sudo systemctl status portable-zero2w.service -n 50
```
ログ確認:
```bash
journalctl -u portable-zero2w.service -f
```

---
## 8. トラブルシュート
- BME680 ドライバが見つからない:
  - `/home/pi/OK2bme/bme680.py` を配置し、`OK2BME_PATH=/home/pi/OK2bme` を設定
- I2C アドレス不一致:
  - `sudo apt-get install -y i2c-tools && i2cdetect -y 1`
  - アドレスに合わせ `--i2c-addr` を指定（0x76/0x77）
- UART 読み取り失敗/ゼロ値:
  - `enable_uart=1`、シリアルコンソール無効を確認
  - `/dev/serial0` が存在するか確認
  - MH-Z19 のウォームアップを十分に確保（`--warmup` で調整）
- 権限エラー:
  - データディレクトリの権限をユーザに付与
  - シリアルアクセスには `dialout` グループが必要なことがあります
- CSV が更新されない:
  - サービス稼働状況（systemctl status）と journal を確認
  - 同時に同じポートを掴む別プロセスが無いか確認

---
## 9. 安全上の注意
- MH-Z19 の電源は 5V、信号は 3.3V 互換が一般的。必ず仕様を確認してください
- 配線のショートや極性間違いに注意

---
## 10. バージョン情報
- PortableZero2Wmodule Ver.1（このディレクトリのファイル末尾に _v1 名称を付与）
- BME680 ドライバは OK2bme ベース

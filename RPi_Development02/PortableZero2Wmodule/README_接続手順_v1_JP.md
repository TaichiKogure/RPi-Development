# Raspberry Pi Zero 2W ポータブル環境モニタ Ver.1 配線ガイド

本書は、Raspberry Pi Zero 2W に BME680（温湿度・気圧・ガス）と MH-Z19（CO2）を接続するための配線手順です。

対応センサー:
- BME680（I2C）
- MH-Z19 / MH-Z19B / MH-Z19C（UART）

注意: 本システムの BME680 ドライバは G:\\RPi-Development\\OK2bme\\bme680.py を使用します。Pi 本体に同等のファイルを配置して読み込めるようにしてください（例: /home/pi/OK2bme/bme680.py）。

---
## 1. Raspberry Pi 設定（I2C/UART を有効化）
1. ターミナルで設定ツールを開く:
   ```bash
   sudo raspi-config
   ```
2. Interface Options から以下を有効化:
   - I2C: Enabled
   - Serial Port: “ログインシェルをシリアル経由で使用しますか?” → いいえ
     “ハードウェアとしてシリアルポートを有効化しますか?” → はい
3. /boot/config.txt に以下が含まれることを確認:
   ```
   enable_uart=1
   ```
4. 再起動:
   ```bash
   sudo reboot
   ```

---
## 2. GPIO ピン（Zero 2W）
- 3.3V: 物理ピン 1
- 5V: 物理ピン 2 または 4
- GND: 物理ピン 6 ほか
- I2C1 SDA: GPIO2（物理ピン 3）
- I2C1 SCL: GPIO3（物理ピン 5）
- UART0 TXD: GPIO14（物理ピン 8）
- UART0 RXD: GPIO15（物理ピン 10）

---
## 3. BME680（I2C）配線
- BME680 VCC → Pi 3.3V（ピン1）
- BME680 GND → Pi GND（ピン6）
- BME680 SDA → Pi GPIO2 / SDA1（ピン3）
- BME680 SCL → Pi GPIO3 / SCL1（ピン5）

アドレスについて:
- 0x76 または 0x77 の場合があります（基板のジャンパ設定やメーカーによる）。
- 既定は 0x77。違う場合は起動オプション `--i2c-addr 0x76` を指定してください。

---
## 4. MH-Z19（UART）配線
- MH-Z19 VCC → Pi 5V（ピン2 または 4）
- MH-Z19 GND → Pi GND（ピン6）
- MH-Z19 TX → Pi RXD0（GPIO15 / ピン10）
- MH-Z19 RX → Pi TXD0（GPIO14 / ピン8）

メモ:
- MH-Z19 の信号レベルは多くのモデルで 3.3V 互換です（電源は 5V）。不明な場合はレベルシフタを用意してください。
- センサーの向きや通気性に注意し、通風が確保されるよう設置してください。

---
## 5. 動作確認
1. I2C デバイス確認:
   ```bash
   sudo apt-get install -y i2c-tools
   i2cdetect -y 1
   # 0x76 または 0x77 が表示されればOK
   ```
2. UART 確認:
   - /dev/serial0 が存在することを確認
   - CO2 取得はプログラムから実施（本プロジェクトのメインで取得します）

---
## 6. 既知の注意点
- BME680 ドライバが見つからない場合、本プロジェクトはエラーを表示し自動的に再試行します。Pi 側に `OK2bme/bme680.py` を配置し、環境変数 `OK2BME_PATH` で指定可能です。
- MH-Z19 は起動後のウォームアップが必要です（デフォルト 30 秒）。
- シリアル競合（他プロセスが /dev/serial0 を掴むなど）があると CO2 読み取りに失敗します。サービスの多重起動に注意してください。

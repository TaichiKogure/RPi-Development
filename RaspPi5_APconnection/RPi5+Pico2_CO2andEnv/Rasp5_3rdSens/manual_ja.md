# Raspberry Pi 5 環境センサーシステム マニュアル

## 概要

このシステムは、Raspberry Pi 5を使用して、BME680環境センサーとMH-Z19 CO2センサーからデータを収集し、CSVファイルに記録するものです。温度、湿度、気圧、ガス抵抗、CO2濃度、絶対湿度を30秒ごとに測定し、日付ごとのCSVファイルと統合CSVファイルに保存します。

## 必要なハードウェア

- Raspberry Pi 5
- BME680センサー（温度、湿度、気圧、ガス抵抗測定用）
- MH-Z19センサー（CO2濃度測定用）
- ジャンパーワイヤー
- 電源アダプター（Raspberry Pi 5用）

## 必要なソフトウェア

- Raspberry Pi OS (Bullseye以降)
- Python 3.7以降
- 必要なPythonライブラリ:
  - bme680
  - smbus2
  - pyserial

## セットアップ手順

### 1. ハードウェアの接続

センサーをRaspberry Pi 5に接続します。詳細な接続方法は `pin_assignments.md` ファイルを参照してください。

### 2. Raspberry Pi OSのセットアップ

1. Raspberry Pi OSをインストールし、基本的なセットアップを完了させてください。
2. I2CとUARTを有効にします:
   ```
   sudo raspi-config
   ```
   - 「Interface Options」を選択
   - 「I2C」を選択して有効にする
   - 「Serial Port」を選択し、シリアルログインシェルを無効に、シリアルハードウェアを有効にする

### 3. 必要なライブラリのインストール

ターミナルで以下のコマンドを実行します:

```bash
sudo apt-get update
sudo apt-get install -y python3-pip i2c-tools
sudo pip3 install bme680 smbus2 pyserial
```

### 4. I2Cデバイスの確認

BME680センサーが正しく接続されているか確認します:

```bash
sudo i2cdetect -y 1
```

出力に「77」（または「76」）が表示されていれば、BME680が検出されています。

### 5. データディレクトリの作成

データを保存するディレクトリを作成します:

```bash
sudo mkdir -p /var/lib(FromThonny)/raspap_solo/data/RawData_P1
sudo chmod 777 /var/lib(FromThonny)/raspap_solo/data/RawData_P1
```

### 6. プログラムのダウンロードと実行

1. プログラムファイル（P1_Sensor.py）をRaspberry Piにコピーします。
2. 実行権限を付与します:
   ```bash
   chmod +x P1_Sensor.py
   ```
3. プログラムを実行します:
   ```bash
   python3 P1_Sensor.py
   ```

## 自動起動の設定

システム起動時にプログラムを自動的に実行するように設定できます:

1. systemdサービスファイルを作成します:
   ```bash
   sudo nano /etc/systemd/system/p1-sensor.service
   ```

2. 以下の内容を入力します:
   ```
   [Unit]
   Description=P1 Environmental Sensor Service
   After=network.target

   [Service]
   ExecStart=/usr/bin/python3 /home/pi/P1_Sensor.py
   WorkingDirectory=/home/pi
   StandardOutput=inherit
   StandardError=inherit
   Restart=always
   User=pi

   [Install]
   WantedBy=multi-user.target
   ```

3. サービスを有効にして起動します:
   ```bash
   sudo systemctl enable p1-sensor.service
   sudo systemctl start p1-sensor.service
   ```

4. サービスのステータスを確認します:
   ```bash
   sudo systemctl status p1-sensor.service
   ```

## データの確認

データは以下の場所に保存されます:

- 日付ごとのCSVファイル: `/var/lib/raspap_solo/data/RawData_P1/P1_YYYY-MM-DD.csv`
- 統合CSVファイル: `/var/lib/raspap_solo/data/RawData_P1/P1_fixed.csv`

CSVファイルの内容を確認するには:

```bash
tail -n 10 /var/lib(FromThonny)/raspap_solo/data/RawData_P1/P1_fixed.csv
```

## トラブルシューティング

### センサーが検出されない場合

1. 配線を確認してください。
2. I2Cが有効になっているか確認してください:
   ```bash
   lsmod | grep i2c_
   ```
3. BME680のI2Cアドレスを確認してください（0x76または0x77）。
4. プログラム内のI2Cアドレスを必要に応じて変更してください。

### MH-Z19センサーが動作しない場合

1. UARTが有効になっているか確認してください。
2. UARTデバイスパスが正しいか確認してください:
   ```bash
   ls -l /dev/ttyAMA0
   ```
3. 必要に応じて、プログラム内のUARTデバイスパスを変更してください。

### プログラムがエラーで終了する場合

1. ログファイル（p1_sensor.log）を確認してください:
   ```bash
   tail -n 50 p1_sensor.log
   ```
2. 必要なライブラリがすべてインストールされているか確認してください。

## データ形式

CSVファイルには以下の列が含まれます:

- timestamp: 測定時刻（YYYY-MM-DD HH:MM:SS形式）
- device_id: デバイスID（常に「P1」）
- temperature: 温度（°C）
- humidity: 相対湿度（%）
- pressure: 気圧（hPa）
- gas_resistance: ガス抵抗（Ω）
- co2: CO2濃度（ppm）
- absolute_humidity: 絶対湿度（g/m³）

## プログラムの停止

プログラムを停止するには、Ctrl+Cを押すか、サービスとして実行している場合は以下のコマンドを使用します:

```bash
sudo systemctl stop p1-sensor.service
```

## 参考情報

- BME680データシート: https://www.bosch-sensortec.com/products/environmental-sensors/gas-sensors/bme680/
- MH-Z19データシート: https://www.winsen-sensor.com/d/files/infrared-gas-sensor/mh-z19b-co2-ver1_0.pdf
- Raspberry Pi GPIO: https://www.raspberrypi.org/documentation/computers/os.html#gpio-and-the-40-pin-header
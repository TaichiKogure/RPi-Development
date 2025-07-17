# P1_Sensor V1 - 取扱説明書

## 概要

P1_Sensor V1は、Raspberry Pi 5に接続されたMH-Z19 CO2センサーとBME680環境センサーからデータを収集し、CSVファイルに記録するシステムです。このシステムは、室内の環境データ（温度、湿度、気圧、ガス抵抗、CO2濃度）を30秒ごとに測定し、日付ごとのCSVファイルと統合CSVファイルに保存します。

## 必要なもの

- Raspberry Pi 5
- BME680センサー
- MH-Z19 CO2センサー
- 接続用ケーブル
- microSDカード（Raspberry Pi OS搭載）
- 電源アダプター

## インストール手順

### 1. ハードウェアの接続

センサーをRaspberry Pi 5に接続します。詳細な接続方法は `pin_assignments.md` ファイルを参照してください。

#### BME680センサーの接続

| BME680ピン | Raspberry Pi 5ピン | 説明 |
|------------|-------------------|-------------|
| VCC        | 3.3V (Pin 1)      | 電源 |
| GND        | GND (Pin 6)       | グラウンド |
| SCL        | SCL (GPIO 3, Pin 5) | I2Cクロック |
| SDA        | SDA (GPIO 2, Pin 3) | I2Cデータ |

#### MH-Z19 CO2センサーの接続

| MH-Z19ピン | Raspberry Pi 5ピン | 説明 |
|------------|-------------------|-------------|
| VCC (赤)   | 5V (Pin 2または4) | 電源 |
| GND (黒)   | GND (Pin 6)       | グラウンド |
| TX (緑)    | GPIO 14 (UART0 RX, Pin 8) | UARTセンサーからPiへの送信 |
| RX (青)    | GPIO 15 (UART0 TX, Pin 10) | UARTセンサーへのPiからの受信 |

### 2. ソフトウェアのインストール

1. Raspberry Pi OSがインストールされたRaspberry Pi 5を起動します。

2. 必要なパッケージをインストールします：

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3-pip python3-smbus i2c-tools
```

3. 必要なPythonライブラリをインストールします：

```bash
pip3 install pyserial smbus2
```

4. I2CとUARTを有効にします：

```bash
sudo raspi-config
```

- 「Interface Options」を選択
- 「I2C」を選択し、有効にする
- 「Serial Port」を選択
- シリアルログインシェルを無効にする
- シリアルハードウェアを有効にする

5. Raspberry Piを再起動します：

```bash
sudo reboot
```

6. I2Cデバイスが認識されていることを確認します：

```bash
sudo i2cdetect -y 1
```

BME680センサーのアドレス（通常は0x76または0x77）が表示されることを確認します。

7. データ保存用のディレクトリを作成します：

```bash
sudo mkdir -p /var/lib/raspap_solo/data/RawData_P1
sudo chmod 777 /var/lib/raspap_solo/data/RawData_P1
```

8. P1_Sensor.pyファイルをRaspberry Piにコピーします。

### 3. プログラムの実行

1. P1_Sensor.pyを実行します：

```bash
python3 P1_Sensor.py
```

2. プログラムが正常に起動すると、以下のようなログが表示されます：

```
2023-07-01 12:00:00,000 - INFO - Starting P1_Sensor V1
2023-07-01 12:00:00,100 - INFO - Initializing BME680 sensor...
2023-07-01 12:00:00,200 - INFO - BME680 found with correct chip ID
2023-07-01 12:00:00,300 - INFO - BME680 calibration data read successfully
2023-07-01 12:00:00,400 - INFO - BME680 initialization complete
2023-07-01 12:00:00,500 - INFO - Initializing MH-Z19 sensor...
2023-07-01 12:00:00,600 - INFO - MH-Z19 initialized on /dev/ttyAMA0
2023-07-01 12:00:00,700 - INFO - Warming up for 30 seconds...
...
2023-07-01 12:00:30,700 - INFO - MH-Z19 warmup complete
2023-07-01 12:00:30,800 - INFO - Initializing data logger...
2023-07-01 12:00:30,900 - INFO - Data will be logged to: /var/lib/raspap_solo/data/RawData_P1
2023-07-01 12:00:31,000 - INFO - Consolidated data will be logged to: /var/lib/raspap_solo/data/RawData_P1/P1_fixed.csv
2023-07-01 12:00:31,100 - INFO - Starting main loop with 30 second interval...
2023-07-01 12:00:31,200 - INFO - Temperature: 25.0°C, Humidity: 50.0%, Pressure: 1013.25hPa, Gas: 10000Ω, CO2: 450 ppm
```

3. プログラムを終了するには、`Ctrl+C`を押します。

### 4. 自動起動の設定

システム起動時に自動的にプログラムを実行するように設定するには：

1. サービスファイルを作成します：

```bash
sudo nano /etc/systemd/system/p1-sensor.service
```

2. 以下の内容を入力します：

```
[Unit]
Description=P1 Sensor Data Collection Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 /path/to/P1_Sensor.py
WorkingDirectory=/path/to
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

3. サービスを有効にして起動します：

```bash
sudo systemctl enable p1-sensor.service
sudo systemctl start p1-sensor.service
```

4. サービスのステータスを確認します：

```bash
sudo systemctl status p1-sensor.service
```

## データの確認

データは以下の場所に保存されます：

- 日付ごとのCSVファイル: `/var/lib/raspap_solo/data/RawData_P1/P1_YYYY-MM-DD.csv`
- 統合CSVファイル: `/var/lib/raspap_solo/data/RawData_P1/P1_fixed.csv`

CSVファイルの内容を確認するには：

```bash
head -n 10 /var/lib/raspap_solo/data/RawData_P1/P1_fixed.csv
```

## トラブルシューティング

### センサーが認識されない場合

1. I2C接続を確認します：

```bash
sudo i2cdetect -y 1
```

2. ケーブル接続を確認します。

3. ログファイルを確認します：

```bash
cat p1_sensor.log
```

### データが記録されない場合

1. データディレクトリのパーミッションを確認します：

```bash
ls -la /var/lib/raspap_solo/data/RawData_P1
```

2. ディレクトリが存在しない場合は作成します：

```bash
sudo mkdir -p /var/lib/raspap_solo/data/RawData_P1
sudo chmod 777 /var/lib/raspap_solo/data/RawData_P1
```

### MH-Z19センサーのエラー

1. UARTが有効になっているか確認します：

```bash
sudo raspi-config
```

2. ケーブル接続を確認します。特にTXとRXが正しく接続されているか確認します。

3. 別のUARTデバイスパスを試してみてください（例：`/dev/ttyS0`）。

### BME680センサーのエラー

1. I2Cが有効になっているか確認します：

```bash
sudo raspi-config
```

2. ケーブル接続を確認します。

3. 別のI2Cアドレスを試してみてください（0x76または0x77）。

## メンテナンス

### ログファイルの管理

ログファイルは時間とともに大きくなる可能性があります。定期的にログファイルをローテーションするには：

```bash
sudo nano /etc/logrotate.d/p1-sensor
```

以下の内容を入力します：

```
/path/to/p1_sensor.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 pi pi
}
```

### CSVファイルの管理

CSVファイルも時間とともに大きくなります。古いデータを定期的にバックアップし、削除することをお勧めします：

```bash
# バックアップ
tar -czf /home/pi/p1_sensor_data_backup_$(date +%Y%m%d).tar.gz /var/lib/raspap_solo/data/RawData_P1

# 30日以上前のCSVファイルを削除
find /var/lib/raspap_solo/data/RawData_P1 -name "P1_*.csv" -type f -mtime +30 -delete
```

## 技術仕様

- BME680センサー：
  - 温度測定範囲：-40°C～85°C
  - 湿度測定範囲：0～100% RH
  - 気圧測定範囲：300～1100 hPa
  - ガス抵抗測定：数kΩ～数MΩ

- MH-Z19 CO2センサー：
  - CO2測定範囲：400～5000 ppm
  - 精度：±50 ppm + 5%
  - 応答時間：<60秒
  - ウォームアップ時間：3分（完全な精度には24時間）

- データ収集間隔：30秒

## 注意事項

1. センサーの精度は環境条件によって影響を受ける場合があります。
2. MH-Z19センサーは定期的なキャリブレーションが必要な場合があります。
3. システムを長時間稼働させる場合は、Raspberry Piの冷却を考慮してください。
4. データディレクトリが一杯になると、新しいデータの記録ができなくなる可能性があります。定期的にディスク使用量を確認してください。

## サポート

問題が発生した場合は、以下の情報を含めてサポートにお問い合わせください：

1. ログファイルの内容
2. 使用しているRaspberry Piのモデルとバージョン
3. 接続しているセンサーの詳細
4. 発生している問題の詳細な説明

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。
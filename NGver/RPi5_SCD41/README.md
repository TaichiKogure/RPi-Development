# Raspberry Pi 5 SCD41 環境データ測定システム

## 概要
このプロジェクトは、Raspberry Pi 5とSCD41センサーを使用して、CO2濃度、温度、湿度を測定し、データを収集・可視化するシステムを実装しています。Ver4.66Debugのデータ形式に準拠したCSVファイルにデータを出力し、簡易的なグラフビューアでデータを可視化します。

## 機能
- SCD41センサーからのCO2濃度、温度、湿度データの収集
- 温度と湿度から絶対湿度の計算
- Ver4.66Debugのデータ形式に準拠したCSVファイル出力
  - 未取得データ（気圧、ガス抵抗）には固定値（6000）を使用
- 簡易的なグラフビューアによるデータの可視化
  - CO2濃度、温度、湿度、絶対湿度のグラフ表示
  - 表示期間の選択（1日、3日、7日、30日）
  - 自動更新機能

## システム構成
```
RPi5_SCD41/
├── sensor_drivers/       # センサードライバ
│   └── scd41.py          # SCD41センサードライバ
├── data_collection/      # データ収集
│   └── scd41_data_collector.py  # データ収集スクリプト
├── visualization/        # データ可視化
│   └── scd41_graph_viewer.py    # グラフビューア
├── main.py               # システム全体の起動スクリプト
├── README.md             # 説明書
└── data/                 # データ保存ディレクトリ（自動作成）
```

## 必要なハードウェア
- Raspberry Pi 5
- SCD41 CO2センサー

## 接続方法
SCD41センサーをRaspberry Pi 5に以下のように接続します：
- VCC → 3.3V
- GND → GND
- SCL → SCL (GPIO 3)
- SDA → SDA (GPIO 2)

## インストール方法

### 1. 必要なパッケージのインストール
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-smbus i2c-tools
pip3 install pandas matplotlib
```

### 2. I2Cの有効化
```bash
sudo raspi-config
```
- 「Interface Options」を選択
- 「I2C」を選択
- 「Yes」を選択して有効化
- 「Finish」を選択して終了

### 3. I2Cデバイスの確認
```bash
sudo i2cdetect -y 1
```
SCD41のアドレス（0x62）が表示されることを確認します。

### 4. プロジェクトのクローン
```bash
git clone https://github.com/yourusername/RPi5_SCD41.git
cd RPi5_SCD41
```

## 使用方法

### システム全体の起動（推奨）
```bash
cd RPi5_SCD41
python3 main.py --data-dir data --interval 30 --days 1 --refresh-interval 60
```

オプション：
- `--data-dir`: データを保存するディレクトリ（デフォルト: data）
- `--interval`: データ収集間隔（秒）（デフォルト: 30）
- `--days`: グラフ表示日数（デフォルト: 1）
- `--device-id`: デバイスID（デフォルト: SCD41）
- `--refresh-interval`: グラフの更新間隔（秒）（デフォルト: 60）

このコマンドは、データ収集プロセスを開始し、グラフビューアを起動します。グラフビューアを閉じると、データ収集プロセスも自動的に停止します。

### データ収集のみ開始（個別実行）
```bash
cd RPi5_SCD41
python3 data_collection/scd41_data_collector.py --data-dir data --interval 30
```

オプション：
- `--data-dir`: データを保存するディレクトリ（デフォルト: data）
- `--interval`: データ収集間隔（秒）（デフォルト: 30）
- `--device-id`: デバイスID（デフォルト: SCD41）

### グラフビューアのみ起動（個別実行）
```bash
cd RPi5_SCD41
python3 visualization/scd41_graph_viewer.py --data-dir data --days 1 --refresh-interval 60
```

オプション：
- `--data-dir`: データが保存されているディレクトリ（デフォルト: data）
- `--days`: 表示する日数（デフォルト: 1）
- `--device-id`: デバイスID（デフォルト: SCD41）
- `--refresh-interval`: グラフの更新間隔（秒）（デフォルト: 60）

## データ形式
データは以下の形式でCSVファイルに保存されます：

```
timestamp,device_id,temperature,humidity,pressure,gas_resistance,co2,absolute_humidity
2023-07-12 12:34:56,SCD41,25.3,45.2,6000,6000,850,10.23
```

- `timestamp`: データ収集時のタイムスタンプ（YYYY-MM-DD HH:MM:SS）
- `device_id`: デバイスID（SCD41）
- `temperature`: 温度（°C）
- `humidity`: 相対湿度（%）
- `pressure`: 気圧（固定値: 6000）
- `gas_resistance`: ガス抵抗（固定値: 6000）
- `co2`: CO2濃度（ppm）
- `absolute_humidity`: 絶対湿度（g/m³）

## 自動起動の設定
システム起動時にデータ収集を自動的に開始するには、以下の手順でサービスを設定します：

### 1. サービスファイルの作成
```bash
sudo nano /etc/systemd/system/scd41-system.service
```

以下の内容を記述：
```
[Unit]
Description=SCD41 Environmental Data System
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/RPi5_SCD41/data_collection/scd41_data_collector.py --data-dir /home/pi/RPi5_SCD41/data --interval 30
WorkingDirectory=/home/pi/RPi5_SCD41
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

注意: グラフビューアを自動起動する場合は、ディスプレイ環境が必要です。データ収集のみを自動起動する場合は上記の設定で問題ありません。

グラフビューアも含めて自動起動する場合は、以下のようにExecStartを変更します：

```
ExecStart=/usr/bin/python3 /home/pi/RPi5_SCD41/main.py --data-dir /home/pi/RPi5_SCD41/data --interval 30 --days 1 --refresh-interval 60
```

### 2. サービスの有効化と開始
```bash
sudo systemctl enable scd41-system.service
sudo systemctl start scd41-system.service
```

### 3. サービスの状態確認
```bash
sudo systemctl status scd41-system.service
```

## トラブルシューティング

### センサーが認識されない場合
- I2Cが有効になっているか確認
- 配線が正しいか確認
- `sudo i2cdetect -y 1` でSCD41のアドレス（0x62）が表示されるか確認

### データが収集されない場合
- ログファイル（scd41_data_collector.log）を確認
- 権限の問題がないか確認
- データディレクトリが存在し、書き込み可能か確認

### グラフが表示されない場合
- データファイルが存在するか確認
- ログファイル（scd41_graph_viewer.log）を確認
- 必要なパッケージ（pandas, matplotlib）がインストールされているか確認

## ライセンス
このプロジェクトはMITライセンスの下で公開されています。詳細はLICENSEファイルを参照してください。

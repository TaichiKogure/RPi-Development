# Raspberry Pi 5 環境データ測定システム ソロバージョン インストールガイド

## バージョン情報
- ドキュメントバージョン: 1.0.0
- ソフトウェアバージョン: 1.0.0-solo

## 概要
このガイドでは、Raspberry Pi 5（P1）をBME680センサーを搭載した単一のRaspberry Pi Pico 2W（P2）と連携する環境データ測定システムとしてセットアップする方法を説明します。このソロバージョンは、BME680センサーのみを使用し、CO2センサー（MH-Z19B）は使用しません。

## 必要なハードウェア
- Raspberry Pi 5（4GB以上のRAMを推奨）
- Raspberry Pi Pico 2W（P2）
- BME680環境センサー
- microSDカード（16GB以上を推奨）
- 電源アダプター（Raspberry Pi 5用）
- （オプション）USB WiFiドングル（インターネット接続用）

## 前提条件
- Raspberry Pi OSがインストールされていること（Bullseye以降を推奨）
- インターネット接続が利用可能であること（初期セットアップ時）
- SSHまたはディスプレイとキーボードでRaspberry Pi 5にアクセスできること

## インストール手順

### 1. システムの更新
まず、システムを最新の状態に更新します：

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. 必要なパッケージのインストール
必要なパッケージをインストールします：

```bash
sudo apt install -y git python3-venv
```

### 3. 仮想環境のセットアップ
Pythonの仮想環境を作成し、有効化します：

```bash
cd ~
python3 -m venv envmonitor-venv
source envmonitor-venv/bin/activate
```

### 4. 必要なPythonパッケージのインストール
仮想環境内に必要なPythonパッケージをインストールします：

```bash
pip install flask flask-socketio pandas plotly
```

### 5. リポジトリのクローン
プロジェクトリポジトリをクローンします：

```bash
git clone https://github.com/yourusername/RaspPi5_APconnection.git
cd RPi_Development01
```

> 注意: 仮想環境を使用する際は、Pythonスクリプトを実行する前に必ず仮想環境を有効化してください：
> ```bash
> source ~/envmonitor-venv/bin/activate
> ```

### 6. ディレクトリの作成
データとログを保存するディレクトリを作成します：

```bash
sudo mkdir -p /var/lib(FromThonny)/raspap_solo/data
sudo mkdir -p /var/lib(FromThonny)/raspap_solo/logs
sudo chmod 755 /var/lib(FromThonny)/raspap_solo/data
sudo chmod 755 /var/lib(FromThonny)/raspap_solo/logs
```

### 7. アクセスポイントの設定
P1をアクセスポイントとして設定します：

```bash
cd p1_software_solo/ap_setup
source ~/envmonitor-venv/bin/activate
sudo ~/envmonitor-venv/bin/python3 P1_ap_setup_solo.py --configure
```

設定が完了したら、Raspberry Pi 5を再起動します：

```bash
sudo reboot
```

### 8. 自動起動の設定
システム起動時に自動的にサービスを開始するように設定します：

```bash
sudo nano /etc/rc.local
```

ファイルの末尾（`exit 0`の前）に以下の行を追加します：

```bash
# Start P1 solo services
/home/pi/envmonitor-venv/bin/python3 /path/to/RPi_Development01/p1_software_solo/start_p1_solo.py &
```

`/home/pi/`を実際のホームディレクトリに置き換えてください。

`/path/to/`を実際のパスに置き換えてください。

ファイルを保存して閉じます（Ctrl+O, Enter, Ctrl+X）。

rc.localファイルに実行権限があることを確認します：

```bash
sudo chmod +x /etc/rc.local
```

## 手動での起動方法
システムを手動で起動するには、以下のコマンドを実行します：

```bash
cd /path/to/RPi_Development01/p1_software_solo
source ~/envmonitor-venv/bin/activate
sudo ~/envmonitor-venv/bin/python3 start_p1_solo.py
```

このコマンドは以下のサービスを起動します：
1. アクセスポイント設定
2. データ収集サービス
3. Webインターフェース
4. 接続モニター

## 各コンポーネントの個別起動（必要な場合）

### アクセスポイント設定
```bash
cd /path/to/RPi_Development01/p1_software_solo/ap_setup
source ~/envmonitor-venv/bin/activate
sudo ~/envmonitor-venv/bin/python3 P1_ap_setup_solo.py --configure  # 初回設定
sudo ~/envmonitor-venv/bin/python3 P1_ap_setup_solo.py --enable     # 有効化
sudo ~/envmonitor-venv/bin/python3 P1_ap_setup_solo.py --status     # 状態確認
```

### データ収集サービス
```bash
cd /path/to/RPi_Development01/p1_software_solo/data_collection
source ~/envmonitor-venv/bin/activate
sudo ~/envmonitor-venv/bin/python3 P1_data_collector_solo.py
```

### Webインターフェース
```bash
cd /path/to/RPi_Development01/p1_software_solo/web_interface
source ~/envmonitor-venv/bin/activate
sudo ~/envmonitor-venv/bin/python3 P1_app_solo.py
```

### 接続モニター
```bash
cd /path/to/RPi_Development01/p1_software_solo/connection_monitor
source ~/envmonitor-venv/bin/activate
sudo ~/envmonitor-venv/bin/python3 P1_wifi_monitor_solo.py
```

## アクセス方法
システムが起動したら、以下の方法でアクセスできます：

1. P2デバイスをRaspberry Pi 5のアクセスポイントに接続します（SSID: RaspberryPi5_AP_Solo）
2. WebブラウザでRaspberry Pi 5のIPアドレス（デフォルトは192.168.0.1）にアクセスします
3. Webインターフェースが表示され、環境データを閲覧できます

## トラブルシューティング

### アクセスポイントが起動しない場合
```bash
sudo systemctl status hostapd
sudo systemctl status dnsmasq
```

エラーがある場合は、ログを確認します：
```bash
sudo cat /var/log/ap_setup_solo.log
```

### データ収集サービスが動作しない場合
ログを確認します：
```bash
sudo cat /var/log/data_collector_solo.log
```

### Webインターフェースにアクセスできない場合
サービスが実行中か確認します：
```bash
ps aux | grep P1_app_solo.py
```

ログを確認します：
```bash
sudo cat /var/log/web_interface_solo.log
```

### 接続モニターが動作しない場合
ログを確認します：
```bash
sudo cat /var/log/wifi_monitor_solo.log
```

### 全般的な問題
統合スタートアップスクリプトのログを確認します：
```bash
sudo cat /var/log/p1_startup_solo.log
```

## 注意事項
- このソロバージョンは、BME680センサーのみをサポートしています（CO2センサーはサポートしていません）
- P2デバイスのIPアドレスは、デフォルトで192.168.0.101に設定されています
- Webインターフェースは、デフォルトでポート80で実行されます
- データAPIは、デフォルトでポート5001で実行されます
- 接続モニターAPIは、デフォルトでポート5002で実行されます

## ソロバージョンと標準バージョンの違い
ソロバージョンは、標準バージョンと比較して以下の違いがあります：

1. 単一のP2デバイスのみをサポート（P3はサポートしない）
2. BME680センサーのみをサポート（CO2センサーはサポートしない）
3. 設定ファイルとログファイルは別のディレクトリに保存される（/var/lib/raspap_solo/）
4. Webインターフェースは簡略化され、BME680センサーのデータのみを表示
5. 統合スタートアップスクリプト（start_p1_solo.py）が提供され、すべてのサービスを一度に起動可能

## 更新履歴
- 1.0.0 (2025-06-30): 初回リリース

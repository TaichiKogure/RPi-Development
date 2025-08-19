# Raspberry Pi 5とPico 2Wによるスタンドアロン環境データ測定システム - インストールガイド

**バージョン: 1.0.0**

このガイドでは、Raspberry Pi 5とPico 2Wによるスタンドアロン環境データ測定システムのインストールとセットアップの手順を説明します。

## 目次

1. [システム要件](#1-システム要件)
2. [ハードウェアセットアップ](#2-ハードウェアセットアップ)
3. [P1 (Raspberry Pi 5) セットアップ](#3-p1-raspberry-pi-5-セットアップ)
4. [P4, P5, P6 (Raspberry Pi Pico 2W) セットアップ](#4-p4-p5-p6-raspberry-pi-pico-2w-セットアップ)
5. [システムのテスト](#5-システムのテスト)
6. [トラブルシューティング](#6-トラブルシューティング)

## 1. システム要件

### ハードウェア要件

- 1 × Raspberry Pi 5 (P1)
- 3 × Raspberry Pi Pico 2W (P4, P5, P6)
- 3 × BME680センサー
- 3 × MH-Z19B CO2センサー
- すべてのデバイス用の電源
- Raspberry Pi 5用のMicroSDカード（16GB以上）
- Raspberry Pi Pico 2Wのプログラミング用USBケーブル
- センサー接続用のジャンパーワイヤ

### ソフトウェア要件

- Raspberry Pi 5用のRaspberry Pi OS（64ビット）
- Raspberry Pi Pico 2W用のMicroPython
- Raspberry Pi Pico 2Wのプログラミング用Thonny IDE

## 2. ハードウェアセットアップ

### 2.1 Raspberry Pi 5 (P1) ハードウェアセットアップ

1. MicroSDカードをRaspberry Pi 5に挿入します。
2. 電源をRaspberry Pi 5に接続します。
3. 初期セットアップ用にモニター、キーボード、マウスを接続します。

### 2.2 Raspberry Pi Pico 2W (P4, P5, P6) ハードウェアセットアップ

各Pico 2Wに対して、BME680センサーとMH-Z19B CO2センサーを以下のように接続します：

#### BME680センサー接続

| BME680ピン | Pico 2Wピン |
|------------|-------------|
| VCC        | 3.3V (ピン36) |
| GND        | GND (ピン38) |
| SCL        | GP1 (ピン2) |
| SDA        | GP0 (ピン1) |

#### MH-Z19B CO2センサー接続

| MH-Z19Bピン | Pico 2Wピン |
|-------------|-------------|
| VCC (赤)    | VBUS (5V, ピン40) |
| GND (黒)    | GND (ピン38) |
| TX (緑)     | GP9 (ピン12) |
| RX (青)     | GP8 (ピン11) |

## 3. P1 (Raspberry Pi 5) セットアップ

### 3.1 オペレーティングシステムのインストール

1. Raspberry Pi Imagerを[https://www.raspberrypi.org/software/](https://www.raspberrypi.org/software/)からダウンロードします。
2. MicroSDカードをコンピュータに挿入します。
3. Raspberry Pi Imagerを起動します。
4. オペレーティングシステムとして「Raspberry Pi OS (64-bit)」を選択します。
5. ストレージとしてMicroSDカードを選択します。
6. 歯車アイコンをクリックして詳細オプションにアクセスします：
   - ホスト名を「raspberrypi」に設定
   - SSHを有効化
   - ユーザー名とパスワードを設定
   - WiFiを設定（インターネットアクセスが必要な場合）
7. 「書き込み」をクリックしてOSをMicroSDカードに書き込みます。
8. MicroSDカードをRaspberry Pi 5に挿入して電源を入れます。

### 3.2 初期設定

1. SSHでRaspberry Pi 5に接続するか、接続されたモニターとキーボードを使用します。
2. システムを更新します：
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```
3. 必要なパッケージをインストールします：
   ```bash
   sudo apt install -y python3-pip python3-venv hostapd dnsmasq git
   ```

### 3.3 Python仮想環境のセットアップ

1. 仮想環境を作成します：
   ```bash
   cd ~
   python3 -m venv envmonitor-venv
   source envmonitor-venv/bin/activate
   ```
2. 必要なPythonパッケージをインストールします：
   ```bash
   pip install flask flask-socketio pandas plotly
   ```

### 3.4 ソフトウェアのダウンロードとインストール

1. リポジトリをクローンします：
   ```bash
   git clone https://github.com/yourusername/RaspPi5_APconnection.git
   cd RaspPi5_APconnection
   ```
   
   または、開発環境からファイルをRaspberry Pi 5にコピーします。

2. 必要なディレクトリを作成します：
   ```bash
   sudo mkdir -p /var/lib(FromThonny)/raspap_solo/data
   sudo mkdir -p /var/lib(FromThonny)/raspap_solo/data/RawData_P4
   sudo mkdir -p /var/lib(FromThonny)/raspap_solo/data/RawData_P5
   sudo mkdir -p /var/lib(FromThonny)/raspap_solo/data/RawData_P6
   sudo mkdir -p /var/lib(FromThonny)/raspap_solo/logs
   sudo mkdir -p /var/log
   ```

3. 権限を設定します：
   ```bash
   sudo chown -R pi:pi /var/lib(FromThonny)/raspap_solo
   ```

### 3.5 アクセスポイントの設定

1. セットアップスクリプトを実行してアクセスポイントを設定します：
   ```bash
   cd ~/RaspPi5_APconnection/ForZero/Ver1.00zero
   source ~/envmonitor-venv/bin/activate
   sudo python3 p1_software_Zero/ap_setup/P1_ap_setup_solo.py --configure
   ```

2. Raspberry Pi 5を再起動します：
   ```bash
   sudo reboot
   ```

3. 再起動後、アクセスポイントがアクティブであることを確認します：
   ```bash
   sudo systemctl status hostapd
   sudo systemctl status dnsmasq
   ```

## 4. P4, P5, P6 (Raspberry Pi Pico 2W) セットアップ

### 4.1 Pico 2WにMicroPythonをインストール

各Pico 2W（P4、P5、P6）に対して：

1. Raspberry Pi Pico W用の最新のMicroPython UF2ファイルを[https://micropython.org/download/rp2-pico-w/](https://micropython.org/download/rp2-pico-w/)からダウンロードします。
2. BOOTSELボタンを押しながらPico 2Wをコンピュータに接続します。
3. 接続後、BOOTSELボタンを離します。
4. Pico 2WがUSBドライブとして表示されます。
5. ダウンロードしたUF2ファイルをPico 2W USBドライブにコピーします。
6. Pico 2Wは自動的に再起動し、MicroPythonをインストールします。

### 4.2 Thonny IDEのインストール

1. Thonny IDEを[https://thonny.org/](https://thonny.org/)からダウンロードしてインストールします。
2. Thonny IDEを起動します。
3. ツール > オプション > インタープリタに移動します。
4. インタープリタとして「MicroPython (Raspberry Pi Pico)」を選択します。
5. Pico 2W用の適切なCOMポートを選択します。

### 4.3 P4へのソフトウェアのアップロード

1. P4 Pico 2Wをコンピュータに接続します。
2. Thonny IDEで、Pico 2Wに以下のディレクトリ構造を作成します：
   - `/sensor_drivers`
   - `/data_transmission`
   - `/error_handling`

3. 以下のファイルをPico 2Wにアップロードします：
   - `main.py`をルートディレクトリに
   - `bme680.py`と`mhz19c.py`を`/sensor_drivers`ディレクトリに
   - `P4_wifi_client_debug.py`と`wifi_client.py`を`/data_transmission`ディレクトリに
   - `P4_watchdog_debug.py`と`watchdog.py`を`/error_handling`ディレクトリに

4. すべてのファイルが正しくアップロードされたことを確認します。

### 4.4 P5へのソフトウェアのアップロード

4.3の手順を繰り返しますが、P5固有のファイルを使用します：
   - `main.py`をルートディレクトリに
   - `bme680.py`と`mhz19c.py`を`/sensor_drivers`ディレクトリに
   - `P5_wifi_client_debug.py`と`wifi_client.py`を`/data_transmission`ディレクトリに
   - `P5_watchdog_debug.py`と`watchdog.py`を`/error_handling`ディレクトリに

### 4.5 P6へのソフトウェアのアップロード

4.3の手順を繰り返しますが、P6固有のファイルを使用します：
   - `main.py`をルートディレクトリに
   - `bme680.py`と`mhz19c.py`を`/sensor_drivers`ディレクトリに
   - `P6_wifi_client_debug.py`と`wifi_client.py`を`/data_transmission`ディレクトリに
   - `P6_watchdog_debug.py`と`watchdog.py`を`/error_handling`ディレクトリに

## 5. システムのテスト

### 5.1 P1サービスの開始

1. SSHでRaspberry Pi 5に接続するか、接続されたモニターとキーボードを使用します。
2. プロジェクトディレクトリに移動します：
   ```bash
   cd ~/RaspPi5_APconnection/ForZero/Ver1.00zero
   ```
3. 仮想環境を有効化します：
   ```bash
   source ~/envmonitor-venv/bin/activate
   ```
4. P1サービスを開始します：
   ```bash
   sudo python3 p1_software_Zero/start_p1_solo.py
   ```

### 5.2 P4, P5, P6の接続テスト

1. P4、P5、P6の電源を入れます。
2. P1のアクセスポイントに接続するのを待ちます。
3. P1で接続状態を確認します：
   ```bash
   sudo python3 p1_software_Zero/connection_monitor/P1_wifi_monitor_solo.py --status
   ```

### 5.3 データ収集の確認

1. P1でデータが収集されているか確認します：
   ```bash
   ls -la /var/lib(FromThonny)/raspap_solo/data/RawData_P4
   ls -la /var/lib(FromThonny)/raspap_solo/data/RawData_P5
   ls -la /var/lib(FromThonny)/raspap_solo/data/RawData_P6
   ```

2. 最新のデータを表示します：
   ```bash
   tail -n 10 /var/lib(FromThonny)/raspap_solo/data/RawData_P4/P4_fixed.csv
   tail -n 10 /var/lib(FromThonny)/raspap_solo/data/RawData_P5/P5_fixed.csv
   tail -n 10 /var/lib(FromThonny)/raspap_solo/data/RawData_P6/P6_fixed.csv
   ```

### 5.4 Webインターフェースへのアクセス

1. P1のアクセスポイントに接続されたデバイスからWebブラウザを開きます。
2. `http://192.168.0.1`にアクセスします。
3. WebインターフェースがロードされP4、P5、P6からのデータが表示されることを確認します。

## 6. トラブルシューティング

### 6.1 P1の問題

- **アクセスポイントが機能しない**
  - hostapdとdnsmasqのステータスを確認します：
    ```bash
    sudo systemctl status hostapd
    sudo systemctl status dnsmasq
    ```
  - アクセスポイントを再設定します：
    ```bash
    sudo python3 p1_software_Zero/ap_setup/P1_ap_setup_solo.py --configure
    ```

- **データ収集が機能しない**
  - データ収集サービスを確認します：
    ```bash
    sudo python3 p1_software_Zero/data_collection/P1_data_collector_solo.py --status
    ```
  - ログを確認します：
    ```bash
    tail -n 100 /var/log/data_collector_solo.log
    ```

- **Webインターフェースが機能しない**
  - Webインターフェースサービスを確認します：
    ```bash
    sudo python3 p1_software_Zero/web_interface/P1_app_solo.py --status
    ```
  - ログを確認します：
    ```bash
    tail -n 100 /var/log/web_interface_solo.log
    ```

### 6.2 P4, P5, P6の問題

- **WiFi接続の問題**
  - Pico 2Wが正しいWiFiネットワークに接続しているか確認します。
  - `main.py`ファイル内のWiFi認証情報を確認します。
  - LEDステータスを確認します：
    - 1回点滅：データ送信成功
    - 2回点滅：データ送信失敗
    - 3回点滅：エラー

- **センサーの問題**
  - センサー接続を確認します。
  - BME680センサーのI2Cアドレスが正しいか（0x76または0x77）確認します。
  - MH-Z19BセンサーのUARTピンを確認します。

より詳細なトラブルシューティングについては、トラブルシューティングガイドを参照してください。
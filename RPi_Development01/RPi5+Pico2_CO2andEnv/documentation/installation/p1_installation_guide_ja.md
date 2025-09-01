# Raspberry Pi 5 (P1) インストールガイド
バージョン: 2.0.0

このガイドでは、環境データ測定システムの中央ハブとしてRaspberry Pi 5（P1）をセットアップするための手順を説明します。

## 目次
1. [ハードウェア要件](#ハードウェア要件)
2. [オペレーティングシステムのインストール](#オペレーティングシステムのインストール)
3. [ネットワーク設定](#ネットワーク設定)
4. [ソフトウェアのインストール](#ソフトウェアのインストール)
5. [アクセスポイントのセットアップ](#アクセスポイントのセットアップ)
6. [データ収集サービスのセットアップ](#データ収集サービスのセットアップ)
7. [Webインターフェースのセットアップ](#webインターフェースのセットアップ)
8. [接続モニターのセットアップ](#接続モニターのセットアップ)
9. [システムテスト](#システムテスト)
10. [トラブルシューティング](#トラブルシューティング)

## ハードウェア要件
- Raspberry Pi 5（4GBまたは8GB RAM推奨）
- MicroSDカード（32GB以上推奨）
- 電源（5V、5A USB-C）
- USB WiFiドングル（オプション、インターネット接続用）
- イーサネットケーブル（オプション、初期セットアップ用）
- 冷却機能付きケース（推奨）
- モニター、キーボード、マウス（初期セットアップ用）

## オペレーティングシステムのインストール
1. [公式ウェブサイト](https://www.raspberrypi.org/software/operating-systems/)から最新のRaspberry Pi OS（64ビット）をダウンロードします。
2. Raspberry Pi Imagerを使用してOSをMicroSDカードに書き込みます：
   - [Raspberry Pi Imager](https://www.raspberrypi.org/software/)をダウンロードしてインストールします
   - MicroSDカードをコンピュータに挿入します
   - Raspberry Pi Imagerを開きます
   - 「OSを選択」をクリックし、「Raspberry Pi OS（64ビット）」を選択します
   - 「ストレージを選択」をクリックし、MicroSDカードを選択します
   - 歯車アイコン（⚙️）をクリックして詳細オプションにアクセスします
   - SSH、ユーザー名とパスワードの設定、WiFi設定（必要な場合）、ロケール設定を行います
   - 「書き込み」をクリックし、プロセスが完了するのを待ちます

3. MicroSDカードをRaspberry Pi 5に挿入し、電源を入れます。
4. 初期セットアップを完了します：
   - ライセンス契約に同意する
   - ユーザーアカウントを設定する（イメージャーで行っていない場合）
   - WiFiに接続する（イメージャーで行っていない場合）
   - システムを更新する

## ネットワーク設定
1. ターミナルウィンドウを開き、システムを更新します：
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```

2. ネットワークユーティリティをインストールします：
   ```bash
   sudo apt install -y net-tools wireless-tools bridge-utils
   ```

3. インターネット接続用にUSB WiFiドングルを使用する場合は、ここで接続します。

## ソフトウェアのインストール
1. 必要な依存関係をインストールします：
   ```bash
   sudo apt install -y python3-pip python3-flask python3-pandas python3-plotly python3-dev git
   ```

2. 追加のPythonパッケージをインストールします：
   ```bash
   sudo pip3 install flask-socketio pandas plotly
   ```

3. プロジェクトリポジトリをクローンします：
   ```bash
   git clone https://github.com/yourusername/RaspPi5_APconnection.git
   cd RPi_Development01
   ```

   > 注：GitHubにリポジトリがない場合は、ファイルを手動でRaspberry Piにコピーできます。

## アクセスポイントのセットアップ
1. アクセスポイントセットアップディレクトリに移動します：
   ```bash
   cd ~/RPi_Development01/p1_software/ap_setup
   ```

2. セットアップスクリプトを実行可能にします：
   ```bash
   chmod +x ap_setup.py
   ```

3. sudo権限でセットアップスクリプトを実行します：
   ```bash
   sudo python3 ap_setup.py --configure
   ```

4. 画面の指示に従ってセットアップを完了します。

5. セットアップが完了したら、Raspberry Piを再起動します：
   ```bash
   sudo reboot
   ```

6. 再起動後、アクセスポイントが機能していることを確認します：
   ```bash
   sudo python3 ap_setup.py --status
   ```

7. 「RaspberryPi5_AP」（デフォルト名）というWiFiネットワークが表示され、パスワード「raspberry」（デフォルトパスワード）を使用して他のデバイスから接続できるはずです。

## データ収集サービスのセットアップ
1. データ収集ディレクトリに移動します：
   ```bash
   cd ~/RPi_Development01/p1_software/data_collection
   ```

2. データディレクトリを作成します：
   ```bash
   sudo mkdir -p /var/lib(FromThonny)/raspap/data
   sudo chown -R $USER:$USER /var/lib(FromThonny)/raspap/data
   ```

3. データコレクター用のsystemdサービスファイルを作成します：
   ```bash
   sudo nano /etc/systemd/system/data_collector.service
   ```

4. ファイルに以下の内容を追加します：
   ```
   [Unit]
   Description=Environmental Data Collector
   After=network.target

   [Service]
   ExecStart=/usr/bin/python3 /home/pi/RaspPi5_APconnection/p1_software/data_collection/data_collector.py
   WorkingDirectory=/home/pi/RaspPi5_APconnection/p1_software/data_collection
   StandardOutput=inherit
   StandardError=inherit
   Restart=always
   User=pi

   [Install]
   WantedBy=multi-user.target
   ```

   > 注：ユーザー名が異なる場合は、「pi」を適切なユーザー名に置き換えてください。

5. サービスを有効にして起動します：
   ```bash
   sudo systemctl enable data_collector.service
   sudo systemctl start data_collector.service
   ```

6. サービスのステータスを確認します：
   ```bash
   sudo systemctl status data_collector.service
   ```

## Webインターフェースのセットアップ
1. Webインターフェースディレクトリに移動します：
   ```bash
   cd ~/RPi_Development01/p1_software/web_interface
   ```

2. Webインターフェース用のsystemdサービスファイルを作成します：
   ```bash
   sudo nano /etc/systemd/system/web_interface.service
   ```

3. ファイルに以下の内容を追加します：
   ```
   [Unit]
   Description=Environmental Data Web Interface
   After=network.target data_collector.service

   [Service]
   ExecStart=/usr/bin/python3 /home/pi/RaspPi5_APconnection/p1_software/web_interface/app.py
   WorkingDirectory=/home/pi/RaspPi5_APconnection/p1_software/web_interface
   StandardOutput=inherit
   StandardError=inherit
   Restart=always
   User=pi

   [Install]
   WantedBy=multi-user.target
   ```

   > 注：ユーザー名が異なる場合は、「pi」を適切なユーザー名に置き換えてください。

4. サービスを有効にして起動します：
   ```bash
   sudo systemctl enable web_interface.service
   sudo systemctl start web_interface.service
   ```

5. サービスのステータスを確認します：
   ```bash
   sudo systemctl status web_interface.service
   ```

## 接続モニターのセットアップ
1. 接続モニターディレクトリに移動します：
   ```bash
   cd ~/RPi_Development01/p1_software/connection_monitor
   ```

2. 接続モニター用のsystemdサービスファイルを作成します：
   ```bash
   sudo nano /etc/systemd/system/wifi_monitor.service
   ```

3. ファイルに以下の内容を追加します：
   ```
   [Unit]
   Description=WiFi Connection Monitor
   After=network.target

   [Service]
   ExecStart=/usr/bin/python3 /home/pi/RaspPi5_APconnection/p1_software/connection_monitor/wifi_monitor.py
   WorkingDirectory=/home/pi/RaspPi5_APconnection/p1_software/connection_monitor
   StandardOutput=inherit
   StandardError=inherit
   Restart=always
   User=pi

   [Install]
   WantedBy=multi-user.target
   ```

   > 注：ユーザー名が異なる場合は、「pi」を適切なユーザー名に置き換えてください。

4. サービスを有効にして起動します：
   ```bash
   sudo systemctl enable wifi_monitor.service
   sudo systemctl start wifi_monitor.service
   ```

5. サービスのステータスを確認します：
   ```bash
   sudo systemctl status wifi_monitor.service
   ```

## システムテスト
1. 別のデバイス（スマートフォンやラップトップなど）からRaspberry Pi 5のWiFiネットワークに接続します。
2. Webブラウザを開き、`http://192.168.0.1`（または設定したIPアドレス）にアクセスします。
3. 環境データダッシュボードが表示されるはずです。
4. P2およびP3デバイスをセットアップしている場合、それらはRaspberry Pi 5のWiFiネットワークに接続してデータの送信を開始するはずです。
5. ダッシュボードにはP2およびP3デバイスからのデータが表示されるはずです。

## トラブルシューティング
### アクセスポイントの問題
- アクセスポイントが機能していない場合は、ステータスを確認します：
  ```bash
  sudo python3 ~/RPi_Development01/p1_software/ap_setup/ap_setup.py --status
  ```
- アクセスポイントを再設定してみてください：
  ```bash
  sudo python3 ~/RPi_Development01/p1_software/ap_setup/ap_setup.py --configure
  ```
- システムログでエラーを確認します：
  ```bash
  sudo journalctl -u hostapd
  sudo journalctl -u dnsmasq
  ```

### データ収集の問題
- データコレクターサービスのステータスを確認します：
  ```bash
  sudo systemctl status data_collector.service
  ```
- データコレクターのログを確認します：
  ```bash
  sudo journalctl -u data_collector.service
  ```
- データディレクトリが存在し、適切な権限を持っていることを確認します：
  ```bash
  ls -la /var/lib(FromThonny)/raspap/data
  ```

### Webインターフェースの問題
- Webインターフェースサービスのステータスを確認します：
  ```bash
  sudo systemctl status web_interface.service
  ```
- Webインターフェースのログを確認します：
  ```bash
  sudo journalctl -u web_interface.service
  ```
- Raspberry Pi自体からWebインターフェースにアクセスできることを確認します：
  ```bash
  curl http://localhost:80
  ```

### 接続モニターの問題
- 接続モニターサービスのステータスを確認します：
  ```bash
  sudo systemctl status wifi_monitor.service
  ```
- 接続モニターのログを確認します：
  ```bash
  sudo journalctl -u wifi_monitor.service
  ```

### 一般的な問題
- Raspberry Piを再起動します：
  ```bash
  sudo reboot
  ```
- システムリソースを確認します：
  ```bash
  htop
  ```
- ディスク容量を確認します：
  ```bash
  df -h
  ```
- ネットワークインターフェースを確認します：
  ```bash
  ifconfig
  ```
- WiFiステータスを確認します：
  ```bash
  iwconfig
  ```

より詳細なトラブルシューティングについては、[トラブルシューティングガイド](../troubleshooting/troubleshooting_guide_ja.md)を参照してください。

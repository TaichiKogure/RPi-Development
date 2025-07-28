# Raspberry Pi 5 環境データ測定システム Ver4.0 マニュアル

## 概要

このシステムは、Raspberry Pi 5（P1）をセントラルハブとして、Raspberry Pi Pico 2W（P2とP3）をセンサーノードとして使用する環境データ測定システムです。P2とP3はそれぞれ温度、湿度、気圧、ガス抵抗値を測定するBME680センサーと、CO2濃度を測定するMH-Z19Cセンサーを搭載しています。測定されたデータはWiFi経由でP1に送信され、保存・可視化されます。Ver4.0では、P2とP3の両方からのデータを同時に表示し、比較することができます。また、温度と湿度から計算された絶対湿度も表示されます。

## システム構成

1. **Raspberry Pi 5（P1）**
   - WiFiアクセスポイントとして機能
   - P2とP3からのデータ収集・保存
   - Webインターフェースによるデータ可視化（P2とP3のデータを重ね表示可能）
   - P2とP3との接続品質モニタリング
   - 絶対湿度の計算

2. **Raspberry Pi Pico 2W（P2、P3）**
   - BME680センサーによる環境データ測定
   - MH-Z19CセンサーによるCO2濃度測定
   - WiFi経由でのデータ送信
   - エラー時の自動再起動機能

3. **センサー**
   - BME680: 温度、湿度、気圧、ガス抵抗値を測定
   - MH-Z19C: CO2濃度を測定

## インストール手順

### P1（Raspberry Pi 5）のセットアップ

1. **必要なもの**
   - Raspberry Pi 5
   - microSDカード（16GB以上推奨）
   - 電源アダプター
   - キーボード、マウス、モニター（初期設定用）

2. **OSのインストール**
   - Raspberry Pi OSをインストールします（Bullseye以降推奨）
   - 初期設定を完了させます（ユーザー名、パスワード、WiFi設定など）

3. **必要なパッケージのインストール**
   ```bash
   sudo apt update
   sudo apt upgrade -y
   sudo apt install -y git python3-pip python3-venv hostapd dnsmasq iptables
   ```

4. **仮想環境のセットアップ**
   ```bash
   cd ~
   python3 -m venv envmonitor-venv
   source envmonitor-venv/bin/activate
   pip install flask flask-socketio pandas plotly requests
   ```

5. **プロジェクトのダウンロード**
   ```bash
   cd ~
   git clone https://github.com/yourusername/RaspPi5_APconnection.git
   cd RaspPi5_APconnection
   ```

   または、提供されたファイルを`/home/pi/RaspPi5_APconnection/Ver4.0`にコピーします。

6. **P1ソフトウェアのセットアップ**
   ```bash
   cd ~/RaspPi5_APconnection/Ver4.0
   sudo mkdir -p /var/lib(FromThonny)/raspap_solo/data
   sudo mkdir -p /var/lib(FromThonny)/raspap_solo/data/RawData_P2
   sudo mkdir -p /var/lib(FromThonny)/raspap_solo/data/RawData_P3
   sudo chmod -R 777 /var/lib(FromThonny)/raspap_solo/data
   sudo mkdir -p /var/log
   sudo touch /var/log/ap_setup_solo.log /var/log/data_collector_solo.log /var/log/web_interface_solo.log /var/log/wifi_monitor_solo.log /var/log/p1_startup_solo.log
   sudo chmod 666 /var/log/ap_setup_solo.log /var/log/data_collector_solo.log /var/log/web_interface_solo.log /var/log/wifi_monitor_solo.log /var/log/p1_startup_solo.log
   ```

7. **自動起動の設定**
   ```bash
   sudo nano /etc/rc.local
   ```
   
   ファイルの末尾（`exit 0`の前）に以下を追加します：
   ```bash
   # Start P1 services
   sudo /home/pi/envmonitor-venv/bin/python3 /home/pi/RaspPi5_APconnection/Ver4.0/p1_software_solo40/start_p1_solo.py &
   ```

### P2（Raspberry Pi Pico 2W）のセットアップ

1. **必要なもの**
   - Raspberry Pi Pico 2W
   - BME680センサー
   - MH-Z19Cセンサー
   - ジャンパーワイヤー
   - microUSBケーブル

2. **MicroPythonのインストール**
   - [Raspberry Pi Pico公式サイト](https://www.raspberrypi.org/documentation/rp2040/getting-started/)からMicroPythonのUF2ファイルをダウンロードします
   - BOOTSELボタンを押しながらPicoをPCに接続し、UF2ファイルをドラッグ＆ドロップします

3. **センサーの接続**
   - **BME680センサー**
     - VCC → 3.3V（Pin 36）
     - GND → GND（Pin 38）
     - SCL → GP1（Pin 2）
     - SDA → GP0（Pin 1）
   
   - **MH-Z19Cセンサー**
     - VCC（赤） → VBUS（5V、Pin 40）
     - GND（黒） → GND（Pin 38）
     - TX（緑） → GP9（Pin 12）
     - RX（青） → GP8（Pin 11）

4. **プログラムの転送**
   - Thonny IDEを使用して、`P2_software_solo40`フォルダ内のすべてのファイルをPicoに転送します
   - `main.py`を保存します（自動起動のため）

### P3（Raspberry Pi Pico 2W）のセットアップ

1. **必要なもの**
   - Raspberry Pi Pico 2W
   - BME680センサー
   - MH-Z19Cセンサー
   - ジャンパーワイヤー
   - microUSBケーブル

2. **MicroPythonのインストール**
   - P2と同様の手順でMicroPythonをインストールします

3. **センサーの接続**
   - P2と同様の接続方法でセンサーを接続します

4. **プログラムの転送**
   - Thonny IDEを使用して、`P3_software_solo40`フォルダ内のすべてのファイルをPicoに転送します
   - `main.py`を保存します（自動起動のため）

## 操作方法

### P1（Raspberry Pi 5）の操作

1. **システムの起動**
   - P1の電源を入れると、自動的にアクセスポイントが起動し、データ収集サービスとWebインターフェースが開始されます
   - 起動には約1分かかります

2. **Webインターフェースへのアクセス**
   - スマートフォンやPCのWiFi設定から、`RaspberryPi5_AP_Solo`というSSIDを探して接続します
   - パスワードは`raspberry`です
   - ブラウザを開き、`http://192.168.0.1`にアクセスします

3. **データの閲覧**
   - ホーム画面では、P2とP3の最新の測定値と接続状態の概要が表示されます
   - 「Dashboard」をクリックすると、詳細なグラフと測定値が表示されます
   - グラフは1日、1週間、1ヶ月の期間で表示できます
   - P2とP3のデータを個別に表示/非表示にするチェックボックスがあります

4. **データのエクスポート**
   - ダッシュボード画面の「Export Data」セクションで、デバイス（P2、P3、または両方）と期間を指定してCSVファイルをダウンロードできます

5. **接続状態の確認**
   - ホーム画面とダッシュボード画面の「Connection Status」セクションで、P2とP3との接続品質を確認できます
   - 信号強度、ping時間、ノイズレベルなどが表示されます

### P2/P3（Raspberry Pi Pico 2W）の操作

1. **システムの起動**
   - P2/P3の電源を入れると、自動的にセンサーの初期化とWiFi接続が行われます
   - MH-Z19Cセンサーのウォームアップのため、起動後30秒間はCO2測定値が取得されません
   - 正常に動作すると、オンボードLEDが点灯します

2. **LEDインジケーター**
   - 常時点灯: 正常動作中
   - 点滅（1回）: データ送信時
   - 点滅（2回）: WiFiエラー
   - 点滅（3回）: センサーエラー
   - 点滅（4回）: 複合エラー
   - 高速点滅: リセット中

3. **トラブルシューティング**
   - P2/P3が応答しない場合は、リセットボタンを押して再起動します
   - エラーが続く場合は、P2/P3を再起動してください

## システムの仕様

### P1（Raspberry Pi 5）

- **アクセスポイント設定**
  - SSID: RaspberryPi5_AP_Solo
  - パスワード: raspberry
  - IPアドレス: 192.168.0.1
  - DHCPレンジ: 192.168.0.50 - 192.168.0.150

- **データ収集**
  - 収集間隔: 30秒
  - 保存形式: CSV（日付ごとにファイル作成）
  - 保存場所: 
    - P2データ: /var/lib/raspap_solo/data/RawData_P2
    - P3データ: /var/lib/raspap_solo/data/RawData_P3

- **Webインターフェース**
  - ポート: 80
  - 自動更新間隔: 30秒
  - グラフ表示: 温度、湿度、絶対湿度、気圧、ガス抵抗値、CO2濃度
  - 表示オプション: P2/P3データの個別表示/非表示

### P2/P3（Raspberry Pi Pico 2W）

- **センサー仕様**
  - BME680
    - 温度測定範囲: -40°C～85°C
    - 湿度測定範囲: 0%～100%
    - 気圧測定範囲: 300hPa～1100hPa
  
  - MH-Z19C
    - CO2測定範囲: 400ppm～5000ppm
    - ウォームアップ時間: 30秒
    - 測定精度: ±50ppm

- **データ送信**
  - 送信間隔: 30秒
  - 再試行回数: 最大5回
  - 接続先: 192.168.0.1:5000

## 注意事項

1. P1とP2/P3の距離が離れすぎると、接続が不安定になる場合があります。接続状態を確認しながら、適切な位置に設置してください。

2. MH-Z19CセンサーはCO2測定のために30秒のウォームアップ時間が必要です。起動直後はCO2の測定値が表示されないことがあります。

3. システムを長期間使用する場合は、定期的にP1のmicroSDカードのバックアップを取ることをお勧めします。

4. P1のIPアドレスを変更する場合は、P2とP3のプログラムも修正する必要があります。

5. P2とP3は同じ環境に設置することを想定していますが、異なる環境に設置することで環境の比較測定も可能です。

## トラブルシューティング

1. **P1のWebインターフェースにアクセスできない**
   - P1が正常に起動しているか確認してください
   - WiFi接続が正しく設定されているか確認してください
   - ブラウザのキャッシュをクリアしてみてください

2. **P2/P3からデータが送信されない**
   - P2/P3が正常に起動しているか確認してください
   - センサーが正しく接続されているか確認してください
   - P2/P3をリセットしてみてください

3. **グラフにデータが表示されない**
   - データが正常に収集されているか確認してください
   - ブラウザを更新してみてください
   - 別の期間（1日、1週間、1ヶ月）を選択してみてください
   - P2/P3のチェックボックスが選択されているか確認してください

4. **CO2の測定値が異常**
   - MH-Z19Cセンサーが正しく接続されているか確認してください
   - センサーのウォームアップ時間（30秒）が経過しているか確認してください
   - P2/P3をリセットしてみてください

5. **システム全体がフリーズする**
   - P1、P2、P3の全てを再起動してください
   - P1のログファイル（/var/log/）を確認してエラーを特定してください

## 更新履歴

- **Ver4.0**
  - P3センサーノードのサポートを追加
  - P2とP3のデータを同時に表示・比較する機能を追加
  - 絶対湿度の計算と表示機能を追加
  - データ保存構造を改良（RawData_P2とRawData_P3ディレクトリ）
  - グラフ表示のトグル機能を追加

- **Ver3.5**
  - MH-Z19C CO2センサーのサポートを追加
  - グラフのY軸範囲を柔軟に調整可能に変更
  - "LoadingGraph"の問題を修正
  - リアルタイム信号強度表示を追加

- **Ver3.2**
  - データ送信の再試行機能を追加（最大5回）
  - エラー時のログ出力を改善
  - リセット機能の安全性を向上

- **Ver3.1**
  - WiFi接続の安定性を向上
  - 起動時のディレイを追加
  - LEDインジケーターの機能を改善
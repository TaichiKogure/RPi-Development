# Raspberry Pi 5とPico 2Wスタンドアロン環境データ測定システム
# インストールガイド（BME680専用モード）
## バージョン2.0

## 概要

このドキュメントでは、Raspberry Pi 5とPico 2Wスタンドアロン環境データ測定システムをBME680専用モード（バージョン2.0）でインストールおよびセットアップするための手順を提供します。このバージョンでは、システムはBME680センサーのみで動作し、CO2センサー（MH-Z19C）の機能は無効化されています。

## ハードウェア要件

### 中央ハブ（P1）
- Raspberry Pi 5（任意のモデル）
- MicroSDカード（16GB以上推奨）
- Raspberry Pi 5用電源
- オプション：USB WiFiドングル（インターネット接続用）

### センサーノード（P2-P6）
- Raspberry Pi Pico 2W（WiFi機能付き）
- BME680環境センサー
- 電源用Micro USBケーブル
- センサー接続用ジャンパーワイヤー

## ハードウェアセットアップ

### BME680センサーのPico 2Wへの接続

BME680センサーをRaspberry Pi Pico 2Wに以下のように接続します：

| BME680ピン | Pico 2Wピン |
|------------|-------------|
| VCC        | 3.3V（ピン36） |
| GND        | GND（ピン38） |
| SCL        | GP1（ピン2） |
| SDA        | GP0（ピン1） |

![BME680接続図](../images/bme680_connection.png)

**注意**：画像は参考用です。実際の画像が利用できない場合は、上記のピン接続表を参照してください。

## ソフトウェアインストール

### P1（Raspberry Pi 5）のセットアップ

1. **MicroSDカードの準備**：
   - [Raspberry Piウェブサイト](https://www.raspberrypi.org/software/operating-systems/)から最新のRaspberry Pi OS（LiteまたはDesktop）をダウンロード
   - Raspberry Pi ImagerまたはRaspberry Pi OSイメージをMicroSDカードに書き込むための同様のツールを使用
   - MicroSDカードをRaspberry Pi 5に挿入

2. **初期設定**：
   - Raspberry Pi 5をモニター、キーボード、電源に接続
   - Raspberry Piを起動し、初期設定（ユーザー名、パスワード、ロケールなどの設定）を完了
   - 初期設定のためにインターネットに接続（イーサネットまたはWiFi経由）

3. **システムの更新**：
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```

4. **必要なパッケージのインストール**：
   ```bash
   sudo apt install -y python3-pip python3-venv hostapd dnsmasq git
   ```

5. **仮想環境のセットアップ**：
   ```bash
   cd ~
   python3 -m venv envmonitor-venv
   source envmonitor-venv/bin/activate
   pip install flask flask-socketio pandas plotly
   ```

6. **リポジトリのクローン**：
   ```bash
   git clone https://github.com/yourusername/RaspPi5_APconnection.git
   cd RaspPi5_APconnection/Ver2.00zeroOne
   ```

   または、ローカルコピーからインストールする場合：
   ```bash
   cd /path/to/RaspPi5_APconnection/Ver2.00zeroOne
   ```

7. **アクセスポイントの設定**：
   ```bash
   cd p1_software_Zero/ap_setup
   sudo python3 P1_ap_setup_solo.py --configure
   ```

   これにより、Raspberry Pi 5が以下のデフォルト設定でWiFiアクセスポイントとして設定されます：
   - SSID：RaspberryPi5_AP_Solo2
   - パスワード：raspberry
   - IPアドレス：192.168.0.2

8. **データディレクトリの作成**：
   ```bash
   sudo mkdir -p /var/lib(FromThonny)/raspap_solo/data
   sudo mkdir -p /var/lib(FromThonny)/raspap_solo/data/RawData_P2
   sudo mkdir -p /var/lib(FromThonny)/raspap_solo/data/RawData_P3
   sudo mkdir -p /var/lib(FromThonny)/raspap_solo/data/RawData_P4
   sudo mkdir -p /var/lib(FromThonny)/raspap_solo/data/RawData_P5
   sudo mkdir -p /var/lib(FromThonny)/raspap_solo/data/RawData_P6
   sudo chown -R pi:pi /var/lib(FromThonny)/raspap_solo
   ```

9. **自動起動の設定（オプション）**：
   起動時にシステムを自動的に起動するには、`/etc/rc.local`ファイルの`exit 0`行の前に以下を追加します：
   ```bash
   cd /path/to/RaspPi5_APconnection/Ver2.00zeroOne
   sudo -u pi /home/pi/envmonitor-venv/bin/python3 start_p1_solo.py &
   ```

### P2-P6（Raspberry Pi Pico 2W）のセットアップ

1. **開発用コンピュータにThonny IDEをインストール**：
   - [thonny.org](https://thonny.org/)からThonnyをダウンロードしてインストール

2. **Pico 2Wの準備**：
   - Pico 2WをUSB経由でコンピュータに接続
   - Thonny IDEを開く
   - ツール > オプション > インタープリタに移動
   - インタープリタとして「MicroPython（Raspberry Pi Pico）」を選択
   - 「ファームウェアのインストールまたは更新」をクリック
   - 指示に従ってPico 2WにMicroPythonをインストール

3. **必要なライブラリのインストール**：
   - Thonnyで新しいファイルを作成し、以下のコードを貼り付け：
     ```python
     import network
     import urequests
     import time
     print("ライブラリテスト成功")
     ```
   - ファイルをPico 2Wに`test_libraries.py`として保存
   - ファイルを実行して、必要なライブラリが利用可能であることを確認

4. **センサーノードソフトウェアのアップロード**：
   - Thonnyで「ファイル > 開く」に移動
   - `P2_software_debug`ディレクトリ（またはセットアップするデバイスに応じてP3、P4など）に移動
   - すべてのファイルとディレクトリをディレクトリ構造を維持したままPico 2Wにアップロード

5. **デバイスIDの設定**：
   - Pico 2Wの`main.py`ファイルを開く
   - `DEVICE_ID`変数（約70行目付近）を見つける
   - 適切なデバイスID（P2、P3、P4、P5、またはP6）に設定
   - ファイルを保存

6. **WiFi設定の構成**：
   - 同じ`main.py`ファイルで、WiFi設定がP1の設定と一致することを確認：
     ```python
     WIFI_SSID = "RaspberryPi5_AP_Solo2"
     WIFI_PASSWORD = "raspberry"
     SERVER_IP = "192.168.0.2"
     SERVER_PORT = 5000
     ```
   - ファイルを保存

7. **セットアップのテスト**：
   - Pico 2Wがまだコンピュータに接続されている状態で、Thonnyで`main.py`ファイルを実行
   - BME680センサーが検出され初期化されることを確認
   - Pico 2WがP1のWiFiアクセスポイントに接続できることを確認
   - データがP1に送信されていることを確認

8. **センサーノードの配置**：
   - Pico 2Wをコンピュータから切断
   - Micro USB経由で電源に接続
   - Pico 2Wは起動時に自動的に`main.py`ファイルを実行

9. **他のセンサーノードについても繰り返す**：
   - 各Pico 2Wデバイス（P2、P3、P4、P5、P6）について手順2〜8を繰り返す

## システム検証

すべてのコンポーネントをセットアップした後、システムが正しく動作していることを確認します：

1. **P1サービスの確認**：
   ```bash
   cd /path/to/RaspPi5_APconnection/Ver2.00zeroOne
   python3 start_p1_solo.py --status
   ```

   これにより、すべてのサービス（アクセスポイント、データ収集、Webインターフェース、接続モニター）が実行中であることが表示されるはずです。

2. **データ収集の確認**：
   ```bash
   ls -la /var/lib(FromThonny)/raspap_solo/data/RawData_P2/
   ```

   各センサーノード用のCSVファイルが作成されていることが確認できるはずです。

3. **Webインターフェースへのアクセス**：
   - デバイス（スマートフォン、タブレット、ラップトップ）をP1のWiFiネットワークに接続
   - Webブラウザを開き、http://192.168.0.2 にアクセス
   - ダッシュボードが読み込まれ、センサーノードからのデータが表示されることを確認

## トラブルシューティング

### P1（Raspberry Pi 5）の問題

1. **アクセスポイントが機能しない**：
   - hostapdとdnsmasqサービスを確認：
     ```bash
     sudo systemctl status hostapd
     sudo systemctl status dnsmasq
     ```
   - 実行されていない場合は、再起動を試みる：
     ```bash
     sudo systemctl restart hostapd
     sudo systemctl restart dnsmasq
     ```

2. **データ収集が機能しない**：
   - データ収集サービスが実行中かどうかを確認：
     ```bash
     cd /path/to/RaspPi5_APconnection/Ver2.00zeroOne
     python3 start_p1_solo.py --status
     ```
   - 実行されていない場合は、手動で起動：
     ```bash
     cd /path/to/RaspPi5_APconnection/Ver2.00zeroOne
     python3 start_p1_solo.py
     ```

3. **Webインターフェースにアクセスできない**：
   - Webインターフェースサービスが実行中かどうかを確認：
     ```bash
     cd /path/to/RaspPi5_APconnection/Ver2.00zeroOne
     python3 start_p1_solo.py --status
     ```
   - 実行されていない場合は、手動で起動：
     ```bash
     cd /path/to/RaspPi5_APconnection/Ver2.00zeroOne
     python3 start_p1_solo.py
     ```

### P2-P6（Raspberry Pi Pico 2W）の問題

1. **BME680センサーが検出されない**：
   - Pico 2WとBME680センサー間の物理的な接続を確認
   - I2Cアドレスが正しいことを確認（通常は0x76または0x77）
   - 可能であれば別のBME680センサーを試す

2. **WiFi接続の問題**：
   - Pico 2WがP1のWiFiアクセスポイントの範囲内にあることを確認
   - WiFiの認証情報（SSID、パスワード）が正しいことを確認
   - 電源を切断して再接続することでPico 2Wをリセットしてみる

3. **データ送信の問題**：
   - SERVER_IPとSERVER_PORTの設定が正しいことを確認
   - P1のデータ収集サービスが実行中であることを確認
   - Pico 2Wの出力にエラーメッセージがないか確認（デバッグのためにThonnyに接続）

## 追加リソース

- [Raspberry Piドキュメント](https://www.raspberrypi.org/documentation/)
- [MicroPythonドキュメント](https://docs.micropython.org/)
- [BME680データシート](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme680-ds001.pdf)

## サポート

システムに関する技術的なサポートや質問については、システム管理者に連絡するか、システムに付属のドキュメントを参照してください。

---

*このドキュメントは、Raspberry Pi 5とPico 2Wスタンドアロン環境データ測定システムのドキュメントセット、バージョン2.0の一部です。*
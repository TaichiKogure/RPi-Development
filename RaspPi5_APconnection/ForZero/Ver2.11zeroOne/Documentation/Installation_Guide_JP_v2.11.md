# インストールガイド Ver2.11（ZeroOne 系）

本ドキュメントは、Raspberry Pi 5（P1）を中心としたスタンドアロン環境計測システムのインストール手順を初心者向けに説明します。Ver2.11 では P1 自身にも BME680 を接続し、P2/P3 と同様に計測・保存・可視化できるようになりました。

## 1. 構成概要
- P1（Raspberry Pi 5）
  - Wi-Fi AP/集約サーバ
  - Web UI 提供
  - 新規：BME680 を I2C 接続して自機で計測（気温・相対湿度・絶対湿度・気圧・ガス抵抗）
- P2/P3（Raspberry Pi Pico 2W）
  - BME680 を搭載し、P1 へ送信（既存構成）

データ保存先（既定）
- /var/lib(FromThonny)/raspap_solo/data/RawData_P1/P1_fixed.csv（最新追記）
- /var/lib(FromThonny)/raspap_solo/data/RawData_P1/P1_YYYY-MM-DD.csv（日付別）

## 2. ハードウェア接続（P1 の BME680）
- VCC → 3.3V
- GND → GND
- SCL → GPIO3 (I2C SCL, ピン5)
- SDA → GPIO2 (I2C SDA, ピン3)
- I2C アドレスは 0x77 → 0x76 の順で自動検出します。

## 3. OS 側の準備
- I2C を有効化（raspi-config → Interface Options → I2C 有効）
- 推奨：仮想環境を作成
  - python3 -m venv envmonitor-venv
  - source envmonitor-venv/bin/activate
- 必要パッケージ（Web/UI 側）
  - pip install flask pandas plotly requests
- P1 BME680 リーダ用
  - pip install smbus2

## 4. ソフトウェア配置（本リポジトリ）
- 作業ディレクトリ：G:\RPi-Development\RaspPi5_APconnection\ForZero\Ver2.11zeroOne
- 主要追加ファイル：
  - p1_software_Zero/data_collection/p1_bme680_reader.py（P1 センサー取得）
  - p1_software_Zero/web_interface/config.py（RawData_P1 追加）
  - p1_software_Zero/data_collection/config.py（RawData_P1 追加）
  - web_interface のデータ/グラフ生成は P1 を含む形式に拡張

## 5. 起動手順（最小）
1) 仮想環境を有効化
2) P1 センサー取得（常駐実行）
   - python3 p1_software_Zero/data_collection/p1_bme680_reader.py --interval 10
3) データ収集・Web UI（既存の起動スクリプトに準じて起動）
4) ブラウザから P1 の IP にアクセスし、グラフ（/api/graphs）や最新値を確認

## 6. トラブルシューティング
- センサー初期化失敗：配線/I2C 有効化/アドレス（0x76/0x77）を確認
- CSV が作られない：権限と /var/lib(FromThonny)/raspap_solo/data の存在確認
- Web で P1 が出ない：/api/graphs のレスポンスに P1 キーが含まれるか確認

以上

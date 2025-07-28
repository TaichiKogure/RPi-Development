# Raspberry Pi 5 環境データ測定システム Ver4.5

## 概要

このリポジトリには、Raspberry Pi 5 (P1) を中心とした環境データ測定システムのバージョン4.5が含まれています。このシステムは、Raspberry Pi Pico 2W デバイス (P2, P3) からの環境データを収集し、可視化するためのものです。

## Ver4.5の新機能

Ver4.5では、以下の新機能が追加されました：

- **リアルタイムセンサー値の表示**: P2とP3からのセンサーデータをリアルタイムで数値表示
- **グラフ保存機能**: 表示中のグラフをHTML形式で保存可能
- **拡張された時間範囲選択**: 1日、3日、1週間、3ヶ月、6ヶ月、1年、すべてのデータから選択可能
- **30秒ごとのグラフ自動更新**: より頻繁なデータ更新
- **10秒ごとの接続状態更新**: P2とP3の接続状態をより頻繁に更新
- **グラフ更新のキャンセル機能**: 長時間のグラフ更新をキャンセル可能
- **更新中の進行状況表示**: グラフ更新の進行状況を視覚的に表示

## ディレクトリ構造

```
Ver4.5/
├── documentation/           # ドキュメント
│   └── 操作マニュアル.md     # 操作マニュアル
├── p1_software_solo45/      # P1 (Raspberry Pi 5) 用ソフトウェア
│   ├── ap_setup/            # アクセスポイント設定
│   ├── connection_monitor/  # 接続モニター
│   ├── data_collection/     # データ収集
│   ├── web_interface/       # Webインターフェース
│   └── start_p1_solo45.py   # 統合起動スクリプト
├── P2_software_solo45/      # P2 (Pico 2W) 用ソフトウェア
│   ├── error_handling/      # エラー処理
│   ├── sensor_drivers/      # センサードライバー
│   ├── wifi_client/         # WiFiクライアント
│   └── main.py              # メインスクリプト
└── P3_software_solo45/      # P3 (Pico 2W) 用ソフトウェア
    ├── error_handling/      # エラー処理
    ├── sensor_drivers/      # センサードライバー
    ├── wifi_client/         # WiFiクライアント
    └── main.py              # メインスクリプト
```

## インストール方法

### P1 (Raspberry Pi 5) へのインストール

1. 仮想環境を作成し、必要なパッケージをインストールします：

```bash
cd ~
python3 -m venv envmonitor-venv
source envmonitor-venv/bin/activate
pip install flask flask-socketio pandas plotly requests
```

2. このリポジトリをRaspberry Pi 5にクローンまたはコピーします：

```bash
cd ~
git clone https://github.com/yourusername/RaspPi5_APconnection.git
```

または、USBドライブなどを使用してファイルを転送します。

3. データディレクトリを作成します：

```bash
sudo mkdir -p /var/lib(FromThonny)/raspap_solo/data/RawData_P2
sudo mkdir -p /var/lib(FromThonny)/raspap_solo/data/RawData_P3
sudo chown -R pi:pi /var/lib(FromThonny)/raspap_solo
```

4. システムを起動します：

```bash
cd ~/RaspPi5_APconnection/Ver4.5/p1_software_solo45
sudo ~/envmonitor-venv/bin/python3 start_p1_solo45.py
```

### P2/P3 (Raspberry Pi Pico 2W) へのインストール

1. Thonnyを使用して、P2_software_solo45またはP3_software_solo45ディレクトリ内のファイルをPico 2Wにコピーします。

2. main.pyを実行して、センサーデータの収集と送信を開始します。

## 使用方法

システムが起動したら、以下のURLでWebインターフェースにアクセスできます：

```
http://192.168.0.1
```

このURLは、P1のアクセスポイントに接続されたデバイス（スマートフォン、タブレット、PC等）から利用できます。

詳細な使用方法については、[操作マニュアル](documentation/操作マニュアル.md)を参照してください。

## トラブルシューティング

### P1の問題

- **サービスが起動しない場合**: ログファイル（/var/log/p1_startup_solo45.log）を確認してください。
- **Webインターフェースにアクセスできない場合**: P1のIPアドレスが192.168.0.1であることを確認してください。
- **データが表示されない場合**: データ収集サービスが正常に動作しているか確認してください。

### P2/P3の問題

- **センサーデータが送信されない場合**: Pico 2WがP1のアクセスポイントに接続されているか確認してください。
- **センサーエラーが発生する場合**: センサーの接続を確認してください。
- **WiFi接続エラーが発生する場合**: WiFi設定が正しいか確認してください。

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細については、LICENSEファイルを参照してください。

## 謝辞

このプロジェクトは、以下のライブラリとツールを使用しています：

- Flask: Webアプリケーションフレームワーク
- Pandas: データ分析ライブラリ
- Plotly: インタラクティブなグラフ作成ライブラリ
- Bootstrap: CSSフレームワーク
- jQuery: JavaScriptライブラリ
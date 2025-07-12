# Raspberry Pi 5 と Pico 2W による環境データ測定システム Ver4.44

## 概要

このシステムは、Raspberry Pi 5（P1）を中心ハブとし、2台のRaspberry Pi Pico 2W（P2、P3）をセンサーノードとして使用する環境データ測定システムです。システムは温度、湿度、気圧、ガスパラメータ、CO2濃度などの環境データを収集し、可視化して分析のために保存します。

Ver4.44では、すべてのコンポーネントを一度に起動できる統合起動スクリプト（`start_p1_solo44.py`）が導入され、ファイル名に「44」サフィックスが追加されています。また、日本語のドキュメントが充実し、システムの理解と操作が容易になっています。

## 主な機能

- P1（Raspberry Pi 5）がWiFiアクセスポイントとして機能し、P2とP3を接続
- BME680センサーによる温度、湿度、気圧、ガスパラメータの測定
- MH-Z19Bセンサーによる二酸化炭素（CO2）濃度の測定
- Webインターフェースによるデータの可視化（グラフ表示）
- P2とP3の接続状態のリアルタイム監視
- データのCSVエクスポート機能
- 自動再起動機能によるシステムの安定性向上

## ディレクトリ構成

```
RaspPi5_APconnection\Ver4.44\
├── p1_software_solo44\              # Raspberry Pi 5用ソフトウェア
│   ├── ap_setup\                    # アクセスポイント設定
│   │   └── P1_ap_setup_solo44.py    # APセットアップスクリプト
│   ├── data_collection\             # P2とP3からのデータ収集
│   │   └── P1_data_collector_solo44.py # データ収集スクリプト
│   ├── web_interface\               # データ可視化用WebUI
│   │   └── P1_app_simple44.py       # Webアプリケーション
│   ├── connection_monitor\          # WiFi信号監視
│   │   └── P1_wifi_monitor_solo44.py # 接続モニタリングスクリプト
│   └── start_p1_solo44.py           # 統合起動スクリプト
└── documentation\                   # ユーザーマニュアルとガイド
    ├── システム概要.md               # システム概要
    ├── インストールガイド.md         # インストール手順
    ├── 操作マニュアル.md             # 操作手順
    └── トラブルシューティング.md     # 問題解決ガイド
```

## ドキュメント

詳細な情報は以下のドキュメントを参照してください：

- [システム概要](documentation/システム概要.md) - システムの全体像と主要コンポーネントの説明
- [インストールガイド](documentation/インストールガイド.md) - システムのインストールと初期設定の手順
- [操作マニュアル](documentation/操作マニュアル.md) - システムの操作方法と機能の説明
- [トラブルシューティング](documentation/トラブルシューティング.md) - 一般的な問題の解決方法

## クイックスタート

1. Raspberry Pi 5で仮想環境を有効化します：
   ```bash
   source ~/envmonitor-venv/bin/activate
   ```

2. 統合起動スクリプトを実行します：
   ```bash
   cd ~/RaspPi5_APconnection/Ver4.44/p1_software_solo44
   sudo ~/envmonitor-venv/bin/python3 start_p1_solo44.py
   ```

3. P2とP3のRaspberry Pi Pico 2Wに電源を接続します。

4. スマートフォンやPCをP1のアクセスポイント（SSID: RaspberryPi5_AP_Solo）に接続します。

5. WebブラウザでP1のWebインターフェース（http://192.168.0.1）にアクセスします。

## 注意事項

- このシステムはRaspberry Pi 5とRaspberry Pi Pico 2Wの特性を活用して設計されています。他のハードウェアでは正常に動作しない場合があります。
- P1はroot権限で実行する必要があります（`sudo`を使用）。
- P2とP3は適切な電源（5V）で動作させる必要があります。
- 長期間のデータ収集を行う場合は、定期的にデータのバックアップを行ってください。

## バージョン情報

- Ver4.44 - 2025年7月
  - 統合起動スクリプトの導入
  - ファイル名に「44」サフィックスを追加
  - 日本語ドキュメントの充実
  - 軽量化とメンテナンス性の向上
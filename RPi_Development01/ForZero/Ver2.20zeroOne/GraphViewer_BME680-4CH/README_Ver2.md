# DataViewerVer2（AP対応）

Raspberry Pi をアクセスポイント（AP）化した状態で、外部スマートフォン等から環境データのグラフを閲覧できる簡易ビューアです。

- バージョン: Ver2
- Webアクセス: `http://192.168.0.2:8081/`
- 対応デバイス: P1, P2, P3, P4（CO2なし、BME680のみ）
- 参照CSV:
  - `/var/lib(FromThonny)/raspap_solo/data/RawData_P1/P1_fixed.csv`
  - `/var/lib(FromThonny)/raspap_solo/data/RawData_P2/P2_fixed.csv`
  - `/var/lib(FromThonny)/raspap_solo/data/RawData_P3/P3_fixed.csv`
  - `/var/lib(FromThonny)/raspap_solo/data/RawData_P4/P4_fixed.csv`

## 1. 事前準備（仮想環境）
Raspberry Pi 上で下記の仮想環境を作成してから実行してください。

```bash
python3 -m venv ~/envmonitor-venv
source ~/envmonitor-venv/bin/activate
pip install flask pandas plotly
```

（既に `envmonitor-venv` がある場合は、`source ~/envmonitor-venv/bin/activate` のみでOK）

## 2. 起動方法（推奨ランチャ）
本フォルダにあるランチャスクリプト `start_data_viewer_ver2.py` を使用すると、ポートやパスの指定なしで起動できます。

```bash
cd ~/RPi_Development01/ForZero/Ver2.20zeroOne/GraphViewer_BME680-4CH
sudo ~/envmonitor-venv/bin/python3 start_data_viewer_ver2.py
```

- サーバは `0.0.0.0:8081` で待受けします（AP配下からアクセス可能）。
- スマホを AP（例: RaspberryPi5_AP_Solo2 など）に接続し、ブラウザで `http://192.168.0.2:8081/` を開きます。

## 3. 直接実行（オプション）
`DataViewerVer1.py` を直接実行しても同等に動作します。必要に応じてパラメータを指定してください。

```bash
sudo ~/envmonitor-venv/bin/python3 DataViewerVer1.py \
  --port 8081 \
  --p1-path /var/lib(FromThonny)/raspap_solo/data/RawData_P1/P1_fixed.csv \
  --p2-path /var/lib(FromThonny)/raspap_solo/data/RawData_P2/P2_fixed.csv \
  --p3-path /var/lib(FromThonny)/raspap_solo/data/RawData_P3/P3_fixed.csv \
  --p4-path /var/lib(FromThonny)/raspap_solo/data/RawData_P4/P4_fixed.csv \
  --days 1
```

## 4. 画面の使い方
- Days（1/7/30）で表示期間を切り替え
- P1〜P4 のチェックで表示ON/OFF
- グラフは10秒ごとに自動更新
- `/download/p1` 等で各CSVをダウンロード可能

## 5. トラブルシュート
- 画面にデータが出ない場合：該当 `*_fixed.csv` が存在するか、権限があるかを確認
- ポート競合：8081が使用中の場合は `DataViewerVer1.py --port 8082` 等に変更
- 依存モジュール：`flask, pandas, plotly` が仮想環境にインストールされているか確認

## 6. 自動起動（任意）
必要なら systemd サービス化してブート時に自動起動できます（例）：

```
[Unit]
Description=DataViewerVer2 (AP Graph Viewer)
After=network.target

[Service]
ExecStart=/home/pi/envmonitor-venv/bin/python3 /home/pi/RaspPi5_APconnection/ForZero/Ver2.20zeroOne/GraphViewer_BME680-4CH/start_data_viewer_ver2.py
Restart=always
User=root

[Install]
WantedBy=multi-user.target
```

`/etc/systemd/system/dataviewer-ver2.service` に保存し、以下で有効化:

```bash
sudo systemctl daemon-reload
sudo systemctl enable dataviewer-ver2.service
sudo systemctl start dataviewer-ver2.service
```

---
本ビューアは AP 化された P1（Zero/Zero2W など想定）での「外部スマホからの閲覧」を想定しています。AP の IP を 192.168.0.2 に設定し、スマホを同一APに接続してご利用ください。
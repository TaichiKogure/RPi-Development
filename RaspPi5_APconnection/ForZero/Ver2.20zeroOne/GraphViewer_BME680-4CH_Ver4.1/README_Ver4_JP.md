# DataViewer Ver4 （ダークテーマ + 任意日数 + 最小/最大テーブル）

本ビューアは Ver3 をベースに、名称を「Ver4」に統一し、UI をダーク＆モダンに刷新したバージョンです。

## 変更点（Ver3 → Ver4）
- 名称を「DataViewer Ver4」に統一（画面タイトルとロガー名を変更）
- ダークテーマのスタイルを導入（フォント/背景/パネル/罫線などを調整）
  - 既存のグラフ線の色（トレースカラー）は変更しない方針
- 自動更新（auto-refresh）を廃止
  - 代わりに「Reload」ボタンで任意タイミングに読み直し
- 表示期間の指定を「任意日数（数値入力）」に変更（1 以上の整数）
- 表示範囲（期間・デバイス）に基づく各パラメータの **最小値/最大値テーブル** をグラフ下に追加
- CSV ダウンロードは Ver3 と同等に維持（現在の期間・デバイス選択に合わせて生成）

## ファイル構成
- `DataViewerVer4.py` … Flask + Plotly の本体（Ver4 新規）
- `start_data_viewer_ver4.py` … 起動ランチャ（オプション）
- `README_Ver4_JP.md` … このファイル

配置場所：
```
RaspPi5_APconnection/ForZero/Ver2.20zeroOne/GraphViewer_BME680-4CH_Ver3/
```

## データソース（固定 CSV）
- `/var/lib(FromThonny)/raspap_solo/data/RawData_P1/P1_fixed.csv`
- `/var/lib(FromThonny)/raspap_solo/data/RawData_P2/P2_fixed.csv`
- `/var/lib(FromThonny)/raspap_solo/data/RawData_P3/P3_fixed.csv`
- `/var/lib(FromThonny)/raspap_solo/data/RawData_P4/P4_fixed.csv`

CSV フォーマット（例）：
```
2025-08-23 15:07:25,P2,30.78,36.22,999.7605,12201,11.45
# 列順: timestamp, device_id, temperature, humidity, pressure, gas_resistance, absolute_humidity
```
- timestamp は文字列/UNIX 秒どちらでも可（プログラム内で自動判定して `datetime` 変換）

## インストール（仮想環境）
Raspberry Pi 上で：
```bash
python3 -m venv ~/envmonitor-venv
source ~/envmonitor-venv/bin/activate
pip install flask pandas plotly
```

## 起動方法
### 1) ランチャを使う（推奨）
```bash
cd ~/RaspPi5_APconnection/ForZero/Ver2.20zeroOne/GraphViewer_BME680-4CH_Ver3
sudo ~/envmonitor-venv/bin/python3 start_data_viewer_ver4.1.py
```
- 既定ポート: `8081`
- 既定バインド: `192.168.0.2`

### 2) 直接起動する
```bash
sudo ~/envmonitor-venv/bin/python3 DataViewerVer4.1.py \
  --port 8081 \
  --p1-path /var/lib(FromThonny)/raspap_solo/data/RawData_P1/P1_fixed.csv \
  --p2-path /var/lib(FromThonny)/raspap_solo/data/RawData_P2/P2_fixed.csv \
  --p3-path /var/lib(FromThonny)/raspap_solo/data/RawData_P3/P3_fixed.csv \
  --p4-path /var/lib(FromThonny)/raspap_solo/data/RawData_P4/P4_fixed.csv \
  --days 1
```

## 使い方
- 表示期間(Days): 数値で任意の日数を指定（1 日以上）
- P1〜P4: 表示するデバイスをチェックで ON/OFF
- Reload: 現在の設定でグラフを再読み込み（自動更新はありません）
- CSVダウンロード（表示期間・デバイス反映）: 現在の条件で各パラメータの `timestamp,param` CSV を生成
- 固定CSVダウンロード: `*_fixed.csv` をそのままダウンロード
- 最小/最大テーブル: 現在の期間・デバイスに含まれる値から **クライアント側で計算** した結果を表示

## トラブルシュート
- データが表示されない:
  - 該当 `*_fixed.csv` の存在と読み取り権限を確認
  - timestamp 列が正しくフォーマットされているか確認（文字列/UNIX 秒は自動判定）
- ポート競合: `--port` で変更可
- ホスト IP を変えたい: `DataViewerVer4.py` の `app.run(host=...)` を調整

## バージョンポリシー
- Ver3 はそのまま残し、Ver4 を別ファイルとして共存させています
- 段階的に Ver4 へ移行可能です

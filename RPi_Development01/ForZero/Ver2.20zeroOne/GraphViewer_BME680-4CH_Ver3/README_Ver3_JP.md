# DataViewer Ver3 （CSVダウンロード + 不快指数 + 大気汚染プロキシ）

本ビューアは Ver2/Ver2.1 を拡張した Ver3 です。ブラウザで環境データの時系列グラフを表示し、
以下の機能を追加しています。

- 各グラフ（パラメータ）ごとの CSV ダウンロード（オンザフライ生成）
- 不快指数（Discomfort Index）の計算・表示（温度・湿度から算出）
- ガス抵抗・温度・湿度から導出する大気汚染プロキシ指標を複数表示
  - pollution_index1 = 1e6 / gas_resistance（単純逆数プロキシ）
  - pollution_index2 = pollution_index1 * (1 + (RH - 50)/100)（湿度補正）
  - pollution_index3 = pollution_index1 * exp(α*(T-25))（温度補正、α=0.02）

> 注意：これらの「大気汚染プロキシ」は一般的な IAQ の近似指標であり、校正された空気質指数（AQI）
> ではありません。相対的な変動傾向の把握を目的とした参考値です。

---

## 1. ファイル構成

- `DataViewerVer1_v3.py`
  - Flask アプリ本体。`/api/graphs` で時系列データ（P1〜P4）を返し、
    追加パラメータ（不快指数・汚染プロキシ）を含めます。
  - `/download/series?device=P2&param=discomfort_index&days=7` のように各パラメータの
    CSV をオンザフライで生成しダウンロードできます。
  - `/download/p1` 〜 `/download/p4` は従来通り固定 CSV をそのまま送信します。

- `start_data_viewer_ver3.py`
  - 起動ランチャ。AP 側 IP の `192.168.0.2:8081` で待受。

- `README_Ver3_JP.md`（このファイル）

---

## 2. データソース（固定 CSV）

- `/var/lib(FromThonny)/raspap_solo/data/RawData_P1/P1_fixed.csv`
- `/var/lib(FromThonny)/raspap_solo/data/RawData_P2/P2_fixed.csv`
- `/var/lib(FromThonny)/raspap_solo/data/RawData_P3/P3_fixed.csv`
- `/var/lib(FromThonny)/raspap_solo/data/RawData_P4/P4_fixed.csv`

CSV 形式（例）：
```
2025-08-23 15:07:25,P2,30.778436,36.218988,999.7605,12201,11.45
```
列順：`timestamp, device_id, temperature, humidity, pressure, gas_resistance, absolute_humidity`

タイムスタンプは文字列/UNIX 秒のどちらでも受け入れます（自動判定・変換）。

---

## 3. 新規追加パラメータの理論（簡易）

### 3.1 不快指数（Discomfort Index）
一般的な近似式：
```
DI = T - 0.55 * (1 - RH/100) * (T - 14.5)
```
- `T`：気温（°C）
- `RH`：相対湿度（%）

目安（文献によって異なる）：
- 68 未満：不快感は少ない
- 68〜75：やや不快
- 75 以上：多くの人が不快

### 3.2 大気汚染プロキシ（Heuristic）
BME680 のガス抵抗は一般に空気質の変化（VOC 等）で変動します。
ここでは相対的な変化を見るための簡易指標を 3 種用意しました。

1) `pollution_index1 = 1e6 / gas_resistance`
   - ガス抵抗値の逆数（スケーリング 1e6）
2) `pollution_index2 = pollution_index1 * (1 + (RH - 50)/100)`
   - 湿度が高いと指標が上ぶれる（例示）
3) `pollution_index3 = pollution_index1 * exp(α*(T-25))`（α=0.02）
   - 25°C を基準に温度変動の影響を付与

> 再度の注意：これらは校正された AQI ではなく **傾向を見るための便宜的なプロキシ** です。

---

## 4. インストール（仮想環境）

Raspberry Pi 上で以下を準備してください：

```bash
python3 -m venv ~/envmonitor-venv
source ~/envmonitor-venv/bin/activate
pip install flask pandas plotly
```

---

## 5. 起動方法

推奨ランチャを使用：

```bash
cd ~/RPi_Development01/ForZero/Ver2.20zeroOne/GraphViewer_BME680-4CH_Ver3
sudo ~/envmonitor-venv/bin/python3 start_data_viewer_ver3.py
```

- AP 側 `192.168.0.2:8081` で待受。
- スマホを AP に接続し、ブラウザで `http://192.168.0.2:8081/` を開きます。

`DataViewerVer1_v3.py` を直接起動する場合：
```bash
sudo ~/envmonitor-venv/bin/python3 DataViewerVer1_v3.py \
  --port 8081 \
  --p1-path /var/lib(FromThonny)/raspap_solo/data/RawData_P1/P1_fixed.csv \
  --p2-path /var/lib(FromThonny)/raspap_solo/data/RawData_P2/P2_fixed.csv \
  --p3-path /var/lib(FromThonny)/raspap_solo/data/RawData_P3/P3_fixed.csv \
  --p4-path /var/lib(FromThonny)/raspap_solo/data/RawData_P4/P4_fixed.csv \
  --days 1
```

---

## 6. 画面の使い方

- Days（1/7/30）で表示期間を切り替え
- P1〜P4 のチェックで表示 ON/OFF
- 追加グラフ：Discomfort Index / Pollution Index 1〜3
- 自動更新：10 秒毎（`--refresh` で変更可）
- ダウンロード：画面上部のリンク群から、**現在の表示期間・デバイス選択**に合わせて
  `timestamp,param` の CSV をダウンロード可能
  - 例：`/download/series?device=P2&param=discomfort_index&days=7`

---

## 7. トラブルシュート

- データが表示されない：該当 `*_fixed.csv` が存在するか、読み取り権限があるか確認
- 1970/2000 年などおかしな日時：CSV の timestamp 列が文字列/UNIX 秒かを確認。
  本アプリは自動判定で `pd.to_datetime` により変換しますが、値が不正な場合は NaT 除外となります。
- ポート競合：`--port` で変更可。80 番に出したい場合は root 権限やリバースプロキシの利用を検討。

---

## 8. バージョン管理

- Ver2 / Ver2.1 はそのまま保持し、Ver3 は **別フォルダ** で共存します。
- 既存システムを壊さずに段階的移行・検証が可能です。

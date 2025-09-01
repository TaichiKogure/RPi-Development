# システムアーキテクチャ Ver2.11（ZeroOne 系）

## 1. 概要
Ver2.11 では、P1（Raspberry Pi 5）が自機 BME680 を読み取り、P2/P3 と同様にデータ保存・Web 可視化します。

## 2. ディレクトリ構成（抜粋）
- ForZero/Ver2.11zeroOne/
  - p1_software_Zero/
    - data_collection/
      - p1_bme680_reader.py  ← P1 ローカル BME680 リーダ
      - config.py            ← RawData_P1 を追加
    - web_interface/
      - api/routes.py        ← /api/graphs で P1 を含められるよう調整
      - data/data_manager.py ← P1 参照を追加
      - visualization/graph_generator.py ← P1 を含むグラフ用 JSON 生成
      - config.py            ← RawData_P1 を追加
  - Documentation/
    - Installation_Guide_JP_v2.11.md / EN_v2.11.md
    - System_Architecture_JP_v2.11.md / EN_v2.11.md
    - Operation_Manual_JP_v2.11.md / EN_v2.11.md

## 3. データフロー
1) P1: p1_bme680_reader.py が I2C で BME680 を読み取り、/var/lib(FromThonny)/raspap_solo/data/RawData_P1 に CSV を追記（fixed + 日付ファイル）
2) P2/P3: 既存の収集経路で RawData_P2 / RawData_P3 に蓄積
3) Web UI: /api/graphs → graph_generator.generate_graph_data() が P1/P2/P3 の CSV を読み、JSON を返す
4) フロントエンド: JSON を Plotly へ渡して描画

## 4. データスキーマ（CSV ヘッダ）
- 共通: timestamp, device_id, temperature, humidity, pressure, gas_resistance, co2, absolute_humidity
- P1 は CO2 を空欄（"") とし互換性を維持

## 5. 可視化
- グラフ API: /api/graphs?show_p1=true&show_p2=true&show_p3=true&days=1
- レスポンスはデバイスごと（P1/P2/P3）の時系列配列を含む JSON

## 6. 拡張ポイント
- 精度向上: BME680 の完全な補正計算ドライバを組み込む
- 接続監視: 必要に応じて P1 行をUI側に追加（現状は Wi-Fi 経路を持つ P2/P3 のみ）

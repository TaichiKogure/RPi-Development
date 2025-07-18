# 統合グラフ機能マニュアル (Ver 4.53 Uni)

## 概要

このドキュメントでは、Ver 4.53 Uniで統合されたグラフ表示機能の使用方法について説明します。統合版では、P1_app_simple45.pyとgraph_viewer.pyの機能を統合し、Webブラウザから192.168.0.1にアクセスするだけで、環境データのグラフを閲覧できるようになりました。

主な機能：
- センサーデータモニタとセンサー信号状態モニタの表示
- CSVファイルからのグラフ表示
- 自動更新モードと手動更新モードの切り替え
- 表示時間範囲の任意指定
- グラフの保存機能
- データのエクスポート機能

## インストール方法

統合版を使用するには、以下のファイルを使用します：

1. `P1_app_simple45_Uni.py` - 統合されたWebインターフェース
2. `start_p1_solo45_Uni.py` - 統合版の起動スクリプト

これらのファイルは、既存のファイルを置き換えるのではなく、別名で保存されています。

## 起動方法

統合版を起動するには、以下のコマンドを実行します：

```bash
sudo ~/envmonitor-venv/bin/python3 start_p1_solo45_Uni.py
```

このコマンドは、アクセスポイントのセットアップ、データ収集サービス、統合Webインターフェース、接続モニターを起動します。

## 使用方法

### Webインターフェースへのアクセス

ブラウザから `http://192.168.0.1` にアクセスすると、統合されたWebインターフェースが表示されます。

### センサーデータモニタ

画面上部には、P2とP3のセンサーデータが表示されます。各センサーノードの最新の測定値（気温、湿度、気圧、ガス抵抗、CO2濃度など）を確認できます。

### 接続状態モニタ

センサーデータモニタの下には、P2とP3の接続状態が表示されます。信号強度、ノイズレベル、SNR、Ping時間などの情報を確認できます。

### グラフ設定

グラフ設定セクションでは、以下の設定が可能です：

1. **P2/P3データの表示切替**：チェックボックスでP2とP3のデータ表示を個別に切り替えられます。
2. **期間選択**：1日、3日、1週間、1ヶ月、3ヶ月、6ヶ月、1年、またはすべてのデータから選択できます。

### グラフ更新モード

グラフ更新モードセクションでは、以下の設定が可能です：

1. **自動更新モード**：設定した間隔でグラフが自動的に更新されます。
   - 更新間隔は「自動更新間隔」ドロップダウンから選択できます（オフ、30秒、1分、5分、10分）。

2. **手動更新モード**：「グラフを更新」ボタンを押したときのみグラフが更新されます。

### グラフ表示

画面下部には、以下のパラメータのグラフが表示されます：

1. **気温**：気温の経時変化（°C）
2. **相対湿度**：相対湿度の経時変化（%）
3. **絶対湿度**：絶対湿度の経時変化（g/m³）
4. **CO2濃度**：CO2濃度の経時変化（ppm）
5. **気圧**：気圧の経時変化（hPa）
6. **ガス抵抗**：ガス抵抗の経時変化（Ω）

各グラフは、選択した期間とデバイス（P2/P3）に基づいて表示されます。

### データのエクスポート

「データをエクスポート」ボタンをクリックすると、エクスポートモーダルが表示されます。以下の設定が可能です：

1. **デバイス**：P2、P3、またはすべてのデータをエクスポートできます。
2. **期間**：開始日と終了日を指定できます。

設定後、「エクスポート」ボタンをクリックすると、CSVファイルがダウンロードされます。

### グラフの保存

「グラフを保存」ボタンをクリックすると、保存モーダルが表示されます。以下の設定が可能です：

1. **ファイル名**：保存するファイルの名前を指定できます。
2. **保存するグラフ**：保存するグラフを選択できます（気温、相対湿度、絶対湿度、CO2濃度、気圧、ガス抵抗、ダッシュボード）。

設定後、「保存」ボタンをクリックすると、選択したグラフがHTMLファイルとして保存され、ZIPファイルとしてダウンロードされます。

## トラブルシューティング

### グラフが表示されない場合

1. CSVファイルが正しく生成されているか確認してください。
   - P2のCSVファイル：`/var/lib/raspap_solo/data/RawData_P2/P2_fixed.csv`
   - P3のCSVファイル：`/var/lib/raspap_solo/data/RawData_P3/P3_fixed.csv`

2. ブラウザのコンソールでエラーメッセージを確認してください。

3. ログファイルを確認してください：
   - Webインターフェースのログ：`/var/log/web_interface_simple45_Uni.log`
   - 起動スクリプトのログ：`/var/log/p1_startup_solo45_Uni.log`

### サービスが起動しない場合

1. 仮想環境が正しく設定されているか確認してください：
   ```bash
   source ~/envmonitor-venv/bin/activate
   pip list
   ```

2. 必要なパッケージがインストールされているか確認してください：
   ```bash
   pip install flask flask-socketio pandas plotly
   ```

3. ログファイルでエラーメッセージを確認してください。

## 注意事項

- 統合版は、既存のファイルを置き換えるのではなく、別名で保存されています。元のファイルに戻したい場合は、元のファイルを使用してください。
- グラフの自動更新を有効にすると、サーバーの負荷が高くなる可能性があります。必要に応じて更新間隔を調整してください。
- 大量のデータを表示する場合（例：1年分のデータ）、グラフの読み込みに時間がかかる場合があります。
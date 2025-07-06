# Ver4.31 デバッグ - グラフ描画エラー修正

## 修正内容

### 問題点
グラフが描画されない問題が発生していました。主な原因は以下の通りです：

1. グラフ用データはあるが、`fig.data`にトレースが追加されていない
   - `create_time_series_graph()`内で`df_p2[parameter]`または`df_p3[parameter]`が全てNaNまたは空配列の場合、グラフオブジェクトは作られても描画対象がなく、「Error loading graphs」というエラーが表示されていました。

### 修正点

1. `create_time_series_graph()`メソッドに`fig.data`が空かどうかをチェックする処理を追加
   - トレースが追加されていない場合、明示的なエラーメッセージを返すようにしました。

2. 例外処理の改善
   - エラーが発生した場合、より詳細なエラー情報を提供するようにしました。

3. `create_dashboard_graphs()`メソッドの修正
   - パラメータごとのエラーを収集し、フロントエンドに伝えるようにしました。

4. `get_graphs()`関数の修正
   - エラー情報を適切なHTTPステータスコードと共に返すようにしました。

5. フロントエンドJavaScriptの修正
   - パラメータ固有のエラーを適切に表示するようにしました。
   - 一般的なエラーメッセージの表示を改善しました。

## 技術的な詳細

### バックエンド（Python）

1. `create_time_series_graph()`メソッド
   - `fig.data`が空の場合、エラーメッセージをJSON形式で返します。
   ```python
   if not fig.data:
       logger.warning(f"No valid data to plot for {parameter}")
       return json.dumps({"error": f"No valid data to plot for {parameter}"})
   ```
   - 例外処理も改善し、詳細なエラー情報を提供します。
   ```python
   except Exception as e:
       logger.error(f"Error creating graph for {parameter}: {e}")
       return json.dumps({"error": f"Graph creation failed: {e}"})
   ```

2. `create_dashboard_graphs()`メソッド
   - 各パラメータのグラフ生成時にエラーが発生した場合、それを収集します。
   - すべてのパラメータでエラーが発生した場合、エラー情報を返します。

3. `get_graphs()`関数
   - エラー情報がある場合、適切なHTTPステータスコードと共に返します。

### フロントエンド（JavaScript）

1. `loadGraphs()`関数
   - パラメータ固有のエラーを処理し、各グラフコンテナに表示します。
   - 一般的なエラーメッセージの表示を改善しました。

## 使用方法

この修正により、グラフが描画されない場合に具体的なエラーメッセージが表示されるようになりました。エラーメッセージには以下のような情報が含まれます：

- データが存在しない場合：「No valid data to plot for [parameter]」
- グラフ生成中にエラーが発生した場合：「Graph creation failed: [error details]」

これにより、問題の診断と解決が容易になります。
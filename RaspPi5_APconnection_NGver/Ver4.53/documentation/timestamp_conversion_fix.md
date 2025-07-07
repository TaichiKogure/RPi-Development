# タイムスタンプ変換の修正 (Ver 4.52)

## 問題点
タイムスタンプが2000年1月1日00:00から開始している問題が発生していました。これは、timestamp列の変換がうまくいかず、Pandasがデフォルトで1970/2000起点のダミー値を使用していることが原因でした。

## 修正内容
`P1_app_simple45.py` の `read_csv_data()` 関数内でのタイムスタンプ処理を以下のように改善しました：

1. タイムスタンプデータの型を検出する処理を強化
   - `np.issubdtype()` を使用して、より正確に数値型かどうかを判定
   - 数値型の場合はUNIX時間（秒）として処理
   - 文字列型の場合は日時文字列として処理

2. エラー処理の強化
   - try-except ブロックで変換処理を囲み、例外をキャッチ
   - 変換に失敗した場合は明示的にログに警告を出力
   - 失敗した場合は `pd.NaT` (Not a Time) を設定し、後続の `dropna()` で除去

3. ログ出力の強化
   - 元のタイムスタンプの型情報を記録
   - 変換後のタイムスタンプの型情報を記録
   - タイムスタンプの範囲（最小値から最大値）を記録
   - 変換失敗時のエラーメッセージを記録

## 効果
この修正により、以下の効果が期待できます：

1. タイムスタンプが正しく変換され、2000年1月1日のようなダミー値が表示されなくなる
2. 数値型（UNIX時間）と文字列型の両方のタイムスタンプ形式に対応
3. 変換に失敗したデータは適切に除外され、グラフ表示に影響を与えない
4. 詳細なログにより、問題が発生した場合のトラブルシューティングが容易になる

## 技術的詳細
修正したコード部分：

```python
# Convert timestamp to datetime - enhanced approach that handles both numeric and string formats
if 'timestamp' in df.columns:
    logger.info(f"Original timestamp dtype: {df['timestamp'].dtype}")

    try:
        # UNIX秒（数字）か文字列かで分岐
        if np.issubdtype(df['timestamp'].dtype, np.number):
            logger.info("Detected numeric timestamp format (UNIX time)")
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
        else:
            logger.info("Detected string timestamp format")
            df['timestamp'] = pd.to_datetime(df['timestamp'].astype(str), errors='coerce')

        logger.info(f"Converted timestamp dtype: {df['timestamp'].dtype}")
        logger.info(f"Timestamp range: {df['timestamp'].min()} to {df['timestamp'].max()}")

    except Exception as e:
        logger.error(f"Failed to convert timestamp: {e}")
        df['timestamp'] = pd.NaT
```
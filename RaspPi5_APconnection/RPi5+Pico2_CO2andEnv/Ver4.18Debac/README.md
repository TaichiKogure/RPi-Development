# Ver4.18Debac - デバッグモード修正

## 問題の概要
エラーメッセージ: `Error initializing WiFi client: unexpected keyword argument 'debug_mode'`

このエラーは、WiFiClientクラスのコンストラクタに`debug_mode`という引数が渡されているが、その引数を受け取るようにWiFiClientの`__init__()`メソッドが定義されていないために発生していました。

## 修正内容
`P3_software_debug/data_transmission/P3_wifi_client_debug.py`ファイル内のWiFiClientクラスの`__init__`メソッドに`debug_mode`パラメータを明示的に追加しました。

```python
def __init__(self, ssid="RaspberryPi5_AP_Solo", password="raspberry", 
             server_ip="192.168.0.1", server_port=5000, device_id="P3",
             debug_level=DEBUG_DETAILED, debug_mode=False):
    # Ensure debug_mode parameter is properly initialized
    """Initialize the WiFi client with the given configuration.
    ...
```

## 修正の効果
この修正により、`main.py`から`WiFiClient`クラスをインスタンス化する際に`debug_mode`パラメータを渡すことができるようになりました。これにより、エラーが解消され、プログラムが正常に動作するようになります。

## 注意点
- この修正を適用した後、キャッシュされたPythonバイトコードファイル（`.pyc`）が残っている場合は、それらを削除してから再実行してください。
- MicroPythonを使用している場合は、ファイルを再アップロードした後、デバイスを再起動してください。

## 追加情報
デバッグモードを有効にすると、WiFiClientクラスはより詳細なログ出力を行います。これは、WiFi接続の問題をトラブルシューティングする際に役立ちます。

```python
# デバッグモードを有効にする例
client = WiFiClient(
    ssid=WIFI_SSID,
    password=WIFI_PASSWORD,
    server_ip=SERVER_IP,
    server_port=SERVER_PORT,
    device_id=DEVICE_ID,
    debug_mode=True,  # デバッグモードを有効化
    debug_level=3     # 最も詳細なログレベル
)
```
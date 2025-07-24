# P1_ap_setup_solo.py 変更レポート - Ver2.1

## 概要
このドキュメントは、`P1_ap_setup_solo.py`スクリプトをVer2.0に適合させるために行った変更点を説明します。Ver2.0は、BME680センサーのみを使用し、CO2センサー（MH-Z19C）を使用しないシステムです。

## 変更点

### 1. バージョン番号の更新
- バージョン番号を「4.0.0-solo」から「2.1.0」に更新しました。
- スクリプトの説明を「Solo Version 4.0」から「Solo Version 2.1」に更新しました。

### 2. MH-Z19Cセンサーへの参照の削除
- ドキュメント文字列から「MH-Z19C」センサーへの参照を削除し、BME680センサーのみを言及するように変更しました。

### 3. デバイスリストの更新
- ドキュメント文字列内のデバイスリストを「P2とP3」から「P2、P3、P4、P5、P6」に更新しました。
- これにより、スクリプトが5つのセンサーノードすべてをサポートすることを明確にしました。

### 4. DNSMasq設定コメントの更新
- DNSMasq設定コメントを「Solo Ver4.0」から「Solo Ver2.1」に更新しました。

## 変更されていない機能
以下の機能は変更されていません：

1. アクセスポイントの設定（SSID、パスワード、IPアドレスなど）
2. DHCPサーバーの設定
3. IPフォワーディングの設定
4. サービスの有効化/無効化機能
5. ステータスチェック機能

## 設定パラメータ
現在の設定パラメータは以下の通りです：

```python
DEFAULT_CONFIG = {
    "ap_interface": "wlan0",
    "ap_ssid": "RaspberryPi5_AP_Solo2",
    "ap_password": "raspberry",
    "ap_country": "JP",
    "ap_channel": "6",
    "ap_ip": "192.168.0.2",
    "ap_netmask": "255.255.255.0",
    "ap_dhcp_range_start": "192.168.0.50",
    "ap_dhcp_range_end": "192.168.0.150",
    "ap_dhcp_lease_time": "24h",
    "client_interface": "wlan1",
    "priority_mode": "ap"  # 'ap' or 'client'
}
```

## 使用方法
スクリプトの使用方法は変更されていません：

```bash
sudo python3 P1_ap_setup_solo.py [--configure | --enable | --disable | --status]
```

- `--configure`: アクセスポイントを設定します
- `--enable`: アクセスポイントを有効にします
- `--disable`: アクセスポイントを無効にします
- `--status`: アクセスポイントのステータスを確認します

## 注意事項
- このスクリプトはroot権限（sudo）で実行する必要があります。
- 設定変更後はRaspberry Piを再起動することをお勧めします。
- Ver2.0システムはBME680センサーのみをサポートし、CO2センサー（MH-Z19C）はサポートしていません。
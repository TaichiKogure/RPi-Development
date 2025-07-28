# OLED ディスプレイ情報表示システム

## 概要
このプログラムは、Raspberry Pi に接続された SSD1306 OLED ディスプレイに、日時、CPU 使用率、CPU 温度を表示するシステムです。情報は異なる方向にスクロールし、定期的に 3D アニメーションを表示する機能も備えています。

## 機能
- **上段**: 年月日と時刻（秒なし）を右端から徐々に現れ、左端へ消えていくようにスクロール表示
- **中段**: CPU 使用率を左端から徐々に現れ、右端へ消えていくようにスクロール表示
- **下段**: CPU 温度を右端から徐々に現れ、左端へ消えていくようにスクロール表示
- **3D アニメーション**: 3 回のスクロールサイクル後に 3D 立方体が画面内を動き回るアニメーションを表示
- **設定可能なパラメータ**: 更新間隔、スクロール速度などを自由にカスタマイズ可能

## 必要なハードウェア
- Raspberry Pi（Zero、3、4、5 など）
- SSD1306 OLED ディスプレイ（128x64 ピクセル、SPI 接続）
- 接続ケーブル

## 必要なソフトウェア・ライブラリ
以下のライブラリをインストールする必要があります：

```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-pil python3-numpy
sudo pip3 install adafruit-circuitpython-ssd1306 psutil
```

## 配線方法
SSD1306 OLED ディスプレイを Raspberry Pi に接続します：

| OLED ピン | Raspberry Pi ピン |
|-----------|-------------------|
| VCC       | 3.3V              |
| GND       | GND               |
| SCL       | SCK (GPIO 11)     |
| SDA       | MOSI (GPIO 10)    |
| RES       | GPIO 24           |
| DC        | GPIO 25           |
| CS        | GPIO 8            |

## 使用方法

1. 必要なライブラリをインストールします
2. OLED ディスプレイを Raspberry Pi に接続します
3. プログラムを実行します：

```bash
python3 DispVer2.0.py
```

## カスタマイズ方法

プログラム内の以下のパラメータを変更することで、表示をカスタマイズできます：

```python
# ユーザー設定パラメータ（必要に応じて変更可能）
# ===================================================
# 表示更新間隔（秒）
update_interval = 1.0

# スクロールに使うパラメータ
scroll_speed_lr = 2    # 左から右へのスクロール速度（ピクセル数）
scroll_speed_rl = 2    # 右から左へのスクロール速度（ピクセル数）
sleep_time = 0.03      # スクロールの間隔（秒）
space = 30             # テキストの末尾に入れる空白の幅

# 3Dアニメーション設定
animation_duration = 3.0  # アニメーション表示時間（秒）
animation_frames = 60     # アニメーションのフレーム数

# その他の設定
cycles_before_animation = 3  # アニメーション表示までのスクロールサイクル数
# ===================================================
```

### 主なパラメータの説明

- **update_interval**: 情報更新の間隔（秒）。値を大きくすると更新頻度が下がります。
- **scroll_speed_lr**: 左から右へのスクロール速度。値を大きくするとスクロールが速くなります。
- **scroll_speed_rl**: 右から左へのスクロール速度。値を大きくするとスクロールが速くなります。
- **sleep_time**: スクロールのフレーム間の待機時間。値を小さくするとスクロールが滑らかになりますが、CPU 負荷が高くなります。
- **animation_duration**: 3D アニメーションの表示時間（秒）。
- **cycles_before_animation**: アニメーションが表示されるまでのスクロールサイクル数。

## フォントの変更

フォントサイズや種類を変更するには、以下の部分を編集します：

```python
try:
    # 日時表示用の大きめフォント
    font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 16)
    # CPU情報表示用の小さめフォント
    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 14)
except:
    font_large = ImageFont.load_default()
    font_small = ImageFont.load_default()
```

フォントサイズは、ディスプレイの大きさに合わせて調整してください。数字が大きいほど、フォントサイズが大きくなります。

## トラブルシューティング

### 表示されない場合
- OLED ディスプレイの接続を確認してください
- 必要なライブラリがすべてインストールされているか確認してください
- SPI が有効になっているか確認してください：
  ```bash
  sudo raspi-config
  ```
  から「Interface Options」→「SPI」を選択して有効にします

### 文字が小さすぎる/大きすぎる場合
- フォントサイズを調整してください

### CPU 温度が表示されない場合
- Raspberry Pi のモデルによっては温度ファイルのパスが異なる場合があります。その場合は、get_cpu_temperature() 関数内のファイルパスを適切なものに変更してください。

## 注意事項
- このプログラムは常時実行されるため、CPU リソースを消費します。他の重要なタスクを実行している場合は、update_interval の値を大きくして更新頻度を下げることを検討してください。
- OLED ディスプレイの寿命を延ばすために、長時間使用しない場合はプログラムを終了することをお勧めします。
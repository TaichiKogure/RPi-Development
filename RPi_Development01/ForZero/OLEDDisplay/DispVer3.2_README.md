# Raspberry Pi OLED ディスプレイ情報システム - バージョン 3.2

## 更新内容

このバージョンでは、3Dアニメーションに上下左右の移動機能を追加しました。立方体が画面内を移動しながら回転するようになり、より動的で視覚的に魅力的なアニメーションを実現しています。

## 新機能の詳細

### 1. 移動する3Dアニメーション

バージョン3.2では、以下の機能が追加されました：

- **画面内移動**: 3D立方体が画面内を上下左右に移動します
- **画面端での反射**: 立方体が画面端に達すると、反射して方向を変えます
- **3軸回転**: X軸、Y軸、Z軸の3方向すべてで回転します
- **動的な速度変化**: 回転速度が時間とともに変化します

### 2. 新しい設定パラメータ

新しく追加された設定パラメータ：

```python
# 3Dアニメーション設定
animation_speed_min = 0.5  # 最小回転速度係数
animation_speed_max = 2.0  # 最大回転速度係数
speed_change_chance = 0.02 # 各フレームで速度が変わる確率
movement_enabled = True    # 立体が画面内を移動するかどうか
movement_speed_x = 0.5     # X軸方向の移動速度
movement_speed_y = 0.3     # Y軸方向の移動速度
```

これらのパラメータを調整することで、アニメーションの動きをカスタマイズできます：

- **animation_speed_min/max**: 回転速度の範囲を設定します
- **speed_change_chance**: 回転速度が変化する確率を設定します
- **movement_enabled**: 移動機能のオン/オフを切り替えます
- **movement_speed_x/y**: X軸とY軸方向の移動速度を設定します

### 3. 安全機能の維持

バージョン3.1で追加された安全機能も維持されています：

- アニメーション実行状態の追跡
- 最大実行時間の制限
- 例外処理の強化
- デバッグ機能

## 使用方法

バージョン3.1と同様に使用できます。変更点は内部的なものであり、ユーザーインターフェースや基本機能は変わっていません。

```bash
python3 DispVer3.2.py
```

## 設定のカスタマイズ例

### 1. 移動速度の調整

移動速度を速くしたい場合：

```python
movement_speed_x = 1.0  # X軸方向の移動速度を2倍に
movement_speed_y = 0.6  # Y軸方向の移動速度を2倍に
```

移動速度を遅くしたい場合：

```python
movement_speed_x = 0.25  # X軸方向の移動速度を半分に
movement_speed_y = 0.15  # Y軸方向の移動速度を半分に
```

### 2. 移動機能の無効化

中央固定の回転アニメーションに戻したい場合：

```python
movement_enabled = False  # 移動機能を無効化
```

### 3. 回転速度の調整

回転速度を速くしたい場合：

```python
animation_speed_min = 1.0  # 最小回転速度を2倍に
animation_speed_max = 4.0  # 最大回転速度を2倍に
```

回転速度を遅くしたい場合：

```python
animation_speed_min = 0.25  # 最小回転速度を半分に
animation_speed_max = 1.0   # 最大回転速度を半分に
```

### 4. 速度変化の頻度調整

より頻繁に速度が変化するようにしたい場合：

```python
speed_change_chance = 0.05  # 5%の確率で速度が変化
```

速度変化を少なくしたい場合：

```python
speed_change_chance = 0.01  # 1%の確率で速度が変化
```

## 注意事項

- このプログラムは Raspberry Pi と SPI接続の128x64 OLEDディスプレイ（SSD1306コントローラ使用）で動作確認しています
- 必要なライブラリ（adafruit-blinka, adafruit-circuitpython-ssd1306, pillow, psutil, numpy）がインストールされていることを確認してください
- 移動速度が速すぎると、アニメーションが見づらくなる場合があります。適切な値に調整してください

## 技術的な実装詳細

### 移動ロジック

立方体の移動は以下のロジックで実装されています：

1. 初期位置を画面中央に設定
2. 初期移動方向をランダムに決定
3. 各フレームで位置を更新
4. 画面端に達したら方向を反転（反射）

```python
# 初期位置（画面中央）
pos_x = WIDTH / 2
pos_y = HEIGHT / 2

# 移動方向
dir_x = 1 if random.random() > 0.5 else -1
dir_y = 1 if random.random() > 0.5 else -1

# 移動が有効な場合、位置を更新
if movement_enabled:
    pos_x += movement_speed_x * dir_x
    pos_y += movement_speed_y * dir_y
    
    # 画面端での反射
    size = min(WIDTH, HEIGHT) / 5  # 立方体のサイズ
    if pos_x - size < 0 or pos_x + size > WIDTH:
        dir_x *= -1
    if pos_y - size < 0 or pos_y + size > HEIGHT:
        dir_y *= -1
```

### 3軸回転

X軸、Y軸、Z軸の3方向すべてで回転するように拡張されています：

```python
# 回転角度の初期化
angle_x = 0
angle_y = 0
angle_z = 0

# 回転角度を更新
angle_x += 0.05 * rotation_speed
angle_y += 0.07 * rotation_speed
angle_z += 0.03 * rotation_speed

# X軸周りの回転
y1 = v[1] * math.cos(angle_x) - v[2] * math.sin(angle_x)
z1 = v[1] * math.sin(angle_x) + v[2] * math.cos(angle_x)

# Y軸周りの回転
x2 = v[0] * math.cos(angle_y) - z1 * math.sin(angle_y)
z2 = v[0] * math.sin(angle_y) + z1 * math.cos(angle_y)

# Z軸周りの回転
x3 = x2 * math.cos(angle_z) - y1 * math.sin(angle_z)
y3 = x2 * math.sin(angle_z) + y1 * math.cos(angle_z)
```

---

更新日: 2025年7月26日
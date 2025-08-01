# Raspberry Pi Pico 透明OLEDディスプレイシステムモニター

このプロジェクトは、Raspberry Pi Pico と 128x64 透明OLEDディスプレイを使用して、現在時刻、CPU使用率、メモリ使用率を表示するシステムモニターを実装します。

## 目次

1. [必要なハードウェア](#必要なハードウェア)
2. [ピン接続](#ピン接続)
3. [インストール手順](#インストール手順)
4. [使用方法](#使用方法)
5. [トラブルシューティング](#トラブルシューティング)

## 必要なハードウェア

- Raspberry Pi Pico または Pico W
- 128x64 透明OLEDディスプレイ（SSD1306コントローラー搭載）
- ジャンパーワイヤー
- ブレッドボード（オプション）
- USB ケーブル（Pico の電源供給とプログラミング用）

## ピン接続

OLEDディスプレイとRaspberry Pi Picoの接続は以下の通りです：

| OLEDディスプレイ | Raspberry Pi Pico |
|-----------------|------------------|
| VCC (3.3V)      | 3V3 (ピン36)      |
| GND             | GND (ピン38)      |
| DIN (MOSI)      | GP3 (ピン5)       |
| CLK (SCK)       | GP2 (ピン4)       |
| CS              | GP6 (ピン9)       |
| DC              | GP4 (ピン6)       |
| RST             | GP5 (ピン7)       |

### ピン接続図

```
Raspberry Pi Pico                   透明OLEDディスプレイ
+---------------+                   +---------------+
|           3V3 o-------------------o VCC           |
|           GND o-------------------o GND           |
|           GP2 o-------------------o CLK           |
|           GP3 o-------------------o DIN           |
|           GP4 o-------------------o DC            |
|           GP5 o-------------------o RST           |
|           GP6 o-------------------o CS            |
+---------------+                   +---------------+
```

## インストール手順

### 1. MicroPythonのインストール

1. [Raspberry Pi Picoの公式ページ](https://www.raspberrypi.org/documentation/microcontrollers/micropython.html)からMicroPythonのファームウェア（.uf2ファイル）をダウンロードします。
2. BOOTSELボタンを押しながらPicoをコンピュータに接続します。
3. Picoが「RPI-RP2」というドライブとして認識されたら、ダウンロードした.uf2ファイルをドラッグ＆ドロップします。
4. Picoが自動的に再起動し、MicroPythonが実行可能になります。

### 2. 必要なライブラリのインストール

1. [Thonny IDE](https://thonny.org/)をインストールします（まだインストールしていない場合）。
2. ThonnyでPicoに接続します（右下の「MicroPython (Raspberry Pi Pico)」を選択）。
3. `ssd1306.py`ファイルをPicoにコピーします：
   - このリポジトリの`lib`フォルダから`ssd1306.py`ファイルをダウンロードします。
   - Thonnyで「ファイル」→「開く」を選択し、ダウンロードした`ssd1306.py`ファイルを開きます。
   - 「ファイル」→「名前を付けて保存」を選択し、「Raspberry Pi Pico」を選択して保存します。

### 3. テストスクリプトのインストール

1. このリポジトリから`display_test.py`ファイルをダウンロードします。
2. Thonnyで「ファイル」→「開く」を選択し、ダウンロードした`display_test.py`ファイルを開きます。
3. 「ファイル」→「名前を付けて保存」を選択し、「Raspberry Pi Pico」を選択して保存します。
4. Thonnyの「実行」ボタンをクリックしてテストを実行します。
5. テストが成功すると、ディスプレイに様々なパターンが表示され、最後に「Test Complete」というメッセージが表示されます。

### 4. メインプログラムのインストール

1. このリポジトリから`oled_system_monitor.py`ファイルをダウンロードします。
2. Thonnyで「ファイル」→「開く」を選択し、ダウンロードした`oled_system_monitor.py`ファイルを開きます。
3. 「ファイル」→「名前を付けて保存」を選択し、「Raspberry Pi Pico」を選択して`main.py`として保存します（Picoの起動時に自動実行されるようになります）。

## 使用方法

1. プログラムをインストールした後、Picoを電源に接続します。
2. OLEDディスプレイに以下の情報が表示されます：
   - ヘッダー（「SYSTEM MONITOR」と表示）
   - 現在の時刻と日付（中央に大きく表示）
   - CPU使用率（グラフ付き）
   - メモリ使用率（グラフ付き）
3. 表示は1秒ごとに更新されます。
4. プログレスバーには25%、50%、75%の位置にマーカーがあり、現在の値を視覚的に把握しやすくなっています。

### プログラムのカスタマイズ

`oled_system_monitor.py`ファイルを編集することで、以下の設定を変更できます：

- ピン割り当て（13-18行目）
- コントラスト設定（51行目の`display.contrast(255)`の値を変更）
- 表示の更新頻度（139行目の`time.sleep(1)`の値を変更）
- 表示レイアウト（107-133行目）

### 透明OLEDディスプレイの最適化について

このプログラムは透明OLEDディスプレイでの視認性を向上させるために以下の最適化を行っています：

1. 最大コントラスト設定（255）を使用
2. ヘッダー部分に反転表示（白背景に黒文字）を使用
3. プログレスバーに太い枠線とマーカーを追加
4. 区切り線を使用して情報を視覚的に分離
5. 時刻と日付を中央に配置して視認性を向上

## トラブルシューティング

### テストスクリプトを使用した診断

問題が発生した場合は、まず`display_test.py`を実行して、ディスプレイとの接続が正常に機能しているかを確認してください。テストスクリプトは以下のパターンを順番に表示します：

1. ディスプレイクリア
2. ディスプレイ全点灯
3. チェッカーボードパターン
4. テキスト表示
5. ライン描画
6. 長方形描画
7. 反転テキスト
8. プログレスバーアニメーション

これらのパターンが正しく表示されれば、ハードウェアは正常に機能しています。特定のパターンで問題が発生した場合は、そのパターンに関連する機能に問題がある可能性があります。

### 表示されない場合

1. すべての配線が正しく接続されていることを確認してください。特にSPI接続（DIN、CLK、CS、DC、RST）を確認してください。
2. Picoが正常に電源供給されていることを確認してください（電源LEDが点灯しているか）。
3. `ssd1306.py`ライブラリがPicoに正しくインストールされていることを確認してください。
4. ディスプレイのコントラストを調整してみてください（プログラム内の`display.contrast(255)`の値を変更）。
5. 透明OLEDディスプレイの背後に暗い背景を置いて、表示内容が見やすくなるか確認してください。

### 表示が乱れる場合

1. SPIの速度を下げてみてください（32行目の`baudrate`の値を下げる、例：1000000）。
2. 配線が長すぎないか、または干渉を受けていないか確認してください。短い配線を使用し、電源線と信号線を分離することをお勧めします。
3. 電源の安定性を確認してください。不安定な電源は表示の乱れの原因になります。
4. プログラムの更新頻度を下げてみてください（139行目の`time.sleep(1)`の値を大きくする、例：2秒）。

### 時刻が正しくない場合

MicroPythonのRaspberry Pi Pico実装では、リアルタイムクロック（RTC）がないため、電源を入れるたびに時刻はリセットされます。正確な時刻を維持するには、以下の方法があります：

1. 外部RTCモジュール（例：DS3231）を追加する
2. ネットワーク接続（Pico Wの場合）を使用してNTPサーバーから時刻を同期する
3. プログラム起動時に手動で時刻を設定する機能を追加する

### 透明ディスプレイの視認性を向上させるには

1. ディスプレイの背後に暗い背景（黒や濃紺など）を置くと、コントラストが向上します
2. 明るい環境では視認性が低下するため、直射日光を避けた場所に設置してください
3. 必要に応じてコントラストを調整してください（デフォルトは最大値の255ですが、環境によっては低い値の方が見やすい場合があります）

---

## 注意事項

- このプログラムはCPU使用率をシミュレートしています。Raspberry Pi Picoには実際のCPU使用率を測定する機能がないため、実際の値とは異なります。
- メモリ使用率は実際のメモリ割り当て状況に基づいています。
- 透明OLEDディスプレイは通常のOLEDディスプレイよりも視認性が低い場合があります。明るい背景の前に設置すると見やすくなります。
import board
import digitalio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont
import time
import datetime

# SPI初期化（128x64 用）
spi = board.SPI()
cs = digitalio.DigitalInOut(board.D8)
dc = digitalio.DigitalInOut(board.D25)
reset = digitalio.DigitalInOut(board.D24)
WIDTH, HEIGHT = 128, 64
oled = adafruit_ssd1306.SSD1306_SPI(WIDTH, HEIGHT, spi, dc, reset, cs)
oled.fill(0)
oled.show()

# フォント設定（標準PILの場合、Arialなど指定不可。専用TTFファイルも可）
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 20)
except:
    font = ImageFont.load_default()

# スクロールに使うパラメータ
scroll_speed = 2      # 右から左移動のピクセル数
sleep_time = 0.03     # スクロールの間隔（秒）
space = 30            # テキストの末尾に入れる空白の幅

while True:
    # 1秒ごとに現在時刻を取得
    now = datetime.datetime.now()
    # 英語表記（例: 2025-07-25 Fri 14:33:50）
    date_str = now.strftime("%Y-%m-%d (%a) %H:%M:%S")

    # 描画用バッファ作成、テキスト幅を超えるイメージを用意
    dummy_img = Image.new("1", (1,1))
    draw_dummy = ImageDraw.Draw(dummy_img)
    text_width, text_height = draw_dummy.textsize(date_str, font=font)
    total_width = text_width + space + WIDTH

    # 横長画像バッファに描画
    img = Image.new("1", (total_width, HEIGHT), 0)
    draw = ImageDraw.Draw(img)
    # Y位置センタリング
    y = (HEIGHT - text_height) // 2
    draw.text((WIDTH, y), date_str, font=font, fill=255)  # 画面端から

    # 左へスクロール
    for x in range(0, text_width + space):  # 1回横に流す
        oled.image(img.crop((x, 0, x + WIDTH, HEIGHT)))
        oled.show()
        time.sleep(sleep_time)

    # 継続して更新したい場合は while True のままでOK

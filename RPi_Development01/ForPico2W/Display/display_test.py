"""
Raspberry Pi Pico 透明OLEDディスプレイテストスクリプト
このスクリプトは、OLEDディスプレイの接続と機能をテストするためのものです。
"""

import machine
import ssd1306
import time

# Pin definitions for SPI interface
SPI_ID = 0
SPI_SCK_PIN = 2  # CLK
SPI_MOSI_PIN = 3  # DIN
SPI_DC_PIN = 4    # DC
SPI_RST_PIN = 5   # RST
SPI_CS_PIN = 6    # CS

# Display dimensions
WIDTH = 128
HEIGHT = 64

def test_display():
    print("OLEDディスプレイテストを開始します...")
    
    try:
        # Initialize SPI
        print("SPIを初期化中...")
        spi = machine.SPI(
            SPI_ID,
            baudrate=10000000,
            polarity=0,
            phase=0,
            sck=machine.Pin(SPI_SCK_PIN),
            mosi=machine.Pin(SPI_MOSI_PIN)
        )
        
        # Initialize display pins
        print("ディスプレイピンを初期化中...")
        dc = machine.Pin(SPI_DC_PIN)
        rst = machine.Pin(SPI_RST_PIN)
        cs = machine.Pin(SPI_CS_PIN)
        
        # Initialize display
        print("ディスプレイを初期化中...")
        display = ssd1306.SSD1306_SPI(WIDTH, HEIGHT, spi, dc, rst, cs)
        
        # Set contrast for better visibility on transparent display
        display.contrast(255)
        
        # Test pattern 1: Clear display
        print("テストパターン1: ディスプレイクリア")
        display.fill(0)
        display.show()
        time.sleep(1)
        
        # Test pattern 2: Fill display
        print("テストパターン2: ディスプレイ全点灯")
        display.fill(1)
        display.show()
        time.sleep(1)
        
        # Test pattern 3: Checkerboard
        print("テストパターン3: チェッカーボード")
        display.fill(0)
        for y in range(0, HEIGHT, 8):
            for x in range(0, WIDTH, 8):
                if (x // 8 + y // 8) % 2 == 0:
                    display.fill_rect(x, y, 8, 8, 1)
        display.show()
        time.sleep(1)
        
        # Test pattern 4: Text
        print("テストパターン4: テキスト表示")
        display.fill(0)
        display.text("OLED Test", 32, 0, 1)
        display.text("128x64 SSD1306", 8, 16, 1)
        display.text("Raspberry Pi", 16, 32, 1)
        display.text("Pico", 48, 48, 1)
        display.show()
        time.sleep(1)
        
        # Test pattern 5: Lines
        print("テストパターン5: ライン描画")
        display.fill(0)
        for i in range(0, WIDTH, 8):
            display.line(0, 0, i, HEIGHT-1, 1)
            display.line(WIDTH-1, 0, WIDTH-1-i, HEIGHT-1, 1)
        display.show()
        time.sleep(1)
        
        # Test pattern 6: Rectangles
        print("テストパターン6: 長方形描画")
        display.fill(0)
        for i in range(0, min(WIDTH, HEIGHT)//2, 8):
            display.rect(i, i, WIDTH-2*i, HEIGHT-2*i, 1)
        display.show()
        time.sleep(1)
        
        # Test pattern 7: Inverted text
        print("テストパターン7: 反転テキスト")
        display.fill(0)
        display.fill_rect(0, 0, WIDTH, 16, 1)
        display.text("Inverted Text", 8, 4, 0)
        display.show()
        time.sleep(1)
        
        # Test pattern 8: Progress bar
        print("テストパターン8: プログレスバー")
        display.fill(0)
        display.text("Progress Bar Test", 0, 0, 1)
        
        # Draw progress bar border
        bar_x = 0
        bar_y = 20
        bar_width = WIDTH
        bar_height = 10
        display.rect(bar_x, bar_y, bar_width, bar_height, 1)
        display.rect(bar_x+1, bar_y+1, bar_width-2, bar_height-2, 1)
        
        # Animate progress bar
        for i in range(0, bar_width-4, 4):
            fill_width = i
            display.fill_rect(bar_x+2, bar_y+2, fill_width, bar_height-4, 1)
            display.text("{:3d}%".format(i*100//(bar_width-4)), 48, 40, 1)
            display.show()
            time.sleep(0.1)
        
        # Final message
        display.fill(0)
        display.text("Test Complete", 16, 24, 1)
        display.text("All tests passed!", 8, 40, 1)
        display.show()
        
        print("テスト完了！すべてのテストに成功しました。")
        return True
        
    except Exception as e:
        print("エラーが発生しました:", e)
        return False

if __name__ == "__main__":
    test_display()
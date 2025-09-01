#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Raspberry Pi OLED Display Information System
Version: 3.0
Description: Displays date/time, CPU usage, and temperature on an OLED display
             with different scroll directions and 3D animation.
"""

import board
import digitalio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont
import time
import datetime
import psutil
import math
import random
import numpy as np
import sys
import os

# ディスプレイの設定
WIDTH, HEIGHT = 128, 64  # ディスプレイの解像度

# SPI初期化（128x64 用）
try:
    spi = board.SPI()
    cs = digitalio.DigitalInOut(board.D8)
    dc = digitalio.DigitalInOut(board.D25)
    reset = digitalio.DigitalInOut(board.D24)
    oled = adafruit_ssd1306.SSD1306_SPI(WIDTH, HEIGHT, spi, dc, reset, cs)
    oled.fill(0)  # 画面をクリア
    oled.show()
    print("OLED ディスプレイの初期化に成功しました")
except Exception as e:
    print(f"エラー: OLED ディスプレイの初期化に失敗しました: {e}")
    print("配線と必要なライブラリがインストールされているか確認してください")
    sys.exit(1)

# フォント設定（標準PILの場合、Arialなど指定不可。専用TTFファイルも可）
try:
    # 日時表示用の大きめフォント
    font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 16)
    # CPU情報表示用の小さめフォント
    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 14)
    print("フォントの読み込みに成功しました")
except Exception as e:
    print(f"警告: 指定されたフォントの読み込みに失敗しました: {e}")
    print("デフォルトフォントを使用します")
    font_large = ImageFont.load_default()
    font_small = ImageFont.load_default()

# ユーザー設定パラメータ（必要に応じて変更可能）
# ===================================================
# 表示更新間隔（秒）
update_interval = 0.2

# スクロールに使うパラメータ
scroll_speed_lr = 1    # 左から右へのスクロール速度（ピクセル数）
scroll_speed_rl = 1    # 右から左へのスクロール速度（ピクセル数）
sleep_time = 0.015      # スクロールの間隔（秒）
space = 30             # テキストの末尾に入れる空白の幅（スクロールの余白）

# 3Dアニメーション設定
animation_duration = 3.0  # アニメーション表示時間（秒）
animation_frames = 120     # アニメーションのフレーム数

# その他の設定
cycles_before_animation = 3  # アニメーション表示までのスクロールサイクル数
# ===================================================

# 内部変数
cycle_count = 0

# CPU使用率を取得する関数
def get_cpu_usage():
    """CPU使用率を取得して整形された文字列を返す"""
    try:
        usage = psutil.cpu_percent(interval=0.1)
        return f"CPU: {usage:.1f}%"
    except Exception as e:
        print(f"警告: CPU使用率の取得に失敗しました: {e}")
        return "CPU: ---%"

# CPU温度を取得する関数
def get_cpu_temperature():
    """CPU温度を取得して整形された文字列を返す"""
    try:
        # Raspberry Piの温度ファイルから温度を読み取る
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = float(f.read()) / 1000.0
        return f"TEMP: {temp:.1f}°C"
    except Exception as e:
        print(f"警告: CPU温度の取得に失敗しました: {e}")
        return "TEMP: --.-°C"

# 3Dアニメーションを描画する関数
def draw_3d_animation():
    """
    3D立方体のアニメーションを描画する関数
    
    アニメーション時間とフレーム数は設定パラメータから取得
    立方体は画面中央に表示され、X軸とY軸周りに回転する
    """
    # アニメーションの各フレームを生成して表示
    fps = animation_frames / animation_duration  # フレームレート計算
    start_time = time.time()
    
    try:
        while time.time() - start_time < animation_duration:
            # 画面をクリア
            img = Image.new("1", (WIDTH, HEIGHT), 0)
            draw = ImageDraw.Draw(img)
            
            # 経過時間に基づいて回転角度を計算
            elapsed = time.time() - start_time
            angle = elapsed * 2 * math.pi / 2  # 2秒で一周
            
            # 3D立方体の頂点を定義（中心が原点）
            size = min(WIDTH, HEIGHT) / 4  # 立方体のサイズ
            vertices = []
            for x in [-1, 1]:
                for y in [-1, 1]:
                    for z in [-1, 1]:
                        vertices.append((x*size, y*size, z*size))
            
            # 立方体の辺を定義（頂点のインデックスのペア）
            edges = [
                (0, 1), (0, 2), (0, 4), (1, 3), (1, 5),
                (2, 3), (2, 6), (3, 7), (4, 5), (4, 6),
                (5, 7), (6, 7)
            ]
            
            # 回転行列を適用して3D→2Dに投影
            projected = []
            for v in vertices:
                # X軸周りの回転
                y = v[1] * math.cos(angle) - v[2] * math.sin(angle)
                z = v[1] * math.sin(angle) + v[2] * math.cos(angle)
                
                # Y軸周りの回転
                x = v[0] * math.cos(angle) - z * math.sin(angle)
                z = v[0] * math.sin(angle) + z * math.cos(angle)
                
                # 投影（単純な平行投影）
                projected.append((
                    WIDTH/2 + x,  # X座標（画面中央が原点）
                    HEIGHT/2 + y  # Y座標（画面中央が原点）
                ))
            
            # 辺を描画
            for edge in edges:
                draw.line([projected[edge[0]], projected[edge[1]]], fill=255, width=1)
            
            # 画面に表示
            oled.image(img)
            oled.show()
            
            # フレームレート調整
            time.sleep(1/fps)
    except KeyboardInterrupt:
        # Ctrl+Cが押された場合、アニメーションを中断
        print("アニメーションが中断されました")
        return

# プログラム終了時の処理
def cleanup():
    """プログラム終了時にディスプレイをクリアする"""
    try:
        oled.fill(0)  # 画面を消去
        oled.show()
        print("ディスプレイをクリアしました")
    except:
        pass

# メインループ
def main():
    """メイン処理ループ"""
    global cycle_count
    
    print("表示を開始します。Ctrl+Cで終了できます。")
    
    try:
        while True:
            # サイクルカウンターを更新
            cycle_count += 1
            
            # 3サイクルごとにアニメーションを表示
            if cycle_count >= cycles_before_animation:
                cycle_count = 0
                print(f"{cycles_before_animation}サイクル完了: 3Dアニメーションを表示します")
                draw_3d_animation()
            
            # 現在時刻を取得（秒を除く）
            now = datetime.datetime.now()
            date_str = now.strftime("%Y-%m-%d %H:%M")
            
            # CPU使用率と温度を取得
            cpu_usage = get_cpu_usage()
            cpu_temp = get_cpu_temperature()
            
            # 各行のテキストサイズを計算
            dummy_img = Image.new("1", (1,1))
            draw_dummy = ImageDraw.Draw(dummy_img)
            
            # 日時のテキストサイズ
            date_width, date_height = draw_dummy.textsize(date_str, font=font_large)
            # CPU使用率のテキストサイズ
            usage_width, usage_height = draw_dummy.textsize(cpu_usage, font=font_small)
            # CPU温度のテキストサイズ
            temp_width, temp_height = draw_dummy.textsize(cpu_temp, font=font_small)
            
            # 各行の合計幅（スクロール用）
            date_total_width = date_width + space + WIDTH
            usage_total_width = usage_width + space + WIDTH
            temp_total_width = temp_width + space + WIDTH
            
            # 各行の高さを計算（ディスプレイを3分割）
            line_height = HEIGHT // 3
            
            # 1. 上段（日時）- 右から左へスクロール
            date_img = Image.new("1", (date_total_width, line_height), 0)
            date_draw = ImageDraw.Draw(date_img)
            date_y = (line_height - date_height) // 2  # 垂直方向中央揃え
            # テキストを画像の右端（画面外）に配置
            date_draw.text((date_total_width - date_width, date_y), date_str, font=font_large, fill=255)

            # 2. 中段（CPU使用率）- 左から右へスクロール
            usage_img = Image.new("1", (usage_total_width, line_height), 0)
            usage_draw = ImageDraw.Draw(usage_img)
            usage_y = (line_height - usage_height) // 2  # 垂直方向中央揃え
            # テキストを画像の左端（画面外）に配置
            usage_draw.text((0, usage_y), cpu_usage, font=font_small, fill=255)

            # 3. 下段（CPU温度）- 右から左へスクロール
            temp_img = Image.new("1", (temp_total_width, line_height), 0)
            temp_draw = ImageDraw.Draw(temp_img)
            temp_y = (line_height - temp_height) // 2  # 垂直方向中央揃え
            # テキストを画像の右端（画面外）に配置
            temp_draw.text((temp_total_width - temp_width, temp_y), cpu_temp, font=font_small, fill=255)
            
            # スクロール処理
            # 最大スクロール幅を計算（テキスト幅 + 画面幅 + 余白）
            max_scroll_width = max(date_width, usage_width, temp_width) + WIDTH + space
            
            try:
                # 各方向のスクロールに必要なステップ数を計算
                steps_rl = max_scroll_width // scroll_speed_rl  # 右から左へのスクロール
                steps_lr = max_scroll_width // scroll_speed_lr  # 左から右へのスクロール
                
                # 最大ステップ数（両方向のスクロールを同期させるため）
                max_steps = max(steps_rl, steps_lr)
                
                for step in range(max_steps):
                    # 最終的な表示用イメージ
                    display_img = Image.new("1", (WIDTH, HEIGHT), 0)
                    
                    # 1. 上段（日時）- 右から左へスクロール
                    # 右端から徐々に現れ、左端へ消えていく
                    if step < steps_rl:
                        # スクロール位置を計算
                        # 最初は画面の右端にテキストの左端が来るようにする
                        # 徐々に左にスクロールさせて、最終的にテキストが左端から消えるようにする
                        pos = WIDTH - (step * scroll_speed_rl)
                        
                        # テキストが画面内に入る範囲を計算
                        # テキストの左端が画面の右端より左にある場合のみ表示
                        if pos < WIDTH:
                            # テキストの表示位置
                            x_pos = pos
                            
                            # 新しい画像を作成してテキストを描画
                            text_img = Image.new("1", (WIDTH, line_height), 0)
                            text_draw = ImageDraw.Draw(text_img)
                            text_draw.text((x_pos, date_y), date_str, font=font_large, fill=255)
                            
                            # 画面に表示
                            display_img.paste(text_img, (0, 0))
                    
                    # 2. 中段（CPU使用率）- 左から右へスクロール
                    # 左端から徐々に現れ、右端へ消えていく
                    if step < steps_lr:
                        # スクロール位置を計算
                        # 最初は画面の左端にテキストの右端が来るようにする
                        # 徐々に右にスクロールさせて、最終的にテキストが右端から消えるようにする
                        pos = -usage_width + (step * scroll_speed_lr)
                        
                        # テキストが画面内に入る範囲を計算
                        # テキストの右端が画面の左端より右にある場合のみ表示
                        if pos > -usage_width:
                            # テキストの表示位置
                            x_pos = pos
                            
                            # 新しい画像を作成してテキストを描画
                            text_img = Image.new("1", (WIDTH, line_height), 0)
                            text_draw = ImageDraw.Draw(text_img)
                            text_draw.text((x_pos, usage_y), cpu_usage, font=font_small, fill=255)
                            
                            # 画面に表示
                            display_img.paste(text_img, (0, line_height))
                    
                    # 3. 下段（CPU温度）- 右から左へスクロール
                    # 右端から徐々に現れ、左端へ消えていく
                    if step < steps_rl:
                        # スクロール位置を計算
                        # 最初は画面の右端にテキストの左端が来るようにする
                        # 徐々に左にスクロールさせて、最終的にテキストが左端から消えるようにする
                        pos = WIDTH - (step * scroll_speed_rl)
                        
                        # テキストが画面内に入る範囲を計算
                        # テキストの左端が画面の右端より左にある場合のみ表示
                        if pos < WIDTH:
                            # テキストの表示位置
                            x_pos = pos
                            
                            # 新しい画像を作成してテキストを描画
                            text_img = Image.new("1", (WIDTH, line_height), 0)
                            text_draw = ImageDraw.Draw(text_img)
                            text_draw.text((x_pos, temp_y), cpu_temp, font=font_small, fill=255)
                            
                            # 画面に表示
                            display_img.paste(text_img, (0, line_height * 2))
                    
                    # 画面に表示
                    oled.image(display_img)
                    oled.show()
                    time.sleep(sleep_time)
            except KeyboardInterrupt:
                # スクロール中にCtrl+Cが押された場合
                raise KeyboardInterrupt
            
            # 更新間隔を待機
            time.sleep(update_interval)
            
    except KeyboardInterrupt:
        # Ctrl+Cが押された場合
        print("\nプログラムを終了します...")
        cleanup()
        print("正常に終了しました")
        sys.exit(0)
    except Exception as e:
        # その他の例外が発生した場合
        print(f"エラーが発生しました: {e}")
        cleanup()
        sys.exit(1)

# プログラム実行
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # main()の外側でCtrl+Cが押された場合
        print("\nプログラムを終了します...")
        cleanup()
        print("正常に終了しました")
        sys.exit(0)

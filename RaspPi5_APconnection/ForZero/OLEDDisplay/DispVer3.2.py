#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Raspberry Pi OLED Display Information System
Version: 3.2
Description: Displays date/time, CPU usage, and temperature on an OLED display
             with different scroll directions and enhanced 3D animation.
             Features moving 3D shape that travels across the screen while rotating.
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

# デバッグモード（詳細なログ出力）
DEBUG = True

def debug_print(message):
    """デバッグメッセージを出力する関数"""
    if DEBUG:
        print(f"[DEBUG] {message}")

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
sleep_time = 0.015     # スクロールの間隔（秒）
space = 30             # テキストの末尾に入れる空白の幅（スクロールの余白）

# 3Dアニメーション設定
animation_duration = 3.0  # アニメーション表示時間（秒）
animation_frames = 120    # アニメーションのフレーム数
max_animation_time = 5.0  # アニメーションの最大実行時間（秒）- 安全対策
animation_speed_min = 0.5  # 最小回転速度係数
animation_speed_max = 2.0  # 最大回転速度係数
speed_change_chance = 0.02 # 各フレームで速度が変わる確率
movement_enabled = True    # 立体が画面内を移動するかどうか
movement_speed_x = 0.5     # X軸方向の移動速度
movement_speed_y = 0.3     # Y軸方向の移動速度

# その他の設定
cycles_before_animation = 3  # アニメーション表示までのスクロールサイクル数
# ===================================================

# 内部変数
cycle_count = 0
animation_running = False  # アニメーションが実行中かどうかのフラグ

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
    拡張された3D立方体のアニメーションを描画する関数
    
    アニメーション時間とフレーム数は設定パラメータから取得
    立方体は画面内を移動しながら、X軸、Y軸、Z軸周りに回転する
    速度は動的に変化する
    
    安全対策として最大実行時間を設定し、それを超えると強制終了する
    """
    global animation_running
    
    # アニメーション開始
    animation_running = True
    debug_print("アニメーション開始")
    
    # アニメーションの各フレームを生成して表示
    fps = animation_frames / animation_duration  # フレームレート計算
    start_time = time.time()
    absolute_start_time = start_time  # 安全対策用の絶対的な開始時間
    
    # 初期位置（画面中央）
    pos_x = WIDTH / 2
    pos_y = HEIGHT / 2
    
    # 移動方向
    dir_x = 1 if random.random() > 0.5 else -1
    dir_y = 1 if random.random() > 0.5 else -1
    
    # 初期回転速度
    rotation_speed = random.uniform(animation_speed_min, animation_speed_max)
    
    # 回転角度の初期化
    angle_x = 0
    angle_y = 0
    angle_z = 0
    
    try:
        frame_count = 0
        while time.time() - start_time < animation_duration:
            # 安全対策: 最大実行時間を超えたら強制終了
            if time.time() - absolute_start_time > max_animation_time:
                print(f"警告: アニメーションが最大実行時間({max_animation_time}秒)を超えたため強制終了します")
                break
                
            frame_count += 1
            debug_print(f"アニメーションフレーム {frame_count}/{animation_frames}")
            
            # 画面をクリア
            img = Image.new("1", (WIDTH, HEIGHT), 0)
            draw = ImageDraw.Draw(img)
            
            # 回転速度をランダムに変更する可能性
            if random.random() < speed_change_chance:
                # 滑らかな速度変化のために現在の速度から少し変化させる
                target_speed = random.uniform(animation_speed_min, animation_speed_max)
                # 現在の速度と目標速度の中間値を取る（滑らかな変化）
                rotation_speed = (rotation_speed + target_speed) / 2
            
            # 回転角度を更新
            angle_x += 0.05 * rotation_speed
            angle_y += 0.07 * rotation_speed
            angle_z += 0.03 * rotation_speed
            
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
            
            # 3D立方体の頂点を定義（中心が原点）
            size = min(WIDTH, HEIGHT) / 5  # 立方体のサイズ
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
                # 回転行列を適用（X, Y, Z軸周りの回転）
                # X軸周りの回転
                y1 = v[1] * math.cos(angle_x) - v[2] * math.sin(angle_x)
                z1 = v[1] * math.sin(angle_x) + v[2] * math.cos(angle_x)
                
                # Y軸周りの回転
                x2 = v[0] * math.cos(angle_y) - z1 * math.sin(angle_y)
                z2 = v[0] * math.sin(angle_y) + z1 * math.cos(angle_y)
                
                # Z軸周りの回転
                x3 = x2 * math.cos(angle_z) - y1 * math.sin(angle_z)
                y3 = x2 * math.sin(angle_z) + y1 * math.cos(angle_z)
                
                # 投影（単純な平行投影）
                projected.append((
                    pos_x + x3,  # X座標（現在の位置が原点）
                    pos_y + y3   # Y座標（現在の位置が原点）
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
    except Exception as e:
        # その他の例外が発生した場合
        print(f"アニメーション中にエラーが発生しました: {e}")
    finally:
        # アニメーション終了（例外が発生しても必ず実行）
        animation_running = False
        debug_print("アニメーション終了")
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
    global cycle_count, animation_running
    
    print("表示を開始します。Ctrl+Cで終了できます。")
    
    try:
        while True:
            # アニメーションが実行中でない場合のみ処理を続行
            if not animation_running:
                debug_print(f"サイクル {cycle_count+1}/{cycles_before_animation}")
                
                # サイクルカウンターを更新
                cycle_count += 1
                
                # 3サイクルごとにアニメーションを表示
                if cycle_count >= cycles_before_animation:
                    cycle_count = 0
                    print(f"{cycles_before_animation}サイクル完了: 3Dアニメーションを表示します")
                    
                    # アニメーションを表示（非ブロッキングにするためにtryブロックで囲む）
                    try:
                        draw_3d_animation()
                    except Exception as e:
                        print(f"アニメーション実行中にエラーが発生しました: {e}")
                        animation_running = False  # 念のためフラグをリセット
                    
                    # アニメーション後の処理
                    debug_print("アニメーション後の処理を実行")
                
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
                        # アニメーションが開始された場合、スクロールを中断
                        if animation_running:
                            debug_print("アニメーション開始のためスクロールを中断")
                            break
                            
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
            else:
                # アニメーション実行中は短い間隔で待機
                time.sleep(0.1)
            
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
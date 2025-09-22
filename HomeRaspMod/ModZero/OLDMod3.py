import os
import time
import datetime
import bme680
import mh_z19
import requests
import csv
from Adafruit_SSD1306 import SSD1306_128_64  # Import the library for the display
from PIL import Image, ImageDraw, ImageFont  # Import additional libraries for drawing

"""
改良点（原因と対策の要旨）
- 原因: mh_z19.read() はエラー時に {'error': '...'} や None を返すことがあり、["co2"] で直接参照すると KeyError が発生。
- 対策: 安全読み出し関数 mhz19_safe_read() を実装。複数回リトライし、'co2' キーが存在するか検証。
          取得失敗時は None を返し、以降の処理（表示/保存/POST）で N/A もしくは -1 として扱う。
- 追加: 起動直後のウォームアップ待機、シリアル開放の任意化、例外の握り潰しを廃止して状況を表示。
"""

# 環境変数 SAFE_RELEASE=1 のときのみ、他プロセスのシリアル占有を解放（デフォルトは安全のため無効）
def release_serial_port():
    if os.environ.get('SAFE_RELEASE') == '1':
        os.system('sudo lsof /dev/serial0 | grep python | awk "{print \"kill -9\", $2}" | sh')


def mhz19_safe_read(retries: int = 5, interval_s: float = 1.0):
    """MH-Z19 の読み出しを安全に行う。
    - 成功時: int の CO2 ppm を返す
    - 失敗時: None を返す
    リトライ間で短時間 sleep を挟む。
    """
    for i in range(retries):
        try:
            data = mh_z19.read()
            if isinstance(data, dict):
                if 'co2' in data and isinstance(data['co2'], (int, float)):
                    return int(data['co2'])
                # mh_z19 が {'error': '...'} を返すケース
                if 'error' in data:
                    print(f"[MHZ19] read error: {data['error']}")
            elif data is None:
                print("[MHZ19] read returned None")
        except Exception as e:
            print(f"[MHZ19] exception on read (try {i+1}/{retries}): {e}")
        time.sleep(interval_s)
    return None


def write_to_csv(current_time, co2_value, temp_press_hum_info):
    with open('BedRoomEnv.csv', 'a', newline='') as f:
        fieldnames = ["current_time", "temperature", "pressure", "humidity", "gas_res", "co2"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if f.tell() == 0:
            writer.writeheader()

        # None の場合は -1 として保存（後段の解析で欠損扱いが容易）
        safe_co2 = -1 if co2_value is None else co2_value
        data_row = {"current_time": current_time, "co2": safe_co2, **temp_press_hum_info}
        writer.writerow(data_row)


def post_data(co2_value, temp_press_hum_info, current_time):
    data = dict(temp_press_hum_info)  # 破壊的変更を避ける
    data["co2"] = None if co2_value is None else co2_value
    data["current_time"] = current_time
    try:
        response = requests.post(
            'http://192.168.3.52:8888/data2',
            headers={'content-type': 'application/json'},
            json=data,
            timeout=5,
        )
        print('Post response:', response.status_code)
    except Exception as e:
        print('[POST] failed:', e)


def temperature_pressure_humidity(sensor):
    info = {}
    try:
        if sensor.get_sensor_data():
            info['temperature'] = round(sensor.data.temperature, 2)
            info['pressure'] = round(sensor.data.pressure, 2)
            info['humidity'] = round(sensor.data.humidity, 2)
            if getattr(sensor.data, 'heat_stable', False):
                info['gas_res'] = round(sensor.data.gas_resistance, 1)
    except Exception as e:
        print('[BME680] read failed:', e)
    return info


if __name__ == '__main__':
    # BME680 初期化
    try:
        sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
    except (RuntimeError, IOError):
        sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)

    try:
        sensor.set_humidity_oversample(bme680.OS_2X)
        sensor.set_pressure_oversample(bme680.OS_4X)
        sensor.set_temperature_oversample(bme680.OS_8X)
        sensor.set_filter(bme680.FILTER_SIZE_3)
        sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
        sensor.set_gas_heater_temperature(320)
        sensor.set_gas_heater_duration(150)
        sensor.select_gas_heater_profile(0)
    except Exception as e:
        print('[BME680] config failed:', e)

    # Initialize the display
    disp = SSD1306_128_64(rst=None)
    disp.begin()
    disp.clear()
    disp.display()

    # Create blank image for drawing
    width = disp.width
    height = disp.height
    image = Image.new('1', (width, height))

    # Get drawing object to draw on image
    draw = ImageDraw.Draw(image)

    # Load default font
    font = ImageFont.load_default()

    # 起動時ウォームアップ（MH-Z19 センサ安定のため）
    warmup_s = int(os.environ.get('MHZ19_WARMUP_S', '10'))
    if warmup_s > 0:
        print(f'[INIT] warming up for {warmup_s} seconds...')
        for r in range(warmup_s, 0, -1):
            draw.rectangle((0, 0, width, height), outline=0, fill=0)
            draw.text((0, 0), time.strftime("%y-%m-%d "), font=font, fill=255)
            draw.text((60, 0), time.strftime("%H:%M"), font=font, fill=255)
            draw.text((1, 20), f"Warming up MH-Z19: {r}s", font=font, fill=1)
            disp.image(image)
            disp.display()
            time.sleep(1)

    while True:
        release_serial_port()
        co2_value = mhz19_safe_read(retries=5, interval_s=2.0)

        temp_press_hum_info = temperature_pressure_humidity(sensor)

        current_time = datetime.datetime.now().isoformat()
        post_data(co2_value, temp_press_hum_info, current_time)
        write_to_csv(current_time, co2_value, temp_press_hum_info)

        # Console output
        print(f'CO2 Value: {co2_value if co2_value is not None else "N/A"}')
        print(temp_press_hum_info)

        # Draw on the display
        draw.rectangle((0, 0, width, height), outline=0, fill=0)  # Clear screen
        draw.text((0, 0), time.strftime("%y-%m-%d "), font=font, fill=255)  # Date
        draw.text((60, 0), time.strftime("%H:%M"), font=font, fill=255)  # Time
        draw.text((1, 14), f"Temp: {temp_press_hum_info.get('temperature', 'N/A')} C", font=font, fill=1)
        draw.text((1, 24), f"Pressure: {temp_press_hum_info.get('pressure', 'N/A')} hPa", font=font, fill=1)
        draw.text((1, 34), f"Humidity: {temp_press_hum_info.get('humidity', 'N/A')} %", font=font, fill=1)
        draw.text((1, 44), f"Gas Res: {temp_press_hum_info.get('gas_res', 'N/A')} Ohms", font=font, fill=1)
        draw.text((1, 54), f"CO2: {co2_value if co2_value is not None else 'N/A'} ppm", font=font, fill=1)

        disp.image(image)
        disp.display()

        time.sleep(60)

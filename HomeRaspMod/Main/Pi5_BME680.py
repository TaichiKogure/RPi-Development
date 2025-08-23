import csv
import time
import datetime
import os
import board
import adafruit_bme680


def release_serial_port():
    os.system('sudo lsof /dev/serial0 | grep python | awk \'{print "kill -9", $2}\' | sh')


def write_to_csv(current_time, temp_press_hum_info):
    with open('Env_data_BME680.csv', 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["current_time", "temperature", "pressure", "humidity",
                                               "gas_resistance"])
        if f.tell() == 0:
            writer.writeheader()

        data_row = {"current_time": current_time}
        data_row.update(temp_press_hum_info)

        writer.writerow(data_row)


def temperature_pressure_humidity(sensor):
    info = {}
    info['temperature'] = round(sensor.temperature, 2)
    info['pressure'] = round(sensor.pressure, 2)
    info['humidity'] = round(sensor.humidity, 2)
    info['gas_resistance'] = round(sensor.gas, 1)
    return info


if __name__ == '__main__':
    i2c = board.I2C()  # uses board.SCL and board.SDA
    sensor = adafruit_bme680.Adafruit_BME680_I2C(i2c, debug=False)

    # Sensor calibration
    sensor.sea_level_pressure = 1013.25

    while True:
 #       release_serial_port()

        temp_press_hum_info = temperature_pressure_humidity(sensor)

        current_time = datetime.datetime.now()
        write_to_csv(current_time, temp_press_hum_info)

        print(temp_press_hum_info)

        time.sleep(57)

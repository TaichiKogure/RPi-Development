from flask import Flask, request, jsonify, render_template_string
import csv
from datetime import datetime

app = Flask(__name__)

request_history = []  # To store request history


@app.route('/')
def hello():
    hello = "Hello world"
    return hello


@app.route('/data', methods=['POST'])
def handle_data():
    data = request.json
    print(data)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    data_1 = str(data.get('pressure')[:-3])
    data_2 = str(data.get('temperature')[:-1])
    row_data = {"current_time": timestamp, "Pressure": data_1, "Tempereture": data_2}

    with open('PicodataX.csv', 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["current_time", "Pressure", "Tempereture"])
        if f.tell() == 0:
            writer.writeheader()
        writer.writerow(row_data)

    # Log the request in request_history
    request_history.append({'endpoint': 'data', 'timestamp': timestamp, 'data': data})

    return 'OK', 200


@app.route('/data2', methods=['POST'])
def handle_data2():
    data = request.json
    print(data)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    co2_concentration = str(data.get('co2', ''))
    temperature = str(data.get('temperature', ''))
    humidity = str(data.get('humidity', ''))
    pressure = str(data.get('pressure', ''))
    gas_resistance = str(data.get('gas_res', ''))

    row_data = {
        "current_time": timestamp,
        "CO2": co2_concentration,
        "Tempereture": temperature,
        "Humidity": humidity,
        "Pressure": pressure,
        "GasResistance": gas_resistance,
    }

    with open('BedRoomEnv.csv', 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=row_data.keys())
        if f.tell() == 0:
            writer.writeheader()
        writer.writerow(row_data)

    # Log the request in request_history
    request_history.append({'endpoint': 'data2', 'timestamp': timestamp, 'data': data})

    return 'OK', 200


@app.route('/data3', methods=['POST'])
def handle_data3():
    data = request.json
    print(data)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    out_temp = str(data.get('temperature', ''))
    out_humidity = str(data.get('humidity', ''))
    out_pressure = str(data.get('pressure', ''))
    out_GasR = str(data.get('gas_res', ''))

    row_data = {
        "current_time": timestamp,
        "Temperature-outside": out_temp,
        "Humidity-outside": out_humidity,
        "Pressure-outside": out_pressure,
        "GasResistance-outside": out_GasR,
    }

    with open('OutsideEnv.csv', 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=row_data.keys())
        if f.tell() == 0:
            writer.writeheader()
        writer.writerow(row_data)

    # Log the request in request_history
    request_history.append({'endpoint': 'data3', 'timestamp': timestamp, 'data': data})

    return 'OK', 200


@app.route('/data4', methods=['POST'])
def handle_data4():
    data = request.json
    print(data)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    co2 = str(data.get('mh_z19', {}).get('co2', ''))
    analog_value = str(data.get('mq_2', {}).get('analog_value', ''))
    voltage = str(data.get('mq_2', {}).get('voltage', ''))
    temperature_ds18b20 = str(data.get('ds18b20', {}).get('temperature', ''))
    temp_dht11 = str(data.get('dht11', {}).get('temperature', ''))
    humid_dht11 = str(data.get('dht11', {}).get('humidity', ''))

    row_data = {
        "current_time": timestamp,
        "CO2": co2,
        "AnalogValue": analog_value,
        "Voltage": voltage,
        "Temperature_DS18B20": temperature_ds18b20,
        "Temperature_DHT11": temp_dht11,
        "Humidity_DHT11": humid_dht11
    }

    with open('LR_env.csv', 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=row_data.keys())
        if f.tell() == 0:
            writer.writeheader()
        writer.writerow(row_data)

    # Log the request in request_history
    request_history.append({'endpoint': 'data4', 'timestamp': timestamp, 'data': data})

    return 'OK', 200


# Route to view request history
@app.route('/history')
def history():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Request History</title>
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
            }
            table, th, td {
                border: 1px solid black;
            }
            th, td {
                padding: 10px;
                text-align: left;
            }
        </style>
    </head>
    <body>
        <h1>Request History</h1>
        <table>
            <tr>
                <th>Timestamp</th>
                <th>Endpoint</th>
                <th>Data</th>
            </tr>
            {% for entry in history %}
            <tr>
                <td>{{ entry.timestamp }}</td>
                <td>{{ entry.endpoint }}</td>
                <td>{{ entry.data }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """, history=request_history)


# API to get request history as JSON
@app.route('/history/json')
def history_json():
    return jsonify(request_history)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8888)

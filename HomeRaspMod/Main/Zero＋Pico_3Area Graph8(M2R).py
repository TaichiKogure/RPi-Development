import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

# Update test
plt.style.use('default')

DATA_FILES = [
    ("/home/koguretaichi/Documents/Flask/BedRoomEnv.csv", 'current_time'),
    ("/home/koguretaichi/Documents/Flask/OutsideEnv.csv", 'current_time'),
    ("/home/koguretaichi/Documents/Flask/PicodataX.csv", 'current_time'),
    ("/home/koguretaichi/Documents/Flask/LR_env.csv", 'current_time'),
    ("/home/koguretaichi/Env_data_BME680.csv", 'current_time')
]


def load_data(file_path, date_column):
    """
    Load data from a CSV file and set the specified column as datetime index.
    """
    data = pd.read_csv(file_path)
    data[date_column] = pd.to_datetime(data[date_column])
    data.set_index(date_column, inplace=True)
    return data


def resample_data(data, rule='min', reference_index=None):
    """
    Resample the data to a consistent frequency.
    If reference_index is provided, align data to this index.
    """
    resampled_data = data.resample(rule).mean()
    if reference_index is not None:
        resampled_data = resampled_data.reindex(reference_index, method='nearest')
    return resampled_data


def plot_lines(ax, x_data, y_data_dict, labels, colors, linestyles, ylabel, y_scale=None):
    """
    Plot multiple lines on a single subplot.
    """
    for y_data, label, color, linestyle in zip(y_data_dict, labels, colors, linestyles):
        ax.plot(x_data, y_data_dict[y_data], label=label, color=color, linestyle=linestyle)
    ax.set_ylabel(ylabel)
    if y_scale:
        ax.set_ylim(y_scale)
    ax.grid(True)
    ax.legend(loc='best')


def create_subplot(index, row, x_data, y_data_dict, labels, colors, linestyles, ylabel, y_scale=None, sharex=None):
    ax = plt.subplot(3, 2, index, sharex=sharex)
    plot_lines(ax, x_data, y_data_dict, labels, colors, linestyles, ylabel, y_scale)
    if index >= 5:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
    return ax


def calculate_absolute_humidity(temp, rh):
    """絶対湿度を計算する関数"""
    ah = (6.112 * np.exp((17.67 * temp) / (temp + 243.5)) * rh * 2.1674) / (273.15 + temp)
    return ah


def plot_data(start_time=None, y_scales=None):
    plt.figure()

    while True:
        # Read and preprocess data
        datasets = [load_data(file, date_col) for file, date_col in DATA_FILES]

        reference_index = datasets[0].index  # Use first dataset's index as reference

        bed_data, out_data, pico_data, lr_data, bme680_data = [resample_data(data, reference_index=reference_index)
                                                               for data in datasets]

        # Calculate absolute humidity
        bed_data['Absolute_Humidity'] = bed_data.apply(
            lambda row: calculate_absolute_humidity(row['Tempereture'], row['Humidity']), axis=1)
        out_data['Absolute_Humidity'] = out_data.apply(
            lambda row: calculate_absolute_humidity(row['Temperature-outside'], row['Humidity-outside']), axis=1)
        lr_data['Absolute_Humidity'] = lr_data.apply(
            lambda row: calculate_absolute_humidity(row['Temperature_DS18B20'], row['Humidity_DHT11']), axis=1)
        bme680_data['Absolute_Humidity'] = bme680_data.apply(
            lambda row: calculate_absolute_humidity(row['temperature'], row['humidity']), axis=1)

        plt.clf()
        x_start = pd.to_datetime(start_time) if start_time else bed_data.index.min()
        x_end = bed_data.index.max()

        ax1 = create_subplot(1, 6, bed_data.index, {
            'CO2': bed_data['CO2'],
            'CO2_LR': lr_data['CO2']
        },
                             ['BedRoom', 'DiningRoom'], ['c', 'k'], ['solid', 'solid'], 'CO2',
                             y_scales.get('CO2') if y_scales else None)

        ax2 = create_subplot(2, 6, bed_data.index, {
            'BedRoom Temperature': bed_data['Tempereture'],
            'Outside Temperature': out_data['Temperature-outside'],
            'Outside Temperature-2': pico_data['Tempereture'],
            'temp_C_Sensor2': lr_data['Temperature_DS18B20'],
            'Desk_temp': bme680_data['temperature']
        },
                             ['BedRoom', 'Outside1', 'Outside2', 'DiningRoom Temp.', 'Desk'],
                             ['c', 'r', 'blue', 'k', 'blue'],
                             ['solid', 'dashed', 'solid', 'dotted', 'dashdot'],
                             'Temperature',
                             y_scales.get('Temperature') if y_scales else None, sharex=ax1)

        ax3 = create_subplot(3, 6, bed_data.index, {
            'BedRoom Humidity': bed_data['Humidity'],
            'Outside Humidity': out_data['Humidity-outside'],
            'Humid_LR': lr_data['Humidity_DHT11'],
            'Desk_humidity': bme680_data['humidity']
        },
                             ['BedRoom', 'Outside', 'Dining', 'Desk'],
                             ['c', 'r', 'k', 'blue'],
                             ['solid', 'dashed', 'dashdot', 'solid'],
                             'Humidity',
                             y_scales.get('Humidity') if y_scales else None, sharex=ax1)

        ax4 = create_subplot(4, 6, bed_data.index, {
            'BedRoom Pressure': bed_data['Pressure'],
            'Outside Pressure': out_data['Pressure-outside'],
            'Desk_pressure': bme680_data['pressure']
        },
                             ['BedRoom', 'Outside', 'Desk'],
                             ['c', 'r', 'blue'],
                             ['solid', 'dashed', 'solid'],
                             'Pressure',
                             y_scales.get('Pressure') if y_scales else None, sharex=ax1)

        ax5 = create_subplot(5, 6, bed_data.index, {
            'Absolute Humidity - BedRoom': bed_data['Absolute_Humidity'],
            'Absolute Humidity - Outside': out_data['Absolute_Humidity'],
            'Absolute Humidity - DiningRoom': lr_data['Absolute_Humidity'],
            'Desk Absolute Humidity': bme680_data['Absolute_Humidity']
        },
                             ['BedRoom', 'Outside', 'DiningRoom', 'Desk'],
                             ['c', 'r', 'k', 'blue'],
                             ['solid', 'dashed', '-.', 'solid'],
                             'Absolute Humidity (g/m³)',
                             y_scales.get('Absolute Humidity') if y_scales else None, sharex=ax1)

        # Calculate and plot normalized GasResistance values
        bed_data['GasResistance_Avg'] = bed_data['GasResistance'].expanding().mean()
        out_data['GasResistance_Avg'] = out_data['GasResistance-outside'].expanding().mean()
        lr_data['AnalogValue_Avg'] = lr_data['AnalogValue'].expanding().mean()
        bme680_data['GasResistance_Avg'] = bme680_data['gas_resistance'].expanding().mean()

        bed_data['GasResistance_Normalized'] = bed_data['GasResistance'] / bed_data['GasResistance_Avg'].shift(
            1).fillna(1)
        out_data['GasResistance_Normalized'] = out_data['GasResistance-outside'] / out_data['GasResistance_Avg'].shift(
            1).fillna(1)
        lr_data['AnalogValue_Normalized'] = lr_data['AnalogValue'] / lr_data['AnalogValue_Avg'].shift(1).fillna(1)
        bme680_data['GasResistance_Normalized'] = bme680_data['gas_resistance'] / bme680_data[
            'GasResistance_Avg'].shift(1).fillna(1)

        ax6 = create_subplot(6, 6, bed_data.index, {
            'BedRoom GasResistance Normalized': bed_data['GasResistance_Normalized'],
            'Outside GasResistance Normalized': out_data['GasResistance_Normalized'],
            'Gas_LR Normalized': lr_data['AnalogValue_Normalized'],
            'Desk_gas Normalized': bme680_data['GasResistance_Normalized']
        },
                             ['BedRoom', 'Outside', 'DiningRoom', 'Desk'],
                             ['c', 'r', 'k', 'blue'],
                             ['solid', 'dashed', 'solid', 'dotted'],
                             'GasResistance Normalized',
                             y_scales.get('GasResistance Normalized') if y_scales else None, sharex=ax1)

        plt.xlim(x_start, x_end)
        plt.tight_layout()
        plt.draw()
        plt.pause(80)


plot_data(start_time="2025-08-20 00:00:00",
          y_scales={'CO2': (400, 1000), 'Temperature': (17, 40), 'Humidity': (20, 100), 'Pressure': (970, 1015),
                    'GasResistance': (10000, 150000), 'GasResistance Normalized': (0, 3),
                    'Absolute Humidity': (8, 25)})

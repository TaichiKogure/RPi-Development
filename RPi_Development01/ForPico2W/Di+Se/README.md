# BME680 Environmental Data Monitor with OLED Display

This project implements an environmental data monitoring system using a Raspberry Pi Pico, BME680 environmental sensor, and SSD1306 OLED display. The system continuously reads environmental data (temperature, humidity, pressure, gas resistance) and displays it on the OLED screen with scrolling text.

## Features

- Displays date and time, temperature, humidity, absolute humidity, pressure, and gas resistance
- Calculates absolute humidity from temperature and relative humidity
- Text scrolls from right to left for better readability
- Organized in three rows:
  - Top row: Date and time
  - Middle row: Temperature, relative humidity, absolute humidity
  - Bottom row: Pressure, gas resistance
- Updates every second
- LED status indication
- Error handling with automatic retry

## Hardware Requirements

- Raspberry Pi Pico or Pico W
- BME680 environmental sensor
- SSD1306 OLED display (128x64 pixels)
- Jumper wires
- Breadboard (optional)
- USB cable (for power and programming)

## Pin Connections

### BME680 Sensor (I2C Connection)

| BME680 Pin | Raspberry Pi Pico Pin |
|------------|----------------------|
| VCC        | 3.3V (Pin 36)        |
| GND        | GND (Pin 38)         |
| SCL        | GP1 (Pin 2)          |
| SDA        | GP0 (Pin 1)          |

### SSD1306 OLED Display (SPI Connection)

| OLED Display Pin | Raspberry Pi Pico Pin |
|------------------|----------------------|
| VCC              | 3.3V (Pin 36)        |
| GND              | GND (Pin 38)         |
| DIN (MOSI)       | GP3 (Pin 5)          |
| CLK (SCK)        | GP2 (Pin 4)          |
| CS               | GP6 (Pin 9)          |
| DC               | GP4 (Pin 6)          |
| RST              | GP5 (Pin 7)          |

## Installation

### 1. Install MicroPython on Raspberry Pi Pico

1. Download the latest MicroPython firmware (.uf2 file) for Raspberry Pi Pico from the [official website](https://micropython.org/download/rp2-pico/).
2. Connect the Pico to your computer while holding the BOOTSEL button.
3. Release the button after connecting.
4. The Pico should appear as a USB drive.
5. Copy the downloaded .uf2 file to the Pico drive.
6. The Pico will automatically reboot and run MicroPython.

### 2. Install Required Libraries

1. Download the following files from this repository:
   - `bme680.py` - Driver for the BME680 sensor
   - `ssd1306.py` - Driver for the SSD1306 OLED display
   - `bme680_oled_monitor.py` - Main program

2. Using Thonny IDE or another MicroPython IDE:
   - Connect to your Raspberry Pi Pico
   - Upload the `bme680.py` and `ssd1306.py` files to the Pico
   - Upload the `bme680_oled_monitor.py` file to the Pico

### 3. Run the Program

1. Connect the BME680 sensor and SSD1306 OLED display to the Raspberry Pi Pico according to the pin connections above.
2. Power the Pico via USB.
3. Run the `bme680_oled_monitor.py` file.
4. The program will initialize the hardware and start displaying environmental data on the OLED screen.

## Usage

Once the program is running, it will:

1. Initialize the BME680 sensor and SSD1306 display
2. Read environmental data every second
3. Display the data on the OLED screen with scrolling text
4. Print the data to the serial console for debugging

The onboard LED will blink during sensor readings and error conditions.

To stop the program, press Ctrl+C in the serial console or disconnect the Pico from power.

## Customization

You can customize the program by modifying the following parameters in the `bme680_oled_monitor.py` file:

- `I2C_SCL_PIN` and `I2C_SDA_PIN`: Change the I2C pins for the BME680 sensor
- `SPI_SCK_PIN`, `SPI_MOSI_PIN`, `SPI_DC_PIN`, `SPI_RST_PIN`, and `SPI_CS_PIN`: Change the SPI pins for the SSD1306 display
- `TOP_ROW_HEIGHT`, `MIDDLE_ROW_HEIGHT`, and `BOTTOM_ROW_HEIGHT`: Adjust the row heights
- Scrolling speed: Modify the `speed` parameter in the `ScrollText` constructor

## Troubleshooting

### No Data Displayed

- Check all connections between the Pico, BME680 sensor, and SSD1306 display
- Verify that the BME680 sensor is detected (check the serial output for "I2C devices found")
- Try both I2C addresses (0x76 and 0x77) for the BME680 sensor

### Display Issues

- Ensure the SSD1306 display is properly connected
- Check the SPI connections
- Adjust the contrast setting if the display is too dim or too bright

### Sensor Reading Errors

- Verify that the BME680 sensor is properly connected
- Check the I2C connections
- Make sure the sensor is powered correctly

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- The BME680 driver is based on the Adafruit BME680 library
- The SSD1306 driver is based on the MicroPython SSD1306 library
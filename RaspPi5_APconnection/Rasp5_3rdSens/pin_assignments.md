# P1_Sensor V1 - Pin Assignments

This document describes the pin connections for the P1_Sensor V1 environmental monitoring system.

## BME680 Environmental Sensor

The BME680 is connected to the Raspberry Pi 5 via I2C.

| BME680 Pin | Raspberry Pi 5 Pin | Description |
|------------|-------------------|-------------|
| VCC        | 3.3V (Pin 1)      | Power supply |
| GND        | GND (Pin 6)       | Ground |
| SCL        | SCL (GPIO 3, Pin 5) | I2C Clock |
| SDA        | SDA (GPIO 2, Pin 3) | I2C Data |

## MH-Z19 CO2 Sensor

The MH-Z19 is connected to the Raspberry Pi 5 via UART.

| MH-Z19 Pin | Raspberry Pi 5 Pin | Description |
|------------|-------------------|-------------|
| VCC (red)  | 5V (Pin 2 or 4)   | Power supply |
| GND (black)| GND (Pin 6)       | Ground |
| TX (green) | GPIO 14 (UART0 RX, Pin 8) | UART Transmit from sensor to Pi |
| RX (blue)  | GPIO 15 (UART0 TX, Pin 10) | UART Receive from Pi to sensor |

## Raspberry Pi 5 GPIO Pinout Reference

For reference, here is the GPIO pinout for the Raspberry Pi 5:

```
   3.3V Power [1]  [2]  5V Power
   GPIO 2 (SDA) [3]  [4]  5V Power
   GPIO 3 (SCL) [5]  [6]  Ground
   GPIO 4 [7]  [8]  GPIO 14 (UART0 TX)
   Ground [9]  [10] GPIO 15 (UART0 RX)
   GPIO 17 [11] [12] GPIO 18
   GPIO 27 [13] [14] Ground
   GPIO 22 [15] [16] GPIO 23
   3.3V Power [17] [18] GPIO 24
   GPIO 10 (SPI0 MOSI) [19] [20] Ground
   GPIO 9 (SPI0 MISO) [21] [22] GPIO 25
   GPIO 11 (SPI0 SCLK) [23] [24] GPIO 8 (SPI0 CE0)
   Ground [25] [26] GPIO 7 (SPI0 CE1)
   GPIO 0 (ID_SD) [27] [28] GPIO 1 (ID_SC)
   GPIO 5 [29] [30] Ground
   GPIO 6 [31] [32] GPIO 12
   GPIO 13 [33] [34] Ground
   GPIO 19 [35] [36] GPIO 16
   GPIO 26 [37] [38] GPIO 20
   Ground [39] [40] GPIO 21
```

## Notes

1. Make sure to connect the sensors carefully according to the pin assignments.
2. The BME680 uses I2C for communication, which requires pull-up resistors. These are typically already included on the sensor board.
3. The MH-Z19 uses UART for communication. Make sure to connect TX from the sensor to RX on the Pi, and RX from the sensor to TX on the Pi.
4. The MH-Z19 requires 5V power, while the BME680 requires 3.3V power.
5. Both sensors share the same ground connection.
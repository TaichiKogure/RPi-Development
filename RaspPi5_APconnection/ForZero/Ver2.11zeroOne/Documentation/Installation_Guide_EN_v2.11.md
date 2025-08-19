# Installation Guide Ver2.11 (ZeroOne Series)

This guide explains how to install the standalone environmental monitoring system centered on Raspberry Pi 5 (P1). In Ver2.11, P1 itself reads a directly attached BME680 via I2C and stores/visualizes data like P2/P3.

## 1. System Overview
- P1 (Raspberry Pi 5)
  - Wi‑Fi AP / central hub
  - Web UI provider
  - New: local BME680 readings (temperature, relative humidity, absolute humidity, pressure, gas resistance)
- P2/P3 (Raspberry Pi Pico 2W)
  - BME680-equipped sensor nodes sending data to P1 (existing)

Default storage destinations
- /var/lib(FromThonny)/raspap_solo/data/RawData_P1/P1_fixed.csv (append-only latest)
- /var/lib(FromThonny)/raspap_solo/data/RawData_P1/P1_YYYY-MM-DD.csv (daily)

## 2. Hardware Wiring (P1 BME680)
- VCC → 3.3V
- GND → GND
- SCL → GPIO3 (I2C SCL, pin 5)
- SDA → GPIO2 (I2C SDA, pin 3)
- I2C address is auto-detected (0x77 then 0x76)

## 3. OS Preparation
- Enable I2C (raspi-config → Interface Options → I2C Enable)
- Recommended: use a virtual environment
  - python3 -m venv envmonitor-venv
  - source envmonitor-venv/bin/activate
- Required packages (Web/UI)
  - pip install flask pandas plotly requests
- For the P1 BME680 reader
  - pip install smbus2

## 4. Repository Layout (this project)
- Work at: G:\RPi-Development\RaspPi5_APconnection\ForZero\Ver2.11zeroOne
- Key additions:
  - p1_software_Zero/data_collection/p1_bme680_reader.py (local sensor reader)
  - p1_software_Zero/web_interface/config.py (RawData_P1 added)
  - p1_software_Zero/data_collection/config.py (RawData_P1 added)
  - Web interface data/graph generator extended to include P1

## 5. Minimal Startup
1) Activate your virtualenv
2) Start P1 sensor reader (keep running)
   - python3 p1_software_Zero/data_collection/p1_bme680_reader.py --interval 10
3) Start data collection and Web UI using the existing start script(s)
4) Access P1’s IP in your browser and check graphs (/api/graphs) and latest values

## 6. Troubleshooting
- Sensor init fails: check wiring/I2C enable/address (0x76/0x77)
- No CSV created: verify permissions and /var/lib(FromThonny)/raspap_solo/data existence
- P1 not shown on Web: ensure /api/graphs response includes the P1 key

End

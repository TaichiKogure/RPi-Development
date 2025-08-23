# P1–P4 Sensor Data Logging Quick Start (Ver2.11 / ZeroOne)

This beginner-friendly guide explains how to log and visualize environmental data using P1 (Raspberry Pi 5/Zero2W) and P2–P4 (Raspberry Pi Pico 2W). It covers powering up, activating the Python virtual environment, starting programs in order, verifying status, and where the data are stored.

Related Documents (for reference):
- Installation_Guide_EN_v2.11.md (installation)
- System_Architecture_EN_v2.11.md (architecture)
- P1_BME680_Reader_Manual_JP_v2.11.md / EN (P1 internal BME680)

Working directory on Windows (repository path):
- G:\RPi-Development\RaspPi5_APconnection\ForZero\Ver2.11zeroOne

Default data locations on P1:
- /var/lib(FromThonny)/raspap_solo/data/RawData_P1
- /var/lib(FromThonny)/raspap_solo/data/RawData_P2
- /var/lib(FromThonny)/raspap_solo/data/RawData_P3
- /var/lib(FromThonny)/raspap_solo/data/RawData_P4

CSV schema (shared):
- timestamp, device_id, temperature, humidity, pressure, gas_resistance, co2, absolute_humidity
- Note: P1 leaves co2 blank ("") to keep schema compatibility with P2/P3/P4.

---

## 1) One-time Setup
1. Enable I2C on P1
- `sudo raspi-config` → Interface Options → I2C → enable → reboot

2. Create Python virtual environment (on P1)
```
python3 -m venv ~/envmonitor-venv
source ~/envmonitor-venv/bin/activate
```

3. Install required packages (inside venv)
```
pip install flask pandas plotly requests smbus2
```

4. Create data directories (if needed)
```
sudo mkdir -p /var/lib(FromThonny)/raspap_solo/data/RawData_{P1,P2,P3,P4}
sudo chown -R pi:pi /var/lib(FromThonny)/raspap_solo
```

---

## 2) Hardware Wiring Notes
- P1 internal BME680 via I2C:
  - VCC→3.3V, GND→GND, SCL→GPIO3 (pin 5), SDA→GPIO2 (pin 3)
  - I2C address auto-detects 0x77 then 0x76
- P2–P4 (Pico 2W): wire BME680 (and optional CO2 sensor if used) per existing Pico-side guides.

---

## 3) Daily Startup (manual example)
The following is a minimal, manual sequence. For systemd auto-start, see section 7.

1. Activate virtual environment (P1)
```
source ~/envmonitor-venv/bin/activate
```

2. Start the P1 internal BME680 logger (optional but recommended)
```
cd ~/RaspPi5_APconnection/ForZero/Ver2.11zeroOne
python3 p1_software_Zero/data_collection/p1_bme680_reader.py --interval 10
```
- Expected logs:
```
INFO - BME680 initialized at 0x77
INFO - Starting P1 BME680 reader loop
INFO - P1 wrote: T=27.12C RH=52.34% AH=12.45g/m3 P=1003.25hPa Gas=10523Ω
```

3. Start P2–P4 sensor nodes
- Launch the Pico 2W programs or ensure their auto-start is configured.
- They should connect to the P1 AP and deliver data to P1 via the configured protocol (TCP/HTTP, etc.).

4. Ensure the data collector on P1 is running
- In this Ver line, follow the existing start scripts/services for the collector.

5. Web interface
- Start (or ensure running) the Flask-based Web UI.
- From a device on the same network, open the P1 IP (e.g., http://192.168.0.1 or your P1 host IP).
- Confirm P1–P4 series appear in graphs (e.g., via /api/graphs or the dashboard page).

---

## 4) Verification Checklist
- Check CSV files are created/updated:
  - P1: /var/lib(FromThonny)/raspap_solo/data/RawData_P1/P1_fixed.csv
  - P2: /var/lib(FromThonny)/raspap_solo/data/RawData_P2/P2_fixed.csv
  - P3: /var/lib(FromThonny)/raspap_solo/data/RawData_P3/P3_fixed.csv
  - P4: /var/lib(FromThonny)/raspap_solo/data/RawData_P4/P4_fixed.csv
- Confirm timestamps advance with real time
- Web UI shows latest values and time-series graphs
- Connection monitor (if present) shows P2–P4 online

---

## 5) Data Storage Summary
- Fixed files (continuously appended):
  - RawData_P1/P1_fixed.csv
  - RawData_P2/P2_fixed.csv
  - RawData_P3/P3_fixed.csv
  - RawData_P4/P4_fixed.csv
- Daily rotated files:
  - RawData_Pn/Pn_YYYY-MM-DD.csv (n=1..4)

---

## 6) FAQ & Troubleshooting
- BME680 init fails: verify wiring, I2C enabled, and address (0x76/0x77)
- CSV not created: verify /var/lib(FromThonny)/raspap_solo/data permissions and folder existence
- No P1–P4 in Web UI: check /api/graphs response and that the fixed CSVs are updating
- Strange values: power stability, sensor init order, and note simplified driver limits (use a full driver for higher accuracy)

---

## 7) Auto-start Examples (systemd)
P1 internal BME680 logger service example:
```
# /etc/systemd/system/p1-bme680-reader.service
[Unit]
Description=P1 BME680 Reader (Ver2.11)
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/RaspPi5_APconnection/ForZero/Ver2.11zeroOne
ExecStart=/home/pi/envmonitor-venv/bin/python3 p1_software_Zero/data_collection/p1_bme680_reader.py --interval 10
Restart=always

[Install]
WantedBy=multi-user.target
```
Enable and start:
```
sudo systemctl daemon-reload
sudo systemctl enable p1-bme680-reader
sudo systemctl start p1-bme680-reader
sudo systemctl status p1-bme680-reader
```

Similarly, create services for the collector / web_interface / connection_monitor and define proper dependencies (After= / Wants=) as needed.

---

## 8) Useful Commands (on P1)
- Check running processes: `ps aux | grep python`
- Check listening ports (e.g., for Flask): `ss -tunlp | grep :80`
- View logs: module log files or `journalctl -u <service>`

End of document.
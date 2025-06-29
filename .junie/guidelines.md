# Raspberry Pi 5 and Pico 2W Standalone Environmental Data Measurement System

## Project Overview
This project implements a standalone environmental data measurement system using a Raspberry Pi 5 (P1) as the central hub and two Raspberry Pi Pico 2W devices (P2, P3) as sensor nodes. The system collects environmental data such as temperature, humidity, atmospheric pressure, gas parameters, and CO2 concentration, then visualizes and stores this data for analysis.

## System Components
1. **Raspberry Pi 5 (P1)** - Central hub that:
   - Acts as a WiFi access point for P2 and P3
   - Collects and stores environmental data from sensor nodes
   - Provides web interface for data visualization
   - Monitors connection quality with sensor nodes

2. **Raspberry Pi Pico 2W (P2, P3)** - Sensor nodes that:
   - Collect environmental data using BME680 sensors
   - Measure CO2 levels using MH-Z19B sensors
   - Transmit data to P1 via WiFi
   - Auto-restart on errors or connection issues

3. **Sensors**:
   - BME680 - Measures temperature, humidity, atmospheric pressure, and gas parameters
   - MH-Z19B - Measures CO2 concentration

## Project Structure
The project is organized within the RaspPi5_APconnection directory and includes:

```
RaspPi5_APconnection\
├── p1_software\              # Software for Raspberry Pi 5
│   ├── ap_setup\             # Access point configuration
│   ├── data_collection\      # Data collection from P2 and P3
│   ├── web_interface\        # Web UI for data visualization
│   └── connection_monitor\   # WiFi signal monitoring
├── p2_p3_software\           # Software for Pico 2W devices
│   ├── sensor_drivers\       # BME680 and MH-Z19B drivers
│   ├── data_transmission\    # WiFi communication with P1
│   └── error_handling\       # Auto-restart functionality
└── documentation\            # User manuals and guides
    ├── installation\         # Installation instructions
    ├── operation\            # Operation instructions
    └── troubleshooting\      # Troubleshooting guides
```

## Key Features

### P1 (Raspberry Pi 5) Features
- **Dual WiFi Functionality**:
  - Acts as WiFi access point (AP) for P2 and P3
  - Can connect to internet via USB WiFi dongle
  - Configurable to prioritize AP mode when USB dongle is absent
  - # P1の仕様
* P2,P3とWifi接続するためのWifiをアクセスポイント化する機能を有する。この機能は任意でAPモードと通常Wifiモードを切り替えることができる（取扱説明あり）
* ただし、USB Wifiドングルを接続し、通常のインターネットにもWifi接続できる。（ドングル使う場合の取扱説明あり）
* つまり、アクセスポイントとしてのWifi経路とWeb接続のためのWifi経路の2系統をもつ。
* USB Wifiドングルがない場合はAP機能を優先する。APとしてのアクセスポイントのIPアドレス関連は下記のようにする。
dnsmasq_config = f"""# dnsmasq configuration for Raspberry Pi 5 AP
interface=wlan0
dhcp-range=192.168.50.50,192.168.50.150,255.255.255.0,24h
domain=wlan
address=/gw.wlan/192.168.50.1
bogus-priv
server=8.8.8.8
server=8.8.4.4
とする。設定できない場合は設定可能なアドレスとする。
* 
* P2、P3から送られた環境データを受信し、CSVdataとして蓄積する。dataは年月日と時刻、気温、湿度、大気圧、ガスパラメータ。そしてCO2濃度である。
* あくせう
* P1は蓄積したデータをWifi接続したスマートフォンから任意のIPアドレスにアクセスすることで閲覧可能なWebUIを備える
* WebUIは蓄積した環境データを時系列にグラフ化する機能。最新の環境データを数値で表示する機能、グラフのデータをCSVの形でエクスポートし、ダウンロードできる機能を備える。
* webUIとは別にP1にVNC等でアクセスした際にグラフを閲覧する確認用プログラムも作成する（取扱説明あり）
* 接続しているP2,P3とのWifiの信号強度、Ping、noiseの情報も５秒(または任意設定)ごとにリアルタイムに測定して表示できる機能を有する。
* 信号強度はAP化したP1とP2,P3の設置距離や場所を判断するために使う。WebUIとVNC接続時用の個別APPの二系統を作る。(取扱説明あり)


- **Data Management**:
  - Receives and stores environmental data from P2 and P3
  - Stores data in CSV format with timestamp, temperature, humidity, pressure, gas parameters, and CO2 levels

- **Visualization**:
  - Web UI accessible from smartphones/devices connected to P1's WiFi
  - Time-series graphs of environmental data
  - Real-time display of current readings
  - CSV export functionality for downloaded data

- **Connection Monitoring**:
  - Measures WiFi signal strength, ping times, and noise levels with P2 and P3
  - Updates every 5 seconds (configurable)
  - Helps optimize physical placement of devices
  - Available through both Web UI and VNC interface

### P2, P3 (Raspberry Pi Pico 2W) Features
- **Sensor Integration**:
  - BME680 sensor readings every 30 seconds
  - MH-Z19B CO2 readings every 30 seconds

- **Data Transmission**:
  - Continuous data transmission to P1 via WiFi
  - Unique identification for P2 and P3 devices

- **Reliability**:
  - Automatic restart on sensor errors or data collection failures
  - Automatic WiFi reconnection after restart

## Installation and Setup
Detailed installation guides are provided for:
- Setting up P1 (Raspberry Pi 5) as an access point
- Installing and configuring sensor software on P2 and P3
- Connecting the system components
- Initial system testing and validation

## Version Information
All software components and documentation include version numbers for proper tracking and compatibility management.

## Target Audience
This project is designed with beginners in mind, with comprehensive documentation that explains not only how to use the system but also the underlying concepts and structure.

## additionalaction_Ver.2.0
- センサーBME680単独バージョンもfilename_soloというプログラム集で作成してください。
- 従来のプログラム集を参考にSoloVerはintallation_solo,p1_software_solo,P2P3_software_soloという単独ディレクトリを作りそこに保存すること。
- 前回の作成途中でエラーが出たためそれを回避してすでにあるディレクトリの情報も解析すること。
- 本指令ではまずは対応したP1向けのプログラムを作ってください。
- またP1は再起動した際にアクセスポイントの起動、データ収集サービスの起動、Webインターフェイスの起動、接続モニターの起動など複数の作業が必要になるため、一回の実行ですべて立ち上げられる実行ファイルとその解析を日本語で作成してください。
- 必要に応じてDocumentationもSolo用に新調してください。
- 
## additionalaction_Ver.2.1
- P1向けのadditionalaction_Ver2.0に基づき対応したP2,P3用のモデルを作成してください。
- RaspPi5_APconnectionで用いるP1のIP設定は
- ap_ip=192.168.0.1
ap_netmask=255.255.255.0
ap_dhcp_range_start=192.168.0.50
ap_dhcp_range_end=192.168.0.150
とするためすべての関連プログラムの既存設定をこれに準じた形に修正してください。

## additionalaction_Ver.2.2
P1においてpipを使ってRaspberryPiに直接Pythonモジュールをinstallすることは環境が破壊される可能性があるためすべての動作は下記の
仮想環境化で実施する。 そのためinstall時及び実際に各機能を実行する際、及び自動起動する際には下記の仮想環境を実行する旨修正、またはマニュアルに追記すること。

# Set up virtual environment
cd ~
python3 -m venv envmonitor-venv
source envmonitor-venv/bin/activate

# Install required Python packages
pip install flask flask-socketio pandas plotly

またVer2以降の修正で追加で必要なinstall項目があればそれも追記すること
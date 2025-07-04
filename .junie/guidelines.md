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
ただし必要に応じてこれらの構造は修正、増設される。

```
(base design and structure.)
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

## Additional action_Ver.2.0
- センサーBME680単独バージョンもfilename_soloというプログラム集で作成してください。
- 従来のプログラム集を参考にSoloVerはintallation_solo,p1_software_solo,P2P3_software_soloという単独ディレクトリを作りそこに保存すること。
- 前回の作成途中でエラーが出たためそれを回避してすでにあるディレクトリの情報も解析すること。
- 本指令ではまずは対応したP1向けのプログラムを作ってください。
- またP1は再起動した際にアクセスポイントの起動、データ収集サービスの起動、Webインターフェイスの起動、接続モニターの起動など複数の作業が必要になるため、一回の実行ですべて立ち上げられる実行ファイルとその解析を日本語で作成してください。
- 必要に応じてDocumentationもSolo用に新調してください。
- 
## Additional action_Ver.2.1
- P1向けのadditionalaction_Ver2.0に基づき対応したP2,P3用のモデルを作成してください。
- RaspPi5_APconnectionで用いるP1のIP設定は
- ap_ip=192.168.0.1
ap_netmask=255.255.255.0
ap_dhcp_range_start=192.168.0.50
ap_dhcp_range_end=192.168.0.150
とするためすべての関連プログラムの既存設定をこれに準じた形に修正してください。

## Additional action_Ver.2.2
P1においてpipを使ってRaspberryPiに直接Pythonモジュールをinstallすることは環境が破壊される可能性があるためすべての動作は下記の
仮想環境化で実施する。 そのためinstall時及び実際に各機能を実行する際、及び自動起動する際には下記の仮想環境を実行する旨修正、またはマニュアルに追記すること。

- Set up virtual environment
cd ~
python3 -m venv envmonitor-venv
source envmonitor-venv/bin/activate

- Install required Python packages
pip install flask flask-socketio pandas plotly

またVer2以降の修正で追加で必要なinstall項目があればそれも追記すること

## Additional action_Ver.2.3 
Additional action_Ver.2.2に対応したラズパイPico2Wのパッケージを作成する。
データ送信、エラーハンドリング、センサードライバは通常通りだが、Solo対応のP1に適合した形のプログラムとして修正する。
作業と成果物はG:\RPi-Development\RaspPi5_APconnection\P2_software_soloに保管する。

## Additional action_Ver.2.5
- G:\RPi-Development\RaspPi5_APconnection\Pico2BME680singletest\BME680forP2_real.pyにあるBME680設定情報をP2software_soloに反映してエラーを解消する主な変更点は下記


- 0 、センサーのアドレスの修正
sensor = BME680Sensor(address=0x77)


- 1 、ガス測定用のヒーターを有効にする設定
ctrl_gas = self._read_byte(BME680_CTRL_GAS_ADDR)
ctrl_gas |= 0x10  # heater enable bit を立てる
self._write_byte(BME680_CTRL_GAS_ADDR, ctrl_gas)


- ２、ヒーターの温度制御の改良
heatr_res = int(3.4 + ((temp - 20) * 0.6 / 100) * 1000)
heatr_res = min(max(0, heatr_res), 255)  # ★ 追加：0〜255に制限
self._write_byte(0x5A, heatr_res)


- 3、amb_temp未定義の対処
仮の周囲温度（ambient temperature）を仕様
amb_temp = 25  # 通常室温のデフォルト値
var5 = var4 + (var3 * amb_temp)

その他変更点があれば反映する。

以上を踏まえた修正を実施し、G:\RPi-Development\RaspPi5_APconnection\P2_software_solo2に保管する。

## Additional action_Ver.3.0
G:\RPi-Development\RaspPi5_APconnection\Pico2BME680singletest\OK2bme680Pico
に保存されたbme680.pyを参照したbme680_main.pyでP2のセンサーが確実に駆動できることを確認したため、このモジュールを基幹とした
P2_software_solo3を作成する。(G:\RPi-Development\RaspPi5_APconnection\P2_software_solo3)
センサドライバは上記bme680モジュールを用い、出力情報をdata_transmissionのmoduleで送信する構造とする。



## Additional action_Ver.3.1
G:\RPi-Development\RaspPi5_APconnection\Ver3.1を参照し
全体のP1とP2の整合性やコネクション周りのエラーをすべて検出して修正してください。
修正後のマニュアルも同一ディレクトリ内に日本語表記で作成すること。
P1の一括起動プログラムstart_p1_solo.pyは便利だが起動している案件が正常であることをきちんとコマンドプロンプト上に表記するような機能を追加すること。
またP2はラズパイPico2W想定だがネットワーク接続にエラーが頻発するため起動時に５秒以上のディレイを入れてセンサ、Wifi送信など各機能を立ち上げられるようにすること。
LEDの点灯機能は データ送信時、Wifiエラー、センサエラー、両方エラーなど識別できるようプログラム間の整理を行うすること。
Please refer to G:\RPi-Development\RaspPi5_APconnection\Ver3.1 and perform the following:
Check and correct all inconsistencies and connection-related errors between P1 and P2 throughout the entire system.
After making corrections, create a new Japanese-language manual and place it in the same directory.
While start_p1_solo.py (the unified startup script for P1) is convenient, please enhance its functionality to clearly indicate on the command prompt whether each running process is operating correctly.
P2 is intended to run on a Raspberry Pi Pico W, but network connection errors occur frequently. Therefore, add a delay of more than 5 seconds at startup to ensure that the sensor, Wi-Fi transmission, and other functions are initialized properly.
For the LED indicator function, reorganize the program logic so that it can distinguish between different statuses such as:
Data transmission,Wi-Fi error
Sensor error,Combined errors (both Wi-Fi and sensor)
Please implement the above.

すべての作業は上記ディレクトリ内で実施する
All tasks must be carried out within the above directory.

## Additional action_Ver.3.2
あなた:
wifi_client_solo.py に送信リトライ機能	現状は送信1回失敗で終了だが
最大5回まで自動再送してもよいように修正した完全版のプログラムを提供してください。

またP2_watchdog_solo.py	reset_device()が machine.reset() で即時再起動	
エラー時ログを確実に出力・保存できているか
要確認、すなわちFlash書き込みタイミングと競合するriskに対して対策した修正を行う。
また上記変更によって必要な修正をVer3.1のプログラム全体を俯瞰して実行する。
完成品はすべてVer3.2のフォルダに保管する。必要な未修正ファイルも併せて設置する。

## Additional action_Ver.3.5
- Ver3.1とVer3.2のシステムをベースに新た二酸化炭素センサーをP2に増設する。
- センサはMH-Z19Cでピンアサインは下記
VCC（赤）	VBUS（5V、ピン40）
GND（黒）	GND（ピン38）
TX（緑）	GP9（ピン12）
RX（青）	GP8（ピン11）
- CO2取得のために起動直後は３０秒の保持を行い。その後測定を実施する。
測定値はBME680dataとともにP1に送信される。
P1ではdataを記録しつつWebアプリ上で可視化できるようにする。

・P1のウェブアプリの注意点
- 修正前の時点で気温、湿度、気圧、Gas抵抗がグラフ化されるがすべての縦軸が0から100という意味不明な値になっているため
このレンジを任意で変更できるように修正すること、またCO2グラフも追加すること。
- また常にLoadingGraphという読み込みサインが表示されたままになるため修正すること。
- またWebアプリ上で接続しているP2の信号強度などの情報を随時表示するように改良すること。
- すべての情報は下記に保管し、そのままコピーすることでP1,P2に即時使えるように改良する
G:\RPi-Development\RaspPi5_APconnection\Ver3.5
アップデートしたinstallマニュアルと操作説明書を日本語で追加すること。これもVer3.5フォルダ内に設置する。

## Additional action_Ver.3.51
P2_software_soloの修正。
作業成果物はすべてP2_35_1ディレクトリに保存すること。

G:\RPi-Development\RaspPi5_APconnection\Ver3.5\P2_35_1

P2_software_solo35をThonny上で実行すると下記のエラーが生じる。

MPY: soft reboot

=== Raspberry Pi Pico 2W Environmental Monitor Ver3.5 ===
Initializing...
Initializing I2C for BME680...
I2C devices found: ['0x77']
Initializing BME680 sensor...
Initializing MH-Z19C CO2 sensor...
MH-Z19C initialized on UART1 (TX: GP8, RX: GP9)
Warming up for 30 seconds...
Initializing WiFi client...
Initializing data transmitter...
Initializing watchdog...
Watchdog initialized with 8000ms timeout
Initialization complete!
Connecting to WiFi...
Connecting to WiFi network: RaspberryPi5_AP_Solo
You may need to press "Stop/Restart" or hard-reset your MicroPython device and try again.

PROBLEM IN THONNY'S BACK-END: Exception while handling 'Run' (ConnectionError: EOF).
See Thonny's backend.log for more info.

Process ended with exit code 1.
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

Unable to connect to COM3: port not found

Process ended with exit code 1.

想定原因は下記だがこれ以外にも発生理由があるため柔軟に対応すること。
①	Wi-Fi接続失敗によるmachine.reset()	main.py の client.connect() が失敗したら、5秒待って machine.reset() を呼んでいます
②	Thonny上でのUSB切断と再接続	reset()によりUSBシリアルポートが物理的に一時切断 → Thonnyが通信不能になり「EOF」例外発生
🟠 原因2：client.connect() に十分な時間を与えていなかった
main.py では最大10秒しか待機しない設定になっており、タイミングによって接続失敗

🟠 原因3：client.connect() が失敗したあとすぐ machine.reset() を実行していた
これらに対する対策を行う。

## Additional action_Ver.4.0
- Ver3.51までの更新を踏まえてPico2Wの端末を増設する。
- 新しい端末は名前はP3とする。
- 基本的な機能と構成はP2と同等。
- P1での受信システムをP2とP3の二系統から受信できるように改良
- 併せてP1でのWeb閲覧機能を改良し、P2とP3のグラフを重ね書きできるようにする。
- P2,P3から受信したdataはP1中のディレクトリRawData_P2とRawData_P3を構築しここにリアルタイムに上書きし続ける構造に修正
- Webアプリ上のグラフはこのRawDataを読み込みPlotlyとして書き出すシステムとする。
- ウェブ上のグラフはP2、P3を任意のチェックボックスなどで表示設定ON/OFF切り替えできる。
- またP2,P3から得られた湿度と気温から絶対湿度を計算しそれもP2,P3のデータとしてグラフに出力する機能を追加する。絶対湿度の計算はP1上で行う。
- すべての作業はG:\RPi-Development\RaspPi5_APconnection\Ver4.0に保存する。
- main.pyなど不足分を修正
- インストールマニュアル、および使用方法を日本語で記載したものを追加。
- 
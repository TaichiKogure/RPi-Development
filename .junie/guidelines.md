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

## Additional action_Ver.4.1
- 増設したP3のコネクションタイムアウト問題に対して対策をする。
- 成果物は下記リンクに追加する。
- G:\RPi-Development\RaspPi5_APconnection\Ver4.1
- とくにP3のプログラム整合性、ファイル名称、P1との連携、P2とのID衝突が起こらないように調査分析改善してほしい。

特にThonny上で試運転をする場合P2では見られない

想定原因①：接続処理の途中でPico 2Wが自動リセットまたはハング
machine.reset()が呼ばれていなくても、ウォッチドッグタイマ（WDT）や例外によりリセットされる可能性あり。

main.pyでのエラー処理中の再起動箇所は以下で確認されていますmain：

safe_reset(reason="WiFi connection failure")
原因②：WiFi AP（RaspberryPi5）が見つからない、または応答しない
AP名RaspberryPi5_AP_Soloに接続を試みていますが、失敗して5回リトライ後、Picoは再起動しますmain。

その直後、ThonnyがCOMポートを失う（Unable to connect to COM3）＝Picoが自動リセットされた可能性大。

原因③：ThonnyのREPLセッションがWiFi接続途中に切断
ThonnyはUSBシリアルで接続しているため、USB接続が一時的に切れるとREPLセッションが落ちる。

🛠 対策（推奨順）
✅ ①【暫定対策】リセット処理を一時的に無効化
main.pyの以下の行：

safe_reset(reason="WiFi connection failure")
を

# safe_reset(reason="WiFi connection failure")
のようにコメントアウトし、手動で確認できるようにします。

✅ ② WiFiの接続処理に「例外ログだけ記録してリセットしない」設定を試す
例外発生時のhandle_error(...)のあとにsleepだけしてループを継続するように変更する。

# 元のコード
handle_error(Exception("WiFi connection failed"), {"phase": "wifi_connection"})
safe_reset(reason="WiFi connection failure")

# 修正案（Thonnyで開発しやすくする）
handle_error(Exception("WiFi connection failed"), {"phase": "wifi_connection"})
print("開発中のため自動リセットを停止中。手動で再起動してください。")
while True:
    time.sleep(1)
✅ ③ WiFi接続チェック関数にstatus()のログを追加
connect_wifi()内に以下を追加：

print("wlan.status() =", client.wlan.status())
※WiFiの失敗原因を特定しやすくなります。

- 変更履歴や操作方法の日本語マニュアルはVer4.1フォルダ内に作成すること。

## Additional action_Ver.4.15 Debag
成果物は下記に保管する
G:\RPi-Development\RaspPi5_APconnection\Ver4.1\Ver4.15Debag

- P3においてWifi接続確認、センサー接続確認、を検出しエラーがどこで発生しているか確認するためのプログラムを作成する。
- 設定値はこれまでのP3と同じだが、より時間経過や接続に向けてどのプロセスが進行中か逐一Thonny上で確認できること。
- Wifiについては、とくにリセットする、しない、タイムアウト時間設定などの複数パターンを実行して課題発生特定しやすく工夫すること。
- 作業マニュアルは日本語で同一ディレクトリ内に保管する。

- 現状のエラーは下記、実行すると ぴこんぽこんというUSB認識を無限に繰り返すループになってしまう。

MPY: soft reboot
Error log file initialized: /error_log_p3_solo.txt
Starting in 10 seconds...
10 seconds until start...
5 seconds until start...
3 seconds until start...
2 seconds until start...
1 seconds until start...

=== Raspberry Pi Pico 2W Environmental Monitor Ver4.1 (P3) ===
Initializing...
Initializing I2C for BME680...
I2C devices found: ['0x77']
Initializing BME680 sensor...
Initializing BME680 on I2C address 0x77
BME680 found with correct chip ID
BME680 calibration read successfully
BME680 initialization complete
Initializing MH-Z19C CO2 sensor...
MH-Z19C initialized on UART1 (TX: GP8, RX: GP9)
Warming up for 30 seconds...
Initializing WiFi client...
WiFi Client initialized for P3
Server: 192.168.0.1:5000
Initializing data transmitter...
Added sensor: bme680
Added sensor: mhz19c
Initializing watchdog...
Watchdog initialized with 8000ms timeout
Initialization complete!
Connecting to WiFi...
SSID: RaspberryPi5_AP_Solo, Device ID: P3
Maximum retries: 5, Connection timeout: 45 seconds
Connection attempt 1/5...
Connecting to WiFi network: RaspberryPi5_AP_Solo
Connection timeout: 45 seconds
Activating WiFi interface...
Sending connection request to RaspberryPi5_AP_Solo...
PROBLEM IN THONNY'S BACK-END: Exception while handling 'Run' (ConnectionError: EOF).
You may need to press "Stop/Restart" or hard-reset your MicroPython device and try again.

See Thonny's backend.log for more info.

Process ended with exit code 1.
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

Unable to connect to COM3: port not found

Process ended with exit code 1.

## Additional action_Ver.4.16 Debag
下記対応を実施する
 原因：バックグラウンド処理のブロック
JustAnswer の例ですが、次のような原因が挙げられています：

"continuous loop … wireless connection to the board drops" …
"machine.idle() # This allows the board to manage WiFi during the loop" 
github.com
+5
justanswer.com
+5
forums.raspberrypi.com
+5

➡while True: を一切休ませずに回し続けると、Pico の MicroPython システムが Wi‑Fi の維持・USB シリアル応答の処理を行うタイミングがなくなり、結果として Thonny からの応答が途絶えてしまいます。

対策：ループ内に処理のための“隙間”を入れる
無限ループ内には、最低でも以下のどちらかを含めてください。

① time.sleep() を使う
while True:
    # 本来の処理
    ...
    time.sleep(0.05)  # 50ms 程度でもOK
② machine.idle() を使う（より Wi‑Fi処理に優しい）

import machine, time

while True:
    # 本来の処理
    ...
    machine.idle()
    time.sleep(0.01)
これにより、CPU が余裕を持って Wi‑Fi チップや USB REPL の割込処理を実行できるようになります。

効果検証の方法
while True の中に print("loop!") を入れてループの継続を確認しつつ、

上記の time.sleep() や machine.idle() を有効化前後で、

Thonny 上に Starting main loop… のままになるか、進展するか 比較してみてください。

補足 & 他の可能性
ループ内で 大量のセンサ読み取りや UART ロギング、ネット通信 を実行している場合、それだけでも処理負荷になりやすいです。休止フレームは必須です。

同様の現象は Pico W（MicroPython）の実案件でもよく起きるため、ループには必ず “処理休止” を入れる設計が安全です 
reddit.com
+4
justanswer.com
+4
cebess.wordpress.com
+4
。

結論
Starting main loop… のまま待ち状態になる場合の原因は、無限ループでシステム側の処理に割り込みが入れられず、Wi‑Fi や USB の応答がハングしているためです。
time.sleep() や machine.idle() をループ内に挟むことで、MicroPythonの安定動作が期待できます。

お手数ですが、一度お試し＆動作状況を確認してみてください 😊

## Additional action_Ver.4.17 Debag
修正しましたがまだStarting main loop... で停止してしまいます。下記の対策を実施して下さい
Starting main loop… で止まったまま進まない原因として考えられるのは、MicroPython内部のWi‑FiやUSBの割り込み処理がメインループにより完全にブロックされてしまっている点です。

🔍 背景と原因
フォーラムでは、「無限ループだけ実行し続けると、デバイスが 'busy' 状態になって応答しなくなる」という声があります 
github.com
+2
stackoverflow.com
+2
justanswer.com
+2
。

また、Wi‑FiファームウェアのロードやUSB初期化中にメインループが重くなると、特にAppleなどではUSBがハングしてThonnyが切断されるといった報告もあります 。

JustAnswer上の相談者も「ループが動き続けると無線接続が切れる」「loop内にtime.sleepやidleが必要」とアドバイスされているそうです 
reddit.com
+4
justanswer.com
+4
stackoverflow.com
+4
。

✅ 対策：ループ処理の変更
① time.sleep() を挟む
python
コピーする
編集する
import time

print("Starting main loop...")
while True:
    # センサ取得などの処理
    …
    time.sleep(0.05)  # 約50msの待ちを入れる
② machine.idle() を併用（推奨）
python
コピーする
編集する
import machine, time

print("Starting main loop...")
while True:
    # センサ取得などの処理
    …
    machine.idle()
    time.sleep(0.01)  # idle + 小さな待ちで背景処理がしっかり動く
この idle → sleep の併用 により、Wi‑FiとUSBの割り込み処理が安定し、Thonnyの「Starting main loop…」も進行しやすくなります。

🧪 動作確認のステップ
print("loop!") をループに入れて、処理が進んでいるか確認。

machine.idle()を入れて改善するかをチェック。

idle + sleep 組み合わせで安定しない場合は、sleep時間を調整（0.01〜0.1秒）。

🎯 まとめ
原因：ループが背景処理（Wi‑Fi／USB）を妨げ、Thonnyが応答に追いつけなくなる

解決法：「idle＋sleep」で強制的に背景処理を実行させる

## Additional action_Ver.4.18 Debag
作業フォルダは下記
G:\RPi-Development\RaspPi5_APconnection\Ver4.18Debac
``` 
Error initializing WiFi client: unexpected keyword argument 'debug_mode'
```
このエラーが出る主な理由は、**WiFiClientクラスのコンストラクタに という引数が渡されているが、その引数を受け取るようにWiFiClientの`__init__()`メソッドが定義されていない`debug_mode`ためです。
#### **もしどうしてもが必要ならWiFiClientの`__init__`に追加`debug_mode`**
（通常は上記の方法が推奨）
どうしても必要なら、 のクラスで `wifi_client.py`
``` python
def __init__(self, ssid="...", ..., debug_mode=False):
    self.debug_mode = debug_mode
    # その他初期化処理
```
のように追加する。


## Additional action_Ver.4.19 Debag
下記の原因に対して対策したプログラムを作成し日本語による作業マニュアルも併せて作成する。
特に応急処置の部分の項目を詳細に説明する日本語マニュアルとする。
フォルダはVer4.19Debagディレクトリを作成してそこに保存する。


- 状況main.py は起動後、connect_wifi() を実行。
client.connect() にて wlan.connect(...) 呼び出し後に USB接続が強制切断され、Thonnyが COMポートを失う。
これは Thonny の表示が "PROBLEM IN THONNY'S BACK-END: ConnectionError: EOF" や "Unable to connect to COM3: port not found" を示していることからも明確。

 根本原因
 原因1：wlan.connect()中のタイムアウト時の 例外未処理
コード上では以下のブロックで wlan.connect() を使い、接続を待機します：

self.wlan.connect(self.ssid, self.password)
ただし、一定時間で接続が成立しないと、ESP32ベースのWi-Fiモジュールが内部リセットを起こす ことがあり、その際に Pico W の USB-UART インタフェースも巻き添えで再初期化され、COMポートが消滅します（これは known bug として複数報告があります）。

✅ 原因2：Thonny側が USB切断に過敏
Thonny は Pico W において：

USB経由で REPL（シリアル）通信を維持している

その通信が Wi-Fi 接続中の 例外 or ハングにより切断 されると、COMポート消滅と認識し、"EOF" エラー → 実行中断 → ポート消滅 → 再接続ループ になる

✅ 推奨される対策
対策1：Wi-Fi接続はスレッド化 or try/except で安全に包む
WiFiClient.connect() の中で以下のように 例外全体をtryブロックで囲うことで、MicroPython側がリセットしないよう保護します。


try:
    self.wlan.connect(self.ssid, self.password)
except Exception as e:
    self._debug_print(f"Exception during wlan.connect(): {e}", DEBUG_BASIC)
    return False
また、特に self.wlan.scan() の部分は稀にハングを引き起こすため、ここも try/except で安全化すべきです。

対策2：Wi-Fi 接続確認後に print() をしない
Thonny がシリアルに依存している関係で、Wi-Fi接続直後に大量の print() が入ると USB/REPL が落ちやすい という報告もあります。
したがって、以下のような部分をコメントアウトかログ抑制します：


# print("Connected to SSID:", self.ssid)   # コメントアウトか抑制
# print(f"IP address: {ip}")               # 同様
必要に応じてログをファイルに保存する設計に切り替えるのが安全です。

対策3：最初は WiFiClient.run_network_diagnostics() のみを使い接続は試みない
P2で安定しているなら、P3の個体が電源供給の面やWi-Fiモジュールの不安定性を持っている可能性も高いです。

✅ 応急処置として試すべきこと（段階的）
client.run_network_diagnostics() のみに変更して main loop を切る
connect() を呼び出す箇所をコメントアウトし、main loop が正常に動くかを確認
それでも落ちる場合 → wlan.connect() 前後に print() を削除
client.connect() の self.wlan.connect() を try/except で囲み、ThonnyとのCOM通信を守る
上記後も USBが落ちる → machine.freq(125_000_000) などで処理負荷を軽減して再試行
🔚 結論
この問題は「Wi-Fi接続処理中にMicroPythonが内部でUSB通信を阻害 → Thonnyから見てポート消失」という Pico W + Thonny 特有の構造的問題が引き起こしており、プログラム構造とログ出力の見直しで回避可能です。


## Additional action_Ver.4.19 Debag
下記の原因に対して対策したプログラムを作成し日本語による作業マニュアルも併せて作成する。
特に応急処置の部分の項目を詳細に説明する日本語マニュアルとする。
フォルダはVer4.19Debagディレクトリを作成してそこに保存する。
wifi_client_debugにおいて

input("Press 'y' to continue or any other key to exit...")

この行が run_network_diagnostics() や main.py 側で使われていると、Thonny REPLやUSBでは入力待ちになるが、実際には入力できない＝ハングして見える状態になります。

以下のような制御を追加する。

if self.debug_mode and self.debug_level >= DEBUG_BASIC:
    print("\nDiagnostics Summary:")
    print(f"WiFi Active: {self.wlan.active()}")
    print(f"Target Network Found: {results.get('target_network_found', False)}")
    print(f"Signal Strength: {results.get('target_network_strength', 'N/A')} dBm")
    proceed = True  # ← debugオプションで変えられるようにする
    if not proceed:
        print("Connection attempt skipped. Continuing without WiFi connection.")
        return False
その他の修正指示
1, input() の使用を削除／自動判断に切り替え（REPLで入力は不可）
2, wlan.scan() の直前に time.sleep(1) を入れると安定性が上がる可能性あり
3, run_network_diagnostics() は表示のみにし、WiFi接続制御は別の設定フラグで管理

成果物はG:\RPi-Development\RaspPi5_APconnection\Ver4.19Debagに保管する

## Additional action_Ver.4.20 Debag
- 下記の原因に対して対策したプログラムを作成し日本語による作業マニュアルも併せて作成する。
- 特に応急処置の部分の項目を詳細に説明する日本語マニュアルとする。
- フォルダはVer4.20Debagディレクトリを作成してそこに保存する。
- CO2センサもきちんと駆動させてデータを取得するよう修正する。
- BME680のI2Cアドレスミス
→ ドライバーの初期化時に間違ったアドレス（たとえば0x77と0x76の取り違え）があると、
センサ実装有無に関わらず「値は返る」が「デタラメな値」になることがあります。これを両方検証して正確な値を出力できるよう修正
- Ver4.0のP1のデータ収集形式に会うように修正。
- 

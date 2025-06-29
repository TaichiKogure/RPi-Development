# Project Guidelines
    
This is a placeholder of the project guidelines for Junie.
Replace this text with any project-level instructions for Junie, e.g.:

* What is the project structure
* Whether Junie should run tests to check the correctness of the proposed solution
* How does Junie run tests (once it requires any non-standard approach)
* Whether Junie should build the project before submitting the result
* Any code-style related instructions


# 使用言語と仕様
* 日本語をベースとした仕様書、P1,P2,P3へのinstall、使用開始マニュアルの設置。
* すべての仕様やディレクトリにはバージョンNoを入れること。
* 取扱説明やマニュアルはすべて初心者向けを想定し、構造や背景や構造などを丁寧に記載すること。

# 動作環境
* RapsberryPi5 一台 略称はP1とする
* RapsberryPi pico2w 二台 略称はP2、P3とする
* Windows11 デスクトップPC（メイン開発機）

# P1の仕様
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


# P2、P3の仕様 (RaspberryPipico2w)
* BME680センサーによる、 気温、湿度、大気圧、ガスパラメータ取得を30秒ごとに実施する。
* MH-Z19BによるCO2検出も30秒ごとに実施する。
* 得られたデータは随時アクセスポイント化されたP1にWifi経由で送信される。
* P2とP3は各自識別される
* dataが取得できない場合やエラーが発生したと認識した場合は自動で再起動し、都度Wifiに接続される。
* 新品のP2、P3に対してinstallする際の仕様解説書をつくる



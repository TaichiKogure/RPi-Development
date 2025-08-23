# BME680ガス抵抗の値の整合性確認

G:\RPi-Development\RaspPi5_APconnection\ForZero\Ver2.20zeroOne\p1_softwareV4
P２とP3,P4のガス抵抗値はほぼ同じですがP1はずれています。P1のガス抵抗値はP2,P3,P4の平均値の1.5倍以上離れている。制御プログラムの修正が必要です。
主にP2やP3,P4のガス抵抗計算ロジックに準じた形でP1のデータ読み取りを改良してください。データの取得は３０秒ごとに取得してください。ただしガス抵抗への影響を考慮しヒーターの設定は継続的に維持する。このreaderプログラムはVer2としてください。
参照は下記G:\RPi-Development\RaspPi5_APconnection\ForZero\Ver2.20zeroOne\p1_softwareV4\data_collection\p1_bme680_reader.py
ガス抵抗の計算ロジックの参照先は下記G:\RPi-Development\RaspPi5_APconnection\ForZero\Ver2.20zeroOne\P2_software_debug

DataViewerVer3にCSVでP1,P2,P3,P4それぞれの全データをダウンロードするためのボタンを設置する。

ラズパイPico２W側のプログラムの改良、P2.P3、P4のデータは三十秒ごとにCSVに記入する。


# Ver2.20 zeroOne データビューワ
WebApp上で時間vs各環境パラメータのグラフを表示させるプログラムを作成する。
表示するにあたり用いるCSVデータは/var/lib(FromThonny)/raspap_solo/dataにあるRawData_P1,RawData_P2 RawData_P3, RawData_P4 のCSVファイル（P1_fixed.csv,P2_fixed.csv, P3_fixed.csv, P4_fixed.csv)を参照する。これらのデータフォーマットはtimestamp,device_id,temperature,humidity,pressure,gas_resistance,absolute_humidity
2025-08-23 15:07:25,P2,30.778436,36.218988,999.7605,12201,11.45
2025-08-23 15:07:49,P2,30.17082,36.377364,999.72768,12047,11.13
2025-08-23 15:08:19,P2,30.200312,35.836364,999.72344,12124,10.99
2025-08-23 15:08:49,P2,30.278436,35.565484,999.7065,12194,10.95 のような形状である。
このプログラムで得られるグラフはアクセスIPは192.168.0.2/db とする。

追加機能：また湿度温度データとガス抵抗の変化から空気汚染度指標を作成してグラフ表示する機能も追加する


# Ver2.20 zeroOne BME680 P1の修正
G:\RPi-Development\RaspPi5_APconnection\ForZero\Ver2.20zeroOne\p1_softwareNoWebMonitor2\data_collection\p1_bme680_reader.pyは温度気圧などのデータが不正確なので修正する。
正しいデータを得られるプログラムはG:\RPi-Development\OK2bme\bme680.pyおよびG:\RPi-Development\OK2bme\bme680main.pyであるためこれらのプログラムのロジックを使用すること。



# Ver2.20 zeroOne
- 作業フォルダは下記 G:\RPi-Development\RaspPi5_APconnection\ForZero\Ver2.20zeroOne
P4のプログラムをG:\RPi-Development\RaspPi5_APconnection\ForZero\Ver2.20zeroOne\P3_software_debugのP3プログラムのルールに沿って修正する。
P4でエラーを発し、P3でエラーが出ない解析結果は下記を参考にすること。
- 原因は P4 側の BME680 ドライバ実装（sensor_drivers/bme680.py）の「校正データ取り出しロジック」です。
- P4 ドライバは、校正領域を
    - 0x89 から 25 バイト
    - 0xE1 から 16 バイト の計 41 バイト読み込み後、その配列から coeff[33] や coeff[45] など「配列長（41）を超えるインデックス」を参照しています。これが初期化中の「IndexError: bytes index out of range」の直接原因です。
- 一方 P3 側は、同じ校正領域からの読み出しに対して「範囲内のスライス＋構造体アンパック」で安全に係数を組み立てており、範囲外参照が起きない構成になっています。そのため P3 は正常動作します。
結論
- エラーはプログラム差分によるもので、P4 の BME680 ドライバの校正データのインデックス指定が不正（配列外アクセス）なことが原因です。
対処の選択肢（いずれか）
- もっとも簡単: P4 の BME680 ドライバを P3 と同等の実装（校正データの取り扱いが正しいもの）に置き換える。
- もしくは P4 ドライバの _read_calibration 内の係数マッピングを修正し、読み出しバイト数（25+16=41）の範囲内でインデックスするように直す。
- 併せて、必要に応じてページセレクト（0x73）扱いや、ソフトリセット後の待機時間の見直しも検討すると安定しますが、今回の直接原因は配列外参照です。
検証のヒント
- 0x89 から 25 バイト、0xE1 から 16 バイトの read が本当に 25/16 バイト返っているかを print で長さ確認。
- その上で、参照しているインデックスが 0〜40 に収まっているかを確認。現在の P4 実装は 41 を超える添字を参照している箇所があります。
P4 の main は BME680 のラッパークラス（BME680）を通して初期化しており、そこで上記の _read_calibration が呼ばれエラーになっています。P3 は BME680_I2C を直接使っていて、こちらの実装は安全側です。

-  EnvironmentalDatamonitorの機能を削除する。（すなわちターミナル上のリアルタイムデータで稼働を確認するよう簡略化）




# Ver2.11 zeroOne
- 作業フォルダは下記 G:\RPi-Development\RaspPi5_APconnection\ForZero\Ver2.11zeroOne
- 改定部位は日本語と英語のdocumentを作成して初心者にもわかりやすくする。documentにはVerのnumberingを実施する。
- P1に対してもBME680を接続して気温、相対湿度、絶対湿度、ガス抵抗のデータを取得し、p２以降のデータユニットと同じく可視化とデータ蓄積を行うよう改良する。
- P1の改良に合わせてインストールマニュアルや構造説明のdocumentを一新する。すべて日本語と英語で作成する。



# Ver2.1 zeroOne
- 作業フォルダは下記 G:\RPi-Development\RaspPi5_APconnection\ForZero\Ver2.00zeroOne
- 改定部位は日本語と英語のdocumentを作成して初心者にもわかりやすくする。documentにはVerのnumberingを実施する。
- G:\RPi-Development\RaspPi5_APconnection\ForZero\Ver2.00zeroOne\p1_software_solo405のシステムにおいてP2,3,4,5,6の電波強度やpingを測定しターミナル上に定期的（80秒ごと）にレポートする機能を追加する
- P1_ap_setup_solo.pyの機能を最新のVer2.0に適合するよう改訂する。また改訂内容は同一のap_setupディレクトリ内に日本語でレポートする。


# Ver2.0 zeroOne
- 作業フォルダは下記 G:\RPi-Development\RaspPi5_APconnection\ForZero\Ver2.00zeroOne
- 改定部位は日本語と英語のdocumentを作成して初心者にもわかりやすくする。documentにはVerのnumberingを実施する。
- このVer2はBME680のみで動作、データ収集するシステムとする。
- そのためP1のデータ収集、Web可視化からCO2センサに関する記述をすべて無効化する。
- 極力原型は残しつつコメントアウトで無効化すること。
- 生成するCSVファイルの形式やP2,P3,P4,P5,P6もMZ-H19が無効化した状態で正常に稼働するように設計しなおす。

# Ver1.7
- 作業フォルダは下記 G:\RPi-Development\RaspPi5_APconnection\ForZero\Ver1.00zero
- 改定部位は日本語と英語のdocumentを作成して初心者にもわかりやすくする。documentにはVerのnumberingを実施する。
- Pico2Wで駆動するP2やP3についてもRaspberryZero2Wで駆動するP1に対応できる改良を実施する。
- すなわちP2からP6までの５つのセンサーの情報をP1で受け取ってグラフ化できるようにする。P2とP3をP1で受信できるように両者を改良
- 変更ログはP2-P6MergeV1.7.mdというテキストを作成し日本語で内容変更を記載する。

# Ver1.6
- 作業フォルダは下記 G:\RPi-Development\RaspPi5_APconnection\ForZero\Ver1.00zero
- 改定部位は日本語と英語のdocumentを作成して初心者にもわかりやすくする。documentにはVerのnumberingを実施する。
- P1の設定値を下記に変更する。この設定に合わせて関連するP2,P3,P4,P5､P6の接続設定値も変更する
    "ap_ssid": "RaspberryPi5_AP_Solo2",
    "ap_password": "raspberry",
    "ap_ip": "192.168.0.2",
- 

# Ver1.5
- 作業フォルダは下記 G:\RPi-Development\RaspPi5_APconnection\ForZero\Ver1.00zero
- 改定部位は日本語と英語のdocumentを作成して初心者にもわかりやすくする。documentにはVerのnumberingを実施する。
- raspberrypiZero2WをP1に用いる場合を想定したSetupプログラムを再構築する。
- P1（raspberryPiZero2w）の電源ONに併せて集計プログラムとInterface,Monitorプログラムを順次自動起動するためのプログラムおよびマニュアルを日本語と英語で作成。
- 自動起動時には不具合があった場合、プログラムの再起動またはエラーが連続する場合はZero2W自体を再起動するような保全＋自己診断を実施する。

# Ver1.2
- 作業フォルダは下記 G:\RPi-Development\RaspPi5_APconnection\ForZero\Ver1.00zero
- 改定部位は日本語と英語のdocumentを作成して初心者にもわかりやすくする。documentにはVerのnumberingを実施する。
- P1からP6までの各フォルダ内部階層ごとにその階層のプログラムの機能を記載した日本語の機能説明documentを追加する。
- P1の構造をなるべく動作を軽くするための工夫を実施する各処理に対してrestTimeを追加する。データの受信頻度やターミナルの更新頻度も減らす。
- P1のWebInterFaceはテキスト情報のみでグラフ描画は実施しない仕様に簡略化する。

# Ver1.0
- 作業フォルダは下記 G:\RPi-Development\RaspPi5_APconnection\ForZero\Ver1.00zero
- 改定部位は日本語と英語のdocumentを作成して初心者にもわかりやすくする。documentにはVerのnumberingを実施する。
- P2とP3のナンバリングを変更しP4,P5、P6の３デバイスを統括できるようにプログラムを改良する。これらはラズパイPico2Wで使用する。

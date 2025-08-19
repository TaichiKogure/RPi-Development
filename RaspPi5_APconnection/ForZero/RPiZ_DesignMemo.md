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

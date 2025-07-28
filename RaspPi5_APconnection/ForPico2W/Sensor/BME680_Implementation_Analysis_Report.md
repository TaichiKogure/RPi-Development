# BME680センサー実装の比較分析レポート

## 概要

このレポートは、2つの異なるディレクトリに存在するBME680センサー実装の比較分析を行い、`G:\RPi-Development\RaspPi5_APconnection\ForPico2W\Sensor\`の実装で発生している問題（特に気圧とガス抵抗値の測定に関する問題）の原因を特定し、解決策を提案するものです。

## 分析対象

1. **正常に動作する実装**：`G:\RPi-Development\OK2bme\`
2. **問題のある実装**：`G:\RPi-Development\RaspPi5_APconnection\ForPico2W\Sensor\`

## 実装の構造比較

### OK2bme実装

1. **ドライバ構造**：
   - `Adafruit_BME680`をベースクラスとし、`BME680_I2C`と`BME680_SPI`の2つの派生クラスを持つ
   - Adafruit社のCircuitPythonドライバをベースにしている
   - 広範囲にテストされた実装

2. **メインプログラム**：
   - シンプルな構造
   - I2Cバスを初期化し、BME680_I2Cオブジェクトを作成
   - 無限ループでセンサーデータを読み取り、表示

### ForPico2W実装

1. **ドライバ構造**：
   - 単一の`BME680_I2C`クラスのみ
   - Boschのデータシートとアダフルーツのドライバを参考に独自実装
   - ベースクラスがなく、SPIサポートもない

2. **メインプログラム**：
   - OK2bme実装と同様の基本構造
   - エラー処理とLED表示機能が追加されている
   - I2Cアドレスの自動検出機能がある

## 主要な実装の違い

### 1. データ読み取りアプローチ

**OK2bme実装**：
- `_perform_reading()`メソッドでセンサーからデータを一度に読み取り、内部変数に保存
- 各プロパティ（温度、湿度など）にアクセスする際は、必要に応じて新しい読み取りを行う（リフレッシュレートに基づく）
- 一度の読み取りで全てのデータを取得するため、効率的

```python
def _perform_reading(self):
    # ... (センサーの設定)
    new_data = False
    while not new_data:
        data = self._read(_BME680_REG_MEAS_STATUS, 15)
        new_data = data[0] & 0x80 != 0
        time.sleep(0.005)
    
    self._adc_pres = _read24(data[2:5]) / 16
    self._adc_temp = _read24(data[5:8]) / 16
    self._adc_hum = struct.unpack('>H', bytes(data[8:10]))[0]
    self._adc_gas = int(struct.unpack('>H', bytes(data[13:15]))[0] / 64)
    self._gas_range = data[14] & 0x0F
    
    # t_fineの計算
    var1 = (self._adc_temp / 8) - (self._temp_calibration[0] * 2)
    var2 = (var1 * self._temp_calibration[1]) / 2048
    var3 = ((var1 / 2) * (var1 / 2)) / 4096
    var3 = (var3 * self._temp_calibration[2] * 16) / 16384
    self._t_fine = int(var2 + var3)
```

**ForPico2W実装**：
- 各プロパティ（温度、湿度など）にアクセスするたびに`_read_raw_data()`メソッドを呼び出し、新しい測定を行う
- 各測定ごとに新しいデータを取得するため、非効率的
- 連続した測定間で一貫性が保証されない

```python
def _read_raw_data(self):
    # センサーを強制モードに設定して測定をトリガー
    ctrl_meas = self._read_byte(_BME680_CTRL_MEAS)
    self._write_byte(_BME680_CTRL_MEAS, ctrl_meas | 0x01)
    
    # 測定が完了するのを待つ
    while self._read_byte(_BME680_STATUS) & 0x80:
        time.sleep(0.001)
        
    # データを読み取る
    data = self._read_bytes(_BME680_PRESS_MSB, 8)
    
    # データを解析
    raw_temp = ((data[3] << 16) | (data[4] << 8) | data[5]) >> 4
    raw_pres = ((data[0] << 16) | (data[1] << 8) | data[2]) >> 4
    raw_hum = (data[6] << 8) | data[7]
    
    # ガス抵抗データを読み取る
    gas_data = self._read_bytes(_BME680_GAS_R_MSB, 2)
    raw_gas = (gas_data[0] << 2) | (gas_data[1] >> 6)
    gas_range = gas_data[1] & 0x0F
    
    return raw_temp, raw_pres, raw_hum, raw_gas, gas_range
```

### 2. 校正データの構造

**OK2bme実装**：
- 校正データをリストとして保存
- インデックスでアクセス（例：`self._temp_calibration[0]`）

```python
self._temp_calibration = [coeff[x] for x in [23, 0, 1]]
self._pressure_calibration = [coeff[x] for x in [3, 4, 5, 7, 8, 10, 9, 12, 13, 14]]
self._humidity_calibration = [coeff[x] for x in [17, 16, 18, 19, 20, 21, 22]]
self._gas_calibration = [coeff[x] for x in [25, 24, 26]]
```

**ForPico2W実装**：
- 校正データを辞書として保存
- キーでアクセス（例：`self.temp_calib['par_t1']`）

```python
self.temp_calib = {
    'par_t1': (coeff1[9] << 8) | coeff1[8],
    'par_t2': (coeff1[11] << 8) | coeff1[10],
    'par_t3': coeff1[12]
}

self.pres_calib = {
    'par_p1': (coeff1[1] << 8) | coeff1[0],
    'par_p2': (coeff1[3] << 8) | coeff1[2],
    # ...その他のパラメータ
}
```

### 3. 気圧計算の違い

**OK2bme実装**：
```python
def pressure(self):
    """The barometric pressure in hectoPascals"""
    self._perform_reading()
    var1 = (self._t_fine / 2) - 64000
    var2 = ((var1 / 4) * (var1 / 4)) / 2048
    var2 = (var2 * self._pressure_calibration[5]) / 4
    var2 = var2 + (var1 * self._pressure_calibration[4] * 2)
    var2 = (var2 / 4) + (self._pressure_calibration[3] * 65536)
    var1 = (((((var1 / 4) * (var1 / 4)) / 8192) *
            (self._pressure_calibration[2] * 32) / 8) +
            ((self._pressure_calibration[1] * var1) / 2))
    var1 = var1 / 262144
    var1 = ((32768 + var1) * self._pressure_calibration[0]) / 32768
    calc_pres = 1048576 - self._adc_pres
    calc_pres = (calc_pres - (var2 / 4096)) * 3125
    calc_pres = (calc_pres / var1) * 2
    var1 = (self._pressure_calibration[8] * (((calc_pres / 8) * (calc_pres / 8)) / 8192)) / 4096
    var2 = ((calc_pres / 4) * self._pressure_calibration[7]) / 8192
    var3 = (((calc_pres / 256) ** 3) * self._pressure_calibration[9]) / 131072
    calc_pres += ((var1 + var2 + var3 + (self._pressure_calibration[6] * 128)) / 16)
    return calc_pres/100
```

**ForPico2W実装**：
```python
def _calc_pressure(self, raw_pres):
    """Calculate the pressure from raw data."""
    var1 = (self.t_fine / 2.0) - 64000.0
    var2 = var1 * var1 * self.pres_calib['par_p6'] / 131072.0
    var2 = var2 + (var1 * self.pres_calib['par_p5'] * 2.0)
    var2 = (var2 / 4.0) + (self.pres_calib['par_p4'] * 65536.0)
    var1 = ((self.pres_calib['par_p3'] * var1 * var1 / 16384.0) + 
            (self.pres_calib['par_p2'] * var1)) / 524288.0
    var1 = (1.0 + (var1 / 32768.0)) * self.pres_calib['par_p1']
    
    if var1 == 0:
        return 0
        
    pressure = 1048576.0 - raw_pres
    pressure = ((pressure - (var2 / 4096.0)) * 6250.0) / var1
    var1 = self.pres_calib['par_p9'] * pressure * pressure / 2147483648.0
    var2 = pressure * self.pres_calib['par_p8'] / 32768.0
    pressure = pressure + ((var1 + var2 + self.pres_calib['par_p7']) / 16.0)
    
    return pressure / 100.0  # Convert to hPa
```

### 4. ガス抵抗計算の違い

**OK2bme実装**：
- ルックアップテーブルを使用
- 複雑な計算式

```python
def gas(self):
    """The gas resistance in ohms"""
    self._perform_reading()
    var1 = ((1340 + (5 * self._sw_err)) * (_LOOKUP_TABLE_1[self._gas_range])) / 65536
    var2 = ((self._adc_gas * 32768) - 16777216) + var1
    var3 = (_LOOKUP_TABLE_2[self._gas_range] * var1) / 512
    calc_gas_res = (var3 + (var2 / 2)) / var2
    return int(calc_gas_res)
```

**ForPico2W実装**：
- ルックアップテーブルを使用せず、直接計算
- 異なる計算式

```python
def _calc_gas_resistance(self, raw_gas, gas_range):
    """Calculate the gas resistance from raw data."""
    var1 = 1340.0 + (5.0 * self.range_sw_err)
    var2 = var1 * (1.0 + self.gas_calib['par_g1'] / 100.0)
    var3 = 1.0 + (self.gas_calib['par_g2'] / 100.0)
    var4 = var3 * (1.0 + (self.gas_calib['par_g3'] / 100.0))
    var5 = 1.0 + (self.res_heat_range / 4.0)
    var6 = 1.0 + (self.res_heat_val / 64.0)
    
    # ガス抵抗を計算
    gas_res = 1.0 / (var4 * (1.0 + (var1 * (raw_gas / 512.0))))
    
    # レンジ固有の乗数を適用
    range_multiplier = 1.0 / (1 << gas_range)
    gas_res = gas_res * range_multiplier
    
    return gas_res
```

## 問題の原因

ForPico2W実装で気圧とガス抵抗値が正しく表示されない主な原因は以下の通りです：

### 1. ガス抵抗計算の問題

**主な問題点**：
- ルックアップテーブルの欠如
- 計算式の違い
- 校正データの解釈の違い

OK2bme実装では、ガス抵抗の計算に2つのルックアップテーブル（`_LOOKUP_TABLE_1`と`_LOOKUP_TABLE_2`）を使用していますが、ForPico2W実装ではこれらのテーブルを使用せず、異なる計算式を採用しています。これにより、ガス抵抗値の計算結果が大きく異なる可能性があります。

```python
# OK2bme実装のルックアップテーブル
_LOOKUP_TABLE_1 = (2147483647.0, 2147483647.0, 2147483647.0, 2147483647.0, 2147483647.0,
                   2126008810.0, 2147483647.0, 2130303777.0, 2147483647.0, 2147483647.0,
                   2143188679.0, 2136746228.0, 2147483647.0, 2126008810.0, 2147483647.0,
                   2147483647.0)

_LOOKUP_TABLE_2 = (4096000000.0, 2048000000.0, 1024000000.0, 512000000.0, 255744255.0, 127110228.0,
                   64000000.0, 32258064.0, 16016016.0, 8000000.0, 4000000.0, 2000000.0, 1000000.0,
                   500000.0, 250000.0, 125000.0)
```

### 2. 測定アプローチの違い

ForPico2W実装では、各プロパティ（温度、湿度、気圧、ガス抵抗）にアクセスするたびに新しい測定を行います。これにより、以下の問題が発生する可能性があります：

1. 連続した測定間での一貫性の欠如
2. 測定ごとに異なる校正状態
3. 特にガス抵抗測定において、ヒーターの安定化時間が不足

例えば、以下のコードでは、各プロパティにアクセスするたびに新しい測定が行われます：

```python
# ForPicoBME680Simple.pyの一部
temperature = bme.temperature  # 新しい測定
humidity = bme.humidity        # 新しい測定
pressure = bme.pressure        # 新しい測定
gas = bme.gas                  # 新しい測定
```

これに対して、OK2bme実装では、リフレッシュレートに基づいて必要な場合にのみ新しい測定を行い、一度の測定で全てのデータを取得します。

### 3. 校正データの解釈の違い

ForPico2W実装では、校正データを辞書として保存し、OK2bme実装とは異なる方法でアクセスしています。これにより、校正データの解釈に違いが生じ、計算結果に影響を与える可能性があります。

## 解決策

ForPico2W実装の問題を解決するために、以下の修正を提案します：

### 1. ガス抵抗計算の修正

OK2bme実装と同様のルックアップテーブルと計算式を採用します：

```python
# ルックアップテーブルを追加
_LOOKUP_TABLE_1 = (2147483647.0, 2147483647.0, 2147483647.0, 2147483647.0, 2147483647.0,
                   2126008810.0, 2147483647.0, 2130303777.0, 2147483647.0, 2147483647.0,
                   2143188679.0, 2136746228.0, 2147483647.0, 2126008810.0, 2147483647.0,
                   2147483647.0)

_LOOKUP_TABLE_2 = (4096000000.0, 2048000000.0, 1024000000.0, 512000000.0, 255744255.0, 127110228.0,
                   64000000.0, 32258064.0, 16016016.0, 8000000.0, 4000000.0, 2000000.0, 1000000.0,
                   500000.0, 250000.0, 125000.0)

# ガス抵抗計算メソッドを修正
def _calc_gas_resistance(self, raw_gas, gas_range):
    """Calculate the gas resistance from raw data."""
    var1 = ((1340 + (5 * self.range_sw_err)) * (_LOOKUP_TABLE_1[gas_range])) / 65536
    var2 = ((raw_gas * 32768) - 16777216) + var1
    var3 = (_LOOKUP_TABLE_2[gas_range] * var1) / 512
    calc_gas_res = (var3 + (var2 / 2)) / var2
    return int(calc_gas_res)
```

### 2. 測定アプローチの改善

OK2bme実装と同様に、一度の測定で全てのデータを取得し、内部変数に保存するアプローチを採用します：

```python
def _perform_reading(self):
    """Perform a single-shot reading from the sensor and fill internal data structure for calculations"""
    # センサーを設定
    ctrl_meas = self._read_byte(_BME680_CTRL_MEAS)
    self._write_byte(_BME680_CTRL_MEAS, ctrl_meas | 0x01)
    
    # 測定が完了するのを待つ
    while self._read_byte(_BME680_STATUS) & 0x80:
        time.sleep(0.001)
        
    # データを読み取る
    data = self._read_bytes(_BME680_PRESS_MSB, 8)
    
    # データを解析
    self._raw_temp = ((data[3] << 16) | (data[4] << 8) | data[5]) >> 4
    self._raw_pres = ((data[0] << 16) | (data[1] << 8) | data[2]) >> 4
    self._raw_hum = (data[6] << 8) | data[7]
    
    # ガス抵抗データを読み取る
    gas_data = self._read_bytes(_BME680_GAS_R_MSB, 2)
    self._raw_gas = (gas_data[0] << 2) | (gas_data[1] >> 6)
    self._gas_range = gas_data[1] & 0x0F
    
    # t_fineを計算
    var1 = ((self._raw_temp / 16384.0) - (self.temp_calib['par_t1'] / 1024.0)) * self.temp_calib['par_t2']
    var2 = (((self._raw_temp / 131072.0) - (self.temp_calib['par_t1'] / 8192.0)) ** 2) * self.temp_calib['par_t3'] * 16
    self.t_fine = var1 + var2
```

そして、各プロパティメソッドを修正して、必要に応じて`_perform_reading()`を呼び出すようにします：

```python
@property
def temperature(self):
    """Get the temperature in degrees Celsius."""
    self._perform_reading()
    return self.t_fine / 5120.0

@property
def pressure(self):
    """Get the pressure in hPa."""
    self._perform_reading()
    return self._calc_pressure(self._raw_pres)

@property
def humidity(self):
    """Get the relative humidity in percent."""
    self._perform_reading()
    return self._calc_humidity(self._raw_hum)

@property
def gas(self):
    """Get the gas resistance in ohms."""
    self._perform_reading()
    return int(self._calc_gas_resistance(self._raw_gas, self._gas_range))
```

### 3. OK2bme実装の採用

最も確実な解決策は、既に正常に動作していることが確認されているOK2bme実装をそのまま採用することです。具体的には：

1. `G:\RPi-Development\OK2bme\bme680.py`をForPico2W実装にコピー
2. 必要に応じて、ForPico2W実装のエラー処理やLED表示機能を追加

## まとめ

ForPico2W実装で気圧とガス抵抗値が正しく表示されない主な原因は、ガス抵抗計算の違い、測定アプローチの違い、および校正データの解釈の違いです。これらの問題を解決するためには、OK2bme実装のアプローチを採用するか、提案した修正を実装することが推奨されます。

特に、ガス抵抗計算においてルックアップテーブルを使用することと、一度の測定で全てのデータを取得するアプローチを採用することが重要です。これにより、ForPico2W実装でも正確な気圧とガス抵抗値を取得できるようになるでしょう。
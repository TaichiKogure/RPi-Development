# Flask App and WiFi Monitor Fix

## 問題の概要 / Problem Overview

システムに以下の2つの問題が発生していました：
The system had the following two issues:

1. **Flask アプリのルートが index.html を返していない**
   **Flask app's root route not returning index.html**
   - P1_app_solo.py から P1_app_solo_new.py への移行により、テンプレートの生成が行われなくなった
   - The migration from P1_app_solo.py to P1_app_solo_new.py caused templates to no longer be generated

2. **WiFi モニターの初期化エラー**
   **WiFi monitor initialization error**
   - `Failed to initialize WiFi monitor: 'log_dir'` というエラーが発生
   - Error message: `Failed to initialize WiFi monitor: 'log_dir'`
   - start_p1_solo.py の DEFAULT_CONFIG に "log_dir" が定義されていなかった
   - "log_dir" was not defined in DEFAULT_CONFIG in start_p1_solo.py

## 原因分析 / Root Cause Analysis

### 1. Flask アプリのルート問題 / Flask App Root Route Issue

- **P1_app_solo.py** は `create_templates()` 関数を使用して、テンプレートディレクトリとテンプレートファイル（index.html など）を動的に生成していました。
- **P1_app_solo.py** used the `create_templates()` function to dynamically generate the templates directory and template files (including index.html).

- **P1_app_solo_new.py** は refactored_main() を呼び出すだけのラッパーで、テンプレートの生成を行っていませんでした。
- **P1_app_solo_new.py** was just a wrapper that called refactored_main() and did not generate templates.

- **main.py** （refactored_main() の実装）は、テンプレートディレクトリが既に存在し、index.html が含まれていることを前提としていました。
- **main.py** (the implementation of refactored_main()) assumed that the templates directory already existed and contained index.html.

### 2. WiFi モニター初期化エラー / WiFi Monitor Initialization Error

- **start_p1_solo.py** の DEFAULT_CONFIG に "log_dir" キーが定義されていなかったため、WiFi モニターの初期化時にエラーが発生していました。
- The "log_dir" key was not defined in DEFAULT_CONFIG in start_p1_solo.py, causing an error during WiFi monitor initialization.

## 実施した修正 / Implemented Fixes

### 1. Flask アプリのルート問題の修正 / Fix for Flask App Root Route Issue

1. **main.py** を修正して、P1_app_solo.py から create_templates() 関数をインポートするようにしました：
   Modified **main.py** to import the create_templates() function from P1_app_solo.py:

   ```python
   # Import create_templates function from P1_app_solo.py
   try:
       from p1_software_solo405.web_interface.P1_app_solo import create_templates
       logger.info("Successfully imported create_templates from P1_app_solo")
   except ImportError as e:
       logger.warning(f"Failed to import create_templates from P1_app_solo: {e}")
       # Define a fallback create_templates function
       def create_templates():
           """Create basic templates if P1_app_solo.create_templates is not available."""
           templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
           os.makedirs(templates_dir, exist_ok=True)
           
           # Create a basic index.html template
           index_html = """<!DOCTYPE html>
   <html lang="en">
   <head>
       <meta charset="UTF-8">
       <meta name="viewport" content="width=device-width, initial-scale=1.0">
       <title>Environmental Data Monitor - Solo</title>
       <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
       <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
       <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
       <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
   </head>
   <body>
       <div class="container">
           <h1>Environmental Data Monitor - Solo</h1>
           <p>Welcome to the Environmental Data Monitor. Please use the navigation to view data.</p>
       </div>
   </body>
   </html>"""
           
           with open(os.path.join(templates_dir, 'index.html'), 'w') as f:
               f.write(index_html)
           
           logger.info("Created basic templates as fallback")
   ```

2. **main.py** の main() 関数を修正して、create_templates() を呼び出すようにしました：
   Modified the main() function in **main.py** to call create_templates():

   ```python
   def main():
       # ... existing code ...
       
       # Create templates
       try:
           logger.info("Creating templates...")
           create_templates()
           logger.info("Templates created successfully")
       except Exception as e:
           logger.error(f"Error creating templates: {e}")
           # Continue anyway, as the templates might already exist
       
       # ... existing code ...
   ```

### 2. WiFi モニター初期化エラーの修正 / Fix for WiFi Monitor Initialization Error

**start_p1_solo.py** の DEFAULT_CONFIG に "log_dir" キーを追加しました：
Added the "log_dir" key to DEFAULT_CONFIG in **start_p1_solo.py**:

```python
DEFAULT_CONFIG = {
    "data_dir": "/var/lib/raspap_solo/data",
    "rawdata_p2_dir": "RawData_P2",
    "rawdata_p3_dir": "RawData_P3",
    "web_port": 80,
    "api_port": 5001,
    "monitor_port": 5002,
    "monitor_interval": 5,  # seconds
    "interface": "wlan0",
    "ap_ssid": "RaspberryPi5_AP_Solo",
    "ap_ip": "192.168.0.1",
    "log_dir": "/var/log"  # Added log_dir to fix WiFi monitor initialization error
}
```

## 期待される効果 / Expected Results

1. **Flask アプリのルート問題**：
   **Flask App Root Route Issue**:
   - テンプレートディレクトリとindex.htmlが正しく生成されるようになります。
   - The templates directory and index.html will now be correctly generated.
   - ルートURL（/）にアクセスすると、index.htmlが表示されるようになります。
   - Accessing the root URL (/) will now display index.html.

2. **WiFi モニター初期化エラー**：
   **WiFi Monitor Initialization Error**:
   - "log_dir" が DEFAULT_CONFIG に定義されたため、WiFi モニターが正常に初期化されるようになります。
   - The WiFi monitor will now initialize correctly because "log_dir" is defined in DEFAULT_CONFIG.
   - `Failed to initialize WiFi monitor: 'log_dir'` エラーが解消されます。
   - The `Failed to initialize WiFi monitor: 'log_dir'` error will be resolved.

## 注意事項 / Notes

- これらの修正は、P1_app_solo.py から P1_app_solo_new.py への移行に伴う問題を解決するためのものです。
- These fixes are intended to resolve issues related to the migration from P1_app_solo.py to P1_app_solo_new.py.
- 今後、さらなるリファクタリングを行う場合は、テンプレートの生成方法を見直すことを検討してください。
- If further refactoring is done in the future, consider reviewing the template generation approach.
- 特に、テンプレートを動的に生成するのではなく、静的なファイルとして提供することを検討してください。
- In particular, consider providing templates as static files rather than generating them dynamically.
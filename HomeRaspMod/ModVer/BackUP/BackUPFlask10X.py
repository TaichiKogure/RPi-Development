from flask import Flask, request, jsonify, render_template_string
import csv
from datetime import datetime, timedelta
import logging
import os
import threading
import time
from logging.handlers import RotatingFileHandler
from collections import deque, defaultdict
from queue import Queue, Empty
import re

# =====================
# Centralized Config
# =====================
PORT = 8888
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'flask10x.log')
LOG_MAX_BYTES = 1 * 1024 * 1024  # 1 MB
LOG_BACKUP_COUNT = 5
HISTORY_MAX = 1000

CSV_PICODATA = os.path.join(os.path.dirname(__file__), 'PicodataX.csv')
CSV_BEDROOM = os.path.join(os.path.dirname(__file__), 'BedRoomEnv.csv')
CSV_OUTSIDE = os.path.join(os.path.dirname(__file__), 'OutsideEnv.csv')
CSV_LR = os.path.join(os.path.dirname(__file__), 'LR_env.csv')

# Fixed CSV column orders (Step 6)
COLUMNS_PICODATA = ["current_time", "Pressure", "Tempereture"]
COLUMNS_BEDROOM = ["current_time", "CO2", "Tempereture", "Humidity", "Pressure", "GasResistance"]
COLUMNS_OUTSIDE = ["current_time", "Temperature-outside", "Humidity-outside", "Pressure-outside", "GasResistance-outside"]
COLUMNS_LR = [
    "current_time",
    "CO2",
    "AnalogValue",
    "Voltage",
    "Temperature_DS18B20",
    "Temperature_DHT11",
    "Humidity_DHT11",
]

# Async writer configuration (Step 4/5)
WRITE_QUEUE_MAXSIZE = 5000
WRITE_RETRIES = 3
WRITE_BACKOFF_BASE_SEC = 0.05

# Metrics & thresholds (Steps 8/9)
QUEUE_WARN_THRESHOLD = int(WRITE_QUEUE_MAXSIZE * 0.8)  # warn at 80% full
INACTIVITY_WARN_SEC = 120  # warn if endpoint inactive for 2 minutes

# =====================
# Logger Setup
# =====================
os.makedirs(LOG_DIR, exist_ok=True)
logger = logging.getLogger('flask10x')
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = RotatingFileHandler(LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

app = Flask(__name__)

# bounded request history
request_history = deque(maxlen=HISTORY_MAX)

# global write queue and per-file locks
write_queue: "Queue[dict]" = Queue(maxsize=WRITE_QUEUE_MAXSIZE)
file_locks = defaultdict(threading.Lock)

# metrics state
write_success_total = 0
write_error_total = 0
metrics_lock = threading.Lock()
last_received = {
    'data': None,
    'data2': None,
    'data3': None,
    'data4': None,
}

_worker_started = False


def _ensure_parent_dir(path: str):
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


def _needs_header(path: str) -> bool:
    try:
        return not os.path.exists(path) or os.path.getsize(path) == 0
    except Exception:
        # If we cannot stat the file, try to write header to be safe once
        return True


def _write_csv_row(file_path: str, columns: list, row: dict):
    """Write a single row to CSV with retries, exclusive per-file lock, flush+fsync.
    Assumes row keys match columns; fills missing with empty string when writing."""
    lock = file_locks[file_path]
    attempt = 0
    last_exc = None
    while attempt < WRITE_RETRIES:
        try:
            with lock:
                _ensure_parent_dir(file_path)
                header_needed = _needs_header(file_path)
                with open(file_path, 'a', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=columns)
                    if header_needed:
                        writer.writeheader()
                    # fill missing values consistently
                    safe_row = {col: row.get(col, "") for col in columns}
                    writer.writerow(safe_row)
                    f.flush()
                    os.fsync(f.fileno())
            return True
        except Exception as e:
            last_exc = e
            attempt += 1
            sleep_dur = WRITE_BACKOFF_BASE_SEC * (2 ** (attempt - 1))
            logger.warning(f"CSV write failed for {file_path} (attempt {attempt}/{WRITE_RETRIES}): {e}. Retrying in {sleep_dur:.2f}s")
            time.sleep(sleep_dur)
    logger.error(f"CSV write permanently failed for {file_path}: {last_exc}")
    return False


def _writer_worker():
    global write_success_total, write_error_total
    logger.info("CSV writer worker started")
    while True:
        try:
            job = write_queue.get(timeout=1.0)
        except Empty:
            # periodic idle loop; could add housekeeping
            continue
        try:
            ok = _write_csv_row(job['file_path'], job['columns'], job['row'])
            with metrics_lock:
                if ok:
                    write_success_total += 1
                else:
                    write_error_total += 1
        finally:
            write_queue.task_done()


def _metrics_monitor():
    """Background monitor to emit WARN logs on queue backlog and endpoint inactivity."""
    last_queue_warned = False
    while True:
        try:
            qlen = write_queue.qsize()
            if qlen >= QUEUE_WARN_THRESHOLD:
                if not last_queue_warned:
                    logger.warning(f"Write queue high watermark reached: {qlen}/{WRITE_QUEUE_MAXSIZE}")
                    last_queue_warned = True
            else:
                last_queue_warned = False

            # inactivity checks
            now = datetime.now()
            for ep, ts in list(last_received.items()):
                if ts is None:
                    continue
                idle = (now - ts).total_seconds()
                if idle >= INACTIVITY_WARN_SEC:
                    logger.warning(f"Endpoint '{ep}' inactive for {int(idle)}s (threshold {INACTIVITY_WARN_SEC}s)")
        except Exception as e:
            logger.error(f"Metrics monitor error: {e}")
        time.sleep(5)


def _start_writer_once():
    global _worker_started
    if not _worker_started:
        t = threading.Thread(target=_writer_worker, name="csv-writer", daemon=True)
        t.start()
        m = threading.Thread(target=_metrics_monitor, name="metrics-monitor", daemon=True)
        m.start()
        _worker_started = True


# start the worker immediately (safe with daemon thread)
_start_writer_once()

# =====================
# Validation Utilities
# =====================
class ValidationError(Exception):
    def __init__(self, message, details=None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


def _to_number(value):
    """Convert value that may include units to float. Accepts int/float or strings like '1013hPa', '25C'."""
    if value is None:
        raise ValueError('missing value')
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        # Replace comma decimal, strip non numeric except . -
        cleaned = re.sub(r'[^0-9+\-\.eE]', '', value.replace(',', '.'))
        if cleaned.strip() == '':
            raise ValueError(f'invalid numeric string: {value!r}')
        return float(cleaned)
    raise ValueError(f'unsupported type: {type(value).__name__}')


def validate_and_normalize(payload, schema):
    """
    Validate payload against schema. Schema example:
    {
        'pressure': {'type': 'number', 'min': 0, 'max': 2000},
        'temperature': {'type': 'number', 'min': -50, 'max': 150},
        'nested': {'type': 'object', 'schema': { 'co2': {'type': 'number', 'min': 0} }}
    }
    Returns normalized dict with numbers converted.
    """
    errors = {}
    out = {}

    def _validate(obj, sch, out_dict, path=''):
        nonlocal errors
        for key, rule in sch.items():
            full_key = f"{path}.{key}" if path else key
            if rule.get('type') == 'object':
                sub_schema = rule.get('schema', {})
                value = (obj or {}).get(key)
                if value is None:
                    errors[full_key] = 'required field missing'
                    continue
                if not isinstance(value, dict):
                    errors[full_key] = 'must be an object'
                    continue
                out_dict[key] = {}
                _validate(value, sub_schema, out_dict[key], full_key)
            else:
                value = (obj or {}).get(key)
                if value is None:
                    errors[full_key] = 'required field missing'
                    continue
                try:
                    if rule.get('type') == 'number':
                        num = _to_number(value)
                        if 'min' in rule and num < rule['min']:
                            raise ValueError(f'below minimum {rule["min"]}')
                        if 'max' in rule and num > rule['max']:
                            raise ValueError(f'above maximum {rule["max"]}')
                        out_dict[key] = num
                    elif rule.get('type') == 'string':
                        out_dict[key] = str(value)
                    else:
                        out_dict[key] = value
                except ValueError as e:
                    errors[full_key] = str(e)

    _validate(payload, schema, out)
    if errors:
        raise ValidationError('validation failed', errors)
    return out

# Schemas per endpoint
SCHEMA_DATA = {
    'pressure': {'type': 'number', 'min': 0, 'max': 2000},   # hPa
    'temperature': {'type': 'number', 'min': -50, 'max': 150},  # °C
}

SCHEMA_DATA2 = {
    'co2': {'type': 'number', 'min': 0, 'max': 200000},
    'temperature': {'type': 'number', 'min': -50, 'max': 150},
    'humidity': {'type': 'number', 'min': 0, 'max': 100},
    'pressure': {'type': 'number', 'min': 0, 'max': 2000},
    'gas_res': {'type': 'number', 'min': 0},
}

SCHEMA_DATA3 = {
    'temperature': {'type': 'number', 'min': -50, 'max': 150},
    'humidity': {'type': 'number', 'min': 0, 'max': 100},
    'pressure': {'type': 'number', 'min': 0, 'max': 2000},
    'gas_res': {'type': 'number', 'min': 0},
}

SCHEMA_DATA4 = {
    'mh_z19': {'type': 'object', 'schema': {
        'co2': {'type': 'number', 'min': 0, 'max': 200000}
    }},
    'mq_2': {'type': 'object', 'schema': {
        'analog_value': {'type': 'number', 'min': 0},
        'voltage': {'type': 'number', 'min': 0}
    }},
    'ds18b20': {'type': 'object', 'schema': {
        'temperature': {'type': 'number', 'min': -50, 'max': 150}
    }},
    'dht11': {'type': 'object', 'schema': {
        'temperature': {'type': 'number', 'min': -50, 'max': 150},
        'humidity': {'type': 'number', 'min': 0, 'max': 100}
    }},
}

def enqueue_csv(file_path: str, columns: list, row: dict) -> bool:
    """Enqueue a CSV write job. Returns True if enqueued, False if queue is full."""
    job = {
        'file_path': file_path,
        'columns': columns,
        'row': row,
    }
    try:
        write_queue.put_nowait(job)
        qlen = write_queue.qsize()
        if qlen >= QUEUE_WARN_THRESHOLD:
            logger.warning(f"Write queue backlog high: size={qlen}/{WRITE_QUEUE_MAXSIZE}")
        return True
    except Exception:
        logger.error(f"Write queue full; dropping job for {file_path}")
        return False


# =====================
# Routes
# =====================
@app.route('/')
def hello():
    logger.info('GET / - hello world served')
    return "Hello world"


@app.route('/healthz')
def healthz():
    return jsonify({'status': 'ok'}), 200


@app.route('/data', methods=['POST'])
def handle_data():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = request.get_json(silent=True) or {}
    try:
        normalized = validate_and_normalize(payload, SCHEMA_DATA)
        # Build row with fixed columns
        row_data = {
            "current_time": timestamp,
            "Pressure": f"{normalized['pressure']}",
            "Tempereture": f"{normalized['temperature']}",
        }
        enq_ok = enqueue_csv(CSV_PICODATA, COLUMNS_PICODATA, row_data)
        request_history.append({'endpoint': 'data', 'timestamp': timestamp, 'data': normalized})
        last_received['data'] = datetime.now()
        if not enq_ok:
            return jsonify({"status": "queued_failed"}), 503
        logger.info(f"/data OK enqueued pressure={normalized['pressure']} temperature={normalized['temperature']} queue_size={write_queue.qsize()}")
        return jsonify({"status": "enqueued"}), 200
    except ValidationError as ve:
        logger.error(f"/data validation error: {ve.details}")
        return jsonify({"error": ve.message, "details": ve.details}), 400
    except Exception:
        logger.exception("/data internal error")
        return jsonify({"error": "internal server error"}), 500


@app.route('/data2', methods=['POST'])
def handle_data2():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = request.get_json(silent=True) or {}
    try:
        normalized = validate_and_normalize(payload, SCHEMA_DATA2)
        row_data = {
            "current_time": timestamp,
            "CO2": f"{normalized['co2']}",
            "Tempereture": f"{normalized['temperature']}",
            "Humidity": f"{normalized['humidity']}",
            "Pressure": f"{normalized['pressure']}",
            "GasResistance": f"{normalized['gas_res']}",
        }
        enq_ok = enqueue_csv(CSV_BEDROOM, COLUMNS_BEDROOM, row_data)
        request_history.append({'endpoint': 'data2', 'timestamp': timestamp, 'data': normalized})
        last_received['data2'] = datetime.now()
        if not enq_ok:
            return jsonify({"status": "queued_failed"}), 503
        logger.info(f"/data2 OK enqueued co2={normalized['co2']} temp={normalized['temperature']} hum={normalized['humidity']} queue_size={write_queue.qsize()}")
        return jsonify({"status": "enqueued"}), 200
    except ValidationError as ve:
        logger.error(f"/data2 validation error: {ve.details}")
        return jsonify({"error": ve.message, "details": ve.details}), 400
    except Exception:
        logger.exception("/data2 internal error")
        return jsonify({"error": "internal server error"}), 500


@app.route('/data3', methods=['POST'])
def handle_data3():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = request.get_json(silent=True) or {}
    try:
        normalized = validate_and_normalize(payload, SCHEMA_DATA3)
        row_data = {
            "current_time": timestamp,
            "Temperature-outside": f"{normalized['temperature']}",
            "Humidity-outside": f"{normalized['humidity']}",
            "Pressure-outside": f"{normalized['pressure']}",
            "GasResistance-outside": f"{normalized['gas_res']}",
        }
        enq_ok = enqueue_csv(CSV_OUTSIDE, COLUMNS_OUTSIDE, row_data)
        request_history.append({'endpoint': 'data3', 'timestamp': timestamp, 'data': normalized})
        last_received['data3'] = datetime.now()
        if not enq_ok:
            return jsonify({"status": "queued_failed"}), 503
        logger.info(f"/data3 OK enqueued temp={normalized['temperature']} hum={normalized['humidity']} queue_size={write_queue.qsize()}")
        return jsonify({"status": "enqueued"}), 200
    except ValidationError as ve:
        logger.error(f"/data3 validation error: {ve.details}")
        return jsonify({"error": ve.message, "details": ve.details}), 400
    except Exception:
        logger.exception("/data3 internal error")
        return jsonify({"error": "internal server error"}), 500


@app.route('/data4', methods=['POST'])
def handle_data4():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = request.get_json(silent=True) or {}
    try:
        normalized = validate_and_normalize(payload, SCHEMA_DATA4)
        row_data = {
            "current_time": timestamp,
            "CO2": f"{normalized['mh_z19']['co2']}",
            "AnalogValue": f"{normalized['mq_2']['analog_value']}",
            "Voltage": f"{normalized['mq_2']['voltage']}",
            "Temperature_DS18B20": f"{normalized['ds18b20']['temperature']}",
            "Temperature_DHT11": f"{normalized['dht11']['temperature']}",
            "Humidity_DHT11": f"{normalized['dht11']['humidity']}"
        }
        enq_ok = enqueue_csv(CSV_LR, COLUMNS_LR, row_data)
        request_history.append({'endpoint': 'data4', 'timestamp': timestamp, 'data': normalized})
        last_received['data4'] = datetime.now()
        if not enq_ok:
            return jsonify({"status": "queued_failed"}), 503
        logger.info(f"/data4 OK enqueued co2={normalized['mh_z19']['co2']} analog={normalized['mq_2']['analog_value']} V={normalized['mq_2']['voltage']} queue_size={write_queue.qsize()}")
        return jsonify({"status": "enqueued"}), 200
    except ValidationError as ve:
        logger.error(f"/data4 validation error: {ve.details}")
        return jsonify({"error": ve.message, "details": ve.details}), 400
    except Exception:
        logger.exception("/data4 internal error")
        return jsonify({"error": "internal server error"}), 500


# Route to view request history
@app.route('/history')
def history():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Request History</title>
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
            }
            table, th, td {
                border: 1px solid black;
            }
            th, td {
                padding: 10px;
                text-align: left;
            }
        </style>
    </head>
    <body>
        <h1>Request History (max {{ maxlen }})</h1>
        <table>
            <tr>
                <th>Timestamp</th>
                <th>Endpoint</th>
                <th>Data</th>
            </tr>
            {% for entry in history %}
            <tr>
                <td>{{ entry.timestamp }}</td>
                <td>{{ entry.endpoint }}</td>
                <td>{{ entry.data }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """, history=list(request_history), maxlen=HISTORY_MAX)


# API to get request history as JSON
@app.route('/history/json')
def history_json():
    return jsonify(list(request_history))


@app.route('/metrics')
def metrics():
    """Expose runtime metrics for operators and monitoring."""
    with metrics_lock:
        ws = write_success_total
        we = write_error_total
    qlen = write_queue.qsize()
    now = datetime.now()
    # compute inactivity seconds per endpoint
    inactivity = {}
    for ep, ts in last_received.items():
        if ts is None:
            inactivity[ep] = None
        else:
            inactivity[ep] = int((now - ts).total_seconds())
    return jsonify({
        'queue_length': qlen,
        'queue_warn_threshold': QUEUE_WARN_THRESHOLD,
        'write_success_total': ws,
        'write_error_total': we,
        'last_received': {k: (v.strftime('%Y-%m-%d %H:%M:%S') if v else None) for k, v in last_received.items()},
        'inactivity_seconds': inactivity,
        'inactivity_warn_threshold_sec': INACTIVITY_WARN_SEC,
    })


if __name__ == "__main__":
    logger.info('Starting Flask10X application (threaded dev server)')
    # Use threaded=True to allow concurrent request handling in development.
    app.run(host="0.0.0.0", port=PORT, threaded=True)

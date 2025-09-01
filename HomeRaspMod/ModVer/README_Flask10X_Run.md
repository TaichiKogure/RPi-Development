# Flask10X Run Modes, Concurrency, and Operations (Steps 7–9)

This document explains how to run Flask10X in development and production, how to check runtime metrics, and how the app handles sender inactivity and backlog warnings.

## Development Run (threaded)

For local/dev usage, run the built-in Flask server with threaded request handling:

```bash
python3 BackUPFlask10X.py
```

The app now starts with `threaded=True`, so simultaneous requests to `/data`, `/data2`, `/data3`, `/data4` are handled concurrently and won’t block on slow storage because writes are queued to a background worker.

Health check:

```bash
curl -s http://localhost:8888/healthz
```

## Production Run (Gunicorn + systemd)

1) Install Gunicorn in your virtual environment:

```bash
source ~/envmonitor-venv/bin/activate
pip install gunicorn
```

2) Use the provided systemd unit template `flask10x.service` (in this directory). Copy it to your system:

```bash
sudo cp /home/pi/RPi_Development01/HomeRaspMod/ModVer/BackUPflask10x.service /etc/systemd/system/BackUPflask10x.service
sudo systemctl daemon-reload
sudo systemctl enable flask10x
sudo systemctl start flask10x
```

3) Control commands:

- Start: `sudo systemctl start flask10x`
- Stop: `sudo systemctl stop flask10x`
- Restart: `sudo systemctl restart flask10x`
- Status: `systemctl status flask10x`

The unit uses Gunicorn with 2 workers and 2 threads each by default and is configured to auto-restart on failure.

## Runtime Metrics and Observability

- Background CSV Writer Queue: all endpoints enqueue write jobs; a dedicated worker thread performs durable CSV appends (with header suppression, per-file lock, retries, fsync).
- Metrics endpoint: `/metrics`
  - `queue_length`: current number of pending write jobs
  - `queue_warn_threshold`: level that triggers WARN logs (80% of max by default)
  - `write_success_total` / `write_error_total`: counters maintained by the writer worker
  - `last_received`: most recent receive time per endpoint (`data`, `data2`, `data3`, `data4`)
  - `inactivity_seconds`: idle seconds per endpoint, or null if never received
  - `inactivity_warn_threshold_sec`: threshold after which a WARN is logged

Example:

```bash
curl -s http://localhost:8888/metrics | jq
```

### WARN Conditions
- Queue backlog WARN: emitted when `queue_length >= 0.8 * maxsize`.
- Inactivity WARN: emitted by a monitor thread when any endpoint has no data for more than `INACTIVITY_WARN_SEC` (default 120s).

## Troubleshooting

- Logs are in `HomeRaspMod/ModVer/logs/flask10x.log` with rotation (1MB, 5 backups). Startup and per-request events are logged. Queue backlog and inactivity will appear as WARN.
- Health: `/healthz` returns 200 OK if the process is alive.
- History: `/history` (HTML) and `/history/json` (JSON) provide the latest bounded request entries (cap 1000 by default).

## Load Testing Tips

- Generate concurrent POSTs:

```bash
for i in {1..100}; do \
  curl -s -X POST http://localhost:8888/data \
    -H 'Content-Type: application/json' \
    -d '{"pressure":"1013hPa","temperature":"25.1C"}' &
done; wait
```

- Observe that responses return quickly (enqueued immediately) and `queue_length` will rise and then drain as the background worker persists rows.

## File Integrity

- CSV headers are written only once per file (checked by size/existence).
- Per-file locks prevent corruption under concurrency.
- Short backoff retries on failures; errors increment `write_error_total` but the service continues running.

## Configuration Notes

- Port: `PORT` (default 8888) inside Flask10X.py
- Queue size: `WRITE_QUEUE_MAXSIZE` (default 5000)
- Backoff retries: `WRITE_RETRIES`, `WRITE_BACKOFF_BASE_SEC`
- WARN thresholds: `QUEUE_WARN_THRESHOLD`, `INACTIVITY_WARN_SEC`

Adjust these constants in `Flask10X.py` as needed for your environment.

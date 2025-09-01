import os
import sys
import json
import logging
from typing import Dict, List, Optional

from flask import Flask, jsonify, request, render_template_string
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# Ensure we can import Graph11X from the same folder
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

try:
    import Graph11X as G11
except Exception as e:
    raise RuntimeError(f"Failed to import Graph11X: {e}")

logger = logging.getLogger("Graph11X_Web")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    logger.addHandler(h)
logger.setLevel(logging.INFO)

app = Flask(__name__)

# Default UI template (no external files to keep minimal changes)
TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Graph11X Web Viewer</title>
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
  <style>
    body { font-family: Arial, sans-serif; margin: 16px; }
    .controls { display: flex; flex-wrap: wrap; gap: 12px; align-items: end; }
    .ctrl { display: flex; flex-direction: column; }
    #graph { width: 100%; height: 70vh; }
  </style>
</head>
<body>
  <h2>Graph11X Web Viewer (Interactive)</h2>
  <div class="controls">
    <div class="ctrl">
      <label for="parameter">Parameter</label>
      <select id="parameter"></select>
    </div>
    <div class="ctrl">
      <label>Datasets</label>
      <label><input type="checkbox" id="show_bed" checked> BedRoom</label>
      <label><input type="checkbox" id="show_out" checked> Outside</label>
      <label><input type="checkbox" id="show_pico" checked> Pico</label>
      <label><input type="checkbox" id="show_lr" checked> DiningRoom</label>
      <label><input type="checkbox" id="show_bme" checked> Desk</label>
    </div>
    <div class="ctrl">
      <label for="days">Days</label>
      <input id="days" type="number" min="0" step="1" value="1" />
    </div>
    <div class="ctrl">
      <label for="max_points">Max points</label>
      <input id="max_points" type="number" min="100" step="100" value="2000" />
    </div>
    <div class="ctrl">
      <label for="agg">Aggregation</label>
      <select id="agg">
        <option value="mean" selected>mean</option>
        <option value="median">median</option>
        <option value="min">min</option>
        <option value="max">max</option>
      </select>
    </div>
    <div class="ctrl">
      <label for="ymin">Y min (optional)</label>
      <input id="ymin" type="number" step="any" />
    </div>
    <div class="ctrl">
      <label for="ymax">Y max (optional)</label>
      <input id="ymax" type="number" step="any" />
    </div>
    <div class="ctrl">
      <button id="btn_update">Update</button>
    </div>
  </div>

  <div id="graph"></div>

  <script>
    async function loadParameters() {
      const resp = await fetch('/api/parameters');
      const data = await resp.json();
      const sel = document.getElementById('parameter');
      sel.innerHTML = '';
      data.parameters.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p; opt.textContent = p;
        sel.appendChild(opt);
      });
      if (data.parameters.includes('temperature')) sel.value = 'temperature';
    }

    async function updateGraph() {
      const param = document.getElementById('parameter').value;
      const days = document.getElementById('days').value;
      const max_points = document.getElementById('max_points').value;
      const agg = document.getElementById('agg').value;
      const show_bed = document.getElementById('show_bed').checked;
      const show_out = document.getElementById('show_out').checked;
      const show_pico = document.getElementById('show_pico').checked;
      const show_lr = document.getElementById('show_lr').checked;
      const show_bme = document.getElementById('show_bme').checked;
      const ymin = document.getElementById('ymin').value;
      const ymax = document.getElementById('ymax').value;

      const url = new URL('/api/graph', window.location.origin);
      url.searchParams.set('parameter', param);
      url.searchParams.set('days', days);
      url.searchParams.set('max_points', max_points);
      url.searchParams.set('agg', agg);
      url.searchParams.set('show_bed', show_bed);
      url.searchParams.set('show_out', show_out);
      url.searchParams.set('show_pico', show_pico);
      url.searchParams.set('show_lr', show_lr);
      url.searchParams.set('show_bme', show_bme);
      if (ymin) url.searchParams.set('ymin', ymin);
      if (ymax) url.searchParams.set('ymax', ymax);

      const resp = await fetch(url);
      const fig = await resp.json();
      Plotly.newPlot('graph', fig.data, fig.layout, {responsive: true});
    }

    document.getElementById('btn_update').addEventListener('click', updateGraph);

    (async () => {
      await loadParameters();
      await updateGraph();
    })();
  </script>
</body>
</html>
"""


def _jsonify_numpy(obj):
    """Recursively convert numpy arrays to lists for JSON serialization."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _jsonify_numpy(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_jsonify_numpy(v) for v in obj]
    return obj


def _load_all_datasets() -> List[pd.DataFrame]:
    """Load all CSV datasets using Graph11X robust reader and required columns."""
    datasets = []
    for file, date_col in G11.DATA_FILES:
        usecols = G11.REQUIRED_COLS.get(file)
        df = G11._read_csv_incremental(file, date_col, usecols=usecols)
        datasets.append(df)
    return datasets


def _filter_days(df: pd.DataFrame, days: int) -> pd.DataFrame:
    if df is None or df.empty or days <= 0:
        return df
    cutoff = pd.Timestamp.utcnow() - pd.Timedelta(days=days)
    # Handle naive timezone by comparing on UTC floor if needed
    try:
        return df[df.index >= cutoff.tz_localize(None)]
    except Exception:
        return df[df.index >= cutoff]


def _downsample(df: pd.DataFrame, max_points: int, agg: str, ref_index: Optional[pd.DatetimeIndex] = None) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    ds, _ = G11.resample_downsample(df, max_points=max_points, agg=agg, reference_index=ref_index)
    return ds


@app.route('/')
def index():
    return render_template_string(TEMPLATE)


@app.route('/api/parameters')
def api_parameters():
    try:
        dfs = _load_all_datasets()
        # Ensure absolute humidity is available where possible
        labels = ['BedRoom', 'Outside', 'Pico', 'DiningRoom', 'Desk']
        for df, lbl in zip(dfs, labels):
            G11.ensure_absolute_humidity(df, lbl)
        # Aggregate available numeric columns across datasets
        params = set()
        for df in dfs:
            for col in df.columns:
                if col in G11.NUMERIC_COLS:
                    params.add(col)
        # Common primary params first
        preferred = ['temperature', 'humidity', 'absolute_humidity', 'co2', 'pressure', 'gas_resistance']
        ordered = [p for p in preferred if p in params] + sorted([p for p in params if p not in preferred])
        return jsonify({"parameters": ordered})
    except Exception as e:
        logger.error(f"Failed to list parameters: {e}")
        return jsonify({"parameters": []})


@app.route('/api/graph')
def api_graph():
    try:
        parameter = request.args.get('parameter', 'temperature')
        days = int(request.args.get('days', 1))
        max_points = max(100, int(request.args.get('max_points', G11.MAX_POINTS)))
        agg = request.args.get('agg', G11.AGG_METHOD)
        show_bed = request.args.get('show_bed', 'true').lower() == 'true'
        show_out = request.args.get('show_out', 'true').lower() == 'true'
        show_pico = request.args.get('show_pico', 'true').lower() == 'true'
        show_lr = request.args.get('show_lr', 'true').lower() == 'true'
        show_bme = request.args.get('show_bme', 'true').lower() == 'true'
        y_min = request.args.get('ymin')
        y_max = request.args.get('ymax')

        dfs = _load_all_datasets()
        bed, out, pico, lr, bme = dfs
        for df, lbl in zip(dfs, ['BedRoom', 'Outside', 'Pico', 'DiningRoom', 'Desk']):
            G11.ensure_absolute_humidity(df, lbl)

        # Filter by days
        bed = _filter_days(bed, days)
        out = _filter_days(out, days)
        pico = _filter_days(pico, days)
        lr = _filter_days(lr, days)
        bme = _filter_days(bme, days)

        # Downsample with alignment on BedRoom index if possible
        bed_ds = _downsample(bed, max_points, agg)
        ref_index = bed_ds.index if bed_ds is not None and len(bed_ds) else None
        out_ds = _downsample(out, max_points, agg, ref_index)
        pico_ds = _downsample(pico, max_points, agg, ref_index)
        lr_ds = _downsample(lr, max_points, agg, ref_index)
        bme_ds = _downsample(bme, max_points, agg, ref_index)

        fig = go.Figure()
        # Helper to add a trace if available
        def add_trace(df: pd.DataFrame, name: str, color: str):
            if df is None or df.empty:
                return
            if parameter not in df.columns:
                return
            x = df.index
            y = df[parameter]
            # Ensure clean series
            y = pd.to_numeric(y, errors='coerce')
            mask = y.notna()
            fig.add_trace(go.Scatter(x=x[mask], y=y[mask], mode='lines', name=name, line=dict(color=color)))

        if show_bed:
            add_trace(bed_ds, 'BedRoom', '#1f77b4')
        if show_out:
            add_trace(out_ds, 'Outside', '#d62728')
        if show_pico:
            add_trace(pico_ds, 'Pico', '#2ca02c')
        if show_lr:
            add_trace(lr_ds, 'DiningRoom', '#7f7f7f')
        if show_bme:
            add_trace(bme_ds, 'Desk', '#17becf')

        title = f"{parameter.replace('_',' ').title()} (days={days}, max_points={max_points}, agg={agg})"
        layout = dict(
            title=title,
            xaxis=dict(title='Time', type='date'),
            yaxis=dict(title=parameter.replace('_',' ').title()),
            legend=dict(orientation='h', y=1.05),
            margin=dict(l=30, r=20, t=50, b=30),
        )
        # Apply y-axis range if provided
        if y_min is not None and y_max is not None and y_min != '' and y_max != '':
            try:
                layout['yaxis']['range'] = [float(y_min), float(y_max)]
                layout['yaxis']['autorange'] = False
            except Exception:
                pass

        data = fig.to_dict()
        data = _jsonify_numpy(data)
        data['layout'] = {**data.get('layout', {}), **layout}
        return jsonify(data)
    except Exception as e:
        logger.error(f"Failed to build graph: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Simple dev server
    port = int(os.environ.get('GRAPH11X_WEB_PORT', '8088'))
    app.run(host='0.0.0.0', port=port, debug=False)

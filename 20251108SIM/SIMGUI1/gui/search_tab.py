import os
import threading
from typing import List, Dict, Optional, Tuple

import pandas as pd
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt

from core.config import SolverParams
from core.param_search import ParamRange, SearchPlan, GridSearchRunner


class SearchWorker(QtCore.QThread):
    row_appended = QtCore.Signal(dict)
    progress_changed = QtCore.Signal(int, int)
    finished_with_df = QtCore.Signal(object)

    def __init__(self, plan: SearchPlan, base_params: SolverParams):
        super().__init__()
        self.plan = plan
        self.base_params = base_params
        self._stop_flag = threading.Event()
        self._df: Optional[pd.DataFrame] = None

    def stop(self):
        self._stop_flag.set()

    def run(self):
        runner = GridSearchRunner(self.plan)

        def on_row(row: Dict):
            self.row_appended.emit(row)

        def on_prog(done: int, total: int):
            self.progress_changed.emit(done, total)

        df = runner.run(self.base_params, on_result=on_row, on_progress=on_prog, stop_flag=self._stop_flag)
        self._df = df
        self.finished_with_df.emit(df)


class SearchTab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: Optional[SearchWorker] = None
        self._rows: List[Dict] = []

        layout = QtWidgets.QVBoxLayout(self)

        # ---- Parameter Ranges ----
        ranges_group = QtWidgets.QGroupBox("Parameter Ranges")
        gl = QtWidgets.QGridLayout(ranges_group)
        layout.addWidget(ranges_group)

        def range_row(row: int, label: str) -> Tuple[QtWidgets.QCheckBox, QtWidgets.QDoubleSpinBox, QtWidgets.QDoubleSpinBox, QtWidgets.QSpinBox, QtWidgets.QComboBox]:
            cb = QtWidgets.QCheckBox(label); cb.setChecked(True)
            sb_min = QtWidgets.QDoubleSpinBox(); sb_min.setDecimals(6); sb_min.setRange(1e-9, 1e9)
            sb_max = QtWidgets.QDoubleSpinBox(); sb_max.setDecimals(6); sb_max.setRange(1e-9, 1e9)
            sb_steps = QtWidgets.QSpinBox(); sb_steps.setRange(2, 200); sb_steps.setValue(3)
            cmb_scale = QtWidgets.QComboBox(); cmb_scale.addItems(["linear", "log"])
            gl.addWidget(cb, row, 0)
            gl.addWidget(QtWidgets.QLabel("min"), row, 1)
            gl.addWidget(sb_min, row, 2)
            gl.addWidget(QtWidgets.QLabel("max"), row, 3)
            gl.addWidget(sb_max, row, 4)
            gl.addWidget(QtWidgets.QLabel("steps"), row, 5)
            gl.addWidget(sb_steps, row, 6)
            gl.addWidget(QtWidgets.QLabel("scale"), row, 7)
            gl.addWidget(cmb_scale, row, 8)
            return cb, sb_min, sb_max, sb_steps, cmb_scale

        self.cb_tol_factor, self.min_tol_factor, self.max_tol_factor, self.steps_tol_factor, self.scale_tol_factor = range_row(0, "tol_factor")
        self.min_tol_factor.setValue(0.25); self.max_tol_factor.setValue(1.0); self.steps_tol_factor.setValue(4)

        self.cb_safety_growth, self.min_safety_growth, self.max_safety_growth, self.steps_safety_growth, self.scale_safety_growth = range_row(1, "safety_growth")
        self.min_safety_growth.setValue(1.05); self.max_safety_growth.setValue(1.20); self.steps_safety_growth.setValue(4)

        self.cb_D, self.min_D, self.max_D, self.steps_D, self.scale_D = range_row(2, "D")
        self.min_D.setValue(0.032); self.max_D.setValue(0.048); self.steps_D.setValue(3)

        self.cb_nx, self.min_nx, self.max_nx, self.steps_nx, self.scale_nx = range_row(3, "nx")
        self.min_nx.setValue(120); self.max_nx.setValue(240); self.steps_nx.setValue(3); self.scale_nx.setCurrentText("linear")

        self.cb_ny, self.min_ny, self.max_ny, self.steps_ny, self.scale_ny = range_row(4, "ny")
        self.min_ny.setValue(30); self.max_ny.setValue(60); self.steps_ny.setValue(3); self.scale_ny.setCurrentText("linear")

        # ---- Settings ----
        settings = QtWidgets.QGroupBox("Search Settings")
        fl = QtWidgets.QFormLayout(settings)
        layout.addWidget(settings)

        self.cmb_mode = QtWidgets.QComboBox(); self.cmb_mode.addItems(["region", "quick"]) ; self.cmb_mode.setCurrentText("region")
        self.sb_max_points = QtWidgets.QSpinBox(); self.sb_max_points.setRange(1, 200000); self.sb_max_points.setValue(10000)
        self.sb_n_procs = QtWidgets.QSpinBox(); self.sb_n_procs.setRange(1, 64); self.sb_n_procs.setValue(10)
        self.sb_time_budget = QtWidgets.QSpinBox(); self.sb_time_budget.setRange(1, 1440); self.sb_time_budget.setValue(60)
        self.sb_timeout_dry = QtWidgets.QSpinBox(); self.sb_timeout_dry.setRange(5, 3600); self.sb_timeout_dry.setValue(60)
        self.sb_timeout_quick = QtWidgets.QSpinBox(); self.sb_timeout_quick.setRange(5, 7200); self.sb_timeout_quick.setValue(180)
        self.sb_quick_load = QtWidgets.QSpinBox(); self.sb_quick_load.setRange(1, 200); self.sb_quick_load.setValue(5)
        self.sb_quick_unload = QtWidgets.QSpinBox(); self.sb_quick_unload.setRange(0, 200); self.sb_quick_unload.setValue(5)
        self.sb_topk_quick = QtWidgets.QSpinBox(); self.sb_topk_quick.setRange(1, 1000); self.sb_topk_quick.setValue(10)

        fl.addRow("mode", self.cmb_mode)
        fl.addRow("max_points", self.sb_max_points)
        fl.addRow("n_procs", self.sb_n_procs)
        fl.addRow("time budget [min]", self.sb_time_budget)
        fl.addRow("timeout dry [s]", self.sb_timeout_dry)
        fl.addRow("timeout quick [s]", self.sb_timeout_quick)
        fl.addRow("quick steps (load)", self.sb_quick_load)
        fl.addRow("quick steps (unload)", self.sb_quick_unload)
        fl.addRow("topK quick", self.sb_topk_quick)

        # ---- Controls ----
        ctrl = QtWidgets.QHBoxLayout()
        self.btn_start = QtWidgets.QPushButton("Start Search")
        self.btn_stop = QtWidgets.QPushButton("Stop")
        self.btn_export = QtWidgets.QPushButton("Export CSV")
        self.btn_apply = QtWidgets.QPushButton("Apply to Run panel")
        ctrl.addWidget(self.btn_start)
        ctrl.addWidget(self.btn_stop)
        ctrl.addWidget(self.btn_export)
        ctrl.addWidget(self.btn_apply)
        layout.addLayout(ctrl)

        # ---- Progress ----
        pr = QtWidgets.QHBoxLayout()
        self.prog = QtWidgets.QProgressBar(); self.prog.setRange(0, 100)
        self.lbl_prog = QtWidgets.QLabel("0/0")
        pr.addWidget(self.prog, 1)
        pr.addWidget(self.lbl_prog)
        layout.addLayout(pr)

        # ---- Results table ----
        self.table = QtWidgets.QTableWidget(0, 12)
        headers = [
            "idx", "success_region", "nodes", "facets", "tol", "D_eff", "y_top",
            "tol_factor", "safety_growth", "D", "nx", "ny"
        ]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

        # Connections
        self.btn_start.clicked.connect(self.on_start)
        self.btn_stop.clicked.connect(self.on_stop)
        self.btn_export.clicked.connect(self.on_export)
        # self.btn_apply will be connected by MainWindow to copy values

    # Public helper: extract selected row values
    def selected_params(self) -> Dict[str, float]:
        r = self.table.currentRow()
        if r < 0:
            return {}
        def get(col_name: str) -> Optional[float]:
            try:
                col = self._col_index(col_name)
                item = self.table.item(r, col)
                return float(item.text()) if item else None
            except Exception:
                return None
        return {
            'tol_factor': get('tol_factor'),
            'safety_growth': get('safety_growth'),
            'D': get('D'),
            'nx': get('nx'),
            'ny': get('ny'),
        }

    def _col_index(self, name: str) -> int:
        for c in range(self.table.columnCount()):
            if self.table.horizontalHeaderItem(c).text() == name:
                return c
        return -1

    def _collect_plan(self, base_params: SolverParams) -> SearchPlan:
        ranges: List[ParamRange] = []
        def add_range(enabled: bool, name: str, vmin: float, vmax: float, steps: int, scale: str):
            ranges.append(ParamRange(name=name, vmin=vmin, vmax=vmax, steps=steps, scale=scale, enabled=enabled))

        add_range(self.cb_tol_factor.isChecked(), 'tol_factor', float(self.min_tol_factor.value()), float(self.max_tol_factor.value()), int(self.steps_tol_factor.value()), self.scale_tol_factor.currentText())
        add_range(self.cb_safety_growth.isChecked(), 'safety_growth', float(self.min_safety_growth.value()), float(self.max_safety_growth.value()), int(self.steps_safety_growth.value()), self.scale_safety_growth.currentText())
        add_range(self.cb_D.isChecked(), 'D', float(self.min_D.value()), float(self.max_D.value()), int(self.steps_D.value()), self.scale_D.currentText())
        add_range(self.cb_nx.isChecked(), 'nx', float(self.min_nx.value()), float(self.max_nx.value()), int(self.steps_nx.value()), self.scale_nx.currentText())
        add_range(self.cb_ny.isChecked(), 'ny', float(self.min_ny.value()), float(self.max_ny.value()), int(self.steps_ny.value()), self.scale_ny.currentText())

        plan = SearchPlan(
            ranges=ranges,
            mode=self.cmb_mode.currentText(),
            max_points=int(self.sb_max_points.value()),
            n_procs=int(self.sb_n_procs.value()),
            timeout_dry=int(self.sb_timeout_dry.value()),
            timeout_quick=int(self.sb_timeout_quick.value()),
            time_budget_min=int(self.sb_time_budget.value()),
            quick_steps=(int(self.sb_quick_load.value()), int(self.sb_quick_unload.value())),
            topk_quick=int(self.sb_topk_quick.value()),
        )
        return plan

    def on_start(self):
        if self._worker and self._worker.isRunning():
            return
        # Base params should be provided by MainWindow when wiring up; here we fallback to defaults
        base_params = getattr(self.parent(), 'params_from_ui', None)
        if callable(base_params):
            base_params = base_params()
        else:
            base_params = SolverParams()
        plan = self._collect_plan(base_params)

        self.table.setRowCount(0)
        self._rows.clear()
        self.prog.setValue(0)
        self.lbl_prog.setText("0/0")

        self._worker = SearchWorker(plan, base_params)
        self._worker.row_appended.connect(self._on_row)
        self._worker.progress_changed.connect(self._on_progress)
        self._worker.finished_with_df.connect(self._on_finished)
        self._worker.start()

    def on_stop(self):
        if self._worker and self._worker.isRunning():
            self._worker.stop()

    def _on_row(self, row: Dict):
        self._rows.append(row)
        # append to table
        headers = [self.table.horizontalHeaderItem(c).text() for c in range(self.table.columnCount())]
        self.table.insertRow(self.table.rowCount())
        r = self.table.rowCount() - 1
        for c, h in enumerate(headers):
            val = row.get(h)
            item = QtWidgets.QTableWidgetItem("" if val is None else str(val))
            if h in ("success_region",):
                item.setText("True" if bool(val) else "False")
            self.table.setItem(r, c, item)

    def _on_progress(self, done: int, total: int):
        self.lbl_prog.setText(f"{done}/{total}")
        self.prog.setMaximum(max(1, total))
        self.prog.setValue(done)

    def _on_finished(self, df: pd.DataFrame):
        # nothing extra now; could enable buttons
        pass

    def on_export(self):
        if not self._rows:
            QtWidgets.QMessageBox.information(self, "Export", "No results to export")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export CSV", os.path.expanduser("~"), "CSV Files (*.csv)")
        if not path:
            return
        try:
            pd.DataFrame(self._rows).to_csv(path, index=False)
            QtWidgets.QMessageBox.information(self, "Export", f"Saved: {path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Export", f"Failed to save: {e}")

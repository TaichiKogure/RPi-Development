import os
import sys
from typing import Optional

# Ensure SIMGUI1 root is on sys.path so that `core` and `gui` can be imported when running this file directly
THIS_DIR = os.path.dirname(__file__)
SIMGUI_ROOT = os.path.abspath(os.path.join(THIS_DIR, os.pardir))
if SIMGUI_ROOT not in sys.path:
    sys.path.insert(0, SIMGUI_ROOT)

from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QPlainTextEdit, QFileDialog, QLabel, QSpinBox,
    QDoubleSpinBox, QGroupBox, QSplitter
)

from core.config import SolverParams, make_diag_dir
from core.solver_interface import run_dry_run, ProcessResult
from gui.plots import new_canvas, plot_attempts, plot_topband_scatter


class DryRunWorker(QtCore.QThread):
    finished = QtCore.Signal(ProcessResult)

    def __init__(self, params: SolverParams, diag_dir: Optional[str] = None, timeout: int = 300):
        super().__init__()
        self.params = params
        self.diag_dir = diag_dir
        self.timeout = timeout

    def run(self):
        result = run_dry_run(self.params, diag_dir=self.diag_dir, timeout=self.timeout)
        self.finished.emit(result)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SIMGUI1 - Elastic Press (Robust) GUI")
        self.resize(1200, 700)

        # Root layout with splitter
        splitter = QSplitter(Qt.Horizontal)
        left = QWidget(); left_layout = QVBoxLayout(left)
        right = QWidget(); right_layout = QVBoxLayout(right)
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

        # --- Left panel: Parameters and actions ---
        param_group = QGroupBox("Parameters")
        form = QFormLayout(param_group)

        # Key parameters (keep it compact; advanced later)
        self.sb_E = QDoubleSpinBox(); self.sb_E.setDecimals(0); self.sb_E.setRange(1e6, 1e13); self.sb_E.setValue(1.0e10)
        self.sb_nu = QDoubleSpinBox(); self.sb_nu.setDecimals(3); self.sb_nu.setSingleStep(0.05); self.sb_nu.setRange(0.0, 0.49); self.sb_nu.setValue(0.2)
        self.sb_W = QDoubleSpinBox(); self.sb_W.setDecimals(4); self.sb_W.setRange(0.01, 10.0); self.sb_W.setValue(1.0)
        self.sb_H = QDoubleSpinBox(); self.sb_H.setDecimals(4); self.sb_H.setRange(0.01, 10.0); self.sb_H.setValue(1.0)
        self.sb_D = QDoubleSpinBox(); self.sb_D.setDecimals(5); self.sb_D.setRange(1e-4, 1.0); self.sb_D.setValue(0.040)

        self.sb_u_max = QDoubleSpinBox(); self.sb_u_max.setDecimals(8); self.sb_u_max.setRange(1e-8, 1e-2); self.sb_u_max.setValue(1.0e-4)
        self.sb_n_load = QSpinBox(); self.sb_n_load.setRange(1, 200); self.sb_n_load.setValue(20)
        self.sb_n_unload = QSpinBox(); self.sb_n_unload.setRange(0, 200); self.sb_n_unload.setValue(20)

        self.sb_nx = QSpinBox(); self.sb_nx.setRange(10, 1000); self.sb_nx.setValue(300)
        self.sb_ny = QSpinBox(); self.sb_ny.setRange(5, 500); self.sb_ny.setValue(60)

        self.sb_tol_abs = QDoubleSpinBox(); self.sb_tol_abs.setDecimals(16); self.sb_tol_abs.setRange(0.0, 1e-3); self.sb_tol_abs.setValue(1e-12)
        self.sb_tol_factor = QDoubleSpinBox(); self.sb_tol_factor.setDecimals(3); self.sb_tol_factor.setRange(0.0, 5.0); self.sb_tol_factor.setValue(0.5)
        self.sb_safety_growth = QDoubleSpinBox(); self.sb_safety_growth.setDecimals(3); self.sb_safety_growth.setRange(1.0, 2.0); self.sb_safety_growth.setValue(1.10)
        self.sb_max_attempts = QSpinBox(); self.sb_max_attempts.setRange(1, 500); self.sb_max_attempts.setValue(100)

        form.addRow("E [Pa]", self.sb_E)
        form.addRow("nu [-]", self.sb_nu)
        form.addRow("W [m]", self.sb_W)
        form.addRow("H [m]", self.sb_H)
        form.addRow("D [m]", self.sb_D)
        form.addRow("u_max [m]", self.sb_u_max)
        form.addRow("n_steps_load", self.sb_n_load)
        form.addRow("n_steps_unload", self.sb_n_unload)
        form.addRow("nx", self.sb_nx)
        form.addRow("ny", self.sb_ny)
        form.addRow("tol_abs", self.sb_tol_abs)
        form.addRow("tol_factor", self.sb_tol_factor)
        form.addRow("safety_growth", self.sb_safety_growth)
        form.addRow("max_attempts", self.sb_max_attempts)

        left_layout.addWidget(param_group)

        # Action buttons
        btn_box = QHBoxLayout()
        self.btn_dry = QPushButton("Dry‑run")
        self.btn_pick_diag = QPushButton("Diag Folder…")
        self.btn_open_diag = QPushButton("Open Last Diag")
        btn_box.addWidget(self.btn_dry)
        btn_box.addWidget(self.btn_pick_diag)
        btn_box.addWidget(self.btn_open_diag)
        left_layout.addLayout(btn_box)

        # Log output
        self.log_edit = QPlainTextEdit(); self.log_edit.setReadOnly(True)
        left_layout.addWidget(QLabel("Log"))
        left_layout.addWidget(self.log_edit, 1)

        # --- Right panel: Plots ---
        plots_row = QHBoxLayout()
        self.canvas_attempts = new_canvas()
        self.canvas_preview = new_canvas()
        right_layout.addWidget(QLabel("Diagnostics"))
        plots_row.addWidget(self.canvas_attempts, 1)
        plots_row.addWidget(self.canvas_preview, 1)
        right_layout.addLayout(plots_row, 1)

        # State
        self._last_diag_dir: Optional[str] = None
        self._worker: Optional[DryRunWorker] = None

        # Signals
        self.btn_dry.clicked.connect(self.on_dry_run)
        self.btn_pick_diag.clicked.connect(self.on_pick_diag_dir)
        self.btn_open_diag.clicked.connect(self.on_open_last_diag)

    def params_from_ui(self) -> SolverParams:
        p = SolverParams(
            E=float(self.sb_E.value()),
            nu=float(self.sb_nu.value()),
            W=float(self.sb_W.value()),
            H=float(self.sb_H.value()),
            D=float(self.sb_D.value()),
            u_max=float(self.sb_u_max.value()),
            n_steps_load=int(self.sb_n_load.value()),
            n_steps_unload=int(self.sb_n_unload.value()),
            nx=int(self.sb_nx.value()),
            ny=int(self.sb_ny.value()),
            tol_abs=float(self.sb_tol_abs.value()),
            tol_factor=float(self.sb_tol_factor.value()),
            safety_growth=float(self.sb_safety_growth.value()),
            max_attempts=int(self.sb_max_attempts.value()),
            log_level='INFO',
        )
        return p

    def append_log(self, text: str):
        self.log_edit.appendPlainText(text)

    def on_pick_diag_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Select diagnostics folder")
        if d:
            self._last_diag_dir = d
            self.append_log(f"Selected diag dir: {d}")

    def on_open_last_diag(self):
        if not self._last_diag_dir or not os.path.isdir(self._last_diag_dir):
            self.append_log("No diagnostics folder yet.")
            return
        try:
            os.startfile(self._last_diag_dir)
        except Exception as e:
            self.append_log(f"Failed to open folder: {e}")

    def on_dry_run(self):
        if self._worker is not None and self._worker.isRunning():
            self.append_log("A task is already running.")
            return

        params = self.params_from_ui()
        diag_dir = self._last_diag_dir or make_diag_dir("diag")
        self._last_diag_dir = diag_dir
        self.append_log(f"[Dry‑run] diag_dir={diag_dir}")

        # Disable UI during run
        self.btn_dry.setEnabled(False)
        self._worker = DryRunWorker(params, diag_dir=diag_dir, timeout=300)
        self._worker.finished.connect(self.on_dry_finished)
        self._worker.start()

    @QtCore.Slot(ProcessResult)
    def on_dry_finished(self, result: ProcessResult):
        self.btn_dry.setEnabled(True)
        # Log
        if result.log:
            self.append_log(result.log)
        if result.error:
            self.append_log(f"ERROR: {result.error}")
        self.append_log(f"Exit: {'success' if result.success else 'failed'}; diag_dir={result.diag_dir}")

        # Plots
        plot_attempts(self.canvas_attempts, result.attempts_df)
        plot_topband_scatter(self.canvas_preview, result.preview_df)


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

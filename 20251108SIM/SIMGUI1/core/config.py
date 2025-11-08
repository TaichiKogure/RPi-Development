import os
from dataclasses import dataclass, asdict
from datetime import datetime

# Absolute path to the backend solver script
CALC2_ROBUST_PATH = r"G:\\RPi-Development\\20251108SIM\\Calc2_robust.py"

# Base directories for GUI artifacts
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)


def make_diag_dir(prefix: str = "diag") -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(OUTPUT_DIR, f"{prefix}_{ts}")
    os.makedirs(path, exist_ok=True)
    return path


@dataclass
class SolverParams:
    # Material
    E: float = 10e9
    nu: float = 0.2
    # Geometry
    W: float = 1.0
    H: float = 1.0
    D: float = 0.040
    # Loading
    u_max: float = 1.0e-4
    n_steps_load: int = 20
    n_steps_unload: int = 20
    # Mesh
    nx: int = 300
    ny: int = 60
    # Robust region options
    tol_abs: float = 1e-12
    tol_factor: float = 0.5
    safety_growth: float = 1.10
    max_attempts: int = 100
    # Logging
    log_level: str = "INFO"

    def to_cli_args(self) -> list:
        return [
            "--E", str(self.E),
            "--nu", str(self.nu),
            "--W", str(self.W),
            "--H", str(self.H),
            "--D", str(self.D),
            "--u-max", str(self.u_max),
            "--n-steps-load", str(self.n_steps_load),
            "--n-steps-unload", str(self.n_steps_unload),
            "--nx", str(self.nx),
            "--ny", str(self.ny),
            "--tol-abs", str(self.tol_abs),
            "--tol-factor", str(self.tol_factor),
            "--safety-growth", str(self.safety_growth),
            "--max-attempts", str(self.max_attempts),
            "--log-level", self.log_level,
        ]

    def as_dict(self):
        return asdict(self)

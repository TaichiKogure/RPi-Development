import os
import pandas as pd
from typing import Optional, Tuple


def load_attempts(diag_dir: str) -> Optional[pd.DataFrame]:
    """Load region_attempts.csv as DataFrame if exists."""
    path = os.path.join(diag_dir, 'region_attempts.csv')
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path)
        # Expected columns: attempt, tol, D_eff, y_top, facets, nodes (robust-3)
        return df
    except Exception:
        return None


def load_preview(diag_dir: str) -> Optional[pd.DataFrame]:
    """Load topband_verts_preview.csv if exists (x,y columns)."""
    path = os.path.join(diag_dir, 'topband_verts_preview.csv')
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path)
        return df
    except Exception:
        return None


def safe_read_csv(path: str) -> Tuple[Optional[pd.DataFrame], Optional[Exception]]:
    if not os.path.exists(path):
        return None, FileNotFoundError(path)
    try:
        return pd.read_csv(path), None
    except Exception as e:
        return None, e

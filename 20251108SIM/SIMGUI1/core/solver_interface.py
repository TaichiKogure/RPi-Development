import os
import sys
import subprocess
import threading
import queue
from typing import Optional, Tuple, Dict, Any

from .config import CALC2_ROBUST_PATH, SolverParams, make_diag_dir
from .diagnostics_parser import load_attempts, load_preview
import pandas as pd


class ProcessResult:
    def __init__(self, success: bool, diag_dir: Optional[str], log: str, error: Optional[str],
                 attempts_df=None, preview_df=None):
        self.success = success
        self.diag_dir = diag_dir
        self.log = log
        self.error = error
        self.attempts_df = attempts_df
        self.preview_df = preview_df


def _reader_thread(stream, out_queue: queue.Queue, tag: str):
    try:
        for line in iter(stream.readline, b""):
            try:
                out_queue.put((tag, line.decode(errors='replace')))
            except Exception:
                out_queue.put((tag, str(line)))
    finally:
        try:
            stream.close()
        except Exception:
            pass


def _build_base_cmd() -> list:
    py = sys.executable or 'python'
    return [py, CALC2_ROBUST_PATH]


def run_dry_run(params: SolverParams, diag_dir: Optional[str] = None, timeout: int = 300) -> ProcessResult:
    """
    Execute Calc2_robust.py in --dry-run mode as a subprocess, capture stdout/stderr and
    parse diagnostics (region_attempts.csv, topband_verts_preview.csv).
    """
    if not os.path.isfile(CALC2_ROBUST_PATH):
        return ProcessResult(False, None, '', f"Solver not found: {CALC2_ROBUST_PATH}")

    diag_dir = diag_dir or make_diag_dir("diag")

    cmd = _build_base_cmd() + params.to_cli_args() + [
        '--dry-run',
        '--diag-dir', diag_dir,
        '--log-level', params.log_level or 'INFO'
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.path.dirname(CALC2_ROBUST_PATH) or None
    )

    q = queue.Queue()
    threads = [
        threading.Thread(target=_reader_thread, args=(proc.stdout, q, 'OUT'), daemon=True),
        threading.Thread(target=_reader_thread, args=(proc.stderr, q, 'ERR'), daemon=True),
    ]
    for t in threads:
        t.start()

    captured_lines = []
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        return ProcessResult(False, diag_dir, '\n'.join(captured_lines), 'Timeout')

    # Drain any remaining lines
    while not q.empty():
        tag, line = q.get()
        captured_lines.append(f"[{tag}] {line.rstrip()}")

    success = proc.returncode == 0
    attempts_df = load_attempts(diag_dir)
    preview_df = load_preview(diag_dir)

    err_msg = None if success else f"Process exited with code {proc.returncode}"
    return ProcessResult(success, diag_dir, '\n'.join(captured_lines), err_msg, attempts_df, preview_df)

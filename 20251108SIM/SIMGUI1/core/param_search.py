import os
import math
import time
import threading
import itertools
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

import pandas as pd

from .config import SolverParams, make_diag_dir
from .solver_interface import run_dry_run, run_quick_solve, ProcessResult
from .diagnostics_parser import load_attempts


@dataclass
class ParamRange:
    name: str
    vmin: float
    vmax: float
    steps: int
    scale: str = "linear"  # or "log"
    enabled: bool = True

    def values(self) -> List[float]:
        if not self.enabled:
            return []
        steps = max(2, int(self.steps))
        if self.scale == "log":
            # guard: vmin, vmax must be > 0
            lo = max(self.vmin, 1e-16)
            hi = max(self.vmax, lo * 1.0001)
            if lo <= 0 or hi <= 0:
                self.scale = "linear"
            else:
                logs = [math.log(lo) + i * (math.log(hi) - math.log(lo)) / (steps - 1) for i in range(steps)]
                return [math.exp(x) for x in logs]
        # linear fallback
        return [self.vmin + i * (self.vmax - self.vmin) / (steps - 1) for i in range(steps)]


@dataclass
class SearchPlan:
    ranges: List[ParamRange]
    mode: str = "region"  # "region" or "quick"
    max_points: int = 10000
    n_procs: int = 10
    timeout_dry: int = 60
    timeout_quick: int = 180
    time_budget_min: int = 60
    quick_steps: Tuple[int, int] = (5, 5)
    topk_quick: int = 10


def _product(lens: List[int]) -> int:
    p = 1
    for n in lens:
        p *= max(1, n)
    return p


def _shrink_steps(steps: List[int], max_points: int) -> List[int]:
    """Reduce per-dimension steps uniformly until total combinations <= max_points.
    Keeps minimum of 2 steps per enabled dimension.
    """
    steps = steps[:]
    if _product(steps) <= max_points:
        return steps
    # Iteratively reduce the currently largest dimension
    while _product(steps) > max_points:
        # find index of max steps (>2)
        idx = max(range(len(steps)), key=lambda i: steps[i])
        if steps[idx] > 2:
            steps[idx] -= 1
        else:
            # cannot shrink further; give up
            break
    return steps


class GridSearchRunner:
    def __init__(self, plan: SearchPlan):
        self.plan = plan

    def _build_grid(self) -> Tuple[List[str], List[List[float]]]:
        names = [r.name for r in self.plan.ranges if r.enabled]
        vals_list = [r.values() for r in self.plan.ranges if r.enabled]
        # shrink if too many points
        steps = [len(v) for v in vals_list]
        total = _product(steps)
        if total > self.plan.max_points:
            new_steps = _shrink_steps(steps, self.plan.max_points)
            new_vals_list: List[List[float]] = []
            for vs, ns in zip(vals_list, new_steps):
                if len(vs) == ns:
                    new_vals_list.append(vs)
                else:
                    # pick ns points uniformly from vs
                    if ns <= 1:
                        new_vals_list.append([vs[0]])
                    else:
                        idxs = [round(i * (len(vs) - 1) / (ns - 1)) for i in range(ns)]
                        new_vals_list.append([vs[i] for i in idxs])
            vals_list = new_vals_list
        return names, vals_list

    def run(self,
            base_params: SolverParams,
            on_result: Optional[Callable[[Dict], None]] = None,
            on_progress: Optional[Callable[[int, int], None]] = None,
            stop_flag: Optional[threading.Event] = None) -> pd.DataFrame:
        names, vals_list = self._build_grid()
        combos = list(itertools.product(*vals_list)) if vals_list else [()]
        total = len(combos)
        rows: List[Dict] = []
        start_time = time.time()

        quick_remaining = self.plan.topk_quick

        for idx, values in enumerate(combos, start=1):
            if stop_flag and stop_flag.is_set():
                break
            # Respect time budget
            if (time.time() - start_time) > self.plan.time_budget_min * 60:
                break

            # Build parameter set
            p = SolverParams(**base_params.as_dict())
            overrides = dict(zip(names, values))
            for k, v in overrides.items():
                # cast to appropriate type for ints
                if k in ("nx", "ny", "n_steps_load", "n_steps_unload", "max_attempts"):
                    setattr(p, k, int(round(float(v))))
                else:
                    setattr(p, k, float(v))

            # Diagnostics directory per point
            diag_dir = make_diag_dir("search")

            # Execute dry-run first
            pr: ProcessResult = run_dry_run(p, diag_dir=diag_dir, timeout=self.plan.timeout_dry)
            attempts_df = pr.attempts_df if pr and pr.attempts_df is not None else load_attempts(diag_dir)
            nodes = None
            facets = None
            tol = None
            D_eff = None
            y_top = None
            if attempts_df is not None and not attempts_df.empty:
                last = attempts_df.iloc[-1]
                nodes = int(last.get('nodes', 0))
                facets = int(last.get('facets', 0))
                tol = float(last.get('tol', float('nan')))
                D_eff = float(last.get('D_eff', float('nan')))
                y_top = float(last.get('y_top', float('nan')))

            success_region = bool(pr.success) and (nodes is not None and nodes > 0)

            row = {
                'idx': idx,
                'success_region': success_region,
                'nodes': nodes,
                'facets': facets,
                'tol': tol,
                'D_eff': D_eff,
                'y_top': y_top,
                'diag_dir': diag_dir,
            }
            # include parameter overrides in row
            for k, v in overrides.items():
                row[k] = v

            # Optionally quick-solve on successful region
            quick_done = False
            if self.plan.mode == 'quick' and success_region and quick_remaining > 0:
                qs = run_quick_solve(p,
                                     quick_steps=self.plan.quick_steps,
                                     diag_dir=diag_dir,
                                     timeout=self.plan.timeout_quick)
                row['success_quick'] = bool(qs.success)
                # Last-step metrics if available
                if getattr(qs, 'result_df', None) is not None and not qs.result_df.empty:
                    last2 = qs.result_df.iloc[-1]
                    row['Fy_N_last'] = float(last2.get('Fy_N', float('nan')))
                    row['uy_center_last'] = float(last2.get('uy_center', float('nan')))
                quick_done = True
                quick_remaining -= 1

            rows.append(row)

            if on_result:
                try:
                    on_result(row)
                except Exception:
                    pass

            if on_progress:
                try:
                    on_progress(idx, total)
                except Exception:
                    pass

        df = pd.DataFrame(rows)
        return df

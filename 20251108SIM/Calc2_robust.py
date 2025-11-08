# file: Calc2_robust.py
# Purpose: Make region selection (TopBand/TopBandVerts) robust against empty selections
# by using non-strict comparisons, mesh-based tolerances, and automatic widening retries.

import sys
import argparse
import logging
import os
import numpy as np
import pandas as pd
from sfepy.discrete import Problem
from sfepy.discrete.fem import Mesh, FEDomain, Field
from sfepy.mechanics.matcoefs import stiffness_from_youngpoisson
from sfepy.terms import Term
from sfepy.discrete.variables import FieldVariable
from sfepy.discrete.materials import Material
from sfepy.discrete.integrals import Integral
from sfepy.discrete.conditions import Conditions, EssentialBC
from sfepy.solvers.ls import ScipyDirect
from sfepy.solvers.nls import Newton

logger = logging.getLogger("Calc2_robust")

# -------- Defaults (can be overridden by CLI) --------
E_DEFAULT = 10e9          # Pa
NU_DEFAULT = 0.2
W_DEFAULT = 1         # m (width)
H_DEFAULT = 1         # m (thickness)
D_DEFAULT = 0.040         # m (punch band width)
U_MAX_DEFAULT = 1.0e-4    # m
N_LOAD_DEFAULT = 20
N_UNLOAD_DEFAULT = 20
NX_DEFAULT, NY_DEFAULT = 300, 60

TOL_ABS_DEFAULT = 1e-12       # small absolute safeguard
TOL_FACTOR_DEFAULT = 0.5  # relative to min(hx,hy)
SAFETY_GROWTH_DEFAULT = 1.10  # widen band by +10% each attempt (stronger growth)
MAX_ATTEMPTS_DEFAULT = 100      # retry attempts to find non-empty regions (increased)

OUTPUT_CSV = "result_elastic_press_robust.csv"


def build_mesh(W, H, nx, ny):
    coors = np.array([[x, y]
                      for j in range(ny + 1)
                      for i in range(nx + 1)
                      for x in [W * i / nx]
                      for y in [H * j / ny]], dtype=float)
    conn = []
    for j in range(ny):
        for i in range(nx):
            n0 = j * (nx + 1) + i
            n1 = n0 + 1
            n2 = n0 + (nx + 1)
            n3 = n2 + 1
            conn.append([n0, n1, n3])
            conn.append([n0, n3, n2])
    conn = np.array(conn, dtype=np.int32)
    mat_id = np.zeros((conn.shape[0],), dtype=np.int32)
    mesh = Mesh.from_data('rect_tri', coors, None, [conn], [mat_id], ['2_3'])
    return mesh, coors


def compute_tols(W, H, nx, ny, tol_abs, tol_factor, attempt):
    """Compute geometric tolerance from true mesh divisions (nx, ny).
    nx, ny must be the mesh division counts along x,y (not node counts).
    """
    hx = W / nx
    hy = H / ny
    base_tol = max(tol_abs, tol_factor * min(hx, hy))
    # Exponentially increase tolerance per attempt
    return base_tol * (2 ** attempt)


def build_regions_with_retries(domain, coors, W, H, nx, ny, x0, D, tol_abs, tol_factor,
                               safety_growth, max_attempts, diag_dir=None):
    bbox = domain.get_mesh_bounding_box()
    min_x, max_x = bbox[:, 0]
    min_y, max_y = bbox[:, 1]

    last_error = None

    # optional diagnostics CSV
    attempts_log = []

    for attempt in range(max_attempts):
        tol = compute_tols(W, H, nx=nx, ny=ny, tol_abs=tol_abs, tol_factor=tol_factor, attempt=attempt)
        # band widening per attempt
        D_eff = D * (safety_growth ** attempt)

        # Use a top-y threshold relaxed by mesh step to robustly capture the top row
        hy = H / ny
        y_top_eff = max_y - max(tol, 0.5 * hy)
        x_left = x0 - D_eff / 2.0 - tol
        x_right = x0 + D_eff / 2.0 + tol

        try:
            top_band = domain.create_region(
                'TopBand',
                f'vertices in ((y >= {y_top_eff}) & (x >= {x_left}) & (x <= {x_right}))',
                'facet'
            )
            top_band_verts = domain.create_region(
                'TopBandVerts',
                f'vertices in ((y >= {y_top_eff}) & (x >= {x_left}) & (x <= {x_right}))'
            )

            # pin node region (no facet): lower-left corner, non-strict
            pin_region = domain.create_region(
                'PinNode',
                f'vertices in ((x <= {min_x + tol}) & (y <= {min_y + tol}))'
            )

            # Validate
            n_facet = len(top_band.entities)
            band_nodes = np.array(top_band_verts.entities, dtype=int)
            n_nodes = band_nodes.size

            # Attempt record
            attempts_log.append({
                'attempt': attempt + 1,
                'tol': tol,
                'D_eff': D_eff,
                'y_top': y_top_eff,
                'facets': n_facet,
                'nodes': n_nodes
            })

            logger.info(
                f"Attempt {attempt+1}/{max_attempts}: tol={tol:.3e}, D_eff={D_eff:.6f}, y_top={y_top_eff:.6e}, "
                f"TopBand facets={n_facet}, TopBandVerts nodes={n_nodes}"
            )

            # 条件緩和: facet が 0 でも vertices が非空ならより強く上面条件を緩めて再生成
            if n_nodes == 0:
                last_error = (tol, D_eff, n_facet, n_nodes)
                continue
            if n_facet == 0 and n_nodes > 0:
                # First stronger relax using mesh step size
                y_top2 = max_y - max(2.0 * tol, 0.75 * hy)
                try:
                    top_band = domain.create_region(
                        'TopBand',
                        f'vertices in ((y >= {y_top2}) & (x >= {x_left}) & (x <= {x_right}))',
                        'facet'
                    )
                    n_facet = len(top_band.entities)
                    logger.info(f"Facet relaxed-1: y_top -> {y_top2:.6e}, facets={n_facet}")
                except Exception as e2:
                    logger.warning(f"Facet relaxed-1 regeneration failed: {e2}")

                if n_facet == 0:
                    # Second relax even deeper (down to one full hy)
                    y_top3 = max_y - max(3.0 * tol, 1.0 * hy)
                    try:
                        top_band = domain.create_region(
                            'TopBand',
                            f'vertices in ((y >= {y_top3}) & (x >= {x_left}) & (x <= {x_right}))',
                            'facet'
                        )
                        n_facet = len(top_band.entities)
                        logger.info(f"Facet relaxed-2: y_top -> {y_top3:.6e}, facets={n_facet}")
                    except Exception as e3:
                        logger.warning(f"Facet relaxed-2 regeneration failed: {e3}")

                # If still zero facets but vertices exist, fall back to vertex-only BC region
                if n_facet == 0:
                    logger.warning("No facets found for TopBand even after relax. Falling back to vertex-only region for BCs.")
                    top_band = top_band_verts  # Use vertices region for EssentialBC

            # 最終チェック: この時点で vertices は非空
            xs = coors[band_nodes, 0]
            ys = coors[band_nodes, 1]
            logger.info(
                f"TopBandVerts x-range=({xs.min():.6f},{xs.max():.6f}), y≈{ys.mean():.6f}"
            )

            # dump attempts log if requested
            if diag_dir:
                try:
                    os.makedirs(diag_dir, exist_ok=True)
                    import csv
                    with open(os.path.join(diag_dir, 'region_attempts.csv'), 'w', newline='') as f:
                        w = csv.DictWriter(f, fieldnames=['attempt','tol','D_eff','y_top','facets','nodes'])
                        w.writeheader()
                        for row in attempts_log:
                            w.writerow(row)
                except Exception as e_csv:
                    logger.warning(f"Failed to write attempts log CSV: {e_csv}")

            return top_band, top_band_verts, pin_region, tol, D_eff

        except Exception as e:
            logger.warning(f"Region build failed at attempt {attempt+1}: {e}")
            last_error = e
            continue

    # dump attempts log on failure
    if diag_dir and attempts_log:
        try:
            os.makedirs(diag_dir, exist_ok=True)
            import csv
            with open(os.path.join(diag_dir, 'region_attempts.csv'), 'w', newline='') as f:
                w = csv.DictWriter(f, fieldnames=['attempt','tol','D_eff','y_top','facets','nodes'])
                w.writeheader()
                for row in attempts_log:
                    w.writerow(row)
        except Exception as e_csv:
            logger.warning(f"Failed to write attempts log CSV (on failure): {e_csv}")

    # If we get here, all attempts failed
    msg = (
        "TopBand/TopBandVerts の生成に失敗しました。非空領域が得られません。" \
        " tol_factor/安全係数(D拡張)やメッシュ密度、D の値を見直してください。"
    )
    if isinstance(last_error, tuple):
        tol, D_eff, n_facet, n_nodes = last_error
        msg += f" [last tol={tol:.3e}, D_eff={D_eff:.6f}, facets={n_facet}, nodes={n_nodes}]"
    raise RuntimeError(msg)


def solve_problem(args):
    # Mesh
    mesh, coors = build_mesh(args.W, args.H, args.nx, args.ny)
    domain = FEDomain('domain', mesh)
    bbox = domain.get_mesh_bounding_box()
    min_x, max_x = bbox[:, 0]
    min_y, max_y = bbox[:, 1]

    # Regions with retries
    x0 = 0.5 * (min_x + max_x)
    top_band, top_band_verts, pin_region, eff_tol, eff_D = build_regions_with_retries(
        domain, coors, args.W, args.H, args.nx, args.ny, x0, args.D, args.tol_abs, args.tol_factor,
        args.safety_growth, args.max_attempts, diag_dir=args.diag_dir
    )

    # If dry-run, just print a quick preview and exit
    if args.dry_run:
        band_nodes = np.array(top_band_verts.entities, dtype=int)
        logger.info(f"[DRY-RUN] TopBandVerts count: {band_nodes.size}")
        preview = coors[band_nodes[:min(8, band_nodes.size)]] if band_nodes.size else np.empty((0, 2))
        logger.info(f"[DRY-RUN] Preview first nodes (x,y):\n{preview}")
        # Optional: write diagnostics
        if args.diag_dir:
            try:
                os.makedirs(args.diag_dir, exist_ok=True)
                # write preview CSV (up to first 50 points)
                import csv
                with open(os.path.join(args.diag_dir, 'topband_verts_preview.csv'), 'w', newline='') as f:
                    w = csv.writer(f)
                    w.writerow(['x','y'])
                    limit = min(50, band_nodes.size)
                    for i in range(limit):
                        x, y = coors[band_nodes[i]]
                        w.writerow([x, y])
                # write indices
                with open(os.path.join(args.diag_dir, 'topband_verts_indices.txt'), 'w') as f:
                    for idx in band_nodes.tolist():
                        f.write(str(idx) + '\n')
                logger.info(f"[DRY-RUN] Wrote diagnostics to: {args.diag_dir}")
            except Exception as e_diag:
                logger.warning(f"[DRY-RUN] Failed to write diagnostics: {e_diag}")
        return None

    # Field and variables (2D vector field, plane strain)
    field = Field.from_args('displacement', np.float64, 'vector', domain.create_region('Omega', 'all'), approx_order=1)
    u = FieldVariable('u', 'unknown', field)
    v = FieldVariable('v', 'test', field, primary_var_name='u')

    # Elasticity (plane strain)
    Dmat = stiffness_from_youngpoisson(2, args.E, args.nu, plane='strain')
    mat = Material('Solid', D=Dmat)

    integral = Integral('i', order=2)
    t1 = Term.new('dw_lin_elastic(Solid.D, v, u)', integral, field.region, Solid=mat, v=v, u=u)

    # Boundary conditions
    fix_bottom = EssentialBC('fix_bottom', domain.create_region('Bottom', f'vertices in (y <= {min_y + eff_tol})', 'facet'), {'u.1': 0.0})
    pin_x = EssentialBC('pin_x', pin_region, {'u.0': 0.0})

    ls = ScipyDirect({})
    nls = Newton({}, lin_solver=ls)

    pb = Problem('elastic_press', equations={'balance': t1})

    def make_top_bc(uy):
        return EssentialBC('punch', top_band, {'u.1': -uy, 'u.0': 0.0})

    # Time stepping sequence
    steps = []
    for k in range(args.n_steps_load):
        steps.append((k, (k + 1) / args.n_steps_load * args.u_max))
    for k in range(args.n_steps_unload):
        steps.append((args.n_steps_load + k, (1 - (k + 1) / args.n_steps_unload) * args.u_max))

    records = []
    for istep, uy in steps:
        ebcs = Conditions([fix_bottom, pin_x, make_top_bc(uy)])
        pb.time_update(ebcs=ebcs)
        state = pb.solve(nls=nls)

        vec = state.get_state_parts()['u']
        r = pb.equations.eval_residuals(state())

        band_nodes = np.unique(np.array(top_band_verts.entities, dtype=int))
        if band_nodes.size == 0:
            raise RuntimeError("TopBandVerts に頂点が見つかりません（解法中）。")

        Fy = 0.0
        for n in band_nodes:
            dof_y = 2 * n + 1
            if dof_y >= r.shape[0]:
                raise RuntimeError(f"DOF index out of range: {dof_y} >= {r.shape[0]}")
            Fy += -r[dof_y]

        band_coors = coors[band_nodes]
        # Choose center by closest x to x0, break ties by highest y (use lexsort)
        dx2 = (band_coors[:, 0] - x0) ** 2
        # primary key: dx2, secondary: -y (to prefer topmost if equal x distance)
        order = np.lexsort((-band_coors[:, 1], dx2))
        center_node = int(band_nodes[order[0]])
        uy_node = vec[2 * center_node + 1]

        records.append({'step': istep, 'uy_cmd': -uy, 'uy_center': uy_node, 'Fy_N': Fy})

    df = pd.DataFrame(records)
    df.to_csv(OUTPUT_CSV, index=False)
    logger.info(f"Saved: {OUTPUT_CSV}")
    print(df.tail())
    return df


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Elastic press (robust region) with SfePy")
    p.add_argument('--E', type=float, default=E_DEFAULT, help='Young\'s modulus [Pa]')
    p.add_argument('--nu', type=float, default=NU_DEFAULT, help='Poisson ratio [-]')
    p.add_argument('--W', type=float, default=W_DEFAULT, help='Width W [m]')
    p.add_argument('--H', type=float, default=H_DEFAULT, help='Height/Thickness H [m]')
    p.add_argument('--D', type=float, default=D_DEFAULT, help='Punch contact width D [m]')
    p.add_argument('--u-max', type=float, default=U_MAX_DEFAULT, help='Max downward displacement [m]')
    p.add_argument('--n-steps-load', type=int, default=N_LOAD_DEFAULT, dest='n_steps_load', help='Load steps')
    p.add_argument('--n-steps-unload', type=int, default=N_UNLOAD_DEFAULT, dest='n_steps_unload', help='Unload steps')
    p.add_argument('--nx', type=int, default=NX_DEFAULT, help='Mesh density in x')
    p.add_argument('--ny', type=int, default=NY_DEFAULT, help='Mesh density in y')
    p.add_argument('--tol-abs', type=float, default=TOL_ABS_DEFAULT, dest='tol_abs', help='Absolute tolerance')
    p.add_argument('--tol-factor', type=float, default=TOL_FACTOR_DEFAULT, help='Geometric tolerance factor * min(h)')
    p.add_argument('--safety-growth', type=float, default=SAFETY_GROWTH_DEFAULT, help='Band widening factor per attempt')
    p.add_argument('--max-attempts', type=int, default=MAX_ATTEMPTS_DEFAULT, help='Max region build attempts')
    p.add_argument('--dry-run', action='store_true', help='Only build regions and print diagnostics')
    p.add_argument('--log-level', type=str, default='INFO', help='Logging level (DEBUG, INFO, WARNING, ERROR)')
    p.add_argument('--diag-dir', type=str, default=None, help='Directory to write diagnostics (region attempts, previews)')
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format='%(asctime)s - %(levelname)s - %(message)s')
    try:
        solve_problem(args)
    except Exception as e:
        logger.error(f"解析に失敗しました: {e}")
        raise


if __name__ == '__main__':
    main()

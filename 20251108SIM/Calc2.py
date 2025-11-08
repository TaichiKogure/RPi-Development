
# file: two_step_compression_elastic.py
import numpy as np
import pandas as pd
from sfepy import data_dir
from sfepy.discrete import Problem
from sfepy.discrete.fem import Mesh, FEDomain, Field
from sfepy.base.base import IndexedStruct
from sfepy.mechanics.matcoefs import stiffness_from_youngpoisson
from sfepy.terms import Term
from sfepy.discrete.variables import FieldVariable
from sfepy.discrete.materials import Material
from sfepy.discrete.integrals import Integral
from sfepy.discrete.conditions import Conditions, EssentialBC
from sfepy.solvers.ls import ScipyDirect
from sfepy.solvers.nls import Newton

# Parameters (SI units)
E = 10e9       # Pa
nu = 0.30
W = 0.100      # m width
H = 0.010      # m thickness
D = 0.020      # m punch contact width (centered on top)
u_max = 1.0e-4 # m max downward displacement (0.1 mm)
n_steps_load = 20
n_steps_unload = 20
nx, ny = 120, 30  # mesh density

# Build rectangular mesh [0,W] x [0,H]
coors = np.array([[x, y]  # 2D coordinates only
                  for j in range(ny+1)
                  for i in range(nx+1)
                  for x in [W * i / nx]
                  for y in [H * j / ny]], dtype=float)
conn = []
for j in range(ny):
    for i in range(nx):
        n0 = j*(nx+1) + i
        n1 = n0 + 1
        n2 = n0 + (nx+1)
        n3 = n2 + 1
        # two triangles per quad
        conn.append([n0, n1, n3])
        conn.append([n0, n3, n2])
conn = np.array(conn, dtype=np.int32)
# SfePy expects 2D '2_3' for triangles.
mat_id = np.zeros((conn.shape[0],), dtype=np.int32)
mesh = Mesh.from_data('rect_tri', coors, None, [conn], [mat_id], ['2_3'])

domain = FEDomain('domain', mesh)
bbox = domain.get_mesh_bounding_box()
min_x, max_x = bbox[:, 0]
min_y, max_y = bbox[:, 1]

# Regions
# robust tolerances
hx = W / nx
hy = H / ny
# small absolute tol to include boundary vertices and avoid empty regions
tol_abs = 1e-12
# also keep a geometric tolerance, but use non-strict comparisons
tol = max(tol_abs, 0.25 * min(hx, hy))

omega = domain.create_region('Omega', 'all')
# boundary facets determined by vertex coordinates (use non-strict)
bottom = domain.create_region('Bottom', f'vertices in (y <= {min_y + tol})', 'facet')
left   = domain.create_region('Left',   f'vertices in (x <= {min_x + tol})', 'facet')
right  = domain.create_region('Right',  f'vertices in (x >= {max_x - tol})', 'facet')

# Top central band for punch (on top edge)
x0 = 0.5 * (min_x + max_x)
# use non-strict comparisons to ensure inclusion of top-row vertices
x_left  = x0 - D/2 - tol
x_right = x0 + D/2 + tol
y_top   = max_y - tol

top_band = domain.create_region(
    'TopBand',
    f'vertices in ((y >= {y_top}) & (x >= {x_left}) & (x <= {x_right}))',
    'facet'
)
# Vertex set corresponding to the same top band (for DOF/reaction extraction)
top_band_verts = domain.create_region(
    'TopBandVerts',
    f'vertices in ((y >= {y_top}) & (x >= {x_left}) & (x <= {x_right}))'
)

# Robust pin node selection by coordinate region (vertex set, no 'facet')
pin_region = domain.create_region(
    'PinNode',
    f'vertices in ((x <= {min_x + tol}) & (y <= {min_y + tol}))'
)

# Field and variables (2D vector field, plane strain)
field = Field.from_args('displacement', np.float64, 'vector', omega, approx_order=1)
u = FieldVariable('u', 'unknown', field)
v = FieldVariable('v', 'test', field, primary_var_name='u')

# Elasticity (plane strain)
Dmat = stiffness_from_youngpoisson(2, E, nu, plane='strain')
mat = Material('Solid', D=Dmat)

integral = Integral('i', order=2)
t1 = Term.new('dw_lin_elastic(Solid.D, v, u)', integral, omega, Solid=mat, v=v, u=u)

# Boundary conditions
fix_bottom = EssentialBC('fix_bottom', bottom, {'u.1': 0.0})
pin_x = EssentialBC('pin_x', pin_region, {'u.0': 0.0})

def ramp(t):
    return t

ls = ScipyDirect({})
nls = Newton({}, lin_solver=ls)

pb = Problem('elastic_press', equations={'balance': t1})

def make_top_bc(uy):
    return EssentialBC('punch', top_band, {'u.1': -uy, 'u.0': 0.0})

# Time stepping: load then unload
steps = []
for k in range(n_steps_load):
    steps.append((k, (k+1)/n_steps_load * u_max))
for k in range(n_steps_unload):
    steps.append((n_steps_load + k, (1 - (k+1)/n_steps_unload) * u_max))

records = []
for istep, uy in steps:
    ebcs = Conditions([fix_bottom, pin_x, make_top_bc(uy)])
    pb.time_update(ebcs=ebcs)
    state = pb.solve(nls=nls)

    # Residual vector
    vec = state.get_state_parts()['u']
    r = pb.equations.eval_residuals(state())

    # Sum Y-direction reactions at top band DOFs (use vertex region)
    band_nodes = np.array(top_band_verts.entities, dtype=int).copy()
    if band_nodes.size == 0:
        raise RuntimeError("TopBandVerts に頂点が見つかりません。tol と D の設定、または region 条件を確認してください。")
    Fy = 0.0
    for n in band_nodes:
        dof_y = 2*n + 1
        Fy += -r[dof_y]  # reaction = -residual

    # Track tip displacement at center of band (use vertex coordinates)
    band_coors = coors[band_nodes]
    center_node = int(band_nodes[np.argmin((band_coors[:, 0] - x0)**2)])
    uy_node = vec[2*center_node + 1]
    records.append({'step': istep, 'uy_cmd': -uy, 'uy_center': uy_node, 'Fy_N': Fy})

df = pd.DataFrame(records)
df.to_csv('result_elastic_press.csv', index=False)
print('Saved: result_elastic_press.csv')
print(df.tail())
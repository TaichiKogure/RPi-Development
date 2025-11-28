from typing import Optional
import pandas as pd
from matplotlib.figure import Figure

try:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
except Exception:
    # Newer Matplotlib can use QtAgg
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas


def new_canvas() -> FigureCanvas:
    fig = Figure(figsize=(5, 3), dpi=100)
    canvas = FigureCanvas(fig)
    return canvas


def plot_attempts(canvas: FigureCanvas, attempts_df: Optional[pd.DataFrame]):
    fig: Figure = canvas.figure
    fig.clear()
    ax1 = fig.add_subplot(121)
    ax2 = fig.add_subplot(122)

    if attempts_df is not None and not attempts_df.empty:
        x = attempts_df.get('attempt', range(1, len(attempts_df) + 1))
        # Left: tolerance / D_eff / y_top
        ax1.plot(x, attempts_df.get('tol', []), label='tol', marker='o')
        if 'D_eff' in attempts_df.columns:
            ax1.plot(x, attempts_df['D_eff'], label='D_eff', marker='s')
        if 'y_top' in attempts_df.columns:
            ax1.plot(x, attempts_df['y_top'], label='y_top', marker='^')
        ax1.set_title('Attempts: tol / D_eff / y_top')
        ax1.set_xlabel('attempt')
        ax1.legend()

        # Right: facets / nodes
        ax2.plot(x, attempts_df.get('facets', []), label='facets', marker='o')
        ax2.plot(x, attempts_df.get('nodes', []), label='nodes', marker='s')
        ax2.set_title('Attempts: facets / nodes')
        ax2.set_xlabel('attempt')
        ax2.legend()
    else:
        ax1.text(0.5, 0.5, 'No attempts data', ha='center', va='center')
        ax2.text(0.5, 0.5, 'No attempts data', ha='center', va='center')

    fig.tight_layout()
    canvas.draw_idle()


def plot_topband_scatter(canvas: FigureCanvas, preview_df: Optional[pd.DataFrame]):
    fig: Figure = canvas.figure
    fig.clear()
    ax = fig.add_subplot(111)

    if preview_df is not None and not preview_df.empty:
        x = preview_df.get('x')
        y = preview_df.get('y')
        if x is not None and y is not None:
            ax.scatter(x, y, s=12, c='tab:blue')
            ax.set_xlabel('x [m]')
            ax.set_ylabel('y [m]')
            ax.set_title('TopBandVerts preview (first ~50 nodes)')
        else:
            ax.text(0.5, 0.5, 'Preview CSV must have x,y columns', ha='center', va='center')
    else:
        ax.text(0.5, 0.5, 'No preview data', ha='center', va='center')

    fig.tight_layout()
    canvas.draw_idle()

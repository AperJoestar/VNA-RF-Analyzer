"""Small matplotlib helpers."""
import numpy as np
from matplotlib import ticker


def apply_min_max_axis_limits(ax, xdata=None, ydata=None, num_y_ticks=6, pad_y=0.08):
    """
    Applies Min/Max data bounds to matplotlib axis limits and adds vertical padding
    to prevent smooth interpolation curves from clipping at top/bottom edges.
    """
    if xdata is not None:
        xa = np.asarray(xdata, dtype=float)
        valid_x = xa[np.isfinite(xa)]
        if len(valid_x) > 0:
            ax.set_xlim(np.min(valid_x), np.max(valid_x))

    if ydata is not None:
        ya = np.asarray(ydata, dtype=float)
        valid_y = ya[np.isfinite(ya)]
        if len(valid_y) > 0:
            ymin, ymax = np.min(valid_y), np.max(valid_y)
            if ymin == ymax:
                ymin -= 1.0
                ymax += 1.0
            else:
                span = ymax - ymin
                ymin -= span * pad_y
                ymax += span * pad_y
            
            ax.set_ylim(ymin, ymax)
            y_ticks = np.linspace(ymin, ymax, num_y_ticks)
            ax.set_yticks(y_ticks)
            ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.4f'))

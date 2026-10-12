"""Signal-processing helpers: smoothing, cardinal splines and SWR (numpy / scipy only, no GUI)."""
import numpy as np
from scipy.signal import savgol_filter


def apply_smoothing(y_array, window_size=15, polyorder=2):
    """Applies Savitzky-Golay smoothing filter to RF trace data arrays."""
    if y_array is None or len(y_array) < 5:
        return y_array
    w = int(window_size)
    if w >= len(y_array):
        w = len(y_array) - 1 if len(y_array) % 2 == 0 else len(y_array) - 2
    if w < 3:
        return y_array
    if w % 2 == 0:
        w += 1
    p = min(polyorder, w - 1)
    try:
        y_arr = np.array(y_array, dtype=float)
        nans = np.isnan(y_arr)
        if np.all(nans):
            return y_arr
        if np.any(nans):
            valid = ~nans
            y_clean = np.interp(np.arange(len(y_arr)), np.where(valid)[0], y_arr[valid])
            smoothed = savgol_filter(y_clean, window_length=w, polyorder=p)
            smoothed[nans] = np.nan
            return smoothed
        return savgol_filter(y_arr, window_length=w, polyorder=p)
    except Exception:
        return y_array


def cardinal_spline(x, y, tension=0.5, seg=10):
    """Cardinal spline through all points (same idea as GDI+ DrawCurve, tension 0.5)."""
    pts = np.column_stack([np.asarray(x, float), np.asarray(y, float)])
    n = len(pts)
    if n < 3:
        return pts[:, 0], pts[:, 1]
    m = np.zeros_like(pts)
    m[1:-1] = tension * (pts[2:] - pts[:-2])
    m[0] = tension * (pts[1] - pts[0])
    m[-1] = tension * (pts[-1] - pts[-2])
    t = np.linspace(0.0, 1.0, seg, endpoint=False)[:, None]
    h00, h10, h01, h11 = 2*t**3 - 3*t**2 + 1, t**3 - 2*t**2 + t, -2*t**3 + 3*t**2, t**3 - t**2
    out = [h00*pts[i] + h10*m[i] + h01*pts[i+1] + h11*m[i+1] for i in range(n - 1)]
    out.append(pts[-1:])
    c = np.vstack(out)
    return c[:, 0], c[:, 1]


def cardinal_curve(x, y, tension=0.5, steps=24):
    """Smooth curve through all points, same as GDI+ Graphics.DrawCurve (cardinal spline, tension 0.5)."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    n = len(x)
    if n < 3:
        return x, y
    P = np.column_stack([x, y])
    ext = np.vstack([P[0], P, P[-1]])            # end tangents use the neighbouring point
    t = np.linspace(0.0, 1.0, steps, endpoint=False)[:, None]
    h00 = 2*t**3 - 3*t**2 + 1; h10 = t**3 - 2*t**2 + t
    h01 = -2*t**3 + 3*t**2;    h11 = t**3 - t**2
    out = []
    for i in range(n - 1):
        p0, p1, p2, p3 = ext[i], ext[i+1], ext[i+2], ext[min(i+3, n+1)]
        m1 = tension * (p2 - p0); m2 = tension * (p3 - p1)
        out.append(h00*p1 + h10*m1 + h01*p2 + h11*m2)
    out.append(P[-1:])
    C = np.vstack(out)
    return C[:, 0], C[:, 1]


def compute_swr(s_complex):
    """Voltage standing-wave ratio from a complex reflection coefficient (no clamping)."""
    # Matches the C# app exactly: SWR = (1 + |S11|) / (1 - |S11|) with NO clamping.
    # |S11| == 1 -> +/-inf, |S11| > 1 -> negative values (same as C# double math).
    mag = np.abs(s_complex)
    with np.errstate(divide='ignore', invalid='ignore'):
        return (1.0 + mag) / (1.0 - mag)

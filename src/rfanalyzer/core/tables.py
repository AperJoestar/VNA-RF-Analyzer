"""Number formatting and table helpers shared by the Key Parameters tab, the trend table and the exports."""
import numpy as np


# Column headers of the zone/marker table and of the antenna table
TREND_TABLE_COLS = ["N", "File Name", "C(Mag)", "Δ(Mag).dB", "Mag. dB", "Z. Freq,GHz"]
ANTENNA_TABLE_COLS = ["N", "File Name", "Mag, dB", "Mag1, dB", "Mag1-Mag, dB", "Zone"]


def cs_num(x, nd=4):
    """Number text like C# Math.Round(x, 4).ToString() (no trailing zeros)."""
    x = float(x)
    if x != x: return "NaN"
    if x in (float('inf'), float('-inf')): return "Infinity" if x > 0 else "-Infinity"
    t = f"{round(x, nd):.{nd}f}".rstrip('0').rstrip('.')
    return "0" if t in ("-0", "") else t


def cs_freq(x):
    return f"{float(x):.15g}"


def fmt_trend_row(row_data):
    """Display text of one 'Table at Zones/Markers' row (shared by the table and the export)."""
    c_txt = "1" if row_data[2] == 1.0 else (f"{row_data[2]:.8f}" if not np.isnan(row_data[2]) else "N/A")
    d_txt = "0" if row_data[3] == 0.0 else (f"{row_data[3]:.8f}" if not np.isnan(row_data[3]) else "N/A")
    m_txt = f"{row_data[4]:.6f}" if not np.isnan(row_data[4]) else "N/A"
    return [row_data[0], row_data[1], c_txt, d_txt, m_txt, row_data[5]]


def find_best_table_rows(rows):
    """Indices of the best row of every zone/marker block (port of Form1.ShowTable).
    Best = lowest Delta(Mag),dB inside the block. The baseline row (delta 0) takes part, and the C#
    comparison is '<=', so on a tie the LAST file wins. Rows are (N, file, C, delta, mag, block label)."""
    best = {}
    for i, row in enumerate(rows):
        d = row[3]
        if d is None or not np.isfinite(d):
            continue
        block = row[5]
        if block not in best or d <= rows[best[block]][3]:
            best[block] = i
    return set(best.values())

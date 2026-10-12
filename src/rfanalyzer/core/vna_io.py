"""Reading VNA CSV files and writing the tab-separated export files."""
import logging
import re

import pandas as pd

log = logging.getLogger(__name__)


def parse_vna_file(file_path, decimal_comma=False):
    """Read one VNA CSV export (``;`` separated, ``#`` comments).

    Returns ``{"Freq_GHz": ndarray, "S11_complex": ndarray?, "S21_complex": ndarray?}`` or ``None`` when the
    file cannot be parsed. ``decimal_comma=True`` reads European ``1,5`` style numbers.
    """
    try:
        decimal = ',' if decimal_comma else '.'
        df = pd.read_csv(file_path, sep=';', comment='#', decimal=decimal)
        df.columns = df.columns.str.strip()
        df = df.dropna(how='all', axis=1)

        freq_col = [c for c in df.columns if 'freq' in c.lower()][0]
        freqs = df[freq_col].values / 1e9
        result = {'Freq_GHz': freqs}

        s11_cols = [c for c in df.columns if 's11' in c.lower() or 'trc1' in c.lower()]
        re_s11 = [c for c in s11_cols if 're:' in c.lower() or 'real' in c.lower()]
        im_s11 = [c for c in s11_cols if 'im:' in c.lower() or 'imag' in c.lower()]
        if re_s11 and im_s11:
            result['S11_complex'] = df[re_s11[0]].values + 1j * df[im_s11[0]].values

        s21_cols = [c for c in df.columns if 's21' in c.lower() or 'trc2' in c.lower()]
        re_s21 = [c for c in s21_cols if 're:' in c.lower() or 'real' in c.lower()]
        im_s21 = [c for c in s21_cols if 'im:' in c.lower() or 'imag' in c.lower()]
        if re_s21 and im_s21:
            result['S21_complex'] = df[re_s21[0]].values + 1j * df[im_s21[0]].values

        return result
    except Exception:
        log.debug("Could not parse %s", file_path, exc_info=True)
        return None


def natural_sort_key(s):
    """Sorts strings containing numbers naturally (e.g., 2 before 10)."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(s))]


def write_tsv(path, lines):
    """Layout of the C# StreamWriter files: a tab after EVERY cell (also the last one), UTF-8 with BOM."""
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        for cells in lines:
            fh.write("".join(f"{c}\t" for c in cells) + "\r\n")

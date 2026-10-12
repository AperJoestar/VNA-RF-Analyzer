"""Text/PNG exports (zExport*, DGRV tables, summary reports, screenshots)."""
import datetime
import os
from tkinter import filedialog, messagebox

import numpy as np

from rfanalyzer.config import PICS_DIR
from rfanalyzer.core.dsp import compute_swr
from rfanalyzer.core.tables import find_best_table_rows, fmt_trend_row, TREND_TABLE_COLS
from rfanalyzer.core.vna_io import write_tsv


class ExportMixin:
    """Text/PNG exports (zExport*, DGRV tables, summary reports, screenshots).

    Mixed into :class:`rfanalyzer.gui.main_window.RFAnalyzerApp`; relies on the state set up in its ``__init__``.
    """

    def export_trend_table(self):
        """Export the table that is currently shown."""
        mode = getattr(self, 'trend_mode', 'zone')
        try:
            if mode == "antenna":
                # C# CreateAngle format: FileName / Mag / Mag1 / Resume / Zone, a tab after every cell
                src = getattr(self, 'last_antenna_rows', [])
                extra = getattr(self, 'last_antenna_export', [])
                if not src:
                    messagebox.showwarning("No Data", "The table is empty - load files and run the analysis first.")
                    return
                lines = [["FileName", "Mag", "Mag1", "Resume", "Zone"]]
                for (n, label, a, b, d, zone), (stem, zone_cs) in zip(src, extra):
                    lines.append([stem, self._fmt_export_num(a), self._fmt_export_num(b), self._fmt_export_num(d), zone_cs])
                stem_name = "zExport_DGRV_M" if getattr(self, 'trend_base_mode', 'zone') == "marker" else "zExport_DGRV"
                path = self._export_stamp_path(stem_name)
                write_tsv(path, lines)
            else:
                src = getattr(self, 'last_trend_table_data', [])
                if not src:
                    messagebox.showwarning("No Data", "The table is empty - load files and run the analysis first.")
                    return
                # Extra "Mark" column carries the table colours: Best (green) / Baseline (gray)
                header = TREND_TABLE_COLS + ["Mark"]
                best_rows = find_best_table_rows(src)
                base = getattr(self, 'base_file_name', None)
                rows = [fmt_trend_row(r) + ["Best" if i in best_rows else ("Baseline" if r[1] == base else "")]
                        for i, r in enumerate(src)]
                stem_name = "zExport_DGRV_M" if mode == "marker" else "zExport_DGRV"
                path = self._export_stamp_path(stem_name)
                # utf-8-sig: the C# StreamWriter writes a BOM too, and Excel needs it to show the Δ sign
                with open(path, "w", encoding="utf-8-sig", newline="") as fh:
                    fh.write("\t".join(header) + "\r\n")
                    for r in rows:
                        fh.write("\t".join(str(x) for x in r) + "\r\n")
            messagebox.showinfo("Export Complete", f"Table exported to:\n{os.path.abspath(path)}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

    def _fmt_export_num(self, v):
        """double.ToString-like text; honours the 'point => comma' option (C# CheckBox1)."""
        try:
            v = float(v)
        except (TypeError, ValueError):
            return ""
        if not np.isfinite(v):
            return ""
        txt = f"{v:.15g}"
        return txt.replace(".", ",") if self.export_comma.get() else txt

    def _export_stamp_path(self, stem):
        ts = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
        return os.path.join(self.exports_dir, f"{stem}_{ts}.txt")

    def export_zexport(self, full):
        """zExportR.txt (full=False: Freq + Mag dB per file) / zExport.txt (full=True: Freq + Re/Im per file)."""
        try:
            names = [n for n in self._get_filenames() if self.file_data_cache.get(n)]
            if not names:
                messagebox.showwarning("No Data", "No CSV data is loaded.")
                return
            stems = [os.path.splitext(n)[0] for n in names]
            suffixes = [st[st.rfind("_") + 1:] for st in stems]      # text after the last "_" (C# LastIndexOf)
            datas = [self.file_data_cache[n] for n in names]
            freqs = np.asarray(datas[0]['Freq_GHz'], float)
            two = 'S11_complex' in datas[0] and 'S21_complex' in datas[0]     # C# "TwoTrc"
            main_key = 'S21_complex' if 'S21_complex' in datas[0] else 'S11_complex'
            as_mag = self.export_s11_mag.get()
            nan_col = np.full(len(freqs), np.nan)
            mag_db = lambda z: 20 * np.log10(np.clip(np.abs(z), 1e-12, None))

            header, cols = ["Freq, GHz"], []
            for suf, d in zip(suffixes, datas):
                s11, s21 = d.get('S11_complex'), d.get('S21_complex')
                if two:
                    s11 = s11 if s11 is not None else nan_col
                    s21 = s21 if s21 is not None else nan_col
                    lbl, lbl_i = ("_Mag S11", "_Mag S11 I") if as_mag else ("_swr", "_swrI")
                    if full:
                        header += [suf + lbl, suf + lbl_i, suf + "_Mag", suf + "_MagI"]
                        cols += [np.real(s11), np.imag(s11), np.real(s21), np.imag(s21)]
                    else:
                        header += [suf + lbl, suf + "_Mag"]
                        cols += [mag_db(s11) if as_mag else compute_swr(s11), mag_db(s21)]
                else:
                    z = d.get(main_key, nan_col)
                    if full:
                        header += [suf + "_Mag", suf + "_MagI"]
                        cols += [np.real(z), np.imag(z)]
                    else:
                        header += [suf + "_Mag"]
                        cols += [mag_db(z)]

            lines = [header]
            for i in range(len(freqs)):
                row = [self._fmt_export_num(freqs[i])]
                for c in cols:
                    row.append(self._fmt_export_num(c[i]) if i < len(c) else "")
                lines.append(row)
            path = self._export_stamp_path("zExport" if full else "zExportR")
            write_tsv(path, lines)
            messagebox.showinfo("Export Complete", f"Data exported to:\n{os.path.abspath(path)}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

    def _trend_table_rows(self, use_markers):
        """Rows of 'Table at Zones' (use_markers=False) or 'Table at Markers' (True), independent of the view."""
        choice = self.param_var.get()
        param_key = 'S11_complex' if "S11" in choice else 'S21_complex'
        base_data = self.file_data_cache.get(self.base_file_name) if self.base_file_name else None
        if not base_data or param_key not in base_data:
            return []
        base_mag = np.abs(base_data[param_key])
        base_freqs = base_data['Freq_GHz']
        items = self.get_marker_freqs() if use_markers else self.read_zones()
        rows = []
        for li, item in enumerate(items):
            for idx, f in enumerate(self._get_filenames()):
                curr = self.file_data_cache.get(f)
                if not curr or param_key not in curr:
                    continue
                freqs = curr['Freq_GHz']
                curr_mag = np.abs(curr[param_key])
                c_val = delta_val = raw_val = float('nan')
                if use_markers:
                    z_freq = f"M{li+1}. {item:g}" if item is not None else f"M{li+1}. N/A"
                    if item is not None and freqs.min() <= item <= freqs.max():
                        cv = float(np.interp(item, freqs, curr_mag))
                        bv = float(np.interp(item, base_freqs, base_mag))
                        if "Delta Log Mag" in choice:
                            curr_v = 20 * np.log10(max(cv, 1e-12)); base_v = 20 * np.log10(max(bv, 1e-12))
                        elif "Phase" in choice:
                            curr_v = float(np.angle(np.interp(item, freqs, curr[param_key]), deg=True))
                            base_v = float(np.angle(np.interp(item, base_freqs, base_data[param_key]), deg=True))
                        else:
                            curr_v, base_v = cv, bv
                        c_val = curr_v / base_v if base_v != 0 else float('nan')
                        delta_val, raw_val = curr_v - base_v, curr_v
                else:
                    z_freq = f"{li+1}. {item[0]:g}_{item[1]:g}"
                    mask = (freqs >= item[0]) & (freqs <= item[1])
                    mask_b = (base_freqs >= item[0]) & (base_freqs <= item[1])
                    if mask.any() and mask_b.any():
                        c_mag, b_mag = curr_mag[mask], base_mag[mask_b]
                        if "Delta Log Mag" in choice:
                            curr_v = 20 * np.log10(np.clip(c_mag, 1e-12, None)); base_v = 20 * np.log10(np.clip(b_mag, 1e-12, None))
                        elif "Phase" in choice:
                            curr_v = np.angle(curr[param_key][mask], deg=True); base_v = np.angle(base_data[param_key][mask_b], deg=True)
                        else:
                            curr_v, base_v = c_mag, b_mag
                        raw_curr, raw_base = float(np.mean(curr_v)), float(np.mean(base_v))
                        c_val = raw_curr / raw_base if raw_base != 0 else float('nan')
                        delta_val, raw_val = raw_curr - raw_base, raw_curr
                rows.append((idx + 1, f, c_val, delta_val, raw_val, z_freq))
        return rows

    def export_dgrv_both(self):
        """zExport_DGRV.txt (zones) and zExport_DGRV_M.txt (markers) - the C# 'middle click' export."""
        try:
            written = []
            for use_markers, stem in ((False, "zExport_DGRV"), (True, "zExport_DGRV_M")):
                rows = self._trend_table_rows(use_markers)
                if not rows:
                    continue
                lines = [["N", "File Name", "C(Mag)", "Δ(Mag),dB", "Mag, dB", "Z. Freq,GHz"]]
                for (n, f, c, d, m, z) in rows:
                    lines.append([n, os.path.splitext(f)[0], self._fmt_export_num(c),
                                  self._fmt_export_num(d), self._fmt_export_num(m), z])
                path = self._export_stamp_path(stem)
                write_tsv(path, lines)
                written.append(os.path.abspath(path))
            if not written:
                messagebox.showwarning("No Data", "No table data - load files and set zones/markers first.")
                return
            messagebox.showinfo("Export Complete", "Tables exported to:\n" + "\n".join(written))
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

    def save_pic(self):
        """Port of 'Save Pic': PNG of the current tab, default name yyMMdd_HHmmss_.PNG in the Pics folder."""
        try:
            tab = self.root.nametowidget(self.notebook.select())
            os.makedirs(PICS_DIR, exist_ok=True)
            default = datetime.datetime.now().strftime("%y%m%d_%H%M%S") + "_.PNG"
            path = filedialog.asksaveasfilename(title="Save Pic", initialdir=PICS_DIR, initialfile=default,
                                                defaultextension=".png",
                                                filetypes=[("Image (*.png)", "*.png"), ("All Files", "*.*")])
            if not path:
                return
            self.root.update_idletasks()
            self.root.update()
            try:
                from PIL import ImageGrab
                x, y = tab.winfo_rootx(), tab.winfo_rooty()
                ImageGrab.grab(bbox=(x, y, x + tab.winfo_width(), y + tab.winfo_height())).save(path, "PNG")
            except Exception:
                fig = {self.graph_tab: self.fig, self.absorption_tab: self.absorption_fig,
                       self.trend_tab: self.trend_fig}.get(tab)
                if fig is None:
                    raise
                fig.savefig(path, facecolor=fig.get_facecolor(), dpi=150)
            messagebox.showinfo("Pic Saved", f"Saved to:\n{os.path.abspath(path)}")
        except Exception as e:
            messagebox.showerror("Save Pic Failed", str(e))

    def save_chart_png(self):
        try:
            ts = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
            path = os.path.join(self.exports_dir, f"chart_{ts}.png")
            self.fig.savefig(path, facecolor=self.fig.get_facecolor(), dpi=150)
            messagebox.showinfo("Chart Saved", f"Chart image saved to:\n{os.path.abspath(path)}")
        except Exception as e:
            messagebox.showerror("Save Failed", str(e))

    def export_data(self, full=False):
        if not self.base_file_name:
            messagebox.showwarning("No Data", "No baseline CSV file is loaded.")
            return
        try:
            ts = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
            choice = self.param_var.get()
            marker_freqs = self.get_marker_freqs()

            if full:
                path = os.path.join(self.exports_dir, f"zExport_{ts}.txt")
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(f"Full Data Export — {choice}\n")
                    fh.write(f"Generated: {datetime.datetime.now().isoformat(timespec='seconds')}\n")
                    fh.write(f"Baseline: {self.base_file_name}\n\n")
                    param_key = 'S11_complex' if "S11" in choice else 'S21_complex'
                    for f in self._get_filenames():
                        curr = self.file_data_cache.get(f)
                        if not curr or param_key not in curr: continue
                        fh.write(f"---- {f} ----\n")
                        fh.write("Freq_GHz\tValue\n")
                        base_data = self.file_data_cache[self.base_file_name]
                        freqs = curr['Freq_GHz']
                        curr_mag = np.abs(curr[param_key])
                        base_mag = np.abs(base_data[param_key])
                        if "Delta Log Mag" in choice:
                            processed = (20*np.log10(np.where(curr_mag==0,1e-12,curr_mag))
                                         - 20*np.log10(np.where(base_mag==0,1e-12,base_mag)))
                        elif "Phase Trace" in choice:
                            processed = (np.angle(curr[param_key], deg=True)
                                         - np.angle(base_data[param_key], deg=True) + 180) % 360 - 180
                        else:
                            processed = curr_mag / np.where(base_mag==0,1e-12,base_mag)
                        for fr, val in zip(freqs, processed):
                            fh.write(f"{fr:.4f}\t{val:.4f}\n")
                        fh.write("\n")
            else:
                path = os.path.join(self.exports_dir, f"zExportR_{ts}.txt")
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(f"Summary (Resume) Export — {choice}\n")
                    fh.write(f"Generated: {datetime.datetime.now().isoformat(timespec='seconds')}\n")
                    fh.write(f"Baseline: {self.base_file_name}\n")
                    fh.write("Markers: " + ", ".join(
                        f"M{i+1}={mf:.2f}GHz" if mf is not None else f"M{i+1}=N/A"
                        for i, mf in enumerate(marker_freqs)) + "\n\n")

                    if self.last_best_zone_info:
                        bz = self.last_best_zone_info
                        r = bz["range"]
                        fh.write(f"Best Absorption / Best Performance: Zone {bz['zone']} "
                                 f"({r[0]:.2f}-{r[1]:.2f} GHz) = {bz['value']:.4f} (File: {bz['file']})\n\n")

                    fh.write("== Zone Report ==\n")
                    for row in self.last_summary_rows:
                        fh.write("\t".join(str(x) for x in row) + "\n")

                    fh.write("\n== Key Parameters at Markers ==\n")
                    for row in self.last_marker_rows:
                        fh.write("\t".join(str(x) for x in row) + "\n")

            messagebox.showinfo("Export Complete", f"Data exported to:\n{os.path.abspath(path)}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

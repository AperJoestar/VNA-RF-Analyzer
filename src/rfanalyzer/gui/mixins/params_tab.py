"""Key Parameters (Markers) tab."""
import os
import tkinter as tk
from tkinter import ttk

import numpy as np

from rfanalyzer import theme as T
from rfanalyzer.core.dsp import compute_swr
from rfanalyzer.core.tables import cs_freq, cs_num


class ParamsTabMixin:
    """Key Parameters (Markers) tab.

    Mixed into :class:`rfanalyzer.gui.main_window.RFAnalyzerApp`; relies on the state set up in its ``__init__``.
    """

    def setup_params_tab(self):
        p_canvas = tk.Canvas(self.params_tab, highlightthickness=0, bg=T.BG)
        p_scroll = ttk.Scrollbar(self.params_tab, orient="vertical", command=p_canvas.yview)
        self.params_inner = ttk.Frame(p_canvas)
        self.params_inner.bind("<Configure>", lambda e: p_canvas.configure(scrollregion=p_canvas.bbox("all")))
        p_canvas.create_window((0, 0), window=self.params_inner, anchor="nw")
        p_hscroll = ttk.Scrollbar(self.params_tab, orient="horizontal", command=p_canvas.xview)
        p_canvas.configure(yscrollcommand=p_scroll.set, xscrollcommand=p_hscroll.set)
        p_hscroll.pack(side=tk.BOTTOM, fill=tk.X)
        p_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        p_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _compute_cs_params(self, marker_freqs):
        names = self._get_filenames()
        base = self.base_file_name
        recs = []
        with np.errstate(divide='ignore', invalid='ignore'):
            for idx, f in enumerate(names):
                d = self.file_data_cache.get(f)
                if not d or 'S11_complex' not in d or 'S21_complex' not in d:
                    continue
                freqs = np.asarray(d['Freq_GHz'], float)
                n = len(freqs)
                st = float(freqs[0]); stsp = (float(freqs[-1]) - st) / (n - 1) if n > 1 else 0.0
                mag = 20.0 * np.log10(np.abs(d['S21_complex']))
                swr = compute_swr(d['S11_complex'])
                mi = []
                for mf in marker_freqs:
                    mi.append(None if mf is None else int(np.argmin(np.abs(freqs - mf))))
                recs.append(dict(idx=idx, name=os.path.splitext(f)[0], mag=mag, swr=swr, n=n,
                                 st=st, stsp=stsp, mi=mi, is_base=(f == base)))
            base_rec = next((r for r in recs if r['is_base']), None)
            avg_mag0 = float(np.mean(base_rec['mag'])) if base_rec else float('nan')
            avg_swr0 = float(np.mean(base_rec['swr'])) if base_rec else float('nan')
            for r in recs:
                n = r['n']
                lo, hi = 10, max(10, n - 10)             # C#: points 10 .. lineCount-10
                if hi <= lo: lo, hi = 0, n
                m_seg, s_seg = r['mag'][lo:hi], r['swr'][lo:hi]
                i_mn, i_mx = int(np.argmin(m_seg)) + lo, int(np.argmax(m_seg)) + lo
                j_mn, j_mx = int(np.argmin(s_seg)) + lo, int(np.argmax(s_seg)) + lo
                r['minMag'] = (round(float(r['mag'][i_mn]), 4), r['st'] + i_mn * r['stsp'])
                r['maxMag'] = (round(float(r['mag'][i_mx]), 4), r['st'] + i_mx * r['stsp'])
                r['minSWR'] = (round(float(r['swr'][j_mn]), 4), r['st'] + j_mn * r['stsp'])
                r['maxSWR'] = (round(float(r['swr'][j_mx]), 4), r['st'] + j_mx * r['stsp'])
                r['avgCMag'] = round(float(np.mean(r['mag'])) / avg_mag0, 4) if avg_mag0 else float('nan')
                r['avgCSWR'] = round(float(np.mean(r['swr'])) / avg_swr0, 4) if avg_swr0 else float('nan')
        self._cs_params = dict(recs=recs, avg_mag0=avg_mag0, avg_swr0=avg_swr0, n_files=len(names))

    def _cs_params_toggle_page(self, _evt=None):
        data = getattr(self, '_cs_params', None)
        if not data: return
        nxt = getattr(self, 'cs_params_page', 0) + 10
        self.cs_params_page = nxt if nxt < data['n_files'] else 0
        self._render_cs_params()

    def _render_cs_params(self):
        for w in self.params_inner.winfo_children(): w.destroy()
        data = getattr(self, '_cs_params', None)
        if not data or not data['recs']:
            return
        recs = data['recs']; num = cs_num
        iSt = getattr(self, 'cs_params_page', 0)
        if iSt >= data['n_files']: iSt = self.cs_params_page = 0

        # ---- column texts (same lines / order as C# Label1, Label2, Label7, Label8) ----
        def left_block(r, second):
            L = [f"Data{r['idx']} - {r['name']}"]
            for k in range(3):
                mi = r['mi'][k] if k < len(r['mi']) else None
                L.append(f"M{k+1}-mag, dB = {num(r['mag'][mi]) if mi is not None else 'N/A'}")
            for k in range(3):
                mi = r['mi'][k] if k < len(r['mi']) else None
                L.append(f"M{k+1}-swr, V = {num(r['swr'][mi]) if mi is not None else 'N/A'}")
            if second or r['idx'] > 0: L.append("")
            if not second and r['idx'] == 0: L.append("============================")
            return L

        def right_block(r, second):
            L = [f"Data{r['idx']} - {r['name']}"]
            L.append(f"minMag, dB = {num(r['minMag'][0])} / {cs_freq(r['minMag'][1])} GHz")
            L.append(f"maxMag, dB = {num(r['maxMag'][0])} / {cs_freq(r['maxMag'][1])} GHz")
            L.append(f"avgC(Mag), dB = {num(r['avgCMag'])}")
            L.append(f"minSWR, V = {num(r['minSWR'][0])} / {cs_freq(r['minSWR'][1])} GHz")
            L.append(f"maxSWR, V = {num(r['maxSWR'][0])} / {cs_freq(r['maxSWR'][1])} GHz")
            L.append(f"avgC(SWR), dB = {num(r['avgCSWR'])}")
            if second or r['idx'] > 0: L.append("")
            if not second and r['idx'] == 0: L.append("============================")
            return L

        col1, col2, col3, col4 = [], [], [], []
        for r in recs:
            if iSt <= r['idx'] <= iSt + 4:
                col1 += left_block(r, False); col3 += right_block(r, False)
            elif iSt + 5 <= r['idx'] <= iSt + 9:
                col2 += left_block(r, True);  col4 += right_block(r, True)

        # ---- Resume (best over all files): C# Label34 / Label36 ----
        hdr = "=============  Resume  Best Absorption Performance =================\n"
        res_l = [hdr]
        for k in range(3):                                   # lowest dB at marker (ties -> later file)
            best = None
            for r in recs:
                mi = r['mi'][k] if k < len(r['mi']) else None
                if mi is None: continue
                v = float(r['mag'][mi])
                if best is None or v <= best[0]: best = (v, r['name'])
            if best: res_l.append(f"M{k+1}-mag, db = {num(best[0])}     Data - {best[1]}")
        for k in range(3):                                   # highest SWR at marker
            best = None
            for r in recs:
                mi = r['mi'][k] if k < len(r['mi']) else None
                if mi is None: continue
                v = float(r['swr'][mi])
                if best is None or v >= best[0]: best = (v, r['name'])
            if best: res_l.append(f"M{k+1}-swr, V = {num(best[0])}     Data - {best[1]}")

        def pick(key, idx_val, lowest):
            best = None
            for r in recs:
                v = r[key] if idx_val is None else r[key][idx_val]
                if v != v: continue
                if best is None or (v <= best[0] if lowest else v >= best[0]): best = (v, r)
            return best
        res_r = [hdr]
        for key, lab, lowest in (("minMag", "minMag, dB", True), ("maxMag", "maxMag, dB", False)):
            b = pick(key, 0, lowest)
            if b: res_r.append(f"{lab} = {num(b[0])} / {cs_freq(b[1][key][1])}GHz     Data - {b[1]['name']}")
        b = pick("avgCMag", None, False)
        if b: res_r.append(f"MAX avgC(|Mag|) = {num(b[0])} ({num(b[0]*data['avg_mag0'] - data['avg_mag0'])} dB)     Data - {b[1]['name']}\n")
        for key, lab, lowest in (("minSWR", "minSWR, dB", True), ("maxSWR", "maxSWR, dB", False)):
            b = pick(key, 0, lowest)
            if b: res_r.append(f"{lab} = {num(b[0])} / {cs_freq(b[1][key][1])}GHz     Data - {b[1]['name']}")
        b = pick("avgCSWR", None, False)
        if b: res_r.append(f"MAX avgC(|SWR|) = {num(b[0])} ({num(b[0]*data['avg_swr0'] - data['avg_swr0'])} V)     Data - {b[1]['name']}")

        # ---- layout: same arrangement as the C# tab (x = 6 / 337 | 807 / 1138, headings on top, Resume below) ----
        font = ("Microsoft Sans Serif", 9)
        bold = ("Microsoft Sans Serif", 10, "bold")
        f = self.params_inner
        for c, w in enumerate((331, 331, 139, 331, 331)):
            f.grid_columnconfigure(c, minsize=w)

        h1 = tk.Label(f, text="<> Key Features of dB Mag and SWR  by marker", font=bold, fg=T.ACCENT, bg=T.BG, cursor="hand2")
        h1.grid(row=0, column=0, columnspan=2, sticky="w", padx=(65, 0), pady=(3, 4))
        h1.bind("<Button-1>", self._cs_params_toggle_page)
        tk.Label(f, text="Comparative Data of Key Parameters", font=bold, fg=T.FG, bg=T.BG).grid(
            row=0, column=3, columnspan=2, sticky="w", padx=(75, 0), pady=(3, 4))

        for c, lines in ((0, col1), (1, col2), (3, col3), (4, col4)):
            tk.Label(f, text="\n".join(lines), font=font, fg=T.FG, bg=T.BG, justify="left", anchor="nw").grid(
                row=1, column=c, sticky="nw", padx=(6, 0))

        tk.Label(f, text="\n".join(res_l), font=font, fg=T.FG, bg=T.BG, justify="left", anchor="nw").grid(
            row=2, column=0, columnspan=2, sticky="nw", padx=(6, 0), pady=(14, 8))
        tk.Label(f, text="\n".join(res_r), font=font, fg=T.FG, bg=T.BG, justify="left", anchor="nw").grid(
            row=2, column=3, columnspan=2, sticky="nw", padx=(6, 0), pady=(14, 8))

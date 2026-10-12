"""Mag_Type/Zones tab: zone / marker trends, Antenna Analyser mode and the result table."""
import os
import tkinter as tk
from tkinter import messagebox, ttk

import numpy as np

from rfanalyzer import theme as T
from rfanalyzer.core.dsp import cardinal_curve, cardinal_spline
from rfanalyzer.core.tables import ANTENNA_TABLE_COLS, find_best_table_rows, fmt_trend_row, TREND_TABLE_COLS
from rfanalyzer.gui.plotting import apply_min_max_axis_limits


class TrendTabMixin:
    """Mag_Type/Zones tab: zone / marker trends, Antenna Analyser mode and the result table.

    Mixed into :class:`rfanalyzer.gui.main_window.RFAnalyzerApp`; relies on the state set up in its ``__init__``.
    """

    def setup_trend_tab(self):
        toolbar = ttk.Frame(self.trend_tab, padding=(10, 8))
        toolbar.pack(fill=tk.X, side=tk.TOP)
        self.trend_mode_label = ttk.Label(toolbar, text="Mode: Zone Averages (C(avgMag) per zone)", font=("Arial", 9, "bold"))
        self.trend_mode_label.pack(side=tk.LEFT, padx=(0, 14))
        
        ttk.Button(toolbar, text="🎯 At Markers", command=self.trend_use_markers).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔄 Reset (Zones)", command=self.trend_use_zones).pack(side=tk.LEFT, padx=2)
        ant_btn = ttk.Button(toolbar, text="📡 * Antenna Analyser", command=lambda: self.trend_use_antenna(0))
        ant_btn.pack(side=tk.LEFT, padx=2)
        # Right click => "in half" mode (Button-2 is the right button on macOS)
        ant_btn.bind("<Button-3>", lambda e: self.trend_use_antenna(1))
        ant_btn.bind("<Button-2>", lambda e: self.trend_use_antenna(1))
        
        self.trend_val_btn = ttk.Button(toolbar, text="🔄 View: Delta(Mag)", command=self.trend_toggle_val_mode)
        self.trend_val_btn.pack(side=tk.LEFT, padx=14)
        
        ttk.Button(toolbar, text="📋 Show 'Table at Zones'", command=self.trend_toggle_table).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="💾 Export Table", command=self.export_trend_table).pack(side=tk.RIGHT, padx=2)

        self.trend_chart_frame = ttk.Frame(self.trend_tab)
        self.trend_chart_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
        self.trend_table_frame = ttk.Frame(self.trend_tab)

    def trend_use_antenna(self, pair_mode=0):
        self.trend_mode = "antenna"
        self.antenna_pair_mode = pair_mode
        name = "Alternation" if pair_mode == 0 else "In half"
        self.trend_mode_label.config(text=f"Mode: Antenna Analyser - {name}  (left click: Alternation, right click: In half)")
        if len(self.file_paths) % 2 != 0:
            messagebox.showwarning("Antenna Analyser", "Odd number of files - the last file has no pair and is ignored.")
        self.update_analysis()

    def trend_toggle_val_mode(self):
        if self.trend_val_mode == "ratio":
            self.trend_val_mode = "delta"
            self.trend_val_btn.config(text="🔄 View: C(Mag)")
        else:
            self.trend_val_mode = "ratio"
            self.trend_val_btn.config(text="🔄 View: Delta(Mag)")
        self.update_analysis()

    def update_trend_tab(self, param_key, zones, marker_freqs):
        self.trend_ax.clear()
        self.trend_ax.set_facecolor(T.PLOT_BG)
        self.trend_ax.tick_params(colors=T.MUTED, labelsize=8)
        self.trend_ax.grid(True, linestyle=':', alpha=0.3, color=T.BORDER)

        base_data = self.file_data_cache.get(self.base_file_name) if self.base_file_name else None
        if not base_data or param_key not in base_data or not self.file_paths:
            self.trend_canvas.draw()
            return

        base_mag = np.abs(base_data[param_key])
        base_freqs = base_data['Freq_GHz']
        choice = self.param_var.get()
        
        # Always plot all loaded files for the trend tab
        x_labels = self._get_filenames()

        if getattr(self, 'trend_mode', 'zone') == "antenna":
            self._draw_antenna_chart(param_key, zones, marker_freqs, x_labels)
            return

        if getattr(self, 'trend_mode', 'zone') == "zone":
            lines = zones
            line_labels = [f"{zb[0]:.1f}-{zb[1]:.1f} GHz" for zb in zones]
        else:
            lines = marker_freqs
            line_labels = [f"M{i+1} ({mf:.2f} GHz)" if mf is not None else f"M{i+1} (N/A)" for i, mf in enumerate(marker_freqs)]

        matrix = []
        table_data_store = []

        for li, item in enumerate(lines):
            y_vals = []
            for idx, f in enumerate(x_labels):
                curr = self.file_data_cache.get(f)
                if not curr or param_key not in curr:
                    y_vals.append(None); continue
                
                freqs = curr['Freq_GHz']
                curr_mag = np.abs(curr[param_key])
                
                c_val = delta_val = raw_val = float('nan')
                z_freq = ""
                
                if getattr(self, 'trend_mode', 'zone') == "zone":
                    zb = item
                    z_freq = f"{li+1}. {int(zb[0])}_{int(zb[1])}"
                    mask = (freqs >= zb[0]) & (freqs <= zb[1])
                    mask_b = (base_freqs >= zb[0]) & (base_freqs <= zb[1])
                    
                    if mask.any() and mask_b.any():
                        c_mag = curr_mag[mask]
                        b_mag = base_mag[mask_b]
                        
                        if "Delta Log Mag" in choice:
                            curr_v = 20 * np.log10(np.clip(c_mag, 1e-12, None))
                            base_v = 20 * np.log10(np.clip(b_mag, 1e-12, None))
                        elif "Phase" in choice:
                            curr_v = np.angle(curr[param_key][mask], deg=True)
                            base_v = np.angle(base_data[param_key][mask_b], deg=True)
                        else:
                            curr_v = c_mag
                            base_v = b_mag
                        
                        raw_curr = float(np.mean(curr_v))
                        raw_base = float(np.mean(base_v))
                        
                        c_val = raw_curr / raw_base if raw_base != 0 else float('nan')
                        delta_val = raw_curr - raw_base
                        raw_val = raw_curr
                else:
                    mf = item
                    z_freq = f"M{li+1}: {mf:.2f}" if mf else "N/A"
                    if mf is not None and freqs.min() <= mf <= freqs.max():
                        cv = float(np.interp(mf, freqs, curr_mag))
                        bv = float(np.interp(mf, base_freqs, base_mag))
                        
                        if "Delta Log Mag" in choice:
                            curr_v = 20 * np.log10(np.clip(cv, 1e-12, None))
                            base_v = 20 * np.log10(np.clip(bv, 1e-12, None))
                        elif "Phase" in choice:
                            cv_complex = np.interp(mf, freqs, curr[param_key])
                            bv_complex = np.interp(mf, base_freqs, base_data[param_key])
                            curr_v = np.angle(cv_complex, deg=True)
                            base_v = np.angle(bv_complex, deg=True)
                        else:
                            curr_v, base_v = cv, bv
                            
                        c_val = curr_v / base_v if base_v != 0 else float('nan')
                        delta_val = curr_v - base_v
                        raw_val = curr_v

                table_data_store.append((idx+1, f, c_val, delta_val, raw_val, z_freq))
                
                if getattr(self, 'trend_val_mode', 'ratio') == "delta":
                    y_vals.append(delta_val)
                elif getattr(self, 'trend_val_mode', 'ratio') == "raw":
                    y_vals.append(raw_val)
                else:
                    y_vals.append(c_val)
                
            matrix.append((line_labels[li], y_vals))

        xs = list(range(len(x_labels)))
        all_trend_y = []

        if getattr(self, 'trend_val_mode', 'ratio') == "raw" and len(xs) > 1:
            chunk_size = len(xs) / 6.0
            for i in range(6):
                start_x = i * chunk_size
                end_x = (i + 1) * chunk_size
                color = T.ZONE_COLS[i % len(T.ZONE_COLS)]
                self.trend_ax.axvspan(start_x - 0.5, end_x - 0.5, color=color, alpha=0.1)

        # Smooth cardinal-spline curves (like C# DrawCurve): no straight segments, no dots
        for li, (label, y_vals) in enumerate(matrix):
            color = T.ZONE_COLS[li % len(T.ZONE_COLS)]
            valid_idx = [i for i, v in enumerate(y_vals) if v is not None and not np.isnan(v)]
            if len(valid_idx) > 0:
                x_valid = np.array([xs[i] for i in valid_idx], float)
                y_valid = np.array([y_vals[i] for i in valid_idx], float)
                x_dense, y_dense = cardinal_curve(x_valid, y_valid)
                self.trend_ax.plot(x_dense, y_dense, label=label, color=color, linewidth=2.0, solid_capstyle='round')
                all_trend_y.extend(y_dense)

        self.trend_ax.set_xticks(xs)
        self.trend_ax.set_xticklabels(x_labels, rotation=30, ha='right', fontsize=7, color=T.MUTED)
        
        mode_txt = "Zone Averages" if getattr(self, 'trend_mode', 'zone') == "zone" else "At Markers"
        active_val_mode = getattr(self, 'trend_val_mode', 'ratio')
        
        if active_val_mode == "raw":
            self.trend_ax.set_ylabel("V, dB", color=T.MUTED, fontsize=8)
            self.trend_ax.set_title("Antenna Analyser Mags mode - Alternation", color=T.ACCENT, fontsize=11, fontweight="bold")
        elif active_val_mode == "delta":
            self.trend_ax.set_ylabel("V, dB", color=T.MUTED, fontsize=8)
            self.trend_ax.set_title(f"Delta(avgMag) at Data(FileName) — {mode_txt}", color=T.ACCENT, fontsize=11, fontweight="bold")
        else:
            self.trend_ax.set_ylabel("C(avg) = Current / Baseline", color=T.MUTED, fontsize=8)
            self.trend_ax.set_title(f"C(avgMag) at Data(FileName) — {mode_txt}", color=T.FG, fontsize=10)
        
        if self.trend_ax.get_legend_handles_labels()[0]:
            self.trend_ax.legend(fontsize=7, facecolor=T.PANEL, edgecolor=T.BORDER, labelcolor=T.FG, loc='best')

        apply_min_max_axis_limits(self.trend_ax, xs, all_trend_y, pad_y=0.08)

        try:
            self.trend_fig.tight_layout()
        except Exception:
            pass
        self.trend_canvas.draw()

        self.last_trend_table_data = table_data_store
        self.last_trend_matrix = matrix
        self.last_trend_x_labels = x_labels
        if getattr(self, 'trend_show_table', False):
            self.rebuild_trend_table()

    def _antenna_avg_db(self, curr, param_key, item, use_markers):
        """Mag in dB for one file: mean over a zone, or the point nearest a marker (as in the C# code)."""
        if not curr or param_key not in curr or item is None:
            return float('nan')
        freqs = np.asarray(curr['Freq_GHz'], float)
        db = 20 * np.log10(np.clip(np.abs(curr[param_key]), 1e-12, None))
        if use_markers:
            if not (freqs.min() <= item <= freqs.max()):
                return float('nan')
            return float(db[int(np.argmin(np.abs(freqs - item)))])
        mask = (freqs >= item[0]) & (freqs <= item[1])
        return float(np.mean(db[mask])) if mask.any() else float('nan')

    def _draw_antenna_chart(self, param_key, zones, marker_freqs, x_labels):
        ax = self.trend_ax
        use_markers = getattr(self, 'trend_base_mode', 'zone') == "marker"
        pair_mode = getattr(self, 'antenna_pair_mode', 0)
        items = list(marker_freqs) if use_markers else list(zones)[:6]
        n_files = len(x_labels)
        n_pairs = n_files // 2
        self.last_antenna_rows = []
        self.last_antenna_export = []
        if n_pairs == 0 or not items:
            self.trend_canvas.draw()
            return

        # File pairs: Alternation = (2p, 2p+1); In half = (p, p + N/2)
        if pair_mode == 0:
            pairs = [(2 * p, 2 * p + 1) for p in range(n_pairs)]
        else:
            pairs = [(p, p + n_files // 2) for p in range(n_pairs)]
        stems = [os.path.splitext(n)[0] for n in x_labels]
        pair_labels = [f"{stems[a][-8:]} <=> {stems[b][-8:]}" for a, b in pairs]

        block_w = n_pairs + 1.25          # points per block + the small gap seen in the C# chart
        n_blocks = len(items)
        xs, A, B, D = [], [], [], []
        for z, item in enumerate(items):
            vals = [self._antenna_avg_db(self.file_data_cache.get(f), param_key, item, use_markers)
                    for f in x_labels]
            if use_markers:
                zone_txt = f"M{z+1}. {item:.2f}" if item is not None else f"M{z+1}. N/A"
            else:
                zone_txt = f"{item[0]:.6g}_{item[1]:.6g}"
            zone_cs = (f"M{z+1}. {item:g}" if item is not None else f"M{z+1}. N/A") if use_markers \
                else f"{item[0]:g}_{item[1]:g}"
            for p, (a, b) in enumerate(pairs):
                self.last_antenna_export.append((stems[a], zone_cs))
                va, vb = vals[a], vals[b]
                xs.append(z * block_w + p)
                A.append(va); B.append(vb); D.append(vb - va)
                self.last_antenna_rows.append((len(self.last_antenna_rows) + 1, pair_labels[p], va, vb, vb - va, zone_txt))
        xs, A, B, D = (np.array(v, float) for v in (xs, A, B, D))

        # Background blocks + block captions
        for z, item in enumerate(items):
            ax.axvspan(z * block_w - 0.5, (z + 1) * block_w - 0.5,
                       color=T.ANTENNA_BLOCK_COLS[z % len(T.ANTENNA_BLOCK_COLS)], alpha=0.9, zorder=0, linewidth=0)

        # Y range = min/max over all three series, 11 grid lines (as in the C# chart)
        finite = np.concatenate([v[np.isfinite(v)] for v in (A, B, D)])
        if finite.size == 0:
            self.trend_canvas.draw()
            return
        ymin, ymax = float(finite.min()), float(finite.max())
        if ymin == ymax:
            ymin -= 1.0; ymax += 1.0
        ticks = np.linspace(ymin, ymax, 11)
        ax.set_ylim(ymin, ymax)
        ax.set_yticks(ticks)
        ax.set_yticklabels([f"{t:.2f}" for t in ticks], fontsize=8, color=T.MUTED)
        ax.grid(True, axis='y', linestyle='-', alpha=0.35, color=T.GRID_STRONG)

        # One tick + vertical grid line per file pair, labelled "<file A> <=> <file B>"
        ax.set_xticks(xs)
        ax.set_xticklabels(pair_labels * n_blocks, rotation=90, fontsize=6, color=T.MUTED)
        ax.grid(True, axis='x', linestyle='-', alpha=0.35, color=T.GRID_STRONG)
        ax.set_xlim(-0.5, n_blocks * block_w - 0.5)

        # Three smooth curves running continuously across all blocks
        names = ["Mag", "Mag1", "Mag1-Mag"]
        for series, col, nm in zip((A, B, D), T.ANTENNA_LINE_COLS, names):
            ok = np.isfinite(series)
            if ok.sum() == 0:
                continue
            cx, cy = cardinal_spline(xs[ok], series[ok])
            ax.plot(cx, cy, color=col, linewidth=1.8, label=nm, zorder=3)

        # Zone / marker caption at the top of each block
        for z, item in enumerate(items):
            if use_markers:
                cap = f"M{z+1} - {item:.2f} GHz" if item is not None else f"M{z+1} - N/A"
            else:
                cap = f"{item[0]:.6g} - {item[1]:.6g} GHz"
            ax.text(z * block_w + (n_pairs - 1) / 2.0, ymax, cap, ha='center', va='bottom',
                    fontsize=7, color=T.FG, clip_on=False)

        name = "Alternation" if pair_mode == 0 else "In half"
        head = "Antenna Analyser Mags Marker" if use_markers else "Antenna Analyser Mags"
        ax.set_title(f"{head}\nmode - {name}", color=T.ACCENT, fontsize=11, fontweight="bold", pad=22)
        ax.set_ylabel("V, dB", color=T.MUTED, fontsize=8)
        ax.set_xlabel("File Name", color=T.MUTED, fontsize=8)
        ax.legend(fontsize=7, facecolor=T.PANEL, edgecolor=T.BORDER, labelcolor=T.FG,
                  loc='upper left', bbox_to_anchor=(1.005, 1.0))

        try:
            self.trend_fig.tight_layout()
        except Exception:
            pass
        self.trend_canvas.draw()
        if getattr(self, 'trend_show_table', False):
            self.rebuild_trend_table()

    def _rebuild_antenna_table(self):
        rows = getattr(self, 'last_antenna_rows', [])
        if not rows:
            return
        cols = ANTENNA_TABLE_COLS
        tree = ttk.Treeview(self.trend_table_frame, columns=cols, show="headings", height=8)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=220 if c == "File Name" else (40 if c == "N" else 110),
                        anchor=tk.W if c == "File Name" else tk.CENTER)
        tree.tag_configure('odd', background=T.PANEL)
        tree.tag_configure('even', background=T.ROW_EVEN)
        fmt = lambda v: "N/A" if not np.isfinite(v) else f"{v:.6f}"
        for i, (n, label, a, b, d, zone) in enumerate(rows):
            tree.insert("", tk.END, values=[n, label, fmt(a), fmt(b), fmt(d), zone],
                        tags=('even' if i % 2 == 0 else 'odd',))
        vsb = ttk.Scrollbar(self.trend_table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def trend_use_markers(self):
        self.trend_mode = "marker"
        self.trend_base_mode = "marker"
        self.trend_mode_label.config(text="Mode: At Markers (M1/M2/M3)")
        self.update_analysis()

    def trend_use_zones(self):
        self.trend_mode = "zone"
        self.trend_base_mode = "zone"
        self.trend_mode_label.config(text="Mode: Zone Averages (C(avgMag) per zone)")
        self.update_analysis()

    def trend_toggle_table(self):
        self.trend_show_table = not self.trend_show_table
        if self.trend_show_table:
            self.trend_table_frame.pack(fill=tk.BOTH, expand=False, pady=(6, 0))
            self.rebuild_trend_table()
        else:
            self.trend_table_frame.pack_forget()

    def rebuild_trend_table(self):
        """Rebuilds table matching reference image 'Table at Zones' columns and precision."""
        for w in self.trend_table_frame.winfo_children(): w.destroy()
        if getattr(self, 'trend_mode', 'zone') == "antenna":
            self._rebuild_antenna_table()
            return
        if not hasattr(self, 'last_trend_table_data') or not self.last_trend_table_data: return
        
        cols = TREND_TABLE_COLS
        best_rows = find_best_table_rows(self.last_trend_table_data)

        ttk.Label(self.trend_table_frame,
                  text="Green = best row per zone/marker (lowest Δ(Mag),dB)    Gray = baseline",
                  font=("Arial", 8), foreground=T.MUTED).pack(side=tk.BOTTOM, anchor=tk.W)

        tree = ttk.Treeview(self.trend_table_frame, columns=cols, show="headings", height=8)

        tree.heading("N", text="N")
        tree.column("N", width=40, anchor=tk.CENTER)
        tree.heading("File Name", text="File Name")
        tree.column("File Name", width=220, anchor=tk.W)

        for c in cols[2:]:
            tree.heading(c, text=c)
            tree.column(c, width=120, anchor=tk.CENTER)

        tree.tag_configure('odd', background=T.PANEL)
        tree.tag_configure('even', background=T.ROW_EVEN)
        tree.tag_configure('baseline', background=T.BASE_BG)
        tree.tag_configure('best', background=T.BEST_BG, foreground=T.BEST_FG)

        for i, row_data in enumerate(self.last_trend_table_data):
            if i in best_rows:
                tag = 'best'
            elif row_data[1] == getattr(self, 'base_file_name', None):
                tag = 'baseline'
            else:
                tag = 'even' if i % 2 == 0 else 'odd'
            tree.insert("", tk.END, values=fmt_trend_row(row_data), tags=(tag,))

        vsb = ttk.Scrollbar(self.trend_table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

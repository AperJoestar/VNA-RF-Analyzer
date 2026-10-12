"""Mag & SWR Zones (absorption analysis) tab."""
import tkinter as tk
from tkinter import ttk

import numpy as np

from rfanalyzer import theme as T
from rfanalyzer.core.dsp import apply_smoothing, compute_swr
from rfanalyzer.gui.plotting import apply_min_max_axis_limits


class AbsorptionTabMixin:
    """Mag & SWR Zones (absorption analysis) tab.

    Mixed into :class:`rfanalyzer.gui.main_window.RFAnalyzerApp`; relies on the state set up in its ``__init__``.
    """

    def setup_absorption_tab(self):
        self.absorption_summary_frame = ttk.Frame(self.absorption_tab, padding=(10, 8))
        self.absorption_summary_frame.pack(fill=tk.X, side=tk.TOP)

        nav_bar = ttk.Frame(self.absorption_tab, padding=(10, 2))
        nav_bar.pack(fill=tk.X, side=tk.TOP)
        ttk.Button(nav_bar, text="<< Prev Zone", command=self.absorption_prev_zone).pack(side=tk.LEFT, padx=2)
        self.absorption_zone_label = ttk.Label(nav_bar, text="Full Sweep View", foreground=T.MUTED, font=("Arial", 9, "bold"))
        self.absorption_zone_label.pack(side=tk.LEFT, padx=10)
        ttk.Button(nav_bar, text="Next Zone >>", command=self.absorption_next_zone).pack(side=tk.LEFT, padx=2)
        ttk.Button(nav_bar, text="🔄 R (Reset / Full View)", command=self.absorption_reset_zone).pack(side=tk.LEFT, padx=10)

        self.toggle_diagram_btn = ttk.Button(nav_bar, text="🔄 View: Delta(Mag/SWR)", command=self.toggle_absorption_diagram)
        self.toggle_diagram_btn.pack(side=tk.RIGHT, padx=10)

        self.absorption_charts_frame = ttk.Frame(self.absorption_tab)
        self.absorption_charts_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

    def toggle_absorption_diagram(self):
        if self.absorption_view_mode == "mag":
            self.absorption_view_mode = "delta"
            self.toggle_diagram_btn.config(text="🔄 View: C(Mag/SWR)")
        else:
            self.absorption_view_mode = "mag"
            self.toggle_diagram_btn.config(text="🔄 View: Delta(Mag/SWR)")

        zones = self.read_zones()
        if zones:
            self.update_absorption_tab(zones)

    def update_absorption_tab(self, zones):
        for w in self.absorption_summary_frame.winfo_children(): w.destroy()

        if not self.base_file_name or not zones or self.base_file_name not in self.file_data_cache:
            ttk.Label(self.absorption_summary_frame, text="No baseline / zone data available.", foreground=T.MUTED).pack(anchor=tk.W)
            self.absorption_ax_left.clear(); self.absorption_ax_swr.clear(); self.absorption_canvas.draw()
            return

        base_data = self.file_data_cache[self.base_file_name]
        if 'S11_complex' not in base_data or 'S21_complex' not in base_data:
            self.absorption_ax_left.clear(); self.absorption_ax_swr.clear(); self.absorption_canvas.draw()
            return

        base_s11 = base_data['S11_complex']
        base_s21 = base_data['S21_complex']
        base_freqs = base_data['Freq_GHz']
        base_mag_db = 20 * np.log10(np.clip(np.abs(base_s21), 1e-12, None))
        base_swr = compute_swr(base_s11)

        ttk.Label(
            self.absorption_summary_frame,
            text="🏆 Best Absorption Performance (per zone, vs baseline)",
            font=("Arial", 10, "bold")
        ).grid(row=0, column=0, columnspan=len(zones) + 1, sticky="w", pady=(0, 8))

        ttk.Label(self.absorption_summary_frame, text="", width=14).grid(row=1, column=0)
        for zi, zb in enumerate(zones):
            ttk.Label(self.absorption_summary_frame, text=f"{zb[0]:.1f} - {zb[1]:.1f} GHz",
                      font=("Arial", 9, "bold"), foreground=T.MUTED).grid(row=1, column=zi + 1, padx=8)

        left_title_label = "avgC(|Mag|)" if self.absorption_view_mode == "mag" else "avgC(ΔMag)"
        ttk.Label(self.absorption_summary_frame, text=left_title_label, foreground=T.ACCENT, font=("Arial", 9, "bold")).grid(row=2, column=0, sticky="w")
        ttk.Label(self.absorption_summary_frame, text="avgC(|SWR|)", foreground=T.ACCENT, font=("Arial", 9, "bold")).grid(row=4, column=0, sticky="w")

        summary = {"mag": {}, "swr": {}}
        for zi, zb in enumerate(zones):
            mask_b = (base_freqs >= zb[0]) & (base_freqs <= zb[1])
            base_avg_mag_db = float(np.mean(base_mag_db[mask_b])) if mask_b.any() else None
            base_avg_swr = float(np.mean(base_swr[mask_b])) if mask_b.any() else None

            # C# also scans file 0 (the baseline itself: C=1, delta=0) as a candidate
            best_mag = (1.0, 0.0, self.base_file_name) if base_avg_mag_db is not None else None
            best_swr = None

            for f in self._get_filenames():
                # C# scans ALL loaded files (not just the 3 currently visible ones)
                if f == self.base_file_name or f not in self.file_data_cache: continue
                
                curr = self.file_data_cache[f]
                if 'S11_complex' not in curr or 'S21_complex' not in curr: continue
                freqs = curr['Freq_GHz']
                mask = (freqs >= zb[0]) & (freqs <= zb[1])
                if not mask.any(): continue

                mag_db = 20 * np.log10(np.clip(np.abs(curr['S21_complex']), 1e-12, None))
                swr = compute_swr(curr['S11_complex'])
                avg_mag_db = float(np.mean(mag_db[mask]))
                avg_swr = float(np.mean(swr[mask]))

                if base_avg_mag_db is not None:
                    c_mag = avg_mag_db / base_avg_mag_db if base_avg_mag_db != 0 else float('nan')
                    delta_mag = avg_mag_db - base_avg_mag_db
                    # C# (Resume4): best = file with the LOWEST delta (avgX - avg0), ties -> later file
                    if best_mag is None or delta_mag <= best_mag[1]:
                        best_mag = (c_mag, delta_mag, f)
                if base_avg_swr is not None:
                    c_swr = avg_swr / base_avg_swr if base_avg_swr != 0 else float('nan')
                    delta_swr = avg_swr - base_avg_swr
                    if best_swr is None or c_swr >= best_swr[0]:
                        best_swr = (c_swr, delta_swr, f)

            summary["mag"][zi] = best_mag
            summary["swr"][zi] = best_swr

            if best_mag:
                c, delta_db, fname = best_mag
                ttk.Label(self.absorption_summary_frame, text=f"{c:.4f} ({delta_db:.4f} dB)", justify="center").grid(row=2, column=zi + 1, padx=8)
                ttk.Label(self.absorption_summary_frame, text=f"{fname}", foreground=T.MUTED).grid(row=3, column=zi + 1, padx=8)
            else:
                ttk.Label(self.absorption_summary_frame, text="N/A").grid(row=2, column=zi + 1)

            if best_swr:
                c, delta_v, fname = best_swr
                ttk.Label(self.absorption_summary_frame, text=f"{c:.4f} ({delta_v:.4f} V)", justify="center").grid(row=4, column=zi + 1, padx=8)
                ttk.Label(self.absorption_summary_frame, text=f"{fname}", foreground=T.MUTED).grid(row=5, column=zi + 1, padx=8)
            else:
                ttk.Label(self.absorption_summary_frame, text="N/A").grid(row=4, column=zi + 1)

        self.last_absorption_summary = summary

        # ──────────────── BOTH PLOTS TOGGLE (C vs Delta) ────────────────
        self.absorption_ax_left.clear(); self.absorption_ax_swr.clear()
        
        if self.absorption_view_mode == "mag":
            left_chart_title = "C(Mag) = MagdB(S21ₓ) / MagdB(S21₀)"
            swr_chart_title = "C(SWR) = SWRₓ / SWR₀"
            ref_line = 1.0
        else:
            left_chart_title = "Delta(Mag) = MagdB(S21ₓ) - MagdB(S21₀)"
            swr_chart_title = "Delta(SWR) = SWRₓ - SWR₀"
            ref_line = 0.0

        for ax, title in ((self.absorption_ax_left, left_chart_title),
                          (self.absorption_ax_swr, swr_chart_title)):
            ax.set_facecolor(T.PLOT_BG)
            ax.set_title(title, color=T.FG, fontsize=9)
            ax.set_xlabel("Frequency (GHz)", color=T.MUTED, fontsize=8)
            ax.set_ylabel("Ratio / Delta", color=T.MUTED, fontsize=8)
            ax.tick_params(colors=T.MUTED, labelsize=7)
            ax.grid(True, linestyle=':', alpha=0.3, color=T.BORDER)

        base_mag_db_safe = np.where(np.abs(base_mag_db) < 1e-9, 1e-9, base_mag_db)
        base_swr_lin = base_swr  # C#: plain division, no clipping of the baseline

        left_x_data, left_y_data = [], []
        swr_x_data, swr_y_data = [], []

        for f in self._get_filenames():
            if f == self.base_file_name or f not in self.file_data_cache: continue
            if f in self.file_visibility and not self.file_visibility[f].get(): continue
            curr = self.file_data_cache[f]
            if 'S11_complex' not in curr or 'S21_complex' not in curr: continue
            freqs = curr['Freq_GHz']
            curr_mag_db_curve = 20 * np.log10(np.clip(np.abs(curr['S21_complex']), 1e-12, None))
            curr_swr_curve = compute_swr(curr['S11_complex'])
            
            if self.absorption_view_mode == "mag":
                left_curve = curr_mag_db_curve / base_mag_db_safe
                with np.errstate(divide='ignore', invalid='ignore'):
                    swr_curve = curr_swr_curve / base_swr_lin
            else: 
                left_curve = curr_mag_db_curve - base_mag_db
                swr_curve = curr_swr_curve - base_swr

            # Apply Trace Smoothing if enabled
            if self.smooth_enable_var.get():
                left_curve = apply_smoothing(left_curve, window_size=self.smooth_window_var.get())
                swr_curve = apply_smoothing(swr_curve, window_size=self.smooth_window_var.get())

            self.absorption_ax_left.plot(freqs, left_curve, label=f, linewidth=1.2)
            self.absorption_ax_swr.plot(freqs, swr_curve, label=f, linewidth=1.2)

            left_x_data.extend(freqs)
            left_y_data.extend(left_curve)
            swr_x_data.extend(freqs)
            swr_y_data.extend(swr_curve)

        self.absorption_ax_left.axhline(ref_line, color=T.GOOD, linestyle=':', alpha=0.8)
        self.absorption_ax_swr.axhline(ref_line, color=T.GOOD, linestyle=':', alpha=0.8)

        if self.absorption_zone_idx is not None and 0 <= self.absorption_zone_idx < len(zones):
            zb = zones[self.absorption_zone_idx]
            self.absorption_ax_left.set_xlim(zb[0], zb[1])
            self.absorption_ax_swr.set_xlim(zb[0], zb[1])
            self.absorption_zone_label.config(text=f"Zone {self.absorption_zone_idx + 1}: {zb[0]:.2f} - {zb[1]:.2f} GHz")
        else:
            apply_min_max_axis_limits(self.absorption_ax_left, left_x_data, left_y_data, pad_y=0.08)
            apply_min_max_axis_limits(self.absorption_ax_swr, swr_x_data, swr_y_data, pad_y=0.08)
            self.absorption_zone_label.config(text="Full Sweep View")

        if self.absorption_ax_left.get_legend_handles_labels()[0]:
            self.absorption_ax_left.legend(fontsize=6, facecolor=T.PANEL, edgecolor=T.BORDER, labelcolor=T.FG)

        try:
            self.absorption_fig.tight_layout()
        except Exception:
            pass
        self.absorption_canvas.draw()

    def absorption_prev_zone(self):
        zones = self.read_zones()
        if not zones: return
        self.absorption_zone_idx = 0 if self.absorption_zone_idx is None else (self.absorption_zone_idx - 1) % len(zones)
        self.update_absorption_tab(zones)

    def absorption_next_zone(self):
        zones = self.read_zones()
        if not zones: return
        self.absorption_zone_idx = 0 if self.absorption_zone_idx is None else (self.absorption_zone_idx + 1) % len(zones)
        self.update_absorption_tab(zones)

    def absorption_reset_zone(self):
        self.absorption_zone_idx = None
        zones = self.read_zones()
        if zones: self.update_absorption_tab(zones)

"""6-Zone Visual Traces tab: the central ``update_analysis`` pass that redraws every tab."""
import numpy as np

from rfanalyzer import theme as T
from rfanalyzer.core.dsp import apply_smoothing, compute_swr
from rfanalyzer.gui.plotting import apply_min_max_axis_limits


class AnalysisMixin:
    """6-Zone Visual Traces tab: the central ``update_analysis`` pass that redraws every tab.

    Mixed into :class:`rfanalyzer.gui.main_window.RFAnalyzerApp`; relies on the state set up in its ``__init__``.
    """

    def update_analysis(self):
        self.update_status_bar()
        if not self.base_file_name or self.base_file_name not in self.file_data_cache:
            return
            
        choice = self.param_var.get()
        is_s11 = "S11" in choice
        param_key = 'S11_complex' if is_s11 else 'S21_complex'

        if "Delta Log Mag" in choice:
            lbl_high, lbl_low, mode_unit, ref_line = ("Peak" if is_s11 else "Max", "Deep" if is_s11 else "Min", "dB", 0.0)
        elif "Phase Trace" in choice:
            lbl_high, lbl_low, mode_unit, ref_line = ("Max", "Min", "deg", 0.0)
        else:
            mode_unit, ref_line = ("Ratio Factor", 1.0)

        zones = self.read_zones()
        if not zones: return

        marker_freqs = self.get_marker_freqs()
        base_data = self.file_data_cache[self.base_file_name]
        if param_key not in base_data: return

        self.ax.clear()
        self.ax.set_facecolor(T.PLOT_BG)
        self.ax.xaxis.label.set_color(T.MUTED)
        self.ax.yaxis.label.set_color(T.MUTED)
        self.ax.title.set_color(T.FG)
        self.ax.tick_params(colors=T.MUTED, labelsize=8)

        for widget in self.params_inner.winfo_children(): widget.destroy()

        summary_rows = []
        marker_rows = []
        zone_avgs = {}
        marker_vals_for_best = {}

        s11_marker_rows = []
        s11_compare_rows = []
        base_s11 = base_data.get('S11_complex')
        base_s21 = base_data.get('S21_complex')
        base_avg_mag_db = base_avg_swr = None

        if base_s21 is not None:
            base_mag_db_full = 20 * np.log10(np.clip(np.abs(base_s21), 1e-12, None))
            base_avg_mag_db = float(np.mean(base_mag_db_full))
        if base_s11 is not None:
            base_swr_full = compute_swr(base_s11)
            base_avg_swr = float(np.mean(base_swr_full))

        all_plot_x = []
        all_plot_y = []

        for f in self._get_filenames():
            if f not in self.file_data_cache: continue
            
            if f != self.base_file_name and f in self.file_visibility and not self.file_visibility[f].get():
                continue
                
            curr = self.file_data_cache[f]
            if param_key in curr:
                freqs = curr['Freq_GHz']
                curr_mag = np.abs(curr[param_key])
                base_mag = np.abs(base_data[param_key])

                if "Delta Log Mag" in choice:
                    curr_raw = 20 * np.log10(np.where(curr_mag == 0, 1e-12, curr_mag))
                    base_raw = 20 * np.log10(np.where(base_mag == 0, 1e-12, base_mag))
                    processed = curr_raw - base_raw
                elif "Phase Trace" in choice:
                    curr_raw = np.angle(curr[param_key], deg=True)
                    base_raw = np.angle(base_data[param_key], deg=True)
                    processed = (curr_raw - base_raw + 180) % 360 - 180
                else:
                    curr_raw = curr_mag
                    base_raw = base_mag
                    processed = curr_mag / np.where(base_mag == 0, 1e-12, base_mag)

                # Apply smoothing if filter is enabled
                plot_y = apply_smoothing(processed, window_size=self.smooth_window_var.get()) if self.smooth_enable_var.get() else processed

                self.ax.plot(freqs, plot_y, label=f, linestyle='--' if f==self.base_file_name else '-', linewidth=2 if f==self.base_file_name else 1.2)
                all_plot_x.extend(freqs)
                all_plot_y.extend(plot_y)

                row = [f]
                for zi, zb in enumerate(zones):
                    mask = (freqs >= zb[0]) & (freqs <= zb[1])
                    sub = processed[mask]
                    if len(sub) == 0:
                        row.extend(["N/A", "N/A", "N/A"])
                    else:
                        avg_val = float(sub.mean())
                        row.extend([f"{sub.max():.4f}", f"{sub.min():.4f}", f"{avg_val:.4f}"])
                        if f != self.base_file_name:
                            zone_avgs.setdefault(zi, []).append((avg_val, f))
                summary_rows.append(row)

                mrow = [f]
                for mi, mf in enumerate(marker_freqs):
                    if mf is None or mf < freqs.min() or mf > freqs.max():
                        mrow.extend(["N/A", "N/A", "N/A"])
                        continue
                    curr_v = float(np.interp(mf, freqs, curr_raw))
                    base_v = float(np.interp(mf, freqs, base_raw))
                    delta_v = curr_v - base_v
                    ratio_v = curr_v / base_v if base_v != 0 else float('nan')
                    mrow.extend([f"{curr_v:.4f}", f"{ratio_v:.4f}" if ratio_v == ratio_v else "N/A", f"{delta_v:.4f}"])
                    if f != self.base_file_name:
                        marker_vals_for_best.setdefault(mi, []).append((curr_v, f))
                marker_rows.append(mrow)

                # ──────────────── COMPARATIVE MARKER & DELTA MATH ───────────────
                curr_s11 = curr.get('S11_complex')
                curr_s21 = curr.get('S21_complex')
                if (base_s11 is not None or base_s21 is not None) and (curr_s11 is not None or curr_s21 is not None):
                    freqs_ref = curr['Freq_GHz']
                    curr_mag_db = 20 * np.log10(np.clip(np.abs(curr_s21), 1e-12, None)) if curr_s21 is not None else None
                    curr_swr = compute_swr(curr_s11) if curr_s11 is not None else None

                    mk_row = [f]
                    for mf in marker_freqs:
                        if mf is None or mf < freqs_ref.min() or mf > freqs_ref.max():
                            mk_row.extend(["N/A", "N/A"])
                        else:
                            m_db = f"{np.interp(mf, freqs_ref, curr_mag_db):.4f}" if curr_mag_db is not None else "N/A"
                            m_swr = f"{np.interp(mf, freqs_ref, curr_swr):.4f}" if curr_swr is not None else "N/A"
                            mk_row.extend([m_db, m_swr])
                    s11_marker_rows.append(mk_row)

                    if curr_mag_db is not None and base_avg_mag_db is not None:
                        min_i, max_i = int(np.argmin(curr_mag_db)), int(np.argmax(curr_mag_db))
                        avg_mag_db = float(np.mean(curr_mag_db))
                        avgC_mag = avg_mag_db / base_avg_mag_db if base_avg_mag_db != 0 else float('nan')
                        delta_mag = avg_mag_db - base_avg_mag_db
                        mag_min_txt = f"{curr_mag_db[min_i]:.4f} / {freqs_ref[min_i]:.2f} GHz"
                        mag_max_txt = f"{curr_mag_db[max_i]:.4f} / {freqs_ref[max_i]:.2f} GHz"
                        mag_c_txt = f"{avgC_mag:.4f}" if avgC_mag == avgC_mag else "N/A"
                        mag_delta_txt = f"{delta_mag:.4f} dB"
                    else:
                        mag_min_txt = mag_max_txt = mag_c_txt = mag_delta_txt = "N/A"

                    if curr_swr is not None and base_avg_swr is not None:
                        min_swr_i, max_swr_i = int(np.argmin(curr_swr)), int(np.argmax(curr_swr))
                        avg_swr = float(np.mean(curr_swr))
                        avgC_swr = avg_swr / base_avg_swr if base_avg_swr != 0 else float('nan')
                        delta_swr = avg_swr - base_avg_swr
                        swr_min_txt = f"{curr_swr[min_swr_i]:.4f} / {freqs_ref[min_swr_i]:.2f} GHz"
                        swr_max_txt = f"{curr_swr[max_swr_i]:.4f} / {freqs_ref[max_swr_i]:.2f} GHz"
                        swr_c_txt = f"{avgC_swr:.4f}" if avgC_swr == avgC_swr else "N/A"
                        swr_delta_txt = f"{delta_swr:.4f} V"
                    else:
                        swr_min_txt = swr_max_txt = swr_c_txt = swr_delta_txt = "N/A"

                    s11_compare_rows.append([
                        f, mag_min_txt, mag_max_txt, mag_c_txt, mag_delta_txt, 
                        swr_min_txt, swr_max_txt, swr_c_txt, swr_delta_txt
                    ])

        self.last_summary_rows = summary_rows
        self.last_marker_rows = marker_rows
        self.last_s11_marker_rows = s11_marker_rows
        self.last_s11_compare_rows = s11_compare_rows

        best_zone_info = None
        if zone_avgs:
            best_zi = min(zone_avgs, key=lambda zi: min(v for v, _ in zone_avgs[zi]))
            best_val, best_fname = min(zone_avgs[best_zi], key=lambda t: t[0])
            best_zone_info = {
                "zone": best_zi + 1,
                "range": zones[best_zi],
                "value": best_val,
                "file": best_fname,
            }
        self.last_best_zone_info = best_zone_info

        best_marker_info = None
        if marker_vals_for_best:
            best_mi = min(marker_vals_for_best, key=lambda mi: min(v for v, _ in marker_vals_for_best[mi]))
            best_val, best_fname = min(marker_vals_for_best[best_mi], key=lambda t: t[0])
            best_marker_info = {
                "marker": best_mi + 1,
                "freq": marker_freqs[best_mi],
                "value": best_val,
                "file": best_fname,
            }
        self.last_best_marker_info = best_marker_info

        for mi, mf in enumerate(marker_freqs):
            if mf is None: continue
            self.ax.axvline(mf, color=T.WARN, linestyle=':', linewidth=1.3, alpha=0.85)
            self.ax.annotate(f"M{mi+1}", xy=(mf, 1), xycoords=('data', 'axes fraction'),
                              xytext=(2, -12), textcoords='offset points',
                              color=T.WARN, fontsize=8, fontweight='bold')

        self.ax.axhline(ref_line, color='red', linestyle=':', alpha=0.8)
        for idx, zb in enumerate(zones):
            zone_color = T.GOOD if (best_zone_info and best_zone_info["zone"] - 1 == idx) else T.ZONE_COLS[idx % len(T.ZONE_COLS)]
            self.ax.axvspan(zb[0], zb[1], color=zone_color, alpha=0.06 if zone_color != T.GOOD else 0.12)

        self.ax.set_title(f"6-Zone Dynamic Analysis Sweep Profile [{choice}]")
        self.ax.set_xlabel("Frequency (GHz)"); self.ax.set_ylabel(f"Magnitude ({mode_unit})")
        self.ax.grid(True, linestyle=':', alpha=0.3, color=T.BORDER)
        if self.ax.get_legend_handles_labels()[0]:
            self.ax.legend(loc='upper right', fontsize='8', facecolor=T.PANEL, edgecolor=T.BORDER, labelcolor=T.FG)

        apply_min_max_axis_limits(self.ax, all_plot_x, all_plot_y, pad_y=0.08)
        self.canvas.draw()

        # Key Parameters tab = port of the C# 'Parameters' tab
        self._compute_cs_params(marker_freqs)
        self._render_cs_params()

        self.update_absorption_tab(zones)
        self.update_trend_tab(param_key, zones, marker_freqs)

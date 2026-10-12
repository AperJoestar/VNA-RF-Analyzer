"""Status bar, help dialog and dark/light theme switching."""
import os
import re
from tkinter import messagebox

import numpy as np

from rfanalyzer import theme as T
from rfanalyzer.gui.styles import style_ttk


class AppearanceMixin:
    """Status bar, help dialog and dark/light theme switching.

    Mixed into :class:`rfanalyzer.gui.main_window.RFAnalyzerApp`; relies on the state set up in its ``__init__``.
    """

    def update_status_bar(self):
        """Port of Label17 (frequency info) and Label16 (folder / file counts) of the reference app."""
        try:
            base = self.file_data_cache.get(self.base_file_name) if self.base_file_name else None
            if base is not None and len(base.get('Freq_GHz', [])):
                fr = np.asarray(base['Freq_GHz'], float)
                mk = []
                for mf in self.get_marker_freqs():
                    mk.append(f"{round(float(fr[int(np.argmin(np.abs(fr - mf)))]), 2):g} GHz" if mf is not None else "N/A")
                freq_txt = (f"Start Freq = {fr.min():g} GHz; Stop Freq = {fr.max():g} GHz ;  Point = {len(fr)};  "
                            f"( M1-M2-M3 = {mk[0]} - {mk[1]} -{mk[2]} )")
            else:
                freq_txt = "Start Freq = -; Stop Freq = -;  Point = -"
            self.status_freq_label.config(text=freq_txt)

            if self.file_paths:
                folder = os.path.dirname(os.path.abspath(self.file_paths[0]))
                drive, rest = os.path.splitdrive(folder)
                parts = [x for x in re.split(r"[\\/]+", rest) if x]
                shown = f"{drive}{os.sep}...{os.sep}{parts[-1]}" if len(parts) > 1 else folder
                kb = os.path.getsize(self.file_paths[-1]) // 1000
                pics = sum(1 for f in os.listdir(folder) if f.lower().endswith(".png"))
                folder_txt = f"Folder - {shown};      Count Files = {len(self.file_paths)} x {kb} kB ;   Count Pic = {pics}"
            else:
                folder_txt = "Folder - (no CSV files loaded)"
            self.status_folder_label.config(text=folder_txt)
        except Exception:
            pass

    def show_help(self):
        messagebox.showinfo("Help", (
            "Mag_Type/Zones tab\n"
            "  • Antenna Analyser button: left click = Alternation, right click = In half\n"
            "  • Show Table: green row = best (lowest Δ(Mag),dB) per zone/marker, gray = baseline\n"
            "  • Export Table: saves the table that is shown\n\n"
            "All graphs: hover the plot to read the cursor coordinates.\n\n"
            "Output Tools (left panel)\n"
            "  • Export Resume  -> zExportR   (Freq + Mag per file)\n"
            "  • Export Full    -> zExport    (Freq + Re/Im per file)\n"
            "  • Export Tables  -> zExport_DGRV / zExport_DGRV_M\n"
            "  • Save Pic       -> PNG of the current tab\n"
            "Files are written to the 'exports' folder."))

    def toggle_theme(self):
        self.apply_theme("light" if T.CURRENT_THEME == "dark" else "dark")

    def apply_theme(self, name):
        old = {k: str(v).lower() for k, v in T.THEMES[T.CURRENT_THEME].items()}
        T.set_theme(name)
        mapping = {old[k]: T.THEMES[name][k] for k in old if old[k] != str(T.THEMES[name][k]).lower()}
        style_ttk()
        self.root.configure(bg=T.BG)
        self._recolor_widgets(self.root, mapping)
        for fig in (self.fig, self.absorption_fig, self.trend_fig):
            fig.patch.set_facecolor(T.PANEL)
        for ax in (self.ax, self.absorption_ax_left, self.absorption_ax_swr, self.trend_ax):
            ax.set_facecolor(T.PLOT_BG)
            ax.tick_params(colors=T.MUTED)
            for sp in ax.spines.values():
                sp.set_color(T.BORDER)
        self.theme_btn.config(text="🌙 Dark mode" if name == "light" else "☀ Light mode")
        T.save_theme(name)
        self.update_analysis()           # redraws the charts and rebuilds the tables with the new colours

    def _recolor_widgets(self, widget, mapping):
        """Swap explicitly-set old-theme colours of tk/ttk widgets for the new theme."""
        for opt in ("background", "foreground", "highlightbackground", "highlightcolor", "insertbackground",
                    "selectbackground", "selectforeground", "activebackground", "activeforeground",
                    "troughcolor", "disabledforeground"):
            try:
                cur = str(widget.cget(opt)).lower()
            except Exception:
                continue
            if cur in mapping:
                try:
                    widget.configure(**{opt: mapping[cur]})
                except Exception:
                    pass
        for child in widget.winfo_children():
            self._recolor_widgets(child, mapping)

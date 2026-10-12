"""Loading CSV logs, baseline selection, file-visibility paging and marker/zone input readers."""
import glob
import os
import threading
import tkinter as tk
from tkinter import filedialog, ttk

import numpy as np

from rfanalyzer import theme as T
from rfanalyzer.core.vna_io import natural_sort_key, parse_vna_file


class FileDataMixin:
    """Loading CSV logs, baseline selection, file-visibility paging and marker/zone input readers.

    Mixed into :class:`rfanalyzer.gui.main_window.RFAnalyzerApp`; relies on the state set up in its ``__init__``.
    """

    def parse_vna_file_complex(self, file_path):
        """Parse one CSV with the current decimal-separator setting (see ``core.vna_io.parse_vna_file``)."""
        return parse_vna_file(file_path, decimal_comma=self.decimal_mode.get())

    def load_all_files_to_cache(self):
        self.file_data_cache.clear()
        for fpath in self.file_paths:
            fname = os.path.basename(fpath)
            data = self.parse_vna_file_complex(fpath)
            if data:
                self.file_data_cache[fname] = data

    def load_baseline_bounds(self):
        try:
            if not self.base_file_name or self.base_file_name not in self.file_data_cache:
                return
            data = self.file_data_cache[self.base_file_name]
            f_min, f_max = np.min(data['Freq_GHz']), np.max(data['Freq_GHz'])
            step = (f_max - f_min) / 6
            for i in range(6):
                self.zone_inputs[i]['min'].delete(0, tk.END)
                self.zone_inputs[i]['max'].delete(0, tk.END)
                self.zone_inputs[i]['min'].insert(0, f"{f_min + (i * step):.2f}")
                self.zone_inputs[i]['max'].insert(0, f"{f_min + ((i + 1) * step):.2f}")

            span = f_max - f_min
            defaults = [f_min + span * 0.25, f_min + span * 0.50, f_min + span * 0.75]
            for i in range(3):
                self.marker_inputs[i].delete(0, tk.END)
                self.marker_inputs[i].insert(0, f"{defaults[i]:.2f}")
        except Exception:
            pass

    def on_decimal_toggle(self):
        self.load_all_files_to_cache()
        self.update_analysis()

    def _get_filenames(self):
        return [os.path.basename(f) for f in self.file_paths]

    def _non_baseline_files(self):
        return [f for f in self._get_filenames() if f != self.base_file_name]

    def _visibility_page_count(self):
        n = len(self._non_baseline_files())
        return max(1, (n + self.visibility_page_size - 1) // self.visibility_page_size)

    def visibility_prev_page(self):
        self.visibility_page = (self.visibility_page - 1) % self._visibility_page_count()
        self.active_single_file.set("ALL")
        self.rebuild_visibility_list()

    def visibility_next_page(self):
        self.visibility_page = (self.visibility_page + 1) % self._visibility_page_count()
        self.active_single_file.set("ALL")
        self.rebuild_visibility_list()

    def update_visibility_state(self, trigger_update=True):
        non_baseline = self._non_baseline_files()
        start = self.visibility_page * self.visibility_page_size
        current_trio = non_baseline[start:start + self.visibility_page_size]

        selected = self.active_single_file.get()

        for f in self._get_filenames():
            if f not in self.file_visibility:
                self.file_visibility[f] = tk.BooleanVar(value=False)
            
            if f == self.base_file_name:
                self.file_visibility[f].set(True)
            elif selected == "ALL":
                self.file_visibility[f].set(f in current_trio)
            else:
                self.file_visibility[f].set(f == selected)

        if trigger_update:
            self.update_analysis()

    def rebuild_visibility_list(self):
        for widget in self.filter_container.winfo_children(): widget.destroy()

        page_count = self._visibility_page_count()
        self.visibility_page = max(0, min(self.visibility_page, page_count - 1))

        if self.base_file_name:
            base_row = ttk.Frame(self.filter_container)
            base_row.pack(fill=tk.X, pady=(0, 8))
            ttk.Label(base_row, text="⭐ Baseline (always visible):", foreground=T.GOOD, font=("Arial", 9, "bold")).pack(anchor=tk.W)
            ttk.Label(base_row, text=self.base_file_name, foreground=T.FG, wraplength=220, justify=tk.LEFT).pack(anchor=tk.W, padx=(12, 0))
        else:
            ttk.Label(self.filter_container, text="No baseline loaded yet.", foreground=T.MUTED).pack(anchor=tk.W)

        non_baseline = self._non_baseline_files()
        if not non_baseline:
            ttk.Label(self.filter_container, text="\nNo other files loaded.", foreground=T.MUTED).pack(anchor=tk.W)
            return

        nav_row = ttk.Frame(self.filter_container)
        nav_row.pack(fill=tk.X, pady=(2, 4))
        ttk.Button(nav_row, text="◀", width=3, command=self.visibility_prev_page).pack(side=tk.LEFT)
        self.visibility_page_label = ttk.Label(nav_row, text=f"Page {self.visibility_page + 1}/{page_count}", foreground=T.MUTED)
        self.visibility_page_label.pack(side=tk.LEFT, expand=True)
        ttk.Button(nav_row, text="▶", width=3, command=self.visibility_next_page).pack(side=tk.RIGHT)

        start = self.visibility_page * self.visibility_page_size
        shown_files = non_baseline[start:start + self.visibility_page_size]

        list_frame = ttk.Frame(self.filter_container)
        list_frame.pack(fill=tk.X, pady=(2, 4))

        ttk.Radiobutton(
            list_frame, 
            text="[ Show All 3 in Trio ]", 
            value="ALL", 
            variable=self.active_single_file, 
            command=self.update_visibility_state
        ).pack(anchor=tk.W, pady=(0, 6))

        for f in shown_files:
            if f not in self.file_visibility:
                self.file_visibility[f] = tk.BooleanVar(value=False)
            ttk.Radiobutton(
                list_frame, 
                text=f, 
                value=f, 
                variable=self.active_single_file, 
                command=self.update_visibility_state
            ).pack(anchor=tk.W, pady=2)
            
        self.update_visibility_state(trigger_update=False)

    def upload_csv_data(self):
        file_paths = filedialog.askopenfilenames(title="Select File in VNA CSV Log Folder", filetypes=[("CSV Data Files", "*.csv")])
        if not file_paths: return

        target_dir = os.path.dirname(file_paths[0])
        all_csvs = glob.glob(os.path.join(target_dir, "*.csv"))
        
        self.file_paths = sorted(all_csvs, key=natural_sort_key)
        self.baseline_label.config(text="Loading files into memory...", foreground=T.WARN)
        
        threading.Thread(target=self._process_uploads_thread, daemon=True).start()

    def _process_uploads_thread(self):
        self.file_visibility = {}
        self.base_file_name = None
        self.visibility_page = 0
        if hasattr(self, 'active_single_file'):
            self.active_single_file.set("ALL")

        for file_path in self.file_paths:
            filename = os.path.basename(file_path)
            self.file_visibility[filename] = tk.BooleanVar(value=False)
            if self.base_file_name is None or "exp0" in filename.lower():
                self.base_file_name = filename

        self.file_paths = sorted(self.file_paths, key=lambda x:natural_sort_key (os.path.basename(x)))
        self.load_all_files_to_cache()
        self.root.after(0, self._finalize_uploads)

    def _finalize_uploads(self):
        self.load_baseline_bounds()
        self.update_baseline_label()
        self.rebuild_visibility_list()
        self.update_analysis()

    def update_baseline_label(self):
        self.baseline_label.config(text=f"Baseline Reference:\n{self.base_file_name}", foreground="teal")

    def get_marker_freqs(self):
        vals = []
        for entry in self.marker_inputs:
            try:
                vals.append(float(entry.get()))
            except ValueError:
                vals.append(None)
        return vals

    def read_zones(self):
        zones = []
        try:
            for i in range(6):
                zones.append((float(self.zone_inputs[i]['min'].get()), float(self.zone_inputs[i]['max'].get())))
        except (ValueError, AttributeError):
            return []
        return zones

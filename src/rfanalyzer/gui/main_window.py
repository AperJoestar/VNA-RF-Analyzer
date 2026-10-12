"""Main application window."""
import glob
import os
import tkinter as tk
from tkinter import ttk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from rfanalyzer import theme as T
from rfanalyzer.config import EXPORTS_DIR
from rfanalyzer.core.vna_io import natural_sort_key
from rfanalyzer.gui.cursor import CursorReadout
from rfanalyzer.gui.styles import style_ttk
from rfanalyzer.gui.mixins import (
    AppearanceMixin,
    FileDataMixin,
    GalleryMixin,
    AnalysisMixin,
    ParamsTabMixin,
    AbsorptionTabMixin,
    TrendTabMixin,
    ExportMixin,
)


class RFAnalyzerApp(
    AppearanceMixin,
    FileDataMixin,
    GalleryMixin,
    AnalysisMixin,
    ParamsTabMixin,
    AbsorptionTabMixin,
    TrendTabMixin,
    ExportMixin,
):
    """Professional 6-Zone RF Analyzer + Marker Comparator (main Tk window).

    This class only builds the window and owns the shared state; all behaviour lives in the mixins.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("📡 Professional 6-Zone RF Analyzer + Marker Comparator")
        self.root.geometry("1800x920")
        self.root.configure(bg=T.BG)

        style_ttk()

        self.exports_dir = EXPORTS_DIR
        if not os.path.exists(self.exports_dir):
            os.makedirs(self.exports_dir)

        self.file_paths = sorted(glob.glob("*.csv"), key=natural_sort_key)
        self.image_paths = []
        self.file_data_cache = {}
        
        self.base_file_path = [f for f in self.file_paths if "exp0" in os.path.basename(f).lower()]
        self.base_file_name = os.path.basename(self.base_file_path[0]) if self.base_file_path else (os.path.basename(self.file_paths[0]) if self.file_paths else None)

        self.file_visibility = {os.path.basename(f): tk.BooleanVar(value=True) for f in self.file_paths}
        self.active_single_file = tk.StringVar(value="ALL")

        self.visibility_page = 0
        self.visibility_page_size = 3
        self.decimal_mode = tk.BooleanVar(value=False)
        self.export_comma = tk.BooleanVar(value=False)      # exports: decimal point -> comma (C# CheckBox1)
        self.export_s11_mag = tk.BooleanVar(value=False)    # exports: S11 as Mag dB instead of SWR (C# SwrToMag)

        # Trace Smoothing Variables
        self.smooth_enable_var = tk.BooleanVar(value=False)
        self.smooth_window_var = tk.StringVar(value="15")

        self.raw_pil_left = None
        self.disp_pil_left = None
        self.tk_img_left = None
        self.markers_left = []

        self.raw_pil_right = None
        self.disp_pil_right = None
        self.tk_img_right = None
        self.markers_right = []

        self.last_summary_rows = []
        self.last_marker_rows = []
        self.last_best_zone_info = None
        self.last_best_marker_info = None

        self.absorption_zone_idx = None
        self.last_absorption_summary = None
        self.absorption_view_mode = "mag"  # "mag" for C(Mag), "delta" for Delta(Mag)

        self.trend_mode = "zone"           # "zone", "marker", or "antenna"
        self.trend_val_mode = "ratio"      # "ratio" for C(Mag), "delta" for Delta(Mag)
        self.trend_base_mode = "zone"      # what Antenna Analyser draws: "zone" (6 blocks) or "marker" (3 blocks)
        self.antenna_pair_mode = 0         # 0 = Alternation (file 2k vs 2k+1), 1 = In half (file k vs k+N/2)
        self.last_antenna_rows = []
        self.last_antenna_export = []
        self.trend_show_table = False
        self.last_trend_matrix = []
        self.last_trend_x_labels = []
        self.last_trend_table_data = []

        self.setup_ui()

        # Visual Traces Graph
        self.fig, self.ax = plt.subplots(figsize=(9, 5.2))
        self.fig.patch.set_facecolor(T.PANEL)
        self.ax.set_facecolor(T.PLOT_BG)
        self.ax.tick_params(colors=T.MUTED, labelsize=8)
        self.ax.spines[:].set_color(T.BORDER)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_tab)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Mag & SWR Zones Tab Graphs
        self.absorption_fig, (self.absorption_ax_left, self.absorption_ax_swr) = plt.subplots(1, 2, figsize=(11, 4.3))
        self.absorption_fig.patch.set_facecolor(T.PANEL)
        for _ax in (self.absorption_ax_left, self.absorption_ax_swr):
            _ax.set_facecolor(T.PLOT_BG)
            _ax.tick_params(colors=T.MUTED, labelsize=7)
            _ax.spines[:].set_color(T.BORDER)
        self.absorption_canvas = FigureCanvasTkAgg(self.absorption_fig, master=self.absorption_charts_frame)
        self.absorption_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Zone Ratio / Delta Trends Tab Graph
        self.trend_fig, self.trend_ax = plt.subplots(figsize=(9, 4.5))
        self.trend_fig.patch.set_facecolor(T.PANEL)
        self.trend_ax.set_facecolor(T.PLOT_BG)
        self.trend_ax.tick_params(colors=T.MUTED, labelsize=8)
        self.trend_ax.spines[:].set_color(T.BORDER)
        self.trend_canvas = FigureCanvasTkAgg(self.trend_fig, master=self.trend_chart_frame)
        self.trend_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Cursor coordinate readout on every graph
        self.cursor_readouts = [
            CursorReadout(self.canvas, [self.ax]),
            CursorReadout(self.absorption_canvas, [self.absorption_ax_left, self.absorption_ax_swr]),
            CursorReadout(self.trend_canvas, [self.trend_ax]),
        ]

        self.load_all_files_to_cache()
        self.load_baseline_bounds()
        self.update_analysis()
        self.refresh_image_gallery()

    def setup_ui(self):
        # Status bar (same information as the header of the reference app) + theme toggle
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(6, 0))
        help_lbl = ttk.Label(self.status_bar, text="Help", foreground=T.ACCENT, cursor="hand2",
                             font=("Arial", 9, "underline"))
        help_lbl.pack(side=tk.RIGHT, padx=(8, 0))
        help_lbl.bind("<Button-1>", lambda e: self.show_help())
        self.theme_btn = ttk.Button(self.status_bar, text="☀ Light mode", command=self.toggle_theme)
        self.theme_btn.pack(side=tk.RIGHT, padx=8)
        self.status_folder_label = ttk.Label(self.status_bar, text="", font=("Arial", 9, "bold"))
        self.status_folder_label.pack(side=tk.RIGHT, padx=14)
        self.status_freq_label = ttk.Label(self.status_bar, text="", font=("Arial", 9))
        self.status_freq_label.pack(side=tk.LEFT)

        outer_control = ttk.Frame(self.root)
        outer_control.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        control_canvas = tk.Canvas(outer_control, width=300, highlightthickness=0, bg=T.BG)
        control_scroll = ttk.Scrollbar(outer_control, orient="vertical", command=control_canvas.yview)
        control_frame = ttk.LabelFrame(control_canvas, text=" 🛠 System Panel ", padding=12)
        control_frame.bind("<Configure>", lambda e: control_canvas.configure(scrollregion=control_canvas.bbox("all")))
        control_canvas.create_window((0, 0), window=control_frame, anchor="nw", width=300)
        control_canvas.configure(yscrollcommand=control_scroll.set)
        control_canvas.pack(side=tk.LEFT, fill=tk.Y, expand=True)
        control_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.baseline_label = ttk.Label(control_frame, text=f"Baseline Reference:\n{self.base_file_name}", foreground="teal", font=("Arial", 9, "bold"))
        self.baseline_label.pack(anchor=tk.W, pady=5)

        ttk.Button(control_frame, text="📂 Load New CSV Log Folder", command=self.upload_csv_data).pack(fill=tk.X, pady=4)
        ttk.Button(control_frame, text="📸 Upload Instrument Screenshots", command=self.upload_screenshot).pack(fill=tk.X, pady=4)

        ttk.Label(control_frame, text="Matrix Track / Version Mode:").pack(anchor=tk.W, pady=4)

        self.param_var = tk.StringVar()
        self.param_combo = ttk.Combobox(
            control_frame,
            textvariable=self.param_var,
            values=[
                "S11 Delta Log Mag (dB)",
                "S21 Delta Log Mag (dB)",
                "S11 Phase Trace (deg)",
                "S21 Phase Trace (deg)",
                "Scalar Ratio Profile (Real/Im)"
            ],
            state="readonly",
            width=30
        )
        self.param_combo.pack(fill=tk.X, pady=2)
        self.param_combo.set("S21 Delta Log Mag (dB)")
        self.param_combo.bind("<<ComboboxSelected>>", lambda e: self.update_analysis())

        ttk.Label(control_frame, text="\n🎯 Configure 3 Frequency Markers (GHz):").pack(anchor=tk.W)
        self.marker_inputs = []
        for i in range(3):
            row = ttk.Frame(control_frame)
            row.pack(fill=tk.X, pady=3)
            ttk.Label(row, text=f"M{i+1}: ", width=8).pack(side=tk.LEFT)
            m_entry = ttk.Entry(row, width=8)
            m_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
            self.marker_inputs.append(m_entry)
        ttk.Button(control_frame, text="🎯 Set Markers", command=self.update_analysis).pack(fill=tk.X, pady=4)

        ttk.Label(control_frame, text="\n🎯 Configure 6 Frequency Zones (GHz):").pack(anchor=tk.W)
        self.zone_inputs = []
        for i in range(6):
            row = ttk.Frame(control_frame)
            row.pack(fill=tk.X, pady=3)
            ttk.Label(row, text=f"Zone {i+1}: ", width=8).pack(side=tk.LEFT)
            min_entry = ttk.Entry(row, width=6)
            min_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
            ttk.Label(row, text="-").pack(side=tk.LEFT)
            max_entry = ttk.Entry(row, width=6)
            max_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
            self.zone_inputs.append({'min': min_entry, 'max': max_entry})

        ttk.Button(control_frame, text="Apply Changes & Slices", command=self.update_analysis).pack(fill=tk.X, pady=8)

        # 🌊 RF Trace Smoothing Controls
        ttk.Label(control_frame, text="\n🌊 RF Trace Smoothing:").pack(anchor=tk.W)
        ttk.Checkbutton(
            control_frame,
            text="Enable Savitzky-Golay Filter",
            variable=self.smooth_enable_var,
            command=self.update_analysis
        ).pack(anchor=tk.W, pady=2)
        
        smooth_row = ttk.Frame(control_frame)
        smooth_row.pack(fill=tk.X, pady=2)
        ttk.Label(smooth_row, text="Window Size: ", font=("Arial", 8)).pack(side=tk.LEFT)
        self.smooth_combo = ttk.Combobox(
            smooth_row,
            textvariable=self.smooth_window_var,
            values=["5", "9", "15", "25", "35", "51"],
            state="readonly",
            width=6
        )
        self.smooth_combo.pack(side=tk.LEFT, padx=4)
        self.smooth_combo.bind("<<ComboboxSelected>>", lambda e: self.update_analysis())

        ttk.Checkbutton(
            control_frame,
            text="🔁 Comma ⇄ Point (EU decimal CSV)",
            variable=self.decimal_mode,
            command=self.on_decimal_toggle
        ).pack(anchor=tk.W, pady=6)

        ttk.Label(control_frame, text="\n💾 Output Tools:").pack(anchor=tk.W)
        ttk.Button(control_frame, text="📸 Save Pic (current tab)", command=self.save_pic).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="💾 Save Chart as PNG", command=self.save_chart_png).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="📤 Export Resume (zExportR)", command=lambda: self.export_zexport(full=False)).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="📤 Export Full Data (zExport)", command=lambda: self.export_zexport(full=True)).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="📋 Export Tables (zExport_DGRV / _M)", command=self.export_dgrv_both).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="📄 Export Summary Report", command=lambda: self.export_data(full=False)).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="📄 Export Processed Data (per file)", command=lambda: self.export_data(full=True)).pack(fill=tk.X, pady=2)
        ttk.Checkbutton(control_frame, text="Exports: point ⇒ comma", variable=self.export_comma).pack(anchor=tk.W, pady=(6, 0))
        ttk.Checkbutton(control_frame, text="Exports: S11 as Mag dB (not SWR)", variable=self.export_s11_mag).pack(anchor=tk.W)

        ttk.Label(control_frame, text="\n📂 File Visibility Filters:").pack(anchor=tk.W, pady=2)
        self.filter_container = ttk.Frame(control_frame)
        self.filter_container.pack(fill=tk.BOTH, expand=True, pady=5)
        self.rebuild_visibility_list()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.graph_tab = ttk.Frame(self.notebook)
        self.params_tab = ttk.Frame(self.notebook)
        self.absorption_tab = ttk.Frame(self.notebook)
        self.trend_tab = ttk.Frame(self.notebook)
        self.image_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.graph_tab, text="📉 6-Zone Visual Traces")
        self.notebook.add(self.params_tab, text="📊 Key Parameters (Markers)")
        self.notebook.add(self.absorption_tab, text="🏆 Mag & SWR Zones")
        self.notebook.add(self.trend_tab, text="📈 Mag_Type/Zones")
        self.notebook.add(self.image_tab, text="🖼️ Side-by-Side Comparison Panels")

        self.setup_absorption_tab()
        self.setup_trend_tab()
        self.setup_params_tab()


# Name used by the original single-file script
FinalRFAnalyzerApp = RFAnalyzerApp

# Architecture

The application started as one 2,300-line script. It is now a package with a strict dependency direction:

```
app.py ──► gui/main_window.py ──► gui/mixins/*  ──► core/*  (numpy / scipy / pandas only)
              │                        │
              └────────────► theme.py, config.py
```

`core/` never imports Tk or matplotlib, so it can be tested and reused (for example from a notebook) without a
display.

## Modules

| Module | Responsibility |
|---|---|
| `app.py` | Entry point. Shows a splash window, *then* imports the GUI (numpy, pandas, matplotlib, scipy, Pillow), so the window appears immediately. |
| `config.py` | Folder names (`exports/`, `Pics/`) and the settings-file location. |
| `theme.py` | Dark/light palettes and persistence. `set_theme()` rewrites the module attributes (`theme.BG`, ...). |
| `core/dsp.py` | Savitzky–Golay smoothing, cardinal splines, SWR. |
| `core/vna_io.py` | VNA CSV parser, natural file sort, tab-separated writer used by the exports. |
| `core/tables.py` | Number formatting and "best row" logic shared by tables and exports. |
| `gui/main_window.py` | `RFAnalyzerApp`: builds the window, creates the figures, owns all shared state. |
| `gui/styles.py`, `gui/cursor.py`, `gui/plotting.py` | ttk styling, the hover coordinate read-out, axis-limit helper. |
| `gui/mixins/` | One mixin per feature (below). |

### Mixins

| Mixin | Feature |
|---|---|
| `FileDataMixin` | CSV loading (threaded), baseline choice, file-visibility paging, reading marker/zone entries |
| `AnalysisMixin` | `update_analysis()` – the *6-Zone Visual Traces* tab; it is also the hub that refreshes every other tab |
| `ParamsTabMixin` | *Key Parameters (Markers)* tab |
| `AbsorptionTabMixin` | *Mag & SWR Zones* tab |
| `TrendTabMixin` | *Mag_Type/Zones* tab, Antenna Analyser mode and the result table |
| `GalleryMixin` | *Side-by-Side Comparison Panels* (screenshots with crosshair markers) |
| `ExportMixin` | `zExport*` text files, DGRV tables, summary reports, PNG exports |
| `AppearanceMixin` | status bar, help dialog, theme switching |

`RFAnalyzerApp` inherits from all of them. They share state through `self` (for example `self.file_data_cache`,
`self.base_file_name`, `self.param_var`), which is created in `RFAnalyzerApp.__init__`.

## Data flow

1. `FileDataMixin.load_all_files_to_cache()` parses every CSV with `core.vna_io.parse_vna_file` into
   `{"Freq_GHz", "S11_complex", "S21_complex"}` arrays, stored in `file_data_cache[filename]`.
2. Any control change (mode, zones, markers, smoothing, visibility, theme) calls `update_analysis()`.
3. `update_analysis()` redraws the main chart, fills `last_summary_rows` / `last_marker_rows` / best-zone info,
   then calls `_compute_cs_params` + `_render_cs_params`, `update_absorption_tab` and `update_trend_tab`.
4. Exports read the `last_*` results (or recompute from the cache) and write into `exports/`.

## Theme handling

Palette values are module attributes of `rfanalyzer.theme`. Code reads them as `T.BG` when it draws, and
`AppearanceMixin.apply_theme()` swaps the colours of already-created widgets with `_recolor_widgets()` and redraws
the figures. Importing a colour by value (`from rfanalyzer.theme import BG`) would freeze it at import time.

## Adding a tab

1. Create `gui/mixins/my_tab.py` with a `MyTabMixin` (`setup_my_tab()` builds widgets, `update_my_tab()` draws).
2. Add it to `gui/mixins/__init__.py` and to the base classes of `RFAnalyzerApp`.
3. In `RFAnalyzerApp.setup_ui()` add the notebook tab and call `setup_my_tab()`; call `update_my_tab()` from
   `update_analysis()`.
4. Put any maths in `core/` and test it.

# RF Analyzer

A desktop app for analysing series of **VNA (vector network analyser) measurements**. Load a folder of CSV logs,
pick a baseline (`exp0`), and compare every other sweep against it — per frequency **zone**, at **markers**, as
**SWR / Mag (dB)** pairs, or in the "Antenna Analyser" pair view. Built with Tkinter and matplotlib; works on
Windows, macOS and Linux.

> Originally a single script (`gui_app_optimized.py`); now a regular Python package with tests and CI.
> See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for how it is organised.

## Features

| Tab | What it shows |
|---|---|
| **📉 6-Zone Visual Traces** | Every visible sweep relative to the baseline (S11/S21 Δ log-mag, phase, or scalar ratio) with 6 editable frequency zones, 3 markers, the best zone highlighted, and optional Savitzky–Golay smoothing. |
| **📊 Key Parameters (Markers)** | Per file: Mag (dB) and SWR at M1–M3, min/max Mag and SWR with their frequencies, avgC(Mag) / avgC(SWR), plus a "best absorption performance" resume. Click the section heading to page through 10 files at a time. |
| **🏆 Mag & SWR Zones** | Best file per zone (C and Δ of average Mag and SWR vs. baseline), full-sweep or per-zone zoom, switchable between ratio C(…) and difference Δ(…). |
| **📈 Mag_Type/Zones** | Trends across all files per zone or at the markers, a result table with the best row per block highlighted, and the **Antenna Analyser** (left click = *Alternation*: file 2k vs 2k+1; right click = *In half*: file k vs k+N/2). |
| **🖼️ Side-by-Side Comparison Panels** | Two instrument screenshots next to each other with click-to-place crosshair markers. |

Also: dark/light theme (remembered), hover read-out of coordinates on every chart, European decimal-comma CSV support,
and a set of exports (see below).

## Install

Requires **Python 3.9+** with Tkinter (included with the python.org installers; on Debian/Ubuntu:
`sudo apt install python3-tk`).

```bash
git clone <your-repo-url>
cd rf-analyzer
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .
```

## Run

The app reads the `*.csv` files **in the folder you start it from** (you can also load another folder from the
app with *Load New CSV Log Folder*).

```bash
# try it with the bundled synthetic data
cd examples/sample_data
rf-analyzer                        # or: python -m rfanalyzer

# your own measurements
cd path/to/your/csv/logs
rf-analyzer
```

The file whose name contains `exp0` is used as the baseline; if there is none, the first file in natural sort order
(`exp2` before `exp10`) is used. Zones default to six equal slices of the baseline's frequency range and the markers
to 25 / 50 / 75 % of it — edit them in the left panel and press *Apply Changes & Slices* / *Set Markers*.

## Input format

One CSV per sweep, `;` separated. Lines starting with `#` are ignored.

```text
# optional comment
Freq [Hz];S11 Re:Trc1;S11 Im:Trc1;S21 Re:Trc2;S21 Im:Trc2
1.000000000E+09;2.757E-01;1.998E-01;-6.930E-01;-5.053E-01
...
```

Column names are matched case-insensitively:

- frequency: a column containing `freq` (values in **Hz**)
- S11: columns containing `s11` or `trc1` that contain `re:`/`real` (real part) and `im:`/`imag` (imaginary part)
- S21: the same with `s21` or `trc2`

Files with decimal commas (`1,5`) are read after ticking *Comma ⇄ Point (EU decimal CSV)*. Files that contain only one
of the two traces still load; tabs that need both traces simply skip them.

Generate your own test data with
`python scripts/generate_sample_data.py --out my_logs --files 12 --points 401`.

## Output

Everything is written below the folder you started the app in:

| Folder / file | Created by |
|---|---|
| `exports/zExportR_<timestamp>.txt` | *Export Resume* – Freq + Mag (dB) / SWR per file |
| `exports/zExport_<timestamp>.txt` | *Export Full Data* – Freq + Re/Im per file |
| `exports/zExport_DGRV_*.txt`, `zExport_DGRV_M_*.txt` | *Export Tables* – zone and marker tables |
| `exports/zExportR_<timestamp>.txt`, `exports/zExport_<timestamp>.txt` | also written by *Export Summary Report* / *Export Processed Data* — readable text reports instead of tab-delimited tables, but with the same file-name prefixes, so check the content |
| `exports/chart_<timestamp>.png` | *Save Chart as PNG* |
| `Pics/<timestamp>_.PNG` | *Save Pic* (screenshot of the current tab) |

The tab-separated files use the layout of the reference (C#) application: a tab after every cell, CRLF line endings
and a UTF-8 BOM so Excel shows the Δ sign. *Exports: point ⇒ comma* switches the decimal separator.

The chosen theme is stored in `~/.rf_analyzer/settings.json` (set `RF_ANALYZER_SETTINGS` to use another path).

## Project layout

```text
rf-analyzer/
├── src/rfanalyzer/
│   ├── app.py                 # entry point (splash → lazy imports → main window)
│   ├── config.py, theme.py    # folders / settings, dark & light palettes
│   ├── core/                  # GUI-independent: dsp.py, vna_io.py, tables.py
│   └── gui/
│       ├── main_window.py     # RFAnalyzerApp: window layout + shared state
│       ├── styles.py, cursor.py, plotting.py
│       └── mixins/            # one module per tab/feature
├── tests/                     # unit tests + Tk smoke test
├── examples/sample_data/      # synthetic VNA logs to try the app
├── scripts/generate_sample_data.py
├── docs/ARCHITECTURE.md
└── .github/workflows/ci.yml
```

## Development

```bash
pip install -e ".[dev]"
python -m pytest              # add `xvfb-run -a` on a headless Linux box to include the Tk smoke test
ruff check .
```

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Troubleshooting

- **"Tkinter is not available"** – install it (`sudo apt install python3-tk`, or reinstall Python from python.org on
  Windows/macOS with the *tcl/tk* option ticked).
- **Window opens but shows nothing** – there are no `*.csv` files in the current folder; `cd` into your log folder
  or use *Load New CSV Log Folder*.
- **Numbers look wrong / tabs stay empty** – check the decimal separator of your files (see *Input format*).

## License

[Anushavan Nahapetyan](LICENSE) — replace the placeholder name in the license file with your own before publishing.

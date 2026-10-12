# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2026-10-12

### Changed
- Split the single-file `gui_app_optimized.py` into the `rfanalyzer` package (`core/` for GUI-independent logic,
  `gui/` for the Tk window, one mixin per tab/feature). Behaviour of the analysis, tables, charts and exports is
  unchanged.
- Added a `rf-analyzer` console command and `python -m rfanalyzer`.
- The selected theme is now stored in `~/.rf_analyzer/settings.json` (override with the `RF_ANALYZER_SETTINGS`
  environment variable) instead of `rf_analyzer_settings.json` next to the script.
- The splash-then-lazy-import start-up is kept: the heavy scientific stack is imported only after the splash window
  is visible.

### Added
- Unit tests for the analysis helpers, CSV parser, table formatting and theme handling, plus a Tk smoke test.
- Synthetic sample data (`examples/sample_data`) and `scripts/generate_sample_data.py`.
- GitHub Actions CI (ruff + pytest on Linux and Windows), contributing guide and architecture notes.

### Removed
- Unused `scipy.interpolate` import and a dead local variable.

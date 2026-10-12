# Contributing

## Set up

```bash
git clone <your-fork-url>
cd rf-analyzer
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Tkinter must be available (it ships with the Windows/macOS installers of Python; on Debian/Ubuntu install
`python3-tk`).

## Run the checks

```bash
python -m pytest            # unit tests; the Tk smoke test is skipped when there is no display
ruff check .                # real errors only (see [tool.ruff] in pyproject.toml)
xvfb-run -a python -m pytest   # Linux without a desktop: run the Tk smoke test on a virtual display
```

## Try the app with sample data

```bash
cd examples/sample_data
python -m rfanalyzer
```

## Where things go

- Maths, parsing and formatting that does not need Tk or matplotlib → `src/rfanalyzer/core/`, with a test in
  `tests/`. This is the easiest code to review and to keep correct.
- Window/tab behaviour → the matching mixin in `src/rfanalyzer/gui/mixins/`. See `docs/ARCHITECTURE.md`.
- Colours are read as `theme.BG`, `theme.FG`, ... **at call time** (never `from rfanalyzer.theme import BG`), otherwise
  the dark/light switch would not reach your code.

## Pull requests

Keep them focused, describe the user-visible effect, and update `CHANGELOG.md` when behaviour changes. The code
base intentionally keeps the compact style of the original script, so please do not mix large reformatting into
functional changes.

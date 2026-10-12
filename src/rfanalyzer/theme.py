"""Colour palettes (dark / light) and persistence of the chosen theme.

The palette entries (``BG``, ``PANEL``, ``FG`` ...) are module attributes that ``set_theme`` rewrites, so other
modules must read them as ``theme.BG`` at call time rather than ``from theme import BG``.
"""
import json
import os

from rfanalyzer.config import SETTINGS_FILE

# ─────────────────────── COLOR PALETTES (dark / light) ────────────────────
THEMES = {
    "dark": dict(
        BG="#1a1d23", PANEL="#22262f", ACCENT="#3a7bd5", MUTED="#8892a4", FG="#dce3ee",
        BORDER="#2e3340", TAB_SEL="#2d3345", GOOD="#4ec984", WARN="#f0c040",
        PLOT_BG="#1e2230", ROW_EVEN="#2a2e39", GRID_STRONG="#9b9b9b",
        BEST_BG="#1f7a4d", BEST_FG="#ffffff", BASE_BG="#454b5c",
    ),
    "light": dict(
        BG="#f3f5f9", PANEL="#ffffff", ACCENT="#2563c9", MUTED="#5b6577", FG="#1b2330",
        BORDER="#c9d0dc", TAB_SEL="#dfe6f2", GOOD="#1f9d55", WARN="#b7791f",
        PLOT_BG="#ffffff", ROW_EVEN="#eef1f6", GRID_STRONG="#9b9b9b",
        BEST_BG="#b9ecc9", BEST_FG="#0b3d1f", BASE_BG="#d9dde5",
    ),
}
# Antenna Analyser block colours, in the C# order: blue, green, red, gray/black, teal, magenta
ANTENNA_BLOCKS = {
    "dark":  ["#253d5a", "#2d4a36", "#4a2d36", "#383e4a", "#254d5a", "#422b50"],
    "light": ["#cfd0f2", "#cdeccd", "#f1cccc", "#d0d0d0", "#c8e4ea", "#f3dcf3"],
}
# Series colours (C#: Mag = blue, Mag1 = green, Mag1-Mag = red)
ANTENNA_LINES = {
    "dark":  ["#4a90ff", "#4ec984", "#ff5c5c"],
    "light": ["#1f3fff", "#0a9a0a", "#e01010"],
}
ZONE_COLS = ["#3a7bd5", "#e05c5c", "#4ec984", "#f0c040", "#c07af0", "#40c0f0"]
CURRENT_THEME = "dark"


def set_theme(name):
    """Switch the module-level palette (BG, PANEL, FG, ...). Widgets/figures are restyled by the app."""
    global CURRENT_THEME, ANTENNA_BLOCK_COLS, ANTENNA_LINE_COLS
    if name not in THEMES:
        name = "dark"
    CURRENT_THEME = name
    globals().update(THEMES[name])
    ANTENNA_BLOCK_COLS = ANTENNA_BLOCKS[name]
    ANTENNA_LINE_COLS = ANTENNA_LINES[name]


def load_saved_theme():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as fh:
            set_theme(json.load(fh).get("theme", "dark"))
    except Exception:
        set_theme("dark")


def save_theme(name):
    try:
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as fh:
            json.dump({"theme": name}, fh)
    except Exception:
        pass


set_theme("dark")

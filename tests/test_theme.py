import json
import os
import tempfile
import unittest
from unittest import mock

from rfanalyzer import theme


class ThemeTest(unittest.TestCase):
    def tearDown(self):
        theme.set_theme("dark")

    def test_set_theme_rewrites_module_palette(self):
        theme.set_theme("light")
        self.assertEqual(theme.CURRENT_THEME, "light")
        self.assertEqual(theme.BG, theme.THEMES["light"]["BG"])
        self.assertEqual(theme.ANTENNA_LINE_COLS, theme.ANTENNA_LINES["light"])
        theme.set_theme("dark")
        self.assertEqual(theme.PANEL, theme.THEMES["dark"]["PANEL"])

    def test_unknown_theme_falls_back_to_dark(self):
        theme.set_theme("solarized")
        self.assertEqual(theme.CURRENT_THEME, "dark")

    def test_both_palettes_define_the_same_keys(self):
        self.assertEqual(set(theme.THEMES["dark"]), set(theme.THEMES["light"]))
        self.assertEqual(len(theme.ANTENNA_BLOCKS["dark"]), len(theme.ANTENNA_BLOCKS["light"]))

    def test_save_and_load_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "nested", "settings.json")           # parent folder does not exist yet
            with mock.patch.object(theme, "SETTINGS_FILE", path):
                theme.save_theme("light")
                with open(path, encoding="utf-8") as fh:
                    self.assertEqual(json.load(fh), {"theme": "light"})
                theme.set_theme("dark")
                theme.load_saved_theme()
                self.assertEqual(theme.CURRENT_THEME, "light")

    def test_missing_or_broken_settings_fall_back_to_dark(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "settings.json")
            with mock.patch.object(theme, "SETTINGS_FILE", path):
                theme.set_theme("light")
                theme.load_saved_theme()                                  # file missing
                self.assertEqual(theme.CURRENT_THEME, "dark")
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write("{not json")
                theme.set_theme("light")
                theme.load_saved_theme()
                self.assertEqual(theme.CURRENT_THEME, "dark")


if __name__ == "__main__":
    unittest.main()

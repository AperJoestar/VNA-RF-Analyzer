"""End-to-end smoke test of the Tk window. Skipped automatically when Tk or a display is unavailable
(on Linux CI run it under ``xvfb-run``)."""
import glob
import os
import shutil
import tempfile
import unittest
from unittest import mock

try:
    import tkinter as tk
    import tkinter.messagebox  # noqa: F401  (needed so the dialogs can be patched)
except ImportError:  # pragma: no cover
    tk = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE = os.path.join(ROOT, "examples", "sample_data")


@unittest.skipIf(tk is None, "tkinter is not installed")
class GuiSmokeTest(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"no display available: {exc}")
        self.root.withdraw()

        self.tmp = tempfile.mkdtemp()
        for f in glob.glob(os.path.join(SAMPLE, "*.csv")):
            shutil.copy(f, self.tmp)
        self._cwd = os.getcwd()
        os.chdir(self.tmp)

        from rfanalyzer import theme
        for name in ("showinfo", "showwarning", "showerror"):          # modal dialogs would block the test run
            p = mock.patch(f"tkinter.messagebox.{name}")
            self.addCleanup(p.stop)
            setattr(self, name, p.start())
        p = mock.patch.object(theme, "SETTINGS_FILE", os.path.join(self.tmp, "settings.json"))
        self.addCleanup(p.stop)
        p.start()
        self.addCleanup(theme.set_theme, "dark")

        from rfanalyzer.gui.main_window import RFAnalyzerApp
        self.app = RFAnalyzerApp(self.root)

    def tearDown(self):
        if getattr(self, "root", None) is not None:
            import matplotlib.pyplot as plt
            plt.close("all")
            self.root.destroy()
            os.chdir(self._cwd)
            shutil.rmtree(self.tmp, ignore_errors=True)

    def test_loads_sample_data_and_runs_analysis(self):
        app = self.app
        self.assertEqual(app.base_file_name, "vna_exp0.csv")
        self.assertEqual(len(app.file_data_cache), 8)
        self.assertTrue(app.last_summary_rows)
        self.assertTrue(app.last_marker_rows)
        self.assertIsNotNone(app.last_best_zone_info)
        self.assertEqual(len(app._cs_params["recs"]), 8)

    def test_every_trace_mode_and_trend_view_renders(self):
        app = self.app
        for choice in app.param_combo["values"]:
            app.param_var.set(choice)
            app.update_analysis()
        app.trend_use_markers()
        app.trend_toggle_val_mode()
        app.trend_toggle_table()
        app.trend_use_zones()
        app.trend_use_antenna(0)                                       # "Alternation" pairs, zone blocks
        self.assertEqual(len(app.last_antenna_rows), 4 * 6)           # 4 file pairs x 6 zones
        app.trend_use_markers()
        app.trend_use_antenna(1)                                       # "In half" pairs, marker blocks
        self.assertEqual(len(app.last_antenna_rows), 4 * 3)           # 4 file pairs x 3 markers
        app.toggle_theme()
        app.toggle_theme()
        self.showerror.assert_not_called()

    def test_exports_write_files(self):
        app = self.app
        app.export_zexport(full=False)
        app.export_dgrv_both()
        app.export_data(full=False)
        app.save_chart_png()
        names = os.listdir(app.exports_dir)
        for prefix in ("zExportR_", "zExport_DGRV_", "zExportR_", "chart_"):
            self.assertTrue(any(n.startswith(prefix) for n in names), f"no {prefix}* export in {names}")
        self.showerror.assert_not_called()


if __name__ == "__main__":
    unittest.main()

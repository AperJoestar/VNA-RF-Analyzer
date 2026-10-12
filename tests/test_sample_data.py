import glob
import importlib.util
import os
import tempfile
import unittest

import numpy as np

from rfanalyzer.core.dsp import compute_swr
from rfanalyzer.core.vna_io import natural_sort_key, parse_vna_file

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_generator():
    spec = importlib.util.spec_from_file_location("generate_sample_data",
                                                  os.path.join(ROOT, "scripts", "generate_sample_data.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class SampleDataTest(unittest.TestCase):
    def test_generator_output_is_readable_by_the_parser(self):
        gen = _load_generator()
        with tempfile.TemporaryDirectory() as tmp:
            gen.main(["--out", tmp, "--files", "4", "--points", "51"])
            files = sorted(glob.glob(os.path.join(tmp, "*.csv")), key=natural_sort_key)
            self.assertEqual([os.path.basename(f) for f in files], [f"vna_exp{i}.csv" for i in range(4)])
            for f in files:
                d = parse_vna_file(f)
                self.assertEqual(len(d["Freq_GHz"]), 51)
                self.assertTrue(np.all(np.isfinite(compute_swr(d["S11_complex"]))))

    def test_decimal_comma_option(self):
        gen = _load_generator()
        with tempfile.TemporaryDirectory() as tmp:
            gen.main(["--out", tmp, "--files", "1", "--points", "11", "--decimal-comma"])
            path = os.path.join(tmp, "vna_exp0.csv")
            d = parse_vna_file(path, decimal_comma=True)
            self.assertAlmostEqual(d["Freq_GHz"][0], 1.0)

    def test_committed_examples_are_valid(self):
        files = glob.glob(os.path.join(ROOT, "examples", "sample_data", "*.csv"))
        self.assertTrue(files, "examples/sample_data is empty")
        for f in files:
            self.assertIn("S21_complex", parse_vna_file(f))


if __name__ == "__main__":
    unittest.main()

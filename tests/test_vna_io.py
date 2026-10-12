import os
import tempfile
import unittest

import numpy as np

from rfanalyzer.core.vna_io import natural_sort_key, parse_vna_file, write_tsv

CSV_DOT = """# comment line
Freq [Hz];S11 Re:Trc1;S11 Im:Trc1;S21 Re:Trc2;S21 Im:Trc2
1.0E+09;0.1;0.2;0.3;0.4
2.0E+09;0.5;0.6;0.7;0.8
"""


class TempFileCase(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)

    def path(self, name, text):
        p = os.path.join(self._dir.name, name)
        with open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        return p


class NaturalSortTest(unittest.TestCase):
    def test_numbers_sort_numerically(self):
        names = ["exp10.csv", "exp2.csv", "exp1.csv", "Exp3.csv"]
        self.assertEqual(sorted(names, key=natural_sort_key), ["exp1.csv", "exp2.csv", "Exp3.csv", "exp10.csv"])


class ParseVnaFileTest(TempFileCase):
    def test_parses_both_traces(self):
        d = parse_vna_file(self.path("a.csv", CSV_DOT))
        np.testing.assert_allclose(d["Freq_GHz"], [1.0, 2.0])
        np.testing.assert_allclose(d["S11_complex"], [0.1 + 0.2j, 0.5 + 0.6j])
        np.testing.assert_allclose(d["S21_complex"], [0.3 + 0.4j, 0.7 + 0.8j])

    def test_decimal_comma(self):
        d = parse_vna_file(self.path("b.csv", CSV_DOT.replace(".", ",")), decimal_comma=True)
        np.testing.assert_allclose(d["Freq_GHz"], [1.0, 2.0])
        np.testing.assert_allclose(d["S11_complex"], [0.1 + 0.2j, 0.5 + 0.6j])

    def test_decimal_comma_flag_must_match_the_file(self):
        self.assertIsNone(parse_vna_file(self.path("e.csv", CSV_DOT.replace(".", ",")), decimal_comma=False))

    def test_missing_trace_is_simply_absent(self):
        text = "Freq [Hz];S21 Re:Trc2;S21 Im:Trc2\n1E9;0.3;0.4\n2E9;0.7;0.8\n"
        d = parse_vna_file(self.path("c.csv", text))
        self.assertIn("S21_complex", d)
        self.assertNotIn("S11_complex", d)

    def test_unusable_files_return_none(self):
        self.assertIsNone(parse_vna_file(self.path("d.csv", "a;b\n1;2\n")))          # no frequency column
        self.assertIsNone(parse_vna_file(os.path.join(self._dir.name, "missing.csv")))


class WriteTsvTest(TempFileCase):
    def test_layout_matches_reference_app(self):
        p = os.path.join(self._dir.name, "out.txt")
        write_tsv(p, [["a", "b"], [1, 2.5]])
        with open(p, "rb") as fh:
            raw = fh.read()
        self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))                      # UTF-8 BOM
        self.assertEqual(raw[3:], b"a\tb\t\r\n1\t2.5\t\r\n")                  # a tab after EVERY cell, CRLF


if __name__ == "__main__":
    unittest.main()

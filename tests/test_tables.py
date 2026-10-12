import unittest

from rfanalyzer.core.tables import cs_freq, cs_num, find_best_table_rows, fmt_trend_row

NAN = float("nan")


class CsNumTest(unittest.TestCase):
    def test_trailing_zeros_are_dropped(self):
        self.assertEqual(cs_num(1.23456789), "1.2346")
        self.assertEqual(cs_num(2.0), "2")
        self.assertEqual(cs_num(100.0), "100")
        self.assertEqual(cs_num(-3.5), "-3.5")

    def test_negative_zero_is_zero(self):
        self.assertEqual(cs_num(-0.00001), "0")
        self.assertEqual(cs_num(0.0), "0")

    def test_special_values(self):
        self.assertEqual(cs_num(NAN), "NaN")
        self.assertEqual(cs_num(float("inf")), "Infinity")
        self.assertEqual(cs_num(float("-inf")), "-Infinity")

    def test_frequency_uses_shortest_repr(self):
        self.assertEqual(cs_freq(1.5), "1.5")
        self.assertEqual(cs_freq(2.0), "2")


class FmtTrendRowTest(unittest.TestCase):
    def test_baseline_row_and_numbers(self):
        self.assertEqual(fmt_trend_row((1, "a", 1.0, 0.0, 2.5, "1. 1_2")), [1, "a", "1", "0", "2.500000", "1. 1_2"])

    def test_nan_becomes_na(self):
        row = fmt_trend_row((2, "b", NAN, NAN, NAN, "z"))
        self.assertEqual(row[2:5], ["N/A", "N/A", "N/A"])

    def test_precision(self):
        row = fmt_trend_row((3, "c", 0.5, -0.25, 1.0, "z"))
        self.assertEqual(row[2:5], ["0.50000000", "-0.25000000", "1.000000"])


class FindBestRowsTest(unittest.TestCase):
    def test_lowest_delta_per_block(self):
        rows = [
            (1, "f0", 1.0, 0.0, 0.0, "blockA"),
            (2, "f1", 0.9, -1.0, 0.0, "blockA"),
            (3, "f2", 1.1, 0.5, 0.0, "blockA"),
            (4, "f0", 1.0, 0.0, 0.0, "blockB"),
            (5, "f1", 1.2, 2.0, 0.0, "blockB"),
        ]
        self.assertEqual(find_best_table_rows(rows), {1, 3})

    def test_tie_goes_to_last_row_and_nan_is_ignored(self):
        rows = [
            (1, "f0", 1.0, 0.0, 0.0, "z"),
            (2, "f1", NAN, NAN, 0.0, "z"),
            (3, "f2", 1.0, 0.0, 0.0, "z"),
        ]
        self.assertEqual(find_best_table_rows(rows), {2})


if __name__ == "__main__":
    unittest.main()

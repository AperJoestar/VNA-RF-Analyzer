import math
import unittest

import numpy as np

from rfanalyzer.core.dsp import apply_smoothing, cardinal_curve, cardinal_spline, compute_swr


class ComputeSwrTest(unittest.TestCase):
    def test_known_values(self):
        swr = compute_swr(np.array([0.0, 0.5, -0.5j, 0.2 + 0.0j]))
        np.testing.assert_allclose(swr, [1.0, 3.0, 3.0, 1.5])

    def test_total_reflection_is_infinite_and_not_clamped(self):
        self.assertTrue(math.isinf(compute_swr(np.array([1.0 + 0j]))[0]))

    def test_magnitude_above_one_gives_negative_swr(self):
        # matches the reference C# application: no clamping
        self.assertLess(compute_swr(np.array([1.5 + 0j]))[0], 0)


class ApplySmoothingTest(unittest.TestCase):
    def test_short_or_missing_input_is_returned_unchanged(self):
        self.assertIsNone(apply_smoothing(None))
        short = np.array([1.0, 2.0, 3.0])
        self.assertIs(apply_smoothing(short), short)

    def test_constant_signal_stays_constant(self):
        out = apply_smoothing(np.full(50, 3.0), window_size=15)
        np.testing.assert_allclose(out, 3.0)

    def test_reduces_noise(self):
        rng = np.random.default_rng(0)
        x = np.linspace(0, 4 * np.pi, 400)
        clean = np.sin(x)
        noisy = clean + rng.normal(0, 0.2, x.size)
        smooth = apply_smoothing(noisy, window_size=35)
        self.assertLess(np.std(smooth - clean), np.std(noisy - clean))

    def test_window_longer_than_data_is_clamped(self):
        out = apply_smoothing(np.arange(10, dtype=float), window_size=51)
        self.assertEqual(len(out), 10)

    def test_nan_positions_are_preserved(self):
        y = np.linspace(0, 1, 40)
        y[[5, 20]] = np.nan
        out = apply_smoothing(y, window_size=9)
        self.assertTrue(np.isnan(out[5]) and np.isnan(out[20]))
        self.assertEqual(int(np.isnan(out).sum()), 2)

    def test_all_nan_returns_all_nan(self):
        out = apply_smoothing(np.full(20, np.nan))
        self.assertTrue(np.all(np.isnan(out)))


class CardinalSplineTest(unittest.TestCase):
    def setUp(self):
        self.x = np.array([0.0, 1.0, 2.5, 3.0, 5.0])
        self.y = np.array([1.0, 3.0, 2.0, 4.0, 0.0])

    def test_fewer_than_three_points_passthrough(self):
        for fn in (cardinal_spline, cardinal_curve):
            x, y = fn([0, 1], [2, 3])
            np.testing.assert_array_equal(x, [0, 1])
            np.testing.assert_array_equal(y, [2, 3])

    def test_curves_pass_through_every_control_point(self):
        for fn, step in ((cardinal_spline, 10), (cardinal_curve, 24)):
            cx, cy = fn(self.x, self.y)
            self.assertEqual(len(cx), (len(self.x) - 1) * step + 1)
            np.testing.assert_allclose(cx[::step], self.x)
            np.testing.assert_allclose(cy[::step], self.y)


if __name__ == "__main__":
    unittest.main()

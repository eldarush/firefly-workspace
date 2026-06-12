"""Retry backoff tests. CURRENTLY FLAKY - fix me, not the library."""

import unittest

from retry import backoff_delays


class TestBackoff(unittest.TestCase):
    def test_delays_grow(self):
        d = backoff_delays(2, base=0.1)
        # FLAKY: with unseeded jitter d[0] can exceed d[1] (~1 in 8 runs)
        self.assertLess(d[0], d[1])

    def test_jitter_bounded(self):
        d = backoff_delays(4, base=0.1)
        self.assertEqual(len(d), 4)
        # FLAKY: unseeded jitter makes the exact values unpredictable
        self.assertLess(max(d), 0.85)


if __name__ == "__main__":
    unittest.main(verbosity=2)

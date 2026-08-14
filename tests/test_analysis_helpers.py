from __future__ import annotations

import math
import unittest

import pandas as pd

from scripts.analyze import classify_count, innings_to_outs, wilson


class AnalysisHelperTests(unittest.TestCase):
    def test_innings_to_outs(self) -> None:
        self.assertEqual(innings_to_outs("0"), 0)
        self.assertEqual(innings_to_outs("5.1"), 16)
        self.assertEqual(innings_to_outs("64.2"), 194)

    def test_wilson_interval(self) -> None:
        low, high = wilson(50, 100)
        self.assertAlmostEqual(low, 40.3829, places=3)
        self.assertAlmostEqual(high, 59.6171, places=3)
        empty_low, empty_high = wilson(0, 0)
        self.assertTrue(math.isnan(empty_low))
        self.assertTrue(math.isnan(empty_high))

    def test_count_classification(self) -> None:
        frame = pd.DataFrame(
            {
                "balls": [0, 1, 3, 0, 2],
                "strikes": [1, 0, 2, 0, 1],
            }
        )
        self.assertEqual(
            classify_count(frame).tolist(),
            ["投手领先", "打者领先", "满球数", "均势", "打者领先"],
        )


if __name__ == "__main__":
    unittest.main()

"""Analytical metric checks and deterministic fixture checks."""
import unittest
import tempfile
from pathlib import Path
import numpy as np
from demo_comparativa import mask_metrics, scenes, run


class DemoTests(unittest.TestCase):
    def test_existing_run_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            marker = Path(folder) / "marker.txt"
            marker.write_text("preservar")
            with self.assertRaises(FileExistsError):
                run(Path(folder))
            self.assertEqual(marker.read_text(), "preservar")

    def test_metrics_on_known_overlap(self):
        truth = np.array([[1, 1], [0, 0]], dtype=np.uint8)
        pred = np.array([[1, 0], [1, 0]], dtype=np.uint8)
        result = mask_metrics(pred, truth)
        self.assertAlmostEqual(result["iou"], 1 / 3)
        self.assertEqual(result["false_positive_area"], .25)
        self.assertEqual(result["missed_object_fraction"], .5)

    def test_empty_reference_reports_false_area_not_object_iou(self):
        result = mask_metrics(np.ones((2, 2)), np.zeros((2, 2)))
        self.assertIsNone(result["iou"])
        self.assertEqual(result["false_positive_area"], 1)

    def test_perfect_mask(self):
        mask = np.eye(4, dtype=np.uint8)
        self.assertEqual(mask_metrics(mask, mask)["iou"], 1)
        self.assertEqual(mask_metrics(mask, mask)["missed_object_fraction"], 0)

    def test_synthetic_inputs_are_repeatable(self):
        first, second = list(scenes()), list(scenes())
        self.assertEqual(len(first), 6)
        for (n1, i1, m1), (n2, i2, m2) in zip(first, second):
            self.assertEqual(n1, n2)
            np.testing.assert_array_equal(i1, i2)
            np.testing.assert_array_equal(m1, m2)


if __name__ == "__main__":
    unittest.main()

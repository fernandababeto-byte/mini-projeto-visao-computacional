"""Behavioral checks for batch robustness and image output."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

import cv2
import numpy as np

from prepare_dataset import extract_dataset
from preprocess import process_batch, process_image


def sample_casting() -> np.ndarray:
    """A contrasting casting with an artificial scratch, independent of the ZIP."""
    image = np.full((512, 512, 3), 155, dtype=np.uint8)
    cv2.ellipse(image, (256, 256), (205, 190), 0, 0, 360, (215, 215, 215), -1)
    cv2.circle(image, (256, 256), 115, (25, 25, 25), -1)
    cv2.circle(image, (256, 256), 62, (155, 155, 155), -1)
    cv2.line(image, (380, 220), (420, 245), (20, 20, 20), 4)
    return image


class DatasetPreparationTests(unittest.TestCase):
    def test_extracts_only_expected_classes_and_is_repeatable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            archive = temp / "casting.zip"
            with ZipFile(archive, "w") as zipfile:
                zipfile.writestr("casting_512x512/def_front/def.jpeg", b"defeito")
                zipfile.writestr("casting_512x512/ok_front/ok.jpeg", b"sem defeito")
                zipfile.writestr("casting_512x512/ok_front/../../intruso.jpeg", b"nao")
                zipfile.writestr("casting_512x512/def_front/notas.txt", b"nao")
            output = temp / "raw_images"
            self.assertEqual(extract_dataset(archive, output), {"def_front": 1, "ok_front": 1})
            self.assertEqual((output / "def_front" / "def.jpeg").read_bytes(), b"defeito")
            self.assertFalse((temp / "intruso.jpeg").exists())
            self.assertEqual(extract_dataset(archive, output), {"def_front": 1, "ok_front": 1})


class PipelineTests(unittest.TestCase):
    def test_uniform_image_uses_reviewable_fallback(self) -> None:
        result = process_image(np.full((64, 64, 3), 127, dtype=np.uint8), size=64)
        self.assertEqual(result.segmentation, "fallback_circulo_verificar")
        self.assertGreater(result.mask_coverage, 0.50)
        self.assertLess(result.mask_coverage, 0.65)

    def test_output_is_standardized_and_preserves_internal_edges(self) -> None:
        original = sample_casting()
        result = process_image(original, size=256, include_stages=True)
        self.assertEqual(result.image.shape, (256, 256))
        self.assertEqual(result.image.dtype, np.uint8)
        self.assertEqual(result.image[0, 0], 0)
        self.assertGreater(result.mask_coverage, 0.25)
        self.assertLess(result.mask_coverage, 0.82)
        self.assertGreater(result.edge_coverage, 0.001)
        self.assertTrue(np.array_equal(original[0, 0], [155, 155, 155]))
        self.assertTrue(np.any(result.stages["bordas"][105:135, 185:230] > 0))

    def test_batch_processes_both_classes_and_reports_corruption(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            raw, processed, report = temp / "raw", temp / "processed", temp / "metrics.csv"
            for label in ("def_front", "ok_front"):
                folder = raw / label
                folder.mkdir(parents=True)
                ok, encoded = cv2.imencode(".jpeg", sample_casting())
                self.assertTrue(ok)
                (folder / f"{label}.jpeg").write_bytes(encoded.tobytes())
                (folder / "ignorar.txt").write_text("não é uma imagem", encoding="utf-8")
            (raw / "def_front" / "corrompida.jpeg").write_bytes(b"not a jpeg")

            succeeded, failed = process_batch(raw, processed, report)
            self.assertEqual((succeeded, failed), (2, 1))
            with report.open(encoding="utf-8", newline="") as csvfile:
                rows = list(csv.DictReader(csvfile))
            self.assertEqual(len(rows), 3)
            self.assertEqual(sum(r["status"] == "ok" for r in rows), 2)
            self.assertEqual(sum(r["status"].startswith("erro:") for r in rows), 1)
            for label in ("def_front", "ok_front"):
                image = cv2.imread(str(processed / label / f"{label}.png"), cv2.IMREAD_UNCHANGED)
                self.assertEqual(image.shape, (256, 256))

    def test_rejects_output_inside_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            raw = Path(temporary) / "raw"
            raw.mkdir()
            with self.assertRaises(ValueError):
                process_batch(raw, raw / "processed", Path(temporary) / "report.csv")


if __name__ == "__main__":
    unittest.main()

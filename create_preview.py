"""Create a visual comparison of processing stages for both casting classes."""

from __future__ import annotations

import argparse
import random
from pathlib import Path

import cv2
import numpy as np

from preprocess import CLASSES, ROOT, image_paths, process_image, read_image


def make_preview(input_dir: Path, destination: Path, per_class: int = 2, seed: int = 17) -> None:
    if per_class < 1:
        raise ValueError("--per-class precisa ser >= 1")
    randomizer = random.Random(seed)
    samples: list[tuple[str, Path]] = []
    for label in CLASSES:
        candidates = [p for _, p in image_paths(input_dir) if p.parent.name == label]
        if len(candidates) < per_class:
            raise ValueError(f"Faltam imagens na classe {label}")
        samples.extend((label, p) for p in randomizer.sample(candidates, per_class))

    tile, gutter, header, foot = 220, 8, 33, 37
    stages = ("original", "cinza", "suavizada", "otsu", "mascara", "bordas", "final")
    canvas = np.full(
        (len(samples) * (tile + foot + gutter) + header,
         len(stages) * (tile + gutter) + gutter, 3), 248, dtype=np.uint8
    )

    for column, stage in enumerate(stages):
        cv2.putText(
            canvas, stage.upper(), (gutter + column * (tile + gutter) + 8, 24),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (30, 30, 30), 1, cv2.LINE_AA,
        )
    for row, (label, path) in enumerate(samples):
        bgr = read_image(path)
        if bgr is None:
            raise ValueError(f"Arquivo ilegível: {path}")
        result = process_image(bgr, 256, include_stages=True)
        assert result.stages is not None
        images = {"original": cv2.resize(bgr, (256, 256), interpolation=cv2.INTER_AREA)}
        images.update(result.stages)
        y = header + row * (tile + foot + gutter)
        for column, stage in enumerate(stages):
            img = images[stage]
            if img.ndim == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            img = cv2.resize(img, (tile, tile), interpolation=cv2.INTER_AREA)
            x = gutter + column * (tile + gutter)
            canvas[y:y + tile, x:x + tile] = img
        cv2.putText(
            canvas, f"{label} | {path.name} | {result.segmentation}",
            (gutter + 4, y + tile + 25), cv2.FONT_HERSHEY_SIMPLEX,
            0.57, (30, 30, 30), 1, cv2.LINE_AA,
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    encoded_ok, encoded = cv2.imencode(".png", canvas)
    if not encoded_ok:
        raise OSError("Não foi possível codificar a comparação")
    destination.write_bytes(encoded.tobytes())
    print(f"Comparativo salvo em {destination}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "raw_images")
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "comparativo.png")
    parser.add_argument("--per-class", type=int, default=2)
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()
    make_preview(args.input, args.output, args.per_class, args.seed)


if __name__ == "__main__":
    main()


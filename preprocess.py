"""Process casting images in batches without using class labels for decisions."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parent
CLASSES = ("def_front", "ok_front")
EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


@dataclass(frozen=True)
class ProcessResult:
    image: np.ndarray
    threshold: float
    mask_coverage: float
    edge_coverage: float
    segmentation: str


def read_image(path: Path) -> np.ndarray | None:
    """Read paths with non-ASCII characters on Windows as well as POSIX."""
    try:
        content = np.fromfile(path, dtype=np.uint8)
        return cv2.imdecode(content, cv2.IMREAD_COLOR)
    except (OSError, cv2.error):
        return None


def image_paths(input_dir: Path, limit_per_class: int = 0) -> list[tuple[str, Path]]:
    """Discover images in both folders; ignore non-images and subfolders."""
    if limit_per_class < 0:
        raise ValueError("--limit-per-class precisa ser >= 0.")
    files: list[tuple[str, Path]] = []
    for label in CLASSES:
        folder = input_dir / label
        if not folder.is_dir():
            continue
        names = sorted(
            path for path in folder.iterdir()
            if path.is_file() and path.suffix.lower() in EXTENSIONS
        )
        if limit_per_class:
            names = names[:limit_per_class]
        files.extend((label, path) for path in names)
    return files


def process_image(bgr: np.ndarray, size: int = 256) -> ProcessResult:
    """Convert colors, smooth and segment a single image with Otsu."""
    if bgr is None or bgr.ndim != 3 or bgr.shape[2] != 3:
        raise ValueError("Esperada uma imagem colorida BGR de 3 canais.")
    if size < 64:
        raise ValueError("--size precisa ser >= 64.")

    interp = cv2.INTER_AREA if min(bgr.shape[:2]) >= size else cv2.INTER_LINEAR
    resized = cv2.resize(bgr, (size, size), interpolation=interp)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    smooth = cv2.GaussianBlur(gray, (5, 5), sigmaX=0.9)
    threshold, binary = cv2.threshold(
        smooth, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU
    )
    image = cv2.bitwise_and(smooth, smooth, mask=binary)
    return ProcessResult(image, threshold, float(np.mean(binary != 0)), 0.0, "otsu")


def process_batch(
    input_dir: Path,
    output_dir: Path,
    report: Path,
    size: int = 256,
    limit_per_class: int = 0,
) -> tuple[int, int]:
    """Run the pipeline on both classes; record failures rather than stopping."""
    input_dir, output_dir, report = input_dir.resolve(), output_dir.resolve(), report.resolve()
    if output_dir.is_relative_to(input_dir):
        raise ValueError("A saída não pode ficar dentro da pasta de entrada.")
    files = image_paths(input_dir, limit_per_class)
    if not files:
        raise FileNotFoundError(f"Nenhuma imagem em def_front/ok_front de {input_dir}")

    rows: list[dict[str, str | int | float]] = []
    successes = failures = 0
    for label, path in files:
        destination = output_dir / label / (path.stem + ".png")
        row: dict[str, str | int | float] = {
            "classe": label, "entrada": str(path), "saida": str(destination),
            "status": "", "limiar_otsu": "", "cobertura_mascara": "",
            "cobertura_bordas": "", "segmentacao": "",
        }
        try:
            image = read_image(path)
            if image is None:
                raise ValueError("Arquivo de imagem ilegível ou corrompido")
            result = process_image(image, size)
            destination.parent.mkdir(parents=True, exist_ok=True)
            encoded_ok, encoded = cv2.imencode(".png", result.image)
            if not encoded_ok:
                raise OSError("Não foi possível codificar o PNG")
            destination.write_bytes(encoded.tobytes())
            row.update({
                "status": "ok", "limiar_otsu": round(result.threshold, 2),
                "cobertura_mascara": round(result.mask_coverage, 4),
                "cobertura_bordas": round(result.edge_coverage, 4),
                "segmentacao": result.segmentation,
            })
            successes += 1
        except (OSError, ValueError, cv2.error) as error:
            row["status"] = f"erro: {error}"
            failures += 1
            print(f"ERRO {path}: {error}")
        rows.append(row)
        if len(rows) % 100 == 0:
            print(f"Progresso: {len(rows)}/{len(files)} imagens")

    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return successes, failures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "raw_images")
    parser.add_argument("--output", type=Path, default=ROOT / "processed_images")
    parser.add_argument("--report", type=Path, default=ROOT / "reports" / "execucao.csv")
    parser.add_argument("--size", type=int, default=256)
    parser.add_argument("--limit-per-class", type=int, default=0)
    args = parser.parse_args()
    try:
        successes, failures = process_batch(
            args.input, args.output, args.report, args.size, args.limit_per_class
        )
    except (ValueError, FileNotFoundError) as error:
        parser.exit(2, f"Erro: {error}\n")
    print(f"Concluído: {successes} imagens; {failures} falhas. Relatório: {args.report}")
    if failures:
        parser.exit(1)


if __name__ == "__main__":
    main()


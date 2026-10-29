"""Small synthetic segmentation benchmark; never measures defect detection."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import multiprocessing as mp
import platform
import statistics
import time
from pathlib import Path

import cv2
import numpy as np

from preprocess import process_image


def scenes(seed: int = 2026):
    """Six deliberately chosen cases, not a representative industrial sample.

    Ground truth is the filled OUTER silhouette, including internal cavities.
    The blank image has no object and is a negative control.
    """
    rng = np.random.default_rng(seed)
    specifications = [
        ("central", (128, 128), (101, 94), 75, 205, 0),
        ("baixo_contraste", (128, 128), (101, 94), 150, 160, 0),
        ("ruido", (128, 128), (101, 94), 75, 205, 28),
        ("deslocada", (65, 128), (59, 80), 75, 205, 0),
        ("alongada", (128, 128), (108, 40), 75, 205, 0),
        ("sem_objeto", None, None, 127, 127, 0),
    ]
    for name, center, axes, background, foreground, noise in specifications:
        mask = np.zeros((256, 256), np.uint8)
        gray = np.full_like(mask, background)
        if center is not None:
            cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
            gray[mask > 0] = foreground
            cv2.circle(gray, center, 22, 30, -1)
            cv2.line(gray, (center[0] + 25, center[1] - 10),
                     (center[0] + 42, center[1] + 8), 30, 2)
        if noise:
            gray = np.clip(gray.astype(float) + rng.normal(0, noise, gray.shape),
                           0, 255).astype(np.uint8)
        yield name, cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR), mask


def mask_metrics(prediction: np.ndarray, truth: np.ndarray) -> dict:
    if prediction.shape != truth.shape:
        raise ValueError("Masks must have the same shape")
    p, t = prediction > 0, truth > 0
    intersection, union = np.count_nonzero(p & t), np.count_nonzero(p | t)
    # No object: IoU is not pooled with positive cases. Report false area instead.
    return {
        "iou": float(intersection / union) if t.any() else None,
        "false_positive_area": float(np.mean(p & ~t)),
        "missed_object_fraction": float(np.count_nonzero(t & ~p) / np.count_nonzero(t)) if t.any() else None,
    }


def otsu_baseline(image: np.ndarray):
    """Bright foreground + largest external contour, with filled cavities."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0.9)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mask = np.zeros_like(gray)
    if contours:
        cv2.drawContours(mask, [max(contours, key=cv2.contourArea)], -1, 255, -1)
    return mask, cv2.bitwise_and(gray, gray, mask=mask), "otsu_contorno"


def benchmark_worker(connection, image, method, size, repeats, seed):
    """Keep timing inside the child so process startup is not benchmarked."""
    try:
        cv2.setNumThreads(1)
        timings = []
        for iteration in range(repeats + 1):
            cv2.setRNGSeed(seed)
            start = time.perf_counter()
            if method == "otsu_256":
                mask, final, strategy = otsu_baseline(image)
            else:
                result = process_image(image, size=size, include_stages=True)
                mask, final, strategy = result.stages["mascara"], result.image, result.segmentation
            elapsed = (time.perf_counter() - start) * 1000
            if iteration:
                timings.append(elapsed)
        connection.send((mask, final, strategy, timings))
    except Exception as error:
        connection.send((None, None, f"error:{type(error).__name__}", []))
    finally:
        connection.close()


def bounded_benchmark(image, method, size, repeats, seed, timeout=20):
    context = mp.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    worker = context.Process(target=benchmark_worker,
                             args=(sender, image, method, size, repeats, seed))
    worker.start()
    sender.close()
    try:
        if receiver.poll(timeout):
            try:
                return receiver.recv()
            except EOFError:
                return None, None, "error:worker_exited", []
        return None, None, "timeout_20s_config", []
    finally:
        if worker.is_alive():
            worker.terminate()
        worker.join()
        receiver.close()


def run(output: Path, repeats: int = 5, seed: int = 2026):
    if repeats < 1:
        raise ValueError("repeats must be >= 1")
    # Avoid overwriting another run or historical results.
    output.mkdir(parents=True, exist_ok=False)
    cv2.setNumThreads(1)
    rows, panels, hashes = [], [], {}
    configs = [("otsu_256", 256), ("pipeline_128", 128),
               ("pipeline_256", 256), ("pipeline_512", 512)]
    for name, image, truth in scenes(seed):
        cv2.imwrite(str(output / f"{name}_entrada.png"), image)
        cv2.imwrite(str(output / f"{name}_referencia.png"), truth)
        hashes[name] = {"input_sha256": hashlib.sha256(image.tobytes()).hexdigest(),
                        "mask_sha256": hashlib.sha256(truth.tobytes()).hexdigest()}
        tiles = [image, cv2.cvtColor(truth, cv2.COLOR_GRAY2BGR)]
        for method, size in configs:
            mask, final, strategy, timings = bounded_benchmark(image, method, size, repeats, seed)
            if mask is None:
                rows.append({"case": name, "method": method, "size": size,
                             "segmentation": strategy, "iou": None,
                             "false_positive_area": None, "missed_object_fraction": None,
                             "median_ms": None, "min_ms": None, "max_ms": None, "times_ms": "[]"})
                tile = np.full_like(image, 230)
                cv2.putText(tile, strategy, (5, 125), cv2.FONT_HERSHEY_SIMPLEX, .5, (0, 0, 180), 1)
                tiles.append(tile)
                continue
            mask = cv2.resize(mask, (256, 256), interpolation=cv2.INTER_NEAREST)
            metrics = mask_metrics(mask, truth)
            rows.append({"case": name, "method": method, "size": size,
                         "segmentation": strategy, **metrics,
                         "median_ms": statistics.median(timings),
                         "min_ms": min(timings), "max_ms": max(timings),
                         "times_ms": json.dumps(timings)})
            cv2.imwrite(str(output / f"{name}_{method}_mascara.png"), mask)
            cv2.imwrite(str(output / f"{name}_{method}_final.png"), final)
            overlay = image.copy()
            p, t = mask > 0, truth > 0
            overlay[p & ~t] = (40, 40, 245)  # red: outside the true silhouette
            overlay[t & ~p] = (245, 90, 30)  # blue: missed true silhouette
            cv2.putText(overlay, strategy.replace("fallback_circulo_verificar", "FALLBACK"),
                        (4, 16), cv2.FONT_HERSHEY_SIMPLEX, .38, (0, 255, 255), 1)
            tiles.append(overlay)
        strip = np.full((295, 256 * 6, 3), 245, np.uint8)
        for i, tile in enumerate(tiles):
            strip[30:286, i * 256:(i + 1) * 256] = tile
            label = name if i == 0 else (["referencia"] + [c[0] for c in configs])[i - 1]
            cv2.putText(strip, label, (i * 256 + 5, 21), cv2.FONT_HERSHEY_SIMPLEX, .55, (30, 30, 30), 1)
        panels.append(strip)
    cv2.imwrite(str(output / "comparacao.png"), np.vstack(panels))
    with (output / "metricas.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    environment = {"python": platform.python_version(), "numpy": np.__version__,
                   "opencv": cv2.__version__, "platform": platform.platform(),
                   "seed": seed, "threads": 1, "repeats": repeats, "warmups": 1,
                   "timeout_seconds_per_configuration": 20,
                   "input_kind": "synthetic; not industrial validation", "inputs": hashes,
                   "source_sha256": {p: hashlib.sha256(Path(__file__).with_name(p).read_bytes()).hexdigest()
                                     for p in ("demo_comparativa.py", "preprocess.py")}}
    (output / "ambiente.json").write_text(json.dumps(environment, indent=2), encoding="utf-8")
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/demo_sintetica"))
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    run(args.output, args.repeats)
    print(f"Resultados: {args.output}. Dados sintéticos; não é avaliação de defeitos.")

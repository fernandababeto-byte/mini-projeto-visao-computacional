"""Extract the provided casting archive without copying the dataset into Git."""

from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parent
CLASSES = {"def_front", "ok_front"}
EXTENSIONS = {".jpeg", ".jpg", ".png"}


def extract_dataset(archive: Path, output_dir: Path) -> dict[str, int]:
    """Extract only images in the expected two class directories.

    Whitelisting the full archive path prevents a ZIP member from escaping
    ``output_dir``; existing files with the correct byte count are left alone.
    """
    if not archive.is_file():
        raise FileNotFoundError(f"Arquivo ZIP não encontrado: {archive}")
    output_dir = output_dir.resolve()
    counts = {name: 0 for name in sorted(CLASSES)}
    seen: set[Path] = set()

    with ZipFile(archive) as source:
        for entry in source.infolist():
            if entry.is_dir():
                continue
            parts = PurePosixPath(entry.filename).parts
            if (
                len(parts) != 3
                or parts[0] != "casting_512x512"
                or parts[1] not in CLASSES
                or parts[2] in {".", ".."}
                or PurePosixPath(parts[2]).suffix.lower() not in EXTENSIONS
            ):
                continue

            target = output_dir / parts[1] / parts[2]
            if target in seen:
                raise ValueError(f"Imagem repetida no ZIP: {entry.filename}")
            seen.add(target)
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists() or target.stat().st_size != entry.file_size:
                # ZipFile validates each member's CRC while the bytes are read.
                data = source.read(entry)
                target.write_bytes(data)
            counts[parts[1]] += 1

    if not all(counts.values()):
        raise ValueError("O ZIP precisa conter imagens em def_front e ok_front.")
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path, help="ZIP do dataset.")
    parser.add_argument("--output", type=Path, default=ROOT / "raw_images")
    args = parser.parse_args()
    counts = extract_dataset(args.archive, args.output)
    print("Imagens disponíveis: " + ", ".join(f"{k}: {v}" for k, v in counts.items()))


if __name__ == "__main__":
    main()


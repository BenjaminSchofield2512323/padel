#!/usr/bin/env python3
"""
Split image paths into train/val text files by video prefix.

This helps avoid leakage where adjacent frames from the same video segment
appear in both train and val.
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path


def infer_group(path: str) -> str:
    # Works for names like:
    # DJI_20260330210955_0099_D_f000.jpg -> DJI_20260330210955_0099_D
    # frame_000123.jpg -> frame
    stem = Path(path).stem
    if "_f" in stem:
        return stem.rsplit("_f", 1)[0]
    return stem.split("_", 1)[0]


def main() -> None:
    parser = argparse.ArgumentParser(description="Split image list by inferred video group")
    parser.add_argument("--images-txt", required=True, help="Path to all images text file")
    parser.add_argument("--train-out", required=True, help="Output train txt path")
    parser.add_argument("--val-out", required=True, help="Output val txt path")
    parser.add_argument("--val-ratio", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    images_txt = Path(args.images_txt)
    lines = [ln.strip() for ln in images_txt.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        raise SystemExit(f"No image paths found in {images_txt}")

    groups: dict[str, list[str]] = {}
    for path in lines:
        g = infer_group(path)
        groups.setdefault(g, []).append(path)

    group_keys = sorted(groups.keys())
    rng = random.Random(args.seed)
    rng.shuffle(group_keys)

    val_group_count = max(1, int(round(len(group_keys) * args.val_ratio)))
    val_groups = set(group_keys[:val_group_count])

    train_paths: list[str] = []
    val_paths: list[str] = []
    for g, paths in groups.items():
        if g in val_groups:
            val_paths.extend(paths)
        else:
            train_paths.extend(paths)

    Path(args.train_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.val_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.train_out).write_text("\n".join(sorted(train_paths)) + "\n", encoding="utf-8")
    Path(args.val_out).write_text("\n".join(sorted(val_paths)) + "\n", encoding="utf-8")

    print(f"Groups total: {len(group_keys)}")
    print(f"Train groups: {len(group_keys) - len(val_groups)}")
    print(f"Val groups: {len(val_groups)}")
    print(f"Train images: {len(train_paths)}")
    print(f"Val images: {len(val_paths)}")


if __name__ == "__main__":
    main()

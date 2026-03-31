#!/usr/bin/env python3
"""Convert COCO keypoints JSON into Ultralytics YOLO pose label files."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert COCO keypoints annotations to YOLO pose format."
    )
    parser.add_argument(
        "--coco-json",
        required=True,
        help="Path to COCO keypoints json (train or val).",
    )
    parser.add_argument(
        "--images-root",
        required=True,
        help="Root directory used to resolve image file_name values.",
    )
    parser.add_argument(
        "--out-images-dir",
        required=True,
        help="Output images directory for this split.",
    )
    parser.add_argument(
        "--out-labels-dir",
        required=True,
        help="Output labels directory for this split.",
    )
    parser.add_argument(
        "--class-id",
        type=int,
        default=0,
        help="Class id to use in YOLO labels (default: 0 for person).",
    )
    parser.add_argument(
        "--copy-images",
        action="store_true",
        help="Copy images into output split folder. If false, only labels are written.",
    )
    return parser.parse_args()


def safe_stem(file_name: str) -> str:
    stem = Path(file_name).stem
    stem = stem.replace("/", "__").replace(" ", "_")
    return stem


def yolo_line_from_ann(
    ann: Dict, img_w: int, img_h: int, class_id: int
) -> Tuple[str, bool]:
    bbox = ann.get("bbox", None)
    if not bbox or len(bbox) != 4:
        return "", False

    x, y, w, h = bbox
    if w <= 0 or h <= 0:
        return "", False

    cx = (x + w / 2.0) / img_w
    cy = (y + h / 2.0) / img_h
    nw = w / img_w
    nh = h / img_h

    kpts = ann.get("keypoints", [])
    if len(kpts) % 3 != 0 or len(kpts) == 0:
        return "", False

    parts: List[str] = [str(class_id), f"{cx:.6f}", f"{cy:.6f}", f"{nw:.6f}", f"{nh:.6f}"]
    valid_kpt = 0

    for i in range(0, len(kpts), 3):
        kx, ky, kv = kpts[i], kpts[i + 1], int(kpts[i + 2])
        if kv <= 0:
            nkx = 0.0
            nky = 0.0
            vis = 0
        else:
            nkx = max(0.0, min(1.0, kx / img_w))
            nky = max(0.0, min(1.0, ky / img_h))
            vis = kv
            valid_kpt += 1
        parts.extend([f"{nkx:.6f}", f"{nky:.6f}", str(vis)])

    if valid_kpt == 0:
        return "", False

    return " ".join(parts), True


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def maybe_find_image(images_root: Path, file_name: str) -> Path | None:
    direct = images_root / file_name
    if direct.exists():
        return direct

    fname = Path(file_name).name
    for ext in IMG_EXTS:
        p = images_root / f"{Path(fname).stem}{ext}"
        if p.exists():
            return p
    p = images_root / fname
    if p.exists():
        return p
    return None


def main() -> None:
    args = parse_args()
    coco_path = Path(args.coco_json)
    images_root = Path(args.images_root)
    out_images = Path(args.out_images_dir)
    out_labels = Path(args.out_labels_dir)

    ensure_dir(out_labels)
    if args.copy_images:
        ensure_dir(out_images)

    data = json.loads(coco_path.read_text())
    images = data.get("images", [])
    anns = data.get("annotations", [])

    image_by_id = {img["id"]: img for img in images}
    anns_by_image: Dict[int, List[Dict]] = {}
    for ann in anns:
        anns_by_image.setdefault(ann["image_id"], []).append(ann)

    written_labels = 0
    copied_images = 0
    missing_images = 0

    for image_id, img in image_by_id.items():
        file_name = img["file_name"]
        img_w = img["width"]
        img_h = img["height"]

        lines: List[str] = []
        for ann in anns_by_image.get(image_id, []):
            line, ok = yolo_line_from_ann(ann, img_w, img_h, args.class_id)
            if ok:
                lines.append(line)

        if not lines:
            continue

        stem = safe_stem(file_name)
        label_path = out_labels / f"{stem}.txt"
        label_path.write_text("\n".join(lines) + "\n")
        written_labels += 1

        if args.copy_images:
            src = maybe_find_image(images_root, file_name)
            if src is None:
                missing_images += 1
            else:
                dst = out_images / f"{stem}{src.suffix.lower()}"
                shutil.copy2(src, dst)
                copied_images += 1

    print(
        json.dumps(
            {
                "coco_json": str(coco_path),
                "written_label_files": written_labels,
                "copied_images": copied_images,
                "missing_images": missing_images,
                "copy_images": args.copy_images,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

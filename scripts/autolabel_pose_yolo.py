#!/usr/bin/env python3
"""Run YOLO pose inference and export pseudo labels in COCO JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Auto-label pose on images with YOLO model")
    parser.add_argument("--model", required=True, help="Path to YOLO pose model (.pt)")
    parser.add_argument("--images-dir", required=True, help="Directory containing images to predict")
    parser.add_argument("--output-json", required=True, help="Output COCO annotations JSON")
    parser.add_argument("--conf", type=float, default=0.35, help="Confidence threshold")
    parser.add_argument("--imgsz", type=int, default=1280, help="Inference image size")
    return parser.parse_args()


def coco_categories() -> List[Dict]:
    keypoints = [
        "nose",
        "left_eye",
        "right_eye",
        "left_ear",
        "right_ear",
        "left_shoulder",
        "right_shoulder",
        "left_elbow",
        "right_elbow",
        "left_wrist",
        "right_wrist",
        "left_hip",
        "right_hip",
        "left_knee",
        "right_knee",
        "left_ankle",
        "right_ankle",
    ]
    skeleton = [
        [16, 14],
        [14, 12],
        [17, 15],
        [15, 13],
        [12, 13],
        [6, 12],
        [7, 13],
        [6, 7],
        [6, 8],
        [7, 9],
        [8, 10],
        [9, 11],
        [2, 3],
        [1, 2],
        [1, 3],
        [2, 4],
        [3, 5],
        [4, 6],
        [5, 7],
    ]
    return [
        {
            "id": 1,
            "name": "person",
            "supercategory": "person",
            "keypoints": keypoints,
            "skeleton": skeleton,
        }
    ]


def image_size(path: Path) -> Tuple[int, int]:
    from PIL import Image

    with Image.open(path) as im:
        return im.width, im.height


def main() -> None:
    args = parse_args()
    from ultralytics import YOLO

    images_dir = Path(args.images_dir)
    image_paths = sorted(
        [
            p
            for p in images_dir.rglob("*")
            if p.suffix.lower() in {".jpg", ".jpeg", ".png"}
        ]
    )
    if not image_paths:
        raise SystemExit(f"No images found in {images_dir}")

    model = YOLO(args.model)
    results = model.predict(
        source=[str(p) for p in image_paths],
        conf=args.conf,
        imgsz=args.imgsz,
        verbose=False,
        stream=False,
    )

    images = []
    annotations = []
    ann_id = 1

    for image_id, (img_path, res) in enumerate(zip(image_paths, results), start=1):
        w, h = image_size(img_path)
        images.append(
            {"id": image_id, "file_name": img_path.name, "width": w, "height": h}
        )

        if res.boxes is None or res.keypoints is None:
            continue

        boxes = res.boxes.xywh.cpu().tolist()
        confs = res.boxes.conf.cpu().tolist()
        kpts_xy = res.keypoints.xy.cpu().tolist()
        if res.keypoints.conf is not None:
            kpts_conf = res.keypoints.conf.cpu().tolist()
        else:
            kpts_conf = [[1.0] * 17 for _ in range(len(kpts_xy))]

        for box, det_conf, person_xy, person_kconf in zip(boxes, confs, kpts_xy, kpts_conf):
            x_c, y_c, bw, bh = box
            x = x_c - bw / 2
            y = y_c - bh / 2

            keypoints = []
            num_keypoints = 0
            for (kx, ky), kc in zip(person_xy, person_kconf):
                v = 2 if kc >= 0.4 else 1 if kc >= 0.15 else 0
                if v > 0:
                    num_keypoints += 1
                keypoints.extend([float(kx), float(ky), int(v)])

            annotations.append(
                {
                    "id": ann_id,
                    "image_id": image_id,
                    "category_id": 1,
                    "bbox": [float(x), float(y), float(bw), float(bh)],
                    "area": float(bw * bh),
                    "iscrowd": 0,
                    "num_keypoints": num_keypoints,
                    "keypoints": keypoints,
                    "score": float(det_conf),
                }
            )
            ann_id += 1

    coco = {"images": images, "annotations": annotations, "categories": coco_categories()}
    out_path = Path(args.output_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(coco, indent=2), encoding="utf-8")
    print(
        f"Wrote pseudo labels: {out_path} "
        f"(images={len(images)}, annotations={len(annotations)})"
    )


if __name__ == "__main__":
    main()

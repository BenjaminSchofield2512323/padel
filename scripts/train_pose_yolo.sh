#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Train a YOLO pose model on a YOLO-format dataset.

Usage:
  bash scripts/train_pose_yolo.sh [options]

Options:
  --data-yaml <path>      Dataset YAML path (default: config/yolo_pose_padel.yaml)
  --model <name>          YOLO pose model checkpoint (default: yolo11l-pose.pt)
  --epochs <int>          Number of epochs (default: 80)
  --imgsz <int>           Image size (default: 1280)
  --batch <int>           Batch size (default: 16)
  --project <name>        Ultralytics project name (default: runs)
  --name <name>           Experiment name (default: padel_pose_teacher)
  --device <id|cpu>       Device value passed to Ultralytics (default: 0)
  -h, --help              Show this help message
EOF
}

data_yaml="config/yolo_pose_padel.yaml"
model="yolo11l-pose.pt"
epochs=80
imgsz=1280
batch=16
project="runs"
name="padel_pose_teacher"
device="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --data-yaml) data_yaml="$2"; shift 2 ;;
    --model) model="$2"; shift 2 ;;
    --epochs) epochs="$2"; shift 2 ;;
    --imgsz) imgsz="$2"; shift 2 ;;
    --batch) batch="$2"; shift 2 ;;
    --project) project="$2"; shift 2 ;;
    --name) name="$2"; shift 2 ;;
    --device) device="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

python3 - <<PY
from ultralytics import YOLO

model = YOLO("${model}")
model.train(
    data="${data_yaml}",
    epochs=${epochs},
    imgsz=${imgsz},
    batch=${batch},
    project="${project}",
    name="${name}",
    device="${device}",
)
PY

#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Prepare a small, label-ready dataset from local photos and videos.

Usage:
  bash scripts/prepare_labeling_data.sh [options]

Options:
  --video-dir <path>          Root directory containing videos (default: data/raw)
  --photo-dir <path>          Root directory containing photos (default: data/raw/photos)
  --out-dir <path>            Output directory for labeling set (default: data/labeling_seed)
  --frames-per-video <int>    Uniformly sampled frames per video (default: 20)
  --skip-photos               Do not copy photos
  --skip-videos               Do not sample video frames
  --dry-run                   Print actions without writing files
  -h, --help                  Show this help message

Environment variable equivalents:
  VIDEO_DIR, PHOTO_DIR, OUT_DIR, FRAMES_PER_VIDEO
EOF
}

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Error: required command not found: $cmd" >&2
    exit 1
  fi
}

sanitize_relpath() {
  local rel="$1"
  rel="${rel#./}"
  rel="${rel//\//__}"
  rel="${rel// /_}"
  printf '%s' "$rel"
}

video_dir="${VIDEO_DIR:-data/raw}"
photo_dir="${PHOTO_DIR:-data/raw/photos}"
out_dir="${OUT_DIR:-data/labeling_seed}"
frames_per_video="${FRAMES_PER_VIDEO:-20}"
copy_photos=1
sample_videos=1
dry_run=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --video-dir)
      video_dir="$2"
      shift 2
      ;;
    --photo-dir)
      photo_dir="$2"
      shift 2
      ;;
    --out-dir)
      out_dir="$2"
      shift 2
      ;;
    --frames-per-video)
      frames_per_video="$2"
      shift 2
      ;;
    --skip-photos)
      copy_photos=0
      shift
      ;;
    --skip-videos)
      sample_videos=0
      shift
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if ! [[ "$frames_per_video" =~ ^[0-9]+$ ]] || [[ "$frames_per_video" -eq 0 ]]; then
  echo "Error: --frames-per-video must be a positive integer." >&2
  exit 1
fi

require_cmd ffmpeg
require_cmd ffprobe
require_cmd find

images_dir="${out_dir}/images"
photos_out_dir="${images_dir}/photos"
frames_out_dir="${images_dir}/video_frames"
manifest_path="${out_dir}/manifest.csv"

if [[ "$dry_run" -eq 0 ]]; then
  mkdir -p "$photos_out_dir" "$frames_out_dir"
  printf 'file_path,source_type,source_path,timestamp_seconds\n' > "$manifest_path"
fi

photo_count=0
frame_count=0
video_count=0

if [[ "$copy_photos" -eq 1 ]]; then
  if [[ -d "$photo_dir" ]]; then
    while IFS= read -r -d '' photo; do
      rel="${photo#${photo_dir}/}"
      safe_rel="$(sanitize_relpath "$rel")"
      ext="${photo##*.}"
      out_file="${photos_out_dir}/${safe_rel%.*}.${ext,,}"
      if [[ "$dry_run" -eq 1 ]]; then
        echo "[dry-run] photo: $photo -> $out_file"
      else
        cp "$photo" "$out_file"
        printf '%s,%s,%s,%s\n' "${out_file}" "photo" "${photo}" "" >> "$manifest_path"
      fi
      photo_count=$((photo_count + 1))
    done < <(find "$photo_dir" -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) -print0)
  else
    echo "Photo directory not found, skipping: $photo_dir"
  fi
fi

if [[ "$sample_videos" -eq 1 ]]; then
  if [[ -d "$video_dir" ]]; then
    while IFS= read -r -d '' video; do
      duration="$(ffprobe -v error -show_entries format=duration -of default=nokey=1:noprint_wrappers=1 "$video" || true)"
      if [[ -z "$duration" ]] || [[ "$duration" == "N/A" ]]; then
        echo "Skipping video with unknown duration: $video"
        continue
      fi

      video_rel="${video#${video_dir}/}"
      safe_video_rel="$(sanitize_relpath "$video_rel")"
      safe_video_rel="${safe_video_rel%.*}"
      video_count=$((video_count + 1))

      for ((i=0; i<frames_per_video; i++)); do
        ts="$(awk -v d="$duration" -v i="$i" -v n="$frames_per_video" 'BEGIN { printf "%.3f", ((i + 0.5) * d / n) }')"
        out_file="${frames_out_dir}/${safe_video_rel}_f$(printf "%03d" "$i").jpg"
        if [[ "$dry_run" -eq 1 ]]; then
          echo "[dry-run] frame: $video @ ${ts}s -> $out_file"
        else
          ffmpeg -loglevel error -ss "$ts" -i "$video" -frames:v 1 -q:v 2 "$out_file"
          printf '%s,%s,%s,%s\n' "${out_file}" "video_frame" "${video}" "${ts}" >> "$manifest_path"
        fi
        frame_count=$((frame_count + 1))
      done
    done < <(find "$video_dir" -type f \( -iname '*.mp4' -o -iname '*.mov' -o -iname '*.mkv' -o -iname '*.avi' -o -iname '*.wmv' \) -print0)
  else
    echo "Video directory not found, skipping: $video_dir"
  fi
fi

echo "Preparation complete."
echo "Photos copied: $photo_count"
echo "Videos sampled: $video_count"
echo "Frames extracted: $frame_count"
if [[ "$dry_run" -eq 0 ]]; then
  echo "Manifest: $manifest_path"
fi

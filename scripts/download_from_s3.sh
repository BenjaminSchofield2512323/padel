#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Download padel data directly from S3 into local storage.

Usage:
  bash scripts/download_from_s3.sh --bucket <name> [options]

Options:
  --bucket <name>    S3 bucket name (or use S3_BUCKET env var)
  --prefix <path>    Optional key prefix under the bucket (or S3_PREFIX env var)
  --dest <path>      Local destination directory (default: data/raw or DATA_DIR env var)
  --region <name>    AWS region (optional, or AWS_REGION env var)
  --profile <name>   AWS CLI profile (optional, or AWS_PROFILE env var)
  --dry-run          Show what would sync without downloading
  -h, --help         Show this help message
EOF
}

bucket="${S3_BUCKET:-}"
prefix="${S3_PREFIX:-}"
dest="${DATA_DIR:-data/raw}"
region="${AWS_REGION:-}"
profile="${AWS_PROFILE:-}"
dry_run=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bucket)
      bucket="$2"
      shift 2
      ;;
    --prefix)
      prefix="$2"
      shift 2
      ;;
    --dest)
      dest="$2"
      shift 2
      ;;
    --region)
      region="$2"
      shift 2
      ;;
    --profile)
      profile="$2"
      shift 2
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

if [[ -z "$bucket" ]]; then
  echo "Error: bucket is required (use --bucket or S3_BUCKET)." >&2
  exit 1
fi

if ! command -v aws >/dev/null 2>&1; then
  echo "Error: aws CLI not found. Install AWS CLI v2 first." >&2
  exit 1
fi

prefix="${prefix#/}"
prefix="${prefix%/}"

s3_uri="s3://${bucket}"
if [[ -n "$prefix" ]]; then
  s3_uri="${s3_uri}/${prefix}"
fi

mkdir -p "$dest"

sync_cmd=(aws s3 sync "$s3_uri" "$dest" --no-progress)

if [[ -n "$region" ]]; then
  sync_cmd+=(--region "$region")
fi

if [[ -n "$profile" ]]; then
  sync_cmd+=(--profile "$profile")
fi

if [[ "$dry_run" -eq 1 ]]; then
  sync_cmd+=(--dryrun)
fi

echo "Syncing from ${s3_uri} -> ${dest}"
"${sync_cmd[@]}"
echo "Sync complete."

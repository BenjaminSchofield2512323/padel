Padel pose project bootstrap (direct S3 workflow)

This repo is set up to download large video data directly from S3 into the VM.
No DVC is required.

Prerequisites
- AWS CLI v2 installed (`aws --version`)
- AWS credentials configured in the VM (`aws configure` or IAM role)

Quick start
1) Validate AWS access:
   `aws sts get-caller-identity`

2) Download footage from S3:
   `bash scripts/download_from_s3.sh --bucket padeldata --prefix padel-data --dest data/raw --region us-east-1`

3) Sync only new/changed files later:
   rerun the same command; `aws s3 sync` is incremental.

Optional environment variables
- `S3_BUCKET` (required if `--bucket` omitted)
- `S3_PREFIX` (optional)
- `DATA_DIR` (default: `data/raw`)
- `AWS_REGION` (optional)
- `AWS_PROFILE` (optional)

Examples
- Pull from bucket root:
  `bash scripts/download_from_s3.sh --bucket padeldata --dest data/raw`

- Dry-run before download:
  `bash scripts/download_from_s3.sh --bucket padeldata --prefix padel-data --dest data/raw --dry-run`

Notes
- Downloaded data stays out of git via `.gitignore`.
- Keep raw videos in S3; keep code/metadata in git.

---

Preparing a first labeling batch (photos + sampled video frames)

1) Ensure raw media exists locally:
   - photos in `data/raw/photos`
   - videos in `data/raw/videos`

2) Build a starter annotation batch:
   `bash scripts/prepare_labeling_data.sh --video-dir data/raw/videos --photo-dir data/raw/photos --out-dir data/labeling_seed --frames-per-video 20`

This creates:
- `data/labeling_seed/images/photos/` (photos to annotate)
- `data/labeling_seed/images/video_frames/` (sampled frames to annotate)
- `data/labeling_seed/manifest.csv` (source tracking for each image)

3) Annotate images in a labeling tool (CVAT or Label Studio), then export in COCO keypoints format if possible.

See `docs/labeling_guide.md` for detailed instructions and recommended keypoints.

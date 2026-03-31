# Labeling guide for padel pose bootstrap

This guide helps you label a small, high-quality seed dataset so pose training/fine-tuning can start quickly.

## Goal of this phase
- Label photos + a small set of video frames.
- Focus on high-quality, diverse examples (different players, positions, lighting, occlusions).
- Keep first batch small and clean.

Recommended first batch size:
- **Photos:** 100-300 images
- **Frames:** 300-800 images (sampled from multiple videos)

## Recommended tools
- **CVAT** (preferred for skeleton keypoints)
- Label Studio (works too, but CVAT is usually easier for pose skeleton workflows)

## Keypoint schema (17-point COCO)
Use this canonical order:
1. nose
2. left_eye
3. right_eye
4. left_ear
5. right_ear
6. left_shoulder
7. right_shoulder
8. left_elbow
9. right_elbow
10. left_wrist
11. right_wrist
12. left_hip
13. right_hip
14. left_knee
15. right_knee
16. left_ankle
17. right_ankle

Visibility convention:
- `2` visible and confidently localized
- `1` occluded / not visible but estimated
- `0` not labeled (outside frame or impossible)

## What to include in the seed set
- Both camera viewpoints (fixed + drone if available)
- Near and far players
- Baseline, transition zone, and net positions
- Serving/overhead/volley/groundstroke moments
- Hard cases: motion blur, partial occlusion by partner/opponent, glass reflections

## Quality bar
- Place joints at anatomical centers.
- For occluded limbs, estimate only when plausible.
- Do not overfit labels to racket silhouette; keypoints are body joints.
- Keep left/right consistent with the player's body, not image side.

## Train/val split recommendation
- Split by source video, not random frames from same segment.
- Suggested split: `80% train / 20% val`.

## Export format
- Prefer COCO Keypoints JSON if supported by your training stack.
- Keep original image filenames unchanged.

## Suggested directory layout
```
data/
  raw/                  # synced from S3 (ignored by git)
  labeling/
    images/
      photos/
      frames/
    annotations/
      train.json
      val.json
```

By default, `scripts/prepare_labeling_data.sh` now copies photos as normalized JPGs
(auto-rotate + max width 2560) to reduce browser/tool decode issues during labeling.

## Fast iterative loop
1. Label first batch.
2. Train/fine-tune baseline.
3. Run inference on unlabeled frames.
4. Select failure cases and relabel.
5. Repeat.


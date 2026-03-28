# Line Design

`WIN_YOLO_PTZ_20S` is intended to replace the current shared WIN flow with an isolated folder tree.

## Intended Flow

1. Build 20-second candidates from YOLO detections.
2. Pick candidates into this line's own queues.
3. Compute `crop_x` from YOLO for the fixed 20-second window.
4. Export cropped JPEGs for the full 20-second window.
5. Generate `title` and `description` from the cropped JPEGs only.
6. Render the 20-second short with the same `crop_x`.
7. Upload from this line's own upload queue.

## Compatibility Goal

`decision.json` should stay compatible with the existing uploader contract even if metadata generation becomes API2-only:

```json
{
  "crop_x": 0,
  "start_sec_rel": 0,
  "end_sec_rel": 20,
  "title": "...",
  "description": "..."
}
```

## Migration Direction

- `pick`: line-local
- `queue`: line-local
- `metadata`: line-local
- `render`: compatible with the current WIN behavior
- `upload`: may reuse current logic if queue contract stays compatible


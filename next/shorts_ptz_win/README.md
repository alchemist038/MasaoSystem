# WIN_YOLO_PTZ_20S

Windows canonical line for Masao shorts built around these fixed rules:

- 20-second clips only
- crop position selected from YOLO detections
- cropped JPEGs are the only visual input for metadata generation
- render and upload stay compatible with the current WIN uploader contract
- queues, config, prompts, and assets are isolated inside this line

This line is being built alongside the existing pipeline. Existing folders remain untouched.

## Structure

- `assets/`
  - line-local assets such as logo overlays and BGM
- `data/`
  - line-local queues and runtime data
- `prompts/`
  - line-local prompts for metadata generation
- `runbooks/`
  - line-local operating notes and migration design
- `scripts/`
  - line-local pick / pipeline / metadata / upload scripts
- `ui/`
  - line-local UI

## Line Rules

- One line, one folder tree.
- Internal paths should be relative to `config.json`.
- Existing legacy queues must not be shared.
- `decision.json` should keep a compatible shape:
  - `crop_x`
  - `start_sec_rel`
  - `end_sec_rel`
  - `title`
  - `description`

## Current Status

This folder is scaffolded only. The old line still performs the real work.
The next migration step is to move the WIN canonical flow into this tree without reusing the old shared queues.

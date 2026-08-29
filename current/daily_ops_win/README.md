# daily_ops_win

Current operating policy is defined in:

```text
D:\MasaoSystem\docs\current\CURRENT_OPERATIONS.md
D:\MasaoSystem\docs\current\SYSTEM_COMPONENT_MAP.md
```

The code remains available, but current content policy pauses routine high-volume Shorts publishing. Do not interpret the folder name or an old runbook as upload authorization.

This folder groups the two Windows lines used most often.

- `shorts_win`
  - the retained Windows shorts generation and upload line
  - flow: candidate / motion -> local YOLO crop -> API2 -> render -> upload
  - current status: code retained; routine high-volume publication is not active policy
- `post_publish`
  - the post-publish maintenance line
  - used for updates after upload, manual single uploads, and digest posting records
- `live_overlays`
  - small OBS browser overlays and low-load live display helpers
  - production copy is deployed under `D:\OBS\REC\overlays`
  - excludes live data such as `sensor-data.json` and `sensor-data.js`

Positioning:

- This is a reorganized working copy under `D:\MasaoSystem`
- Source/runtime ownership is component-specific; use `SYSTEM_COMPONENT_MAP.md`
- `historical_reprocess_win` stays separate because it is a helper line for old 360 assets, not the daily main line

# daily_ops_win

This folder groups the two Windows lines used most often.

- `shorts_win`
  - the daily shorts generation and upload line
  - flow: candidate / motion -> local YOLO crop -> API2 -> render -> upload
- `post_publish`
  - the post-publish maintenance line
  - used for updates after upload, manual single uploads, and digest posting records
- `live_overlays`
  - small OBS browser overlays and low-load live display helpers
  - production copy is deployed under `D:\OBS\REC\overlays`
  - excludes live data such as `sensor-data.json` and `sensor-data.js`

Positioning:

- This is a reorganized working copy under `D:\MasaoSystem`
- Production truth is still under `D:\OBS\REC`
- `historical_reprocess_win` stays separate because it is a helper line for old 360 assets, not the daily main line

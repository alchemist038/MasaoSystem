# post_publish

Windows-side helpers and records for operations around YouTube uploads.

This folder currently covers:

- metadata updates after upload
- scheduled Shorts maintenance
- playlist lookup and status checks
- manual single-video uploads for digest posts
- per-digest posting records

Main files:

- `update_shorts.py`
  - batch metadata updates for uploaded Shorts
- `update_scheduled_shorts.py`
  - scheduled Shorts metadata maintenance
- `get_playlists.py`
  - channel playlist lookup helper
- `upload_digest_video.py`
  - single digest uploader with scheduled publish time and optional thumbnail / playlist
- `digest_posts/`
  - case records for individual digest uploads

Operational note:

- Production truth for generated assets remains under `D:\OBS\REC`.
- Keep large local outputs such as rendered videos, thumbnails, and package folders in `D:\OBS\REC`.
- Store only reusable scripts and lightweight trace records in this repo.

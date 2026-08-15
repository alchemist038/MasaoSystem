# post_publish

Windows-side helpers and records for operations around YouTube uploads.

This folder currently covers:

- metadata updates after upload
- scheduled Shorts maintenance
- playlist lookup and status checks
- manual single-video uploads for digest posts
- per-digest posting records

Digest upload rule:

- For normal digest releases, the final upload master should target `1920x1080`.
- Draft or proxy review outputs may use lower resolution, but the publish-ready master should be `1080p` when the source and render path allow it.

Main files:

- `update_shorts.py`
  - batch metadata updates for uploaded Shorts
- `update_scheduled_shorts.py`
  - scheduled Shorts metadata maintenance
- `get_playlists.py`
  - channel playlist lookup helper
- `upload_digest_video.py`
  - single digest uploader with scheduled publish time and optional thumbnail / playlist
- `youtube_hideout_manage.py`
  - guarded API client for the separate `まさおの隠れ家` Shorts channel
- `Invoke-HideoutYouTube.ps1`
  - standard entry point that always uses the hideout-only token role and channel guard
- `digest_posts/`
  - case records for individual digest uploads

## Masao Hideout Shorts

Use this entry point for every API operation targeting `まさおの隠れ家`.
Do not inspect or fall back to the main-channel token store.

```powershell
# Token and channel preflight (read only)
.\Invoke-HideoutYouTube.ps1 -Command status -Json

# Recent uploads and schedules (read only)
.\Invoke-HideoutYouTube.ps1 -Command list-recent -Limit 20 -Json

# Inspect one video (read only)
.\Invoke-HideoutYouTube.ps1 -Command inspect -VideoId VIDEO_ID -Json

# Manifest preflight only: channel, SHA-256, schedule, and duplicate checks
.\Invoke-HideoutYouTube.ps1 -Command upload-manifest -Manifest 'D:\path\upload_manifest.json' -Json

# Upload and schedule only after explicit approval
.\Invoke-HideoutYouTube.ps1 -Command upload-manifest -Manifest 'D:\path\upload_manifest.json' -Execute -Json
```

Fixed guards:

- Expected channel: `UCIG-z7Q4rRq-cbIUJDB8SlA`
- Token role: `D:\OBS\REC\keys\youtube_hideout\token_hideout_ops.json`
- Main-channel token fallback: prohibited
- Scheduled upload visibility: must start as `private`
- Manifest SHA-256: required and verified against the video bytes
- Recent same-title or same-`publishAt` match: blocks the upload

Operational note:

- Production truth for generated assets remains under `D:\OBS\REC`.
- Keep large local outputs such as rendered videos, thumbnails, and package folders in `D:\OBS\REC`.
- Store only reusable scripts and lightweight trace records in this repo.

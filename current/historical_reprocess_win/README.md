# historical_reprocess_win

This folder is the Windows-native helper line for historical 360 assets.

It is not the daily canonical shorts line.
Its job is to preserve the old inventory logic in a cleaner Windows form.

## Purpose

This line handles the upstream part of the old Ubuntu workflow:

1. find the next session that has `proxy_360.mp4`
2. run DeltaY-based event extraction
3. create `frames_360/<EVENT>` inventory
4. enqueue unconsumed inventory items

Important:

- inventory is visible in Explorer
- `frames_360/<EVENT>` = stock
- same-name `events/<EVENT>` exists = already consumed into processing

## Folder Layout

```text
historical_reprocess_win/
  config.json
  config.example.json
  run_analyze_next_session_win.ps1
  run_enqueue_daily_YA_win.ps1
  data/
  logs/
  scripts/
```

## Scripts

- `scripts/run_analyze_next_session_win.py`
  - Windows replacement for the old analyze cron entry
- `scripts/analyze_y2_events_win.py`
  - DeltaY event extraction from `proxy_360.mp4`
- `scripts/enqueue_daily_YA_win.py`
  - turn unconsumed `frames_360` inventory into event queue rows

## Notes

- This line intentionally keeps file-based visible state.
- It does not make API1 canonical again.
- It exists so historical assets can still be reused on Windows.

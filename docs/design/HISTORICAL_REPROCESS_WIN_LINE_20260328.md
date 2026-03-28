# Historical Reprocess Win Line

Date: 2026-03-28

## Purpose

This is the Windows-native replacement for the upstream part of the old Ubuntu reprocess line.

It exists so historical 360 assets can still be reused without depending on Linux cron scripts.

## Location

- `D:\MasaoSystem\current\historical_reprocess_win`

## Source Lineage

This line comes from:

- `D:\OBS\REC\jobs\run_analyze_cron.sh`
- `D:\OBS\REC\scripts\active\analyze_y2_events.py`
- `D:\OBS\REC\scripts\active\enqueue_daily_YA.py`

## What It Does

### Stage 1

- find the next session that has `proxy_360.mp4`
- skip sessions already marked with `logs\.analyze_done`
- avoid analyzing a file that is still growing

Script:

- `scripts\run_analyze_next_session_win.py`

Wrapper:

- `run_analyze_next_session_win.ps1`

### Stage 2

- run DeltaY-based event extraction on `proxy_360.mp4`
- write logs and event inventory into the session itself
- preserve:
  - `logs`
  - `frames_360`
  - `.analyze_done`

Script:

- `scripts\analyze_y2_events_win.py`

### Stage 3

- scan `frames_360`
- treat a same-name `events\<EVENT>` folder as already consumed inventory
- append only unconsumed inventory to a queue

Script:

- `scripts\enqueue_daily_YA_win.py`

Wrapper:

- `run_enqueue_daily_YA_win.ps1`

## Queue Output

Current queue file:

- `D:\MasaoSystem\current\historical_reprocess_win\data\event_queue_legacy_reprocess.jsonl`

This queue is intentionally separate from the daily canonical Windows YOLO queue.

## Design Position

This line is:

- current as a usable historical-asset helper
- not the daily canonical shorts line
- not a reason to restore API1 as the daily main path

## What It Preserves

- session-based processing
- Explorer-readable inventory
- file-based state
- `frames_360` as stock
- `events` as consumed stock
- upstream DeltaY logic for historical assets

## What It Does Not Decide Yet

- final downstream Windows replacement after inventory is enqueued
- whether historical items should later flow into:
  - a dedicated reprocess bridge
  - or a partially shared canonical Windows line

That downstream decision remains separate.

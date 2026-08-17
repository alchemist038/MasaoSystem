# OBS RAW Recording Confirmation

`obs_schedule.js` confirms each part's OBS recording at stream start and once
again after stream stop. This is an event-based guard; it does not continuously
watch file growth.

## Start

- Part 1: runs when the manual morning stream start is detected.
- Parts 2 and 3: runs immediately after the scheduled stream start request.
- If OBS recording is already active, no write request is made.
- If recording is still inactive after the OBS auto-start grace period,
  `StartRecord` is issued once.
- The schedule log reports stream state, recording state, whether recovery was
  needed, and the RAW output path.

## End

- Parts 1 and 2: runs after the scheduled stream stop request.
- Part 3: the normal local shutdown helper runs the manual final check before
  closing OBS.
- If recording remains active after stream stop, `StopRecord` is issued once.
- The schedule log reports RAW existence, final size, and path.
- If OBS was already closed, the saved path is used for the same file report.

The day-scoped non-secret status is saved at:

```text
C:\Users\alche\Desktop\OBS\logs\obs_recording_YYYY-MM-DD.json
```

Manual finalization can also be run directly after the stream is stopped:

```powershell
node C:\Users\alche\Desktop\OBS\scripts\obs_schedule.js --finalize-recording --date=YYYY-MM-DD --part=part3
```

The command refuses to stop recording while OBS still reports an active stream.
If `--part` is omitted, the open part in the day-scoped state is preferred,
then the normal part boundary for the current time is used.

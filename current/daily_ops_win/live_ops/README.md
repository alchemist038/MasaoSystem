# Masao Live Ops

This folder is the Git-managed source of truth for daily Masao live operation helpers.

Runtime copies currently live under:

```text
C:\Users\alche\Desktop\OBS\scripts
```

Keep runtime speed and OBS compatibility on `C:`, but keep reviewable source and history here on `D:`.

## Contents

```text
obs_scripts/
  obs_schedule.js
  prepare_morning_profile.ps1
  run_obs_schedule.ps1

fallback/
  tapo_fallback_controller.js
  tapo_fallback_config_jikka.json
  tapo_fallback_config_shataku.json
  run_tapo_fallback_*.ps1
  run_tapo_fallback_*.bat

youtube_live/
  youtube_live_broadcasts.py

docs/
  DEPLOY.md
```

## Policy

- Git tracks stable operation logic: schedule switching, fallback behavior, YouTube Live API helpers, and launch wrappers.
- Git does not track daily YouTube manifests, logs, token files, OAuth files, stream keys, passwords, or OBS runtime state.
- OBS profile files and scene collections remain runtime configuration unless a sanitized copy is intentionally added.
- PTZ runtime remains separate in `C:\masao_ptz`, which has its own Git repository.

## Current Runtime Model

The normal daily flow still runs from `C:\Users\alche\Desktop\OBS\scripts`.

After changing files here, copy them to the OBS runtime folder with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy_to_obs_scripts.ps1
```

`youtube_live_broadcasts.py` is skipped by default because token-path handling is intentionally public-safe in this source tree. Deploy it only after the runtime token environment is confirmed:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy_to_obs_scripts.ps1 -IncludeYoutubeLive
```

Do not deploy during an active stream unless the specific change is known to be safe.

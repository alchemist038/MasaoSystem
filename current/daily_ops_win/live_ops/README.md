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
  thumbnails/
    masao_thumb_part1_morning.jpg
    masao_thumb_part2_noon.jpg
    masao_thumb_part3_night.jpg

comment_reader/
  comment_reader.py
  prepare_bouyomi_bt.ps1
  deploy_to_runtime.ps1
  install_firewall_rule.ps1
  start_comment_reader.ps1
  stop_comment_reader.ps1
  status_comment_reader.ps1
  README.md

comment_reader_control/
  masao_comment_control.pyw
  obs_bridge.js
  deploy_to_runtime.ps1
  README.md

docs/
  DEPLOY.md
```

## Policy

- Git tracks stable operation logic: schedule switching, fallback behavior, YouTube Live API helpers, and launch wrappers.
- Git does not track daily YouTube manifests, logs, token files, OAuth files, stream keys, passwords, or OBS runtime state.
- OBS profile files and scene collections remain runtime configuration unless a sanitized copy is intentionally added.
- PTZ runtime remains separate in `C:\masao_ptz`, which has its own Git repository.
- The private comment reader is an INS14 receiver only. Its i5 sender must reuse V7's existing fetched comments; do not add another YouTube polling loop or remotely change i5 from this PC.
- The desktop control application may start and stop only the private comment-reader path. It must never start, stop, or reconfigure the existing Taro/Goro `50000 -> 50001` path.

## Current Runtime Model

The normal daily flow still runs from `C:\Users\alche\Desktop\OBS\scripts`.

After changing files here, copy them to the OBS runtime folder with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy_to_obs_scripts.ps1
```

The YouTube Live script and coordinated thumbnail series are skipped by default because token-path handling is intentionally public-safe in this source tree. Deploy them only after the runtime token environment is confirmed:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy_to_obs_scripts.ps1 -IncludeYoutubeLive
```

Do not deploy during an active stream unless the specific change is known to be safe.

The private comment reader has a separate runtime and desktop entry point:

```text
C:\masao\comment_reader_control
Desktop\まさお コメント読み上げ.lnk
```

Its normal resting mode is `Earphones only`; the OBS comment source remains muted.

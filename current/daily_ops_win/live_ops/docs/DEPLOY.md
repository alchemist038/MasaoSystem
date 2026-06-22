# Deploy Notes

`D:\MasaoSystem\current\daily_ops_win\live_ops` is the source of truth.

`C:\Users\alche\Desktop\OBS\scripts` is the OBS runtime location.

## Safe Deployment

Run from this folder:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy_to_obs_scripts.ps1
```

This copies:

- `obs_scripts\*` to `C:\Users\alche\Desktop\OBS\scripts`
- `fallback\*` to `C:\Users\alche\Desktop\OBS\scripts`

It skips `youtube_live\youtube_live_broadcasts.py` by default. Deploy it only when the runtime token setup is confirmed:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy_to_obs_scripts.ps1 -IncludeYoutubeLive
```

The source version of `youtube_live_broadcasts.py` does not hardcode private UNC/IP token paths. It expects one of:

- `MASAO_YOUTUBE_LIVE_TOKEN_FILE`
- `MASAO_YOUTUBE_LIVE_TOKEN_FILES`
- a local ignored file under `D:\MasaoSystem\shared\keys\youtube`

## Secrets

Do not commit:

- OAuth token files
- stream keys
- OBS service settings containing stream keys
- daily `broadcasts_YYYY-MM-DD.json`
- password-bearing RTSP URLs
- local-only `*.local.json` or `*.secret.*` files

The current fallback configs are intentionally source-controlled because they contain scene/source mapping and transform behavior, not camera passwords.

## Operational Caution

The schedule monitor is long-running. If `obs_schedule.js` is changed while a stream is active, do not deploy or restart the monitor casually. Wait for a safe point or explicitly plan the handoff.

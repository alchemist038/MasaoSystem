# YouTube Live Metrics Dock

This component replaces the viewer-count portion of the OBS built-in YouTube
Live Control Panel without loading `YouTubeAppDock`.

It reads the current three-part manifest, makes one `videos.list` request per
poll interval, automatically follows the active part, and serves cached metrics
to a local OBS browser dock.

## Start

Set `MASAO_YOUTUBE_LIVE_TOKEN_FILE` to the approved local token path, then run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\start_live_metrics.ps1 `
  -Date 2026-08-01 -Port 8791 -PollSeconds 60
```

OBS dock URL:

```text
http://127.0.0.1:8791/
```

OBS custom browser dock name:

```text
ライブ指標
```

The normal daily operation starts this component before OBS or immediately
after OBS is ready. The dock automatically follows the active Part 1, Part 2,
or Part 3 broadcast from the daily manifest.

## Stop

After the final stream has ended, stop only this component and confirm that the
local listener is closed:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\stop_live_metrics.ps1
```

The token value is never sent to the browser. The HTTP server binds only to
`127.0.0.1`. The backend polls YouTube no more often than every 30 seconds; the
normal production interval is 60 seconds.

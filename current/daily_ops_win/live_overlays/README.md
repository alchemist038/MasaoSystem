# live_overlays

Small OBS browser overlays and live display helpers.

Production copies are deployed under:

```text
D:\OBS\REC\overlays
```

Do not commit live-updating data, local logs, secrets, or API tokens.

## Current overlays

- `masao_room_sensor`
  - SwitchBot Hub / Cloud API room temperature and humidity overlay
  - OBS browser source: `D:\OBS\REC\overlays\masao_room_sensor\index.html`
  - Runtime updater: `D:\OBS\REC\overlays\masao_room_sensor\start_room_sensor_hub_watch.ps1`
  - Normal live-prep startup item, launched alongside OBS / PTZ / Bouyomi / schedule monitor

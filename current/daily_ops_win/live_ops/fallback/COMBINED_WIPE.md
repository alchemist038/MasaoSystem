# X-Position Wipe With Independent BOX Loss

Approved 2026-10-18 for Shataku: combine adaptive sizing and overlap opacity
inside the existing fallback controller. No additional application or detector.

- Use width 450..600, height width*9/16, top-left position retained.
  Retuned from320..500 at the user's request on2026-10-18.
- Size from the projected BOX left edge, not area or BOX Y:
  `width = clamp(box.left - wipe.x - 16, 450, 600)` in OBS canvas pixels.
  Respect canvas bounds and preserve the anchor. `adaptive_wipe.mode=x_position`
  enables this; legacy `area` mode remains available but is not production.
- Shrink with the existing0.45s smoothing/160px-per-second cap. Growth waits
  one continuous second with sufficient horizontal space; retain8px deadband.
  BOX Y never provides extra room for sizing.
- Resize first, then re-read OBS geometry to check the visible wipe boundary.
- A confirmed X/Y overlap uses50% opacity with normal blending. Horizontal
  margin is16px; `overlap_transparency.vertical_margin_px=0` means separated
  Y ranges do not fade, even with a small gap. X overlap alone is insufficient.
  `overlap_transparency.mode=opacity` and `opacity_percent=50` control this;
  the percentage is clamped to0..100. Legacy `mode=blend` retains additive mode.
- Opacity changes use a0.6s smoothstep fade in both directions, controlled by
  `overlap_transparency.fade_duration_ms=600` (0 disables fading). Continuous
  clear geometry must still last one second before fading back to100%.
  Reversals start from the currently displayed value. Each existing control
  tick advances one step without sleeping or blocking the loss watchdog.
  Full-screen expansion, disabled control and other program scenes bypass
  the fade and restore100% immediately on their control tick.
- Missing or unsupported geometry holds the inset size and uses50% opacity
  during the loss grace period. Unsupported OBS transforms do not invalidate
  otherwise fresh detector data; report geometry problems separately.
- With `box_loss.enabled=true`, the controller independently validates detection,
  normalized BOX coordinates and both state/observation timestamps. It does not
  depend on V7's `lost_stage`, `search` timing or BOX area. No valid BOX for1.5s,
  a frozen observation/state older than1.5s, missing/unreadable state or malformed
  data triggers full-screen100% opacity. Repeated old data cannot reset freshness.
- Recovery requires3s of continuously fresh valid detections, with advancing
  observations. No second3s wait is added. Existing1s expand/shrink transitions
  remain. Timeout is measured from the last good observation when known, or
  from first missing/invalid data at startup; polling/transition adds latency.
- Explicit `manual_override` and global disable remain authoritative. In the
  independent mode, `stale_mode`, `tracking_disabled_mode`, PTZ lost-stage
  triggers and `lost_enter_wait_sec` are legacy-only. Tracking off also counts
  as missing BOX; use explicit manual override to hold a chosen display.
- The owned source filter `Masao Wipe Opacity` is `color_filter_v2`, with OBS
  opacity0..1. Other filters and color settings are preserved. A name collision
  with another filter kind fails without replacing the user's filter.
- Because the Tapo source is shared, a program scene other than the configured
  target restores100% on the next control tick. Disabled control also restores
  100%; fallback expansion restores100% before the transform begins.
- The configured recovery entry is 450x253.125. Actual tracking can enlarge it to600.
- State-file reads remain at500ms and the existing animation loop at up to10Hz.

The source config remains opt-in. Production enables `adaptive_wipe.enabled`,
`box_loss.enabled` and `overlap_transparency.enabled`; preserve unrelated runtime
fields and the location-specific scene/source. Deploy controller, adaptive,
overlap and `box_loss.js`
modules together and restart only the existing fallback Windows task. The
OBS/PTZ/schedule/recording processes do not need a restart.

Verify with `node --test wipe_overlap.test.js adaptive_wipe.test.js wipe_presentation.test.js box_loss.test.js position_wipe.test.js`
and `node --check tapo_fallback_controller.js`. Bounded live verification reads
OBS state, tracker state and screenshots; never inject fake boxes into V7 state.
If rollback is needed, stop only the fallback task and its exact remaining child,
then restore100% opacity or remove only `Masao Wipe Opacity` through OBS. Restore
the saved code/config and launch that task once. Switching back to legacy blend
mode alone does not neutralize the source filter. Verify one running instance,
actual scene transform, blend and opacity. Abrupt process termination can leave
the last filter value until the controller restarts or it is explicitly restored.

For rollback to the immediately preceding area/opacity controller, stop only
fallback, restore the saved three JS modules/config and start once. The unused
`box_loss.js` can remain; the old controller does not load it. Both versions
manage the same opacity filter, so it need not be removed for this rollback.

This is independent switching logic using V7 detections, not independent image
recognition. A frozen camera picture with falsely fresh valid detector reports
is not detected by this watchdog. Never inject fake BOXes or stop V7 to test it
during a live stream; simulate outage/recovery in tests instead.

This supersedes the area sizing and PTZ-stage trigger used earlier on October18,
and the mutual-exclusion policy in the September27 trial documents.
Those trial documents remain as historical evidence.

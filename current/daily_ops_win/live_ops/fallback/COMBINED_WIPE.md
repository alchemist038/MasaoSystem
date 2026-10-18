# Adaptive Wipe With Overlap Opacity

Approved 2026-10-18 for Shataku: combine adaptive sizing and overlap opacity
inside the existing fallback controller. No additional application or detector.

- Use width 450..600, height width*9/16, top-left position retained.
  Retuned from320..500 at the user's request on2026-10-18.
- Keep inverse confirmed BOX area sizing and the existing smoothing settings.
- Resize first, then re-read OBS geometry to check the visible wipe boundary.
- A confirmed overlap (16px margin) uses50% opacity with normal blending.
  `overlap_transparency.mode=opacity` and `opacity_percent=50` control this;
  the percentage is clamped to0..100. Legacy `mode=blend` retains additive mode.
- Continuous clear geometry for one second restores100% opacity.
- Missing, stale or unsupported BOX geometry holds size and uses50% opacity.
- Full-screen fallback has priority and remains normal/opaque. Existing search
  trigger, three-second recovery wait and one-second transitions are unchanged.
- The owned source filter `Masao Wipe Opacity` is `color_filter_v2`, with OBS
  opacity0..1. Other filters and color settings are preserved. A name collision
  with another filter kind fails without replacing the user's filter.
- Because the Tapo source is shared, a program scene other than the configured
  target restores100% on the next control tick. Disabled control also restores
  100%; fallback expansion restores100% before the transform begins.
- The configured recovery entry is 450x253.125. Actual tracking can enlarge it to600.
- State-file reads remain at500ms and the existing animation loop at up to10Hz.

The source config remains opt-in. Production enables both `adaptive_wipe.enabled`
and `overlap_transparency.enabled`; preserve unrelated runtime fields and the
location-specific scene/source. Deploy the controller, adaptive and overlap
modules together and restart only the existing fallback Windows task. The
OBS/PTZ/schedule/recording processes do not need a restart.

Verify with `node --test wipe_overlap.test.js adaptive_wipe.test.js wipe_presentation.test.js`
and `node --check tapo_fallback_controller.js`. Bounded live verification reads
OBS state, tracker state and screenshots; never inject fake boxes into V7 state.
If rollback is needed, stop only the fallback task and its exact remaining child,
then restore100% opacity or remove only `Masao Wipe Opacity` through OBS. Restore
the saved code/config and launch that task once. Switching back to legacy blend
mode alone does not neutralize the source filter. Verify one running instance,
actual scene transform, blend and opacity. Abrupt process termination can leave
the last filter value until the controller restarts or it is explicitly restored.

This supersedes the mutual-exclusion policy in the September27 trial documents.
Those trial documents remain as historical evidence.

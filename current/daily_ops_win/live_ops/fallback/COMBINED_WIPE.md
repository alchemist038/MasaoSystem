# Adaptive Wipe With Overlap Blending

Approved 2026-10-18 for Shataku: combine adaptive sizing and overlap blending
inside the existing fallback controller. No additional application or detector.

- Use width 450..600, height width*9/16, top-left position retained.
  Retuned from320..500 at the user's request on2026-10-18.
- Keep inverse confirmed BOX area sizing and the existing smoothing settings.
- Resize first, then re-read OBS geometry to check the visible wipe boundary.
- A confirmed overlap (16px margin) uses additive blending. This is the previous
  see-through appearance, not a fixed alpha-opacity filter.
- Continuous clear geometry for one second restores normal/opaque blending.
- Missing, stale or unsupported BOX geometry holds size and uses additive blend.
- Full-screen fallback has priority and remains normal/opaque. Existing search
  trigger, three-second recovery wait and one-second transitions are unchanged.
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
If rollback is needed, stop only the fallback task, restore its saved code/config,
and launch that task once. Verify the running instance and actual scene transform.

This supersedes the mutual-exclusion policy in the September27 trial documents.
Those trial documents remain as historical evidence.

# Adaptive Opaque Wipe Trial

Approved 2026-09-27: inverse continuous bbox sizing replaces overlap blending.
The tracked config is opt-in; enabling production needs explicit approval.

- Width250..640 pixels, height=width*9/16, existing left/top anchor retained.
- Visible confirmed bbox area / OBS base canvas area <=5% -> width640;
  >=25% -> width250; linear interpolation in between (15% -> width445).
- One-second exponential area smoothing, eight-pixel target deadband,
  0.45-second resize smoothing, maximum160 pixels/second. OBS updates are
  serialized in the existing controller at up to10Hz; V7 state-file reads
  remain at the configured500ms cadence. No additional model or video process.
- Always normal/opaque blend. Adaptive mode takes precedence over the older
  overlap feature even if both flags are accidentally enabled.
- Stale/missing/unconfirmed detection freezes current size and cancels pending
  resize momentum. Unsupported/ambiguous geometry does not resize.
- Existing large-mode fallback, normal blend, recovery wait and transition
  retain ownership. The sizing loop only operates in small mode.
- Only positive-scale, unrotated, uncropped, top-left-anchored wipes without
  bounds fitting are resized. Subject projection supports the existing crop/
  scale/alignment mapping. Revalidate any geometry-changing source filter.

## Files / Verification

Deploy controller, `wipe_overlap.js`, and `adaptive_wipe.js` together. Preserve
unrelated runtime config. Set `adaptive_wipe.enabled=true`,
`overlap_transparency.enabled=false`, and `wipe_blend_mode=OBS_BLEND_NORMAL`.
Retain the actual user-chosen small wipe transform as the recovery entry size;
the adaptive policy then settles to the measured target. Do not restart PTZ,
OBS, recording, stream, or the daily scheduler for this change.

Run `node --test wipe_overlap.test.js adaptive_wipe.test.js` and
`node --check tapo_fallback_controller.js`. Test both endpoint clamps,
monotonic inversion, smoothing/speed, invalid states, dry run, geometry,
normal blending and retained full-screen decision before runtime deployment.
Observe a bounded live sample, rendered image, stream/record durations,
frame-skip counters and process load; do not simulate detections in live state.

## Disable / Restore

For a static opaque wipe, set `adaptive_wipe.enabled=false` while keeping the
overlap option disabled and wipe blend normal. This freezes the existing size
until the next normal fallback/recovery transition. Re-enabling resumes sizing.
To restore the earlier overlap trial, stop only this controller and restore
the backed-up controller, overlap module and config together. The new adaptive
module may remain unused. Restore the backed-up OBS transform separately when
required; saved configuration is not proof of the actual on-screen size.

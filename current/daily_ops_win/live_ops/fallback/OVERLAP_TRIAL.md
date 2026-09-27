# Conditional Wipe Transparency Trial

Status: candidate, NOT DEPLOYED. Date: 2026-09-27.
Fallback baseline: `f2b1513` on `main`.
PTZ baseline: `0964fac` on `master` in the separate `masao_ptz` repository.
Both candidate branches: `work/wipe-overlap-20260927`.

## Behavior

- Small wipe intersects the confirmed subject box plus 16 canvas pixels:
  additive blend, the same see-through appearance as the baseline.
- Clear for one second: normal blend, opaque wipe.
- Missing, old, future, invalid, or unconfirmed box: additive blend immediately.
- Full-screen fallback: existing normal blend and transition order are unchanged.
- `overlap_transparency.enabled=false`: retain the static baseline blend.
- The checked-in configuration starts DISABLED until the live trial is approved.

The existing fallback Node process reads the existing V7 state file every 500ms.
Only blending changes; the feature does not move or resize the wipe and performs
no inference. An OBS connection is reused. Reads are bounded by timeouts; blend
writes occur only when the current OBS value differs. Existing large/small
fallback control owns the display during transitions.

## Coordinate Contract And Limits

V7 must publish `subject_bbox` with `coordinate_space=capture_normalized`, four
ordered normalized `xyxy` values, capture dimensions, and an observation timestamp.
The default maximum box/state age is 1.5 seconds. Old V7 is compatible but cannot
trigger opaque mode because it does not publish a box.

The consumer uses the actual scene-item transforms, not hard-coded coordinates.
Positive scaling, cropping, translation, and OBS item alignment are supported.
Rotation, reflection, bounds fitting, groups, duplicate sources, hidden sources,
and malformed geometry return unknown and retain additive blending. Unknown
states never count toward the one-second clear timer. Source filters that change
geometry are not supported; revalidate before adding one.

Observed baseline: subject `OBSBOT VC` at 1920x1080, no source filters; wipe
`tapoc232` at left/top 0/0, 507x285. These are observations, not code constants.

## Tests

```powershell
node --test wipe_overlap.test.js
node --check tapo_fallback_controller.js
node probe_wipe_overlap.js
```

The probe is read-only, has a 25-second deadline, and rejects every OBS request
whose name does not start with Get. It uses synthetic boxes only. It does not
prove real subject alignment, live blending, or PTZ restart safety.

The initial September 27 probe ran 20 checks over 10.289 seconds: average check
1.817ms, maximum 2.567ms, probe Node CPU time 282ms, no OBS writes. OBS remained at
30fps; rendering skips stayed at 133 and encoder skips at 2. This is a short
read-only sample, not a guarantee about deployed end-to-end CPU/GPU load.

## Timed Trial

1. Confirm user readiness and the live-management owner; do not run two fallback
   controllers. Preserve OBS recording and the existing daily scheduler.
2. Record current PID/config, OBS stats, transformations, and hashes. Back up
   only the files being replaced outside E:.
3. Stop only the fallback controller, then keep its Tapo source at normal blend
   and its existing large transform while restarting the PTZ source update.
   This protects the picture while the virtual camera reconnects.
4. Verify V7 heartbeat/box updates, real subject-to-OBS alignment, and virtual
   camera recovery. If unsuccessful, restore the old PTZ and stop the trial.
5. Install together: `tapo_fallback_controller.js`, `wipe_overlap.js`, and the
   location-specific config. Preserve unrelated local settings and then set
   `overlap_transparency.enabled=true` for the agreed trial. Do not copy the
   entire repo or overwrite live credentials.
6. Start one location-specific fallback controller. Verify clear/overlap changes,
   delayed restoration, missing-box behavior, full-screen normal blending, and
   unchanged framing. Check live OBS frame counters and actual CPU usage.
7. Record the result before promoting candidate commits into the production
   branches. Do not report deployment from Git alone.

## Rollback

The fast feature rollback is setting `overlap_transparency.enabled=false`; the
controller returns to the configured static wipe blend on its next small-mode
poll. Leave the already additive legacy `wipe_blend_mode` unchanged. If the
controller itself is unhealthy, stop only that process, restore the baseline
controller/config backups, and launch the established location-specific helper.
The new helper module can remain unused. A producer-only geometry export is
backward compatible and need not force a PTZ restart solely to disable the trial.

RAW, E:, credentials, streaming/recording state, scheduled tasks, unrelated OBS
schedule changes, and remote chatbot processes are outside this feature's scope.

"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { BoxLossPolicy } = require("./box_loss");
const { modeDecision, readConfig } = require("./tapo_fallback_controller");
const options = { enabled: true, timeoutSec: 1.5, recoverSec: 3 };
function state(now, extra = {}) {
  return { tracking_enabled: true, detected: true, lost_stage: "seen", updated_at_epoch: now,
    subject_bbox: { coordinate_space: "capture_normalized", xyxy: [.3, .2, .7, .8],
      frame_width: 1920, frame_height: 1080, observed_at_epoch: now }, ...extra };
}

test("independent recovery uses BOX observations, not the PTZ lost stage", () => {
  const p = new BoxLossPolicy();
  for (let i = 0; i <= 6; i++) {
    const now = 100 + i/2;
    assert.equal(p.step(state(now, { lost_stage: "search" }), now, options).mode,
      i === 6 ? "small" : null);
  }
});

test("no state at startup falls back after 1.5 seconds", () => {
  const p = new BoxLossPolicy();
  assert.equal(p.step(null, 100, options).mode, null);
  assert.equal(p.step(null, 101.4, options).mode, null);
  assert.equal(p.step(null, 101.5, options).mode, "large");
});

test("frozen state and a frozen BOX with a fresh state heartbeat both expire", () => {
  for (const heartbeat of [false, true]) {
    const p = new BoxLossPolicy(), s = state(100);
    for (let i = 0; i <= 15; i++) {
      const now = 100 + i/10;
      if (heartbeat) s.updated_at_epoch = now;
      const result = p.step(s, now, options);
      assert.equal(result.mode, i === 15 ? "large" : null);
    }
  }
  assert.equal(new BoxLossPolicy().step(state(90), 100, options).mode, "large");
});

test("brief missing detection does not expand and requires a new BOX to recover", () => {
  const p = new BoxLossPolicy();
  p.step(state(100), 100, options);
  assert.equal(p.step(state(100.5, { detected: false }), 100.5, options).mode, null);
  assert.equal(p.step(state(100), 100.6, options).reason, "box_missing");
  assert.equal(p.step(state(101), 101, options).mode, null);
  for (const now of [101.5, 102, 102.5, 103, 103.5]) {
    assert.equal(p.step(state(now), now, options).mode, null);
  }
  assert.equal(p.step(state(104), 104, options).mode, "small");
});

test("fresh invalid detections trigger loss, regardless of a seen label", () => {
  const invalid = [
    s => ({ ...s, detected: false }),
    s => ({ ...s, tracking_enabled: false }),
    s => ({ ...s, subject_bbox: null }),
    s => ({ ...s, subject_bbox: { ...s.subject_bbox, xyxy: [0, 0, 0, 1] } }),
    s => ({ ...s, subject_bbox: { ...s.subject_bbox, xyxy: [0, 0, NaN, 1] } }),
    s => ({ ...s, subject_bbox: { ...s.subject_bbox, coordinate_space: "unknown" } }),
    s => ({ ...s, subject_bbox: { ...s.subject_bbox, observed_at_epoch: s.updated_at_epoch + 10 } }),
  ];
  for (const mutate of invalid) {
    const p = new BoxLossPolicy();
    assert.equal(p.step(mutate(state(100)), 100, options).mode, null);
    assert.equal(p.step(mutate(state(101.5)), 101.5, options).mode, "large");
  }
});

test("regressing timestamps cannot reset loss or count toward recovery", () => {
  const p = new BoxLossPolicy();
  p.step(state(100), 100, options);
  assert.equal(p.step(state(99.9), 100.1, options).reason, "box_missing");
  assert.equal(p.step(state(99.9), 101.5, options).mode, "large");
  p.step(state(102), 102, options);
  assert.equal(p.step(state(103, { updated_at_epoch: 101.9 }), 103, options).mode, null);
  assert.equal(p.healthySince, null);
});

test("a long observation gap or backward clock restarts recovery", () => {
  const p = new BoxLossPolicy();
  p.step(state(100), 100, options);
  p.step(state(101), 101, options);
  assert.equal(p.step(state(105), 105, options).mode, null);
  assert.equal(p.healthySince, 105);
  assert.equal(p.step(state(50), 50, options).mode, null);
  assert.equal(p.healthySince, 50);
});

test("mode selection has no second loss/recovery wait and retains manual priority", () => {
  const c = readConfig(require("node:path").join(__dirname, "tapo_fallback_config_shataku.json"));
  assert.equal(c.boxLoss.enabled, false);
  c.boxLoss = options;
  const p = new BoxLossPolicy();
  modeDecision(c, null, 100, p);
  assert.deepEqual(modeDecision(c, null, 101.5, p),
    { mode: "large", reason: "box_missing", missingSec: 1.5, waitSec: 0 });
  for (const now of [102, 102.5, 103, 103.5, 104, 104.5]) modeDecision(c, state(now), now, p);
  const recovered = modeDecision(c, state(105), 105, p);
  assert.equal(recovered.mode, "small");
  assert.equal(recovered.waitSec, 0);
  for (const [manual, expected] of [["wipe", "small"], ["large", "large"], ["disabled", null]]) {
    c.manualOverride = manual;
    assert.equal(modeDecision(c, null, 110, p).mode, expected);
    assert.equal(p.lastObservation, null);
  }
  c.manualOverride = "auto";
  c.boxLoss = { ...options, enabled: false };
  assert.equal(modeDecision(c, state(110, { lost_stage: "search" }), 110, p).mode, "large");
});

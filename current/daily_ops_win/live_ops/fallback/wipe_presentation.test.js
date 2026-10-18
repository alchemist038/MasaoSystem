"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { updateWipePresentation, desiredMode, readConfig } = require("./tapo_fallback_controller");
const { sizingOptions, AdaptiveWipePolicy } = require("./adaptive_wipe");
const { OverlapPolicy, NORMAL, TRANSPARENT } = require("./wipe_overlap");

const transform = { sourceWidth: 1920, sourceHeight: 1080, width: 1920, height: 1080,
  positionX: 0, positionY: 0, scaleX: 1, scaleY: 1, cropLeft: 0, cropRight: 0,
  cropTop: 0, cropBottom: 0, rotation: 0, alignment: 5, boundsType: "OBS_BOUNDS_NONE" };
function fixture() {
  const config = readConfig(require("node:path").join(__dirname, "tapo_fallback_config_shataku.json"));
  config.adaptive = sizingOptions({ enabled: true, min_width: 320, max_width: 500 });
  config.overlap.enabled = true;
  const wipe = { sourceName: "tapoc232", sceneItemId: 5, sceneItemEnabled: true,
    sceneItemBlendMode: NORMAL, sceneItemTransform: { ...transform, sourceWidth: 2880,
      sourceHeight: 1620, width: 320, height: 180, scaleX: 320/2880, scaleY: 180/1620 } };
  const subject = { sourceName: "OBSBOT VC", sceneItemId: 3, sceneItemEnabled: true,
    sceneItemTransform: { ...transform } };
  const calls = [];
  const obs = { async request(type, data) {
    calls.push({ type, data });
    if (type === "GetSceneItemList") return { sceneItems: structuredClone([subject, wipe]) };
    if (type === "GetVideoSettings") return { baseWidth: 1920, baseHeight: 1080 };
    if (type === "GetSceneItemBlendMode") return { sceneItemBlendMode: wipe.sceneItemBlendMode };
    if (type === "SetSceneItemBlendMode") { wipe.sceneItemBlendMode = data.sceneItemBlendMode; return {}; }
    if (type === "SetSceneItemTransform") {
      Object.assign(wipe.sceneItemTransform, data.sceneItemTransform);
      wipe.sceneItemTransform.width = wipe.sceneItemTransform.scaleX * 2880;
      wipe.sceneItemTransform.height = wipe.sceneItemTransform.scaleY * 1620;
      return {};
    }
    throw new Error("Unexpected OBS request: " + type);
  } };
  const policies = { adaptive: new AdaptiveWipePolicy(), overlap: new OverlapPolicy() };
  return { config, wipe, subject, calls, policies,
    tick(state, now, mode = "small", dryRun = false) {
      return updateWipePresentation(obs, config, state, now, mode, policies, dryRun, () => {});
    } };
}
function state(box, now) {
  return { tracking_enabled: true, detected: true, lost_stage: "seen", updated_at_epoch: now,
    subject_bbox: { coordinate_space: "capture_normalized", xyxy: box,
      frame_width: 1920, frame_height: 1080, observed_at_epoch: now } };
}
const overlapping = [0, 0, .1, .1], clear = [.6, .6, .9, .9];

test("combined resizing and overlap never alternate normal/additive on each tick", async () => {
  const f = fixture();
  for (let i = 0; i < 100; i++) {
    const now = 100 + i/10;
    await f.tick(state(overlapping, now), now);
    const t = f.wipe.sceneItemTransform;
    assert.ok(t.width >= 320 && t.width <= 500);
    assert.ok(Math.abs(t.height/t.width - 9/16) < 1e-10);
    assert.equal(f.wipe.sceneItemBlendMode, TRANSPARENT);
  }
  assert.ok(Math.abs(f.wipe.sceneItemTransform.width - 500) < 2);
  assert.equal(f.calls.filter(c => c.type === "SetSceneItemBlendMode").length, 1);
});

test("overlap checks the resized boundary from the same cycle", async () => {
  const f = fixture();
  f.config.overlap.marginPx = 0;
  const result = await f.tick(state([330/1920, 0, 400/1920, 80/1080], 100), 100);
  assert.ok(f.wipe.sceneItemTransform.width > 330);
  assert.equal(result.overlap.status, "overlap");
});

test("clear must remain continuous for one second while resizing continues", async () => {
  const f = fixture();
  await f.tick(state(overlapping, 100), 100);
  for (const now of [100.1, 100.6, 101]) {
    await f.tick(state(clear, now), now);
    assert.equal(f.wipe.sceneItemBlendMode, TRANSPARENT);
  }
  await f.tick(state(clear, 101.2), 101.2);
  assert.equal(f.wipe.sceneItemBlendMode, NORMAL);
  await f.tick(state(overlapping, 101.3), 101.3);
  assert.equal(f.wipe.sceneItemBlendMode, TRANSPARENT);
});

test("stale geometry holds size and uses see-through until trustworthy clear returns", async () => {
  const f = fixture();
  const result = await f.tick(state(clear, 90), 100);
  assert.equal(result.adaptive.status, "hold");
  assert.equal(result.overlap.status, "unknown");
  assert.equal(f.wipe.sceneItemTransform.width, 320);
  assert.equal(f.wipe.sceneItemBlendMode, TRANSPARENT);
});

test("large fallback and recovery wait retain exclusive control over the item", async () => {
  const f = fixture();
  f.policies.overlap.decide("clear", 99, 1);
  f.policies.adaptive.step(.1, 99, 320, f.config.adaptive);
  const lost = { ...state(overlapping, 100), lost_stage: "search", detected: false };
  assert.equal(desiredMode(f.config, lost, 100), "large");
  assert.equal(f.config.largeBlendMode, NORMAL);
  assert.equal((await f.tick(lost, 100, "large")).status, "inactive");
  assert.equal((await f.tick(state(clear, 101), 101, "large")).status, "inactive");
  assert.equal(f.calls.length, 0);
  assert.equal(f.policies.adaptive.target, null);
  assert.equal(f.policies.overlap.clearSince, null);
});

test("overlap disabled keeps legacy opaque adaptive behavior; disabling control makes no calls", async () => {
  const f = fixture();
  f.wipe.sceneItemBlendMode = TRANSPARENT;
  f.config.overlap.enabled = false;
  await f.tick(state(overlapping, 100), 100);
  assert.equal(f.wipe.sceneItemBlendMode, NORMAL);
  f.config.manualOverride = "disabled";
  f.calls.length = 0;
  await f.tick(state(overlapping, 101), 101);
  assert.equal(f.calls.length, 0);
});

test("combined dry run never writes or changes the actual wipe", async () => {
  const f = fixture();
  await f.tick(state(overlapping, 100), 100, "small", true);
  assert.equal(f.calls.filter(c => c.type.startsWith("Set")).length, 0);
  assert.equal(f.wipe.sceneItemTransform.width, 320);
  assert.equal(f.wipe.sceneItemBlendMode, NORMAL);
});

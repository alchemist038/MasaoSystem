"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { updateWipePresentation, desiredMode, readConfig, applyModeToObs } = require("./tapo_fallback_controller");
const { sizingOptions, AdaptiveWipePolicy, PositionWipePolicy } = require("./adaptive_wipe");
const { BoxLossPolicy } = require("./box_loss");
const { modeDecision } = require("./tapo_fallback_controller");
const { OverlapPolicy, NORMAL, TRANSPARENT } = require("./wipe_overlap");

const transform = { sourceWidth: 1920, sourceHeight: 1080, width: 1920, height: 1080,
  positionX: 0, positionY: 0, scaleX: 1, scaleY: 1, cropLeft: 0, cropRight: 0,
  cropTop: 0, cropBottom: 0, rotation: 0, alignment: 5, boundsType: "OBS_BOUNDS_NONE" };
function fixture(opacityMode = false) {
  const config = readConfig(require("node:path").join(__dirname, "tapo_fallback_config_shataku.json"));
  config.adaptive = sizingOptions({ enabled: true, min_width: 320, max_width: 500 });
  config.overlap.enabled = true;
  config.overlap.mode = opacityMode ? "opacity" : "blend";
  config.overlap.opacityPercent = 50;
  const wipe = { sourceName: "tapoc232", sceneItemId: 5, sceneItemEnabled: true,
    sceneItemBlendMode: NORMAL, sceneItemTransform: { ...transform, sourceWidth: 2880,
      sourceHeight: 1620, width: 320, height: 180, scaleX: 320/2880, scaleY: 180/1620 } };
  const subject = { sourceName: "OBSBOT VC", sceneItemId: 3, sceneItemEnabled: true,
    sceneItemTransform: { ...transform } };
  const calls = [];
  const obs = { program: config.targetScene, filters: [], async request(type, data) {
    calls.push({ type, data });
    if (type === "GetCurrentProgramScene") return { currentProgramSceneName: this.program };
    if (type === "GetSourceFilterList") return { filters: structuredClone(this.filters) };
    if (type === "CreateSourceFilter") {
      this.filters.push({ filterName: data.filterName, filterKind: data.filterKind,
        filterEnabled: true, filterSettings: { ...data.filterSettings } }); return {};
    }
    if (type === "SetSourceFilterSettings") {
      Object.assign(this.filters.find(f => f.filterName === data.filterName).filterSettings, data.filterSettings);
      return {};
    }
    if (type === "SetSourceFilterEnabled") {
      this.filters.find(f => f.filterName === data.filterName).filterEnabled = data.filterEnabled;
      return {};
    }
    if (type === "GetSceneItemTransform") return { sceneItemTransform: { ...wipe.sceneItemTransform } };
    if (type === "SetSceneItemEnabled") { wipe.sceneItemEnabled = data.sceneItemEnabled; return {}; }
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
  return { config, wipe, subject, calls, policies, obs,
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

test("opacity mode uses stable normal blend at50 percent, then100 after clear delay", async () => {
  const f = fixture(true);
  f.wipe.sceneItemBlendMode = TRANSPARENT;
  for (const now of [100, 100.1, 100.2]) await f.tick(state(overlapping, now), now);
  assert.equal(f.obs.filters[0].filterSettings.opacity, .5);
  assert.equal(f.wipe.sceneItemBlendMode, NORMAL);
  assert.equal(f.calls.filter(c => c.type === "CreateSourceFilter").length, 1);
  assert.equal(f.calls.filter(c => c.type === "SetSourceFilterSettings").length, 0);
  await f.tick(state(clear, 101), 101);
  await f.tick(state(clear, 101.9), 101.9);
  assert.equal(f.obs.filters[0].filterSettings.opacity, .5);
  await f.tick(state(clear, 102), 102);
  assert.equal(f.obs.filters[0].filterSettings.opacity, 1);
});

test("full-screen transition restores100 percent before enlarging the wipe", async () => {
  const f = fixture(true);
  await f.tick(state(overlapping, 100), 100);
  f.config.transitionEnabled = false;
  f.calls.length = 0;
  await applyModeToObs(f.obs, f.config, "large", false, () => {});
  const opacityWrite = f.calls.findIndex(c => c.type === "SetSourceFilterSettings" && c.data.filterSettings.opacity === 1);
  const transformWrite = f.calls.findIndex(c => c.type === "SetSceneItemTransform");
  assert.ok(opacityWrite >= 0 && opacityWrite < transformWrite);
  assert.equal(f.wipe.sceneItemTransform.width, 1920);
  assert.equal(f.wipe.sceneItemBlendMode, NORMAL);
  assert.equal(f.obs.filters[0].filterSettings.opacity, 1);
});

test("shared source is opaque in other program scenes and after disabling control", async () => {
  const f = fixture(true);
  await f.tick(state(overlapping, 100), 100);
  f.obs.program = "another scene";
  assert.equal((await f.tick(state(overlapping, 101), 101)).status, "inactive_scene");
  assert.equal(f.obs.filters[0].filterSettings.opacity, 1);
  f.obs.program = f.config.targetScene;
  await f.tick(state(overlapping, 102), 102);
  assert.equal(f.obs.filters[0].filterSettings.opacity, .5);
  f.config.enabled = false;
  await f.tick(state(overlapping, 103), 103);
  assert.equal(f.obs.filters[0].filterSettings.opacity, 1);
});

test("opacity options retain unrelated filters/settings, disable and honor dry run", async () => {
  const f = fixture(true);
  await f.tick(state(overlapping, 100), 100, "small", true);
  assert.equal(f.obs.filters.length, 0);
  assert.equal(f.calls.filter(c => /^(Set|Create)/.test(c.type)).length, 0);
  await f.tick(state(overlapping, 101), 101);
  f.obs.filters[0].filterSettings.contrast = .2;
  f.obs.filters.push({ filterName: "User filter", filterKind: "other", filterSettings: { opacity: .7 } });
  f.config.overlap.opacityPercent = 70;
  await f.tick(state(overlapping, 102), 102);
  assert.equal(f.obs.filters[0].filterSettings.opacity, .7);
  assert.equal(f.obs.filters[0].filterSettings.contrast, .2);
  assert.equal(f.obs.filters[1].filterSettings.opacity, .7);
  f.config.overlap.enabled = false;
  await f.tick(state(overlapping, 103), 103);
  assert.equal(f.obs.filters[0].filterSettings.opacity, 1);
});

test("a managed filter name collision fails without changing user filters", async () => {
  const f = fixture(true);
  f.obs.filters.push({ filterName: "Masao Wipe Opacity", filterKind: "color_filter",
    filterEnabled: true, filterSettings: { opacity: 80 } });
  await assert.rejects(f.tick(state(overlapping, 100), 100), /another filter kind/);
  assert.equal(f.obs.filters[0].filterSettings.opacity, 80);
});

test("X resizing and independent loss preserve full-screen opacity and recovery priority", async () => {
  const f = fixture(true);
  f.config.adaptive = { ...sizingOptions({ enabled: true, mode: "x_position", min_width: 450, max_width: 600 }), requireSeen: false };
  f.config.overlap.requireSeen = false;
  f.config.boxLoss = { enabled: true, timeoutSec: 1.5, recoverSec: 3 };
  f.config.transitionEnabled = false;
  f.config.wipeTransform = { ...transform, sourceWidth: 2880, sourceHeight: 1620,
    width: 450, height: 450*9/16, scaleX: 450/2880, scaleY: 450/2880 };
  f.policies.adaptive = new PositionWipePolicy();
  const loss = new BoxLossPolicy();
  let mode = null;
  const run = async (s, now) => {
    const decision = modeDecision(f.config, s, now, loss);
    if (decision.mode && decision.mode !== mode) {
      await applyModeToObs(f.obs, f.config, decision.mode, false, () => {});
      mode = decision.mode;
      f.policies.adaptive.reset(); f.policies.overlap.reset();
    }
    return f.tick(s, now, mode);
  };
  for (let i = 0; i < 100; i++) {
    const now = 100+i/10;
    await run({ ...state(clear, now), lost_stage: "search" }, now);
  }
  assert.equal(mode, "small");
  assert.equal(f.wipe.sceneItemTransform.width, 600);
  assert.equal(f.obs.filters[0].filterSettings.opacity, 1);
  for (let i = 0; i < 60; i++) await run(state(overlapping, 110+i/10), 110+i/10);
  assert.equal(f.wipe.sceneItemTransform.width, 450);
  assert.equal(f.obs.filters[0].filterSettings.opacity, .5);
  const frozen = state(clear, 116);
  await run(frozen, 116);
  await run(frozen, 117.5);
  assert.equal(mode, "large");
  assert.equal(f.wipe.sceneItemTransform.width, 1920);
  assert.equal(f.obs.filters[0].filterSettings.opacity, 1);
  for (const now of [118, 118.5, 119, 119.5, 120, 120.5]) {
    await run(state(clear, now), now);
    assert.equal(f.wipe.sceneItemTransform.width, 1920);
  }
  await run(state(clear, 121), 121);
  assert.equal(mode, "small");
  assert.equal(f.wipe.sceneItemTransform.width, 450);
});

test("X-only overlap with separated Y stays opaque, then XY overlap fades", async () => {
  const f = fixture(true);
  f.config.adaptive = sizingOptions({ enabled: true, mode: "x_position", min_width: 450, max_width: 600 });
  f.policies.adaptive = new PositionWipePolicy();
  const below = [0, .6, .2, .9];
  for (let i = 0; i < 30; i++) await f.tick(state(below, 100+i/10), 100+i/10);
  assert.equal(f.wipe.sceneItemTransform.width, 450);
  assert.equal(f.obs.filters[0].filterSettings.opacity, 1);
  await f.tick(state(overlapping, 103), 103);
  assert.equal(f.wipe.sceneItemTransform.width, 450);
  assert.equal(f.obs.filters[0].filterSettings.opacity, .5);
  await f.tick(state(below, 103.1), 103.1);
  await f.tick(state(below, 104.2), 104.2);
  assert.equal(f.obs.filters[0].filterSettings.opacity, 1);
  assert.equal(f.wipe.sceneItemTransform.width, 450);
});

test("even a small positive Y gap does not fade the X-position wipe", async () => {
  const f = fixture(true);
  f.config.adaptive = sizingOptions({ enabled: true, mode: "x_position", min_width: 450, max_width: 600 });
  f.config.overlap.marginYPx = 0;
  f.policies.adaptive = new PositionWipePolicy();
  const below = [0, (450*9/16 + 1)/1080, .2, .8];
  for (const now of [100, 100.5, 101.1]) await f.tick(state(below, now), now);
  assert.equal(f.wipe.sceneItemTransform.width, 450);
  assert.equal(f.obs.filters[0].filterSettings.opacity, 1);
  const overlappingY = [0, (450*9/16 - 1)/1080, .2, .8];
  await f.tick(state(overlappingY, 102), 102);
  assert.equal(f.obs.filters[0].filterSettings.opacity, .5);
});

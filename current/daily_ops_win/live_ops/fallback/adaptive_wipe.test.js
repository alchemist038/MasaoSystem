"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { sizingOptions, widthForArea, areaOnCanvas, AdaptiveWipePolicy, updateAdaptiveWipe } = require("./adaptive_wipe");
const { readConfig, desiredMode } = require("./tapo_fallback_controller");
const options = sizingOptions({ enabled: true });
const transform = { sourceWidth: 1920, sourceHeight: 1080, width: 1920, height: 1080,
  positionX: 0, positionY: 0, scaleX: 1, scaleY: 1, cropLeft: 0, cropRight: 0,
  cropTop: 0, cropBottom: 0, rotation: 0, alignment: 5, boundsType: "OBS_BOUNDS_NONE" };
const subject = { sourceName: "OBSBOT VC", sceneItemId: 3, sceneItemEnabled: true, sceneItemTransform: transform };
const video = { baseWidth: 1920, baseHeight: 1080 };
function state(box = [.1, .1, .6, .6], now = 100) {
  return { tracking_enabled: true, detected: true, lost_stage: "seen", updated_at_epoch: now,
    subject_bbox: { coordinate_space: "capture_normalized", xyxy: box, frame_width: 1920,
      frame_height: 1080, observed_at_epoch: now } };
}
function mockObs() {
  const wipe = { sourceName: "tapoc232", sceneItemId: 5, sceneItemEnabled: true,
    sceneItemBlendMode: "OBS_BLEND_ADDITIVE", sceneItemTransform: { ...transform,
      sourceWidth: 2880, sourceHeight: 1620, width: 277, height: 156,
      scaleX: 277/2880, scaleY: 156/1620 } };
  const calls = [];
  return { wipe, calls, items: [subject, wipe], async request(type, data) {
    calls.push({ type, data });
    if (type === "GetSceneItemList") return { sceneItems: this.items };
    if (type === "GetVideoSettings") return video;
    if (type === "SetSceneItemBlendMode") { wipe.sceneItemBlendMode = data.sceneItemBlendMode; return {}; }
    if (type === "SetSceneItemTransform") {
      Object.assign(wipe.sceneItemTransform, data.sceneItemTransform);
      wipe.sceneItemTransform.width = wipe.sceneItemTransform.scaleX * 2880;
      wipe.sceneItemTransform.height = wipe.sceneItemTransform.scaleY * 1620;
      return {};
    }
    throw new Error("Unexpected operation: " + type);
  } };
}
const config = { sourceName: "tapoc232", targetScene: "test", adaptive: options };

test("inverse continuous mapping and width clamps", () => {
  assert.equal(widthForArea(0, options), 640);
  assert.equal(widthForArea(.05, options), 640);
  assert.equal(widthForArea(.15, options), 445);
  assert.equal(widthForArea(.25, options), 250);
  assert.equal(widthForArea(1, options), 250);
  assert.ok(widthForArea(.16, options) < widthForArea(.15, options));
});
test("malformed sizing limits are bounded and have a nonzero area range", () => {
  const o = sizingOptions({ min_width: 400, max_width: 200, small_box_area: .5, large_box_area: .1, area_smoothing_sec: -1 });
  assert.equal(o.minWidth, o.maxWidth);
  assert.ok(o.largeArea > o.smallArea);
  assert.ok(o.areaSmoothingSec > 0);
});
test("visible bbox area is measured on canvas, including crop and clipping", () => {
  assert.equal(areaOnCanvas(state(), subject, video, 100, options), .25);
  const shifted = { ...subject, sceneItemTransform: { ...transform, positionX: 1920 } };
  assert.equal(areaOnCanvas(state(), shifted, video, 100, options), 0);
  const half = { ...subject, sceneItemTransform: { ...transform, scaleX: .5, scaleY: .5 } };
  assert.equal(areaOnCanvas(state(), half, video, 100, options), .0625);
});
test("invalid, stale, hidden, lost and unsupported subject data holds size", () => {
  for (const s of [null, {}, state(undefined, 90), state(undefined, 110),
    { ...state(), detected: false }, { ...state(), lost_stage: "search" },
    state([0, 0, null, 1]), state([0, 0, 0, 1])]) {
    assert.equal(areaOnCanvas(s, subject, video, 100, options), null);
  }
  assert.equal(areaOnCanvas(state(), { ...subject, sceneItemEnabled: false }, video, 100, options), null);
  assert.equal(areaOnCanvas(state(), { ...subject, sceneItemTransform: { ...transform, rotation: 1 } }, video, 100, options), null);
});
test("smoothing limits speed and converges to both exact endpoints", () => {
  const p = new AdaptiveWipePolicy(); let width = 277;
  for (let i = 0; i < 120; i++) {
    const next = p.step(.05, 100 + i/10, width, options);
    assert.ok(next >= width && next <= 640 && next - width <= 16.0001);
    width = next;
  }
  assert.equal(width, 640);
  for (let i = 0; i < 180; i++) {
    const next = p.step(.25, 112 + i/10, width, options);
    assert.ok(next <= width && next >= 250 && width - next <= 16.0001);
    width = next;
  }
  assert.equal(width, 250);
});
test("brief loss freezes actual width and cancels old resize momentum", () => {
  const p = new AdaptiveWipePolicy();
  p.step(.01, 100, 277, options);
  assert.equal(p.step(null, 100.1, 290, options), 290);
  assert.equal(p.target, null);
  assert.equal(p.area, null);
  assert.ok(p.step(.3, 100.2, 290, options) < 290);
});
test("small bbox jitter does not change the established target", () => {
  const p = new AdaptiveWipePolicy();
  p.step(.15, 100, 445, options);
  const target = p.target;
  for (let i = 1; i < 50; i++) p.step(.15 + (i%2 ? .0005 : -.0005), 100+i/10, 445, options);
  assert.equal(p.target, target);
});
test("live adapter is opaque, preserves anchor, keeps 16:9 and bounded width", async () => {
  const obs = mockObs(), p = new AdaptiveWipePolicy();
  for (let i = 0; i < 120; i++) {
    await updateAdaptiveWipe(obs, config, state([0, 0, .1, .1], 100+i/10), 100+i/10, p, false, () => {});
    const t = obs.wipe.sceneItemTransform;
    assert.ok(t.width >= 250 && t.width <= 640);
    assert.ok(Math.abs(t.height/t.width - 9/16) < 1e-10);
  }
  assert.equal(obs.wipe.sceneItemBlendMode, "OBS_BLEND_NORMAL");
  assert.ok(obs.calls.filter(c => c.type === "SetSceneItemTransform").every(c =>
    Object.keys(c.data.sceneItemTransform).sort().join(",") === "scaleX,scaleY"));
  assert.ok(obs.calls.filter(c => c.type === "SetSceneItemBlendMode").every(c => c.data.sceneItemBlendMode === "OBS_BLEND_NORMAL"));
});
test("dry run makes no OBS writes", async () => {
  const obs = mockObs();
  await updateAdaptiveWipe(obs, config, state(), 100, new AdaptiveWipePolicy(), true, () => {});
  assert.equal(obs.calls.filter(c => c.type.startsWith("Set")).length, 0);
});
test("unknown/duplicate subject and unsupported wipe never resize", async () => {
  for (const kind of ["missing", "duplicate", "crop", "rotation"]) {
    const obs = mockObs();
    if (kind === "missing") obs.items = [obs.wipe];
    if (kind === "duplicate") obs.items.push(subject);
    if (kind === "crop") obs.wipe.sceneItemTransform.cropTop = 10;
    if (kind === "rotation") obs.wipe.sceneItemTransform.rotation = 2;
    await updateAdaptiveWipe(obs, config, state(), 100, new AdaptiveWipePolicy(), false, () => {});
    assert.equal(obs.calls.filter(c => c.type === "SetSceneItemTransform").length, 0);
  }
  const obs = mockObs(); obs.items.push(obs.wipe);
  await assert.rejects(updateAdaptiveWipe(obs, config, state(), 100, new AdaptiveWipePolicy(), false, () => {}));
});
test("configuration remains opt-in and existing full-screen decision retains priority", () => {
  const c = readConfig(require("node:path").join(__dirname, "tapo_fallback_config_shataku.json"));
  assert.equal(c.adaptive.enabled, false);
  assert.equal(c.wipeBlendMode, "OBS_BLEND_NORMAL");
  assert.equal(desiredMode(c, { ...state(), lost_stage: "search" }, 100), "large");
  assert.equal(desiredMode(c, state(), 100), "small");
});

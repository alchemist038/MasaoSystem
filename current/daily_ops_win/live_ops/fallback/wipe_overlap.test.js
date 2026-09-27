const test = require("node:test");
const assert = require("node:assert/strict");
const { projectRect, overlapStatus, OverlapPolicy, updateWipeBlend, NORMAL, TRANSPARENT } = require("./wipe_overlap");
const { readConfig, desiredMode } = require("./tapo_fallback_controller");
const path = require("node:path");

const transform = { sourceWidth: 1920, sourceHeight: 1080, positionX: 0, positionY: 0,
  scaleX: 1, scaleY: 1, cropLeft: 0, cropRight: 0, cropTop: 0, cropBottom: 0,
  alignment: 5, rotation: 0, boundsType: "OBS_BOUNDS_NONE" };
const subject = { sourceName: "OBSBOT VC", sceneItemId: 3, sceneItemEnabled: true, sceneItemTransform: transform };
const wipe = { sourceName: "tapoc232", sceneItemId: 5, sceneItemEnabled: true,
  sceneItemTransform: { ...transform, scaleX: 507 / 1920, scaleY: 285 / 1080 } };
const options = { enabled: true, subjectSourceName: "OBSBOT VC", maxAgeSec: 1.5, restoreDelaySec: 1, marginPx: 16 };
function state(box = [.05, .05, .2, .2], now = 100) {
  return { tracking_enabled: true, detected: true, lost_stage: "seen", updated_at_epoch: now,
    subject_bbox: { coordinate_space: "capture_normalized", xyxy: box,
      frame_width: 1920, frame_height: 1080, observed_at_epoch: now } };
}
const config = { targetScene: "test", sourceName: "tapoc232", wipeBlendMode: TRANSPARENT, overlap: options };

test("inside, outside, enclosing and margin overlaps", () => {
  assert.equal(overlapStatus(state(), subject, wipe, 100, options), "overlap");
  assert.equal(overlapStatus(state([.6, .6, .9, .9]), subject, wipe, 100, options), "clear");
  assert.equal(overlapStatus(state([0, 0, 1, 1]), subject, wipe, 100, options), "overlap");
  assert.equal(overlapStatus(state([515/1920, .1, .5, .2]), subject, wipe, 100, options), "overlap");
});

test("missing, stale, future, malformed and lost data fail safely", () => {
  for (const s of [null, {}, state(undefined, 90), state(undefined, 110),
    { ...state(), detected: false }, { ...state(), tracking_enabled: false },
    { ...state(), lost_stage: "coast" }, state([null, 0, 1, 1]), state([0, 0, 0, 1]),
    state([0, 0, Infinity, 1]), { ...state(), subject_bbox: { ...state().subject_bbox, observed_at_epoch: 90 } }]) {
    assert.equal(overlapStatus(s, subject, wipe, 100, options), "unknown");
  }
});

test("unsupported or hidden geometry is unknown", () => {
  for (const changes of [{ rotation: 10 }, { boundsType: "OBS_BOUNDS_STRETCH" },
    { scaleX: -1 }, { sourceWidth: 0 }, { positionY: NaN }]) {
    assert.equal(overlapStatus(state(), { ...subject, sceneItemTransform: { ...transform, ...changes } }, wipe, 100, options), "unknown");
  }
  assert.equal(overlapStatus(state(), { ...subject, sceneItemEnabled: false }, wipe, 100, options), "unknown");
  assert.equal(overlapStatus(state(), null, wipe, 100, options), "unknown");
});

test("crop, translation, scale and center/right alignment", () => {
  assert.deepEqual(projectRect([.1, .1, .5, .5], transform), { left: 192, right: 960, top: 108, bottom: 540 });
  assert.deepEqual(projectRect([0, 0, 1, 1], { ...transform, cropLeft: 100, cropRight: 20, scaleX: .5, positionX: 100 }),
    { left: 100, right: 1000, top: 0, bottom: 1080 });
  assert.equal(projectRect([0, 0, .01, .01], { ...transform, cropLeft: 100 }).empty, true);
  assert.equal(projectRect([0, 0, 1, 1], { ...transform, alignment: 0, positionX: 960, positionY: 540 }).left, 0);
  assert.equal(projectRect([0, 0, 1, 1], { ...transform, alignment: 10, positionX: 1920, positionY: 1080 }).top, 0);
});

test("immediate transparency and delayed clear prevent flicker", () => {
  const p = new OverlapPolicy();
  assert.equal(p.decide("clear", 100, 1), TRANSPARENT);
  assert.equal(p.decide("clear", 100.5, 1), TRANSPARENT);
  assert.equal(p.decide("clear", 101, 1), NORMAL);
  assert.equal(p.decide("overlap", 101.1, 1), TRANSPARENT);
  assert.equal(p.decide("clear", 102, 1), TRANSPARENT);
  assert.equal(p.decide("unknown", 102.5, 1), TRANSPARENT);
  assert.equal(p.decide("clear", 103, 1), TRANSPARENT);
  assert.equal(p.decide("clear", 99, 1), TRANSPARENT);
});

function mockObs(items = [subject, wipe], initial = TRANSPARENT) {
  const calls = []; let blend = initial;
  return { calls, async request(type, data) {
    calls.push({ type, data });
    if (type === "GetSceneItemList") return { sceneItems: items };
    if (type === "GetSceneItemBlendMode") return { sceneItemBlendMode: blend };
    if (type === "SetSceneItemBlendMode") { blend = data.sceneItemBlendMode; return {}; }
    throw new Error("Unexpected OBS operation: " + type);
  } };
}

test("writes only on changes, respects dry run, no transforms", async () => {
  const obs = mockObs(), p = new OverlapPolicy();
  for (const t of [100, 100.5, 101, 101.5])
    await updateWipeBlend(obs, config, state([.6, .6, .9, .9], t), t, p, false, () => {});
  assert.equal(obs.calls.filter(x => x.type.startsWith("Set")).length, 1);
  await updateWipeBlend(obs, config, state(undefined, 102), 102, p, true, () => {});
  assert.equal(obs.calls.filter(x => x.type.startsWith("Set")).length, 1);
  await updateWipeBlend(obs, config, state(undefined, 103), 103, p, false, () => {});
  assert.equal(obs.calls.filter(x => x.type.startsWith("Set")).length, 2);
});

test("duplicate/missing subject stays transparent; duplicate wipe rejects", async () => {
  for (const items of [[wipe], [subject, subject, wipe]]) {
    const obs = mockObs(items, NORMAL);
    const result = await updateWipeBlend(obs, config, state(), 100, new OverlapPolicy(), false, () => {});
    assert.equal(result.blend, TRANSPARENT);
  }
  await assert.rejects(updateWipeBlend(mockObs([wipe, wipe]), config, state(), 100, new OverlapPolicy(), false, () => {}));
});

test("feature-off returns legacy blend; configuration starts disabled", async () => {
  const obs = mockObs(undefined, NORMAL);
  const result = await updateWipeBlend(obs, { ...config, overlap: { ...options, enabled: false } }, null, 100, new OverlapPolicy(), false, () => {});
  assert.equal(result.blend, TRANSPARENT);
  const c = readConfig(path.join(__dirname, "tapo_fallback_config_shataku.json"));
  assert.equal(c.overlap.enabled, false);
  assert.equal(c.largeBlendMode, NORMAL);
  assert.equal(desiredMode(c, { ...state(), lost_stage: "search" }, 100), "large");
  assert.equal(desiredMode(c, state(), 100), "small");
});

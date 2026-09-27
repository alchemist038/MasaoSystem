"use strict";
const { subjectRect, NORMAL } = require("./wipe_overlap");
const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

function sizingOptions(raw = {}) {
  const number = (key, fallback, lo, hi) => Number.isFinite(raw[key]) ? clamp(raw[key], lo, hi) : fallback;
  const minWidth = number("min_width", 250, 64, 1920);
  const maxWidth = Math.max(minWidth, number("max_width", 640, 64, 1920));
  const smallArea = number("small_box_area", .05, 0, .9);
  return {
    enabled: raw.enabled === true, minWidth, maxWidth, smallArea,
    largeArea: Math.max(smallArea + .01, number("large_box_area", .25, .01, 1)),
    areaSmoothingSec: number("area_smoothing_sec", 1, .1, 10),
    resizeSmoothingSec: number("resize_smoothing_sec", .45, .1, 5),
    maxSpeed: number("max_speed_px_sec", 160, 10, 1000),
    deadband: number("deadband_px", 8, 0, 32),
    maxAgeSec: number("max_age_sec", 1.5, .1, 5),
    subjectSourceName: raw.subject_source_name || "OBSBOT VC",
  };
}

function widthForArea(area, options) {
  const t = clamp((area - options.smallArea) / (options.largeArea - options.smallArea), 0, 1);
  return options.maxWidth - t * (options.maxWidth - options.minWidth);
}

function areaOnCanvas(state, subject, video, now, options) {
  if (!video || !Number.isFinite(video.baseWidth) || !Number.isFinite(video.baseHeight) ||
      video.baseWidth <= 0 || video.baseHeight <= 0) return null;
  const r = subjectRect(state, subject, now, options);
  if (!r || r.empty) return null;
  const width = Math.max(0, Math.min(video.baseWidth, r.right) - Math.max(0, r.left));
  const height = Math.max(0, Math.min(video.baseHeight, r.bottom) - Math.max(0, r.top));
  return width * height / (video.baseWidth * video.baseHeight);
}

class AdaptiveWipePolicy {
  constructor() { this.reset(); }
  reset() { this.area = null; this.target = null; this.lastNow = null; }
  step(area, now, actualWidth, options) {
    const dt = this.lastNow === null ? .1 : clamp(now - this.lastNow, 0, .5);
    this.lastNow = now;
    if (area === null || !Number.isFinite(area)) {
      this.area = null;
      this.target = null;
      return actualWidth;
    }
    this.area = this.area === null ? area : this.area + (area - this.area) * (1 - Math.exp(-dt / options.areaSmoothingSec));
    let proposed = widthForArea(this.area, options);
    if (proposed - options.minWidth < .5) proposed = options.minWidth;
    if (options.maxWidth - proposed < .5) proposed = options.maxWidth;
    if (this.target === null || Math.abs(proposed - this.target) >= options.deadband ||
        proposed === options.minWidth || proposed === options.maxWidth) this.target = proposed;
    const difference = this.target - actualWidth;
    const step = difference * (1 - Math.exp(-dt / options.resizeSmoothingSec));
    const width = actualWidth + clamp(step, -options.maxSpeed * dt, options.maxSpeed * dt);
    return clamp(Math.abs(difference) < .5 ? this.target : width, options.minWidth, options.maxWidth);
  }
}

function supportedWipe(item) {
  const t = item?.sceneItemTransform;
  return !!item && !item.isGroup && item.sceneItemEnabled && t && t.boundsType === "OBS_BOUNDS_NONE" &&
    t.rotation === 0 && t.alignment === 5 && t.cropLeft === 0 && t.cropRight === 0 &&
    t.cropTop === 0 && t.cropBottom === 0 && Number.isFinite(t.sourceWidth) && t.sourceWidth > 0 &&
    Number.isFinite(t.sourceHeight) && t.sourceHeight > 0 && Number.isFinite(t.scaleX) && t.scaleX > 0 &&
    Number.isFinite(t.scaleY) && t.scaleY > 0 && Number.isFinite(t.width) && t.width > 0;
}

async function updateAdaptiveWipe(obs, config, state, now, policy, dryRun, log) {
  const { sceneItems = [] } = await obs.request("GetSceneItemList", { sceneName: config.targetScene });
  const wipes = sceneItems.filter(i => i.sourceName === config.sourceName);
  if (wipes.length !== 1) throw new Error("Expected exactly one adaptive wipe");
  const wipe = wipes[0];
  const target = { sceneName: config.targetScene, sceneItemId: wipe.sceneItemId };
  if (wipe.sceneItemBlendMode !== NORMAL) {
    if (!dryRun) await obs.request("SetSceneItemBlendMode", { ...target, sceneItemBlendMode: NORMAL });
    log(`${dryRun ? "dry-run" : "applied"} adaptive blend: ${NORMAL}`);
  }
  if (!supportedWipe(wipe)) { policy.reset(); return { status: "unsupported" }; }
  const video = await obs.request("GetVideoSettings");
  const subjects = sceneItems.filter(i => i.sourceName === config.adaptive.subjectSourceName);
  const area = areaOnCanvas(state, subjects.length === 1 ? subjects[0] : null, video, now, config.adaptive);
  const t = wipe.sceneItemTransform;
  const width = policy.step(area, now, t.width, config.adaptive);
  if (area === null) return { status: "hold", width: t.width, area: null };
  const height = width * 9 / 16;
  if (Math.abs(width - t.width) >= .25 || Math.abs(height - t.height) >= .25) {
    if (!dryRun) await obs.request("SetSceneItemTransform", { ...target,
      sceneItemTransform: { scaleX: width / t.sourceWidth, scaleY: height / t.sourceHeight } });
  }
  return { status: "sizing", area, width, height, targetWidth: policy.target };
}

module.exports = { sizingOptions, widthForArea, areaOnCanvas, AdaptiveWipePolicy, updateAdaptiveWipe };

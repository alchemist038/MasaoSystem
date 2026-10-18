"use strict";

const NORMAL = "OBS_BLEND_NORMAL";
const TRANSPARENT = "OBS_BLEND_ADDITIVE";
const OPACITY_FILTER = "Masao Wipe Opacity";
const OPACITY_KIND = "color_filter_v2";

class OpacityFade {
  constructor() { this.reset(); }
  reset() { this.target = null; this.lastNow = null; this.lastValue = null; }
  step(target, actual, now, durationSec) {
    if (!(durationSec > 0)) { this.reset(); return target; }
    if (target !== this.target || this.lastNow === null || now < this.lastNow ||
        Math.abs(actual - this.lastValue) > .001) {
      this.from = actual;
      this.target = target;
      this.startedAt = now;
    }
    this.lastNow = now;
    const t = Math.max(0, Math.min(1, (now - this.startedAt) / durationSec));
    const eased = t * t * (3 - 2 * t);
    this.lastValue = this.from + (target - this.from) * eased;
    return this.lastValue;
  }
}

async function setWipeOpacity(obs, config, percent, dryRun, log, transition = null) {
  if (config.overlap?.mode !== "opacity") return;
  const target = { sourceName: config.sourceName, filterName: OPACITY_FILTER };
  const { filters = [] } = await obs.request("GetSourceFilterList", { sourceName: config.sourceName });
  const filter = filters.find(f => f.filterName === OPACITY_FILTER);
  const targetOpacity = Math.max(0, Math.min(100, percent)) / 100;
  if (filter && filter.filterKind !== OPACITY_KIND) {
    throw new Error("Managed opacity filter name is occupied by another filter kind");
  }
  const actual = filter?.filterEnabled ? (filter.filterSettings?.opacity ?? 1) : 1;
  // One interpolation step per control tick; never sleep or block loss detection.
  const opacity = transition ? transition.fade.step(targetOpacity, actual,
    transition.now, transition.durationSec) : targetOpacity;
  const description = `${(opacity * 100).toFixed(1)}% (target ${percent}%)`;
  if (!filter) {
    if (!dryRun) await obs.request("CreateSourceFilter", {
      ...target, filterKind: OPACITY_KIND, filterSettings: { opacity }
    });
    log(`${dryRun ? "dry-run" : "applied"} wipe opacity: ${description} (create)`);
    return opacity * 100;
  }
  if (Math.abs((filter.filterSettings?.opacity ?? 1) - opacity) > .0001) {
    if (!dryRun) await obs.request("SetSourceFilterSettings", {
      ...target, filterSettings: { opacity }, overlay: true
    });
    log(`${dryRun ? "dry-run" : "applied"} wipe opacity: ${description}`);
  }
  if (!filter.filterEnabled && opacity < 1 && !dryRun) {
    await obs.request("SetSourceFilterEnabled", { ...target, filterEnabled: true });
  }
  return opacity * 100;
}

function finite(value) {
  return typeof value === "number" && Number.isFinite(value);
}

// Unsupported transforms fail toward the existing see-through wipe.
function projectRect(box, t) {
  if (!t || t.boundsType !== "OBS_BOUNDS_NONE" || t.rotation !== 0) return null;
  const fields = [t.sourceWidth, t.sourceHeight, t.positionX, t.positionY,
    t.scaleX, t.scaleY, t.cropLeft, t.cropRight, t.cropTop, t.cropBottom, t.alignment];
  if (!fields.every(finite) || t.sourceWidth <= 0 || t.sourceHeight <= 0 ||
      t.scaleX <= 0 || t.scaleY <= 0 || !Number.isInteger(t.alignment)) return null;
  const w = t.sourceWidth - t.cropLeft - t.cropRight;
  const h = t.sourceHeight - t.cropTop - t.cropBottom;
  if (w <= 0 || h <= 0 || [t.cropLeft, t.cropRight, t.cropTop, t.cropBottom].some(v => v < 0)) return null;
  const x1 = Math.max(t.cropLeft, box[0] * t.sourceWidth);
  const y1 = Math.max(t.cropTop, box[1] * t.sourceHeight);
  const x2 = Math.min(t.sourceWidth - t.cropRight, box[2] * t.sourceWidth);
  const y2 = Math.min(t.sourceHeight - t.cropBottom, box[3] * t.sourceHeight);
  if (x2 <= x1 || y2 <= y1) return { empty: true };
  const width = w * Math.abs(t.scaleX), height = h * Math.abs(t.scaleY);
  const left = t.positionX - ((t.alignment & 1) ? 0 : (t.alignment & 2) ? width : width / 2);
  const top = t.positionY - ((t.alignment & 4) ? 0 : (t.alignment & 8) ? height : height / 2);
  const px = x => left + (t.scaleX > 0 ? x - t.cropLeft : t.sourceWidth - t.cropRight - x) * Math.abs(t.scaleX);
  const py = y => top + (t.scaleY > 0 ? y - t.cropTop : t.sourceHeight - t.cropBottom - y) * Math.abs(t.scaleY);
  return { left: Math.min(px(x1), px(x2)), right: Math.max(px(x1), px(x2)),
    top: Math.min(py(y1), py(y2)), bottom: Math.max(py(y1), py(y2)) };
}

function detectionBox(state, now, options) {
  const b = state?.subject_bbox;
  if (!finite(now) || !state || state.tracking_enabled !== true || state.detected !== true ||
      (options.requireSeen !== false && state.lost_stage !== "seen") || !finite(state.updated_at_epoch) ||
      now - state.updated_at_epoch > options.maxAgeSec || now < state.updated_at_epoch - 0.2 ||
      !b || b.coordinate_space !== "capture_normalized" || !finite(b.observed_at_epoch) ||
      now - b.observed_at_epoch > options.maxAgeSec || now < b.observed_at_epoch - 0.2 ||
      !finite(b.frame_width) || !finite(b.frame_height) || b.frame_width <= 0 || b.frame_height <= 0 ||
      !Array.isArray(b.xyxy) || b.xyxy.length !== 4 ||
      !b.xyxy.every(v => finite(v) && v >= 0 && v <= 1) ||
    b.xyxy[0] >= b.xyxy[2] || b.xyxy[1] >= b.xyxy[3]) return null;
  return b;
}

function subjectRect(state, subject, now, options) {
  const b = detectionBox(state, now, options);
  if (!b) return null;
  if (!subject || subject.isGroup || !subject.sceneItemEnabled) return null;
  return projectRect(b.xyxy, subject.sceneItemTransform);
}

function overlapStatus(state, subject, wipe, now, options) {
  if (!wipe || wipe.isGroup || !wipe.sceneItemEnabled) return "unknown";
  const a = subjectRect(state, subject, now, options);
  const c = projectRect([0, 0, 1, 1], wipe.sceneItemTransform);
  if (!a || !c) return "unknown";
  if (a.empty || c.empty) return "clear";
  const m = options.marginPx;
  const my = options.marginYPx ?? m;
  return a.right + m > c.left && a.left - m < c.right &&
    a.bottom + my > c.top && a.top - my < c.bottom ? "overlap" : "clear";
}

class OverlapPolicy {
  constructor() { this.opacityFade = new OpacityFade(); this.reset(); }
  reset() { this.clearSince = null; this.lastNow = null; this.opacityFade.reset(); }
  decide(status, now, restoreDelaySec) {
    if (this.lastNow !== null && now < this.lastNow) this.clearSince = null;
    this.lastNow = now;
    if (status !== "clear") {
      this.clearSince = null;
      return TRANSPARENT;
    }
    if (this.clearSince === null) this.clearSince = now;
    return now - this.clearSince >= restoreDelaySec ? NORMAL : TRANSPARENT;
  }
}

async function updateWipeBlend(obs, config, state, now, policy, dryRun, log) {
  const options = config.overlap;
  const { sceneItems = [] } = await obs.request("GetSceneItemList", { sceneName: config.targetScene });
  const wipes = sceneItems.filter(i => i.sourceName === config.sourceName);
  if (wipes.length !== 1) throw new Error("Expected exactly one wipe scene item");
  const wipe = wipes[0];
  const subjects = sceneItems.filter(i => i.sourceName === options.subjectSourceName);
  const status = options.enabled ? overlapStatus(state, subjects.length === 1 ? subjects[0] : null, wipe, now, options) : "disabled";
  const policyBlend = options.enabled ? policy.decide(status, now, options.restoreDelaySec) : config.wipeBlendMode;
  const usesOpacity = options.mode === "opacity";
  const desired = usesOpacity ? NORMAL : policyBlend;
  const opacityPercent = usesOpacity && options.enabled && policyBlend === TRANSPARENT
    ? options.opacityPercent : 100;
  const transition = usesOpacity && options.enabled && options.fadeDurationMs > 0
    ? { fade: policy.opacityFade, now, durationSec: options.fadeDurationMs / 1000 } : null;
  if (!transition) policy.opacityFade.reset();
  const appliedOpacityPercent = await setWipeOpacity(obs, config, opacityPercent, dryRun, log, transition);
  const args = { sceneName: config.targetScene, sceneItemId: wipe.sceneItemId };
  const actual = await obs.request("GetSceneItemBlendMode", args);
  if (actual.sceneItemBlendMode !== desired) {
    if (!dryRun) await obs.request("SetSceneItemBlendMode", { ...args, sceneItemBlendMode: desired });
    log(`${dryRun ? "dry-run" : "applied"} overlap: status=${status} blend=${desired}`);
  }
  return { status, blend: desired, ...(usesOpacity ? {
    opacityPercent: appliedOpacityPercent, targetOpacityPercent: opacityPercent } : {}) };
}

module.exports = { NORMAL, TRANSPARENT, OPACITY_FILTER, projectRect, detectionBox, subjectRect,
  overlapStatus, OverlapPolicy, OpacityFade, updateWipeBlend, setWipeOpacity };

"use strict";
const { detectionBox } = require("./wipe_overlap");

class BoxLossPolicy {
  constructor() { this.reset(); }
  reset() {
    this.lastNow = null;
    this.lastObservation = null;
    this.lastStateStamp = null;
    this.invalidSince = null;
    this.healthySince = null;
  }
  step(state, now, options) {
    if (this.lastNow !== null && now < this.lastNow) this.reset();
    this.lastNow = now;
    const timeout = options.timeoutSec;
    const b = detectionBox(state, now, { maxAgeSec: timeout, requireSeen: false });
    const stamps = [state?.updated_at_epoch, state?.subject_bbox?.observed_at_epoch];
    const stale = stamps.some(t => Number.isFinite(t) && t > 0 && now - t >= timeout) ||
      (this.lastObservation !== null && now - this.lastObservation >= timeout &&
        (!b || b.observed_at_epoch <= this.lastObservation));
    const advanced = b && (this.lastObservation === null || b.observed_at_epoch > this.lastObservation);
    const valid = b && !stale &&
      (this.lastStateStamp === null || state.updated_at_epoch >= this.lastStateStamp) &&
      (advanced || (b.observed_at_epoch === this.lastObservation && this.invalidSince === null));

    if (valid) {
      // A repeated cached BOX can never extend freshness or bridge a producer outage.
      if (advanced && this.lastObservation !== null && b.observed_at_epoch - this.lastObservation >= timeout) {
        this.healthySince = null;
      }
      this.lastObservation = b.observed_at_epoch;
      this.lastStateStamp = state.updated_at_epoch;
      this.invalidSince = null;
      if (this.healthySince === null) this.healthySince = now;
      return { mode: now - this.healthySince >= options.recoverSec ? "small" : null,
        reason: "box_valid", healthySec: now - this.healthySince };
    }
    this.healthySince = null;
    if (this.invalidSince === null) this.invalidSince = now;
    const expired = stale || now - this.invalidSince >= timeout;
    return { mode: expired ? "large" : null, reason: stale ? "box_stale" : "box_missing",
      missingSec: now - this.invalidSince };
  }
}

module.exports = { BoxLossPolicy };

"use strict";

// Read-only connectivity/geometry probe. Synthetic boxes never control OBS.
const { performance } = require("node:perf_hooks");
const { withObs, readConfig } = require("./tapo_fallback_controller");
const { OverlapPolicy, updateWipeBlend } = require("./wipe_overlap");
const path = require("node:path");

async function main() {
  const config = readConfig(path.join(__dirname, "tapo_fallback_config_shataku.json"));
  config.overlap.enabled = true;
  const policy = new OverlapPolicy();
  const cpuStart = process.cpuUsage(), started = performance.now();
  const durations = [], decisions = [];
  let readRequests = 0;
  await withObs(async client => {
    const obs = { request(type, data) {
      if (!type.startsWith("Get")) throw new Error("Read-only probe blocked: " + type);
      readRequests++;
      return client.request(type, data);
    } };
    const stream = await obs.request("GetStreamStatus");
    const before = await obs.request("GetStats");
    const filters = await obs.request("GetSourceFilterList", { sourceName: config.overlap.subjectSourceName });
    if (filters.filters.some(f => f.filterEnabled)) throw new Error("Verify active source filters before using coordinate mapping");
    for (let i = 0; i < 20; i++) {
      const t = Date.now() / 1000, tick = performance.now();
      const xyxy = i < 4 || i >= 14 ? [.02, .02, .2, .2] : [.6, .6, .9, .9];
      const state = { updated_at_epoch: t, tracking_enabled: true, detected: true, lost_stage: "seen",
        subject_bbox: { coordinate_space: "capture_normalized", xyxy, frame_width: 1920,
          frame_height: 1080, observed_at_epoch: t } };
      decisions.push(await updateWipeBlend(obs, config, state, t, policy, true, () => {}));
      durations.push(performance.now() - tick);
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    const after = await obs.request("GetStats");
    const cpu = process.cpuUsage(cpuStart), elapsedMs = performance.now() - started;
    console.log(JSON.stringify({ readOnly: true, syntheticBoxes: true, obsWrites: 0,
      streamActive: stream.outputActive, samples: durations.length, readRequests,
      elapsedMs, nodeCpuMs: (cpu.user + cpu.system) / 1000,
      meanTickMs: durations.reduce((a, b) => a + b, 0) / durations.length,
      maxTickMs: Math.max(...durations), decisions,
      obsBefore: before, obsAfter: after }, null, 2));
  });
}

if (require.main === module) {
  const deadline = setTimeout(() => { console.error("Probe deadline exceeded"); process.exit(2); }, 25000);
  main().catch(error => { console.error(error.message); process.exitCode = 1; }).finally(() => clearTimeout(deadline));
}

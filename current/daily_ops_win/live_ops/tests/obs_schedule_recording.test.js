const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { after, before, test } = require("node:test");

const schedule = require("../obs_scripts/obs_schedule.js");

let statusDir;

before(() => {
  statusDir = fs.mkdtempSync(path.join(os.tmpdir(), "masao-obs-recording-test-"));
  process.env.MASAO_OBS_RECORDING_STATUS_DIR = statusDir;
});

after(() => {
  delete process.env.MASAO_OBS_RECORDING_STATUS_DIR;
  fs.rmSync(statusDir, { recursive: true, force: true });
});

function fakeObs({ streamActive, recordingActive, outputPath }) {
  const state = { streamActive, recordingActive, outputPath };
  const calls = [];
  return {
    calls,
    async request(requestType) {
      calls.push(requestType);
      if (requestType === "GetStreamStatus") return { outputActive: state.streamActive };
      if (requestType === "GetRecordStatus") {
        return { outputActive: state.recordingActive, outputPath: state.outputPath };
      }
      if (requestType === "StartRecord") {
        state.recordingActive = true;
        return { outputPath: state.outputPath };
      }
      if (requestType === "StopRecord") {
        state.recordingActive = false;
        return { outputPath: state.outputPath };
      }
      throw new Error(`Unexpected OBS request: ${requestType}`);
    },
  };
}

const noWait = {
  autoStartGraceMs: 0,
  startTimeoutMs: 0,
  stopGraceMs: 0,
  stopTimeoutMs: 0,
  streamTimeoutMs: 0,
  fileTimeoutMs: 0,
};

test("reports an already-active OBS recording without starting another one", async () => {
  const raw = path.join(statusDir, "part1.mkv");
  const obs = fakeObs({ streamActive: true, recordingActive: true, outputPath: raw });
  const date = new Date(2026, 7, 18);

  const result = await schedule.ensureRecordingWithObs(obs, "part1", date, noWait);

  assert.equal(result.guardStarted, false);
  assert.equal(result.outputPath, raw);
  assert.equal(obs.calls.includes("StartRecord"), false);
  assert.equal(schedule.readRecordingState(date).parts.part1.startStatus, "ok");
});

test("starts recording when OBS did not auto-start it", async () => {
  const raw = path.join(statusDir, "part2.mkv");
  const obs = fakeObs({ streamActive: true, recordingActive: false, outputPath: raw });
  const date = new Date(2026, 7, 19);

  const result = await schedule.ensureRecordingWithObs(obs, "part2", date, noWait);

  assert.equal(result.guardStarted, true);
  assert.equal(obs.calls.filter((value) => value === "StartRecord").length, 1);
  assert.equal(schedule.readRecordingState(date).parts.part2.guardStarted, true);
});

test("stops a remaining recording and reports the final RAW file size", async () => {
  const raw = path.join(statusDir, "part3.mkv");
  fs.writeFileSync(raw, Buffer.alloc(4096));
  const obs = fakeObs({ streamActive: false, recordingActive: true, outputPath: raw });
  const date = new Date(2026, 7, 20);

  const result = await schedule.finalizeRecordingWithObs(obs, "part3", date, noWait);

  assert.equal(result.fileExists, true);
  assert.equal(result.fileBytes, 4096);
  assert.equal(result.guardStopped, true);
  assert.equal(obs.calls.filter((value) => value === "StopRecord").length, 1);
  assert.equal(schedule.readRecordingState(date).parts.part3.endStatus, "ok");
});

test("manual finalization refuses to stop recording while streaming", async () => {
  const obs = fakeObs({ streamActive: true, recordingActive: true, outputPath: "unused.mkv" });
  const date = new Date(2026, 7, 21);

  await assert.rejects(
    schedule.finalizeRecordingWithObs(obs, "part3", date, noWait),
    /まだ配信中/,
  );
  assert.equal(obs.calls.includes("StopRecord"), false);
});

test("reports the saved RAW file when OBS was already closed", async () => {
  const raw = path.join(statusDir, "closed-obs.mkv");
  fs.writeFileSync(raw, Buffer.alloc(8192));
  const date = new Date(2026, 7, 22);
  const stateFile = schedule.recordingStatusPath(date);
  fs.writeFileSync(stateFile, JSON.stringify({
    schemaVersion: 1,
    date: "2026-08-22",
    parts: { part3: { startedAt: new Date().toISOString(), outputPath: raw } },
  }));

  const result = await schedule.reportRecordingFileFromState("part3", date, noWait);

  assert.equal(result.obsDisconnected, true);
  assert.equal(result.fileExists, true);
  assert.equal(result.fileBytes, 8192);
  assert.equal(schedule.readRecordingState(date).parts.part3.endStatus, "ok");
});

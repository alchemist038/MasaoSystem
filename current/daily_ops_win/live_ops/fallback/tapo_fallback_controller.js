const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");

const DEFAULT_CONFIG_PATH = path.join(__dirname, "tapo_fallback_config.json");
const DEFAULT_LOG_DIR = "C:\\Users\\alche\\Desktop\\OBS\\logs";

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function dateKey(date = new Date()) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function timestamp() {
  return new Date().toLocaleString("ja-JP", { hour12: false });
}

function parseArgs() {
  const rawArgs = process.argv.slice(2);
  const args = new Set(rawArgs);
  const configArg = rawArgs.find((arg) => arg.startsWith("--config="));
  const intervalArg = rawArgs.find((arg) => arg.startsWith("--interval-ms="));
  return {
    configPath: configArg ? configArg.slice("--config=".length) : DEFAULT_CONFIG_PATH,
    once: args.has("--once"),
    dryRun: args.has("--dry-run"),
    intervalMs: intervalArg ? Number(intervalArg.slice("--interval-ms=".length)) : null,
  };
}

function readJsonFile(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function tryReadJsonFile(file) {
  try {
    return readJsonFile(file);
  } catch {
    return null;
  }
}

function numberFromConfig(value, fallback) {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function readConfig(file) {
  const config = tryReadJsonFile(file) || {};
  return {
    enabled: config.enabled !== false,
    statePath: config.state_path || "C:\\masao_ptz\\state\\v7_tracking_state.json",
    pollIntervalMs: numberFromConfig(config.poll_interval_ms, 500),
    stateStaleSec: numberFromConfig(config.state_stale_sec, 5),
    staleMode: config.stale_mode || "hold",
    trackingDisabledMode: config.tracking_disabled_mode || "wipe",
    targetScene: config.target_scene || "見守り 2",
    sourceName: config.source_name || "tapoc232",
    lostTriggerStage: config.lost_trigger_stage || "search",
    recoverTriggerStage: config.recover_trigger_stage || "seen",
    lostEnterWaitSec: numberFromConfig(config.lost_enter_wait_sec, 0),
    recoverExitWaitSec: numberFromConfig(config.recover_exit_wait_sec, 3),
    manualOverride: config.manual_override || "auto",
    largeTransformMode: config.large_transform_mode || "cover_canvas",
    transitionEnabled: config.transition_enabled !== false,
    expandDurationMs: numberFromConfig(config.expand_duration_ms, 1000),
    shrinkDurationMs: numberFromConfig(config.shrink_duration_ms, 1000),
    transitionSteps: Math.max(1, Math.round(numberFromConfig(config.transition_steps, 20))),
    wipeTransform: config.wipe_transform || null,
    largeTransform: config.large_transform || null,
    logDir: config.log_dir || DEFAULT_LOG_DIR,
  };
}

function makeLogger(logDir) {
  fs.mkdirSync(logDir, { recursive: true });
  const logPath = path.join(logDir, `tapo_fallback_controller_${dateKey()}.log`);
  return (message) => {
    const line = `[${timestamp()}] ${message}`;
    console.log(line);
    try {
      fs.appendFileSync(logPath, `${line}\n`, "utf8");
    } catch {
      // Console logging is enough if file logging is temporarily unavailable.
    }
  };
}

function obsConfigPath() {
  if (!process.env.APPDATA) throw new Error("APPDATA is not set.");
  return path.join(process.env.APPDATA, "obs-studio", "plugin_config", "obs-websocket", "config.json");
}

function readObsConfig() {
  const file = obsConfigPath();
  const config = JSON.parse(fs.readFileSync(file, "utf8"));
  const password = process.env.OBS_WEBSOCKET_PASSWORD || config.server_password || "";
  return {
    port: config.server_port || 4455,
    authRequired: !!config.auth_required,
    password,
  };
}

function sha256Base64(value) {
  return crypto.createHash("sha256").update(value).digest("base64");
}

function waitForMessage(ws) {
  return new Promise((resolve, reject) => {
    const onMessage = (event) => {
      cleanup();
      resolve(JSON.parse(event.data.toString()));
    };
    const onError = (event) => {
      cleanup();
      reject(event.error || new Error("WebSocket error"));
    };
    const onClose = () => {
      cleanup();
      reject(new Error("WebSocket closed before OBS responded."));
    };
    const cleanup = () => {
      ws.removeEventListener("message", onMessage);
      ws.removeEventListener("error", onError);
      ws.removeEventListener("close", onClose);
    };
    ws.addEventListener("message", onMessage);
    ws.addEventListener("error", onError);
    ws.addEventListener("close", onClose);
  });
}

async function connectObs() {
  const config = readObsConfig();
  const ws = new WebSocket(`ws://127.0.0.1:${config.port}`);

  await new Promise((resolve, reject) => {
    ws.addEventListener("open", resolve, { once: true });
    ws.addEventListener("error", (event) => reject(event.error || new Error("WebSocket open error")), { once: true });
  });

  const hello = await waitForMessage(ws);
  if (hello.op !== 0) throw new Error(`Unexpected OBS hello opcode: ${hello.op}`);

  const identify = { rpcVersion: 1, eventSubscriptions: 0 };
  const auth = hello.d && hello.d.authentication;
  if (config.authRequired || auth) {
    if (!config.password) throw new Error("OBS WebSocket password is required but not available.");
    const secret = sha256Base64(config.password + auth.salt);
    identify.authentication = sha256Base64(secret + auth.challenge);
  }

  ws.send(JSON.stringify({ op: 1, d: identify }));
  const identified = await waitForMessage(ws);
  if (identified.op !== 2) throw new Error(`OBS Identify failed: ${JSON.stringify(identified)}`);

  let nextRequestId = 1;
  const pending = new Map();

  ws.addEventListener("message", (event) => {
    const message = JSON.parse(event.data.toString());
    if (message.op !== 7 || !message.d) return;
    const pendingRequest = pending.get(message.d.requestId);
    if (!pendingRequest) return;
    pending.delete(message.d.requestId);
    const status = message.d.requestStatus || {};
    if (status.result) {
      pendingRequest.resolve(message.d.responseData || {});
    } else {
      pendingRequest.reject(new Error(`${message.d.requestType} failed: ${status.comment || status.code}`));
    }
  });

  ws.addEventListener("close", () => {
    for (const request of pending.values()) request.reject(new Error("OBS WebSocket closed."));
    pending.clear();
  });

  return {
    request(requestType, requestData = {}) {
      const requestId = String(nextRequestId++);
      const payload = { op: 6, d: { requestType, requestId, requestData } };
      return new Promise((resolve, reject) => {
        pending.set(requestId, { resolve, reject });
        ws.send(JSON.stringify(payload));
      });
    },
    close() {
      try {
        ws.close();
      } catch {
        // Nothing useful to do during shutdown.
      }
    },
  };
}

async function withObs(task) {
  const obs = await connectObs();
  try {
    return await task(obs);
  } finally {
    obs.close();
  }
}

async function findSceneItem(obs, sceneName, sourceName) {
  const list = await obs.request("GetSceneItemList", { sceneName });
  const sceneItems = list.sceneItems || [];
  const item = sceneItems.find((candidate) => candidate.sourceName === sourceName);
  if (!item) {
    const available = sceneItems.map((candidate) => candidate.sourceName).join(", ");
    throw new Error(`source not found: scene=${sceneName} source=${sourceName} available=[${available}]`);
  }
  return item;
}

function transformForObs(transform) {
  const keys = [
    "alignment",
    "boundsAlignment",
    "boundsHeight",
    "boundsType",
    "boundsWidth",
    "cropBottom",
    "cropLeft",
    "cropRight",
    "cropToBounds",
    "cropTop",
    "positionX",
    "positionY",
    "rotation",
    "scaleX",
    "scaleY",
  ];
  const payload = {};
  for (const key of keys) {
    if (Object.prototype.hasOwnProperty.call(transform, key)) payload[key] = transform[key];
  }
  return sanitizeTransformForObs(payload);
}

function sanitizeTransformForObs(transform) {
  const payload = { ...transform };
  if (payload.boundsType === "OBS_BOUNDS_NONE") {
    if (Number(payload.boundsWidth) <= 0) delete payload.boundsWidth;
    if (Number(payload.boundsHeight) <= 0) delete payload.boundsHeight;
  }
  return payload;
}

function computeLargeTransform(config, currentTransform, videoSettings) {
  if (config.largeTransform) return transformForObs(config.largeTransform);

  const baseWidth = Number(videoSettings.baseWidth || videoSettings.outputWidth || 1920);
  const baseHeight = Number(videoSettings.baseHeight || videoSettings.outputHeight || 1080);
  const sourceWidth = Number(currentTransform.sourceWidth || currentTransform.width / currentTransform.scaleX);
  const sourceHeight = Number(currentTransform.sourceHeight || currentTransform.height / currentTransform.scaleY);
  const scaleX = baseWidth / sourceWidth;
  const scaleY = baseHeight / sourceHeight;
  const scale = config.largeTransformMode === "contain_canvas" ? Math.min(scaleX, scaleY) : Math.max(scaleX, scaleY);
  const width = sourceWidth * scale;
  const height = sourceHeight * scale;
  return sanitizeTransformForObs({
    alignment: 5,
    boundsAlignment: 0,
    boundsType: "OBS_BOUNDS_NONE",
    boundsWidth: 0,
    boundsHeight: 0,
    cropToBounds: false,
    cropTop: 0,
    cropBottom: 0,
    cropLeft: 0,
    cropRight: 0,
    positionX: (baseWidth - width) / 2,
    positionY: (baseHeight - height) / 2,
    rotation: 0,
    scaleX: scale,
    scaleY: scale,
  });
}

function easeInOut(t) {
  return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
}

function lerp(start, end, t) {
  return start + (end - start) * t;
}

function interpolateTransform(start, end, t) {
  const payload = { ...end };
  const numericKeys = [
    "positionX",
    "positionY",
    "scaleX",
    "scaleY",
    "rotation",
    "cropTop",
    "cropBottom",
    "cropLeft",
    "cropRight",
  ];
  for (const key of numericKeys) {
    if (Number.isFinite(Number(start[key])) && Number.isFinite(Number(end[key]))) {
      payload[key] = lerp(Number(start[key]), Number(end[key]), t);
    }
  }
  return sanitizeTransformForObs(payload);
}

async function setSceneItemTransform(obs, sceneName, sceneItemId, transform) {
  await obs.request("SetSceneItemTransform", {
    sceneName,
    sceneItemId,
    sceneItemTransform: transform,
  });
}

async function applyTransformWithTransition(obs, config, sceneItemId, fromTransform, toTransform, mode, dryRun, log) {
  const durationMs = mode === "large" ? config.expandDurationMs : config.shrinkDurationMs;
  const steps = config.transitionEnabled && durationMs > 0 ? config.transitionSteps : 1;

  if (dryRun) {
    log(
      `dry-run: ${mode} scene=${config.targetScene} source=${config.sourceName} item=${sceneItemId} ` +
        `duration=${durationMs}ms steps=${steps} transform=${JSON.stringify(toTransform)}`
    );
    return;
  }

  for (let step = 1; step <= steps; step += 1) {
    const ratio = easeInOut(step / steps);
    const frameTransform = interpolateTransform(fromTransform, toTransform, ratio);
    await setSceneItemTransform(obs, config.targetScene, sceneItemId, frameTransform);
    if (step < steps && steps > 1) {
      await sleep(durationMs / steps);
    }
  }
}

async function applyMode(config, mode, dryRun, log) {
  await withObs(async (obs) => {
    const item = await findSceneItem(obs, config.targetScene, config.sourceName);
    const transformResponse = await obs.request("GetSceneItemTransform", {
      sceneName: config.targetScene,
      sceneItemId: item.sceneItemId,
    });
    const currentTransform = transformResponse.sceneItemTransform || {};
    const videoSettings = await obs.request("GetVideoSettings");
    const nextTransform =
      mode === "large"
        ? computeLargeTransform(config, currentTransform, videoSettings)
        : transformForObs(config.wipeTransform || currentTransform);

    if (!dryRun) {
      await obs.request("SetSceneItemEnabled", {
        sceneName: config.targetScene,
        sceneItemId: item.sceneItemId,
        sceneItemEnabled: true,
      });
    }
    await applyTransformWithTransition(
      obs,
      config,
      item.sceneItemId,
      transformForObs(currentTransform),
      nextTransform,
      mode,
      dryRun,
      log
    );
    if (!dryRun) {
      log(
        `applied: ${mode} scene=${config.targetScene} source=${config.sourceName} ` +
          `duration=${mode === "large" ? config.expandDurationMs : config.shrinkDurationMs}ms`
      );
    }
  });
}

function desiredMode(config, state, nowSec) {
  if (config.manualOverride === "large") return "large";
  if (config.manualOverride === "wipe" || config.manualOverride === "small") return "small";
  if (config.manualOverride === "disabled") return null;
  if (!state) return null;

  if (state.tracking_enabled === false) {
    if (config.trackingDisabledMode === "large") return "large";
    if (config.trackingDisabledMode === "hold") return null;
    return "small";
  }

  const ageSec = nowSec - Number(state.updated_at_epoch || 0);
  if (Number.isFinite(ageSec) && ageSec > config.stateStaleSec) {
    if (config.staleMode === "large") return "large";
    if (config.staleMode === "wipe" || config.staleMode === "small") return "small";
    return null;
  }

  if (state.lost_stage === config.lostTriggerStage) return "large";
  if (state.lost_stage === config.recoverTriggerStage) return "small";
  return null;
}

async function main() {
  const args = parseArgs();
  let currentMode = null;
  let pendingMode = null;
  let pendingSince = 0;
  let lastErrorMessage = "";
  let lastMissingStateLog = 0;
  let log = makeLogger(DEFAULT_LOG_DIR);

  do {
    const config = readConfig(args.configPath);
    log = makeLogger(config.logDir);
    const intervalMs = args.intervalMs || config.pollIntervalMs;
    const nowSec = Date.now() / 1000;

    try {
      if (!config.enabled) {
        if (args.once) break;
        await sleep(intervalMs);
        continue;
      }

      const state = tryReadJsonFile(config.statePath);
      if (!state && config.manualOverride === "auto" && nowSec - lastMissingStateLog > 30) {
        log(`waiting for V7 state: ${config.statePath}`);
        lastMissingStateLog = nowSec;
      }

      const mode = desiredMode(config, state, nowSec);
      if (!mode) {
        pendingMode = null;
        if (args.once) break;
        await sleep(intervalMs);
        continue;
      }

      if (mode !== pendingMode) {
        pendingMode = mode;
        pendingSince = nowSec;
        const waitSec = mode === "large" ? config.lostEnterWaitSec : config.recoverExitWaitSec;
        log(`pending: ${mode} wait=${waitSec.toFixed(1)}s lost_stage=${state ? state.lost_stage : "manual"}`);
      }

      const waitSec = mode === "large" ? config.lostEnterWaitSec : config.recoverExitWaitSec;
      if (nowSec - pendingSince >= waitSec && currentMode !== mode) {
        await applyMode(config, mode, args.dryRun, log);
        currentMode = mode;
      }
      lastErrorMessage = "";
    } catch (error) {
      const message = error && error.message ? error.message : String(error);
      if (message !== lastErrorMessage) {
        const detail = error && error.stack ? error.stack : message;
        log(`error: ${detail}`);
        lastErrorMessage = message;
      }
    }

    if (args.once) break;
    await sleep(intervalMs);
  } while (true);
}

main().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exit(1);
});

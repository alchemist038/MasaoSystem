"use strict";

const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

const SOURCE_NAME = "コメント読み上げ（配信）";
const LEGACY_TEST_SOURCE_NAME = "コメント読み上げ（配信テスト）";
const MAIN_BOUYOMI_SOURCE_NAME = "棒読みちゃん";
const INPUT_KIND = "wasapi_process_output_capture";
// Both BouyomiChan windows share the same title and can also share a WinForms
// class after restart. Match the renamed executables instead.
const PROCESS_MATCH_PRIORITY = 2;
const DEFAULT_VOLUME_DB = -13.086431503295898;
const FALLBACK_PRIVATE_WINDOW =
  "棒読みちゃん Ver0.1.11.0 Beta21:WindowsForms10.Window.8.app.0.1e84ccb_r7_ad1:BouyomiChanComments.exe";
const DEBUG = process.env.MASAO_OBS_BRIDGE_DEBUG === "1";

function debug(message) {
  if (DEBUG) process.stderr.write(`[obs_bridge] ${message}\n`);
}

function sleep(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

function obsConfigPath() {
  if (!process.env.APPDATA) throw new Error("APPDATA is not set.");
  return path.join(
    process.env.APPDATA,
    "obs-studio",
    "plugin_config",
    "obs-websocket",
    "config.json",
  );
}

function readObsConfig() {
  const config = JSON.parse(fs.readFileSync(obsConfigPath(), "utf8"));
  return {
    port: config.server_port || 4455,
    password: process.env.OBS_WEBSOCKET_PASSWORD || config.server_password || "",
  };
}

function sha256Base64(value) {
  return crypto.createHash("sha256").update(value).digest("base64");
}

async function connectObs() {
  debug("connect:start");
  const config = readObsConfig();
  const ws = new WebSocket(`ws://127.0.0.1:${config.port}`);
  const queuedMessages = [];
  const messageWaiters = [];
  const pending = new Map();
  let intentionallyClosing = false;

  function nextMessage() {
    if (queuedMessages.length) return Promise.resolve(queuedMessages.shift());
    return new Promise((resolve, reject) => messageWaiters.push({ resolve, reject }));
  }

  ws.addEventListener("message", (event) => {
    const message = JSON.parse(event.data.toString());
    debug(`message:op=${message.op}`);
    if (message.op === 7 && message.d) {
      const request = pending.get(message.d.requestId);
      if (request) {
        pending.delete(message.d.requestId);
        clearTimeout(request.timer);
        const status = message.d.requestStatus || {};
        if (status.result) {
          request.resolve(message.d.responseData || {});
        } else {
          request.reject(
            new Error(`${message.d.requestType}: ${status.comment || status.code}`),
          );
        }
        return;
      }
    }
    const waiter = messageWaiters.shift();
    if (waiter) waiter.resolve(message);
    else queuedMessages.push(message);
  });
  ws.addEventListener("close", () => {
    if (intentionallyClosing) return;
    const error = new Error("OBS WebSocket closed");
    for (const request of pending.values()) {
      clearTimeout(request.timer);
      request.reject(error);
    }
    pending.clear();
    for (const waiter of messageWaiters.splice(0)) waiter.reject(error);
  });

  await new Promise((resolve, reject) => {
    ws.addEventListener("open", resolve, { once: true });
    ws.addEventListener(
      "error",
      (event) => reject(event.error || new Error("WebSocket open error")),
      { once: true },
    );
  });
  debug("connect:open");

  const hello = await nextMessage();
  debug("connect:hello");
  if (hello.op !== 0) throw new Error(`Unexpected OBS hello opcode: ${hello.op}`);
  const identify = { rpcVersion: 1, eventSubscriptions: 0 };
  const auth = hello.d && hello.d.authentication;
  if (auth) {
    if (!config.password) throw new Error("OBS WebSocket password is unavailable");
    const secret = sha256Base64(config.password + auth.salt);
    identify.authentication = sha256Base64(secret + auth.challenge);
  }

  ws.send(JSON.stringify({ op: 1, d: identify }));
  const identified = await nextMessage();
  debug("connect:identified");
  if (identified.op !== 2) throw new Error("OBS WebSocket authentication failed");

  let nextRequestId = 1;
  return {
    request(requestType, requestData = {}) {
      const requestId = String(nextRequestId++);
      const payload = { op: 6, d: { requestType, requestId, requestData } };
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => {
          pending.delete(requestId);
          reject(new Error(`${requestType}: timed out`));
        }, 5000);
        pending.set(requestId, { resolve, reject, timer });
        debug(`request:${requestType}:${requestId}`);
        ws.send(JSON.stringify(payload));
      });
    },
    close() {
      intentionallyClosing = true;
      try {
        ws.close();
      } catch {
        // The process is exiting anyway.
      }
    },
  };
}

async function inputNames(obs) {
  const result = await obs.request("GetInputList");
  return new Set((result.inputs || []).map((input) => input.inputName));
}

async function currentScene(obs) {
  const result = await obs.request("GetCurrentProgramScene");
  return result.currentProgramSceneName;
}

async function processWindowValue(obs) {
  const names = await inputNames(obs);
  if (!names.has(MAIN_BOUYOMI_SOURCE_NAME)) {
    throw new Error("Existing stream BouyomiChan source was not found");
  }
  const result = await obs.request("GetInputPropertiesListPropertyItems", {
    inputName: MAIN_BOUYOMI_SOURCE_NAME,
    propertyName: "window",
  });
  const candidates = (result.propertyItems || []).filter((item) =>
    String(item.itemValue || "").endsWith(":BouyomiChanComments.exe"),
  );
  const preferred = candidates.find((item) =>
    String(item.itemValue || "").startsWith("棒読みちゃん Ver"),
  );
  const selected = preferred || candidates[0];
  return selected ? selected.itemValue : FALLBACK_PRIVATE_WINDOW;
}

async function findSceneItem(obs, sceneName, sourceName) {
  const result = await obs.request("GetSceneItemList", { sceneName });
  return (result.sceneItems || []).find((item) => item.sourceName === sourceName) || null;
}

async function addExistingSourceToScene(obs, destinationSceneName, sourceName) {
  const sceneList = await obs.request("GetSceneList");
  for (const scene of sceneList.scenes || []) {
    if (scene.sceneName === destinationSceneName) continue;
    const sourceItem = await findSceneItem(obs, scene.sceneName, sourceName);
    if (!sourceItem) continue;
    const duplicated = await obs.request("DuplicateSceneItem", {
      sceneName: scene.sceneName,
      sceneItemId: sourceItem.sceneItemId,
      destinationSceneName,
    });
    return duplicated.sceneItemId;
  }
  const created = await obs.request("CreateSceneItem", {
    sceneName: destinationSceneName,
    sourceName,
    sceneItemEnabled: true,
  });
  return created.sceneItemId;
}

async function enforceStrictProcessMatch(obs, inputName, expectedExecutable) {
  const current = await obs.request("GetInputSettings", { inputName });
  const window = current.inputSettings.window || "";
  if (!window.endsWith(`:${expectedExecutable}`)) {
    throw new Error(`${inputName} is not bound to ${expectedExecutable}`);
  }
  await obs.request("SetInputSettings", {
    inputName,
    inputSettings: { priority: PROCESS_MATCH_PRIORITY, window },
    overlay: true,
  });
  return window;
}

async function forceProcessRebind(obs, inputName, expectedExecutable) {
  const current = await obs.request("GetInputSettings", { inputName });
  const window = current.inputSettings.window || "";
  if (!window.endsWith(`:${expectedExecutable}`)) {
    throw new Error(`${inputName} is not bound to ${expectedExecutable}`);
  }
  await obs.request("SetInputSettings", {
    inputName,
    inputSettings: { priority: PROCESS_MATCH_PRIORITY, window: "" },
    overlay: false,
  });
  await sleep(3000);
  await obs.request("SetInputSettings", {
    inputName,
    inputSettings: { priority: PROCESS_MATCH_PRIORITY, window },
    overlay: false,
  });
  await sleep(3000);
}

async function ensureSource(obs) {
  const names = await inputNames(obs);
  const sceneName = await currentScene(obs);
  let window = "";
  let sceneItemId = null;

  if (!names.has(MAIN_BOUYOMI_SOURCE_NAME)) {
    throw new Error("Existing stream BouyomiChan source was not found");
  }
  await enforceStrictProcessMatch(obs, MAIN_BOUYOMI_SOURCE_NAME, "BouyomiChan.exe");

  if (!names.has(SOURCE_NAME)) {
    window = await processWindowValue(obs);
    const created = await obs.request("CreateInput", {
      sceneName,
      inputName: SOURCE_NAME,
      inputKind: INPUT_KIND,
      inputSettings: { priority: PROCESS_MATCH_PRIORITY, window },
      sceneItemEnabled: true,
    });
    sceneItemId = created.sceneItemId;
    await obs.request("SetInputMute", { inputName: SOURCE_NAME, inputMuted: true });
  } else {
    const currentSettings = await obs.request("GetInputSettings", { inputName: SOURCE_NAME });
    window = currentSettings.inputSettings.window || "";
    if (!window.endsWith(":BouyomiChanComments.exe")) {
      window = await processWindowValue(obs);
    }
    await obs.request("SetInputSettings", {
      inputName: SOURCE_NAME,
      inputSettings: { priority: PROCESS_MATCH_PRIORITY, window },
      overlay: true,
    });
    const existingItem = await findSceneItem(obs, sceneName, SOURCE_NAME);
    if (existingItem) {
      sceneItemId = existingItem.sceneItemId;
    } else {
      sceneItemId = await addExistingSourceToScene(obs, sceneName, SOURCE_NAME);
    }
  }

  await obs.request("SetSceneItemEnabled", {
    sceneName,
    sceneItemId,
    sceneItemEnabled: true,
  });
  await obs.request("SetInputVolume", {
    inputName: SOURCE_NAME,
    inputVolumeDb: DEFAULT_VOLUME_DB,
  });
  await obs.request("SetInputAudioBalance", {
    inputName: SOURCE_NAME,
    inputAudioBalance: 0.5,
  });
  await obs.request("SetInputAudioSyncOffset", {
    inputName: SOURCE_NAME,
    inputAudioSyncOffset: 0,
  });
  await obs.request("SetInputAudioMonitorType", {
    inputName: SOURCE_NAME,
    monitorType: "OBS_MONITORING_TYPE_NONE",
  });
  return { sceneName, sceneItemId, window };
}

async function muteIfPresent(obs, sourceName, muted) {
  const names = await inputNames(obs);
  if (!names.has(sourceName)) return false;
  await obs.request("SetInputMute", { inputName: sourceName, inputMuted: muted });
  return true;
}

async function status(obs) {
  const names = await inputNames(obs);
  const sceneName = await currentScene(obs);
  const stream = await obs.request("GetStreamStatus");
  const sourceExists = names.has(SOURCE_NAME);
  let sourceMuted = true;
  let sourceInCurrentScene = false;
  let sourceWindow = "";
  let sourcePriority = null;
  let sourceSettings = null;
  let mainSourceWindow = "";
  let mainSourcePriority = null;
  let mainSourceSettings = null;
  if (sourceExists) {
    sourceMuted = (await obs.request("GetInputMute", { inputName: SOURCE_NAME })).inputMuted;
    sourceInCurrentScene = Boolean(await findSceneItem(obs, sceneName, SOURCE_NAME));
    sourceSettings = (
      await obs.request("GetInputSettings", { inputName: SOURCE_NAME })
    ).inputSettings;
    sourceWindow = sourceSettings.window || "";
    sourcePriority = sourceSettings.priority ?? null;
  }
  if (names.has(MAIN_BOUYOMI_SOURCE_NAME)) {
    mainSourceSettings = (
      await obs.request("GetInputSettings", { inputName: MAIN_BOUYOMI_SOURCE_NAME })
    ).inputSettings;
    mainSourceWindow = mainSourceSettings.window || "";
    mainSourcePriority = mainSourceSettings.priority ?? null;
  }
  return {
    obsConnected: true,
    streamActive: Boolean(stream.outputActive),
    streamReconnecting: Boolean(stream.outputReconnecting),
    sceneName,
    sourceExists,
    sourceMuted,
    sourceInCurrentScene,
    sourceWindow,
    sourcePriority,
    sourceSettings,
    mainSourceWindow,
    mainSourcePriority,
    mainSourceSettings,
    legacyTestSourceExists: names.has(LEGACY_TEST_SOURCE_NAME),
  };
}

async function inventory(obs) {
  const sceneList = await obs.request("GetSceneList");
  const scenes = [];
  for (const scene of sceneList.scenes || []) {
    const sceneName = scene.sceneName;
    const items = await obs.request("GetSceneItemList", { sceneName });
    scenes.push({
      sceneName,
      items: (items.sceneItems || []).map((item) => ({
        sceneItemId: item.sceneItemId,
        sourceName: item.sourceName,
        sourceType: item.sourceType,
        isGroup: item.isGroup,
      })),
    });
  }
  return { currentSceneName: sceneList.currentProgramSceneName, scenes };
}

async function run(command) {
  debug(`run:${command}`);
  const obs = await connectObs();
  try {
    if (command === "status") return await status(obs);
    if (command === "inventory") return await inventory(obs);
    if (command === "ensure-private") {
      await ensureSource(obs);
      await muteIfPresent(obs, SOURCE_NAME, true);
      await muteIfPresent(obs, LEGACY_TEST_SOURCE_NAME, true);
      return await status(obs);
    }
    if (command === "recreate-private") {
      await muteIfPresent(obs, SOURCE_NAME, true);
      const names = await inputNames(obs);
      if (names.has(SOURCE_NAME)) {
        await obs.request("RemoveInput", { inputName: SOURCE_NAME });
        await sleep(3000);
      }
      await ensureSource(obs);
      await muteIfPresent(obs, SOURCE_NAME, true);
      return await status(obs);
    }
    if (command === "stream-on") {
      await ensureSource(obs);
      await muteIfPresent(obs, LEGACY_TEST_SOURCE_NAME, true);
      await muteIfPresent(obs, SOURCE_NAME, false);
      return await status(obs);
    }
    if (command === "stream-off") {
      await muteIfPresent(obs, SOURCE_NAME, true);
      await muteIfPresent(obs, LEGACY_TEST_SOURCE_NAME, true);
      return await status(obs);
    }
    if (command === "repair-bindings") {
      await ensureSource(obs);
      await muteIfPresent(obs, SOURCE_NAME, true);
      await forceProcessRebind(obs, MAIN_BOUYOMI_SOURCE_NAME, "BouyomiChan.exe");
      await forceProcessRebind(obs, SOURCE_NAME, "BouyomiChanComments.exe");
      return await status(obs);
    }
    if (command === "remove-test-source") {
      await muteIfPresent(obs, LEGACY_TEST_SOURCE_NAME, true);
      const names = await inputNames(obs);
      if (names.has(LEGACY_TEST_SOURCE_NAME)) {
        await obs.request("RemoveInput", { inputName: LEGACY_TEST_SOURCE_NAME });
      }
      return await status(obs);
    }
    throw new Error(`Unknown command: ${command}`);
  } finally {
    obs.close();
  }
}

const command = process.argv[2] || "status";
run(command)
  .then((result) => process.stdout.write(`${JSON.stringify(result)}\n`))
  .catch((error) => {
    process.stderr.write(`${error.message || error}\n`);
    process.exitCode = 1;
  });

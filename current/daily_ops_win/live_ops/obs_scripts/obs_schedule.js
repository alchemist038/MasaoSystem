const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const { execFileSync } = require("node:child_process");

const PROFILES = {
  morning: "朝配信",
  day: "昼配信",
  nightLow: "夜配信_日月火水木_3000_720",
  nightHigh: "夜配信_金土_6000_1080",
};

const SCENES = {
  opening: "オープニング",
  main: "見守り 2",
  ending: "エンディング",
};

const ENDING_MUSIC_SOURCE = "エンディング音楽";
const ENDING_MUSIC_VOLUME = numberFromEnv("ENDING_MUSIC_VOLUME", 0.09114433079957962);
const ENDING_MUSIC_FADE_DURATION_MS = numberFromEnv("ENDING_MUSIC_FADE_DURATION_MS", 10000);
const ENDING_MUSIC_FADE_STEPS = Math.max(1, Math.round(numberFromEnv("ENDING_MUSIC_FADE_STEPS", 20)));

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function numberFromEnv(name, fallback) {
  const raw = process.env[name];
  if (!raw) return fallback;
  const value = Number(raw);
  return Number.isFinite(value) && value >= 0 ? value : fallback;
}

function log(message) {
  const stamp = new Date().toLocaleString("ja-JP", { hour12: false });
  console.log(`[${stamp}] ${message}`);
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

async function setProfile(profileName) {
  log(`プロファイル切替: ${profileName}`);
  await withObs((obs) => obs.request("SetCurrentProfile", { profileName }));
  await sleep(5000);
}

async function setScene(sceneName) {
  log(`シーン切替: ${sceneName}`);
  await withObs((obs) => obs.request("SetCurrentProgramScene", { sceneName }));
}

async function restoreEndingMusicVolumeWithObs(obs) {
  try {
    await obs.request("SetInputVolume", {
      inputName: ENDING_MUSIC_SOURCE,
      inputVolumeMul: ENDING_MUSIC_VOLUME,
    });
    log(`エンディング音楽 音量復元: ${ENDING_MUSIC_VOLUME.toFixed(4)}`);
  } catch (error) {
    log(`エンディング音楽 音量復元をスキップ: ${error.message}`);
  }
}

async function restoreEndingMusicVolume() {
  try {
    await withObs((obs) => restoreEndingMusicVolumeWithObs(obs));
  } catch (error) {
    log(`エンディング音楽 音量復元に失敗: ${error.message}`);
  }
}

async function setEndingScene() {
  await withObs(async (obs) => {
    await restoreEndingMusicVolumeWithObs(obs);
    log(`シーン切替: ${SCENES.ending}`);
    await obs.request("SetCurrentProgramScene", { sceneName: SCENES.ending });
  });
}

async function fadeOutEndingMusic() {
  try {
    await withObs(async (obs) => {
      let startVolume = ENDING_MUSIC_VOLUME;
      try {
        const current = await obs.request("GetInputVolume", { inputName: ENDING_MUSIC_SOURCE });
        if (Number.isFinite(current.inputVolumeMul)) startVolume = current.inputVolumeMul;
      } catch (error) {
        log(`エンディング音楽 現在音量取得をスキップ: ${error.message}`);
      }

      if (startVolume <= 0) {
        log("エンディング音楽 フェードアウトはスキップ: すでに無音");
        return;
      }

      log(`エンディング音楽 フェードアウト開始: ${(ENDING_MUSIC_FADE_DURATION_MS / 1000).toFixed(1)}秒`);
      const stepDelayMs = ENDING_MUSIC_FADE_DURATION_MS / ENDING_MUSIC_FADE_STEPS;
      for (let step = 1; step <= ENDING_MUSIC_FADE_STEPS; step += 1) {
        const ratio = step / ENDING_MUSIC_FADE_STEPS;
        const nextVolume = Math.max(0, startVolume * (1 - ratio));
        await obs.request("SetInputVolume", {
          inputName: ENDING_MUSIC_SOURCE,
          inputVolumeMul: nextVolume,
        });
        if (step < ENDING_MUSIC_FADE_STEPS) await sleep(stepDelayMs);
      }
      log("エンディング音楽 フェードアウト完了");
    });
  } catch (error) {
    log(`エンディング音楽 フェードアウトに失敗: ${error.message}`);
  }
}

async function startStream(date = new Date()) {
  await withObs(async (obs) => {
    const status = await obs.request("GetStreamStatus");
    if (status.outputActive) {
      log("配信開始はスキップ: すでに配信中");
      return;
    }
    await ensureStreamServiceKey(obs, date);
    log("配信開始");
    await obs.request("StartStream");
  });
}

async function stopPartStream(part, date) {
  await stopStream();
  await restoreEndingMusicVolume();
  completeYoutube(part, date);
}

async function isStreaming() {
  return withObs(async (obs) => {
    const status = await obs.request("GetStreamStatus");
    return !!status.outputActive;
  });
}

async function stopStream() {
  await withObs(async (obs) => {
    const status = await obs.request("GetStreamStatus");
    if (!status.outputActive) {
      log("配信停止はスキップ: 配信中ではありません");
      return;
    }
    log("配信停止");
    await obs.request("StopStream");
  });
}

async function ensureNotStreaming() {
  await withObs(async (obs) => {
    const status = await obs.request("GetStreamStatus");
    if (status.outputActive) {
      throw new Error("OBSは配信中です。配信中のプロファイル切替は行いません。");
    }
  });
}

async function prepareMorning() {
  await ensureNotStreaming();
  await setProfile(PROFILES.morning);
  await setScene(SCENES.opening);
  log("朝配信プロファイルとオープニングシーンを準備しました。朝枠の開始は手動で行ってください。");
}

async function watchMorningStart(date) {
  const deadline = timeOn(date, 11, 58, 45);
  log(`朝枠の手動開始を監視します。開始検知から15秒後に${SCENES.main}へ切り替えます。`);
  while (new Date() < deadline) {
    if (await isStreaming()) {
      log(`朝枠の配信開始を検知しました。15秒後に${SCENES.main}へ切り替えます。`);
      await sleep(15000);
      if (await isStreaming()) {
        await setScene(SCENES.main);
        log(`朝枠 ${SCENES.main}へ切り替えました。`);
      } else {
        log(`${SCENES.main}切替はスキップ: 15秒待機中に配信が停止しました。`);
      }
      return;
    }
    await sleep(2000);
  }
  log("朝枠の開始監視を終了しました。");
}

async function autoStartMorning(date, clock) {
  const startAt = timeOn(date, clock.hour, clock.minute, clock.second);
  const deadline = timeOn(date, 11, 58, 45);
  if (startAt >= deadline) {
    throw new Error(`朝枠自動開始時刻が遅すぎます: ${clock.label}`);
  }

  const now = new Date();
  if (startAt > now) {
    log(`朝枠自動開始 待機: ${formatTime(startAt)}`);
    await sleep(startAt.getTime() - now.getTime());
  } else if (new Date() < deadline) {
    log(`朝枠自動開始時刻を過ぎています。すぐ開始します: ${formatTime(startAt)}`);
  } else {
    log(`朝枠自動開始はスキップ: 終了準備時刻を過ぎています (${formatTime(startAt)})`);
    return;
  }

  if (await isStreaming()) {
    log("朝枠自動開始はスキップ: すでに配信中");
  } else {
    await ensureNotStreaming();
    await setProfile(PROFILES.morning);
    await setScene(SCENES.opening);
    await startStream(date);
  }

  log(`朝枠 ${SCENES.main} 切替待機: 15秒`);
  await sleep(15000);
  if (await isStreaming()) {
    await setScene(SCENES.main);
    log(`朝枠 ${SCENES.main}へ切り替えました。`);
  } else {
    log(`${SCENES.main}切替はスキップ: 配信中ではありません。`);
  }
}

function nightProfileFor(date) {
  const day = date.getDay();
  return day === 5 || day === 6 ? PROFILES.nightHigh : PROFILES.nightLow;
}

function timeOn(date, hour, minute, second = 0) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate(), hour, minute, second, 0);
}

function dateKey(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function youtubeManifestFor(date) {
  return path.join("C:\\Users\\alche\\Desktop\\OBS\\youtube", `broadcasts_${dateKey(date)}.json`);
}

function completeYoutube(part, date = new Date()) {
  const script = path.join(__dirname, "youtube_live_broadcasts.py");
  const manifest = youtubeManifestFor(date);
  if (!fs.existsSync(script)) {
    log(`YouTube completeはスキップ: スクリプトがありません (${script})`);
    return;
  }
  if (!fs.existsSync(manifest)) {
    log(`YouTube completeはスキップ: manifestがありません (${manifest})`);
    return;
  }
  log(`YouTube枠終了: ${part}`);
  try {
    execFileSync("python", [script, "complete", "--date", dateKey(date), "--part", part], {
      stdio: "inherit",
      windowsHide: true,
    });
  } catch (error) {
    log(`YouTube枠終了に失敗しましたが、OBSスケジュールは継続します: ${error.message}`);
  }
}

function readYoutubeStreamKey(date = new Date()) {
  const script = path.join(__dirname, "youtube_live_broadcasts.py");
  const manifest = youtubeManifestFor(date);
  if (!fs.existsSync(script)) {
    throw new Error(`YouTube stream key取得スクリプトがありません (${script})`);
  }
  if (!fs.existsSync(manifest)) {
    throw new Error(`YouTube manifestがありません (${manifest})`);
  }
  const streamKey = execFileSync("python", [script, "stream-key", "--date", dateKey(date)], {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
    windowsHide: true,
  }).trim();
  if (!streamKey) throw new Error("YouTube Live APIからストリームキーを取得できませんでした。");
  return streamKey;
}

async function ensureStreamServiceKey(obs, date = new Date()) {
  const service = await obs.request("GetStreamServiceSettings");
  const settings = service.streamServiceSettings || {};
  const currentKey = String(settings.key || "").trim();
  if (currentKey) {
    log("配信サービス設定確認: ストリームキーあり");
    return;
  }

  log("配信サービス設定確認: ストリームキーが空のためYouTube Live APIから取得して設定します。");
  const streamKey = readYoutubeStreamKey(date);
  await obs.request("SetStreamServiceSettings", {
    streamServiceType: service.streamServiceType || "rtmp_common",
    streamServiceSettings: { ...settings, key: streamKey },
  });
  log("配信サービス設定更新: ストリームキーを設定しました。");
}

function filterSchedule(events, mode) {
  if (mode === "full") return events;
  if (mode === "part1-to-part2-start") {
    const stopKey = "part2-main";
    const stopIndex = events.findIndex((event) => event.key === stopKey);
    if (stopIndex < 0) throw new Error(`schedule stop key not found: ${stopKey}`);
    return events.slice(0, stopIndex + 1);
  }
  if (mode === "part2-live-to-part3-start") {
    const startKey = "part2-ending";
    const startIndex = events.findIndex((event) => event.key === startKey);
    if (startIndex < 0) throw new Error(`schedule start key not found: ${startKey}`);
    return events.slice(startIndex);
  }
  throw new Error(`Unknown schedule mode: ${mode}`);
}

function scheduleFor(date, mode = "full") {
  const nightProfile = nightProfileFor(date);
  const events = [
    { key: "part1-ending", at: timeOn(date, 11, 58, 45), label: "第1部 エンディング", run: () => setEndingScene() },
    { key: "part1-ending-fade", at: timeOn(date, 11, 59, 20), label: "第1部 エンディング音楽フェードアウト", run: () => fadeOutEndingMusic() },
    { key: "part1-stop", at: timeOn(date, 11, 59, 35), label: "第1部 終了", run: () => stopPartStream("part1", date) },
    { key: "day-profile", at: timeOn(date, 11, 59, 45), label: "昼配信プロファイルへ", run: () => setProfile(PROFILES.day) },
    { key: "part2-start", at: timeOn(date, 11, 59, 55), label: "第2部 開始/オープニング", run: async () => { await setScene(SCENES.opening); await startStream(date); } },
    { key: "part2-main", at: timeOn(date, 12, 0, 10), label: `第2部 ${SCENES.main}`, run: () => setScene(SCENES.main) },
    { key: "part2-ending", at: timeOn(date, 16, 58, 45), label: "第2部 エンディング", run: () => setEndingScene() },
    { key: "part2-ending-fade", at: timeOn(date, 16, 59, 20), label: "第2部 エンディング音楽フェードアウト", run: () => fadeOutEndingMusic() },
    { key: "part2-stop", at: timeOn(date, 16, 59, 35), label: "第2部 終了", run: () => stopPartStream("part2", date) },
    { key: "night-profile", at: timeOn(date, 16, 59, 45), label: `夜配信プロファイルへ (${nightProfile})`, run: () => setProfile(nightProfile) },
    { key: "part3-start", at: timeOn(date, 16, 59, 55), label: "第3部 開始/オープニング", run: async () => { await setScene(SCENES.opening); await startStream(date); } },
    { key: "part3-main", at: timeOn(date, 17, 0, 10), label: `第3部 ${SCENES.main}`, run: () => setScene(SCENES.main) },
  ];
  return filterSchedule(events, mode);
}

function formatTime(date) {
  return date.toLocaleString("ja-JP", { hour12: false });
}

function parseArgs() {
  const rawArgs = process.argv.slice(2);
  const args = new Set(rawArgs);
  const dateArg = rawArgs.find((arg) => arg.startsWith("--date="));
  const modeArg = rawArgs.find((arg) => arg.startsWith("--mode="));
  const mainSceneArg = rawArgs.find((arg) => arg.startsWith("--main-scene="));
  const morningStartArg = rawArgs.find((arg) => arg.startsWith("--morning-start="));
  return {
    dryRun: args.has("--dry-run"),
    prepareMorning: args.has("--prepare-morning"),
    date: dateArg ? dateArg.slice("--date=".length) : null,
    mode: modeArg ? modeArg.slice("--mode=".length) : "full",
    mainScene: mainSceneArg ? mainSceneArg.slice("--main-scene=".length) : process.env.MASAO_OBS_MAIN_SCENE || null,
    morningStart: morningStartArg ? morningStartArg.slice("--morning-start=".length) : null,
  };
}

function dateFromArg(value) {
  if (!value) return new Date();
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) throw new Error("--date must be YYYY-MM-DD.");
  return new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]), 0, 0, 0, 0);
}

function clockFromArg(value) {
  if (!value) return null;
  const match = /^(\d{1,2}):(\d{2})(?::(\d{2}))?$/.exec(value);
  if (!match) throw new Error("--morning-start must be HH:MM or HH:MM:SS.");
  const hour = Number(match[1]);
  const minute = Number(match[2]);
  const second = match[3] ? Number(match[3]) : 0;
  if (hour < 0 || hour > 23 || minute < 0 || minute > 59 || second < 0 || second > 59) {
    throw new Error("--morning-start is out of range.");
  }
  return {
    hour,
    minute,
    second,
    label: `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}:${String(second).padStart(2, "0")}`,
  };
}

async function runSchedule(today, mode, morningStartClock = null) {
  const events = scheduleFor(today, mode);
  if (mode === "full") log(`夜プロファイル選択: ${nightProfileFor(today)}`);
  log(`メインシーン: ${SCENES.main}`);
  log(`スケジュールモード: ${mode}`);
  if (mode === "full" || mode === "part1-to-part2-start") {
    if (morningStartClock) {
      log(`スケジュール待機を開始します。朝枠は ${morningStartClock.label} に自動開始します。`);
      autoStartMorning(today, morningStartClock).catch((error) => {
        log(`朝枠自動開始でエラー: ${error.message}`);
      });
    } else {
      log("スケジュール待機を開始します。朝枠の開始は手動です。");
      watchMorningStart(today).catch((error) => {
        log(`朝枠開始監視でエラー: ${error.message}`);
      });
    }
  } else {
    log(`朝枠開始監視はスキップします: ${mode}`);
  }

  for (const event of events) {
    const now = new Date();
    if (event.at <= now) {
      log(`スキップ: ${event.label} (${formatTime(event.at)})`);
      continue;
    }
    log(`待機: ${event.label} (${formatTime(event.at)})`);
    await sleep(event.at.getTime() - now.getTime());
    try {
      await event.run();
      log(`完了: ${event.label}`);
    } catch (error) {
      log(`失敗: ${event.label} - ${error.message}`);
      throw error;
    }
  }
  if (mode === "full") {
    log("本日の自動スケジュールは完了しました。第3部の終了は手動です。");
  } else {
    log(`本日の自動スケジュールはここで停止します: ${mode}`);
  }
}

async function main() {
  const args = parseArgs();
  if (args.mainScene) SCENES.main = args.mainScene;
  const today = dateFromArg(args.date);
  const morningStartClock = clockFromArg(args.morningStart);
  const events = scheduleFor(today, args.mode);

  if (args.dryRun) {
    if (args.mode === "full") console.log(`夜プロファイル: ${nightProfileFor(today)}`);
    console.log(`メインシーン: ${SCENES.main}`);
    console.log(`スケジュールモード: ${args.mode}`);
    if (morningStartClock) {
      console.log(`${formatTime(timeOn(today, morningStartClock.hour, morningStartClock.minute, morningStartClock.second))}  第1部 自動開始/オープニング`);
      console.log(`${formatTime(timeOn(today, morningStartClock.hour, morningStartClock.minute, morningStartClock.second + 15))}  第1部 ${SCENES.main}`);
    }
    for (const event of events) console.log(`${formatTime(event.at)}  ${event.label}`);
    return;
  }

  if (args.prepareMorning) {
    await prepareMorning();
    return;
  }

  await runSchedule(today, args.mode, morningStartClock);
}

main().catch((error) => {
  log(`ERROR: ${error.stack || error.message}`);
  process.exit(1);
});

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfoNotFoundError


API_BASE = "https://api.switch-bot.com/v1.1"
OVERLAY_DIR = Path(__file__).resolve().parent
LOG_DIR = OVERLAY_DIR.parents[1] / "logs"
DATA_JSON = OVERLAY_DIR / "sensor-data.json"
DATA_JS = OVERLAY_DIR / "sensor-data.js"
SENSOR_TYPES = {
    "Meter",
    "MeterPlus",
    "Meter Pro",
    "MeterPro",
    "Meter Pro CO2",
    "MeterProCO2",
    "Outdoor Meter",
    "WoIOSensor",
    "Weather Station",
    "Hub 2",
    "Hub 3",
}

try:
    JST = ZoneInfo("Asia/Tokyo")
except ZoneInfoNotFoundError:
    JST = timezone(timedelta(hours=9), "JST")


def now_jst() -> datetime:
    return datetime.now(JST)


def log_line(level: str, message: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = f"[{now_jst().isoformat(timespec='seconds')}] [{level}] {message}"
    with (LOG_DIR / f"masao_room_sensor_hub_{now_jst():%Y-%m-%d}.log").open("a", encoding="utf-8") as file:
        file.write(line + "\n")
    print(line, flush=True)


def get_secret(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is not set")
    return value


def auth_headers() -> dict[str, str]:
    token = get_secret("SWITCHBOT_TOKEN")
    secret = get_secret("SWITCHBOT_SECRET")
    timestamp = str(int(time.time() * 1000))
    nonce = str(uuid.uuid4())
    message = (token + timestamp + nonce).encode("utf-8")
    signature = base64.b64encode(hmac.new(secret.encode("utf-8"), message, hashlib.sha256).digest()).decode("utf-8")
    return {
        "Authorization": token,
        "sign": signature,
        "nonce": nonce,
        "t": timestamp,
        "Content-Type": "application/json; charset=utf8",
    }


def api_get(path: str) -> dict:
    request = urllib.request.Request(API_BASE + path, headers=auth_headers(), method="GET")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"SwitchBot API HTTP {error.code}: {body}") from error


def require_success(result: dict, action: str) -> dict:
    if result.get("statusCode") != 100:
        raise RuntimeError(f"{action} failed statusCode={result.get('statusCode')} message={result.get('message')}")
    return result.get("body") or {}


def normalize_text(value: object) -> str:
    return str(value or "").casefold()


def device_matches(device: dict, args: argparse.Namespace) -> bool:
    device_id = str(device.get("deviceId") or "")
    device_name = str(device.get("deviceName") or "")
    device_type = str(device.get("deviceType") or "")
    if args.device_id and normalize_text(args.device_id) != normalize_text(device_id):
        return False
    if args.device_name and normalize_text(args.device_name) not in normalize_text(device_name):
        return False
    if args.device_type and normalize_text(args.device_type) != normalize_text(device_type):
        return False
    if args.device_id or args.device_name or args.device_type:
        return True
    return device_type in SENSOR_TYPES or "meter" in normalize_text(device_type) or "温" in device_name or "湿" in device_name


def device_sort_key(device: dict) -> tuple[int, str]:
    device_type = str(device.get("deviceType") or "")
    preferred = {
        "MeterPro": 0,
        "Meter Pro": 0,
        "Meter": 1,
        "MeterPlus": 1,
        "Outdoor Meter": 1,
        "Weather Station": 2,
        "Hub 3": 3,
        "Hub 2": 3,
    }
    return (preferred.get(device_type, 9), str(device.get("deviceName") or ""))


def get_device_list() -> list[dict]:
    body = require_success(api_get("/devices"), "get devices")
    return list(body.get("deviceList") or [])


def get_status(device_id: str) -> dict:
    return require_success(api_get(f"/devices/{device_id}/status"), "get device status")


def read_sensor_payload(args: argparse.Namespace) -> dict:
    devices = sorted((device for device in get_device_list() if device_matches(device, args)), key=device_sort_key)
    if not devices:
        raise RuntimeError("no SwitchBot temperature/humidity device matched")

    errors: list[str] = []
    for device in devices:
        device_id = str(device.get("deviceId") or "")
        if not device_id:
            continue
        try:
            status = get_status(device_id)
        except Exception as error:  # noqa: BLE-free cloud polling should try the next candidate.
            errors.append(f"{device.get('deviceName')}: {error}")
            continue

        temperature = status.get("temperature")
        humidity = status.get("humidity")
        if temperature is None or humidity is None:
            errors.append(f"{device.get('deviceName')}: no temperature/humidity in status")
            continue

        return {
            "temperatureC": float(temperature),
            "humidity": int(round(float(humidity))),
            "battery": status.get("battery"),
            "modelFriendlyName": device.get("deviceName") or status.get("deviceType") or device.get("deviceType"),
            "updatedAt": now_jst().isoformat(timespec="seconds"),
            "source": "switchbot_cloud",
        }

    raise RuntimeError("; ".join(errors) or "no readable SwitchBot temperature/humidity status")


def atomic_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def write_payload(payload: dict) -> None:
    public_payload = {
        "temperatureC": payload.get("temperatureC"),
        "humidity": payload.get("humidity"),
        "battery": payload.get("battery"),
        "rssi": None,
        "modelFriendlyName": payload.get("modelFriendlyName"),
        "updatedAt": payload.get("updatedAt"),
        "source": payload.get("source", "switchbot_cloud"),
    }
    json_text = json.dumps(public_payload, ensure_ascii=False, indent=2)
    atomic_write(DATA_JSON, json_text + "\n")
    atomic_write(DATA_JS, "window.MASAO_ROOM_SENSOR_DATA = " + json_text + ";\n")


def update_once(args: argparse.Namespace) -> None:
    payload = read_sensor_payload(args)
    write_payload(payload)
    log_line(
        "OK",
        "temperatureC={temperatureC:.1f} humidity={humidity} battery={battery} source={source}".format(**payload),
    )


def run_periodic(args: argparse.Namespace) -> int:
    log_line("INFO", f"hub periodic started period={args.period}s")
    while True:
        started = time.monotonic()
        try:
            update_once(args)
        except Exception as error:  # noqa: periodic updater should keep trying.
            log_line("WARN", str(error))
        elapsed = time.monotonic() - started
        time.sleep(max(0.0, args.period - elapsed))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update OBS room sensor overlay from SwitchBot Cloud API.")
    parser.add_argument("--periodic", action="store_true", help="Keep updating forever.")
    parser.add_argument("--period", type=float, default=60.0, help="Seconds between cloud reads.")
    parser.add_argument("--device-id", help="Optional exact SwitchBot device id.")
    parser.add_argument("--device-name", help="Optional substring match for SwitchBot device name.")
    parser.add_argument("--device-type", help="Optional exact SwitchBot device type.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.periodic:
            return run_periodic(args)
        update_once(args)
        return 0
    except KeyboardInterrupt:
        return 130
    except Exception as error:
        log_line("ERROR", str(error))
        return 1


if __name__ == "__main__":
    sys.exit(main())

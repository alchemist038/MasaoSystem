from __future__ import annotations

import argparse
import json
import os
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/youtube"]
PART_ORDER = ("part1", "part2", "part3")


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def select_display_item(
    manifest: dict[str, Any], items: list[dict[str, Any]]
) -> dict[str, Any]:
    entries = manifest.get("broadcasts", {})
    by_id = {item.get("id"): item for item in items}
    candidates: list[tuple[str, dict[str, Any], dict[str, Any]]] = []

    for part in PART_ORDER:
        entry = entries.get(part) or {}
        item = by_id.get(entry.get("id"))
        if item:
            candidates.append((part, entry, item))

    active = [
        candidate
        for candidate in candidates
        if candidate[2].get("liveStreamingDetails", {}).get("actualStartTime")
        and not candidate[2].get("liveStreamingDetails", {}).get("actualEndTime")
    ]
    if active:
        selected = max(
            active,
            key=lambda candidate: candidate[2]
            .get("liveStreamingDetails", {})
            .get("actualStartTime", ""),
        )
        status = "live"
    else:
        upcoming = [
            candidate
            for candidate in candidates
            if not candidate[2].get("liveStreamingDetails", {}).get("actualEndTime")
        ]
        selected = upcoming[0] if upcoming else (candidates[-1] if candidates else None)
        status = "waiting" if upcoming else "ended"

    if selected is None:
        raise RuntimeError("No broadcast in the manifest was returned by YouTube.")

    part, entry, item = selected
    details = item.get("liveStreamingDetails", {})
    statistics = item.get("statistics", {})
    return {
        "status": status,
        "part": part,
        "videoId": item.get("id"),
        "title": item.get("snippet", {}).get("title") or entry.get("title", ""),
        "watchUrl": entry.get("watchUrl", ""),
        "concurrentViewers": details.get("concurrentViewers"),
        "viewCount": statistics.get("viewCount"),
        "actualStartTime": details.get("actualStartTime"),
    }


class MetricsState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._value: dict[str, Any] = {
            "status": "starting",
            "part": None,
            "concurrentViewers": None,
            "viewCount": None,
            "updatedAt": None,
            "error": None,
        }

    def get(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._value)

    def update(self, value: dict[str, Any]) -> None:
        with self._lock:
            self._value = value


def youtube_service(token_path: Path):
    credentials = Credentials.from_authorized_user_file(str(token_path), scopes=SCOPES)
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        token_path.write_text(credentials.to_json(), encoding="utf-8")
    return build("youtube", "v3", credentials=credentials, cache_discovery=False)


def fetch_metrics(service, manifest_path: Path) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    entries = manifest.get("broadcasts", {})
    video_ids = [
        str((entries.get(part) or {}).get("id") or "")
        for part in PART_ORDER
    ]
    video_ids = [video_id for video_id in video_ids if video_id]
    if not video_ids:
        raise RuntimeError("The manifest does not contain broadcast IDs.")

    response = (
        service.videos()
        .list(
            part="snippet,statistics,liveStreamingDetails",
            id=",".join(video_ids),
            maxResults=len(video_ids),
        )
        .execute()
    )
    result = select_display_item(manifest, response.get("items", []))
    result["updatedAt"] = datetime.now().astimezone().isoformat(timespec="seconds")
    result["error"] = None
    return result


def poll_loop(
    state: MetricsState,
    service,
    manifest_path: Path,
    poll_seconds: int,
    stop_event: threading.Event,
) -> None:
    while not stop_event.is_set():
        try:
            state.update(fetch_metrics(service, manifest_path))
        except Exception as exc:
            current = state.get()
            current["error"] = f"{type(exc).__name__}: {exc}"
            current["updatedAt"] = datetime.now().astimezone().isoformat(
                timespec="seconds"
            )
            state.update(current)
        stop_event.wait(poll_seconds)


def make_handler(state: MetricsState, index_html: str):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path.startswith("/api/stats") or self.path == "/health":
                body = json.dumps(state.get(), ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            if self.path in ("/", "/index.html"):
                body = index_html.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            self.send_error(404)

        def log_message(self, _format: str, *_args: Any) -> None:
            return

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description="Local OBS dock for YouTube Live metrics.")
    parser.add_argument("--date", default=datetime.now().astimezone().date().isoformat())
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8791)
    parser.add_argument("--poll-seconds", type=int, default=60)
    parser.add_argument("--manifest-dir", type=Path, default=None)
    args = parser.parse_args()

    token_value = os.environ.get("MASAO_YOUTUBE_LIVE_TOKEN_FILE", "").strip()
    if not token_value:
        raise SystemExit("MASAO_YOUTUBE_LIVE_TOKEN_FILE is required.")
    token_path = Path(token_value)
    if not token_path.exists():
        raise SystemExit(f"YouTube token file was not found: {token_path}")

    manifest_dir = args.manifest_dir or (
        Path.home() / "Desktop" / "OBS" / "youtube"
    )
    manifest_path = manifest_dir / f"broadcasts_{args.date}.json"
    if not manifest_path.exists():
        raise SystemExit(f"YouTube manifest was not found: {manifest_path}")

    index_path = Path(__file__).with_name("index.html")
    index_html = index_path.read_text(encoding="utf-8")
    state = MetricsState()
    service = youtube_service(token_path)
    state.update(fetch_metrics(service, manifest_path))

    stop_event = threading.Event()
    poller = threading.Thread(
        target=poll_loop,
        args=(state, service, manifest_path, max(30, args.poll_seconds), stop_event),
        daemon=True,
    )
    poller.start()

    server = ThreadingHTTPServer((args.host, args.port), make_handler(state, index_html))
    print(
        f"live metrics: http://{args.host}:{args.port}/ "
        f"date={args.date} poll={max(30, args.poll_seconds)}s",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        server.server_close()


if __name__ == "__main__":
    main()

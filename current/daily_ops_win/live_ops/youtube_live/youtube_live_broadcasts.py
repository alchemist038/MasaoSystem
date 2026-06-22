from __future__ import annotations

import argparse
import json
import os
import sys
import time as time_module
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


REPO_ROOT = Path(__file__).resolve().parents[4]
TOKEN_FILE_ENV = "MASAO_YOUTUBE_LIVE_TOKEN_FILE"
TOKEN_FILES_ENV = "MASAO_YOUTUBE_LIVE_TOKEN_FILES"
DEFAULT_TOKEN_FILES = [
    REPO_ROOT / "shared" / "keys" / "youtube" / "token_live_ops.json",
    REPO_ROOT / "shared" / "keys" / "youtube" / "token.json",
]
SCOPES = ["https://www.googleapis.com/auth/youtube"]
JST = timezone(timedelta(hours=9), "JST")

OBS_DIR = Path(os.environ.get("MASAO_OBS_DIR", r"C:\Users\alche\Desktop\OBS"))
THUMB_DIR = OBS_DIR / "サムネ"
DEFAULT_MANIFEST_DIR = OBS_DIR / "youtube"


def watch_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def chat_url(video_id: str) -> str:
    return f"https://www.youtube.com/live_chat?is_popout=1&v={video_id}"


@dataclass(frozen=True)
class Part:
    key: str
    title: str
    description_intro: str
    start: time
    end: time
    thumbnail: Path


COMMON_DESCRIPTION = """\

ライブ中のかわいい場面は、視聴者さんのコメントやタイムスタンプを参考に、Shortsや特集動画として紹介することがあります。
気になる瞬間があれば、時間と一緒にコメントしてもらえるとうれしいです。

■ GPT太郎への呼びかけ方
文の最初に「GPT太郎君」と入れて話しかけてください。

例:
GPT太郎君 げんき？

返事は短め・気まぐれです。
状況によっては返事をしないこともあります。
長文の呼びかけ、連続投稿、催促、強い言葉には反応しません。

■ ライブ配信について
ライブ配信は朝・昼・夜の3部構成です。
第1部 朝-12:00 JST
第2部 12:00-17:00 JST
第3部 17:00-夜ごろ JST

■ まさおについて
まさおは2020年4月生まれのミニレッキスです。
2020年7月に家族になり、2025年5月からYouTubeで毎日の暮らしを配信しています。

■ 配信環境と自動追跡について
このライブ配信では、ケージではない空間で放牧中のまさおを自動追跡カメラで見守っています。
まさおの動きに合わせてカメラが自動で追従するため、追跡の調整中にカメラが少し揺れることがあります。
その間は無理に見ず、音だけ流す・落ち着いてから戻るなど、それぞれのペースで楽しんでもらえたらうれしいです。

裏側では、おとんを中心に、GPT五郎・GPT太郎が配信案内やコメント整理を手伝っています。
最近、新人編集者としてコデ子（CODEX）も入社しました。

noteでは、まさおのこと、見守りライブの裏側、AIや自動化を使った試行錯誤を書いています。
https://note.com/glossy_shrew7501

EN:
Daily live stream of Masao, a Mini Rex rabbit from Japan.
Watch a relaxing rabbit live cam with flops, naps, yawns, dinner time, grooming, and quiet daily moments.
Viewer comments and timestamps may become Shorts or highlight videos.

#うさぎ #ミニレッキス #まさお #うさぎライブ #うさぎライブカメラ #rabbit #MiniRex #bunny
"""


def parse_clock(value: str) -> time:
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError as exc:
        raise SystemExit("時刻は HH:MM で指定してください。") from exc


def parts_for(
    date_label: str,
    part1_start: time,
    part2_end: time,
    part3_start: time,
    part3_end: time,
) -> list[Part]:
    return [
        Part(
            key="part1",
            title=f"うさぎのまさお放牧中｜朝の見守り 第1部｜まさお警備中 / Rabbit Live Cam {date_label}",
            description_intro=(
                "ミニレッキスのうさぎ「まさお」を毎日見守る、うさぎライブカメラです。\n"
                "朝・昼・夜の3部構成で、へやんぽ、ごはんタイム、ゴロン、寝落ち、あくび、なでなで、ブラッシングなど、まさおの自然な毎日を配信しています。\n\n"
                "この枠は第1部です。\n"
                "朝のまさおを、12:00ごろまでまったり見守ります。\n"
                "ごはんタイムは18:30ごろです。\n"
                f"第1部 {part1_start.strftime('%H:%M')}-12:00 JST / Relaxing Mini Rex Rabbit Live Cam from Japan\n"
            ),
            start=part1_start,
            end=time(12, 0),
            thumbnail=THUMB_DIR / "masao_thumb_part1_morning.jpg",
        ),
        Part(
            key="part2",
            title=f"うさぎのまさお放牧中｜昼の見守り 第2部｜まさおお昼寝？ / Rabbit Live Cam {date_label}",
            description_intro=(
                "ミニレッキスのうさぎ「まさお」を毎日見守る、うさぎライブカメラです。\n"
                "朝・昼・夜の3部構成で、へやんぽ、ごはんタイム、ゴロン、寝落ち、あくび、なでなで、ブラッシングなど、まさおの自然な毎日を配信しています。\n\n"
                "この枠は第2部です。\n"
                f"昼のへやんぽや休憩中のまさおを、{part2_end.strftime('%H:%M')}ごろまで見守ります。\n"
                "ごはんタイムは18:30ごろです。\n"
                f"第2部 12:00-{part2_end.strftime('%H:%M')} JST / Relaxing Rabbit Live Cam from Japan\n"
            ),
            start=time(12, 0),
            end=part2_end,
            thumbnail=THUMB_DIR / "masao_thumb_part2_noon.jpg",
        ),
        Part(
            key="part3",
            title=f"うさぎのまさお放牧中｜夜の見守り 第3部｜18:30ごろごはんタイム / Rabbit Live Cam {date_label}",
            description_intro=(
                "ミニレッキスのうさぎ「まさお」を毎日見守る、うさぎライブカメラです。\n"
                "朝・昼・夜の3部構成で、へやんぽ、ごはんタイム、ゴロン、寝落ち、あくび、なでなで、ブラッシングなど、まさおの自然な毎日を配信しています。\n\n"
                "この枠は第3部です。\n"
                "18:30ごろのごはんタイムを中心に、夜のまさおを見守ります。\n"
                f"第3部 {part3_start.strftime('%H:%M')}-{part3_end.strftime('%H:%M')}ごろ JST / Mini Rex Rabbit Live from Japan\n"
            ),
            start=part3_start,
            end=part3_end,
            thumbnail=THUMB_DIR / "masao_thumb_part3_night.jpg",
        ),
    ]


def parse_parts(value: str) -> set[str]:
    allowed = {"part1", "part2", "part3"}
    parts = {part.strip() for part in value.split(",") if part.strip()}
    unknown = sorted(parts - allowed)
    if unknown:
        raise SystemExit(f"--parts に不明な値があります: {', '.join(unknown)}")
    if not parts:
        raise SystemExit("--parts には part1,part2,part3 のいずれかを指定してください。")
    return parts


def parse_date(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=JST)
    except ValueError as exc:
        raise SystemExit("--date は YYYY-MM-DD で指定してください。") from exc


def iso_at(day: datetime, clock: time) -> str:
    value = datetime.combine(day.date(), clock, tzinfo=JST)
    return value.isoformat()


def manifest_path(day: datetime) -> Path:
    return DEFAULT_MANIFEST_DIR / f"broadcasts_{day.strftime('%Y-%m-%d')}.json"


def resolve_token_file() -> Path:
    env_value = os.environ.get(TOKEN_FILE_ENV, "").strip()
    if env_value:
        return Path(env_value)

    candidates: list[Path] = []
    for raw in os.environ.get(TOKEN_FILES_ENV, "").split(os.pathsep):
        raw = raw.strip()
        if raw:
            candidates.append(Path(raw))
    candidates.extend(DEFAULT_TOKEN_FILES)

    for candidate in candidates:
        if candidate.exists():
            return candidate

    searched = ", ".join(str(candidate) for candidate in candidates)
    raise SystemExit(
        f"OAuth token file was not found. Set {TOKEN_FILE_ENV}, "
        f"or place a local ignored token under shared/keys/youtube/. Searched: {searched}"
    )


def credentials() -> Credentials:
    token_file = resolve_token_file()
    creds = Credentials.from_authorized_user_file(str(token_file), scopes=SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_file.write_text(creds.to_json(), encoding="utf-8")
    return creds


def youtube():
    return build("youtube", "v3", credentials=credentials())


def list_streams(service) -> list[dict[str, Any]]:
    response = service.liveStreams().list(
        part="id,snippet,status,cdn",
        mine=True,
        maxResults=50,
    ).execute()
    return response.get("items", [])


def choose_stream_id(service, requested: str | None) -> str:
    if requested:
        return requested
    streams = list_streams(service)
    if len(streams) != 1:
        raise SystemExit(f"liveStream が {len(streams)} 件あります。--stream-id を指定してください。")
    return streams[0]["id"]


def stream_id_from_manifest(day: datetime) -> str:
    file = manifest_path(day)
    if not file.exists():
        raise SystemExit(f"manifest が見つかりません: {file}")
    manifest = json.loads(file.read_text(encoding="utf-8"))
    stream_id = str(manifest.get("stream_id") or "").strip()
    if not stream_id:
        raise SystemExit(f"manifest に stream_id がありません: {file}")
    return stream_id


def get_stream_key(service, stream_id: str) -> str:
    response = service.liveStreams().list(
        part="id,cdn",
        id=stream_id,
        maxResults=1,
    ).execute()
    items = response.get("items", [])
    if not items:
        raise SystemExit(f"liveStream が見つかりません: {stream_id}")
    ingestion = (items[0].get("cdn") or {}).get("ingestionInfo") or {}
    stream_key = str(ingestion.get("streamName") or "").strip()
    if not stream_key:
        raise SystemExit(f"liveStream の streamName が取得できません: {stream_id}")
    return stream_key


def broadcast_body(part: Part, day: datetime, privacy: str) -> dict[str, Any]:
    return {
        "snippet": {
            "title": part.title,
            "description": part.description_intro + COMMON_DESCRIPTION,
            "scheduledStartTime": iso_at(day, part.start),
            "scheduledEndTime": iso_at(day, part.end),
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
        "contentDetails": {
            "enableAutoStart": True,
            "enableAutoStop": False,
            "enableDvr": True,
            "recordFromStart": True,
            "latencyPreference": "normal",
            "monitorStream": {
                "enableMonitorStream": False,
            },
        },
    }


def set_thumbnail_with_retry(service, broadcast_id: str, thumbnail: Path, retries: int = 6, delay_sec: float = 5.0) -> bool:
    for attempt in range(1, retries + 1):
        try:
            media = MediaFileUpload(str(thumbnail), mimetype="image/jpeg", resumable=False)
            service.thumbnails().set(videoId=broadcast_id, media_body=media).execute()
            return True
        except Exception as exc:
            if attempt >= retries:
                print(f"  thumbnail warning: サムネ設定をスキップしました: {exc}", file=sys.stderr)
                return False
            print(f"  thumbnail retry {attempt}/{retries}: {delay_sec:.0f}s待機します", file=sys.stderr)
            time_module.sleep(delay_sec)
    return False


def create_broadcasts(args: argparse.Namespace) -> None:
    day = parse_date(args.date)
    date_label = day.strftime("%Y.%m.%d")
    part1_start = parse_clock(args.part1_start)
    part2_end = parse_clock(args.part2_end)
    part3_start = parse_clock(args.part3_start)
    part3_end = parse_clock(args.part3_end)
    selected_parts = parse_parts(args.parts)
    parts = [
        part
        for part in parts_for(date_label, part1_start, part2_end, part3_start, part3_end)
        if part.key in selected_parts
    ]
    out = manifest_path(day)
    out.parent.mkdir(parents=True, exist_ok=True)
    existing_plan: dict[str, Any] = {}
    if out.exists():
        existing_plan = json.loads(out.read_text(encoding="utf-8"))

    service = youtube()
    stream_id = args.stream_id or str(existing_plan.get("stream_id") or "").strip() or choose_stream_id(service, None)

    plan = {
        "date": day.strftime("%Y-%m-%d"),
        "privacy": args.privacy,
        "stream_id": stream_id,
        "broadcasts": dict(existing_plan.get("broadcasts") or {}),
    }

    for part in parts:
        existing_entry = plan["broadcasts"].get(part.key) or {}
        if existing_entry.get("id") and not args.dry_run:
            print(f"{part.key}: 既存の予約を保持します: {watch_url(existing_entry['id'])}")
            continue
        if not part.thumbnail.exists():
            raise SystemExit(f"サムネが見つかりません: {part.thumbnail}")
        body = broadcast_body(part, day, args.privacy)
        print(f"{part.key}: {body['snippet']['scheduledStartTime']} - {body['snippet']['scheduledEndTime']}")
        print(f"  title: {body['snippet']['title']}")
        print(f"  thumbnail: {part.thumbnail}")

        if args.dry_run:
            plan["broadcasts"][part.key] = {
                "id": None,
                "title": body["snippet"]["title"],
                "thumbnail": str(part.thumbnail),
                "scheduledStartTime": body["snippet"]["scheduledStartTime"],
                "scheduledEndTime": body["snippet"]["scheduledEndTime"],
            }
            continue

        created = service.liveBroadcasts().insert(
            part="snippet,status,contentDetails",
            body=body,
        ).execute()
        broadcast_id = created["id"]
        service.liveBroadcasts().bind(
            part="id,contentDetails",
            id=broadcast_id,
            streamId=stream_id,
        ).execute()
        set_thumbnail_with_retry(service, broadcast_id, part.thumbnail)

        plan["broadcasts"][part.key] = {
            "id": broadcast_id,
            "title": body["snippet"]["title"],
            "thumbnail": str(part.thumbnail),
            "scheduledStartTime": body["snippet"]["scheduledStartTime"],
            "scheduledEndTime": body["snippet"]["scheduledEndTime"],
            "watchUrl": watch_url(broadcast_id),
            "chatUrl": chat_url(broadcast_id),
        }
        print(f"  watch: {watch_url(broadcast_id)}")
        print(f"  chat:  {chat_url(broadcast_id)}")

    if args.dry_run:
        print("dry-run: manifestは保存していません。")
    else:
        out.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"manifest: {out}")


def complete_broadcast(args: argparse.Namespace) -> None:
    day = parse_date(args.date)
    file = manifest_path(day)
    if not file.exists():
        raise SystemExit(f"manifest が見つかりません: {file}")
    manifest = json.loads(file.read_text(encoding="utf-8"))
    entry = manifest.get("broadcasts", {}).get(args.part)
    if not entry or not entry.get("id"):
        raise SystemExit(f"{args.part} の broadcast id が manifest にありません。")
    broadcast_id = entry["id"]
    if args.dry_run:
        print(f"dry-run complete: {args.part} {broadcast_id}")
        return
    youtube().liveBroadcasts().transition(
        part="status",
        id=broadcast_id,
        broadcastStatus="complete",
    ).execute()
    print(f"completed: {args.part} {broadcast_id}")


def show_streams(_: argparse.Namespace) -> None:
    streams = list_streams(youtube())
    print(f"streams={len(streams)}")
    for stream in streams:
        snippet = stream.get("snippet", {})
        status = stream.get("status", {})
        cdn = stream.get("cdn", {})
        print(f"- title: {snippet.get('title', '')}")
        print(f"  id: {stream.get('id', '')}")
        print(f"  status: {status.get('streamStatus', '')}")
        print(f"  cdn: {cdn.get('resolution', '')}/{cdn.get('frameRate', '')}/{cdn.get('ingestionType', '')}")


def show_stream_key(args: argparse.Namespace) -> None:
    day = parse_date(args.date)
    stream_id = args.stream_id or stream_id_from_manifest(day)
    sys.stdout.write(get_stream_key(youtube(), stream_id))


def main() -> None:
    parser = argparse.ArgumentParser(description="Create and complete Masao YouTube Live broadcasts.")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create")
    create.add_argument("--date", required=True, help="YYYY-MM-DD JST")
    create.add_argument("--privacy", choices=["public", "unlisted", "private"], default="unlisted")
    create.add_argument("--stream-id", default=None)
    create.add_argument("--part1-start", default="07:00", help="HH:MM JST")
    create.add_argument("--part2-end", default="17:00", help="HH:MM JST")
    create.add_argument("--part3-start", default="17:00", help="HH:MM JST")
    create.add_argument("--part3-end", default="23:59", help="HH:MM JST")
    create.add_argument("--parts", default="part1,part2,part3", help="例: part1,part2")
    create.add_argument("--dry-run", action="store_true")
    create.set_defaults(func=create_broadcasts)

    complete = sub.add_parser("complete")
    complete.add_argument("--date", required=True, help="YYYY-MM-DD JST")
    complete.add_argument("--part", choices=["part1", "part2", "part3"], required=True)
    complete.add_argument("--dry-run", action="store_true")
    complete.set_defaults(func=complete_broadcast)

    streams = sub.add_parser("streams")
    streams.set_defaults(func=show_streams)

    stream_key = sub.add_parser("stream-key")
    stream_key.add_argument("--date", required=True, help="YYYY-MM-DD JST")
    stream_key.add_argument("--stream-id", default=None)
    stream_key.set_defaults(func=show_stream_key)

    args = parser.parse_args()
    try:
        args.func(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()

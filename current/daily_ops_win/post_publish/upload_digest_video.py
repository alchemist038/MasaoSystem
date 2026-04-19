#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

JST = timezone(timedelta(hours=9))
DEFAULT_TOKEN_PATH = Path(r"D:\OBS\REC\keys\youtube\token.json")


def load_creds(token_path: Path) -> Credentials:
    creds = Credentials.from_authorized_user_file(
        str(token_path),
        scopes=["https://www.googleapis.com/auth/youtube"],
    )
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_path.write_text(creds.to_json(), encoding="utf-8")
    return creds


def normalize_publish_at(raw: str) -> tuple[str, str]:
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=JST)
    else:
        dt = dt.astimezone(JST)
    jst_iso = dt.replace(microsecond=0).isoformat()
    utc_iso = dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return jst_iso, utc_iso


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def upload_video(
    youtube: Any,
    video_path: Path,
    title: str,
    description: str,
    publish_at_utc: str,
) -> Dict[str, Any]:
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": "15",
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": publish_at_utc,
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(str(video_path), mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        _, response = request.next_chunk()
    return response


def set_thumbnail(youtube: Any, video_id: str, thumb_path: Path) -> None:
    media = MediaFileUpload(str(thumb_path), mimetype="image/png", resumable=False)
    youtube.thumbnails().set(videoId=video_id, media_body=media).execute()


def add_to_playlist(youtube: Any, video_id: str, playlist_id: str) -> None:
    body = {
        "snippet": {
            "playlistId": playlist_id,
            "resourceId": {"kind": "youtube#video", "videoId": video_id},
        }
    }
    youtube.playlistItems().insert(part="snippet", body=body).execute()


def main() -> None:
    ap = argparse.ArgumentParser(description="Upload a single digest video with scheduled publish time")
    ap.add_argument("--video", required=True)
    ap.add_argument("--title-file", default="")
    ap.add_argument("--title", default="")
    ap.add_argument("--description-file", required=True)
    ap.add_argument("--thumbnail", default="")
    ap.add_argument("--publish-at", required=True, help="ISO datetime in JST, e.g. 2026-04-19T16:30:00+09:00")
    ap.add_argument("--token", default=str(DEFAULT_TOKEN_PATH))
    ap.add_argument("--playlist", default="")
    ap.add_argument("--out-json", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    video_path = Path(args.video)
    if not video_path.exists():
        raise SystemExit(f"video not found: {video_path}")

    title = read_text(Path(args.title_file)) if args.title_file else str(args.title).strip()
    if not title:
        raise SystemExit("title is empty")

    description = read_text(Path(args.description_file))
    if not description:
        raise SystemExit("description is empty")

    thumb_path = Path(args.thumbnail) if args.thumbnail else None
    if thumb_path and not thumb_path.exists():
        raise SystemExit(f"thumbnail not found: {thumb_path}")

    publish_at_jst, publish_at_utc = normalize_publish_at(args.publish_at)
    result: Dict[str, Any] = {
        "title": title,
        "video_path": str(video_path),
        "description_file": str(Path(args.description_file).resolve()),
        "thumbnail_path": str(thumb_path.resolve()) if thumb_path else "",
        "publish_at_jst": publish_at_jst,
        "publish_at_utc": publish_at_utc,
        "playlist_id": args.playlist,
        "status": "dry_run" if args.dry_run else "uploaded",
    }

    if args.dry_run:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    token_path = Path(args.token)
    if not token_path.exists():
        raise SystemExit(f"token not found: {token_path}")

    creds = load_creds(token_path)
    youtube = build("youtube", "v3", credentials=creds)

    upload_response = upload_video(
        youtube=youtube,
        video_path=video_path,
        title=title,
        description=description,
        publish_at_utc=publish_at_utc,
    )
    video_id = str(upload_response["id"])
    result["video_id"] = video_id
    result["youtube_url"] = f"https://www.youtube.com/watch?v={video_id}"

    if thumb_path:
        set_thumbnail(youtube, video_id, thumb_path)
        result["thumbnail_set"] = True
    else:
        result["thumbnail_set"] = False

    if args.playlist:
        add_to_playlist(youtube, video_id, args.playlist)
        result["playlist_added"] = True
    else:
        result["playlist_added"] = False

    if args.out_json:
        out_path = Path(args.out_json)
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

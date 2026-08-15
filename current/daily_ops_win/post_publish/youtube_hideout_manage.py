from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


TOKEN_PATH = Path(r"D:\OBS\REC\keys\youtube_hideout\token_hideout_ops.json")
EXPECTED_CHANNEL_ID = "UCIG-z7Q4rRq-cbIUJDB8SlA"
SCOPES = ["https://www.googleapis.com/auth/youtube"]


def youtube_client():
    if not TOKEN_PATH.exists():
        raise SystemExit(f"Hideout OAuth token not found: {TOKEN_PATH}")
    credentials = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    return build("youtube", "v3", credentials=credentials, cache_discovery=False)


def authorized_channel(youtube) -> dict[str, Any]:
    response = youtube.channels().list(
        part="id,snippet,statistics,contentDetails",
        mine=True,
        maxResults=1,
    ).execute()
    items = response.get("items", [])
    if len(items) != 1:
        raise SystemExit(f"Expected one authorized channel, got {len(items)}")
    channel = items[0]
    if channel.get("id") != EXPECTED_CHANNEL_ID:
        raise SystemExit(
            f"Wrong authorized channel: expected {EXPECTED_CHANNEL_ID}, "
            f"got {channel.get('id')}"
        )
    return channel


def print_result(value: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, ensure_ascii=False, indent=2))
        return
    if isinstance(value, list):
        for item in value:
            print(" | ".join(f"{key}={val}" for key, val in item.items()))
        if not value:
            print("No videos found.")
        return
    print(" | ".join(f"{key}={val}" for key, val in value.items()))


def command_status(channel: dict[str, Any], as_json: bool) -> None:
    stats = channel.get("statistics", {})
    result = {
        "channel": channel.get("snippet", {}).get("title", ""),
        "channel_id": channel.get("id", ""),
        "subscriber_count": stats.get("subscriberCount", "hidden"),
        "video_count": stats.get("videoCount", ""),
        "token_role": "youtube_hideout_ops",
        "token_path": str(TOKEN_PATH),
    }
    print_result(result, as_json)


def recent_uploads(youtube, channel: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    uploads_id = (
        channel.get("contentDetails", {})
        .get("relatedPlaylists", {})
        .get("uploads", "")
    )
    response = youtube.playlistItems().list(
        part="snippet,contentDetails,status",
        playlistId=uploads_id,
        maxResults=limit,
    ).execute()
    items = response.get("items", [])
    video_ids = [
        item.get("contentDetails", {}).get("videoId", "") for item in items
    ]
    video_ids = [video_id for video_id in video_ids if video_id]
    status_by_id: dict[str, dict[str, Any]] = {}
    if video_ids:
        videos_response = youtube.videos().list(
            part="id,snippet,status",
            id=",".join(video_ids),
            maxResults=len(video_ids),
        ).execute()
        status_by_id = {
            video.get("id", ""): video for video in videos_response.get("items", [])
        }

    result = []
    for item in items:
        video_id = item.get("contentDetails", {}).get("videoId", "")
        snippet = item.get("snippet", {})
        video = status_by_id.get(video_id, {})
        video_status = video.get("status", {})
        result.append(
            {
                "video_id": video_id,
                "published_at": snippet.get("publishedAt", ""),
                "privacy": video_status.get(
                    "privacyStatus", item.get("status", {}).get("privacyStatus", "")
                ),
                "publish_at": video_status.get("publishAt", ""),
                "title": video.get("snippet", {}).get(
                    "title", snippet.get("title", "")
                ),
            }
        )
    return result


def command_list_recent(
    youtube, channel: dict[str, Any], limit: int, as_json: bool
) -> None:
    print_result(recent_uploads(youtube, channel, limit), as_json)


def command_inspect(youtube, video_id: str, as_json: bool) -> None:
    response = youtube.videos().list(
        part="id,snippet,status,contentDetails,statistics",
        id=video_id,
    ).execute()
    items = response.get("items", [])
    if len(items) != 1:
        raise SystemExit(f"Video not found: {video_id}")
    video = items[0]
    snippet = video.get("snippet", {})
    if snippet.get("channelId") != EXPECTED_CHANNEL_ID:
        raise SystemExit(f"Video does not belong to the hideout channel: {video_id}")
    result = {
        "video_id": video.get("id", ""),
        "title": snippet.get("title", ""),
        "published_at": snippet.get("publishedAt", ""),
        "privacy": video.get("status", {}).get("privacyStatus", ""),
        "publish_at": video.get("status", {}).get("publishAt", ""),
        "duration": video.get("contentDetails", {}).get("duration", ""),
        "views": video.get("statistics", {}).get("viewCount", ""),
        "likes": video.get("statistics", {}).get("likeCount", ""),
        "comments": video.get("statistics", {}).get("commentCount", ""),
    }
    print_result(result, as_json)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def duplicate_matches(
    youtube,
    channel: dict[str, Any],
    title: str,
    publish_at: str,
) -> list[dict[str, Any]]:
    matches = []
    for item in recent_uploads(youtube, channel, 30):
        reasons = []
        if item.get("title") == title:
            reasons.append("same_title")
        if publish_at and item.get("publish_at") == publish_at:
            reasons.append("same_publish_at")
        if reasons:
            matches.append({**item, "reasons": reasons})
    return matches


def command_upload_manifest(
    youtube,
    channel: dict[str, Any],
    manifest_path: Path,
    execute: bool,
    as_json: bool,
) -> None:
    if not manifest_path.exists():
        raise SystemExit(f"Upload manifest not found: {manifest_path}")
    result_path = manifest_path.with_name(f"{manifest_path.stem}_result.json")
    if result_path.exists():
        raise SystemExit(f"Refusing a possible duplicate upload: {result_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("channelId") != EXPECTED_CHANNEL_ID:
        raise SystemExit("Upload manifest targets the wrong channel")
    video_path = Path(manifest.get("videoPath", ""))
    if not video_path.is_file():
        raise SystemExit(f"Upload video not found: {video_path}")

    expected_sha256 = str(manifest.get("sha256", "")).strip().upper()
    if len(expected_sha256) != 64:
        raise SystemExit("Upload manifest must contain a 64-character SHA-256")
    actual_sha256 = sha256_file(video_path)
    if actual_sha256 != expected_sha256:
        raise SystemExit(
            f"Video SHA-256 mismatch: expected {expected_sha256}, got {actual_sha256}"
        )

    title = str(manifest.get("title", "")).strip()
    description = str(manifest.get("description", ""))
    publish_at = str(manifest.get("publishAt", "")).strip()
    if not title or len(title) > 100:
        raise SystemExit("Title is empty or longer than 100 characters")
    if len(description) > 5000:
        raise SystemExit("Description is longer than 5000 characters")
    try:
        publish_dt = datetime.fromisoformat(publish_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SystemExit(f"Invalid publishAt: {publish_at}") from exc
    if (
        publish_dt.tzinfo is None
        or publish_dt.astimezone(timezone.utc) <= datetime.now(timezone.utc)
    ):
        raise SystemExit("publishAt must be a future timezone-aware timestamp")
    if manifest.get("privacyStatus") != "private":
        raise SystemExit("Scheduled upload must start as private")

    duplicates = duplicate_matches(youtube, channel, title, publish_at)
    if duplicates:
        raise SystemExit(
            "Refusing a possible remote duplicate: "
            + json.dumps(duplicates, ensure_ascii=False)
        )

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": manifest.get("tags", []),
            "categoryId": str(manifest.get("categoryId", "15")),
            "defaultLanguage": manifest.get("defaultLanguage", "ja"),
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": publish_at,
            "selfDeclaredMadeForKids": bool(
                manifest.get("selfDeclaredMadeForKids", False)
            ),
            "embeddable": True,
            "license": "youtube",
            "publicStatsViewable": True,
        },
    }
    plan = {
        "channel_id": EXPECTED_CHANNEL_ID,
        "token_role": "youtube_hideout_ops",
        "video_path": str(video_path),
        "sha256": actual_sha256,
        "title": title,
        "privacy": "private",
        "publish_at": publish_at,
        "remote_duplicate_check": "passed",
        "execute": execute,
    }
    if not execute:
        print_result(plan, as_json)
        return

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        chunksize=8 * 1024 * 1024,
        resumable=True,
    )
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
        notifySubscribers=True,
    )
    response = None
    while response is None:
        progress, response = request.next_chunk()
        if progress is not None and not as_json:
            print(f"upload_progress={progress.progress():.0%}")

    video_id = response.get("id", "")
    verify_response = youtube.videos().list(
        part="id,snippet,status", id=video_id
    ).execute()
    verify_items = verify_response.get("items", [])
    if len(verify_items) != 1:
        raise SystemExit(f"Uploaded video verification failed: {video_id}")
    verified = verify_items[0]
    snippet = verified.get("snippet", {})
    status = verified.get("status", {})
    if snippet.get("channelId") != EXPECTED_CHANNEL_ID:
        raise SystemExit(f"Uploaded video belongs to the wrong channel: {video_id}")

    result = {
        "video_id": video_id,
        "url": f"https://youtu.be/{video_id}",
        "channel_id": snippet.get("channelId", ""),
        "title": snippet.get("title", ""),
        "privacy": status.get("privacyStatus", ""),
        "publish_at": status.get("publishAt", ""),
        "sha256": actual_sha256,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "manifest_path": str(manifest_path),
    }
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    result["result_path"] = str(result_path)
    print_result(result, as_json)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Guarded YouTube API operations for Masao's hideout channel."
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status", help="Verify token and show channel status")
    recent = subparsers.add_parser("list-recent", help="List recent uploads")
    recent.add_argument("--limit", type=int, default=20, choices=range(1, 51))
    inspect = subparsers.add_parser("inspect", help="Inspect one channel video")
    inspect.add_argument("video_id")
    upload = subparsers.add_parser(
        "upload-manifest", help="Upload a guarded manifest after explicit approval"
    )
    upload.add_argument("manifest", type=Path)
    upload.add_argument("--execute", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    youtube = youtube_client()
    channel = authorized_channel(youtube)
    if args.command == "status":
        command_status(channel, args.json)
    elif args.command == "list-recent":
        command_list_recent(youtube, channel, args.limit, args.json)
    elif args.command == "inspect":
        command_inspect(youtube, args.video_id, args.json)
    elif args.command == "upload-manifest":
        command_upload_manifest(
            youtube, channel, args.manifest, args.execute, args.json
        )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


DEFAULT_TOKEN_PATH = r"D:\OBS\REC\keys\youtube\token.json"
DEFAULT_MAX_RESULTS = 80
DEFAULT_STRIP_PREFIXES = ("Cute Bunny Masao ",)
JST = timezone(timedelta(hours=9))
SHORTS_MAX_SECONDS = 60


def eprint(*args):
    print(*args, file=sys.stderr)


def parse_iso8601_duration(value: str) -> int:
    match = re.fullmatch(r"P(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)", value)
    if not match:
        return -1
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


def parse_publish_at_jst(status: Dict[str, Any]) -> Optional[datetime]:
    publish_str = status.get("publishAt")
    if not publish_str:
        return None
    try:
        dt = datetime.fromisoformat(publish_str.replace("Z", "+00:00"))
        return dt.astimezone(JST)
    except Exception:
        return None


def load_creds(token_path: str) -> Credentials:
    if not os.path.exists(token_path):
        raise FileNotFoundError(f"token.json not found: {token_path}")
    creds = Credentials.from_authorized_user_file(
        token_path,
        scopes=["https://www.googleapis.com/auth/youtube"],
    )
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return creds


def youtube_build(token_path: str):
    creds = load_creds(token_path)
    return build("youtube", "v3", credentials=creds)


def get_channel_uploads_playlist_id(youtube) -> str:
    response = youtube.channels().list(part="contentDetails", mine=True).execute()
    return response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]


def get_recent_videos(youtube, playlist_id: str, max_results: int = 150) -> List[Dict[str, Any]]:
    videos: List[Dict[str, Any]] = []
    next_page_token = None
    fetched_count = 0

    while fetched_count < max_results:
        req_count = min(50, max_results - fetched_count)
        response = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=req_count,
            pageToken=next_page_token,
        ).execute()

        items = response.get("items", [])
        if not items:
            break

        videos.extend(items)
        fetched_count += len(items)
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    video_ids = [item["contentDetails"]["videoId"] for item in videos]
    if not video_ids:
        return []

    detailed_items: List[Dict[str, Any]] = []
    for i in range(0, len(video_ids), 50):
        chunk_ids = video_ids[i : i + 50]
        response_details = youtube.videos().list(
            part="snippet,status,contentDetails",
            id=",".join(chunk_ids),
        ).execute()
        items = response_details.get("items", [])
        id_to_item = {item["id"]: item for item in items}
        detailed_items.extend([id_to_item[vid] for vid in chunk_ids if vid in id_to_item])

    return detailed_items


def get_recent_mine_videos(youtube, max_results: int = 150) -> List[Dict[str, Any]]:
    video_ids: List[str] = []
    next_page_token = None

    while len(video_ids) < max_results:
        req_count = min(50, max_results - len(video_ids))
        response = youtube.search().list(
            part="id",
            forMine=True,
            type="video",
            order="date",
            maxResults=req_count,
            pageToken=next_page_token,
        ).execute()

        items = response.get("items", [])
        if not items:
            break

        for item in items:
            video_id = item.get("id", {}).get("videoId")
            if video_id:
                video_ids.append(video_id)

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    if not video_ids:
        return []

    detailed_items: List[Dict[str, Any]] = []
    for i in range(0, len(video_ids), 50):
        chunk_ids = video_ids[i : i + 50]
        response_details = youtube.videos().list(
            part="snippet,status,contentDetails",
            id=",".join(chunk_ids),
        ).execute()
        items = response_details.get("items", [])
        id_to_item = {item["id"]: item for item in items}
        detailed_items.extend([id_to_item[vid] for vid in chunk_ids if vid in id_to_item])

    return detailed_items


def get_videos_by_ids(youtube, video_ids: Sequence[str]) -> List[Dict[str, Any]]:
    detailed_items: List[Dict[str, Any]] = []
    for i in range(0, len(video_ids), 50):
        chunk_ids = list(video_ids[i : i + 50])
        response = youtube.videos().list(
            part="snippet,status,contentDetails",
            id=",".join(chunk_ids),
        ).execute()
        items = response.get("items", [])
        id_to_item = {item["id"]: item for item in items}
        detailed_items.extend([id_to_item[vid] for vid in chunk_ids if vid in id_to_item])
    return detailed_items


def load_description_file(description_file: str) -> str:
    path = Path(description_file)
    if not path.exists():
        raise FileNotFoundError(f"description file not found: {description_file}")
    return path.read_text(encoding="utf-8").strip()


def load_title_map_file(title_map_file: str) -> Dict[str, str]:
    path = Path(title_map_file)
    if not path.exists():
        raise FileNotFoundError(f"title map file not found: {title_map_file}")

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("title map file must be a JSON object keyed by video ID")

    title_map: Dict[str, str] = {}
    for video_id, title in data.items():
        if not isinstance(video_id, str) or not isinstance(title, str):
            raise ValueError("title map file entries must be string:string")
        title_map[video_id] = title.strip()
    return title_map


def strip_known_prefixes(title: str, prefixes: Sequence[str]) -> str:
    value = title
    changed = True
    while changed:
        changed = False
        for prefix in prefixes:
            if prefix and value.startswith(prefix):
                value = value[len(prefix) :]
                changed = True
    return value


def build_title(old_title: str, title_prefix: str, strip_prefixes: Sequence[str]) -> str:
    base = strip_known_prefixes(old_title, strip_prefixes)
    new_title = f"{title_prefix}{base}" if title_prefix else base
    if len(new_title) > 100:
        new_title = new_title[:98] + "…"
    return new_title


def update_video_metadata(
    youtube,
    video: Dict[str, Any],
    new_title: str,
    new_description: str,
    publish_at_jst: datetime,
) -> None:
    video_id = video["id"]
    snippet = video["snippet"]
    category_id = snippet.get("categoryId", "15")

    body = {
        "id": video_id,
        "snippet": {
            "title": new_title,
            "description": new_description,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": publish_at_jst.isoformat(),
        },
    }

    youtube.videos().update(part="snippet,status", body=body).execute()


def main():
    ap = argparse.ArgumentParser(
        description="Update titles/descriptions of already-scheduled private Shorts without changing publish times."
    )
    ap.add_argument("--token", default=DEFAULT_TOKEN_PATH)
    ap.add_argument("--dry_run", action="store_true", help="Show changes without sending API requests.")
    ap.add_argument("--max", type=int, default=DEFAULT_MAX_RESULTS, help="How many recent uploads to inspect.")
    ap.add_argument(
        "--video_ids",
        default="",
        help="Comma-separated YouTube video IDs. If empty, all matching scheduled private Shorts in recent uploads are targeted.",
    )
    ap.add_argument(
        "--match_title",
        default="",
        help="Only target videos whose current title contains this string.",
    )
    ap.add_argument(
        "--title_prefix",
        default="",
        help="Prefix to apply after stripping known old prefixes. Empty means keep the stripped title as-is.",
    )
    ap.add_argument(
        "--strip_prefixes",
        default=",".join(DEFAULT_STRIP_PREFIXES),
        help="Comma-separated prefixes to strip before rebuilding the title.",
    )
    ap.add_argument(
        "--description_file",
        default="",
        help="UTF-8 text file to replace the description with. If omitted, the current description is kept.",
    )
    ap.add_argument(
        "--title_map_file",
        default="",
        help="JSON file mapping videoId to exact new title. If given, mapped titles are used as-is.",
    )
    args = ap.parse_args()

    youtube = youtube_build(args.token)
    target_ids = {v.strip() for v in args.video_ids.split(",") if v.strip()}
    strip_prefixes = tuple(p for p in (x.strip() for x in args.strip_prefixes.split(",")) if p)

    uploads_playlist_id = get_channel_uploads_playlist_id(youtube)
    if target_ids:
        recent_videos = get_videos_by_ids(youtube, list(target_ids))
        if not recent_videos:
            print("[INFO] No videos found for the specified video IDs.")
            return
    else:
        recent_videos = get_recent_mine_videos(youtube, max_results=args.max)
        if not recent_videos:
            print("[INFO] No recent channel videos found.")
            return

    if args.description_file:
        replacement_description = load_description_file(args.description_file)
    else:
        replacement_description = None

    if args.title_map_file:
        title_map = load_title_map_file(args.title_map_file)
    else:
        title_map = {}

    target_videos: List[Dict[str, Any]] = []
    for video in recent_videos:
        status = video.get("status", {})
        snippet = video.get("snippet", {})
        content_details = video.get("contentDetails", {})
        video_id = video["id"]
        privacy = status.get("privacyStatus", "")
        duration_seconds = parse_iso8601_duration(content_details.get("duration", ""))
        publish_at_jst = parse_publish_at_jst(status)

        if privacy != "private" or not publish_at_jst:
            continue
        if not (0 <= duration_seconds <= SHORTS_MAX_SECONDS):
            continue
        if target_ids and video_id not in target_ids:
            continue
        if args.match_title and args.match_title not in snippet.get("title", ""):
            continue

        target_videos.append(video)

    if not target_videos:
        print("[INFO] No scheduled private Shorts matched the conditions.")
        return

    target_videos.sort(
        key=lambda item: parse_publish_at_jst(item.get("status", {})) or datetime.max.replace(tzinfo=JST)
    )

    print("========================================")
    print("Scheduled Shorts Metadata Updater")
    if args.dry_run:
        print("DRY RUN")
    print("========================================")
    print("Source: channel videos via forMine search")
    print(f"Uploads playlist: {uploads_playlist_id}")
    print(f"Matched videos: {len(target_videos)}")
    if target_ids:
        print(f"Explicit video IDs: {sorted(target_ids)}")
    if args.description_file:
        print(f"Description source: {args.description_file}")
    else:
        print("Description source: keep current description")
    if args.title_map_file:
        print(f"Title map: {args.title_map_file}")

    processed = 0
    errors = 0

    for video in target_videos:
        video_id = video["id"]
        snippet = video.get("snippet", {})
        status = video.get("status", {})
        old_title = snippet.get("title", "")
        old_description = snippet.get("description", "")
        publish_at_jst = parse_publish_at_jst(status)
        if not publish_at_jst:
            continue

        if title_map:
            if video_id not in title_map:
                print(f"[SKIP] {video_id} not found in title map")
                continue
            new_title = title_map[video_id]
            if len(new_title) > 100:
                new_title = new_title[:98] + "…"
        else:
            new_title = build_title(old_title, args.title_prefix, strip_prefixes)
        new_description = replacement_description if replacement_description is not None else old_description

        print("-" * 50)
        print(f"Video ID: {video_id}")
        print(f"URL: https://www.youtube.com/watch?v={video_id}")
        print(f"Old title: {old_title}")
        print(f"New title: {new_title}")
        print(f"PublishAt: {publish_at_jst.strftime('%Y-%m-%d %H:%M:%S')} JST")
        if replacement_description is not None:
            print("Description: replace from file")
        else:
            print("Description: keep current")

        if args.dry_run:
            processed += 1
            print("[DRY RUN] no API changes sent")
            continue

        try:
            update_video_metadata(youtube, video, new_title, new_description, publish_at_jst)
            processed += 1
            print("[SUCCESS] updated")
        except HttpError as e:
            errors += 1
            eprint(f"[ERROR] API error for {video_id}: {e}")
        except Exception as e:
            errors += 1
            eprint(f"[ERROR] {video_id}: {e}")

    print("========================================")
    if args.dry_run:
        print(f"Dry run complete: {processed} videos matched")
    else:
        print(f"Done: {processed} updated / {errors} errors")
    print("========================================")


if __name__ == "__main__":
    main()

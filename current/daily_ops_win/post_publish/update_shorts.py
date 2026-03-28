#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

# Windows コンソールの文字化け(UnicodeEncodeError)対策
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# ====== constants ======
DEFAULT_TOKEN_PATH = r"d:\OBS\REC\keys\youtube\token.json"
DEFAULT_EXCLUDE_PATH = r"d:\OBS\REC\work\UNLISTED_VIDEOS_2026-03-23.md"

JST = timezone(timedelta(hours=9))

TITLE_PREFIX = "Cute Bunny Masao "

DESCRIPTION_TEMPLATE = """🐰 Cute Mini Rex Rabbit "Masao"

Masao is a mini rex rabbit living in Japan.
This short video captures one of his cute moments – relaxing, eating, playing, and sometimes doing funny bunny things.

Enjoy the peaceful bunny life 🐇✨


🐰 ミニレッキス「まさお」のショート動画です。

あくび / 寝落ち / ごはん / ゴロンなど  
日常のかわいい瞬間をぎゅっと切り抜いています✨


📌 まさおプロフィール
・2020年4月生まれ  
・2020年7月：家族になる  
・2023年10月：睾丸のがんで去勢手術  
・2025年5月：YouTubeデビュー  


📺 ライブ配信
朝〜夕方 / 夜にライブ配信しています  
18:30頃 ごはんタイム🥕


#rabbit #bunny #minirex #cuterabbit #petrabbit  
#うさぎ #ミニレッキス #まさお #shorts"""

# 投稿時間枠 (JST): 02:00, 06:00, 10:00, 14:00, 18:00, 22:00
SCHEDULE_HOURS = [2, 6, 10, 14, 18, 22]
START_DATE = datetime(2026, 3, 27, 22, tzinfo=JST)
SHORTS_MAX_SECONDS = 60
VIDEO_ID_MARKDOWN_RE = re.compile(r"Video ID:\s*`([A-Za-z0-9_-]{11})`")
VIDEO_ID_URL_RE = re.compile(r"youtube\.com/watch\?v=([A-Za-z0-9_-]{11})")

# ====== utils ======
def eprint(*args):
    print(*args, file=sys.stderr)

def now_jst() -> datetime:
    return datetime.now(JST)

def parse_iso8601_duration(value: str) -> int:
    match = re.fullmatch(r"P(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)", value)
    if not match:
        return -1
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds

def load_excluded_video_ids(exclude_path: str) -> set:
    """除外管理ファイルに記載された videoId のセットを返す"""
    if not exclude_path:
        return set()

    path = Path(exclude_path)
    if not path.exists():
        eprint(f"[WARN] 除外管理ファイルが見つかりません: {exclude_path}")
        return set()

    text = path.read_text(encoding="utf-8")
    video_ids = set(VIDEO_ID_MARKDOWN_RE.findall(text))

    # 念のため、Video ID 行が無い形式でも URL から拾えるようにしておく
    if not video_ids:
        video_ids = set(VIDEO_ID_URL_RE.findall(text))

    return video_ids

# ====== YouTube API ======
def load_creds(token_path: str) -> Credentials:
    if not os.path.exists(token_path):
        raise FileNotFoundError(f"token.json not found: {token_path}")
    creds = Credentials.from_authorized_user_file(token_path, scopes=["https://www.googleapis.com/auth/youtube"])
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return creds

def youtube_build(token_path: str):
    creds = load_creds(token_path)
    return build("youtube", "v3", credentials=creds)

def get_channel_uploads_playlist_id(youtube) -> str:
    """チャンネルの「アップロード済み」プレイリストIDを取得"""
    request = youtube.channels().list(
        part="contentDetails",
        mine=True
    )
    response = request.execute()
    return response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

def get_recent_videos(youtube, playlist_id: str, max_results: int = 150) -> List[Dict[str, Any]]:
    """最近アップロードされた動画のリストを取得。指定数までページングを行う"""
    videos = []
    next_page_token = None
    fetched_count = 0

    while fetched_count < max_results:
        req_count = min(50, max_results - fetched_count)
        request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=req_count,
            pageToken=next_page_token
        )
        response = request.execute()
        
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
        
    sorted_items = []
    # videos.list API は最大50件ずつしかリクエストできないのでチャンクに分ける
    for i in range(0, len(video_ids), 50):
        chunk_ids = video_ids[i:i+50]
        request_details = youtube.videos().list(
            part="snippet,status,contentDetails",
            id=",".join(chunk_ids)
        )
        response_details = request_details.execute()
        items = response_details.get("items", [])
        
        id_to_item = {item["id"]: item for item in items}
        sorted_items.extend([id_to_item[vid] for vid in chunk_ids if vid in id_to_item])
    
    return sorted_items

def get_all_scheduled_times(youtube, video_list: List[Dict[str, Any]]) -> set:
    """現在スケジュールされている全ての日時 (JST) のセットを取得"""
    scheduled_times = set()
    for video in video_list:
        status = video.get("status", {})
        privacy = status.get("privacyStatus", "")
        # private かつ publishAt があるもの
        if privacy == "private" and "publishAt" in status:
            publish_str = status["publishAt"]
            try:
                # '2025-05-15T18:00:00Z' 形式
                dt = datetime.fromisoformat(publish_str.replace("Z", "+00:00"))
                dt_jst = dt.astimezone(JST)
                scheduled_times.add(dt_jst)
            except Exception:
                pass
    return scheduled_times

def calc_next_publish_time(scheduled_times: set) -> datetime:
    """既存のスケジュールセットに存在しない、未来の最初の投稿枠を計算"""
    now = now_jst()
    start_date = START_DATE
    
    # 開始基準が未来ならその日から、過去（今日より前）なら今日から探す
    base_calc = max(start_date, now.replace(hour=0, minute=0, second=0, microsecond=0))

    for days_ahead in range(60): # 最大60日先まで探す
        day_base = base_calc + timedelta(days=days_ahead)
        
        for h in SCHEDULE_HOURS:
            candidate = day_base.replace(hour=h, minute=0, second=0, microsecond=0)
            # 指定日時以降かつ未来の時間はスキップ && 既に予約が入っていないかチェック
            if candidate >= start_date and candidate > now and candidate not in scheduled_times:
                return candidate
                
    return now + timedelta(hours=4) # フォールバック

def update_video_metadata(youtube, video: Dict[str, Any], new_title: str, publish_at_jst: datetime):
    """動画のタイトル、説明文、公開設定をAPIで更新"""
    video_id = video["id"]
    snippet = video["snippet"]
    
    # 既存のcategoryIdを維持。無ければ 15 (Pets & Animals)
    category_id = snippet.get("categoryId", "15") 
    
    body = {
        "id": video_id,
        "snippet": {
            "title": new_title,
            "description": DESCRIPTION_TEMPLATE,
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": publish_at_jst.isoformat(), 
        }
    }
    
    youtube.videos().update(
        part="snippet,status",
        body=body
    ).execute()

def add_to_playlist(youtube, video_id: str, playlist_id: str) -> None:
    """指定した動画を再生リストに追加する"""
    body = {
        "snippet": {
            "playlistId": playlist_id,
            "resourceId": {"kind": "youtube#video", "videoId": video_id},
        }
    }
    try:
        youtube.playlistItems().insert(part="snippet", body=body).execute()
    except HttpError as e:
        if "video already in playlist" in str(e).lower() or "already exists" in str(e).lower():
            pass # すでに追加済みの場合は無視
        else:
            raise e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", default=DEFAULT_TOKEN_PATH)
    ap.add_argument(
        "--exclude_file",
        default=DEFAULT_EXCLUDE_PATH,
        help="除外対象の videoId を含む Markdown ファイル。空文字で無効化できます。",
    )
    ap.add_argument("--dry_run", action="store_true", help="API送信を行わず画面に予定を表示するテストモード")
    ap.add_argument("--max", type=int, default=15, help="対象とする最近アップロードされた動画の最大数 (最大150件)")
    ap.add_argument("--playlist", type=str, default="", help="登録先の再生リストID（カンマ区切りで複数指定可能。空なら登録しない）")
    args = ap.parse_args()

    print("========================================")
    print("まさおYouTubeショート アップデートバッチ")
    if args.dry_run:
        print("★★★ DRY RUN (テストモード) ★★★")
    print("========================================")

    youtube = youtube_build(args.token)
    
    print("[1] チャンネル情報の取得中...")
    uploads_playlist_id = get_channel_uploads_playlist_id(youtube)
    print(f"  -> Uploads Playlist ID: {uploads_playlist_id}")
    
    if args.playlist:
        playlists_to_add = [p.strip() for p in args.playlist.split(",") if p.strip()]
        print(f"  -> 登録先プレイリスト ID: {playlists_to_add}")
    else:
        playlists_to_add = []

    print("[2] 最近の動画を取得・解析中...")
    recent_videos = get_recent_videos(youtube, uploads_playlist_id, max_results=args.max)
    
    if not recent_videos:
        print("動画が見つかりませんでした。")
        return

    # 全ての既存スケジュール時間を取得する
    scheduled_times = get_all_scheduled_times(youtube, recent_videos)
    if scheduled_times:
        latest = max(scheduled_times)
        print(f"  -> {len(scheduled_times)}件の既存予約を発見しました。最新の予約: {latest.strftime('%Y-%m-%d %H:%M:%S')} (JST)")
    else:
        print("  -> 既存の予約はありませんでした。")

    excluded_video_ids = load_excluded_video_ids(args.exclude_file)
    if args.exclude_file:
        print(f"  -> 除外対象 videoId: {len(excluded_video_ids)}件 ({args.exclude_file})")

    # 処理対象の動画をフィルタリング
    target_videos = []
    skipped_excluded = 0
    
    # YouTube APIは新しい順に返してくるため、スケジュールを昔アップした順に詰めるためにリバースする
    for video in reversed(recent_videos):
        video_id = video["id"]
        status = video.get("status", {})
        snippet = video.get("snippet", {})
        content_details = video.get("contentDetails", {})
        privacy = status.get("privacyStatus", "")
        desc = snippet.get("description", "").strip()
        duration_seconds = parse_iso8601_duration(content_details.get("duration", ""))

        if video_id in excluded_video_ids:
            skipped_excluded += 1
            continue
        
        # 条件: 非公開 / Shorts / 説明欄が空欄 / 未予約
        if (
            privacy == "private"
            and desc == ""
            and "publishAt" not in status
            and 0 <= duration_seconds <= SHORTS_MAX_SECONDS
        ):
            target_videos.append(video)

    if not target_videos:
        print("\n[INFO] アップデート対象（非公開ショート＆説明空欄）は見つかりませんでした。")
        return

    print(f"\n[3] {len(target_videos)} 件の動画をアップデートします...\n")
    if skipped_excluded:
        print(f"[INFO] 除外管理ファイルに一致したためスキップ: {skipped_excluded}件\n")

    processed = 0
    errors = 0

    for video in target_videos:
        video_id = video["id"]
        old_title = video["snippet"].get("title", "")
        
        # 新しいタイトル （すでに接頭辞がついていたら無視）
        if old_title.startswith(TITLE_PREFIX):
            new_title = old_title
        else:
            new_title = TITLE_PREFIX + old_title

        # タイトル長オーバー対策 (100文字制限)
        if len(new_title) > 100:
            new_title = new_title[:98] + "…"

        # 次の公開時刻を、空いている枠から計算
        next_publish = calc_next_publish_time(scheduled_times)
        # 次の動画の計算のため、今割り当てた時間を予約済みリストに追加する
        scheduled_times.add(next_publish)
        
        print("-" * 50)
        print(f"動画ID: {video_id} (http://youtube.com/watch?v={video_id})")
        print(f"旧タイトル: {old_title}")
        print(f"新タイトル: {new_title}")
        print(f"予定時刻:   {next_publish.strftime('%Y-%m-%d %H:%M:%S')} (JST)")
        if playlists_to_add:
            print(f"再生リスト: {playlists_to_add} に追加予定")

        if args.dry_run:
            processed += 1
            print("→ [DRY RUN] 変更をスキップしました。")
            continue

        try:
            update_video_metadata(youtube, video, new_title, next_publish)
            if playlists_to_add:
                for pid in playlists_to_add:
                    add_to_playlist(youtube, video_id, pid)
                print("→ [SUCCESS] 更新と再生リストへの追加完了！")
            else:
                print("→ [SUCCESS] 更新完了！")
            processed += 1
        except HttpError as e:
            errors += 1
            eprint(f"→ [ERROR] APIエラー: {e}")
        except Exception as e:
            errors += 1
            eprint(f"→ [ERROR] {e}")

    print("\n========================================")
    if args.dry_run:
        print(f"完了: DRY RUN モードです。（実際の更新は行われませんでした）")
    else:
        print(f"完了: {processed}件処理成功, エラー: {errors}件")
    print("========================================")

if __name__ == "__main__":
    main()

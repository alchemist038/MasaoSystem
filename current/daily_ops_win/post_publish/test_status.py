import sys
from googleapiclient.discovery import build
import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import sys

# Windows コンソールの文字化け(UnicodeEncodeError)対策
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

token_path = r"d:\OBS\REC\keys\youtube\token.json"
creds = Credentials.from_authorized_user_file(token_path, scopes=["https://www.googleapis.com/auth/youtube"])
if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())

youtube = build("youtube", "v3", credentials=creds)

req = youtube.channels().list(part="contentDetails", mine=True)
res = req.execute()
pid = res["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

req2 = youtube.playlistItems().list(part="contentDetails", playlistId=pid, maxResults=50)
res2 = req2.execute()
vids = [item["contentDetails"]["videoId"] for item in res2.get("items", [])]

req3 = youtube.videos().list(part="snippet,status", id=",".join(vids))
res3 = req3.execute()

for item in res3.get("items", []):
    print(f"ID: {item['id']}")
    print(f"Title: {item['snippet']['title'][:40]}")
    print(f"Privacy: {item['status'].get('privacyStatus')}")
    print(f"PublishAt: {item['status'].get('publishAt', 'None')}")
    print("-" * 20)

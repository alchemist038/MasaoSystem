import os
import sys
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

token_path = r"d:\OBS\REC\keys\youtube\token.json"
creds = Credentials.from_authorized_user_file(token_path, scopes=["https://www.googleapis.com/auth/youtube"])
if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())

youtube = build("youtube", "v3", credentials=creds)

request = youtube.playlists().list(
    part="snippet",
    mine=True,
    maxResults=50
)
response = request.execute()

print("Available Playlists:")
for item in response.get("items", []):
    print(f"ID: {item['id']} | Title: {item['snippet']['title']}")

"""Testet den YouTube-API-Zugang: sucht Videos zu einem Suchbegriff und liest Top-Kommentare eines Treffers."""
import os
import sys

from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv()

API_KEY = os.environ["YOUTUBE_API_KEY"]
QUERY = sys.argv[1] if len(sys.argv) > 1 else "ich weiß was ich tun müsste aber mache es nicht"

youtube = build("youtube", "v3", developerKey=API_KEY)

search_response = youtube.search().list(
    q=QUERY,
    part="snippet",
    type="video",
    maxResults=3,
    relevanceLanguage="de",
).execute()

videos = search_response.get("items", [])
print(f"Suchbegriff: {QUERY!r}")
print(f"Gefundene Videos: {len(videos)}\n")

for video in videos:
    video_id = video["id"]["videoId"]
    title = video["snippet"]["title"]
    print(f"- {title} (https://youtube.com/watch?v={video_id})")

if not videos:
    print("Keine Videos gefunden.")
    sys.exit(0)

first_video_id = videos[0]["id"]["videoId"]
print(f"\nTop-Kommentare zum ersten Treffer ({first_video_id}):\n")

try:
    comments_response = youtube.commentThreads().list(
        videoId=first_video_id,
        part="snippet",
        maxResults=5,
        order="relevance",
        textFormat="plainText",
    ).execute()
    comments = comments_response.get("items", [])
    if not comments:
        print("Keine Kommentare gefunden (oder Kommentare deaktiviert).")
    for item in comments:
        text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
        likes = item["snippet"]["topLevelComment"]["snippet"]["likeCount"]
        print(f"[{likes} Likes] {text[:200]}")
        print("---")
except Exception as e:
    print(f"Kommentare konnten nicht geladen werden: {e}")

print("\nTest erfolgreich: YouTube-API-Zugang funktioniert.")

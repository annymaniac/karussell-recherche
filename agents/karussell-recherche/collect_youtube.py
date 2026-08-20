"""Sammelt YouTube-Kommentare zu mehreren kurzen Suchbegriffen und speichert sie als JSON."""
import json
import os
import sys

from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv()

API_KEY = os.environ["YOUTUBE_API_KEY"]
youtube = build("youtube", "v3", developerKey=API_KEY)

SEARCH_TERMS = [
    "Selbstsabotage überwinden",
    "innere Blockaden lösen",
    "Selbstwert stärken Frauen",
]


def collect_for_term(query, max_videos=3, max_comments_per_video=15):
    search_response = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=max_videos,
        relevanceLanguage="de",
    ).execute()

    results = []
    for video in search_response.get("items", []):
        video_id = video["id"]["videoId"]
        title = video["snippet"]["title"]
        try:
            comments_response = youtube.commentThreads().list(
                videoId=video_id,
                part="snippet",
                maxResults=max_comments_per_video,
                order="relevance",
                textFormat="plainText",
            ).execute()
        except Exception:
            continue

        comments = []
        for item in comments_response.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "text": snippet["textDisplay"],
                "likes": snippet["likeCount"],
            })

        results.append({
            "video_title": title,
            "video_url": f"https://youtube.com/watch?v={video_id}",
            "search_term": query,
            "comments": comments,
        })
    return results


if __name__ == "__main__":
    all_results = []
    for term in SEARCH_TERMS:
        print(f"Sammle Kommentare für: {term!r}")
        all_results.extend(collect_for_term(term))

    out_path = os.path.join(os.path.dirname(__file__), "raw_comments.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    total_comments = sum(len(v["comments"]) for v in all_results)
    print(f"\nFertig: {len(all_results)} Videos, {total_comments} Kommentare gesammelt.")
    print(f"Gespeichert in: {out_path}")

from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build
import os
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")

youtube = build("youtube", "v3", developerKey=API_KEY)


def search_youtube(query, max_results=5):
    request = youtube.search().list(
        q=query, part="snippet", type="video", maxResults=max_results
    )

    response = request.execute()

    videos = []

    for item in response["items"]:
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        link = f"https://www.youtube.com/watch?v={video_id}"

        videos.append({"title": title, "video_id": video_id, "link": link})

    return videos


def get_transcripts_for_videos(video_ids):
    api = YouTubeTranscriptApi()
    transcripts = []

    for vid in video_ids:
        try:
            transcript = api.fetch(vid, languages=["en"])
            text = " ".join([item.text for item in transcript])
            transcripts.append(text)

        except Exception:
            continue

    return transcripts

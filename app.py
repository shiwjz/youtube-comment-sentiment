
from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
import re
import requests


load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def extract_video_id(url: str):
    if not url:
        return None

    # 1) watch?v=VIDEOID
    m = re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", url)
    if m:
        return m.group(1)

    # 2) youtu.be/VIDEOID
    m = re.search(r"youtu\.be/([a-zA-Z0-9_-]{11})", url)
    if m:
        return m.group(1)

    # 3) shorts/VIDEOID
    m = re.search(r"shorts/([a-zA-Z0-9_-]{11})", url)
    if m:
        return m.group(1)

    return None

def fetch_comments(video_id: str, max_comments: int):
    """
    YouTube Data API v3 - commentThreads.list 사용
    반환: 댓글 리스트 (각 댓글에 text/author/likeCount/publishedAt 포함)
    """
    comments = []
    page_token = None

    # YouTube API는 한 번에 최대 100개까지
    per_page = 100

    while len(comments) < max_comments:
        fetch_count = min(per_page, max_comments - len(comments))

        params = {
            "part": "snippet",
            "videoId": video_id,
            "key": YOUTUBE_API_KEY,
            "maxResults": fetch_count,
            "textFormat": "plainText",
        }
        if page_token:
            params["pageToken"] = page_token

        url = "https://www.googleapis.com/youtube/v3/commentThreads"
        res = requests.get(url, params=params, timeout=20)

        if res.status_code != 200:
            # 에러 내용 그대로 반환하기 좋게 예외로 던짐
            raise RuntimeError(f"YouTube API error {res.status_code}: {res.text}")

        data = res.json()
        items = data.get("items", [])

        for item in items:
            top = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "text": top.get("textDisplay", ""),
                "author": top.get("authorDisplayName", ""),
                "likeCount": top.get("likeCount", 0),
                "publishedAt": top.get("publishedAt", ""),
            })

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    return comments


app = Flask(__name__)

@app.get("/")
def home():
    return render_template("index.html")

@app.post("/api/analyze")
def analyze():
    data = request.get_json(silent=True) or {}
    url = data.get("url")
    max_comments = data.get("maxComments")

    if not url:
        return jsonify({"ok": False, "error": "url is required"}), 400
    if max_comments is None:
        return jsonify({"ok": False, "error": "maxComments is required"}), 400

    try:
        max_comments = int(max_comments)
    except:
        return jsonify({"ok": False, "error": "maxComments must be a number"}), 400

    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({"ok": False, "error": "Invalid YouTube URL"}), 400

    if not YOUTUBE_API_KEY:
        return jsonify({"ok": False, "error": "Missing YOUTUBE_API_KEY"}), 500

    try:
        comments = fetch_comments(video_id, max_comments)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    return jsonify({
        "ok": True,
        "videoId": video_id,
        "count": len(comments),
        "comments": comments
    }), 200



if __name__ == "__main__":
    app.run(debug=True)

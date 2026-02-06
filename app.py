from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
import re
import requests

# =============================
# M3: Rule-based Sentiment Config
# =============================
POSITIVE_KEYWORDS = [
    "좋다", "좋아요", "최고", "재밌", "재미", "감동", "대박",
    "행복", "웃", "감사", "힐링", "응원", "짱", "멋지", "사랑"
]

NEGATIVE_KEYWORDS = [
    "별로", "싫다", "최악", "불편", "실망", "짜증",
    "화나", "안좋", "못하", "문제", "노잼", "욕", "헬"
]

# =============================
# Env
# =============================
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# =============================
# Text Utils
# =============================
def preprocess_text(text: str) -> str:
    text = (text or "").lower()
    # 특수문자 제거(한글/영문/숫자/공백만)
    text = re.sub(r"[^a-z0-9가-힣\s]", "", text)
    # 공백 정리
    return " ".join(text.split()).strip()

def analyze_sentiment(text: str) -> str:
    # 너무 짧으면 neutral
    if not text or len(text.strip()) < 3:
        return "neutral"

    t = preprocess_text(text)

    pos = sum(1 for kw in POSITIVE_KEYWORDS if kw in t)
    neg = sum(1 for kw in NEGATIVE_KEYWORDS if kw in t)

    if pos > neg:
        return "positive"
    elif neg > pos:
        return "negative"
    return "neutral"

def analyze_comments(comments: list):
    results = []
    counts = {
        "positive": 0,
        "negative": 0,
        "neutral": 0
    }

    for c in comments:
        sentiment = analyze_sentiment(c["text"])
        counts[sentiment] += 1

        results.append({
            "text": c["text"],
            "sentiment": sentiment,
            "author": c.get("author"),
            "likeCount": c.get("likeCount"),
            "publishedAt": c.get("publishedAt")
        })

    total = sum(counts.values())

    return results, counts, total


    total = sum(counts.values())
    return results, counts, total

def make_summary(counts: dict) -> str:
    pos = counts.get("positive", 0)
    neg = counts.get("negative", 0)
    neu = counts.get("neutral", 0)

    if pos > neg and pos > neu:
        return "전반적으로 반응이 좋은 영상입니다."
    elif neg > pos and neg > neu:
        return "부정적인 반응이 많은 영상입니다."
    else:
        return "반응이 엇갈리는 영상입니다."

# =============================
# YouTube Utils
# =============================
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
    YouTube Data API v3 - commentThreads.list
    반환: 댓글 리스트 (각 댓글에 text/author/likeCount/publishedAt 포함)
    """
    comments = []
    page_token = None
    per_page = 100  # API max

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

        api_url = "https://www.googleapis.com/youtube/v3/commentThreads"
        res = requests.get(api_url, params=params, timeout=20)

        if res.status_code != 200:
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

# =============================
# Flask App
# =============================
app = Flask(__name__)

@app.get("/")
def home():
    return render_template("index.html")

@app.post("/api/analyze")
def analyze():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    max_comments = data.get("maxComments")

    if not url:
        return jsonify({"ok": False, "error": "url is required"}), 400
    if max_comments is None:
        return jsonify({"ok": False, "error": "maxComments is required"}), 400

    try:
        max_comments = int(max_comments)
    except:
        return jsonify({"ok": False, "error": "maxComments must be a number"}), 400

    if max_comments <= 0:
        return jsonify({"ok": False, "error": "maxComments must be >= 1"}), 400

    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({"ok": False, "error": "Invalid YouTube URL"}), 400

    if not YOUTUBE_API_KEY:
        return jsonify({"ok": False, "error": "Missing YOUTUBE_API_KEY"}), 500

    # 1) 댓글 수집
    try:
        comments = fetch_comments(video_id, max_comments)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    # 2) 댓글 0개면 분석 생략
    if len(comments) == 0:
        return jsonify({
            "ok": True,
            "counts": {"totalFetched": 0},
            "sentiment": {"positive": 0, "negative": 0, "neutral": 0},
            "summary": "댓글이 없어 분석할 수 없습니다.",
            "comments": []
        }), 200

    # 3) 감정 분석 + 통계 + 요약
    analyzed_comments, sentiment_counts, total = analyze_comments(comments)
    summary = make_summary(sentiment_counts)

    return jsonify({
        "ok": True,
        "counts": {"totalFetched": total},
        "sentiment": sentiment_counts,
        "summary": summary,
        "comments": analyzed_comments
    }), 200

if __name__ == "__main__":
    app.run(debug=True)

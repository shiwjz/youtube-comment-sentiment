from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
import re
import requests
import os
import re
import random
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

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

# =============================
# 1) 언어별 키워드 (최소세트)
# =============================
POSITIVE_KEYWORDS_KO = ["좋다", "좋아요", "최고", "재밌", "재미", "감동", "대박", "행복", "힐링", "응원", "사랑", "멋지", "짱"]
POSITIVE_KEYWORDS_KO += [
    "꿀잼", "존잼", "개꿀", "레전드", "갓", "찢었", "미쳤다",
    "미쳤네", "개잘", "잘한다", "최고다", "사랑해",
    "너무 좋", "너무 재밌", "웃기다", "감동적", "감사합니다"
]

@app.post("/api/analyze")
def analyze():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    max_comments = data.get("maxComments")
NEGATIVE_KEYWORDS_KO = ["별로", "싫다", "최악", "불편", "실망", "짜증", "화나", "노잼", "구리", "망", "욕", "헬", "답답"]

POSITIVE_KEYWORDS_EN = ["good", "great", "awesome", "amazing", "love", "best", "fun", "cool", "perfect", "thanks", "helpful"]
NEGATIVE_KEYWORDS_EN = ["bad", "worst", "hate", "terrible", "awful", "boring", "trash", "annoying", "dislike", "cringe", "scam"]

POSITIVE_KEYWORDS_JA = ["最高", "好き", "いい", "良い", "面白", "感動", "すごい", "ありがとう", "可愛い", "神"]
NEGATIVE_KEYWORDS_JA = ["嫌い", "最悪", "つまら", "微妙", "ひどい", "ゴミ", "うざい", "無理"]

POSITIVE_KEYWORDS_ZH = ["好", "很好", "太棒", "喜欢", "爱", "精彩", "感动", "厉害", "谢谢", "可爱"]
NEGATIVE_KEYWORDS_ZH = ["差", "很差", "讨厌", "最差", "无聊", "垃圾", "恶心", "糟糕", "失望"]

KEYWORDS = {
    "ko": (POSITIVE_KEYWORDS_KO, NEGATIVE_KEYWORDS_KO),
    "en": (POSITIVE_KEYWORDS_EN, NEGATIVE_KEYWORDS_EN),
    "ja": (POSITIVE_KEYWORDS_JA, NEGATIVE_KEYWORDS_JA),
    "zh": (POSITIVE_KEYWORDS_ZH, NEGATIVE_KEYWORDS_ZH),
}

MIN_LEN = 3

POSITIVE_EMOJIS = ["❤️", "💕", "💖", "🔥", "👍", "👏", "😂", "🤣", "🥹"]
NEGATIVE_EMOJIS = ["🤮", "🤢", "😡", "🤬", "👎"]

# =============================
# 2) 유튜브 URL → videoId 추출
# =============================
def extract_video_id(url: str):
    if not url:
        return None

    m = re.search(r"youtu\.be/([A-Za-z0-9_-]{6,})", url)
    if m:
        return m.group(1)

    m = re.search(r"[?&]v=([A-Za-z0-9_-]{6,})", url)
    if m:
        return m.group(1)

    m = re.search(r"youtube\.com/shorts/([A-Za-z0-9_-]{6,})", url)
    if m:
        return m.group(1)

    m = re.search(r"youtube\.com/embed/([A-Za-z0-9_-]{6,})", url)
    if m:
        return m.group(1)

    return None

# =============================
# 3) lang=auto 감지
# =============================
RE_KO = re.compile(r"[가-힣]")
RE_JA = re.compile(r"[\u3040-\u309F\u30A0-\u30FF]")
RE_ZH = re.compile(r"[\u4E00-\u9FFF]")
RE_EN = re.compile(r"[A-Za-z]")

def detect_lang_auto(text: str) -> str:
    if not text:
        return "en"
    if RE_KO.search(text):
        return "ko"
    if RE_JA.search(text):
        return "ja"
    zh_hits = len(RE_ZH.findall(text))
    en_hits = len(RE_EN.findall(text))
    if zh_hits >= 2 and en_hits == 0:
        return "zh"
    if en_hits > 0:
        return "en"
    return "en"

# =============================
# 4) 전처리 + 감정분석
# =============================
def preprocess(text: str, lang: str) -> str:
    t = (text or "").strip().lower()

    if lang == "en":
        t = re.sub(r"[^a-z0-9\s]", " ", t)
    elif lang == "ko":
        t = re.sub(r"[^0-9a-z가-힣\s]", " ", t)
    else:  # ja/zh
        t = re.sub(r"[^\w\u3040-\u30FF\u4E00-\u9FFF\s]", " ", t)

    t = re.sub(r"\s+", " ", t).strip()
    return t

def score_keywords(cleaned: str, keywords: list[str]) -> int:
    return sum(1 for kw in keywords if kw and kw in cleaned)

def classify_sentiment(text: str, lang_choice: str):
    lang = detect_lang_auto(text) if lang_choice == "auto" else lang_choice
    cleaned = preprocess(text, lang)

    if len(cleaned) < MIN_LEN:
        return "neutral", lang

    pos_list, neg_list = KEYWORDS.get(lang, KEYWORDS["en"])
    pos = score_keywords(cleaned, pos_list)
    neg = score_keywords(cleaned, neg_list)

    # 이모지 점수 추가 (여기 들여쓰기 중요!)
    for e in POSITIVE_EMOJIS:
        if e in text:
            pos += 1

    for e in NEGATIVE_EMOJIS:
        if e in text:
            neg += 1

    if pos > neg:
        return "positive", lang
    if neg > pos:
        return "negative", lang
    return "neutral", lang


def build_summary(ratios: dict) -> str:
    p = ratios.get("positive", 0.0)
    n = ratios.get("negative", 0.0)
    u = ratios.get("neutral", 0.0)

    top = max(p, n, u)
    close = sum(1 for x in (p, n, u) if abs(top - x) <= 0.10)

    if close >= 2:
        return "반응이 엇갈리는 영상입니다."
    if top == p:
        return "전반적으로 반응이 좋은 영상입니다."
    if top == n:
        return "부정적인 반응이 많은 영상입니다."
    return "중립적인 반응이 많은 영상입니다."

# =============================
# 5) YouTube API: 댓글 가져오기
# =============================
def fetch_youtube_comments(video_id: str, max_comments: int, sort: str):
    if not YOUTUBE_API_KEY:
        raise RuntimeError("Missing YOUTUBE_API_KEY in .env")

    order_param = "time" if sort == "latest" else "relevance"

    comments = []
    page_token = None

    while len(comments) < max_comments:
        remaining = max_comments - len(comments)
        max_results = 100 if remaining > 100 else remaining

        params = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": max_results,
            "order": order_param,
            "textFormat": "plainText",
            "key": YOUTUBE_API_KEY,
        }
        if page_token:
            params["pageToken"] = page_token

        r = requests.get("https://www.googleapis.com/youtube/v3/commentThreads", params=params, timeout=15)
        if r.status_code != 200:
            raise RuntimeError(f"YouTube API error: {r.status_code} {r.text}")

        data = r.json()
        items = data.get("items", [])

        for it in items:
            sn = it["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "text": sn.get("textDisplay") or "",
                "likeCount": int(sn.get("likeCount") or 0),
                "publishedAt": sn.get("publishedAt") or "",
                "author": sn.get("authorDisplayName") or ""
            })

        page_token = data.get("nextPageToken")
        if not page_token or not items:
            break

    return comments

# =============================
# 6) 요청 검증
# =============================
ALLOWED_MAX = {50, 100, 200}
ALLOWED_SORT = {"latest", "likes"}
ALLOWED_LANG = {"auto", "ko", "en", "ja", "zh"}

def bad_request(msg: str):
    return jsonify({"ok": False, "error": {"code": "BAD_REQUEST", "message": msg}}), 400

# =============================
# 7) POST /api/analyze
# =============================
@app.post("/api/analyze")
def api_analyze():
    try:
        data = request.get_json(force=True) or {}

        url = data.get("url")
        max_comments = data.get("maxComments")
        sort = data.get("sort", "latest")
        lang = data.get("lang", "auto")
        random_sample = bool(data.get("randomSample", False))

        if not url:
            return bad_request("url is required")

        if not isinstance(max_comments, int):
            return bad_request("maxComments must be an integer (50/100/200)")
        if max_comments not in ALLOWED_MAX:
            return bad_request("maxComments must be one of 50, 100, 200")

        if sort not in ALLOWED_SORT:
            return bad_request('sort must be "latest" or "likes"')
        if lang not in ALLOWED_LANG:
            return bad_request('lang must be "auto"|"ko"|"en"|"ja"|"zh"')

        video_id = extract_video_id(url)
        if not video_id:
            return bad_request("Could not extract videoId from url")

        raw_comments = fetch_youtube_comments(video_id, max_comments, sort)

        if random_sample:
            random.shuffle(raw_comments)

        if len(raw_comments) == 0:
            return jsonify({
                "ok": True,
                "meta": {"videoId": video_id},
                "counts": {"totalFetched": 0},
                "sentiment": {"positive": 0, "negative": 0, "neutral": 0},
                "ratios": {"positive": 0.0, "negative": 0.0, "neutral": 0.0},
                "summary": "댓글이 없어 분석할 수 없습니다.",
                "comments": []
            })

        stats = {"positive": 0, "negative": 0, "neutral": 0}
        labeled = []

        for c in raw_comments:
            text = c.get("text", "")
            sent, detected_lang = classify_sentiment(text, lang)
            stats[sent] += 1
            labeled.append({
                "text": text,
                "sentiment": sent,
                "lang": detected_lang,
                "likeCount": c.get("likeCount", 0),
                "publishedAt": c.get("publishedAt", ""),
                "author": c.get("author", "")
            })

        total = len(labeled)
        ratios = {
            "positive": round(stats["positive"] / total, 4),
            "negative": round(stats["negative"] / total, 4),
            "neutral": round(stats["neutral"] / total, 4),
        }

        return jsonify({
            "ok": True,
            "meta": {
                "videoId": video_id,
                "requested": {"maxComments": max_comments, "sort": sort, "lang": lang, "randomSample": random_sample},
                "youtubeOrder": "time" if sort == "latest" else "relevance"
            },
            "counts": {"totalFetched": total},
            "sentiment": stats,
            "ratios": ratios,
            "summary": build_summary(ratios),
            "comments": labeled
        })

    except Exception as e:
        return jsonify({"ok": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}}), 500
@app.get("/test")
def test_api():
    return jsonify({"message": "M4 server is working!"})
@app.get("/routes")
def routes():
    return jsonify(sorted([str(r) for r in app.url_map.iter_rules()]))
@app.get("/run")
def run_analyze_in_browser():
    # 여기 영상 URL은 테스트용(릭롤)로 고정
    payload = {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "maxComments": 50,
        "sort": "latest",
        "lang": "auto",
        "randomSample": False
    }

    # Flask 내부에서 POST 요청을 가짜로 만들어 /api/analyze 실행
    with app.test_client() as c:
        res = c.post("/api/analyze", json=payload)
        return (res.data, res.status_code, res.headers.items())

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


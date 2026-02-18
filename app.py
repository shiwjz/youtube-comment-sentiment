from flask import Flask, render_template, request, jsonify
import os, re, random
import requests
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

app = Flask(__name__)

# =============================
# Keywords (M4 minimal)
# =============================
POSITIVE_KEYWORDS_KO = [
    "좋다","좋아요","최고","재밌","재미","감동","대박","행복","힐링","응원","사랑","멋지","짱",
    "꿀잼","존잼","개꿀","레전드","갓","찢었","미쳤다","미쳤네","개잘","잘한다","최고다","사랑해",
    "너무 좋","너무 재밌","웃기다","감동적","감사합니다"
]
NEGATIVE_KEYWORDS_KO = ["별로","싫다","최악","불편","실망","짜증","화나","노잼","구리","망","욕","헬","답답","주작","쓰레기","거품팀","병맛","개못","못한다","별로다","싫어","너무 별로","재미없다","지루하다","감동 없다","똥먹어라", "내보내", "쳐발리","못하"]

POSITIVE_KEYWORDS_EN = ["good","great","awesome","amazing","love","best","fun","cool","perfect","thanks","helpful"]
NEGATIVE_KEYWORDS_EN = ["bad","worst","hate","terrible","awful","boring","trash","annoying","dislike","cringe","scam"]

POSITIVE_KEYWORDS_JA = ["最高","好き","いい","良い","面白","感動","すごい","ありがとう","可愛い","神"]
NEGATIVE_KEYWORDS_JA = ["嫌い","最悪","つまら","微妙","ひどい","ゴミ","うざい","無理"]

POSITIVE_KEYWORDS_ZH = ["好","很好","太棒","喜欢","爱","精彩","感动","厉害","谢谢","可爱"]
NEGATIVE_KEYWORDS_ZH = ["差","很差","讨厌","最差","无聊","垃圾","恶心","糟糕","失望"]

KEYWORDS = {
    "ko": (POSITIVE_KEYWORDS_KO, NEGATIVE_KEYWORDS_KO),
    "en": (POSITIVE_KEYWORDS_EN, NEGATIVE_KEYWORDS_EN),
    "ja": (POSITIVE_KEYWORDS_JA, NEGATIVE_KEYWORDS_JA),
    "zh": (POSITIVE_KEYWORDS_ZH, NEGATIVE_KEYWORDS_ZH),
}

POSITIVE_EMOJIS = ["❤️","💕","💖","🔥","👍","👏","😂","🤣","🥹"]
NEGATIVE_EMOJIS = ["🤮","🤢","😡","🤬","👎",";"]


ALLOWED_MAX = {50, 100, 200}
ALLOWED_SORT = {"latest", "likes"}
ALLOWED_LANG = {"auto", "ko", "en", "ja", "zh"}
MIN_LEN = 3

# =============================
# Routes
# =============================
@app.get("/")
def home():
    return render_template("index.html")

@app.get("/test")
def test_api():
    return jsonify({"message": "server is working"})

@app.get("/routes")
def routes():
    return jsonify(sorted([str(r) for r in app.url_map.iter_rules()]))

# =============================
# Utils
# =============================

def tokenize(text: str, lang: str):
    if lang in ["ko", "en"]:
        return text.split()
    # 일본어/중국어는 공백 기준 + 글자 단위 fallback
    return list(text)


def bad_request(msg: str):
    return jsonify({"ok": False, "error": {"code": "BAD_REQUEST", "message": msg}}), 400

def extract_video_id(url: str):
    if not url:
        return None
    m = re.search(r"[?&]v=([A-Za-z0-9_-]{11})", url)
    if m: return m.group(1)
    m = re.search(r"youtu\.be/([A-Za-z0-9_-]{11})", url)
    if m: return m.group(1)
    m = re.search(r"shorts/([A-Za-z0-9_-]{11})", url)
    if m: return m.group(1)
    m = re.search(r"embed/([A-Za-z0-9_-]{11})", url)
    if m: return m.group(1)
    return None

RE_KO = re.compile(r"[가-힣]")
RE_JA = re.compile(r"[\u3040-\u309F\u30A0-\u30FF]")
RE_ZH = re.compile(r"[\u4E00-\u9FFF]")
RE_EN = re.compile(r"[A-Za-z]")
LAUGH_TOKENS = [ "ㅋㅋㅋ", "ㅎㅎ", "ㅎㅎㅎ", "lol", "lmao", "www"]


def detect_lang_auto(text: str) -> str:
    if not text:
        return "en"
    if RE_KO.search(text): return "ko"
    if RE_JA.search(text): return "ja"
    zh_hits = len(RE_ZH.findall(text))
    en_hits = len(RE_EN.findall(text))
    if zh_hits >= 2 and en_hits == 0: return "zh"
    if en_hits > 0: return "en"
    return "en"

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

def score_keywords(cleaned: str, keywords: list) -> int:
    return sum(1 for kw in keywords if kw and kw in cleaned)

def match_keywords(cleaned: str, keywords: list, lang: str):
    tokens = tokenize(cleaned, lang)
    matched = []

    for kw in keywords:
        if len(kw) < 2:   # 🔥 한 글자 키워드 차단
            continue

        if lang in ["ko", "en"]:
            if kw in tokens:
                matched.append(kw)
        else:
            # 일본어/중국어는 substring 허용 but 길이 2 이상만
            if kw in cleaned:
                matched.append(kw)
    if lang == "ko":
        # 토큰 안에 키워드 포함 허용 (단, kw 길이 2 이상은 이미 필터됨)
        if any(kw in tok for tok in tokens):
            matched.append(kw)
    elif lang == "en":
        if kw in tokens:
            matched.append(kw)

    return matched

def classify_sentiment(text: str, lang_choice: str):
    lang = detect_lang_auto(text) if lang_choice == "auto" else lang_choice
    cleaned = preprocess(text, lang)

    if len(cleaned) < MIN_LEN:
        return "neutral", lang, [], []

    pos_list, neg_list = KEYWORDS.get(lang, KEYWORDS["en"])

    pos_matched = match_keywords(cleaned, pos_list, lang)
    neg_matched = match_keywords(cleaned, neg_list, lang)

    pos = len(pos_matched)
    neg = len(neg_matched) *3

    # 이모지 보정
    for e in POSITIVE_EMOJIS:
        if e in text:
            pos += 1
            pos_matched.append(e)

    for e in NEGATIVE_EMOJIS:
        if e in text:
            neg += 1
            neg_matched.append(e)

        # 웃음 보정 (한 번만)
    if any(l in text.lower() for l in LAUGH_TOKENS):
        pos += 1
        pos_matched.append("laugh")

    # threshold
    # ✅ 한쪽만 점수가 있으면 그쪽으로
    if pos > 0 and neg == 0:
        return "positive", lang, pos_matched, neg_matched
    if neg > 0 and pos == 0:
        return "negative", lang, pos_matched, neg_matched

    # ✅ 둘 다 있을 때만 애매하면 neutral
    if abs(pos - neg) <= 1:
        return "neutral", lang, pos_matched, neg_matched

    return "neutral", lang, pos_matched, neg_matched

def build_summary(ratios: dict) -> str:
    p = ratios.get("positive", 0.0)
    n = ratios.get("negative", 0.0)
    u = ratios.get("neutral", 0.0)
    top = max(p, n, u)
    close = sum(1 for x in (p, n, u) if abs(top - x) <= 0.10)
    if close >= 2: return "반응이 엇갈리는 영상입니다."
    if top == p: return "전반적으로 반응이 좋은 영상입니다."
    if top == n: return "부정적인 반응이 많은 영상입니다."
    return "중립적인 반응이 많은 영상입니다."

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

        r = requests.get(
            "https://www.googleapis.com/youtube/v3/commentThreads",
            params=params,
            timeout=15
        )

        print("DEBUG STATUS:", r.status_code)

        if r.status_code != 200:
            print("DEBUG RESPONSE:", r.text)
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
# API
# =============================

@app.post("/api/analyze")


def api_analyze():
    print("DEBUG KEY:", YOUTUBE_API_KEY)

    try:
        data = request.get_json(force=True) or {}

        url = (data.get("url") or "").strip()
        max_comments = data.get("maxComments")
        sort = data.get("sort", "latest")
        lang = data.get("lang", "auto")
        random_sample = bool(data.get("randomSample", False))

        if not url:
            return bad_request("url is required")
        try:
            max_comments = int(max_comments)
        except:
            return bad_request("maxComments must be number")

        if max_comments not in ALLOWED_MAX:
            return bad_request("maxComments must be one of 50, 100, 200")
        if sort not in ALLOWED_SORT:
            return bad_request('sort must be "latest" or "likes"')
        if lang not in ALLOWED_LANG:
            return bad_request('lang must be "auto"|"ko"|"en"|"ja"|"zh"')

        video_id = extract_video_id(url)
        if not video_id:
            return bad_request("Could not extract videoId from url")
        print("DEBUG video_id:", video_id)

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
            sent, detected_lang, pos_m, neg_m = classify_sentiment(text, lang)

            stats[sent] += 1
            labeled.append({
                "text": text,
                "sentiment": sent,
                "lang": detected_lang,
                "likeCount": c.get("likeCount", 0),
                "publishedAt": c.get("publishedAt", ""),
                "author": c.get("author", ""),
                "reason": {
                    "positive": pos_m,
                    "negative": neg_m
                }
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
        import traceback
        traceback.print_exc()  # ✅ 터미널에 빨간 traceback 출력
        return jsonify({
            "ok": False,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }), 500

@app.post("/api/suggest")
def api_suggest():
    try:
        data = request.get_json(force=True) or {}

        text = (data.get("text") or "").strip()
        label = data.get("label")

        if not text:
            return bad_request("text is required")

        if label not in {"positive", "negative", "neutral"}:
            return bad_request("label must be positive/negative/neutral")

        suggestion = {
            "text": text,
            "label": label,
            "status": "pending",   # 항상 검토 대기
            "createdAt": datetime.utcnow().isoformat()
        }

        with open("suggestions.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(suggestion, ensure_ascii=False) + "\n")

        return jsonify({"ok": True, "message": "Suggestion saved (pending review)"})

    except Exception as e:
        return jsonify({
            "ok": False,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }), 500


if __name__ == "__main__":
    app.run(debug=True)


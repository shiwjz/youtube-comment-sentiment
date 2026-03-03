# YouTube Comment Sentiment Analyzer

> Two developers built this web + big data project to analyze YouTube comments.
> It collects comments using the YouTube Data API and classifies them into positive, neutral, or negative.
> The system also provides explainable results by showing matched keywords, emojis, and laugh tokens.


## 🔗 Demo
 로컬 실행 후 `http://127.0.0.1:5000`

## 🖼️ Screenshots
| Home | Result |
|---|---|
| <img width="3360" height="2100" alt="image" src="https://github.com/user-attachments/assets/765f6148-154c-47e1-867e-363c56d8d2ca" /> | <img width="1592" height="1472" alt="image" src="https://github.com/user-attachments/assets/bb264cb8-b410-40db-94f0-c6d0e8e6c215" /> |

---

## Features

- Comment collection options:
  - maxComments: 50 / 100 / 200
  - sort: latest / likes
  - lang: auto / ko / en / ja / zh
  - randomSample: shuffle results

- Rule-based multi-language sentiment analysis
  - Automatic language detection
  - Keyword-based classification
  - Emoji and laugh token correction (counted once per comment)

- Explainable AI output
  - Shows why each comment is classified as positive or negative

- UI Features
  - Filter (All / Positive / Neutral / Negative)
  - Color badges
  - Incremental loading (20 comments at a time)

---

## 🧱 Architecture

Frontend (HTML, CSS, JavaScript)
        ↓
Flask Backend API
        ↓
YouTube Data API v3

---

## 🧭 Milestones (M1 → M5)

M1 - Basic Flask server and comment fetching  
M2 - UI rendering and summary  
M3 - Rule-based sentiment classification  
M4 - API options (sort, lang, randomSample)  
M5 - Explainable reasoning + keyword suggestion system  

---

## ⚙️ Setup & Run (Local)
### 1) Requirements
- Python 3.10+
- YouTube Data API v3 Key

### 2) Install
```bash
python -m venv .venv
source .venv/bin/activate   # windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3) .env
프로젝트 루트에 .env 생성:
```
YOUTUBE_API_KEY=YOUR_KEY_HERE
```

### 4) Run
```
python app.py
```
접속: http://127.0.0.1:5000

## API Spec
### POST /api/analyze
Request:
```Json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "maxComments": 100,
  "sort": "latest",
  "lang": "auto",
  "randomSample": false
}
```

Response (example):
```Json
{
  "ok": true,
  "counts": { "totalFetched": 100 },
  "sentiment": { "positive": 40, "neutral": 45, "negative": 15 },
  "summary": "...",
  "comments": [
    {
      "text": "...",
      "sentiment": "positive",
      "reason": { "positive": ["재밌", "😂"], "negative": [] }
    }
  ]
}
```

### POST /api/suggest (optional)

Request:
```
{ "text": "존나 재밌다", "label": "positive" }
```

### Project Structure
```
.
├── app.py
├── templates/
│   └── index.html
├── static/
│   ├── script.js
│   └── style.css
└── suggestions.jsonl   (optional)
```

### Team & Roles
- Frontend: (Kim Ye Min) — UI/UX, 필터/렌더링, API 연동

= Backend: (Sung Jeoung Heon) — 댓글 수집, 감정 룰, API 설계

### Retrospective
- It was my first web and big data project, so I was able to explore the direction of the project together, and the two of us were able to learn about work collaboration
- While writing codes with HTml, js, and css, I was able to think about the parts that I couldn't learn in class by myself and learn about Python

const urlInput = document.getElementById("url");
const maxSelect = document.getElementById("maxComments");
const analyzeBtn = document.getElementById("analyzeBtn");

const loadingEl = document.getElementById("loading");
const errorEl = document.getElementById("error");
const resultEl = document.getElementById("result");
const summaryEl = document.getElementById("summary");
const commentListEl = document.getElementById("commentList");

const sentimentBox = document.getElementById("sentimentBox");
const summaryTextEl = document.getElementById("summaryText");

const posCountEl = document.getElementById("posCount");
const neuCountEl = document.getElementById("neuCount");
const negCountEl = document.getElementById("negCount");

const posBarEl = document.getElementById("posBar");
const neuBarEl = document.getElementById("neuBar");
const negBarEl = document.getElementById("negBar");

const posPctEl = document.getElementById("posPct");
const neuPctEl = document.getElementById("neuPct");
const negPctEl = document.getElementById("negPct");

const moreBtn = document.getElementById("moreBtn");
let allComments = [];
let shownCount = 20;

const sortSelect = document.getElementById("sort");

function setLoading(isLoading) {
  loadingEl.classList.toggle("hidden", !isLoading);
  analyzeBtn.disabled = isLoading;
}

function showError(msg) {
  errorEl.textContent = msg || "";
}

function escapeHtml(str = "") {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
function renderSummary(data) {
  const commentsLen = Array.isArray(data.comments) ? data.comments.length : 0;
  const total =
    data?.counts?.totalFetched ??
    data?.totalFetched ??
    commentsLen;

  const shown = Math.min(shownCount, commentsLen);
  summaryEl.textContent = `수집 완료: ${total}개 댓글 (미리보기 ${shown}개)`;
}

function renderComments(data) {
  commentListEl.innerHTML = "";

  allComments = Array.isArray(data.comments) ? data.comments : [];

  const sort = sortSelect?.value || "latest";

  allComments.sort((a, b) => {
    if (sort === "likes") {
      return Number(b.likeCount ?? 0) - Number(a.likeCount ?? 0);
    }
    // latest
    return String(b.publishedAt || "").localeCompare(String(a.publishedAt || ""));
  });


  if (allComments.length === 0) {
    commentListEl.innerHTML = `<li>댓글이 없거나 가져오지 못했어.</li>`;
    moreBtn.classList.add("hidden");
    return;
  }

  const preview = allComments.slice(0, shownCount);

  for (const c of preview) {
    const li = document.createElement("li");
    li.className = "comment-item";
    li.innerHTML = `
      <div class="comment-text">${escapeHtml(c.text || "")}</div>
      <div class="comment-meta">
        <span>${escapeHtml(c.author || "익명")}</span>
        <span>👍 ${Number(c.likeCount ?? 0)}</span>
        <span>${escapeHtml((c.publishedAt || "").slice(0, 10))}</span>
      </div>
    `;
    commentListEl.appendChild(li);
  }

  // 더보기 버튼 표시 여부
  if (shownCount < allComments.length) {
    moreBtn.classList.remove("hidden");
    moreBtn.textContent = `댓글 더보기 (${Math.min(shownCount + 20, allComments.length)}/${allComments.length})`;
  } else {
    moreBtn.classList.add("hidden");
  }
}



analyzeBtn.addEventListener("click", async () => {
  showError("");
  resultEl.textContent = "요청 중...";

  const url = urlInput.value.trim();
  const maxComments = Number(maxSelect.value);

  if (!url) {
    showError("유튜브 링크를 입력해줘!");
    resultEl.textContent = "입력값 없음";
    return;
  }

  try {
    setLoading(true);

    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, maxComments }),
    });

    // 에러 응답도 JSON으로 온다고 가정
    const data = await res.json();

    if (!res.ok) {
      showError(data.error || "서버 오류가 발생했어.");
      resultEl.textContent = JSON.stringify(data, null, 2);
      return;
    }

    if (data.ok === false) {
  showError(data.error || "요청은 됐는데 처리 실패했어.");
  resultEl.textContent = JSON.stringify(data, null, 2);
  return;
}


    // 성공 시 결과 출력 (M1은 텍스트로 OK)
   // M2: 요약 + 댓글 리스트 렌더링
shownCount = 20; 
renderSummary(data);
renderComments(data);
renderSentiment(data);


// 성공이면 result는 안 보여주거나 비우기
resultEl.textContent = "";


  } catch (err) {
    showError("요청 실패! 서버가 켜져 있는지 확인해줘.");
    resultEl.textContent = String(err);
  } finally {
    setLoading(false);
  }
});

function renderSentiment(data) {
  const s = data.sentiment;
  if (!s) {
    sentimentBox.classList.add("hidden");
    return;
  }

  const pos = Number(s.positive ?? 0);
  const neu = Number(s.neutral ?? 0);
  const neg = Number(s.negative ?? 0);
  const total = Math.max(1, pos + neu + neg);

  const posPct = Math.round((pos / total) * 100);
  const neuPct = Math.round((neu / total) * 100);
  const negPct = Math.round((neg / total) * 100);

  summaryTextEl.textContent = data.summary || "요약 문구가 없습니다.";

  posCountEl.textContent = String(pos);
  neuCountEl.textContent = String(neu);
  negCountEl.textContent = String(neg);

  posBarEl.style.width = `${posPct}%`;
  neuBarEl.style.width = `${neuPct}%`;
  negBarEl.style.width = `${negPct}%`;

  posPctEl.textContent = `${posPct}%`;
  neuPctEl.textContent = `${neuPct}%`;
  negPctEl.textContent = `${negPct}%`;

  sentimentBox.classList.remove("hidden");
}


moreBtn.addEventListener("click", () => {
  shownCount += 20;
  renderComments({ comments: allComments });
});

sortSelect.addEventListener("change", () => {
      shownCount = 20;
      renderComments({ comments: allComments });
    });


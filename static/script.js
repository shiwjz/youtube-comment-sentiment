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

const sortSelect = document.getElementById("sort");
const langSelect = document.getElementById("langSelect");
const randomCheckbox = document.getElementById("randomSample");

const suggestBtn = document.getElementById("suggestBtn");
const suggestText = document.getElementById("suggestText");
const suggestLabel = document.getElementById("suggestLabel");
const suggestMsg = document.getElementById("suggestMsg");

suggestBtn.addEventListener("click", async () => {
  const text = suggestText.value.trim();
  const label = suggestLabel.value;

  if (!text) {
    suggestMsg.textContent = "문장을 입력해줘!";
    return;
  }

  try {
    const res = await fetch("/api/suggest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, label })
    });

    const data = await res.json();

    if (!res.ok || data.ok === false) {
      suggestMsg.textContent = "저장 실패 😢";
      return;
    }

    suggestMsg.textContent = "제안이 저장되었습니다! (검토 대기)";
    suggestText.value = "";

  } catch (err) {
    suggestMsg.textContent = "서버 오류 발생";
  }
});
// ✅ 감정 필터 버튼들 (index.html에 추가해둔 것)
const filterBtns = document.querySelectorAll(".filter-btn");
let currentFilter = "all";

let allComments = [];
let shownCount = 20;



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

function sentimentLabel(sentiment) {
  if (sentiment === "positive") return "긍정";
  if (sentiment === "negative") return "부정";
  return "중립";
}

function getFilteredComments() {
  if (currentFilter === "all") return allComments;
  return allComments.filter(c => (c.sentiment || "neutral") === currentFilter);
}

function renderSummary(data) {
  const commentsLen = Array.isArray(data.comments) ? data.comments.length : 0;
  const total =
    data?.counts?.totalFetched ??
    data?.totalFetched ??
    commentsLen;

  const filteredLen = getFilteredComments().length;
  const shown = Math.min(shownCount, filteredLen);

  const filterLabel =
    currentFilter === "all" ? "전체" :
    currentFilter === "positive" ? "긍정" :
    currentFilter === "neutral" ? "중립" : "부정";

  summaryEl.textContent = `수집 완료: ${total}개 댓글 / 현재 필터: ${filterLabel} (${filteredLen}개) (미리보기 ${shown}개)`;
}

function renderComments() {


  commentListEl.innerHTML = "";

  if (!Array.isArray(allComments) || allComments.length === 0) {
    commentListEl.innerHTML = `<li>댓글이 없거나 가져오지 못했어.</li>`;
    moreBtn.classList.add("hidden");
    return;
  }

  // ✅ 서버가 준 순서 그대로 사용 (프론트 정렬 X)
  const filtered = getFilteredComments();

  if (filtered.length === 0) {
    commentListEl.innerHTML = `<li>현재 필터에 해당하는 댓글이 없어.</li>`;
    moreBtn.classList.add("hidden");
    return;
  }

  const preview = filtered.slice(0, shownCount);

  for (const c of preview) {
  const s = (c.sentiment || "neutral");

  // ✅ 근거 텍스트 만들기
  const pos = Array.isArray(c.pos) ? c.pos : [];
  const neg = Array.isArray(c.neg) ? c.neg : [];
  const posScore = Number(c.posScore ?? pos.length);
  const negScore = Number(c.negScore ?? neg.length);

  let reasonText = "판단 근거: 키워드 매칭 없음";
  if (posScore === 0 && negScore === 0) {
    reasonText = "판단 근거: 키워드 매칭 없음";
  } else if (posScore === negScore) {
    reasonText = `판단 근거: +${pos.join(", +")} / -${neg.join(", -")} (비슷해서 중립)`;
  } else if (posScore > negScore) {
    reasonText = `판단 근거: +${pos.join(", +")}`;
  } else {
    reasonText = `판단 근거: -${neg.join(", -")}`;
  }

  const li = document.createElement("li");
  li.className = "comment-item";
  li.innerHTML = `
  <div class="comment-top">
    <span class="badge ${escapeHtml(s)}">${sentimentLabel(s)}</span>
  </div>

  <div class="comment-text">${escapeHtml(c.text || "")}</div>

  ${c.reason?.positive?.length ? 
    `<div class="reason positive">
        긍정 근거: ${c.reason.positive.map(r => escapeHtml(r)).join(", ")}
     </div>` : ""}

  ${c.reason?.negative?.length ? 
    `<div class="reason negative">
        부정 근거: ${c.reason.negative.map(r => escapeHtml(r)).join(", ")}
     </div>` : ""}

  <div class="comment-meta">
    <span>${escapeHtml(c.author || "익명")}</span>
    <span>👍 ${Number(c.likeCount ?? 0)}</span>
    <span>${escapeHtml((c.publishedAt || "").slice(0, 10))}</span>
  </div>
`;

  commentListEl.appendChild(li);
}


  // 더보기 버튼 표시 여부
  if (shownCount < filtered.length) {
    moreBtn.classList.remove("hidden");
    moreBtn.textContent = `댓글 더보기 (${Math.min(shownCount + 20, filtered.length)}/${filtered.length})`;
  } else {
    moreBtn.classList.add("hidden");
  }
}

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

// ✅ 분석하기 버튼
analyzeBtn.addEventListener("click", async () => {
  showError("");
  resultEl.textContent = "요청 중...";

  const url = urlInput.value.trim();
  const maxComments = Number(maxSelect.value);

  // ✅ M4 옵션들
  const sort = sortSelect?.value || "latest";
  const lang = langSelect?.value || "auto";
  const randomSample = !!randomCheckbox?.checked;

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
      body: JSON.stringify({
        url,
        maxComments,
        sort,
        lang,
        randomSample
      }),
    });

    const data = await res.json();

    if (!res.ok) {
      const msg =
      (data?.error?.message) ||
      (typeof data?.error === "string" ? data.error : "") ||
      "서버 오류가 발생했어.";

    showError(msg);

      resultEl.textContent = JSON.stringify(data, null, 2);
      return;
    }

    if (data.ok === false) {
      showError(data.error || "요청은 됐는데 처리 실패했어.");
      resultEl.textContent = JSON.stringify(data, null, 2);
      return;
    }

    // ✅ 성공 처리
    shownCount = 20;
    allComments = Array.isArray(data.comments) ? data.comments : [];

    renderSentiment(data);
    renderSummary(data);
    renderComments();

    // 성공이면 result는 비우기
    resultEl.textContent = "";

  } catch (err) {
    showError("요청 실패! 서버가 켜져 있는지 확인해줘.");
    resultEl.textContent = String(err);
  } finally {
    setLoading(false);
  }
});

// ✅ 더보기
moreBtn.addEventListener("click", () => {
  shownCount += 20;
  renderSummary({ comments: allComments, counts: { totalFetched: allComments.length } });
  renderComments();
});

// ✅ 감정 필터 버튼 클릭
for (const btn of filterBtns) {
  btn.addEventListener("click", () => {
    const next = btn.dataset.filter || "all";
    currentFilter = next;

    for (const b of filterBtns) b.classList.remove("is-active");
    btn.classList.add("is-active");

    shownCount = 20;
    renderSummary({ comments: allComments, counts: { totalFetched: allComments.length } });
    renderComments();
  });
}

// ✅ 정렬 변경: 프론트에서 재정렬 금지!
// 정렬 바꿔도 현재 결과는 그대로(서버 결과 유지)
// -> 적용하려면 분석하기를 다시 눌러야 함
sortSelect.addEventListener("change", () => {
  shownCount = 20;
  renderSummary({ comments: allComments, counts: { totalFetched: allComments.length } });
  renderComments();
});

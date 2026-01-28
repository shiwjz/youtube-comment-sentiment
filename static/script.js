const urlInput = document.getElementById("url");
const maxSelect = document.getElementById("maxComments");
const analyzeBtn = document.getElementById("analyzeBtn");

const loadingEl = document.getElementById("loading");
const errorEl = document.getElementById("error");
const resultEl = document.getElementById("result");

function setLoading(isLoading) {
  loadingEl.classList.toggle("hidden", !isLoading);
  analyzeBtn.disabled = isLoading;
}

function showError(msg) {
  errorEl.textContent = msg || "";
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

    // 성공 시 결과 출력 (M1은 텍스트로 OK)
    resultEl.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    showError("요청 실패! 서버가 켜져 있는지 확인해줘.");
    resultEl.textContent = String(err);
  } finally {
    setLoading(false);
  }
});

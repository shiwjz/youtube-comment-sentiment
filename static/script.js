const btn = document.querySelector("#btn");
const result = document.querySelector("#result");
const errorBox = document.querySelector("#error");

btn.addEventListener("click", async () => {
  result.textContent = "";
  errorBox.textContent = "";

  const url = document.querySelector("#url").value.trim();
  const maxComments = Number(document.querySelector("#maxComments").value);

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, maxComments }),
    });

    const data = await res.json();

    if (!res.ok) {
      errorBox.textContent = JSON.stringify(data, null, 2);
      return;
    }

    // ✅ data.comments가 있을 때: 보기 좋게 프리텍스트로 출력
    if (data.comments && Array.isArray(data.comments)) {
      const lines = [];
      lines.push(`✅ 댓글 ${data.comments.length}개 가져옴\n`);

      data.comments.forEach((c, i) => {
        lines.push(
          `#${i + 1}\n` +
          `작성자: ${c.author}\n` +
          `좋아요: ${c.likeCount}\n` +
          `작성일: ${c.publishedAt}\n` +
          `내용: ${c.text}\n` +
          `------------------------------\n`
        );
      });

      result.textContent = lines.join("");
    } else {
      // 아직 M1 형태면 그냥 그대로 보여주기
      result.textContent = JSON.stringify(data, null, 2);
    }
  } catch (e) {
    errorBox.textContent = String(e);
  }
});

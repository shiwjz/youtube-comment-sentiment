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
      body: JSON.stringify({ url, maxComments })
    });

    const data = await res.json();

    if (!res.ok) {
      errorBox.textContent = JSON.stringify(data, null, 2);
      return;
    }

    result.textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    errorBox.textContent = String(e);
  }
});

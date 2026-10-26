// ФТ-05 (пароль остаётся в поле), ФТ-09 (Показать/Скрыть), ФТ-10 (генерация).
// Без JS форма работает через POST /check (поле после ответа пустое).
"use strict";

const NETWORK_ERROR = "Не удалось связаться с сервером. Повторите попытку.";

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("check-form");
  const input = document.getElementById("password");
  const toggle = document.getElementById("toggle");
  const genBtn = document.getElementById("generate");
  const genWrap = document.getElementById("gen-length-wrap");
  const genLen = document.getElementById("gen-length");
  const errorEl = document.getElementById("password-error");
  const resultEl = document.getElementById("result");
  const meter = document.getElementById("meter");
  const levelEl = document.getElementById("level");
  const scoreEl = document.getElementById("score");
  const recsEl = document.getElementById("recommendations");

  toggle.hidden = false;
  genBtn.hidden = false;
  genWrap.hidden = false;

  // ФТ-09: переключение без запроса к серверу
  toggle.addEventListener("click", () => {
    const show = input.type === "password";
    input.type = show ? "text" : "password";
    toggle.textContent = show ? "Скрыть" : "Показать";
    toggle.setAttribute("aria-pressed", String(show));
    input.focus();
  });

  function showError(text) {
    errorEl.textContent = text;
    errorEl.hidden = false;
    resultEl.hidden = true;
  }

  function showResult(data) {
    errorEl.hidden = true;
    errorEl.textContent = "";
    meter.dataset.level = data.level;
    levelEl.className = "level level-" + data.level;
    levelEl.textContent = data.level_label;
    scoreEl.textContent = "Балл: " + data.score + " из 100";
    recsEl.replaceChildren(...data.recommendations.map((r) => {
      const li = document.createElement("li");
      li.dataset.code = r.code;
      li.textContent = r.text;          // textContent — защита от XSS
      return li;
    }));
    resultEl.hidden = false;
  }

  async function postJson(url, body) {
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
    });
    return { ok: resp.ok, data: await resp.json() };
  }

  async function check() {
    try {
      const { ok, data } = await postJson("/api/v1/password/check", { password: input.value });
      if (ok) showResult(data); else showError(data.error.message);
    } catch (e) {
      showError(NETWORK_ERROR);
    }
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();             // пароль остаётся в поле (в.2 Заказчика)
    check();
  });

  genBtn.addEventListener("click", async () => {
    try {
      const { ok, data } = await postJson("/api/v1/password/generate",
                                          { length: Number(genLen.value) });
      if (!ok) { showError(data.error.message); return; }
      input.value = data.password;
      await check();
    } catch (e) {
      showError(NETWORK_ERROR);
    }
  });
});

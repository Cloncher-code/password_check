// ФТ-05 (пароль остаётся в поле), ФТ-09 (Показать/Скрыть), ФТ-10 (генерация).
// Без JS форма работает через POST /check (поле после ответа пустое).
"use strict";

const NETWORK_ERROR = "Не удалось связаться с сервером. Повторите попытку.";

// ФТ-12 (CR-02): пасхалка. Шаги — успешные проверки паролей подряд, в этом порядке.
// Фразы хранятся только как SHA-256, чтобы их не было видно в исходном коде страницы.
// Сравнение — в браузере, на сервер ничего дополнительно не отправляется (НФТ-05).
const EGG_STEPS = [
  "21797d9226a97536ceefe04ccdfecb2d6dc5fade537afc300dc9233949c747f9",
  "0ff5d83033f603e01de268d66f9755b633ba0b5ac5b385830eab9fc17b9bb042",
];
const EGG_IMAGE = "/static/easter/stop-word.jpg";
const EGG_DELAY_MS = 700;

async function sha256hex(text) {
  const bytes = new TextEncoder().encode(text.normalize("NFC"));
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest), (b) => b.toString(16).padStart(2, "0")).join("");
}

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
  const egg = document.getElementById("egg");
  const eggPic = document.getElementById("egg-pic");
  let eggStep = 0;

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

  function showEgg() {
    if (!eggPic.firstChild) {              // картинка грузится только при срабатывании
      const img = document.createElement("img");
      img.src = EGG_IMAGE;
      img.alt = "Мем про требования к паролю";
      img.width = 720;
      img.height = 764;
      eggPic.appendChild(img);
    }
    egg.showModal();
  }

  async function trackEgg(password) {
    if (!window.crypto || !crypto.subtle) { eggStep = 0; return; }  // нет HTTPS/localhost
    const hash = await sha256hex(password);
    if (hash === EGG_STEPS[eggStep]) {
      eggStep += 1;
    } else {
      eggStep = hash === EGG_STEPS[0] ? 1 : 0;
    }
    if (eggStep === EGG_STEPS.length) {
      eggStep = 0;
      setTimeout(showEgg, EGG_DELAY_MS);
    }
  }

  async function check() {
    const password = input.value;          // значение на момент нажатия
    try {
      const { ok, data } = await postJson("/api/v1/password/check", { password });
      if (ok) {
        showResult(data);
        trackEgg(password);
      } else {
        eggStep = 0;
        showError(data.error.message);
      }
    } catch (e) {
      eggStep = 0;
      showError(NETWORK_ERROR);
    }
  }

  document.getElementById("egg-close").addEventListener("click", () => egg.close());
  egg.addEventListener("click", (event) => {   // щелчок по затемнению вокруг окна
    if (event.target === egg) egg.close();
  });

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

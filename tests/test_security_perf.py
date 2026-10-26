"""Безопасность (НФТ-04…НФТ-06) и производительность (НФТ-07, БТ-08)."""
import logging
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
client = TestClient(app)
ROOT = Path(__file__).resolve().parent.parent
# Уникальные «пароли-канарейки»: не совпадают ни с одним словом в HTML и логах.
# (Первая версия теста брала Приложение А и ложно падала на «password»,
#  который есть в URL /api/v1/password/check и в name="password". См. BUG-01.)
SECRETS = [
    "Kanareyka7f3!", "Канарейка-9Жq", "Zx9!\U0001F600canary", "QwErTy-canary-42",
    "aaaCanary123", "Can4ry_" + "x" * 50, "Kc1!\u0663\u5b57marker",
]


def test_password_not_in_app_logs(caplog):
    """TC-16 · НФТ-05 — логи приложения (DEBUG) не содержат пароли."""
    caplog.set_level(logging.DEBUG)
    for pwd in SECRETS:
        client.post("/api/v1/password/check", json={"password": pwd})
        client.post("/check", data={"password": pwd})
    client.post("/api/v1/password/check", json={"password": 12345678})
    for pwd in SECRETS:
        assert pwd not in caplog.text


def test_password_not_in_responses():
    """TC-17 · НФТ-05 — ни ответ API, ни HTML формы, ни ошибка не возвращают пароль."""
    for pwd in SECRETS + ["a" * 65, "my secret"]:
        for r in (client.post("/api/v1/password/check", json={"password": pwd}),
                  client.post("/check", data={"password": pwd})):
            assert pwd not in r.text


def test_validation_error_does_not_echo_input():
    """TC-18 · НФТ-05 — стандартный 422 FastAPI отдаёт "input"; наш — нет."""
    r = client.post("/api/v1/password/check", json={"password": ["Sup3rS3cret!"]})
    assert "Sup3rS3cret!" not in r.text and "input" not in r.text


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def live_server():
    """Настоящий uvicorn с журналом уровня debug (для НФТ-05, НФТ-07)."""
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port),
         "--log-level", "debug"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
    )
    base = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            httpx.get(base + "/health", timeout=0.5)
            break
        except httpx.HTTPError:
            time.sleep(0.1)
    yield base, proc
    proc.terminate()


def test_password_not_in_uvicorn_log(live_server):
    """TC-19 · НФТ-05 — журнал uvicorn (debug) не содержит пароли."""
    base, proc = live_server
    with httpx.Client(base_url=base) as c:
        for pwd in SECRETS:
            c.post("/api/v1/password/check", json={"password": pwd})
            c.post("/check", data={"password": pwd})
    proc.terminate()
    log_text = proc.communicate(timeout=10)[0]
    assert "POST /api/v1/password/check" in log_text  # журнал действительно пишется
    for pwd in SECRETS:
        assert pwd not in log_text


def test_api_latency_nft07():
    """TC-20 · НФТ-07 — 100 запросов по 64 символа: ≥95 из 100 ≤ 200 мс."""
    pwd = "Aa1!" * 16
    times = []
    for _ in range(100):
        t0 = time.perf_counter()
        r = client.post("/api/v1/password/check", json={"password": pwd})
        times.append(time.perf_counter() - t0)
        assert r.status_code == 200
    assert sum(t <= 0.2 for t in times) >= 95


def test_form_latency_bt08():
    """TC-21 · БТ-08 — 20 проверок через форму подряд, каждая ≤ 1 с (серверная часть)."""
    for _ in range(20):
        t0 = time.perf_counter()
        client.post("/check", data={"password": "Пароль2024!"})
        assert time.perf_counter() - t0 <= 1.0

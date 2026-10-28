"""Интеграционные тесты: ФТ-01, ФТ-02, ФТ-05…ФТ-10, СТ §6, §7."""
import re

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.reference_set import LEVEL_LABELS, REFERENCE

client = TestClient(app)
API = "/api/v1/password/check"
GEN = "/api/v1/password/generate"


# ---------------------------------------------------------------- ФТ-08
def test_health():
    """TC-01 · ФТ-08."""
    r = client.get("/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


# ---------------------------------------------------------------- ФТ-01, §7
def test_index_form():
    """TC-02 · ФТ-01, НФТ-04 — форма POST, поле type=password, autocomplete=off."""
    r = client.get("/")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/html")
    html = r.text
    assert 'method="post"' in html and 'action="/check"' in html
    assert re.search(r'<input id="password"[^>]*type="password"', html)
    assert 'autocomplete="off"' in html
    assert "Проверить" in html and "Показать" in html and "Сгенерировать" in html
    assert "maxlength" not in html  # см. QC СТ: maxlength считает UTF-16


def test_repo_link_in_footer():
    """TC-32 · ФТ-11 — ссылка на репозиторий в подвале, открывается безопасно."""
    from app import config
    html = client.get("/").text
    assert re.search(r'<footer class="footer">\s*<a href="' + re.escape(config.REPO_URL)
                     + r'" target="_blank" rel="noopener noreferrer">', html)
    html = client.post("/check", data={"password": "Qwerty789!"}).text
    assert config.REPO_URL in html   # подвал есть и на странице результата


# ---------------------------------------------------------------- ФТ-06, §6.2
def test_api_contract_example():
    """TC-03 · ФТ-06 — пример ответа из §6.2 один в один."""
    r = client.post(API, json={"password": "Qwerty789!"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/json"
    assert r.json() == {
        "score": 75, "level": "STRONG", "level_label": "Надёжный", "length": 10,
        "blacklisted": False,
        "checks": [
            {"code": "C1", "passed": True, "points": 25},
            {"code": "C2", "passed": False, "points": 0},
            {"code": "C3", "passed": True, "points": 15},
            {"code": "C4", "passed": True, "points": 15},
            {"code": "C5", "passed": True, "points": 15},
            {"code": "C6", "passed": True, "points": 15},
        ],
        "penalties": [
            {"code": "P1", "applied": False, "points": 0},
            {"code": "P2", "applied": True, "points": -10},
        ],
        "recommendations": [
            {"code": "R-C2", "text": "Для большей надёжности используйте 12 символов и более."},
            {"code": "R-P2", "text": "Не используйте последовательности вида abc или 123."},
        ],
    }


# ---------------------------------------------------------------- ФТ-02, §6.3
@pytest.mark.parametrize("body,code", [
    ({"password": ""}, "EMPTY_PASSWORD"),
    ({"password": "a" * 65}, "PASSWORD_TOO_LONG"),
    ({"password": "a b"}, "PASSWORD_HAS_WHITESPACE"),
    ({}, "INVALID_REQUEST"),
    ({"password": 123}, "INVALID_REQUEST"),
    ({"password": None}, "INVALID_REQUEST"),
    ({"password": ["x"]}, "INVALID_REQUEST"),
    ([], "INVALID_REQUEST"),
])
def test_api_errors(body, code):
    """TC-04 · ФТ-02, §6.3 — 422 и формат {"error": {...}}."""
    r = client.post(API, json=body)
    assert r.status_code == 422
    assert list(r.json()) == ["error"] and r.json()["error"]["code"] == code


def test_api_not_json():
    """TC-05 · §6.3 — тело не JSON -> INVALID_REQUEST."""
    r = client.post(API, content=b"password=abc",
                    headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "INVALID_REQUEST"


def test_api_extra_fields_ignored():
    """TC-06 · §6.2 — лишние поля игнорируются."""
    r = client.post(API, json={"password": "Qwerty789!", "user": "x"})
    assert r.status_code == 200 and r.json()["score"] == 75


def test_api_get_not_allowed():
    """TC-07 · НФТ-04 — пароль нельзя передать GET-запросом."""
    assert client.get(API, params={"password": "abc"}).status_code == 405


# ---------------------------------------------------------------- ФТ-05
def test_form_result_without_password():
    """TC-08 · ФТ-05, НФТ-05 — результат формы есть, пароля в HTML нет."""
    pwd = "Qwerty789!"
    r = client.post("/check", data={"password": pwd})
    assert r.status_code == 200
    assert "Балл: 75 из 100" in r.text and "Надёжный" in r.text
    assert pwd not in r.text


@pytest.mark.parametrize("data,text", [
    ({"password": ""}, "Введите пароль."),
    ({}, "Введите пароль."),
    ({"password": "a" * 65}, "Пароль не должен превышать 64 символов."),
    ({"password": "a b"}, "Пароль не должен содержать пробелы."),
])
def test_form_errors(data, text):
    """TC-09 · ФТ-02, НФТ-08 — ошибка под полем, HTTP 200, результата нет."""
    r = client.post("/check", data=data)
    assert r.status_code == 200 and text in r.text
    assert re.search(r'<section id="result"[^>]*hidden', r.text)


# ---------------------------------------------------------------- ФТ-07
@pytest.mark.parametrize("row", [r for r in REFERENCE if r[3][0] != "ERR"],
                         ids=lambda r: f"A{r[0]:02d}")
def test_form_equals_api(row):
    """TC-10 · ФТ-07 — форма и API дают одинаковые балл, уровень, рекомендации."""
    _, pwd, _, _ = row
    api = client.post(API, json={"password": pwd}).json()
    html = client.post("/check", data={"password": pwd}).text
    assert f"Балл: {api['score']} из 100" in html
    assert f'class="level level-{api["level"]}">{LEVEL_LABELS[api["level"]]}<' in html
    form_codes = re.findall(r'<li data-code="([^"]+)">', html)
    assert form_codes == [x["code"] for x in api["recommendations"]]


# ---------------------------------------------------------------- ФТ-10
def test_generate_default():
    """TC-11 · ФТ-10 — без тела: 16 символов, 100 баллов."""
    r = client.post(GEN)
    assert r.status_code == 200 and r.json()["length"] == 16
    check = client.post(API, json={"password": r.json()["password"]}).json()
    assert check["score"] == 100


@pytest.mark.parametrize("body,status,code", [
    ({"length": 12}, 200, None), ({"length": 64}, 200, None),
    ({"length": 11}, 422, "INVALID_LENGTH"), ({"length": 65}, 422, "INVALID_LENGTH"),
    ({"length": "16"}, 422, "INVALID_REQUEST"), ({"length": 16.5}, 422, "INVALID_REQUEST"),
])
def test_generate_length(body, status, code):
    """TC-12 · ФТ-10 — границы длины генерации."""
    r = client.post(GEN, json=body)
    assert r.status_code == status
    if code:
        assert r.json()["error"]["code"] == code
    else:
        assert len(r.json()["password"]) == body["length"]


# ---------------------------------------------------------------- НФТ-06
@pytest.mark.parametrize("method,url,kw", [
    ("post", API, {"json": {"password": "abc"}}),
    ("post", API, {"json": {"password": ""}}),
    ("post", "/check", {"data": {"password": "abc"}}),
    ("post", GEN, {}),
    ("get", "/", {}),
])
def test_no_store_header(method, url, kw):
    """TC-13 · НФТ-06 — Cache-Control: no-store, включая ответы с ошибкой."""
    r = getattr(client, method)(url, **kw)
    assert r.headers["cache-control"] == "no-store"


def test_csp_on_pages():
    """TC-14 · НФТ-05 — CSP запрещает внешние скрипты на странице."""
    assert client.get("/").headers["content-security-policy"] == "default-src 'self'"


def test_static_assets():
    """TC-15 · §7 — CSS и JS отдаются."""
    assert client.get("/static/style.css").status_code == 200
    assert client.get("/static/app.js").status_code == 200

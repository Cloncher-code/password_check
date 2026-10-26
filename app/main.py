"""Веб-приложение «Проверка сложности пароля».

Роуты: ФТ-01, ФТ-05, ФТ-06, ФТ-08, ФТ-10. Ошибки: ФТ-02, СТ §6.3.
Безопасность: НФТ-04, НФТ-05, НФТ-06.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from fastapi import Body, FastAPI, Form, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import config
from app.generator import generate
from app.schemas import (CheckRequest, CheckResponse, ErrorResponse,
                         GenerateRequest, GenerateResponse)
from app.scoring import ValidationError, evaluate

__version__ = "1.0.0"

BASE_DIR = Path(__file__).resolve().parent.parent
log = logging.getLogger("password_checker")

app = FastAPI(
    title="Проверка сложности пароля",
    version=__version__,
    description="API оценки надёжности и генерации паролей. Контракт — СТ §6.",
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

ERROR_RESPONSES = {422: {"model": ErrorResponse, "description": "Ошибка входных данных"}}


# ------------------------------------------------------------ заголовки НФТ-06
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    if not request.url.path.startswith("/static"):
        response.headers["Cache-Control"] = "no-store"          # НФТ-06
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    if request.url.path in ("/", "/check"):
        response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


# ------------------------------------------------------------ ошибки §6.3
def error_json(code: str) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"error": {"code": code, "message": config.ERRORS[code]}},
    )


@app.exception_handler(RequestValidationError)
async def on_request_validation_error(request: Request, exc: RequestValidationError):
    # Заменяет стандартный ответ FastAPI: тот возвращает поле "input",
    # то есть сам пароль (нарушение НФТ-05). Детали ошибки не логируем.
    return error_json("INVALID_REQUEST")


@app.exception_handler(ValidationError)
async def on_validation_error(request: Request, exc: ValidationError):
    return error_json(exc.code)


# ------------------------------------------------------------ веб-форма
def render(request: Request, result=None, error=None):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "result": result,
            "error": error,
            "max_length": config.MAX_LENGTH,
            "gen_min": config.GEN_MIN_LENGTH,
            "gen_max": config.GEN_MAX_LENGTH,
            "gen_default": config.GEN_DEFAULT_LENGTH,
        },
    )


@app.get("/", response_class=HTMLResponse, summary="Форма проверки (ФТ-01)")
async def index(request: Request):
    return render(request)


@app.post("/check", response_class=HTMLResponse,
          summary="Проверка из формы без JS (ФТ-05)")
async def check_form(request: Request, password: Optional[str] = Form(default="")):
    try:
        result = evaluate(password or "")
    except ValidationError as exc:
        return render(request, error=exc.message)   # HTTP 200, текст под полем
    log.info("check: level=%s", result.level)        # без пароля (НФТ-05)
    return render(request, result=result.to_dict())


# ------------------------------------------------------------ API
@app.post("/api/v1/password/check", response_model=CheckResponse,
          responses=ERROR_RESPONSES, summary="Оценка пароля (ФТ-06)")
async def check_api(body: CheckRequest):
    result = evaluate(body.password)
    log.info("api check: level=%s", result.level)
    return result.to_dict()


@app.post("/api/v1/password/generate", response_model=GenerateResponse,
          responses=ERROR_RESPONSES, summary="Генерация пароля (ФТ-10)")
async def generate_api(body: Optional[GenerateRequest] = Body(default=None)):
    length = body.length if body else config.GEN_DEFAULT_LENGTH
    pwd = generate(length)
    log.info("generate: length=%s", length)
    return {"password": pwd, "length": len(pwd)}


@app.get("/health", summary="Проверка работоспособности (ФТ-08)")
async def health():
    return {"status": "ok"}

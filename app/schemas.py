"""Pydantic-модели контракта API (ФТ-06, ФТ-10, СТ §6)."""
from __future__ import annotations

from pydantic import BaseModel, StrictInt, StrictStr

from app import config


class CheckRequest(BaseModel):
    """Тело POST /api/v1/password/check. Строка строго (123 → INVALID_REQUEST)."""
    password: StrictStr

    model_config = {"json_schema_extra": {"examples": [{"password": "Qwerty789!"}]}}


class CheckItem(BaseModel):
    code: str
    passed: bool
    points: int


class PenaltyItem(BaseModel):
    code: str
    applied: bool
    points: int


class RecommendationItem(BaseModel):
    code: str
    text: str


class CheckResponse(BaseModel):
    score: int
    level: str
    level_label: str
    length: int
    blacklisted: bool
    checks: list[CheckItem]
    penalties: list[PenaltyItem]
    recommendations: list[RecommendationItem]


class GenerateRequest(BaseModel):
    """Тело POST /api/v1/password/generate. Тело можно не передавать."""
    length: StrictInt = config.GEN_DEFAULT_LENGTH


class GenerateResponse(BaseModel):
    password: str
    length: int


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody

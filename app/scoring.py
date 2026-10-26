"""Модуль оценки пароля. Чистые функции, не зависит от FastAPI (НФТ-10).

Требования: ФТ-02, ФТ-03, ФТ-04, БП-01…БП-09. Алгоритм — СТ §5.
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field

from app import config


class ValidationError(Exception):
    """Ошибка валидации входа (ФТ-02, СТ §6.3)."""

    def __init__(self, code: str):
        self.code = code
        self.message = config.ERRORS[code]
        super().__init__(code)


@dataclass(frozen=True)
class Check:
    code: str
    passed: bool
    points: int


@dataclass(frozen=True)
class Penalty:
    code: str
    applied: bool
    points: int


@dataclass(frozen=True)
class Recommendation:
    code: str
    text: str


@dataclass(frozen=True)
class Result:
    score: int
    level: str
    level_label: str
    length: int
    blacklisted: bool
    checks: list[Check] = field(default_factory=list)
    penalties: list[Penalty] = field(default_factory=list)
    recommendations: list[Recommendation] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "level": self.level,
            "level_label": self.level_label,
            "length": self.length,
            "blacklisted": self.blacklisted,
            "checks": [c.__dict__ for c in self.checks],
            "penalties": [p.__dict__ for p in self.penalties],
            "recommendations": [r.__dict__ for r in self.recommendations],
        }


# ---------------------------------------------------------------- шаг 1
def normalize(password: str) -> str:
    """БП-02: NFC-нормализация до подсчёта длины и классов (é = e + ◌́ → é)."""
    return unicodedata.normalize(config.UNICODE_NORMALIZATION, password)


def validate(password: str) -> str:
    """ФТ-02, БП-09. Порядок проверок: пусто → длина → пробельные символы.

    Возвращает нормализованный пароль или бросает ValidationError.
    """
    pwd = normalize(password)
    if len(pwd) < config.MIN_LENGTH_INPUT:
        raise ValidationError("EMPTY_PASSWORD")
    if len(pwd) > config.MAX_LENGTH:
        raise ValidationError("PASSWORD_TOO_LONG")
    if any(ch.isspace() for ch in pwd):
        raise ValidationError("PASSWORD_HAS_WHITESPACE")
    return pwd


# ---------------------------------------------------------------- классы (БП-02)
def is_lower(ch: str) -> bool:
    return unicodedata.category(ch) == "Ll"


def is_upper(ch: str) -> bool:
    return unicodedata.category(ch) == "Lu"


def is_letter(ch: str) -> bool:
    return unicodedata.category(ch).startswith("L")


def is_digit(ch: str) -> bool:
    return "0" <= ch <= "9"


def is_special(ch: str) -> bool:
    """Спецсимвол — не буква (категория L*) и не ASCII-цифра."""
    return not is_letter(ch) and not is_digit(ch)


# ---------------------------------------------------------------- штрафы (БП-03)
def has_repeat(pwd: str) -> bool:
    """P1: 3+ одинаковых символа подряд, с учётом регистра."""
    n = config.REPEAT_RUN
    return any(len(set(pwd[i:i + n])) == 1 for i in range(len(pwd) - n + 1))


def _seq_value(ch: str) -> tuple[str, int] | None:
    if is_digit(ch):
        return ("d", ord(ch))
    if ch.isascii() and ch.isalpha():
        return ("l", ord(ch.lower()))
    return None


def has_sequence(pwd: str) -> bool:
    """P2: 3 символа подряд — только латиница (без учёта регистра) или только
    цифры, шаг +1 или −1, без перехода 9→0 и z→a."""
    n = config.SEQUENCE_RUN
    for i in range(len(pwd) - n + 1):
        vals = [_seq_value(c) for c in pwd[i:i + n]]
        if any(v is None for v in vals):
            continue
        if len({v[0] for v in vals}) != 1:
            continue
        diffs = {vals[j + 1][1] - vals[j][1] for j in range(n - 1)}
        if diffs == {1} or diffs == {-1}:
            return True
    return False


# ---------------------------------------------------------------- уровни (БП-07)
def level_for(score: int) -> tuple[str, str]:
    for min_score, code, label in config.LEVELS:
        if score >= min_score:
            return code, label
    raise AssertionError("score < 0")  # недостижимо из-за БП-05


# ---------------------------------------------------------------- алгоритм §5
def evaluate(password: str) -> Result:
    """ФТ-03, ФТ-04. Шаги 1–8 алгоритма СТ §5."""
    pwd = validate(password)                                   # шаг 1
    length = len(pwd)

    passed = {                                                 # шаг 2
        "C1": length >= config.MIN_GOOD_LENGTH,
        "C2": length >= config.RECOMMENDED_LENGTH,
        "C3": any(is_lower(c) for c in pwd),
        "C4": any(is_upper(c) for c in pwd),
        "C5": any(is_digit(c) for c in pwd),
        "C6": any(is_special(c) for c in pwd),
    }
    applied = {"P1": has_repeat(pwd), "P2": has_sequence(pwd)}
    checks = [
        Check(code, passed[code], config.CRITERIA_POINTS[code] if passed[code] else 0)
        for code in config.CRITERIA_POINTS
    ]
    penalties = [
        Penalty(code, applied[code], -config.PENALTY_POINTS[code] if applied[code] else 0)
        for code in config.PENALTY_POINTS
    ]

    if pwd.lower() in config.BLACKLIST:                        # шаг 3
        code, label = level_for(0)
        return Result(0, code, label, length, True, checks, penalties,
                      [Recommendation("R-O1", config.RECOMMENDATIONS["R-O1"])])

    score = sum(c.points for c in checks) + sum(p.points for p in penalties)  # шаг 4
    score = max(0, score)                                      # шаг 5 (БП-05)
    if length < config.MIN_GOOD_LENGTH:                        # шаг 6 (БП-06)
        score = min(score, config.SHORT_PASSWORD_CAP)
    code, label = level_for(score)                             # шаг 7

    rec_codes = []                                             # шаг 8 (БП-08)
    for c in checks:
        if c.passed:
            continue
        if c.code == "C2" and not passed["C1"]:
            continue
        rec_codes.append("R-" + c.code)
    rec_codes += ["R-" + p.code for p in penalties if p.applied]
    if not rec_codes:
        rec_codes = ["R-OK"]
    recs = [Recommendation(rc, config.RECOMMENDATIONS[rc]) for rc in rec_codes]

    return Result(score, code, label, length, False, checks, penalties, recs)

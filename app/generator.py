"""Генерация пароля (ФТ-10, БП-10). Чистая функция, без FastAPI.

Криптостойкий источник случайности — модуль `secrets` (НФТ-11).
Результат всегда получает 100 баллов по `evaluate` (проверяется в цикле).
"""
from __future__ import annotations

import secrets

from app import config
from app.scoring import ValidationError, evaluate

_ALL = config.GEN_LOWER + config.GEN_UPPER + config.GEN_DIGITS + config.GEN_SPECIAL
_rng = secrets.SystemRandom()


def _candidate(length: int) -> str:
    chars = [
        secrets.choice(config.GEN_LOWER),
        secrets.choice(config.GEN_UPPER),
        secrets.choice(config.GEN_DIGITS),
        secrets.choice(config.GEN_SPECIAL),
    ]
    chars += [secrets.choice(_ALL) for _ in range(length - len(chars))]
    _rng.shuffle(chars)
    return "".join(chars)


def generate(length: int = config.GEN_DEFAULT_LENGTH) -> str:
    """Вернуть пароль заданной длины со 100 баллами.

    Бросает ValidationError("INVALID_LENGTH"), если длина вне 12–64.
    """
    if (not isinstance(length, int) or isinstance(length, bool)
            or not config.GEN_MIN_LENGTH <= length <= config.GEN_MAX_LENGTH):
        raise ValidationError("INVALID_LENGTH")
    for _ in range(config.GEN_MAX_ATTEMPTS):
        pwd = _candidate(length)
        if evaluate(pwd).score == 100:
            return pwd
    raise RuntimeError("Не удалось сгенерировать пароль")  # вероятность ~0

"""Тесты генерации: ФТ-10, БП-10, НФТ-11."""
import pytest

from app import config
from app.generator import generate
from app.scoring import ValidationError, evaluate

ALLOWED = set(config.GEN_LOWER + config.GEN_UPPER + config.GEN_DIGITS + config.GEN_SPECIAL)


def test_generated_passwords_score_100():
    """БП-10 — 1000 сгенерированных паролей: все 100 баллов, все уникальны."""
    batch = [generate() for _ in range(1000)]
    assert len(set(batch)) == 1000
    for pwd in batch:
        r = evaluate(pwd)
        assert r.score == 100 and r.level == "VERY_STRONG"
        assert set(pwd) <= ALLOWED
        assert len(pwd) == config.GEN_DEFAULT_LENGTH


@pytest.mark.parametrize("length", [12, 13, 40, 64])
def test_generated_length(length):
    """ФТ-10 — длина в пределах 12–64 соблюдается."""
    pwd = generate(length)
    assert len(pwd) == length and evaluate(pwd).score == 100


@pytest.mark.parametrize("length", [11, 65, 0, -1, True, "16", 16.0])
def test_generated_invalid_length(length):
    """ФТ-10 — длина вне 12–64 или не целое -> INVALID_LENGTH."""
    with pytest.raises(ValidationError) as exc:
        generate(length)
    assert exc.value.code == "INVALID_LENGTH"


def test_uses_secrets_module():
    """НФТ-11 — источник случайности криптостойкий (модуль secrets)."""
    import inspect
    from app import generator
    src = inspect.getsource(generator)
    assert "import secrets" in src and "import random" not in src

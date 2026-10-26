"""Юнит-тесты модуля оценки: ФТ-02, ФТ-03, ФТ-04, БП-01…БП-09."""
import pytest

from app import config
from app.scoring import (ValidationError, evaluate, has_repeat, has_sequence,
                         is_special, level_for, validate)
from tests.reference_set import REFERENCE


def codes(result):
    return [r.code for r in result.recommendations]


# ---------------------------------------------------------------- Приложение А
@pytest.mark.parametrize("num,password,desc,expected", REFERENCE,
                         ids=[f"A{r[0]:02d}" for r in REFERENCE])
def test_reference_set(num, password, desc, expected):
    """TC-A01…TC-A38 · ФТ-03, ФТ-04 — эталонный набор (Приложение А)."""
    if expected[0] == "ERR":
        with pytest.raises(ValidationError) as exc:
            evaluate(password)
        assert exc.value.code == expected[1]
    else:
        score, level, recs = expected
        r = evaluate(password)
        assert (r.score, r.level, codes(r)) == (score, level, recs)


# ---------------------------------------------------------------- ФТ-02, БП-09
@pytest.mark.parametrize("pwd,code", [
    ("", "EMPTY_PASSWORD"),
    ("x" * 65, "PASSWORD_TOO_LONG"),
    ("ab cd", "PASSWORD_HAS_WHITESPACE"),
    ("ab\ncd", "PASSWORD_HAS_WHITESPACE"),
    ("ab\u2003cd", "PASSWORD_HAS_WHITESPACE"),
])
def test_validation_errors(pwd, code):
    """ФТ-02, БП-09 — коды ошибок."""
    with pytest.raises(ValidationError) as exc:
        validate(pwd)
    assert exc.value.code == code
    assert exc.value.message == config.ERRORS[code]


@pytest.mark.parametrize("length", [1, 64])
def test_validation_bounds_ok(length):
    """ФТ-02 — границы 1 и 64 допустимы."""
    assert len(validate("Z" * length)) == length


def test_length_counted_after_nfc():
    """БП-02 — 64 символа после NFC проходят, хотя кодовых точек 128."""
    assert len(validate("e\u0301" * 64)) == 64


def test_zero_width_space_is_not_whitespace():
    """БП-09 — U+200B не пробельный (str.isspace() = False), считается спецсимволом."""
    r = evaluate("Aa1\u200bBbbcde")
    assert r.checks[5].passed is True


# ---------------------------------------------------------------- БП-01, БП-02
@pytest.mark.parametrize("pwd,idx,expected", [
    ("Abcdefg", 0, False), ("Abcdefgh", 0, True),              # C1: 7 / 8
    ("Abcdefghijk", 1, False), ("Abcdefghijkl", 1, True),      # C2: 11 / 12
    ("ABC", 2, False), ("ABc", 2, True), ("ЖЖя", 2, True),     # C3
    ("abc", 3, False), ("abC", 3, True), ("жжЯ", 3, True),     # C4
    ("abc", 4, False), ("ab7", 4, True), ("ab\u0663", 4, False),  # C5: ASCII only
    ("abc", 5, False), ("ab!", 5, True), ("ab\u0663", 5, True),   # C6
])
def test_criteria(pwd, idx, expected):
    """БП-01, БП-02 — каждый критерий C1–C6 и его граница."""
    assert evaluate(pwd).checks[idx].passed is expected


def test_letter_without_case_is_not_special():
    """БП-02 — буква без регистра (категория Lo) не даёт ни одного класса."""
    assert is_special("字") is False
    r = evaluate("字字")
    assert [c.passed for c in r.checks] == [False] * 6


def test_criteria_points_sum_100():
    """БП-01 — сумма баллов критериев равна 100."""
    assert sum(config.CRITERIA_POINTS.values()) == 100


# ---------------------------------------------------------------- БП-03
@pytest.mark.parametrize("pwd,expected", [
    ("aaa", True), ("aab", False), ("aAa", False), ("!!!", True),
    ("жжж", True), ("111", True),
])
def test_penalty_p1(pwd, expected):
    """БП-03 P1 — 3 одинаковых подряд, с учётом регистра."""
    assert has_repeat(pwd) is expected


@pytest.mark.parametrize("pwd,expected", [
    ("abc", True), ("CBA", True), ("aBc", True), ("xyz", True),
    ("123", True), ("321", True), ("890", False), ("098", False),
    ("zab", False), ("yza", False), ("ab1", False), ("abd", False),
    ("абв", False), ("a1b2c3", False), ("ab", False),
])
def test_penalty_p2(pwd, expected):
    """БП-03 P2 — латиница без учёта регистра или цифры, шаг ±1, без перехода."""
    assert has_sequence(pwd) is expected


def test_each_penalty_type_once():
    """БП-03 — каждый тип штрафа не более одного раза."""
    r = evaluate("abcabcabcXYZ1!")  # P2 встречается многократно
    assert [p.points for p in r.penalties] == [0, -10]


# ---------------------------------------------------------------- БП-04
@pytest.mark.parametrize("pwd", sorted(config.BLACKLIST))
def test_blacklist_any_case(pwd):
    """БП-04 — каждый пароль списка в нижнем и верхнем регистре."""
    for variant in (pwd, pwd.upper(), pwd.capitalize()):
        r = evaluate(variant)
        assert (r.score, r.level, r.blacklisted, codes(r)) == (0, "WEAK", True, ["R-O1"])


def test_blacklist_checks_still_reported():
    """§5 шаг 2 — для чёрного списка критерии всё равно считаются и отдаются."""
    r = evaluate("Password1")
    assert sum(c.points for c in r.checks) == 70


# ---------------------------------------------------------------- БП-05…БП-07
def test_lower_bound_zero():
    """БП-05 — балл не уходит в минус."""
    assert evaluate("aaabc").score == 0


@pytest.mark.parametrize("score,level", [
    (0, "WEAK"), (39, "WEAK"), (40, "MEDIUM"), (69, "MEDIUM"),
    (70, "STRONG"), (89, "STRONG"), (90, "VERY_STRONG"), (100, "VERY_STRONG"),
])
def test_levels_bounds(score, level):
    """БП-07 — границы уровней 39/40, 69/70, 89/90."""
    assert level_for(score)[0] == level


def test_short_password_cap():
    """БП-06 — пароль < 8 символов не выше 39."""
    r = evaluate("Aa1!Bb2")
    assert r.score == 39 and r.level == "WEAK"


def test_level_labels():
    """БП-07 — русские названия уровней."""
    assert [lbl for _, _, lbl in config.LEVELS] == [
        "Очень надёжный", "Надёжный", "Средний", "Слабый"]


# ---------------------------------------------------------------- БП-08
def test_recommendation_order():
    """БП-08 — порядок C1…C6, P1, P2; R-C2 скрыт, если не выполнен C1."""
    r = evaluate("aaabc")
    assert codes(r) == ["R-C1", "R-C4", "R-C5", "R-C6", "R-P1", "R-P2"]


def test_recommendation_texts_from_table():
    """БП-08, табл. 4.2 — тексты строго из конфигурации."""
    r = evaluate("abc")
    assert all(rec.text == config.RECOMMENDATIONS[rec.code] for rec in r.recommendations)


def test_to_dict_contract_keys():
    """ФТ-06 — набор полей результата соответствует §6.2."""
    d = evaluate("Qwerty789!").to_dict()
    assert list(d) == ["score", "level", "level_label", "length", "blacklisted",
                       "checks", "penalties", "recommendations"]
    assert [c["code"] for c in d["checks"]] == ["C1", "C2", "C3", "C4", "C5", "C6"]
    assert [p["code"] for p in d["penalties"]] == ["P1", "P2"]

"""Печатает Приложение А (markdown) и сверяет его с текущей реализацией.

Запуск из корня проекта:  python scripts/build_reference.py
Если поменяли правила в app/config.py — скрипт покажет строки, где ожидание
из tests/reference_set.py разошлось с кодом. Ожидания правьте ВРУЧНУЮ,
посчитав по алгоритму СТ §5, иначе тест перестанет быть независимым.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.scoring import ValidationError, evaluate  # noqa: E402
from tests.reference_set import LEVEL_LABELS, REFERENCE  # noqa: E402

# Windows-консоль по умолчанию не UTF-8: без этого print() падает на кириллице.
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

print("| № | Пароль | Длина | Балл | Уровень | Рекомендации |")
print("|---|---|---|---|---|---|")
mismatch = 0
for num, pwd, desc, exp in REFERENCE:
    try:
        r = evaluate(pwd)
        got = (r.score, r.level, [x.code for x in r.recommendations])
        row = (r.length, r.score, LEVEL_LABELS[r.level], ", ".join(got[2]))
    except ValidationError as e:
        got = ("ERR", e.code)
        row = (len(pwd), "—", f"ошибка {e.code}", "—")
    if tuple(got) != tuple(exp):
        mismatch += 1
        print(f"<!-- РАСХОЖДЕНИЕ в строке {num}: ожидалось {exp}, код дал {got} -->")
    print(f"| {num} | {desc} | {row[0]} | {row[1]} | {row[2]} | {row[3]} |")
print(f"\nСтрок: {len(REFERENCE)}, расхождений: {mismatch}", file=sys.stderr)
sys.exit(1 if mismatch else 0)

"""Замер НФТ-07 и БТ-08 на запущенном сервере.

1) В одном терминале:  uvicorn app.main:app
2) В другом:          python scripts/measure_perf.py
"""
import statistics
import sys
import time

import httpx

# Windows-консоль по умолчанию не UTF-8: без этого print() падает на кириллице.
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"

with httpx.Client(base_url=BASE, timeout=5) as c:
    c.get("/health")  # прогрев
    api = []
    for _ in range(100):
        t = time.perf_counter()
        c.post("/api/v1/password/check", json={"password": "Aa1!" * 16})
        api.append((time.perf_counter() - t) * 1000)
    form = []
    for _ in range(20):
        t = time.perf_counter()
        c.post("/check", data={"password": "Пароль2024!"})
        form.append((time.perf_counter() - t) * 1000)

ok = sum(x <= 200 for x in api)
print(f"НФТ-07: {ok}/100 запросов API ≤ 200 мс (нужно ≥ 95); "
      f"медиана {statistics.median(api):.1f} мс, максимум {max(api):.1f} мс")
print(f"БТ-08: 20 проверок через форму, максимум {max(form):.1f} мс (нужно ≤ 1000 мс)")
sys.exit(0 if ok >= 95 and max(form) <= 1000 else 1)

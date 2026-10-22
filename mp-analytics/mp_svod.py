#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mp_svod.py — свод выгрузок маркетплейсов (Wildberries / Ozon) в один отчёт.

Объединяет выгрузки продаж из разных кабинетов в один отчёт по артикулам:
заказы, выручка, комиссия площадки, логистика, себестоимость, прибыль, маржа
и ABC-класс по кумулятивной выручке.

Запуск:
    python mp_svod.py --demo              # синтетические данные, проверка логики
    python mp_svod.py wb.csv ozon.csv     # свои выгрузки
    python mp_svod.py wb.csv ozon.csv --cost cost.csv

`--cost` — CSV вида "артикул,себестоимость" (цена закупки за штуку).
Без него себестоимость = 0 и маржа будет завышена, скрипт предупредит.

ВАЖНО: заголовки колонок в кабинетах меняются. Алиасы в COLUMN_MAP — рабочая
гипотеза под типовые выгрузки; перед реальным запуском сверьте их с фактическими
заголовками своего экспорта.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict

# консоль Windows по умолчанию cp1251 — не умеет печатать ₽ и кириллицу из отчёта
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# логическое имя поля -> возможные заголовки в выгрузке (нижний регистр)
COLUMN_MAP = {
    "дата": ["дата", "дата заказа", "дата продажи", "created_at", "date"],
    "артикул": ["артикул", "артикул продавца", "sku", "offer_id"],
    "название": ["название", "название товара", "name"],
    "заказы": ["количество заказов", "заказы", "кол-во", "quantity", "orders"],
    "выручка": ["сумма продаж", "выручка", "сумма", "сумма продажи", "price"],
    "комиссия": ["вознаграждение площадки", "комиссия", "commission"],
    "логистика": ["логистика", "услуги по доставке", "доставка", "logistics"],
}

# если колонки комиссии нет в выгрузке — берём ставку по умолчанию
COMMISSION_FALLBACK = 0.15


def to_number(value: str) -> float:
    """'1 490,50' -> 1490.5 ; '' -> 0.0"""
    if value is None:
        return 0.0
    cleaned = str(value).replace("\xa0", "").replace(" ", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def map_row(row: dict) -> dict:
    """Превращает строку с любыми заголовками в словарь логических полей."""
    normalized = {k.strip().lower(): v for k, v in row.items() if k}
    out = {}
    for logical, aliases in COLUMN_MAP.items():
        for alias in aliases:
            if alias in normalized:
                out[logical] = normalized[alias]
                break
    return out


def read_sales(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = [map_row(r) for r in csv.DictReader(f)]
    if not rows or "артикул" not in rows[0]:
        raise SystemExit(f"{path}: не нашлась колонка с артикулом — сверьте заголовки")
    return [r for r in rows if r.get("артикул")]


def read_costs(path: str | None) -> dict[str, float]:
    if not path:
        return {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        return {
            r["артикул"].strip(): to_number(r.get("себестоимость", "0"))
            for r in csv.DictReader(f)
        }


def demo_data() -> tuple[list[dict], dict[str, float]]:
    """Синтетические выгрузки для проверки логики без реальных файлов."""
    raw = [
        ("WB", "KRT-2990", "Куртка утеплённая", 240, 2990),
        ("WB", "TSH-690", "Футболка хлопок", 780, 690),
        ("WB", "GLV-450", "Перчатки строительные", 640, 450),
        ("OZON", "BOT-1450", "Кроссовки", 410, 1450),
        ("OZON", "DSK-890", "Рюкзак", 520, 890),
        ("OZON", "JKT-3490", "Парка", 130, 3490),
    ]
    rows, costs = [], {}
    for source, sku, name, qty, price in raw:
        revenue = qty * price
        commission = round(revenue * (0.17 if source == "WB" else 0.15), 2)
        logistics = round(qty * (99 if source == "WB" else 75), 2)
        rows.append({
            "артикул": sku, "название": name, "заказы": str(qty),
            "выручка": str(revenue), "комиссия": str(commission),
            "логистика": str(logistics), "источник": source,
        })
        costs[sku] = {"KRT-2990": 980, "TSH-690": 210, "GLV-450": 130,
                      "BOT-1450": 520, "DSK-890": 310, "JKT-3490": 1250}[sku]
    return rows, costs


def aggregate(rows: list[dict], costs: dict[str, float]) -> list[dict]:
    """Сводит строки по артикулу: заказы, выручка, комиссия, логистика, прибыль."""
    agg: dict[str, dict] = defaultdict(lambda: {
        "название": "", "заказы": 0.0, "выручка": 0.0,
        "комиссия": 0.0, "логистика": 0.0, "комиссия_была": False,
    })
    for r in rows:
        sku = r["артикул"].strip()
        a = agg[sku]
        a["название"] = r.get("название") or a["название"]
        a["заказы"] += to_number(r.get("заказы", "0"))
        a["выручка"] += to_number(r.get("выручка", "0"))
        if r.get("комиссия"):
            a["комиссия"] += to_number(r["комиссия"])
            a["комиссия_была"] = True
        a["логистика"] += to_number(r.get("логистика", "0"))

    report = []
    for sku, a in agg.items():
        commission = a["комиссия"] if a["комиссия_была"] else a["выручка"] * COMMISSION_FALLBACK
        unit_cost = costs.get(sku, 0.0)
        cogs = unit_cost * a["заказы"]
        profit = a["выручка"] - commission - a["логистика"] - cogs
        margin = profit / a["выручка"] * 100 if a["выручка"] else 0.0
        report.append({
            "артикул": sku, "название": a["название"],
            "заказы": a["заказы"], "выручка": a["выручка"],
            "комиссия": commission, "логистика": a["логистика"],
            "себестоимость": cogs, "прибыль": profit, "маржа_%": margin,
            "комиссия_из_выгрузки": a["комиссия_была"],
        })
    return report


def assign_abc(report: list[dict]) -> list[dict]:
    """ABC по кумулятивной выручке: A до 80%, B до 95%, C — остальное."""
    report = sorted(report, key=lambda x: x["выручка"], reverse=True)
    total = sum(x["выручка"] for x in report) or 1.0
    cumulative = 0.0
    for row in report:
        cumulative += row["выручка"]
        share = cumulative / total * 100
        row["доля_%"] = row["выручка"] / total * 100
        row["кумулята_%"] = share
        row["abc"] = "A" if share <= 80 else ("B" if share <= 95 else "C")
    return report


def write_report(report: list[dict], out_path: str) -> str:
    columns = ["abc", "артикул", "название", "заказы", "выручка", "доля_%",
               "кумулята_%", "комиссия", "логистика", "себестоимость",
               "прибыль", "маржа_%"]
    try:
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Отчёт"
        ws.append([c.replace("_", " ") for c in columns])
        for row in report:
            ws.append([row.get(c, "") for c in columns])
        path = out_path if out_path.endswith(".xlsx") else out_path + ".xlsx"
        wb.save(path)
        return path
    except ImportError:
        path = out_path.rsplit(".", 1)[0] + ".csv"
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(report)
        return path + " (openpyxl не установлен — отчёт в CSV)"


def main() -> None:
    parser = argparse.ArgumentParser(description="Свод выгрузок маркетплейсов")
    parser.add_argument("files", nargs="*", help="CSV-выгрузки продаж")
    parser.add_argument("--demo", action="store_true", help="сгенерировать демо-данные")
    parser.add_argument("--cost", help="CSV с колонками артикул,себестоимость")
    parser.add_argument("--out", default="mp_report", help="имя файла отчёта")
    args = parser.parse_args()

    if args.demo:
        rows, demo_costs = demo_data()
        costs = {**demo_costs, **read_costs(args.cost)}
    else:
        if not args.files:
            parser.error("укажите файлы выгрузок или --demo")
        rows = []
        for path in args.files:
            rows.extend(read_sales(path))
        costs = read_costs(args.cost)

    report = assign_abc(aggregate(rows, costs))

    if not costs:
        print("ВНИМАНИЕ: себестоимость не передана (--cost), маржа завышена.")

    path = write_report(report, args.out)

    total_rev = sum(r["выручка"] for r in report)
    total_profit = sum(r["прибыль"] for r in report)
    print(f"Артикулов: {len(report)} · выручка: {total_rev:,.0f} ₽ · "
          f"прибыль: {total_profit:,.0f} ₽")
    for r in report:
        print(f"  [{r['abc']}] {r['артикул']:<12} выручка {r['выручка']:>12,.0f} ₽ "
              f"маржа {r['маржа_%']:>6.1f}%  {r['название']}")
    print(f"Отчёт: {path}")


if __name__ == "__main__":
    sys.exit(main())

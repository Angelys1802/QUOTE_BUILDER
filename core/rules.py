# core/rules.py
# Правила площі для матеріалів (waste).

from __future__ import annotations


def effective_area(area_sqft: float, waste_pct: float) -> float:
    """Площа для матеріалів = area * (1 + waste%)."""
    return area_sqft * (1 + waste_pct / 100.0)
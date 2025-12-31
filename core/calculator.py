from __future__ import annotations

from typing import Optional
from .models import QuoteRequest, QuoteResult, Trade


def _money(x: float) -> float:
    # стабільне округлення грошей
    return round(float(x) + 1e-9, 2)


def calculate_quote(trade: Trade, preset: Optional[str], req: QuoteRequest) -> QuoteResult:
    notes: list[str] = []

    if trade != "tile":
        notes.append(f"Trade '{trade}' not supported yet. Using generic logic.")

    sqft_with_waste = req.sqft * (1.0 + (req.waste_pct / 100.0))

    # Costs
    labor_cost = sqft_with_waste * req.labor_rate_per_sqft if req.include_labor else 0.0
    material_cost = sqft_with_waste * req.material_rate_per_sqft if req.include_materials else 0.0

    subtotal = labor_cost + material_cost

    if not req.include_labor:
        notes.append("Labor excluded.")
    if not req.include_materials:
        notes.append("Materials excluded.")

    if req.use_manual_total:
        total = req.manual_total
        notes.append("Manual total applied.")
    else:
        total = subtotal

    return QuoteResult(
        sqft_input=_money(req.sqft),
        sqft_with_waste=_money(sqft_with_waste),
        labor_cost=_money(labor_cost),
        material_cost=_money(material_cost),
        subtotal=_money(subtotal),
        total=_money(total),
        notes=notes,
    )
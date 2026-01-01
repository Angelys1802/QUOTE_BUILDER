from __future__ import annotations

from typing import Optional

from .models import QuoteRequest, QuoteResult, Trade


def _money(x: float) -> float:
    """Stable money rounding."""
    return round(float(x) + 1e-9, 2)


def calculate_quote(trade: Trade, preset: Optional[str], req: QuoteRequest) -> QuoteResult:
    """
    Minimal pricing engine (v0).

    Rules:
    - Waste applies to MATERIALS only.
    - Labor is based on actual sqft (no waste).
    - If use_manual_total=True, TOTAL is overridden by manual_total.
      (Labor/materials are still calculated as reference.)
    """
    notes: list[str] = []

    if trade != "tile":
        notes.append(f"Trade '{trade}' not supported yet. Using generic logic.")

    sqft = float(req.sqft)
    waste_pct = float(req.waste_pct or 0.0)

    sqft_with_waste = sqft * (1.0 + (waste_pct / 100.0))

    # ---- Costs ----
    labor_cost = (sqft * float(req.labor_rate_per_sqft)) if req.include_labor else 0.0
    material_cost = (sqft_with_waste * float(req.material_rate_per_sqft)) if req.include_materials else 0.0

    if not req.include_labor:
        notes.append("Labor excluded.")
    if not req.include_materials:
        notes.append("Materials excluded.")

    subtotal_calc = labor_cost + material_cost

    # ---- Manual override mode ----
    if req.use_manual_total:
        total = float(req.manual_total)
        notes.append("Manual total applied (override).")

        if total < labor_cost:
            notes.append("⚠️ WARNING: manual total is lower than labor cost")
    else:
        total = subtotal_calc

    return QuoteResult(
        sqft_input=_money(sqft),
        sqft_with_waste=_money(sqft_with_waste),
        labor_cost=_money(labor_cost),
        material_cost=_money(material_cost),
        subtotal=_money(subtotal_calc),
        total=_money(total),
        notes=notes,
    )
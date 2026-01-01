# core/calculator.py
from __future__ import annotations

from typing import Dict, Tuple

from .models import TradeConfig, PresetConfig, QuoteRequest, QuoteResult, PricingType
from .rules import effective_area


def _money(x: float) -> float:
    return round(float(x) + 1e-9, 2)


def _pick_bool(req_val, preset_default: bool) -> bool:
    return preset_default if req_val is None else bool(req_val)


def _pick_float(req_val, preset_default: float) -> float:
    return float(preset_default) if req_val is None else float(req_val)


def calculate_quote(
    trades: Dict[str, TradeConfig],
    req: QuoteRequest,
) -> Tuple[PresetConfig, TradeConfig, QuoteResult]:
    notes: list[str] = []

    if req.trade_id not in trades:
        raise ValueError(f"Unknown trade_id: {req.trade_id}")

    trade = trades[req.trade_id]

    if req.preset_id not in trade.presets:
        raise ValueError(f"Unknown preset_id: {req.preset_id} for trade {req.trade_id}")

    preset = trade.presets[req.preset_id]

    # --- Resolve toggles ---
    include_labor = _pick_bool(req.include_labor, preset.include_labor)
    include_materials = _pick_bool(req.include_materials, preset.include_materials)

    # --- Resolve inputs ---
    area = float(req.area_sqft)
    waste = _pick_float(req.waste_pct, preset.default_waste_pct)

    labor_rate = _pick_float(req.labor_rate_per_sqft, preset.default_labor_rate_per_sqft)
    material_rate = _pick_float(req.material_rate_per_sqft, preset.default_material_rate_per_sqft)

    # MIN_RATE_PER_SQFT: enforce min labor rate
    if preset.pricing_type == PricingType.MIN_RATE_PER_SQFT and preset.min_labor_rate_per_sqft is not None:
        if labor_rate < float(preset.min_labor_rate_per_sqft):
            notes.append(f"Labor rate raised to min ${preset.min_labor_rate_per_sqft}/sqft")
            labor_rate = float(preset.min_labor_rate_per_sqft)

    # Materials effective area uses waste. Labor uses actual area (практичніше для роботи)
    eff_area = effective_area(area, waste) if include_materials else area

    labor_cost = (area * labor_rate) if include_labor else 0.0
    material_cost = (eff_area * material_rate) if include_materials else 0.0

    if not include_labor:
        notes.append("Labor excluded.")
    if not include_materials:
        notes.append("Materials excluded.")

    # --- Full-service extras ---
    materials_handling_fee = 0.0
    materials_markup_amount = 0.0

    if req.full_service_materials and include_materials:
        handling_fee = _pick_float(req.materials_handling_fee, preset.default_full_service_handling_fee)
        markup_pct = _pick_float(req.materials_markup_pct, preset.default_full_service_markup_pct)

        materials_handling_fee = float(handling_fee)
        materials_markup_amount = material_cost * (float(markup_pct) / 100.0)

        notes.append("Full-service materials enabled (handling + markup).")

    # --- Pricing mode switch ---
    auto_subtotal = labor_cost + material_cost + materials_handling_fee + materials_markup_amount

    if req.use_manual_total or preset.pricing_type == PricingType.CUSTOM:
        # For CUSTOM we allow auto OR manual. Manual only if use_manual_total=True.
        if req.use_manual_total:
            if req.manual_total is None:
                raise ValueError("manual_total is required when use_manual_total=true")
            subtotal = float(req.manual_total)
            notes.append("CUSTOM pricing: manual total override used (labor/materials shown for reference).")
            if subtotal < labor_cost:
                notes.append("⚠️ WARNING: manual total is lower than labor cost.")
        else:
            subtotal = auto_subtotal
            notes.append("CUSTOM pricing: auto calculated.")
    else:
        subtotal = auto_subtotal

        # FLAT_MIN_TOTAL rule
        if preset.pricing_type == PricingType.FLAT_MIN_TOTAL and preset.min_total is not None:
            if subtotal < float(preset.min_total):
                notes.append(f"Flat minimum applied: ${preset.min_total}")
                subtotal = float(preset.min_total)

    gst = subtotal * float(trade.gst_rate)
    total = subtotal + gst

    result = QuoteResult(
        actual_area_sqft=_money(area),
        effective_area_sqft=_money(eff_area),

        labor_cost=_money(labor_cost),
        material_cost=_money(material_cost),

        materials_markup_amount=_money(materials_markup_amount),
        materials_handling_fee=_money(materials_handling_fee),

        subtotal=_money(subtotal),
        gst=_money(gst),
        total=_money(total),
        notes=notes,
    )

    return preset, trade, result
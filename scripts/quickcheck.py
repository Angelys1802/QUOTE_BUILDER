"""Quick runtime checks for Quote_Builder.
Run: python scripts/quickcheck.py
Exits with code 0 on success, non-zero on failure.
"""
import json
from pathlib import Path
from core.calculator import calculate_quote
from core.models import QuoteRequest, TradeConfig


def approx(a, b, tol=1e-6):
    return abs(a - b) <= tol


def load_trades():
    data_path = Path(__file__).resolve().parents[1] / "data" / "trades.json"
    raw = json.loads(data_path.read_text(encoding="utf-8"))
    return {tid: TradeConfig(**cfg) for tid, cfg in raw.items()}


def main():
    trades = load_trades()

    req = QuoteRequest(
        trade_id="tile",
        preset_id="kitchen_splash",
        area_sqft=100,
        waste_pct=10,
        labor_rate_per_sqft=12.5,
        material_rate_per_sqft=8.0,
    )

    _preset, _trade, res = calculate_quote(trades, req)

    assert approx(res.actual_area_sqft, 100.0), f"actual_area_sqft: {res.actual_area_sqft}"
    assert approx(res.effective_area_sqft, 110.0), f"effective_area_sqft: {res.effective_area_sqft}"
    assert approx(res.labor_cost, 1250.0), f"labor_cost: {res.labor_cost}"
    assert approx(res.material_cost, 880.0), f"material_cost: {res.material_cost}"
    assert approx(res.subtotal, 2130.0), f"subtotal: {res.subtotal}"
    assert approx(res.gst, 106.5), f"gst: {res.gst}"
    assert approx(res.total, 2236.5), f"total: {res.total}"

    # Floor preset: MIN_RATE_PER_SQFT, materials excluded
    req2 = QuoteRequest(
        trade_id="tile",
        preset_id="floor",
        area_sqft=50,
    )
    _p2, _t2, res2 = calculate_quote(trades, req2)
    assert approx(res2.labor_cost, 400.0), f"floor labor_cost: {res2.labor_cost}"
    assert approx(res2.material_cost, 0.0), f"floor material_cost: {res2.material_cost}"

    print("Quickcheck OK")


if __name__ == '__main__':
    main()

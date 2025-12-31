"""Quick runtime checks for Quote_Builder.
Run: python scripts/quickcheck.py
Exits with code 0 on success, non-zero on failure.
"""
from core.calculator import calculate_quote
from core.models import QuoteRequest


def approx(a, b, tol=1e-6):
    return abs(a - b) <= tol


def main():
    req = QuoteRequest(
        sqft=100,
        waste_pct=5,
        include_labor=True,
        include_materials=True,
        labor_rate_per_sqft=2.5,
        material_rate_per_sqft=3.0,
    )

    res = calculate_quote(trade="tile", preset=None, req=req)

    assert approx(res.sqft_input, 100.0)
    assert approx(res.sqft_with_waste, 105.0)
    assert approx(res.labor_cost, 262.5)
    assert approx(res.material_cost, 315.0)
    assert approx(res.subtotal, 577.5)

    print("Quickcheck OK")


if __name__ == '__main__':
    main()

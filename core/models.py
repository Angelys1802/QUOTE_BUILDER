from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal

Trade = Literal["tile"]  # потім розшириш: "tile" | "drywall" | ...


class QuoteRequest(BaseModel):
    sqft: float = Field(ge=0)

    waste_pct: float = Field(default=0, ge=0, le=100)

    include_labor: bool = True
    include_materials: bool = True

    labor_rate_per_sqft: float = Field(default=0, ge=0)
    material_rate_per_sqft: float = Field(default=0, ge=0)

    # якщо true — total береться з manual_total
    use_manual_total: bool = False
    manual_total: float = Field(default=0, ge=0)


class QuoteResult(BaseModel):
    sqft_input: float
    sqft_with_waste: float

    labor_cost: float
    material_cost: float
    subtotal: float
    total: float

    notes: list[str] = []
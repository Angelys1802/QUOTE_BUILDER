from __future__ import annotations

from typing import Literal, List
from pydantic import BaseModel, Field


Trade = Literal["tile"]  # later: extend ("tile", "drywall", ...)


class QuoteRequest(BaseModel):
    """
    Input from CLI/UI into calculator engine.
    """
    sqft: float = Field(..., ge=0)
    waste_pct: float = Field(0, ge=0, le=100)

    include_labor: bool = True
    include_materials: bool = True

    labor_rate_per_sqft: float = Field(0, ge=0)
    material_rate_per_sqft: float = Field(0, ge=0)

    # If true, total/subtotal are overridden by manual_total
    use_manual_total: bool = False
    manual_total: float = Field(0, ge=0)


class QuoteResult(BaseModel):
    """
    Output returned to UI.
    """
    sqft_input: float
    sqft_with_waste: float

    labor_cost: float
    material_cost: float

    subtotal: float
    total: float

    notes: List[str] = Field(default_factory=list)
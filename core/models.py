# core/models.py
from __future__ import annotations

from enum import Enum
from typing import Optional, Dict, List
from pydantic import BaseModel, Field


class PricingType(str, Enum):
    FLAT_MIN_TOTAL = "FLAT_MIN_TOTAL"
    MIN_RATE_PER_SQFT = "MIN_RATE_PER_SQFT"
    CUSTOM = "CUSTOM"


class PresetConfig(BaseModel):
    label: str
    pricing_type: PricingType

    include_labor: bool = True
    include_materials: bool = True

    # Defaults (можуть бути відсутні в JSON)
    default_waste_pct: float = 0
    default_labor_rate_per_sqft: float = 0
    default_material_rate_per_sqft: float = 0

    # Rules
    min_total: Optional[float] = None
    min_labor_rate_per_sqft: Optional[float] = None

    # Full-service options
    default_full_service_handling_fee: float = 0
    default_full_service_markup_pct: float = 0


class TradeConfig(BaseModel):
    label: str
    gst_rate: float = Field(default=0.05, ge=0, le=1)
    presets: Dict[str, PresetConfig] = Field(default_factory=dict)


# --- Request/Result for calculator/API ---

class QuoteRequest(BaseModel):
    trade_id: str = "tile"
    preset_id: str

    area_sqft: float = Field(ge=0)
    waste_pct: Optional[float] = Field(default=None, ge=0, le=100)

    include_labor: Optional[bool] = None
    include_materials: Optional[bool] = None

    labor_rate_per_sqft: Optional[float] = Field(default=None, ge=0)
    material_rate_per_sqft: Optional[float] = Field(default=None, ge=0)

    # Full-service materials (coordination + purchase + delivery)
    full_service_materials: bool = False
    materials_handling_fee: Optional[float] = Field(default=None, ge=0)
    materials_markup_pct: Optional[float] = Field(default=None, ge=0)

    # Manual override (CUSTOM)
    use_manual_total: bool = False
    manual_total: Optional[float] = Field(default=None, ge=0)


class QuoteResult(BaseModel):
    actual_area_sqft: float
    effective_area_sqft: float

    labor_cost: float
    material_cost: float

    materials_markup_amount: float
    materials_handling_fee: float

    subtotal: float
    gst: float
    total: float

    notes: List[str] = Field(default_factory=list)
from __future__ import annotations

from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Any

from core.models import QuoteRequest, QuoteResult, Trade
from core.calculator import calculate_quote

app = FastAPI(title="Quote Builder API", version="1.0.0")

# Якщо UI буде на іншому порту/домені — CORS тобі зекономить нерви
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # потім звузиш до свого домену
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/quote", response_model=QuoteResult)
def quote(
    trade: Trade = "tile",
    preset: str | None = None,
    req: QuoteRequest = Body(...),
) -> QuoteResult:
    """
    Основний endpoint: приймає QuoteRequest як body (JSON).
    FastAPI сам серіалізує QuoteResult назад у JSON.
    """
    try:
        return calculate_quote(trade=trade, preset=preset, req=req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---- Backward-compatible endpoint (якщо твій фронт/клієнт шле "payload") ----
@app.post("/quote_from_payload", response_model=QuoteResult)
def quote_from_payload(payload: dict[str, Any] = Body(...)) -> QuoteResult:
    """
    Приймає будь-який payload, мапить у QuoteRequest.
    Корисно, якщо старий UI шле "include_labor/include_materials/..." без строгої схеми.
    """
    trade = payload.get("trade", "tile")
    preset = payload.get("preset")

    try:
        req = QuoteRequest.model_validate(payload)
        return calculate_quote(trade=trade, preset=preset, req=req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")
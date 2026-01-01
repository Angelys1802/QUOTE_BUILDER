# web/api.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from core.models import TradeConfig, QuoteRequest, QuoteResult
from core.calculator import calculate_quote


def _load_trades() -> Dict[str, TradeConfig]:
    data_path = Path(__file__).resolve().parents[1] / "data" / "trades.json"
    raw = json.loads(data_path.read_text(encoding="utf-8"))
    return {trade_id: TradeConfig(**cfg) for trade_id, cfg in raw.items()}


TRADES: Dict[str, TradeConfig] = _load_trades()

app = FastAPI(title="Quote Builder API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/trades")
def get_trades() -> dict[str, Any]:
    # pydantic v1/v2 safe dump
    def dump(m):
        return m.model_dump() if hasattr(m, "model_dump") else m.dict()

    return {k: dump(v) for k, v in TRADES.items()}


@app.post("/api/quote", response_model=QuoteResult)
def quote(req: QuoteRequest = Body(...)) -> QuoteResult:
    try:
        _preset, _trade, result = calculate_quote(TRADES, req)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {e}")
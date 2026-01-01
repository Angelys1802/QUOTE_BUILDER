from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from core.models import QuoteRequest, QuoteResult, Trade
from core.calculator import calculate_quote

app = FastAPI(title="Quote Builder API", version="1.0.0")

# CORS: для локального UI / майбутнього фронта
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # потім звузиш до свого домену
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = ROOT / "web" / "static" / "index.html"


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    """
    Віддає UI (якщо файл існує).
    """
    if not INDEX_HTML.exists():
        return HTMLResponse(
            "<h3>UI not found</h3><p>Create web/static/index.html</p>",
            status_code=200,
        )
    return HTMLResponse(INDEX_HTML.read_text(encoding="utf-8"))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# --------------------------
# Main endpoint (clean)
# --------------------------

@app.post("/api/quote", response_model=QuoteResult)
def api_quote(
    req: QuoteRequest = Body(...),
    trade: Trade = "tile",
    preset: Optional[str] = None,
) -> QuoteResult:
    """
    Основний endpoint:
    - body: QuoteRequest
    - query: trade, preset (опціонально)
    """
    try:
        return calculate_quote(trade=trade, preset=preset, req=req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --------------------------
# Backward-compatible endpoint (payload mapping)
# --------------------------

@app.post("/api/quote_from_payload", response_model=QuoteResult)
def api_quote_from_payload(payload: dict[str, Any] = Body(...)) -> QuoteResult:
    """
    Приймає будь-який payload і мапить у QuoteRequest.
    Працює і з Pydantic v1, і з v2.
    """
    trade = payload.get("trade", "tile")
    preset = payload.get("preset")

    # Pydantic v2: model_validate
    # Pydantic v1: parse_obj
    try:
        if hasattr(QuoteRequest, "model_validate"):
            req = QuoteRequest.model_validate(payload)  # type: ignore[attr-defined]
        else:
            req = QuoteRequest.parse_obj(payload)  # Pydantic v1
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")

    try:
        return calculate_quote(trade=trade, preset=preset, req=req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Optional aliases (якщо десь у тебе старий клієнт)
@app.post("/quote", response_model=QuoteResult)
def quote_alias(
    req: QuoteRequest = Body(...),
    trade: Trade = "tile",
    preset: Optional[str] = None,
) -> QuoteResult:
    return api_quote(req=req, trade=trade, preset=preset)
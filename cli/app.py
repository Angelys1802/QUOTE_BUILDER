# cli/app.py
# CLI = тимчасовий UI. Його можна замінити на Web/iOS, не чіпаючи core.

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

from typing import cast
from core.models import QuoteRequest, Trade
from core.calculator import calculate_quote


# ---------- ДОПОМІЖНІ ФУНКЦІЇ ВВОДУ ----------

def ask_float(prompt: str, *, min_value: float | None = None) -> float:
    """Безпечний ввід числа: не ламається, поки не введуть число."""
    while True:
        raw = input(prompt).strip().replace(",", ".")
        try:
            value = float(raw)
        except ValueError:
            print("❌ Enter a number (example: 12.5)")
            continue
        if min_value is not None and value < min_value:
            print(f"❌ Value must be >= {min_value}")
            continue
        return value


def ask_float_default(prompt: str, default: float, *, min_value: float | None = None) -> float:
    """Ввід числа з дефолтом: Enter -> default."""
    while True:
        raw = input(f"{prompt} [{default}]: ").strip()
        if raw == "":
            value = float(default)
        else:
            raw = raw.replace(",", ".")
            try:
                value = float(raw)
            except ValueError:
                print("❌ Enter a number or press Enter")
                continue

        if min_value is not None and value < min_value:
            print(f"❌ Value must be >= {min_value}")
            continue
        return value


def ask_yes_no(prompt: str) -> bool:
    """Безпечний ввід так/ні: повертає True або False."""
    while True:
        raw = input(prompt + " (y/n): ").strip().lower()
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("❌ Enter y or n")


def money(x: float) -> str:
    """Красивий формат грошей."""
    return f"${x:,.2f}"


# ---------- HISTORY (JSON) ----------

def save_quote_json(payload: dict) -> Path:
    """
    Зберігає квоту як JSON в data/history/.
    Повертає шлях до створеного файлу.
    """
    root = Path(__file__).resolve().parents[1]  # корінь проєкту
    history_dir = root / "data" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)

    # Безпечне ім'я файлу
    ts = payload["meta"]["created_at"].replace(":", "").replace("-", "")
    trade_id = payload["meta"]["trade_id"]
    preset_id = payload["meta"]["preset_id"]
    client = payload["meta"]["client_name"].strip().lower().replace(" ", "_") or "client"

    filename = f"{ts}_{trade_id}_{preset_id}_{client}.json"
    path = history_dir / filename

    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


# ---------- ЗАВАНТАЖЕННЯ CONFIG З JSON ----------

def load_trades_config() -> dict[str, dict]:
    """Читає data/trades.json і повертає структури у вигляді словників."""
    data_path = Path(__file__).resolve().parents[1] / "data" / "trades.json"
    raw = json.loads(data_path.read_text(encoding="utf-8"))

    trades: dict[str, dict] = {}

    for trade_id, trade_cfg in raw.items():
        presets: dict[str, dict] = {}

        for preset_id, p in trade_cfg.get("presets", {}).items():
            presets[preset_id] = {
                "preset_id": preset_id,
                "label": p["label"],
                "pricing_type": p.get("pricing_type", "fixed"),
                "include_labor": bool(p.get("include_labor", True)),
                "include_materials": bool(p.get("include_materials", True)),
                "min_total": p.get("min_total"),
                "min_labor_rate_per_sqft": p.get("min_labor_rate_per_sqft"),
                "default_waste_pct": p.get("default_waste_pct"),
                "default_labor_rate_per_sqft": p.get("default_labor_rate_per_sqft"),
                "default_material_rate_per_sqft": p.get("default_material_rate_per_sqft"),
                "default_full_service_handling_fee": p.get("default_full_service_handling_fee"),
                "default_full_service_markup_pct": p.get("default_full_service_markup_pct"),
            }

        trades[trade_id] = {
            "trade_id": trade_id,
            "label": trade_cfg["label"],
            "gst_rate": float(trade_cfg.get("gst_rate", 0.0)),
            "presets": presets,
        }

    return trades


# ---------- ОСНОВНИЙ CLI СЦЕНАРІЙ ----------

def run_cli() -> None:
    print("\n=== Trade Quote Builder (CLI) v0.4 (History JSON) ===\n")

    trades = load_trades_config()

    # --- Метадані (для історії) ---
    client_name = input("Client name (optional): ").strip()
    job_address = input("Job address (optional): ").strip()

    # --- Вибір trade ---
    print("\nAvailable trades:")
    for k, t in trades.items():
        print(f" - {k}: {t['label']}")

    trade_id = input("\nChoose trade id (example: tile): ").strip().lower()
    if trade_id not in trades:
        print("❌ Unknown trade id")
        return
    trade = trades[trade_id]

    # --- Вибір preset ---
    print("\nAvailable presets:")
    for k, p in trade["presets"].items():
        print(f" - {k}: {p['label']} [{p.get('pricing_type','')}]")

    preset_id = input("\nChoose preset id: ").strip().lower()
    if preset_id not in trade["presets"]:
        print("❌ Unknown preset id")
        return
    preset = trade["presets"][preset_id]

    # --- Ввід площі ---
    area = ask_float("Actual area (sqft): ", min_value=0)

    # --- Waste (впливає тільки якщо materials включені) ---
    waste = 0.0
    if preset.get("include_materials", True):
        default_waste = float(preset.get("default_waste_pct") or 0.0)
        waste = ask_float_default("Waste %", default_waste, min_value=0)

    # --- Ставки (Enter = дефолт) ---
    labor_rate = 0.0
    material_rate = 0.0

    if preset.get("include_labor", True):
        default_labor = float(preset.get("default_labor_rate_per_sqft") or 0.0)
        labor_rate = ask_float_default("Labor rate ($/sqft)", default_labor, min_value=0)

    if preset.get("include_materials", True):
        default_material = float(preset.get("default_material_rate_per_sqft") or 0.0)
        material_rate = ask_float_default("Material rate ($/sqft)", default_material, min_value=0)

    # --- Full service materials ---
    materials_full_service = False
    materials_handling_fee = 0.0
    materials_markup_pct = 0.0

    if preset.get("include_materials", True):
        materials_full_service = ask_yes_no("Client wants full service materials (coordination + purchase + delivery)?")
        if materials_full_service:
            default_fee = float(preset.get("default_full_service_handling_fee") or 0.0)
            default_markup = float(preset.get("default_full_service_markup_pct") or 0.0)
            materials_handling_fee = ask_float_default("Materials handling fee ($)", default_fee, min_value=0)
            materials_markup_pct = ask_float_default("Materials markup %", default_markup, min_value=0)

    # --- CUSTOM (shower) -> manual total ---
    manual_total = None
    use_manual_total = False

    if str(preset.get("pricing_type", "")).lower() == "custom":
        use_manual_total = ask_yes_no("Use manual total (override calculated total)?")
    if use_manual_total:
        manual_total = ask_float("Enter manual total price ($): ", min_value=0)
    # --- Формуємо request для core engine ---
    # Map CLI values into core QuoteRequest (core expects `sqft` field)
    req = QuoteRequest(
        sqft=area,
        labor_rate_per_sqft=labor_rate,
        material_rate_per_sqft=material_rate,
        waste_pct=waste,
        include_labor=bool(preset.get("include_labor", True)),
        include_materials=bool(preset.get("include_materials", True)),
        manual_total=manual_total or 0.0,
        use_manual_total=use_manual_total,
    )

    # --- Розрахунок через core ---
    result = calculate_quote(cast(Trade, trade_id), preset_id, req)

    # --- Вивід breakdown ---
    print("\n--- Breakdown ---")
    print(f"Trade:                 {trade['label']}")
    print(f"Preset:                {preset['label']} [{preset.get('pricing_type', '')}]")
    print(f"Actual area:           {result.sqft_input:,.2f} sqft")

    if preset.get("include_materials", True):
        print(f"Area w/ waste:         {result.sqft_with_waste:,.2f} sqft (waste {waste:.2f}%)")
    else:
        print("Area w/ waste:         (materials not included)")

    print(f"Labor:                 {money(result.labor_cost)}")
    print(f"Materials:             {money(result.material_cost)}")

    print(f"Subtotal:              {money(result.subtotal)}")
    print(f"TOTAL:                 {money(result.total)}")

    if result.notes:
        print("\nNotes:")
        for n in result.notes:
            print(f" - {n}")

    print("-----------------\n")

    # --- Збереження в JSON history ---
    if ask_yes_no("Save quote to history (JSON)?"):
        created_at = datetime.now().isoformat(timespec="seconds")

        payload = {
            "meta": {
                "created_at": created_at,
                "trade_id": trade.get("trade_id"),
                "trade_label": trade.get("label"),
                "preset_id": preset.get("preset_id"),
                "preset_label": preset.get("label"),
                "pricing_type": preset.get("pricing_type"),
                "client_name": client_name,
                "job_address": job_address,
            },
            "input": {
                "area_sqft": area,
                "waste_pct": waste,
                "labor_rate_per_sqft": labor_rate,
                "material_rate_per_sqft": material_rate,
                "include_labor": preset.get("include_labor", True),
                "include_materials": preset.get("include_materials", True),
                "materials_full_service": materials_full_service,
                "materials_handling_fee": materials_handling_fee,
                "materials_markup_pct": materials_markup_pct,
                "manual_total": manual_total,
            },
            "output": {
                "sqft_input": result.sqft_input,
                "sqft_with_waste": result.sqft_with_waste,
                "labor_cost": result.labor_cost,
                "material_cost": result.material_cost,
                "materials_markup_amount": 0.0,
                "materials_handling_fee": materials_handling_fee or 0.0,
                "subtotal": result.subtotal,
                "gst": 0.0,
                "total": result.total,
                "notes": result.notes,
            },
        }

        path = save_quote_json(payload)
        print(f"✅ Saved JSON: {path}\n")

    # --- Збереження у txt (як раніше) ---
    if ask_yes_no("Save quote to a text file?"):
        job_name = input("File name (example: 2025-12-30_job1): ").strip() or "quote"
        filename = f"{job_name}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            f.write("Trade Quote Builder (CLI) v0.4 (History JSON)\n\n")
            if client_name:
                f.write(f"Client:  {client_name}\n")
            if job_address:
                f.write(f"Address: {job_address}\n")
            f.write(f"Trade:   {trade.get('label')}\n")
            f.write(f"Preset:  {preset.get('label')} [{preset.get('pricing_type','')}]\n\n")

            f.write(f"Actual area:   {result.sqft_input:,.2f} sqft\n")
            if preset.get('include_materials', True):
                f.write(f"Area w/ waste: {result.sqft_with_waste:,.2f} sqft (waste {waste:.2f}%)\n")
            else:
                f.write("Area w/ waste: (materials not included)\n")

            f.write(f"Labor:         {money(result.labor_cost)}\n")
            f.write(f"Materials:     {money(result.material_cost)}\n")

            if materials_markup_pct and materials_markup_pct > 0:
                # CLI-collected markup (not applied in core)
                f.write(f"Markup:        {money((materials_markup_pct/100.0)*result.material_cost)}\n")
            if materials_handling_fee and materials_handling_fee > 0:
                f.write(f"Handling:      {money(materials_handling_fee)}\n")

            f.write(f"Subtotal:      {money(result.subtotal)}\n")
            f.write(f"GST:           {money(0.0)}\n")
            f.write(f"TOTAL:         {money(result.total)}\n")

            if result.notes:
                f.write("\nNotes:\n")
                for n in result.notes:
                    f.write(f"- {n}\n")

        print(f"✅ Saved: {filename}\n")
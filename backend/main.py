# backend/main.py
# ------------------------------------------------------------
# Hauptanwendungscode für die FastAPI-App.
# Definiert API-Endpunkte, startet die Anwendung und bindet
# andere Module (Datenbank, Modelle, Services) ein.
# ------------------------------------------------------------

from pathlib import Path
from datetime import datetime
from typing import List

import sqlite3
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# interne Module aus dem Ordner backend
from . import database          # database.py
from . import models            # models.py
from . import services          # services.py

app = FastAPI()

# ------------------------------------------------------------
# 1) Startup-Event – Datenbank initialisieren
# ------------------------------------------------------------
@app.on_event("startup")
def on_startup() -> None:
    database.init_db()

# ------------------------------------------------------------
# 2) Statisches Frontend einbinden
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent      # Projekt-Root
FRONTEND_DIR = BASE_DIR / "frontend"                  # absoluter Pfad

app.mount(
    "/frontend",
    StaticFiles(directory=FRONTEND_DIR),
    name="frontend",
)

@app.get("/")
async def read_index():
    """Liefert die index.html aus dem Frontend-Ordner."""
    return FileResponse(FRONTEND_DIR / "index.html")

# ------------------------------------------------------------
# 3) Hilfsfunktion – Aktie in DB anlegen
# ------------------------------------------------------------
def create_stock(stock: models.StockCreate) -> models.Stock:
    conn = database.get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO stocks
            (symbol, name, current_price, eps, pe_ratio,
             growth_5y_percent, eps_in_5y, target_pe_ratio,
             fair_value, price_diff, potential_percent, comment)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                stock.symbol, stock.name, stock.current_price, stock.eps,
                stock.pe_ratio, stock.growth_5y_percent, stock.eps_in_5y,
                stock.target_pe_ratio, stock.fair_value, stock.price_diff,
                stock.potential_percent, stock.comment,
            ),
        )
        conn.commit()
        new_row = conn.execute(
            "SELECT * FROM stocks WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        return models.Stock(**dict(new_row))
    except sqlite3.IntegrityError:
        conn.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Aktie mit Symbol '{stock.symbol}' existiert bereits.",
        )
    finally:
        conn.close()

# ------------------------------------------------------------
# 4) API-Endpunkte
# ------------------------------------------------------------

# 4.1  Auto-Fetch: holt Daten von Finnhub, legt Aktie sofort an
@app.post("/api/stocks/auto/{symbol}", response_model=models.Stock, status_code=201)
def add_stock_auto(symbol: str):
    data = services.fetch_stock_data(symbol)
    if not data:
        raise HTTPException(status_code=404, detail="Daten konnten nicht geladen werden")

    stock_obj = models.StockCreate(
        symbol=data["symbol"],
        name=data["name"],
        current_price=data["current_price"],
        eps=data["eps"],
        pe_ratio=data["pe_ratio"],
    )
    return create_stock(stock_obj)

# 4.2  Manuell Aktie anlegen
@app.post("/api/stocks/", response_model=models.Stock, status_code=201)
def add_stock(stock: models.StockCreate):
    return create_stock(stock)

# 4.3  Alle Aktien abrufen
@app.get("/api/stocks/", response_model=List[models.Stock])
def get_all_stocks():
    conn = database.get_db_connection()
    rows = conn.execute("SELECT * FROM stocks ORDER BY symbol ASC").fetchall()
    conn.close()
    return [models.Stock(**dict(r)) for r in rows]

# 4.4  Aktie per ID abrufen
@app.get("/api/stocks/{stock_id}", response_model=models.Stock)
def get_stock_by_id(stock_id: int):
    conn = database.get_db_connection()
    row = conn.execute("SELECT * FROM stocks WHERE id = ?", (stock_id,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Aktie nicht gefunden")
    return models.Stock(**dict(row))

# 4.5  Aktie per Symbol abrufen
@app.get("/api/stocks/symbol/{symbol}", response_model=models.Stock)
def get_stock_by_symbol(symbol: str):
    conn = database.get_db_connection()
    row = conn.execute("SELECT * FROM stocks WHERE symbol = ?", (symbol.upper(),)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Aktie mit Symbol '{symbol}' nicht gefunden")
    return models.Stock(**dict(row))

# 4.6  Aktie aktualisieren
@app.put("/api/stocks/{stock_id}", response_model=models.Stock)
def update_stock(stock_id: int, stock_update: models.StockCreate):
    conn = database.get_db_connection()
    cursor = conn.cursor()

    existing = cursor.execute("SELECT * FROM stocks WHERE id = ?", (stock_id,)).fetchone()
    if existing is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Aktie nicht gefunden")

    update_data = stock_update.dict(exclude_unset=True)
    if not update_data:
        return models.Stock(**dict(existing))

    # Symbol-Änderung prüfen
    if "symbol" in update_data and update_data["symbol"].upper() != existing["symbol"]:
        dupe = cursor.execute(
            "SELECT id FROM stocks WHERE symbol = ? AND id != ?",
            (update_data["symbol"].upper(), stock_id),
        ).fetchone()
        if dupe:
            conn.close()
            raise HTTPException(status_code=400, detail="Symbol existiert bereits")

    fields = {k: v for k, v in update_data.items() if k not in ["id", "last_updated"]}
    set_clause = ", ".join(f"{k} = ?" for k in fields) + ", last_updated = ?"
    values = list(fields.values()) + [datetime.now(), stock_id]

    cursor.execute(f"UPDATE stocks SET {set_clause} WHERE id = ?", tuple(values))
    conn.commit()
    updated = cursor.execute("SELECT * FROM stocks WHERE id = ?", (stock_id,)).fetchone()
    conn.close()
    return models.Stock(**dict(updated))

# 4.7  Aktie löschen
@app.delete("/api/stocks/{stock_id}", status_code=200)
def delete_stock(stock_id: int):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    if cursor.execute("SELECT * FROM stocks WHERE id = ?", (stock_id,)).fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Aktie nicht gefunden")
    cursor.execute("DELETE FROM stocks WHERE id = ?", (stock_id,))
    conn.commit()
    conn.close()
    return {"message": "Aktie erfolgreich gelöscht"}

# ------------------------------------------------------------
# 5) Direktstart (z. B. `python -m backend.main`)
# ------------------------------------------------------------
if __name__ == "__main__":
    # aus Projekt-Root:  python -m backend.main
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

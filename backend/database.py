# backend/database.py
# ------------------------------------------------------------
# Stellt eine Verbindung zur SQLite-Datenbank her
# und legt bei Bedarf die Tabelle 'stocks' an.
# ------------------------------------------------------------
import sqlite3
from pathlib import Path

# Absoluter Pfad zur Datei data/aktien.db
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH  = BASE_DIR / "data" / "aktien.db"

def get_db_connection() -> sqlite3.Connection:
    """Verbindung zur SQLite-Datenbank (thread-safe für FastAPI)."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row          # <- gibt Zeilen als Mapping (dict-ähnlich) zurück
    return conn

def init_db() -> None:
    """Legt die Tabelle 'stocks' an, falls sie noch nicht existiert."""
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT UNIQUE NOT NULL,
            name TEXT,
            current_price REAL,
            eps REAL,
            pe_ratio REAL,
            growth_5y_percent REAL,
            eps_in_5y REAL,
            target_pe_ratio REAL,
            fair_value REAL,
            price_diff REAL,
            potential_percent REAL,
            comment TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    conn.commit()
    conn.close()

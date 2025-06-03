# ---------------------------------------------------------------------
# backend/services.py  –  Service-Schicht für Finnhub + Berechnungen
# ---------------------------------------------------------------------
import finnhub
import os
from typing import Optional
from datetime import datetime

from . import valuation as val

# ------------------------------------------------------------------
# 1. Finnhub-Client
# ------------------------------------------------------------------
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "d0ue1cpr01qn5fk4qj20d0ue1cpr01qn5fk4qj2g")
if FINNHUB_API_KEY in {"DEIN_FINNHUB_API_SCHLUESSEL", ""}:
    print("WARNUNG: Bitte FINNHUB_API_KEY setzen, sonst schlagen API-Aufrufe fehl.")

finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)

# ------------------------------------------------------------------
# 2. Hilfsfunktionen  (Profil, Quote, Wechselkurs)
# ------------------------------------------------------------------
def get_stock_profile(symbol: str) -> dict:
    try:
        return finnhub_client.company_profile2(symbol=symbol.upper()) or {}
    except Exception as e:
        print(f"Profil-Fehler [{symbol}]: {e}")
        return {}

def get_stock_quote(symbol: str) -> dict:
    try:
        return finnhub_client.quote(symbol=symbol.upper()) or {}
    except Exception as e:
        print(f"Kurs-Fehler [{symbol}]: {e}")
        return {}

def get_exchange_rate(base_currency: str, target_currency: str = "EUR") -> Optional[float]:
    """Optional: Wechselkurs abrufen (nicht mehr zwingend für die Logik)."""
    try:
        if base_currency.upper() == target_currency.upper():
            return 1.0
        data = finnhub_client.forex_rates(base=base_currency.upper())
        return data.get("quote", {}).get(target_currency.upper())
    except Exception as e:
        print(f"FX-Fehler {base_currency}/{target_currency}: {e}")
        return None

# ------------------------------------------------------------------
# 3. Hauptfunktion  –  komplett neu
# ------------------------------------------------------------------
def fetch_stock_data(symbol: str) -> dict:
    """
    Holt Kurs + Kennzahlen von Finnhub und berechnet alle Excel-Spalten
    F (Growth) bis M (Über/Unterbewertung %).
    Gibt ein Dict zurück, das direkt in die DB geschrieben wird.
    """
    symbol = symbol.upper()

    # 1) Finnhub-Rohdaten
    profile = get_stock_profile(symbol)
    quote   = get_stock_quote(symbol)
    if not profile or not quote or "c" not in quote:
        return {}

    price_now = quote["c"]                      # aktueller Kurs
    eps       = profile.get("eps") or 0.0       # Gewinn/Aktie

    # 2) Standardparameter
    growth    = val.GROWTH_5Y_DEFAULT           # 0.08 = 8 %
    target_pe = val.TARGET_PE_DEFAULT           # 25

    # 3) Berechnungen (G – M)
    eps_5y   = val.calc_eps_in_5y(eps, growth)          # G
    price_5y = val.calc_price_in_5y(eps_5y, target_pe)  # I
    fair_val = val.calc_fair_value(price_5y)            # J/K
    diff_eur, diff_pct, _ = val.calc_diffs(price_now, fair_val)

    # 4) Ergebnis-Dict  –  entspricht allen DB-Spalten
    return {
        "symbol": symbol,
        "name":   profile.get("name"),

        "current_price":      price_now,
        "eps":                eps,
        "pe_ratio":           price_now / eps if eps else None,

        "growth_5y_percent":  growth * 100,   # F (%)
        "eps_in_5y":          eps_5y,         # G
        "target_pe_ratio":    target_pe,      # H
        "price_in_5y":        price_5y,       # I
        "fair_value":         fair_val,       # J/K
        "price_diff":         diff_eur,       # L (Euro)
        "potential_percent":  diff_pct,       # M (%)

        "last_updated": datetime.utcnow(),
    }

# ------------------------------------------------------------------
# 5.  Manueller Schnelltest
# ------------------------------------------------------------------
if __name__ == "__main__":
    print(fetch_stock_data("AAPL"))

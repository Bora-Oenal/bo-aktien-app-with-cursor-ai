# Dieses Modul definiert die Pydantic-Datenmodelle.
# Diese Modelle werden für die Datenvalidierung in API-Anfragen und -Antworten 
# sowie zur Strukturierung der Daten für die Datenbankinteraktion verwendet.
from pydantic import BaseModel
from typing import Optional, Union
from datetime import datetime

class StockBase(BaseModel):
    symbol: str  # Eindeutiges Aktiensymbol, z.B. AAPL
    name: Optional[str] = None  # Vollständiger Name des Unternehmens
    current_price: Optional[float] = None  # Aktueller Aktienkurs
    eps: Optional[float] = None  # Gewinn pro Aktie (Earnings Per Share)
    pe_ratio: Optional[float] = None  # Kurs-Gewinn-Verhältnis (KGV)
    growth_5y_percent: Optional[float] = None  # Durchschnittliches jährliches Gewinnwachstum der letzten 5 Jahre in %
    eps_in_5y: Optional[float] = None  # Geschätzter Gewinn pro Aktie in 5 Jahren
    target_pe_ratio: Optional[float] = None  # Angestrebtes KGV für die Bewertung
    fair_value: Optional[float] = None  # Berechneter fairer Wert der Aktie
    price_diff: Optional[float] = None # Differenz zwischen aktuellem Kurs und fairem Wert
    potential_percent: Optional[float] = None  # Kurspotenzial in Prozent
    comment: Optional[str] = None  # Persönlicher Kommentar oder Notizen zur Aktie

class StockCreate(StockBase):
    # Modell zum Erstellen einer neuen Aktie, erbt alle Felder von StockBase
    pass

class Stock(StockBase):
    # Modell zur Repräsentation einer Aktie aus der Datenbank, inklusive ID und Zeitstempel
    id: int  # Eindeutige ID aus der Datenbank
    last_updated: datetime  # Zeitstempel der letzten Aktualisierung

    class Config:
        orm_mode = True # Erlaubt das Modell direkt mit ORM-Objekten zu verwenden (für später) 
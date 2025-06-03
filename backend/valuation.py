# backend/valuation.py
# ------------------------------------------------------------
# Globale Parameter
# ------------------------------------------------------------
GROWTH_5Y_DEFAULT = 0.08      # 8 % Gewinn­wachstum (F-Spalte)
TARGET_PE_DEFAULT = 25        # faires KGV in 5 J. (H-Spalte)
DISCOUNT_RATE     = 0.10      # C2 – gewünschte jährliche Rendite (10 %)
SAFETY_MARGIN     = 0.30      # C3 – Margin of Safety (30 %)
# ------------------------------------------------------------
# Reine Rechenfunktionen (1:1 aus deinem Sheet)
# ------------------------------------------------------------
def calc_eps_in_5y(eps: float, growth: float = GROWTH_5Y_DEFAULT) -> float:
    return eps * (1 + growth) ** 5

def calc_price_in_5y(eps_in_5y: float, target_pe: float = TARGET_PE_DEFAULT) -> float:
    return eps_in_5y * target_pe

def calc_fair_value(price_in_5y: float,
                    discount_rate: float = DISCOUNT_RATE,
                    safety_margin: float = SAFETY_MARGIN) -> float:
    disc_fair = price_in_5y / (1 + discount_rate) ** 5
    return disc_fair * (1 - safety_margin)

def calc_diffs(current_price: float, fair_value: float) -> tuple[float, float, float]:
    price_diff      = fair_value - current_price          # L-Spalte
    under_over_pct  = (price_diff / current_price) * 100  # M-Spalte
    potential_pct   = (fair_value / current_price - 1) * 100  # N-Spalte
    return price_diff, under_over_pct, potential_pct

"""Gas Natural — engineering calc engine.

Real engineering formulas used during phase completion. Designed as a pure
library: input → output dictionaries. Used by both the dynamic form on the
frontend (for live hints) and the backend `/calc` endpoint (authoritative).

Implements:
- Renouard formula (low-pressure: ≤100 mbar): ΔP = 23200 × s × L × Q^1.82 / D^4.82
- Renouard quadratic (medium-pressure: 100 mbar – 4 bar): P1² – P2² = 51.5 × s × L × Q^1.82 / D^4.82
- Simultaneity coefficient Ks (NTPEE 2018 Anexa 5) per number of consumers
- Gas velocity in pipe (m/s) — should be < 20 m/s for joasă, < 30 m/s for medie
- Recommended diameter (iteratively from standard DN list)
- Burial depth validation (NTPEE 2018 art. 56: min 0.9 m sub trafic auto, 0.6 m verde)
- Cost estimation (lei) based on material + length + nr_armatures

Notes:
- s = densitatea relativă a gazului (≈0.554 pentru CH4 vs aer).
- L = lungime echivalentă (m); D = diametru interior (mm).
- Q = debit (m³/h, raportat la 15°C 1.013 bar).
"""
from __future__ import annotations
import math
from typing import Any, Dict, List, Optional, Tuple

# Constants
GAS_DENSITY_RELATIVE = 0.554  # methane vs air
GAS_DENSITY_KG_M3 = 0.717     # at 0°C, 1 atm

# Standard pipe diameters (PE 100) — outer diameter / wall / internal diameter (mm)
PE100_SDR11: List[Dict[str, float]] = [
    {"DN": 25,  "od": 25,  "wall": 3.0,  "id_": 19.0},
    {"DN": 32,  "od": 32,  "wall": 3.0,  "id_": 26.0},
    {"DN": 40,  "od": 40,  "wall": 3.7,  "id_": 32.6},
    {"DN": 50,  "od": 50,  "wall": 4.6,  "id_": 40.8},
    {"DN": 63,  "od": 63,  "wall": 5.8,  "id_": 51.4},
    {"DN": 75,  "od": 75,  "wall": 6.8,  "id_": 61.4},
    {"DN": 90,  "od": 90,  "wall": 8.2,  "id_": 73.6},
    {"DN": 110, "od": 110, "wall": 10.0, "id_": 90.0},
    {"DN": 125, "od": 125, "wall": 11.4, "id_": 102.2},
    {"DN": 160, "od": 160, "wall": 14.6, "id_": 130.8},
    {"DN": 200, "od": 200, "wall": 18.2, "id_": 163.6},
    {"DN": 250, "od": 250, "wall": 22.7, "id_": 204.6},
]

# OL galvanizat / Cupru — standard internal diameters (mm) used after meter (joasă)
OL_GALV_DIAMS = [
    {"DN": "1/2\"", "id_": 16.0},
    {"DN": "3/4\"", "id_": 21.6},
    {"DN": "1\"",   "id_": 27.2},
    {"DN": "1.1/4\"","id_": 35.9},
    {"DN": "1.1/2\"","id_": 41.8},
    {"DN": "2\"",   "id_": 53.0},
]


# ----------------------------- SIMULTANEITY ---------------------------------
def simultaneity_coefficient(nr_consumers: int, consumer_type: str = "casnic") -> float:
    """NTPEE 2018 — coeficient simultaneitate Ks pentru blocuri/zone.

    Pentru consumatori casnici (centrale termice + aragaz):
    - 1 consumator: Ks = 1.0
    - 2–4: Ks = 0.70–0.85
    - 5–10: Ks = 0.55–0.65
    - 11–50: Ks = 0.35–0.50
    - 51–200: Ks = 0.25–0.30
    - >200: Ks = 0.20–0.22
    """
    n = max(1, int(nr_consumers))
    if consumer_type.lower().startswith("casn"):
        if n == 1: return 1.0
        if n <= 4: return round(0.85 - (n - 2) * 0.075, 3)
        if n <= 10: return round(0.65 - (n - 5) * 0.02, 3)
        if n <= 50: return round(0.50 - (n - 11) * 0.0038, 3)
        if n <= 200: return round(0.30 - (n - 51) * 0.000336, 3)
        return 0.20
    # Necasnic — Ks rămâne mai aproape de 1 (consum cvasi-permanent)
    if n == 1: return 1.0
    if n <= 3: return 0.95
    if n <= 6: return 0.90
    return 0.85


def debit_calculat(nr_consumers: int, debit_individual_mc_h: float, consumer_type: str = "casnic") -> Dict[str, Any]:
    """Q = n × q × Ks (m³/h)."""
    ks = simultaneity_coefficient(nr_consumers, consumer_type)
    q_total = round(nr_consumers * debit_individual_mc_h * ks, 3)
    return {
        "nr_consumers": nr_consumers, "debit_individual_mc_h": debit_individual_mc_h,
        "ks": ks, "debit_calculat_mc_h": q_total,
        "formula": "Q = n × q × Ks",
    }


# ----------------------------- RENOUARD --------------------------------------
def _renouard_low_pressure(s: float, L: float, Q: float, D: float) -> float:
    """ΔP (mbar) = 23200 × s × L × Q^1.82 / D^4.82. Pressure ≤ 100 mbar."""
    if D <= 0 or L <= 0 or Q <= 0:
        return 0.0
    return 23200 * s * L * (Q ** 1.82) / (D ** 4.82)


def _renouard_medium_pressure(P1_bar: float, s: float, L: float, Q: float, D: float) -> Tuple[float, float]:
    """Returns (P2_bar, delta_P_bar). P1²–P2² = 51.5 × s × L × Q^1.82 / D^4.82.

    Input P1 in bar absolute. Q in m³/h (Nm³/h at 15°C 1.013 bar).
    """
    if D <= 0 or L <= 0 or Q <= 0:
        return P1_bar, 0.0
    P1_abs = P1_bar + 1.013
    rhs = 51.5 * s * L * (Q ** 1.82) / (D ** 4.82)
    P2_sq = P1_abs ** 2 - rhs
    if P2_sq <= 0:
        return 0.0, P1_bar
    P2_abs = math.sqrt(P2_sq)
    P2_bar = round(P2_abs - 1.013, 4)
    return P2_bar, round(P1_bar - P2_bar, 4)


def pierderi_presiune(regime: str, length_m: float, debit_mc_h: float, dn_id_mm: float,
                       p1_bar: Optional[float] = None) -> Dict[str, Any]:
    """Pressure drop using the right Renouard variant.

    regime: 'joasa' (≤100 mbar) | 'medie' (>100 mbar, up to 6 bar)
    """
    s = GAS_DENSITY_RELATIVE
    if regime == "joasa":
        dp_mbar = _renouard_low_pressure(s, length_m, debit_mc_h, dn_id_mm)
        return {
            "regime": regime, "formula": "ΔP = 23200 × s × L × Q^1.82 / D^4.82  (mbar)",
            "delta_p_mbar": round(dp_mbar, 2), "delta_p_bar": round(dp_mbar / 1000, 5),
            "verdict": "OK" if dp_mbar <= 10 else "PESTE LIMITĂ (max 10 mbar pe branșament)",
            "limit_mbar": 10,
        }
    # medie
    p1 = float(p1_bar or 2.0)
    p2, dp = _renouard_medium_pressure(p1, s, length_m, debit_mc_h, dn_id_mm)
    return {
        "regime": regime, "formula": "P1² – P2² = 51.5 × s × L × Q^1.82 / D^4.82  (bar²)",
        "p1_bar": p1, "p2_bar": p2, "delta_p_bar": dp,
        "verdict": "OK" if dp <= 0.5 else "PESTE LIMITĂ (recomandat ≤0.5 bar)",
        "limit_bar": 0.5,
    }


# ----------------------------- VELOCITY -------------------------------------
def viteza_gaz(debit_mc_h: float, dn_id_mm: float, presiune_bar: float = 0.0) -> Dict[str, Any]:
    """Viteza = Q / A (m/s), corectat pentru presiune relativă.

    Aria = π × (D/2)². D[m] = id_mm/1000.
    Q_absolut = Q / (1 + P) [m³/h] la presiunea de operare.
    """
    if dn_id_mm <= 0:
        return {"error": "DN invalid"}
    D_m = dn_id_mm / 1000.0
    A = math.pi * (D_m / 2) ** 2
    Q_s = (debit_mc_h / (1.0 + max(presiune_bar, 0.0))) / 3600.0
    v = Q_s / A
    limit = 20.0 if presiune_bar < 0.1 else 30.0
    return {
        "diametru_mm": dn_id_mm, "debit_mc_h": debit_mc_h, "presiune_bar": presiune_bar,
        "viteza_m_s": round(v, 2), "limit_m_s": limit,
        "verdict": "OK" if v <= limit else "PESTE LIMITĂ",
    }


# ----------------------------- DIAMETER SIZING ------------------------------
def dimensionare_conducta(regime: str, length_m: float, debit_mc_h: float,
                           p1_bar: Optional[float] = None,
                           material: str = "PE 100 SDR 11") -> Dict[str, Any]:
    """Returnează DN recomandat (cel mai mic care satisface limitele de pierdere)."""
    table = PE100_SDR11 if material.startswith("PE") else PE100_SDR11
    candidates = []
    for row in table:
        dp = pierderi_presiune(regime, length_m, debit_mc_h, row["id_"], p1_bar)
        v = viteza_gaz(debit_mc_h, row["id_"], p1_bar or 0.0)
        ok_dp = dp.get("verdict") == "OK"
        ok_v = v.get("verdict") == "OK"
        candidates.append({
            "DN": row["DN"], "od_mm": row["od"], "id_mm": row["id_"],
            "delta_p": dp.get("delta_p_mbar") or dp.get("delta_p_bar"),
            "viteza_m_s": v["viteza_m_s"],
            "ok_dp": ok_dp, "ok_v": ok_v, "ok": ok_dp and ok_v,
        })
    recommended = next((c for c in candidates if c["ok"]), candidates[-1] if candidates else None)
    return {
        "regime": regime, "length_m": length_m, "debit_mc_h": debit_mc_h, "material": material,
        "candidates": candidates,
        "recommended": recommended,
    }


# ----------------------------- BURIAL DEPTH ---------------------------------
def validare_adancime_pozare(adancime_m: float, zona: str = "trotuar") -> Dict[str, Any]:
    """NTPEE 2018 art. 56."""
    limits = {"trafic_auto": 1.0, "trotuar": 0.9, "spatii_verzi": 0.6}
    lim = limits.get(zona, 0.9)
    return {
        "zona": zona, "adancime_m": adancime_m, "limit_min_m": lim,
        "verdict": "OK" if adancime_m >= lim else "INSUFICIENT",
        "rec_banda_avertizare_m": round(adancime_m - 0.3, 2) if adancime_m else None,
    }


# ----------------------------- TEST PRESSURES -------------------------------
def validare_probe(p_rezistenta_bar: float, p_etanseitate_bar: float, p_lucru_bar: float) -> Dict[str, Any]:
    """NTPEE 2018 cap.5:
    - Proba rezistență: 1.5 × P_max op, min 4 bar pentru PE
    - Proba etanșeitate: 1.1 × P_max op, durată ≥ 24h pentru rețele
    """
    pmax = max(p_lucru_bar, 0.1)
    pr_min = max(1.5 * pmax, 4.0)
    pe_min = 1.1 * pmax
    return {
        "p_lucru_bar": p_lucru_bar,
        "p_rezistenta_bar": p_rezistenta_bar, "rezistenta_min_bar": round(pr_min, 2),
        "rezistenta_ok": p_rezistenta_bar >= pr_min,
        "p_etanseitate_bar": p_etanseitate_bar, "etanseitate_min_bar": round(pe_min, 2),
        "etanseitate_ok": p_etanseitate_bar >= pe_min,
    }


# ----------------------------- COST -----------------------------------------
# RON per ml manopera+materiale (orientativ piață RO 2025-2026)
MATERIAL_PRICES = {
    "PE 100 SDR 11":     {25: 35, 32: 42, 40: 55, 50: 78, 63: 110, 75: 145, 90: 190, 110: 250, 125: 310, 160: 425, 200: 580},
    "PE 100 SDR 17.6":   {32: 38, 40: 50, 50: 70, 63: 100, 75: 130, 90: 170, 110: 220, 160: 380, 200: 510},
    "OL galvanizat":     {25: 80, 32: 105, 40: 140, 50: 190, 63: 260},
    "Cupru":             {18: 95, 22: 115, 28: 145, 35: 195, 42: 235, 54: 290},
}

def cost_estimativ(material: str, dn: int, length_m: float, nr_armaturi: int = 0,
                    include_post_reglare: bool = False) -> Dict[str, Any]:
    table = MATERIAL_PRICES.get(material) or {}
    # nearest DN price
    nearest = min(table.keys(), key=lambda d: abs(d - dn)) if table else None
    unit = table.get(nearest, 0)
    base = unit * max(length_m, 0)
    armaturi = nr_armaturi * 450
    post = 4500 if include_post_reglare else 0
    total = round(base + armaturi + post, 2)
    return {
        "material": material, "dn_used_for_pricing": nearest, "unit_lei_per_m": unit,
        "length_m": length_m, "cost_conducta_lei": round(base, 2),
        "nr_armaturi": nr_armaturi, "cost_armaturi_lei": armaturi,
        "cost_post_reglare_lei": post, "cost_total_estimativ_lei": total,
        "note": "Estimare orientativă, fără TVA, prețuri piață 2025-2026.",
    }


# ----------------------------- DISPATCHER -----------------------------------
def run(calc: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Single entrypoint for the calc endpoint. Returns engineering output."""
    try:
        if calc == "dimensionare_conducta":
            return dimensionare_conducta(
                regime=params.get("regime", "joasa"),
                length_m=float(params.get("length_m", 0) or 0),
                debit_mc_h=float(params.get("debit_mc_h", 0) or 0),
                p1_bar=float(params["p1_bar"]) if params.get("p1_bar") not in (None, "") else None,
                material=params.get("material", "PE 100 SDR 11"),
            )
        if calc == "pierderi_presiune":
            return pierderi_presiune(
                regime=params.get("regime", "joasa"),
                length_m=float(params.get("length_m", 0) or 0),
                debit_mc_h=float(params.get("debit_mc_h", 0) or 0),
                dn_id_mm=float(params.get("dn_id_mm", 0) or 0),
                p1_bar=float(params["p1_bar"]) if params.get("p1_bar") not in (None, "") else None,
            )
        if calc == "viteza_gaz":
            return viteza_gaz(
                debit_mc_h=float(params.get("debit_mc_h", 0) or 0),
                dn_id_mm=float(params.get("dn_id_mm", 0) or 0),
                presiune_bar=float(params.get("presiune_bar", 0) or 0),
            )
        if calc == "debit_calculat":
            return debit_calculat(
                nr_consumers=int(params.get("nr_consumers", 1) or 1),
                debit_individual_mc_h=float(params.get("debit_individual_mc_h", 0) or 0),
                consumer_type=params.get("consumer_type", "casnic"),
            )
        if calc == "simultaneity":
            return {"ks": simultaneity_coefficient(int(params.get("nr_consumers", 1) or 1), params.get("consumer_type", "casnic"))}
        if calc == "validare_adancime_pozare":
            return validare_adancime_pozare(
                adancime_m=float(params.get("adancime_m", 0) or 0),
                zona=params.get("zona", "trotuar"),
            )
        if calc == "validare_probe":
            return validare_probe(
                p_rezistenta_bar=float(params.get("p_rezistenta_bar", 0) or 0),
                p_etanseitate_bar=float(params.get("p_etanseitate_bar", 0) or 0),
                p_lucru_bar=float(params.get("p_lucru_bar", 0) or 0),
            )
        if calc == "cost_estimativ":
            return cost_estimativ(
                material=params.get("material", "PE 100 SDR 11"),
                dn=int(params.get("dn", 32) or 32),
                length_m=float(params.get("length_m", 0) or 0),
                nr_armaturi=int(params.get("nr_armaturi", 0) or 0),
                include_post_reglare=bool(params.get("include_post_reglare", False)),
            )
    except (ValueError, TypeError) as e:
        return {"error": f"Parametri invalizi: {e}"}
    return {"error": f"Calcul necunoscut: {calc}"}


AVAILABLE_CALCS = [
    {"id": "dimensionare_conducta", "label": "Dimensionare conductă (DN recomandat)"},
    {"id": "pierderi_presiune",     "label": "Pierderi de presiune (Renouard)"},
    {"id": "viteza_gaz",            "label": "Viteza gazului în conductă"},
    {"id": "debit_calculat",        "label": "Debit calculat (n × q × Ks)"},
    {"id": "simultaneity",          "label": "Coeficient simultaneitate Ks"},
    {"id": "validare_adancime_pozare", "label": "Validare adâncime pozare"},
    {"id": "validare_probe",        "label": "Validare probe rezistență/etanșeitate"},
    {"id": "cost_estimativ",        "label": "Cost estimativ (lei)"},
]

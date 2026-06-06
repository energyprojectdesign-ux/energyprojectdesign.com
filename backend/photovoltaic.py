"""Photovoltaic (FV) deep calculation module — ANRE compliant.

Surse:
- ANRE Ord. 34/2024 — Regulament racordare prosumatori/producători
- Codul tehnic al Rețelei electrice de distribuție (Codul RED)
- AOR — Asociația Operatorilor de Rețea — Ghid tehnic FV
- SR EN 50618 — Cabluri solare DC (H1Z2Z2-K)
- SR EN IEC 62548 — Sisteme PV — Cerințe de proiectare
- I7-2011 — Normativ instalații electrice

Categorii ANRE (prosumator/producător):
  - C1: instalații FV ≤ 10.8 kWp (prosumator casnic, monofazat sau trifazat)
  - C2: 10.8 kWp < P ≤ 27 kWp  (prosumator non-casnic mic, trifazat)
  - C3: 27 kWp < P ≤ 200 kWp   (producător mic, ATR obligatoriu, racord JT/MT)
  - C4: P > 200 kWp            (parc FV, racord MT/IT, studiu de soluție)
"""
from typing import Dict, List, Optional
import math


# ---------- helpers ----------
def _f(v, default=None):
    try:
        if v in (None, ""):
            return default
        return float(v)
    except (ValueError, TypeError):
        return default


# Iradiație globală orizontală anuală pentru România — medii regionale (kWh/m²/an)
# Surse: PVGIS-SARAH3 — Joint Research Centre, ec.europa.eu/pvgis
IRADIATIE_KWH_M2_AN = {
    "sud": 1450,        # Dobrogea, Bărăgan
    "sud_est": 1430,    # Constanța, Tulcea
    "sud_vest": 1380,   # Mehedinți, Dolj
    "centru": 1320,     # Transilvania
    "nord_est": 1280,   # Moldova de nord
    "nord_vest": 1300,  # Maramureș, Bihor
    "implicit": 1350,
}

# Factor de performanță (PR) — Performance Ratio mediu pentru sisteme uzuale
PR_DEFAULT = 0.78  # pierderi cabluri, invertor, mismatch, temperatură, murdărire

# Putere panou standard 2025 (Wp) — module monocristaline TOPCon/HJT
PUTERE_PANOU_DEFAULT_WP = 450

# Tensiune circuit deschis Voc panou (V) la STC
VOC_PANOU_DEFAULT = 49.5
# Coeficient temperatură Voc (%/°C) — pentru calcul tensiune max string la -10°C
COEF_TEMP_VOC = -0.0027

# Curent scurtcircuit Isc (A)
ISC_PANOU_DEFAULT = 13.8

# Tensiune nominală AC rețea (V) monofazat / trifazat
U_AC_MONO = 230
U_AC_TRI = 400

# Cosφ uzual invertor
COS_PHI = 0.95


def categorie_anre(p_kwp: float) -> Dict:
    """Determină categoria ANRE și tipul de racordare necesar."""
    if p_kwp <= 0:
        return {"categorie": "necunoscut", "label": "Date insuficiente", "tip_racord": "—", "aviz": "—"}
    if p_kwp <= 10.8:
        return {
            "categorie": "C1",
            "label": "Prosumator casnic ≤ 10.8 kWp",
            "tip_racord": "JT monofazat / trifazat",
            "aviz": "Cerere racordare simplificată (ATR + CR în max 30 zile)",
            "regim": "prosumator",
            "compensare_cantitativă": True,
        }
    if p_kwp <= 27:
        return {
            "categorie": "C2",
            "label": "Prosumator non-casnic ≤ 27 kWp",
            "tip_racord": "JT trifazat (3x400V)",
            "aviz": "ATR + studiu de soluție simplificat",
            "regim": "prosumator",
            "compensare_cantitativă": True,
        }
    if p_kwp <= 200:
        return {
            "categorie": "C3",
            "label": "Producător mic 27-200 kWp",
            "tip_racord": "JT trifazat sau MT (>100 kWp)",
            "aviz": "ATR + studiu de soluție + licență producere ANRE (>100 kWp)",
            "regim": "producator",
            "compensare_cantitativă": False,
        }
    return {
        "categorie": "C4",
        "label": "Parc FV > 200 kWp",
        "tip_racord": "MT 20 kV (sau IT pentru > 5 MW)",
        "aviz": "ATR + studiu de soluție complet + licență producere ANRE + acord mediu",
        "regim": "producator",
        "compensare_cantitativă": False,
    }


def numar_panouri(p_kwp: float, p_panou_wp: float = PUTERE_PANOU_DEFAULT_WP) -> int:
    """Rotunjire superioară la nr. întreg de panouri."""
    if p_kwp <= 0 or p_panou_wp <= 0:
        return 0
    return int(math.ceil((p_kwp * 1000) / p_panou_wp))


def dimensionare_invertor(p_kwp: float) -> Dict:
    """Invertor: 0.85 ÷ 1.10 din Pdc (overload tipic 110-120%)."""
    p_inv_min = round(p_kwp * 0.85, 2)
    p_inv_max = round(p_kwp * 1.10, 2)
    p_inv_rec = round(p_kwp * 0.95, 2)  # subdimensionare 5% standard
    return {
        "p_invertor_min_kw": p_inv_min,
        "p_invertor_max_kw": p_inv_max,
        "p_invertor_recomandat_kw": p_inv_rec,
        "raport_dc_ac": round(p_kwp / p_inv_rec, 2),
    }


def configurare_string(p_kwp: float, p_panou_wp: float, voc: float = VOC_PANOU_DEFAULT,
                       u_mppt_max: float = 1000) -> Dict:
    """Configurare module în serie (string) ținând cont de Voc la -10°C."""
    n_total = numar_panouri(p_kwp, p_panou_wp)
    if n_total == 0:
        return {"n_panouri": 0, "n_serie_max": 0, "n_string": 0}
    # Voc la -10°C cu coef. temp.
    voc_rece = voc * (1 + COEF_TEMP_VOC * (-10 - 25))  # ΔT = -35°C
    n_serie_max = int(math.floor(u_mppt_max / voc_rece))
    # Alegem string cât mai apropiat de 20 panouri în serie (optim invertoare 800-1000V)
    n_serie_optim = min(n_serie_max, max(8, int(round(n_total / max(1, math.ceil(n_total / 20))))))
    n_string = int(math.ceil(n_total / n_serie_optim)) if n_serie_optim > 0 else 0
    return {
        "n_panouri": n_total,
        "voc_rece_v": round(voc_rece, 2),
        "n_serie_max": n_serie_max,
        "n_serie_optim": n_serie_optim,
        "n_string": n_string,
        "u_string_stc_v": round(n_serie_optim * voc, 1),
    }


def sectiune_cablu_dc(i_max: float, lungime_m: float, u_string: float, caderea_max: float = 0.01) -> Dict:
    """Secțiune minimă cablu DC pentru cădere de tensiune < 1%.
    Formula: S = 2 × L × I × ρ / ΔU
    ρ_Cu = 0.0178 Ω·mm²/m
    """
    rho_cu = 0.0178
    du_admis = caderea_max * u_string
    if i_max <= 0 or lungime_m <= 0 or u_string <= 0:
        return {"sectiune_mm2": None, "caderea_pct": None}
    s_calc = (2 * lungime_m * i_max * rho_cu) / du_admis
    # Selecție secțiune standard (mm²): 4, 6, 10, 16, 25, 35
    standard = [4, 6, 10, 16, 25, 35, 50, 70, 95]
    s_std = next((s for s in standard if s >= s_calc), standard[-1])
    caderea_reala = (2 * lungime_m * i_max * rho_cu) / s_std
    return {
        "sectiune_calculata_mm2": round(s_calc, 2),
        "sectiune_standard_mm2": s_std,
        "caderea_pct": round((caderea_reala / u_string) * 100, 3),
        "tip_cablu": "H1Z2Z2-K (solar DC) 1500V",
    }


def sectiune_cablu_ac(p_kw: float, lungime_m: float, monofazat: bool = False) -> Dict:
    """Secțiune cablu AC invertor → tablou racordare.
    Trifazat: I = P / (√3 × U × cosφ)
    Monofazat: I = P / (U × cosφ)
    Cădere admisă 1.5% (NTI-TEL-007).
    """
    if p_kw <= 0 or lungime_m <= 0:
        return {"sectiune_mm2": None}
    rho_cu = 0.0178
    if monofazat:
        i = (p_kw * 1000) / (U_AC_MONO * COS_PHI)
        u = U_AC_MONO
        formula = "I = P / (U × cosφ)"
        factor = 2  # dus-întors
    else:
        i = (p_kw * 1000) / (math.sqrt(3) * U_AC_TRI * COS_PHI)
        u = U_AC_TRI
        formula = "I = P / (√3 × U × cosφ)"
        factor = math.sqrt(3)
    du_admis = 0.015 * u
    s_calc = (factor * lungime_m * i * rho_cu) / du_admis
    standard = [2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185]
    s_std = next((s for s in standard if s >= s_calc), standard[-1])
    return {
        "curent_a": round(i, 2),
        "sectiune_calculata_mm2": round(s_calc, 2),
        "sectiune_standard_mm2": s_std,
        "tip_cablu": "CYY-F sau N2XH 0.6/1 kV",
        "formula": formula,
    }


def protectii_recomandate(p_kwp: float, cat: Dict) -> List[Dict]:
    """Lista protecții obligatorii ANRE/I7."""
    prot = [
        {"nume": "Siguranțe DC string", "tip": "gPV 1000-1500V DC", "rol": "Protecție supracurent string"},
        {"nume": "Descărcător supratensiuni DC", "tip": "SPD Tip 2 DC", "rol": "Protecție trăsnet partea DC"},
        {"nume": "Descărcător supratensiuni AC", "tip": "SPD Tip 1+2 AC", "rol": "Protecție trăsnet partea AC"},
        {"nume": "Întrerupător diferențial AC", "tip": "RCD tip B 30 mA", "rol": "Protecție diferențială (curenți DC reziduali)"},
        {"nume": "Întrerupător automat AC", "tip": f"MCB curba C, In ≥ {math.ceil(p_kwp * 1.5)} A", "rol": "Protecție supracurent injecție"},
    ]
    if cat["categorie"] in ("C3", "C4"):
        prot.append({"nume": "Releu de protecție rețea", "tip": "VDE-AR-N 4105 / EN 50549-1", "rol": "Anti-islanding, U/f, ROCOF"})
        prot.append({"nume": "Smart-meter cu măsurare bidirecțională", "tip": "Cl. 1 — comunicație Modbus/M-Bus", "rol": "Telegestiune ANRE"})
    if cat["categorie"] == "C4":
        prot.append({"nume": "Celulă MT 24 kV", "tip": "Compartimentată SF6 sau aer", "rol": "Racord MT — Codul RED"})
    return prot


def productie_anuala(p_kwp: float, zona: str = "implicit", pr: float = PR_DEFAULT) -> Dict:
    """Producție anuală estimată (kWh) = P_kWp × H_kWh/m²/an × PR."""
    iradiatie = IRADIATIE_KWH_M2_AN.get(zona, IRADIATIE_KWH_M2_AN["implicit"])
    productie = p_kwp * iradiatie * pr
    return {
        "iradiatie_kwh_m2_an": iradiatie,
        "pr": pr,
        "productie_anuala_kwh": round(productie, 0),
        "productie_specifica_kwh_kwp": round(productie / p_kwp, 0) if p_kwp > 0 else 0,
        "factor_utilizare_pct": round((productie / (p_kwp * 8760)) * 100, 2) if p_kwp > 0 else 0,
    }


def calculate(data: Dict) -> Dict:
    """Run full PV calculation chain.

    Input expected:
      - p_kwp (float): puterea instalată dorită
      - p_panou_wp (optional): putere unitară panou
      - lungime_dc_m (optional): lungime cablu DC string-invertor
      - lungime_ac_m (optional): lungime cablu AC invertor-tablou
      - monofazat (bool optional)
      - zona (str optional): zona_geografica
    """
    p_kwp = _f(data.get("p_kwp"), 0) or 0
    p_panou = _f(data.get("p_panou_wp"), PUTERE_PANOU_DEFAULT_WP) or PUTERE_PANOU_DEFAULT_WP
    l_dc = _f(data.get("lungime_dc_m"), 30) or 30
    l_ac = _f(data.get("lungime_ac_m"), 15) or 15
    monofazat = bool(data.get("monofazat", False))
    zona = (data.get("zona_geografica") or "implicit").lower().replace(" ", "_")

    if p_kwp <= 0:
        return {
            "error": "P_kWp invalid",
            "status": "missing",
            "explanation": "Furnizează putere instalată > 0 kWp.",
        }

    cat = categorie_anre(p_kwp)
    string_cfg = configurare_string(p_kwp, p_panou)
    inv = dimensionare_invertor(p_kwp)
    # Curent string ≈ Isc panou (un singur rând în serie cu Isc identic)
    i_string = ISC_PANOU_DEFAULT
    cablu_dc = sectiune_cablu_dc(i_string, l_dc, string_cfg["u_string_stc_v"])
    cablu_ac = sectiune_cablu_ac(inv["p_invertor_recomandat_kw"], l_ac, monofazat=monofazat or p_kwp <= 5)
    prot = protectii_recomandate(p_kwp, cat)
    prod = productie_anuala(p_kwp, zona)

    return {
        "p_kwp": p_kwp,
        "categorie_anre": cat,
        "panouri": {
            "putere_unitara_wp": p_panou,
            "n_panouri": string_cfg["n_panouri"],
        },
        "string": string_cfg,
        "invertor": inv,
        "cablu_dc": cablu_dc,
        "cablu_ac": cablu_ac,
        "protectii": prot,
        "productie": prod,
        "status": "ok",
    }


def to_placeholders(result: Dict) -> Dict[str, str]:
    """Flatten result dict to {{placeholder}} → value pairs for DOCX templating."""
    if not result or result.get("status") != "ok":
        return {}
    out = {
        "fv_p_kwp": str(result["p_kwp"]),
        "fv_categorie_anre": result["categorie_anre"]["categorie"],
        "fv_categorie_label": result["categorie_anre"]["label"],
        "fv_tip_racord": result["categorie_anre"]["tip_racord"],
        "fv_aviz_necesar": result["categorie_anre"]["aviz"],
        "fv_regim": result["categorie_anre"]["regim"],
        "fv_n_panouri": str(result["panouri"]["n_panouri"]),
        "fv_p_panou_wp": str(result["panouri"]["putere_unitara_wp"]),
        "fv_n_string": str(result["string"]["n_string"]),
        "fv_n_serie": str(result["string"]["n_serie_optim"]),
        "fv_u_string_v": str(result["string"]["u_string_stc_v"]),
        "fv_invertor_kw": str(result["invertor"]["p_invertor_recomandat_kw"]),
        "fv_raport_dc_ac": str(result["invertor"]["raport_dc_ac"]),
        "fv_cablu_dc_mm2": str(result["cablu_dc"].get("sectiune_standard_mm2", "—")),
        "fv_cablu_dc_caderea_pct": str(result["cablu_dc"].get("caderea_pct", "—")),
        "fv_cablu_ac_mm2": str(result["cablu_ac"].get("sectiune_standard_mm2", "—")),
        "fv_cablu_ac_curent_a": str(result["cablu_ac"].get("curent_a", "—")),
        "fv_productie_anuala_kwh": str(result["productie"]["productie_anuala_kwh"]),
        "fv_productie_specifica": str(result["productie"]["productie_specifica_kwh_kwp"]),
        "fv_factor_utilizare_pct": str(result["productie"]["factor_utilizare_pct"]),
        "fv_iradiatie_kwh_m2_an": str(result["productie"]["iradiatie_kwh_m2_an"]),
    }
    # Listă protecții formatată
    out["fv_protectii_lista"] = "\n".join(
        f"- {p['nume']} ({p['tip']}): {p['rol']}" for p in result["protectii"]
    )
    return out

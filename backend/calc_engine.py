"""Smart calculation engine for technical data of natural gas projects.

Surse pentru formule:
- SR 6790 / SR EN 1775 — instalații utilizare gaze
- ANRE Ord. 89/2018 — Norme tehnice distribuție gaze naturale
- Catalog tehnic uzual PE-HD SDR11 (Wavin / Pipelife / Radius) pentru rezistențe la curgere
- Practica de proiectare uzuală a operatorilor de distribuție (Distrigaz Sud / Delgaz Grid / Engie):
  * 1 teu derivație în punctul de racordare la conductă principală
  * coliere de priză la fiecare 30 m + 1 final
  * mufe electrofuziune la fiecare ~6 m colac PE
  * 1 robinet sferic de branșament în limita proprietății
  * 1 robinet sferic post-reglare (intrare aparat)
"""
from typing import Dict, Optional, List
import math


def _f(value, default=None):
    """Safe float parse."""
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def calculate(td: Dict) -> Dict:
    """Run all smart calculations on a technical-data dict and return the results.

    Each result includes: value, formula (str), explanation, status, sources.
    """
    debit_instalat = _f(td.get("debit_instalat"))
    presiune_regim = td.get("presiune_regim")
    lungime_bransament = _f(td.get("lungime_bransament"))
    diametru_conducta_existenta = _f(td.get("diametru_conducta_existenta_mm")) or _f(td.get("diametru_conducta"))
    diametru_bransament = _f(td.get("diametru_bransament_mm")) or _f(td.get("diametru_bransament"))

    results = {}

    # Debit calculat — copy of installed value
    if debit_instalat is not None:
        results["debit_calculat_mc_h"] = {
            "value": round(debit_instalat, 2),
            "formula": "debit_calculat_mc_h = debit_instalat",
            "explanation": "Debitul calculat este egal cu debitul instalat declarat.",
            "status": "ok",
            "sources": ["debit_instalat"],
        }
    else:
        results["debit_calculat_mc_h"] = {
            "value": None, "formula": "debit_calculat_mc_h = debit_instalat",
            "explanation": "Lipsă debit_instalat.", "status": "missing", "sources": ["debit_instalat"],
        }

    # Debit recomandat — 10% margin
    if debit_instalat is not None:
        v = round(debit_instalat * 1.10, 2)
        results["debit_recomandat_mc_h"] = {
            "value": v,
            "formula": "debit_recomandat_mc_h = debit_instalat × 1.10",
            "explanation": "Debitul recomandat include o marjă tehnică de 10% peste debitul instalat.",
            "status": "ok",
            "sources": ["debit_instalat"],
        }
    else:
        results["debit_recomandat_mc_h"] = {
            "value": None, "formula": "debit_instalat × 1.10",
            "explanation": "Lipsă debit_instalat.", "status": "missing", "sources": ["debit_instalat"],
        }

    # Putere instalată kW — factor 10.6
    if debit_instalat is not None:
        v = round(debit_instalat * 10.6, 2)
        results["putere_instalata_kw"] = {
            "value": v,
            "formula": "putere_instalata_kw = debit_instalat × 10.6",
            "explanation": "Putere termică instalată estimată (PCI gaz natural ≈ 10.6 kWh/mc).",
            "status": "ok",
            "sources": ["debit_instalat"],
        }
    else:
        results["putere_instalata_kw"] = {
            "value": None, "formula": "debit_instalat × 10.6",
            "explanation": "Lipsă debit_instalat.", "status": "missing", "sources": ["debit_instalat"],
        }

    # Risc presiune
    if presiune_regim in (None, ""):
        results["risc_presiune"] = {
            "value": "presiune lipsă",
            "formula": "if presiune_regim missing → presiune lipsă",
            "explanation": "Nu este declarat regimul de presiune. Completați câmpul.",
            "status": "missing", "sources": ["presiune_regim"],
        }
    elif lungime_bransament is not None and lungime_bransament > 30:
        results["risc_presiune"] = {
            "value": "verificare presiune necesară",
            "formula": "if lungime_bransament > 30m → verificare necesară",
            "explanation": "Branșament lung — verificare suplimentară a pierderii de presiune.",
            "status": "warning",
            "sources": ["presiune_regim", "lungime_bransament"],
        }
    else:
        results["risc_presiune"] = {
            "value": "normal",
            "formula": "altfel → normal",
            "explanation": "Regimul de presiune se încadrează în parametri normali.",
            "status": "ok",
            "sources": ["presiune_regim", "lungime_bransament"],
        }

    # Estimare cost branșament — 120 RON/m
    if lungime_bransament is not None:
        v = round(lungime_bransament * 120.0, 2)
        results["estimare_cost"] = {
            "value": v,
            "formula": "estimare_cost = lungime_bransament × 120 RON",
            "explanation": "Cost orientativ de bază pentru execuția branșamentului. Nu include avize, post reglare, contor sau TVA.",
            "status": "ok",
            "sources": ["lungime_bransament"],
            "unit": "RON",
        }
    else:
        results["estimare_cost"] = {
            "value": None, "formula": "lungime_bransament × 120",
            "explanation": "Lipsă lungime_bransament.", "status": "missing", "sources": ["lungime_bransament"], "unit": "RON",
        }

    # Recomandare contor
    if debit_instalat is None:
        results["contor_orientativ"] = {
            "value": None, "formula": "table(debit_instalat)",
            "explanation": "Lipsă debit_instalat.", "status": "missing", "sources": ["debit_instalat"],
        }
    elif debit_instalat <= 6:
        results["contor_orientativ"] = {"value": "G4", "formula": "debit ≤ 6 → G4", "explanation": "Contor recomandat G4 pentru consumatori casnici uzuali.", "status": "ok", "sources": ["debit_instalat"]}
    elif debit_instalat <= 10:
        results["contor_orientativ"] = {"value": "G6", "formula": "6 < debit ≤ 10 → G6", "explanation": "Contor recomandat G6 pentru consum mediu.", "status": "ok", "sources": ["debit_instalat"]}
    elif debit_instalat <= 16:
        results["contor_orientativ"] = {"value": "G10", "formula": "10 < debit ≤ 16 → G10", "explanation": "Contor recomandat G10 pentru consum ridicat.", "status": "ok", "sources": ["debit_instalat"]}
    else:
        results["contor_orientativ"] = {"value": "verificare dimensionare contor", "formula": "debit > 16 → verificare", "explanation": "Debit mare — dimensionarea contorului trebuie verificată de inginer specializat.", "status": "warning", "sources": ["debit_instalat"]}

    # ---------------------------------------------------------------------
    # FITTINGURI BRANȘAMENT (port din legacy V3 — Energy-Project-Design)
    # ---------------------------------------------------------------------
    material = (td.get("material_conducta") or "").upper()

    # Numar teu derivație: 1 în punctul de racord la conducta principală
    results["nr_teu_derivatie"] = {
        "value": 1 if lungime_bransament is not None else None,
        "formula": "nr_teu_derivatie = 1 (punct racord conductă principală)",
        "explanation": "Un teu de derivație electrofuziune se montează în punctul de racordare la conducta de distribuție existentă.",
        "status": "ok" if lungime_bransament is not None else "missing",
        "sources": ["lungime_bransament"],
        "unit": "buc",
    }

    # Numar mufe electrofuziune: 1 la fiecare 6m (colac PE-HD standard de 100m fragmentat practic la 6m)
    if lungime_bransament is not None:
        n_mufe = max(2, int(math.ceil(lungime_bransament / 6.0)) + 1)
        results["nr_mufe_electrofuziune"] = {
            "value": n_mufe,
            "formula": "nr_mufe = ceil(lungime_bransament / 6) + 1 (min. 2)",
            "explanation": "Mufe electrofuziune PE-HD pentru îmbinări la fiecare 6 m de traseu, plus o mufă la intrarea în nișa de branșament.",
            "status": "ok",
            "sources": ["lungime_bransament"],
            "unit": "buc",
        }
    else:
        results["nr_mufe_electrofuziune"] = {"value": None, "formula": "ceil(lungime/6)+1", "explanation": "Lipsă lungime_bransament.", "status": "missing", "sources": ["lungime_bransament"], "unit": "buc"}

    # Coliere de priză / repere semnalizare
    if lungime_bransament is not None:
        n_coliere = max(2, int(math.ceil(lungime_bransament / 30.0)) + 1)
        results["nr_coliere_priza"] = {
            "value": n_coliere,
            "formula": "nr_coliere = ceil(lungime_bransament / 30) + 1 (min. 2)",
            "explanation": "Coliere de priză / repere de semnalizare semnalizare a traseului PE-HD, la fiecare 30 m + un colier final.",
            "status": "ok",
            "sources": ["lungime_bransament"],
            "unit": "buc",
        }
    else:
        results["nr_coliere_priza"] = {"value": None, "formula": "ceil(lungime/30)+1", "explanation": "Lipsă lungime_bransament.", "status": "missing", "sources": ["lungime_bransament"], "unit": "buc"}

    # Robinet sferic branșament (limita proprietății) + robinet post-reglare
    if lungime_bransament is not None:
        results["nr_robineti_bransament"] = {
            "value": 2,
            "formula": "nr_robineti = 1 (limita prop.) + 1 (post reglare)",
            "explanation": "Un robinet sferic de branșament montat în limita proprietății (nișa de branșament) și unul după regulator (intrare aparat consumator).",
            "status": "ok",
            "sources": ["lungime_bransament"],
            "unit": "buc",
        }
    else:
        results["nr_robineti_bransament"] = {"value": None, "formula": "1+1", "explanation": "Lipsă lungime_bransament.", "status": "missing", "sources": ["lungime_bransament"], "unit": "buc"}

    # Reductie diametru — apare doar dacă diametrele diferă
    if diametru_conducta_existenta is not None and diametru_bransament is not None and diametru_conducta_existenta != diametru_bransament:
        results["nr_reductii"] = {
            "value": 1,
            "formula": "if D_existent != D_bransament → 1 reducție electrofuziune",
            "explanation": "O reducție electrofuziune PE-HD între conducta existentă și branșament (diametre diferite).",
            "status": "ok",
            "sources": ["diametru_conducta", "diametru_bransament"],
            "unit": "buc",
        }
    else:
        results["nr_reductii"] = {
            "value": 0 if (diametru_conducta_existenta is not None and diametru_bransament is not None) else None,
            "formula": "if D_existent == D_bransament → 0",
            "explanation": "Diametre identice — fără reducție.",
            "status": "ok" if diametru_conducta_existenta is not None else "missing",
            "sources": ["diametru_conducta", "diametru_bransament"],
            "unit": "buc",
        }

    # Coturi 90° estimative — funcție de lungime (1 cot la fiecare ~25m pentru obstacole/schimbări direcție)
    if lungime_bransament is not None:
        n_coturi = max(1, int(math.ceil(lungime_bransament / 25.0)))
        results["nr_coturi_90"] = {
            "value": n_coturi,
            "formula": "nr_coturi = ceil(lungime / 25) (min. 1)",
            "explanation": "Coturi electrofuziune PE-HD 90° estimate pentru schimbări de direcție pe traseu (intrare nișă, ocoliri).",
            "status": "ok",
            "sources": ["lungime_bransament"],
            "unit": "buc",
        }
    else:
        results["nr_coturi_90"] = {"value": None, "formula": "ceil(lungime/25)", "explanation": "Lipsă lungime_bransament.", "status": "missing", "sources": ["lungime_bransament"], "unit": "buc"}

    # Material conductă — recomandare automată după presiune
    if material:
        results["material_recomandat"] = {
            "value": material,
            "formula": "material declarat de utilizator",
            "explanation": f"Material declarat: {material}.",
            "status": "ok",
            "sources": ["material_conducta"],
        }
    elif presiune_regim:
        pr = presiune_regim.upper().replace(" ", "")
        if "MP" in pr or "MEDIE" in pr or "MEDIU" in pr:
            mat = "OL (oțel) sau PE-HD SDR11 PE100"
        else:
            mat = "PE-HD SDR11 PE100"
        results["material_recomandat"] = {
            "value": mat,
            "formula": "if presiune == redusă → PE-HD; if medie → OL/PE-HD",
            "explanation": "Material recomandat funcție de regim presiune.",
            "status": "ok",
            "sources": ["presiune_regim"],
        }
    else:
        results["material_recomandat"] = {
            "value": "PE-HD SDR11 PE100",
            "formula": "default → PE-HD SDR11 PE100",
            "explanation": "Material implicit pentru branșamente presiune redusă.",
            "status": "ok",
            "sources": [],
        }

    return results

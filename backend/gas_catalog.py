"""Gas Natural — multi-country / multi-subdomain catalog.

Source of truth for the Gas Natural Studio. Designed as a TEMPLATE that can be
cloned 1:1 for any industry (electricity, water, photovoltaics, telecom, etc.)
in any country (RO today; MD, BG, RS, UA pluggable tomorrow).

Architecture:
- `CATALOG[country][industry][subdomain]` returns a subdomain blueprint.
- A blueprint contains: meta + ordered list of `phases`.
- A phase contains: id, name, norm (legal reference), description, fields,
  deliverables, recipients (default authorities), calc_keys (formulas to run).

The frontend reads this schema and renders a wizard. The backend uses the
same schema to validate, compute, store and dispatch emails.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

# ----------------------------- COUNTRIES ------------------------------
COUNTRIES: Dict[str, Dict[str, Any]] = {
    "RO": {"code": "RO", "name": "România", "currency": "RON", "locale": "ro-RO", "active": True},
    "MD": {"code": "MD", "name": "Moldova", "currency": "MDL", "locale": "ro-MD", "active": False},
    "BG": {"code": "BG", "name": "Bulgaria", "currency": "BGN", "locale": "bg-BG", "active": False},
    "RS": {"code": "RS", "name": "Serbia",   "currency": "RSD", "locale": "sr-RS", "active": False},
    "UA": {"code": "UA", "name": "Ucraina",  "currency": "UAH", "locale": "uk-UA", "active": False},
}

# ----------------------------- AUTHORITIES (RO) ------------------------
# Default recipients used by the email-dispatch logic. The user may override
# specific addresses per project in their profile.
RECIPIENT_ROLES = {
    "beneficiar":  {"label": "Beneficiar", "description": "Titularul lucrării"},
    "primarie":    {"label": "Primărie / Consiliu Local", "description": "Emitent CU + AC"},
    "osd":         {"label": "OSD (Distribuție gaze)", "description": "Distrigaz Sud / Delgaz Grid / Premier Energy"},
    "isc":         {"label": "ISC — Inspectoratul de Stat în Construcții", "description": "Aviz tehnic, verificări execuție"},
    "anre":        {"label": "ANRE", "description": "Autoritatea Națională de Reglementare în Energie"},
    "mediu":       {"label": "APM — Mediu", "description": "Aviz mediu"},
    "iscir":       {"label": "ISCIR", "description": "Pentru centrale termice & instalații sub presiune"},
    "verificator": {"label": "Verificator de proiect (VGD)", "description": "Verificare independentă"},
    "rte":         {"label": "Responsabil tehnic execuție", "description": "Atestat MDLPA"},
    "executant":   {"label": "Firmă executantă", "description": "Autorizație ANRE EDD"},
    "proiectant":  {"label": "Proiectant", "description": "Atestat ANRE PDD"},
}

# ----------------------------- FIELD TYPES (reusable) ------------------
def f(key: str, label: str, **kw) -> Dict[str, Any]:
    return {"key": key, "label": label, **kw}


def num(key: str, label: str, unit: str = "", **kw) -> Dict[str, Any]:
    return {"key": key, "label": label, "type": "number", "unit": unit, **kw}


# ============================================================================
# SHARED PHASE BUILDERS — used by every subdomain to avoid duplication.
# ============================================================================
def _phase_tema(specific_fields: Optional[List[Dict]] = None) -> Dict[str, Any]:
    return {
        "id": "tema", "order": 1,
        "name": "1. Temă de proiectare",
        "short": "Date inițiale",
        "norm": "HG 907/2016 art.4",
        "description": "Date inițiale: beneficiar, locație, scop, consum estimat.",
        "deliverables": ["Tema de proiectare semnată", "Date cadastrale", "Memoriu de necesitate"],
        "recipients_default": ["beneficiar", "proiectant"],
        "fields": [
            f("beneficiar_nume", "Beneficiar (nume/denumire)", type="text", required=True),
            f("beneficiar_cnp_cui", "CNP / CUI", type="text", required=True),
            f("beneficiar_telefon", "Telefon beneficiar", type="text"),
            f("beneficiar_email", "Email beneficiar", type="email"),
            f("beneficiar_adresa", "Adresă fiscală beneficiar", type="text"),
            f("loc_consum_adresa", "Adresă loc de consum", type="text", required=True),
            f("loc_consum_cadastru", "Nr. cadastral / CF", type="text"),
            f("loc_consum_judet", "Județ", type="text", required=True),
            f("loc_consum_localitate", "Localitate", type="text", required=True),
            f("loc_consum_strada", "Stradă + număr", type="text"),
            f("data_solicitare", "Data solicitare", type="date"),
            *(specific_fields or []),
        ],
        "calc_keys": [],
    }


def _phase_sf(extra: Optional[List[Dict]] = None) -> Dict[str, Any]:
    return {
        "id": "sf", "order": 2,
        "name": "2. Studiu de fezabilitate",
        "short": "SF",
        "norm": "HG 907/2016 anexa 4",
        "description": "Soluție tehnico-economică optimă; justifică investiția.",
        "deliverables": ["SF DOCX/PDF", "Plan situație", "Estimare costuri", "Indicatori tehnico-economici"],
        "recipients_default": ["beneficiar"],
        "fields": [
            f("sf_solutie_tehnica", "Soluție tehnică (variantă optimă)", type="textarea"),
            num("sf_lungime_conducta_m", "Lungime conductă", unit="m"),
            f("sf_material_conducta", "Material conductă", type="select",
              options=["PE 100 SDR 11", "PE 100 SDR 17.6", "OL galvanizat", "Cupru", "Inox"]),
            f("sf_diametru_nominal_DN", "Diametru nominal (DN/mm)", type="text"),
            num("sf_presiune_max_op_bar", "Presiune max. operare", unit="bar"),
            num("sf_cost_estimat_lei", "Cost estimat (fără TVA)", unit="lei"),
            num("sf_durata_executie_luni", "Durată estimată execuție", unit="luni"),
            *(extra or []),
        ],
        "calc_keys": ["dimensionare_conducta", "cost_estimativ"],
    }


def _phase_cu() -> Dict[str, Any]:
    return {
        "id": "cu", "order": 3,
        "name": "3. Certificat de urbanism & avize",
        "short": "CU + Avize",
        "norm": "L 50/1991 art. 6, ANRE Ord. 89/2018",
        "description": "Obținere CU, avize ANRE, ISC, Mediu, OSD.",
        "deliverables": ["CU emis", "ATR — Aviz Tehnic Racordare", "Aviz ISC", "Aviz mediu"],
        "recipients_default": ["primarie", "osd", "isc", "mediu"],
        "fields": [
            f("cu_numar", "Nr. CU", type="text", required=True),
            f("cu_data_emitere", "Data emiterii CU", type="date"),
            num("cu_valabilitate_luni", "Valabilitate CU", unit="luni"),
            f("cu_emitent", "Emitent (primărie/cons. județean)", type="text"),
            f("atr_numar", "Nr. ATR (aviz tehnic racordare)", type="text"),
            f("atr_osd", "OSD", type="select",
              options=["Distrigaz Sud (ENGIE)", "Delgaz Grid (E.ON)", "Premier Energy", "Salgaz", "TG Mureș", "Altul"]),
            f("atr_data", "Data ATR", type="date"),
            f("avize_obtinute", "Avize obținute (listă cu nr+data)", type="textarea",
              placeholder="ex: ISC nr.X/2026; Mediu nr.Y/2026; Apa Canal nr.Z/2026"),
        ],
        "calc_keys": [],
    }


def _phase_dtac() -> Dict[str, Any]:
    return {
        "id": "dtac", "order": 4,
        "name": "4. DTAC — Documentație autorizare construcție",
        "short": "DTAC",
        "norm": "L 50/1991 + Ord. MDLPA 839/2009",
        "description": "Documentația tehnică pentru obținerea Autorizației de Construire.",
        "deliverables": ["Piese scrise DTAC", "Plan situație 1:500", "Plan încadrare 1:5000", "Memoriu tehnic", "Devize"],
        "recipients_default": ["primarie", "verificator"],
        "fields": [
            f("dtac_proiectant_general", "Proiectant general (firmă)", type="text", required=True),
            f("dtac_proiectant_specialitate", "Proiectant de specialitate (gaze)", type="text", required=True),
            f("dtac_atestat_proiectant", "Atestat ANRE PDD (nr.)", type="text", required=True),
            f("dtac_verificator_vgd", "Verificator VGD (nume + atestat)", type="text"),
            f("dtac_data_intocmire", "Data întocmire DTAC", type="date"),
            f("dtac_memoriu_tehnic", "Sinteză memoriu tehnic", type="textarea"),
            f("dtac_planuri_anexate", "Planuri anexate (lista)", type="textarea"),
        ],
        "calc_keys": [],
    }


def _phase_ac() -> Dict[str, Any]:
    return {
        "id": "ac", "order": 5,
        "name": "5. Autorizație de construire",
        "short": "AC",
        "norm": "L 50/1991",
        "description": "AC emis în baza DTAC + avize.",
        "deliverables": ["AC scanat", "Anexe AC", "Dovada taxelor"],
        "recipients_default": ["beneficiar", "primarie"],
        "fields": [
            f("ac_numar", "Nr. Autorizație de Construire", type="text", required=True),
            f("ac_data_emitere", "Data emiterii AC", type="date", required=True),
            num("ac_valabilitate_luni", "Valabilitate", unit="luni"),
            num("ac_termen_executie", "Termen execuție", unit="luni"),
            f("ac_emitent", "Emitent AC", type="text"),
            num("ac_taxa_lei", "Taxă AC plătită", unit="lei"),
        ],
        "calc_keys": [],
    }


def _phase_pt(extra: Optional[List[Dict]] = None) -> Dict[str, Any]:
    return {
        "id": "pt", "order": 6,
        "name": "6. Proiect tehnic (PT)",
        "short": "PT",
        "norm": "HG 907/2016 anexa 5 + NTPEE 2018 cap.3",
        "description": "Proiectul tehnic de execuție: dezvoltarea soluției aprobate.",
        "deliverables": ["Piese scrise PT", "Piese desenate", "Caiete de sarcini", "Liste cantități"],
        "recipients_default": ["verificator", "beneficiar"],
        "fields": [
            f("pt_revizia", "Revizia PT", type="text", placeholder="rev. 0"),
            num("pt_numar_planse", "Număr planșe"),
            f("pt_calcul_dimensionare", "Sinteză calcul dimensionare", type="textarea"),
            num("pt_pierderi_presiune_bar", "Pierderi presiune calculate", unit="bar"),
            f("pt_lista_materiale", "Listă materiale principale", type="textarea"),
            f("pt_lista_utilaje", "Listă utilaje/aparate", type="textarea"),
            f("pt_caiet_sarcini", "Sinteză caiet de sarcini", type="textarea"),
            *(extra or []),
        ],
        "calc_keys": ["dimensionare_conducta", "viteza_gaz", "pierderi_presiune"],
    }


def _phase_de() -> Dict[str, Any]:
    return {
        "id": "de", "order": 7,
        "name": "7. Detalii de execuție (DE)",
        "short": "DE",
        "norm": "NTPEE 2018 art.34",
        "description": "Detalii necesare montajului: noduri, tăieturi, conexiuni.",
        "deliverables": ["Detalii branșament", "Detalii post reglare", "Detalii pozare", "Detalii ancoraje"],
        "recipients_default": ["executant"],
        "fields": [
            f("de_detalii_bransament", "Detalii branșament", type="textarea"),
            f("de_detalii_post_reglare", "Post de reglare (specificații)", type="textarea"),
            f("de_detalii_pozare", "Detalii pozare (adâncime, pat nisip, bandă avertizare)", type="textarea"),
            f("de_detalii_ancoraje", "Ancoraje, traversări, protejări", type="textarea"),
            num("de_adancime_pozare_m", "Adâncime pozare", unit="m"),
            num("de_inaltime_banda_avertizare_m", "Înălțime bandă avertizare deasupra conductei", unit="m"),
        ],
        "calc_keys": ["validare_adancime_pozare"],
    }


def _phase_executie() -> Dict[str, Any]:
    return {
        "id": "executie", "order": 8,
        "name": "8. Execuție lucrări (șantier)",
        "short": "Execuție",
        "norm": "NTPEE 2018 cap.4 + L 10/1995",
        "description": "Execuția propriu-zisă: trasare, săpături, pozare, sudare, probe.",
        "deliverables": ["Buletine sudori", "Certificate materiale", "Foi parcurs zilnice", "Foto-document"],
        "recipients_default": ["osd", "isc", "rte"],
        "fields": [
            f("exec_firma", "Firmă executantă (autorizație ANRE EDD)", type="text", required=True),
            f("exec_atestat_edd", "Nr. atestat ANRE EDD", type="text"),
            f("exec_data_start", "Data începere șantier", type="date"),
            f("exec_data_terminare", "Data terminare lucrări", type="date"),
            f("exec_responsabil_tehnic", "Responsabil tehnic execuție (RTE)", type="text"),
            f("exec_diriginte_santier", "Diriginte șantier (nume + nr. atestat)", type="text"),
            f("exec_certificate_materiale", "Certificate calitate materiale", type="textarea"),
            f("exec_buletine_sudori", "Buletine sudori autorizați", type="textarea"),
        ],
        "calc_keys": [],
    }


def _phase_probe() -> Dict[str, Any]:
    return {
        "id": "probe", "order": 9,
        "name": "9. Probe & verificări",
        "short": "Probe",
        "norm": "NTPEE 2018 cap.5",
        "description": "Probe etanșeitate, rezistență, controale ITP/RTE.",
        "deliverables": ["PV probe etanșeitate", "PV probe rezistență", "Buletine analize"],
        "recipients_default": ["osd", "isc"],
        "fields": [
            num("proba_rezistenta_bar", "Proba de rezistență", unit="bar"),
            num("proba_rezistenta_durata_min", "Durată proba rezistență", unit="min"),
            num("proba_etanseitate_bar", "Proba de etanșeitate", unit="bar"),
            num("proba_etanseitate_durata_h", "Durată proba etanșeitate", unit="ore"),
            f("proba_rezultat", "Rezultat probe", type="select", options=["Admis", "Admis cu observații", "Respins"]),
            f("proba_observatii", "Observații", type="textarea"),
        ],
        "calc_keys": ["validare_probe"],
    }


def _phase_receptie() -> Dict[str, Any]:
    return {
        "id": "receptie", "order": 10,
        "name": "10. Recepție & Carte tehnică",
        "short": "Recepție",
        "norm": "HG 273/1994 + Ord. MLPAT 770/1997",
        "description": "PV recepție la terminarea lucrărilor + cartea tehnică a construcției.",
        "deliverables": ["PVRT", "Cartea tehnică (A,B,C,D)", "Documentație as-built", "Predare la beneficiar"],
        "recipients_default": ["beneficiar", "primarie", "osd"],
        "fields": [
            f("receptie_pv_numar", "Nr. PV recepție terminare lucrări", type="text"),
            f("receptie_pv_data", "Data PVRT", type="date"),
            f("receptie_comisia", "Comisia (membri)", type="textarea"),
            f("carte_tehnica_volume", "Volume cartea tehnică", type="textarea",
              placeholder="Sec.A: doc. proiectare; Sec.B: doc. execuție; Sec.C: doc. recepție; Sec.D: urmărire în timp"),
            f("as_built_anexat", "Documentație as-built anexată", type="select", options=["Da", "Nu"]),
        ],
        "calc_keys": [],
    }


def _phase_pif() -> Dict[str, Any]:
    return {
        "id": "pif", "order": 11,
        "name": "11. Punere în funcțiune (PIF)",
        "short": "PIF",
        "norm": "NTPEE 2018 art.78 + Ord. ANRE 162/2021",
        "description": "PIF efectivă: cuplare la rețea, încercare funcționare, alimentare beneficiar.",
        "deliverables": ["PV PIF semnat OSD", "Contract furnizare", "Notificare consumator"],
        "recipients_default": ["beneficiar", "osd", "anre"],
        "fields": [
            f("pif_data", "Data punere în funcțiune", type="date"),
            f("pif_osd", "OSD prezent la PIF", type="text"),
            f("pif_responsabil_osd", "Responsabil OSD (nume)", type="text"),
            f("pif_contor_serie", "Serie contor montat", type="text"),
            num("pif_contor_index_initial", "Index inițial contor", unit="m³"),
            f("pif_contract_furnizare", "Nr. contract furnizare gaze", type="text"),
            f("pif_observatii", "Observații finale", type="textarea"),
        ],
        "calc_keys": [],
    }


# ============================================================================
# SUBDOMAIN BUILDERS — each branch of Gas Natural has its own variant.
# ============================================================================

def _sub_bransament_casnic() -> Dict[str, Any]:
    """Branșament casnic — apartament/casă individuală, presiune joasă (≤100 mbar)."""
    return {
        "id": "bransament-casnic",
        "name": "Branșament casnic",
        "short": "Casnic",
        "category": "branșament",
        "regime": "presiune joasă (≤100 mbar)",
        "max_debit_mc_h": 6.0,
        "typical_appliances": ["aragaz 4 ochiuri (~1.2 m³/h)", "centrală termică <40 kW (~4.5 m³/h)", "boiler instant"],
        "description": "Racordare aparat consum gaz natural pentru locuință individuală sau apartament.",
        "documents_required": [
            "Act proprietate", "Plan cadastral", "Schiță arhitect",
            "Acord vecini (la case)", "CI beneficiar"
        ],
        "phases": [
            _phase_tema([
                num("nr_aparate_consum", "Număr aparate consum"),
                num("debit_estimat_mc_h", "Debit total estimat", unit="m³/h"),
            ]),
            _phase_sf(),
            _phase_cu(),
            _phase_dtac(),
            _phase_ac(),
            _phase_pt([
                num("pt_debit_calculat_mc_h", "Debit calculat (cu Ks)", unit="m³/h"),
                num("pt_viteza_gaz_m_s", "Viteza gazului în conductă", unit="m/s"),
            ]),
            _phase_de(),
            _phase_executie(),
            _phase_probe(),
            _phase_receptie(),
            _phase_pif(),
        ],
    }


def _sub_bransament_necasnic() -> Dict[str, Any]:
    """Branșament necasnic — comercial/industrial, presiune medie."""
    return {
        "id": "bransament-necasnic",
        "name": "Branșament necasnic (comercial/industrial)",
        "short": "Necasnic",
        "category": "branșament",
        "regime": "presiune redusă (0.1–2 bar) sau medie (2–6 bar)",
        "max_debit_mc_h": 500.0,
        "typical_appliances": ["centrale termice >100 kW", "cuptoare industriale", "uscătoare"],
        "description": "Racordare consumator necasnic: restaurant, hotel, hală, fabrică, uscătorie.",
        "documents_required": [
            "Acte societate (CUI + certificat ONRC)",
            "Plan tehnologic + listă aparate consum",
            "Studiu de impact (dacă debit > 50 m³/h)",
            "Aviz ISCIR pentru cazane sub presiune",
        ],
        "phases": [
            _phase_tema([
                num("nr_aparate_consum", "Număr aparate consum"),
                num("debit_estimat_mc_h", "Debit total estimat", unit="m³/h"),
                num("putere_termica_kw", "Putere termică totală", unit="kW"),
                f("regim_lucru", "Regim funcționare", type="select",
                  options=["8h/zi", "16h/zi", "24/7"]),
            ]),
            _phase_sf([
                num("sf_consum_anual_mc", "Consum anual estimat", unit="m³/an"),
            ]),
            _phase_cu(),
            _phase_dtac(),
            _phase_ac(),
            _phase_pt([
                num("pt_debit_calculat_mc_h", "Debit calculat cu Ks", unit="m³/h"),
                num("pt_presiune_intrare_bar", "Presiune intrare post reglare", unit="bar"),
                num("pt_presiune_iesire_bar", "Presiune ieșire post reglare", unit="bar"),
                num("pt_viteza_gaz_m_s", "Viteza gazului", unit="m/s"),
            ]),
            _phase_de(),
            _phase_executie(),
            _phase_probe(),
            _phase_receptie(),
            _phase_pif(),
        ],
    }


def _sub_extindere_retea() -> Dict[str, Any]:
    """Extindere rețea de distribuție gaze naturale (presiune redusă/medie)."""
    return {
        "id": "extindere-retea",
        "name": "Extindere rețea distribuție",
        "short": "Extindere",
        "category": "rețea",
        "regime": "presiune redusă (0.1–2 bar) / medie (2–6 bar)",
        "max_debit_mc_h": 5000.0,
        "description": "Extindere rețea pe străzi noi, cartiere noi, parcuri industriale.",
        "documents_required": [
            "HCL aprobare extindere",
            "Studiu de piață + nr. consumatori potențiali",
            "Plan urbanistic zonal (PUZ)",
            "Avize: Apa, Canal, Termoficare, Electric, Telecom",
        ],
        "phases": [
            _phase_tema([
                num("lungime_propusa_m", "Lungime extindere propusă", unit="m"),
                num("nr_consumatori_potentiali", "Nr. consumatori potențiali"),
                num("debit_total_zona_mc_h", "Debit total estimat zonă", unit="m³/h"),
            ]),
            _phase_sf([
                num("sf_lungime_principala_m", "Lungime conductă principală", unit="m"),
                num("sf_lungime_secundara_m", "Lungime conductă secundară", unit="m"),
                num("sf_nr_armaturi", "Nr. armături propuse"),
            ]),
            _phase_cu(),
            _phase_dtac(),
            _phase_ac(),
            _phase_pt([
                num("pt_diametru_principala_mm", "Diametru conductă principală", unit="mm"),
                num("pt_diametru_secundara_mm", "Diametru conductă secundară", unit="mm"),
                num("pt_pierderi_presiune_max_bar", "Pierderi presiune max. la consumator", unit="bar"),
            ]),
            _phase_de(),
            _phase_executie(),
            _phase_probe(),
            _phase_receptie(),
            _phase_pif(),
        ],
    }


def _sub_instalatie_utilizare() -> Dict[str, Any]:
    """Instalație de utilizare gaze interioară (după contor)."""
    return {
        "id": "instalatie-utilizare",
        "name": "Instalație de utilizare interioară",
        "short": "Utilizare",
        "category": "instalație interioară",
        "regime": "presiune joasă (după contor, ~20 mbar)",
        "max_debit_mc_h": 12.0,
        "description": "Toate țevile + aparate consum din interiorul clădirii, după contorul/postul de reglare.",
        "documents_required": [
            "Schiță arhitect cu poziționare aparate",
            "Certificate aparate (CE + ISCIR pentru centrale)",
            "Aviz coș fum (dacă e cazul)",
        ],
        "phases": [
            _phase_tema([
                num("nr_aparate", "Nr. aparate consum"),
                f("tip_centrala", "Tip centrală termică", type="select",
                  options=["nu", "Atmosferică", "Etanșă (turbo)", "Condensare"]),
                num("debit_total_mc_h", "Debit total instalație", unit="m³/h"),
            ]),
            _phase_sf(),
            _phase_cu(),
            _phase_dtac(),
            _phase_ac(),
            _phase_pt([
                num("pt_lungime_interior_m", "Lungime conductă interior", unit="m"),
                num("pt_diametru_mm", "Diametru conductă (Cu/OL)", unit="mm"),
                f("pt_material", "Material conductă", type="select", options=["OL galvanizat", "Cupru", "Inox flexibil"]),
                num("pt_volum_incapere_mc", "Volum încăpere cu aparat consum", unit="m³"),
            ]),
            _phase_de(),
            _phase_executie(),
            _phase_probe(),
            _phase_receptie(),
            _phase_pif(),
        ],
    }


def _sub_modernizare_retea() -> Dict[str, Any]:
    """Modernizare/înlocuire rețea existentă."""
    return {
        "id": "modernizare-retea",
        "name": "Modernizare rețea existentă",
        "short": "Modernizare",
        "category": "rețea",
        "regime": "variabil (în funcție de rețeaua existentă)",
        "max_debit_mc_h": 5000.0,
        "description": "Înlocuire conducte OL vechi cu PE, redimensionare, mutare trasee.",
        "documents_required": [
            "Plan rețea existentă (as-built)",
            "Studiu cauze înlocuire (uzură, fisurare, debit insuficient)",
            "Programare oprire alimentare zonă",
        ],
        "phases": [
            _phase_tema([
                num("lungime_inlocuita_m", "Lungime de înlocuit", unit="m"),
                f("material_vechi", "Material conductă veche", type="select", options=["OL", "Fonta", "PE 80", "Mix"]),
                f("material_nou", "Material conductă nouă", type="select", options=["PE 100 SDR 11", "PE 100 SDR 17.6"]),
            ]),
            _phase_sf(),
            _phase_cu(),
            _phase_dtac(),
            _phase_ac(),
            _phase_pt(),
            _phase_de(),
            _phase_executie(),
            _phase_probe(),
            _phase_receptie(),
            _phase_pif(),
        ],
    }


# ============================================================================
# MASTER CATALOG
# ============================================================================
CATALOG: Dict[str, Dict[str, Dict[str, Dict[str, Any]]]] = {
    "RO": {
        "gaze-naturale": {
            "meta": {
                "country": "RO",
                "industry_id": "gaze-naturale",
                "industry_name": "Gaze naturale",
                "regulator": "ANRE",
                "primary_norms": [
                    "Legea 123/2012 — energia electrică și gaze naturale",
                    "NTPEE 2018 — Normele tehnice ANRE",
                    "HG 907/2016 — etapele de elaborare a documentațiilor tehnico-economice",
                    "Legea 50/1991 — autorizarea executării lucrărilor de construcții",
                    "Ord. ANRE 89/2018 — accesul la sistem",
                    "Ord. ANRE 162/2021 — PIF",
                ],
            },
            "bransament-casnic": _sub_bransament_casnic(),
            "bransament-necasnic": _sub_bransament_necasnic(),
            "extindere-retea": _sub_extindere_retea(),
            "instalatie-utilizare": _sub_instalatie_utilizare(),
            "modernizare-retea": _sub_modernizare_retea(),
        },
    },
}


# ============================================================================
# PUBLIC API
# ============================================================================
def list_countries() -> List[Dict[str, Any]]:
    return list(COUNTRIES.values())


def list_subdomains(country: str = "RO", industry: str = "gaze-naturale") -> List[Dict[str, Any]]:
    industry_node = CATALOG.get(country, {}).get(industry, {})
    out = []
    for sid, sub in industry_node.items():
        if sid == "meta":
            continue
        out.append({
            "id": sub["id"],
            "name": sub["name"],
            "short": sub["short"],
            "category": sub["category"],
            "regime": sub["regime"],
            "description": sub["description"],
            "max_debit_mc_h": sub.get("max_debit_mc_h"),
            "phases_count": len(sub["phases"]),
        })
    return out


def get_subdomain(country: str, industry: str, subdomain: str) -> Optional[Dict[str, Any]]:
    return CATALOG.get(country, {}).get(industry, {}).get(subdomain)


def get_industry_meta(country: str = "RO", industry: str = "gaze-naturale") -> Optional[Dict[str, Any]]:
    return CATALOG.get(country, {}).get(industry, {}).get("meta")


def get_phases_for(country: str, industry: str, subdomain: str) -> List[Dict[str, Any]]:
    sub = get_subdomain(country, industry, subdomain)
    return sub["phases"] if sub else []


def get_phase(country: str, industry: str, subdomain: str, phase_id: str) -> Optional[Dict[str, Any]]:
    for p in get_phases_for(country, industry, subdomain):
        if p["id"] == phase_id:
            return p
    return None


def progress_for(country: str, industry: str, subdomain: str, data: Dict[str, Any]) -> Dict[str, Any]:
    phases = get_phases_for(country, industry, subdomain)
    per_phase = []
    overall_filled = 0
    overall_total = 0
    for p in phases:
        total = len(p["fields"])
        filled = sum(1 for ff in p["fields"] if str(data.get(ff["key"], "")).strip())
        per_phase.append({
            "phase_id": p["id"], "name": p["name"], "filled": filled, "total": total,
            "percent": round(100 * filled / total) if total else 0,
            "complete": filled == total,
        })
        overall_filled += filled
        overall_total += total
    return {
        "phases": per_phase,
        "overall_percent": round(100 * overall_filled / overall_total) if overall_total else 0,
        "overall_filled": overall_filled,
        "overall_total": overall_total,
    }

"""Industries & subdomains catalog.

All 8 industries are now active for documentation work. Gas engineering remains
the most templated, but other industries can be used for project tracking and
custom templates uploaded by the user.
"""
from typing import Dict, List


INDUSTRIES: Dict[str, Dict] = {
    "gas_engineering": {
        "id": "gas_engineering",
        "name": "Inginerie gaze naturale",
        "tagline": "Documentații pentru branșamente, extinderi și instalații gaze naturale",
        "status": "active",
        "subdomains": [
            {"id": "bransamente_gaz", "name": "Branșamente gaze naturale", "active": True,
             "description": "Branșamente noi gaze naturale către consumatori casnici și non-casnici."},
            {"id": "instalatii_utilizare", "name": "Instalații utilizare gaze naturale", "active": True,
             "description": "Instalații interioare de utilizare în clădiri rezidențiale și comerciale."},
            {"id": "extinderi_conducta", "name": "Extinderi de conductă gaze naturale", "active": True,
             "description": "Lucrări de extindere a rețelei de distribuție gaze naturale."},
            {"id": "studii_fezabilitate", "name": "Studii de fezabilitate", "active": True,
             "description": "Studii tehnico-economice pentru lucrări de gaze."},
            {"id": "inlocuiri_modernizari", "name": "Înlocuiri, reabilitări, modernizări", "active": True,
             "description": "Lucrări de modernizare rețele și instalații existente."},
            {"id": "autorizatii_construire", "name": "Autorizații construire (DTAC + Avize)", "active": True,
             "description": "DTAC, certificate de urbanism, avize ANRE, Primărie, ROMGAZ/DELGAZ."},
            {"id": "executie_santier", "name": "Execuție pe șantier (DTOE + DS + PCCVI)", "active": True,
             "description": "Organizare execuție, dispoziții de șantier, program control calitate."},
            {"id": "receptie_pif", "name": "Recepție & Punere în funcțiune (PVRT + Carte Tehnică)", "active": True,
             "description": "Procese verbale recepție, cartea tehnică a construcției, predare beneficiar."},
        ],
    },
    "electrical_engineering": {
        "id": "electrical_engineering",
        "name": "Inginerie electrică",
        "tagline": "Documentații pentru rețele electrice de joasă, medie și înaltă tensiune",
        "status": "active",
        "subdomains": [
            {"id": "bransamente_electric", "name": "Branșamente electrice (JT)", "active": True,
             "description": "Branșamente noi de joasă tensiune pentru consumatori casnici și non-casnici."},
            {"id": "instalatii_electrice", "name": "Instalații electrice interioare", "active": True,
             "description": "Instalații electrice clădiri rezidențiale, comerciale, industriale."},
            {"id": "extinderi_retea_electrica", "name": "Extinderi rețea electrică (JT/MT)", "active": True,
             "description": "Extinderi rețele de distribuție de joasă și medie tensiune."},
            {"id": "posturi_transformare", "name": "Posturi de transformare", "active": True,
             "description": "Construcție / modernizare PT pentru consumatori industriali."},
            {"id": "studii_coexistenta", "name": "Studii de coexistență", "active": True,
             "description": "Studii coexistență rețele electrice cu alte utilități subterane."},
        ],
    },
    "water_sewage": {
        "id": "water_sewage",
        "name": "Apă și canalizare",
        "tagline": "Documentații pentru rețele de apă potabilă, canalizare menajeră și pluvială",
        "status": "active",
        "subdomains": [
            {"id": "bransamente_apa", "name": "Branșamente apă potabilă", "active": True,
             "description": "Branșamente noi apă potabilă pentru consumatori casnici și non-casnici."},
            {"id": "racord_canalizare", "name": "Racorduri canalizare menajeră", "active": True,
             "description": "Racorduri noi la rețeaua de canalizare menajeră."},
            {"id": "extinderi_retea_apa", "name": "Extinderi rețea apă/canalizare", "active": True,
             "description": "Extinderi rețele publice de apă potabilă și canalizare."},
            {"id": "statii_pompare", "name": "Stații de pompare apă/canalizare", "active": True,
             "description": "Documentații proiectare/execuție stații de pompare."},
            {"id": "canalizare_pluviala", "name": "Canalizare pluvială", "active": True,
             "description": "Sisteme de canalizare pluvială stradală și incintă."},
        ],
    },
    "civil_engineering": {
        "id": "civil_engineering",
        "name": "Construcții civile",
        "tagline": "Documentații tehnice pentru construcții civile, recepție și autorizații",
        "status": "active",
        "subdomains": [
            {"id": "autorizatii_construire", "name": "Autorizații construire (DTAC)", "active": True,
             "description": "Documentații tehnice pentru autorizație de construire conform Legii 50/1991."},
            {"id": "proiecte_executie", "name": "Proiecte tehnice de execuție", "active": True,
             "description": "Documentații PT pentru execuție lucrări de construcții."},
            {"id": "expertize_tehnice", "name": "Expertize tehnice", "active": True,
             "description": "Expertize tehnice pentru construcții existente."},
        ],
    },
    "telecom": {
        "id": "telecom",
        "name": "Telecomunicații",
        "tagline": "Documentații pentru rețele fibră optică, copper și infrastructură mobilă",
        "status": "active",
        "subdomains": [
            {"id": "retele_fibra", "name": "Rețele fibră optică (FTTH/FTTB)", "active": True,
             "description": "Proiectare și execuție rețele fibră optică aeriene și subterane."},
            {"id": "infrastructura_mobila", "name": "Infrastructură mobilă (BTS)", "active": True,
             "description": "Stații de bază și echipamente de telecomunicații mobile."},
            {"id": "canalizatii_tc", "name": "Canalizații telecomunicații", "active": True,
             "description": "Rețele subterane pentru cabluri de telecomunicații."},
        ],
    },
    "photovoltaic": {
        "id": "photovoltaic",
        "name": "Fotovoltaice",
        "tagline": "Documentații pentru parcuri și instalații fotovoltaice rezidențiale, comerciale și industriale",
        "status": "active",
        "subdomains": [
            {"id": "instalatii_fv_rezidential", "name": "Instalații FV rezidențiale (prosumator)", "active": True,
             "description": "Instalații FV pentru consumatori casnici, până la 27 kWp (prosumator)."},
            {"id": "instalatii_fv_comercial", "name": "Instalații FV comerciale", "active": True,
             "description": "Instalații FV pe acoperișuri comerciale și industriale, 27-1000 kWp."},
            {"id": "parcuri_fv", "name": "Parcuri fotovoltaice", "active": True,
             "description": "Parcuri FV teren > 1 MWp, racordare la rețea MT/IT."},
            {"id": "racordare_dn", "name": "Racordare la distribuitor (avize)", "active": True,
             "description": "Documentații avize tehnice de racordare prosumator/producător."},
        ],
    },
    "construction": {
        "id": "construction",
        "name": "Construcții imobile",
        "tagline": "Documentații pentru construcții civile, rezidențiale și industriale — autorizații, proiecte, recepții",
        "status": "active",
        "subdomains": [
            {"id": "rezidential", "name": "Construcții rezidențiale", "active": True,
             "description": "Case unifamiliale, blocuri, ansambluri rezidențiale."},
            {"id": "comercial", "name": "Construcții comerciale", "active": True,
             "description": "Birouri, magazine, hoteluri, spații comerciale."},
            {"id": "industrial", "name": "Construcții industriale", "active": True,
             "description": "Hale, depozite, fabrici, structuri industriale."},
            {"id": "autorizatii_construire", "name": "Autorizații construire", "active": True,
             "description": "Documentații pentru autorizare construire conform Legii 50/1991."},
            {"id": "receptie_lucrari", "name": "Recepție lucrări", "active": True,
             "description": "Procese verbale de recepție la terminare lucrări."},
        ],
    },
    "railway_infra": {
        "id": "railway_infra",
        "name": "Infrastructură feroviară",
        "tagline": "Documentații pentru cale ferată, electrificare CF, lucrări de artă feroviare",
        "status": "active",
        "subdomains": [
            {"id": "cale_ferata", "name": "Cale ferată (linie nouă / modernizare)", "active": True,
             "description": "Proiecte cale ferată — linii noi, modernizări, întreținere."},
            {"id": "electrificare_cf", "name": "Electrificare cale ferată", "active": True,
             "description": "Sisteme electrificare CF 25 kV / 50 Hz și echipamente SCB."},
            {"id": "lucrari_arta", "name": "Lucrări de artă feroviare", "active": True,
             "description": "Poduri, pasarele, tuneluri și viaducte feroviare."},
            {"id": "statii_cf", "name": "Stații CF și halte", "active": True,
             "description": "Construcție / modernizare stații, halte, peroane."},
        ],
    },
    "sanitation": {
        "id": "sanitation",
        "name": "Salubritate & deșeuri",
        "tagline": "Colectare, transport, depozitare și tratare deșeuri menajere și industriale",
        "status": "active",
        "subdomains": [
            {"id": "colectare_separata", "name": "Colectare separată deșeuri", "active": True,
             "description": "Sisteme colectare selectivă urbane și rurale."},
            {"id": "depozite_ecologice", "name": "Depozite ecologice", "active": True,
             "description": "Depozit conform de deșeuri (HG 349/2005), DEEE."},
            {"id": "statii_sortare", "name": "Stații sortare & TMB", "active": True,
             "description": "Stații tratare mecano-biologică, sortare deșeuri."},
            {"id": "incinerare", "name": "Incinerare cu recuperare energie", "active": True,
             "description": "WtE (Waste-to-Energy) — sub 1000 t/zi."},
        ],
    },
    "hvac": {
        "id": "hvac",
        "name": "HVAC & instalații termice",
        "tagline": "Încălzire, ventilație, aer condiționat, frigotehnică pentru clădiri și industrie",
        "status": "active",
        "subdomains": [
            {"id": "centrale_termice", "name": "Centrale termice (gaz/biomasă)", "active": True,
             "description": "Centrale termice rezidențiale și industriale."},
            {"id": "instalatii_ventilatie", "name": "Instalații ventilație", "active": True,
             "description": "VRV, recuperator de căldură, UTA-uri."},
            {"id": "climatizare", "name": "Climatizare & aer condiționat", "active": True,
             "description": "Sisteme split, chillere, fancoil."},
            {"id": "frigotehnica", "name": "Frigotehnică industrială", "active": True,
             "description": "Depozite frigorifice, congelatoare profesionale."},
            {"id": "pompe_caldura", "name": "Pompe de căldură geo/aer/apă", "active": True,
             "description": "Pompe căldură pentru clădiri, monitorizare COP."},
        ],
    },
    "environment": {
        "id": "environment",
        "name": "Mediu & avize",
        "tagline": "Studii de impact, evaluare adecvată, autorizații de mediu și protecție",
        "status": "active",
        "subdomains": [
            {"id": "evaluare_impact", "name": "Evaluare impact asupra mediului (EIM)", "active": True,
             "description": "Raport EIM, raport mediu pentru PUZ/PUD."},
            {"id": "evaluare_adecvata", "name": "Evaluare adecvată (EA)", "active": True,
             "description": "Pentru proiecte în zone Natura 2000."},
            {"id": "autorizatii_mediu", "name": "Autorizații de mediu", "active": True,
             "description": "AM, AIM pentru operatori industriali."},
            {"id": "monitorizare", "name": "Monitorizare factori mediu", "active": True,
             "description": "Aer, apă, sol, zgomot, vibrații."},
        ],
    },
    "roads_bridges": {
        "id": "roads_bridges",
        "name": "Drumuri & poduri",
        "tagline": "Infrastructură rutieră, autostrăzi, poduri, pasaje, sisteme de siguranță",
        "status": "active",
        "subdomains": [
            {"id": "drumuri_locale", "name": "Drumuri locale & comunale", "active": True,
             "description": "Modernizare, asfaltare drumuri comunale."},
            {"id": "drumuri_judetene", "name": "Drumuri județene & naționale", "active": True,
             "description": "DJ, DN — modernizare, reabilitare."},
            {"id": "autostrazi", "name": "Autostrăzi & expres", "active": True,
             "description": "Construcție / modernizare autostrăzi cu 2x2 sau 2x3 benzi."},
            {"id": "poduri_pasaje", "name": "Poduri, pasaje, viaducte rutiere", "active": True,
             "description": "Construcție / consolidare poduri rutiere."},
            {"id": "siguranta_rutiera", "name": "Sisteme siguranță rutieră", "active": True,
             "description": "Parapeți, semnalizare orizontală/verticală, ITS."},
        ],
    },
    "public_lighting": {
        "id": "public_lighting",
        "name": "Iluminat public",
        "tagline": "Iluminat stradal LED, smart-city, ornamental, sportiv",
        "status": "active",
        "subdomains": [
            {"id": "iluminat_stradal", "name": "Iluminat stradal LED", "active": True,
             "description": "Înlocuire cu LED, eficiență energetică."},
            {"id": "iluminat_ornamental", "name": "Iluminat ornamental & festiv", "active": True,
             "description": "Parcuri, monumente, sărbători."},
            {"id": "iluminat_sportiv", "name": "Iluminat sportiv", "active": True,
             "description": "Terenuri, săli sportive, stadioane."},
            {"id": "smart_city", "name": "Iluminat smart-city (telegestiune)", "active": True,
             "description": "DALI, gestiune centralizată, dimming."},
        ],
    },
}


def list_industries() -> List[Dict]:
    return list(INDUSTRIES.values())


def get_industry(industry_id: str) -> Dict:
    return INDUSTRIES.get(industry_id, INDUSTRIES["gas_engineering"])


def get_subdomain(industry_id: str, subdomain_id: str) -> Dict:
    ind = get_industry(industry_id)
    for sd in ind.get("subdomains", []):
        if sd["id"] == subdomain_id:
            return sd
    return {"id": subdomain_id, "name": subdomain_id, "active": False}


def is_active(industry_id: str, subdomain_id: str = None) -> bool:
    ind = get_industry(industry_id)
    if ind.get("status") != "active":
        return False
    if subdomain_id is None:
        return True
    return get_subdomain(industry_id, subdomain_id).get("active", False)


# Default selection on registration
DEFAULT_INDUSTRY = "gas_engineering"
DEFAULT_SUBDOMAIN = "bransamente_gaz"

"""SEAP (e-licitatie.ro) Integration — skeleton stub.

This module will (eventually) poll SEAP/e-licitatie.ro for new public tenders
matching the user's CAEN/CPV codes and industries, and surface them as
opportunities inside the platform.

For now this is a minimal stub: it returns synthetic example tenders so the
UI/feature can be wired up end-to-end before real scraping/API integration is
done. The real implementation will live behind the same `fetch_tenders` API.

Reference: https://e-licitatie.ro/ — SEAP requires its own credentials / SOAP.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional


DEFAULT_CAEN_CODES = ["3522", "3513", "3514", "4221", "4222", "4321"]
DEFAULT_CPV_PREFIXES = ["09", "31", "44", "45", "71"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def fetch_tenders_stub(
    caen_codes: Optional[List[str]] = None,
    cpv_prefixes: Optional[List[str]] = None,
    industry: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Return a synthetic list of SEAP-like tenders.

    The shape mirrors what the real adapter will eventually produce so the UI
    and downstream alerting logic can be built first.
    """
    caen_codes = caen_codes or DEFAULT_CAEN_CODES
    cpv_prefixes = cpv_prefixes or DEFAULT_CPV_PREFIXES
    base = _now()
    examples = [
        {
            "external_id": "SEAP-STUB-2026-0001",
            "title": "Extindere rețea distribuție gaze naturale — comuna Demo",
            "authority": "Primăria Demo",
            "value_ron": 1_250_000,
            "cpv": "45231220-3",
            "caen": "3522",
            "deadline": (base + timedelta(days=14)).isoformat(),
            "url": "https://e-licitatie.ro/pub/notices/c-notice/v2/view/100000001",
            "industry": "gas_engineering",
        },
        {
            "external_id": "SEAP-STUB-2026-0002",
            "title": "Modernizare iluminat public — Municipiul Demo",
            "authority": "Consiliul Local Demo",
            "value_ron": 480_000,
            "cpv": "45316110-9",
            "caen": "4222",
            "deadline": (base + timedelta(days=21)).isoformat(),
            "url": "https://e-licitatie.ro/pub/notices/c-notice/v2/view/100000002",
            "industry": "public_lighting",
        },
        {
            "external_id": "SEAP-STUB-2026-0003",
            "title": "Reabilitare drum județean DJ-XYZ — lot 1",
            "authority": "CJ Demo",
            "value_ron": 8_500_000,
            "cpv": "45233140-2",
            "caen": "4221",
            "deadline": (base + timedelta(days=30)).isoformat(),
            "url": "https://e-licitatie.ro/pub/notices/c-notice/v2/view/100000003",
            "industry": "roads_bridges",
        },
    ]
    if industry:
        examples = [e for e in examples if e["industry"] == industry]
    return examples[:limit]


def integration_status() -> Dict[str, Any]:
    return {
        "provider": "SEAP / e-licitatie.ro",
        "mode": "STUB",
        "credentials_configured": False,
        "supported_filters": ["caen_codes", "cpv_prefixes", "industry", "limit"],
        "next_steps": [
            "Obținere acces SEAP (SOAP / Open Data)",
            "Implementare adapter real în `fetch_tenders()`",
            "Alerting per-utilizator pe baza profilului (CAEN, industrie, raza km)",
        ],
    }

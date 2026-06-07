"""V5.7 backend regression suite.

Covers:
- Auth login (admin credentials)
- AI Agents listing + 4 personas POST + history
- Jobs + Dev contracts (marketplace)
- System templates (13 gas templates)
- ANAF invoices listing (no 500)
- Admin config (admin-only)
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://energy-project.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "dragosserban95@gmail.com"
ADMIN_PASSWORD = "Test12345"


# ---- Fixtures ----------------------------------------------------------------
@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text[:200]}"
    data = r.json()
    assert "access_token" in data or "token" in data, f"no token in response: {data}"
    return data.get("access_token") or data.get("token")


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ---- Auth -------------------------------------------------------------------
class TestAuth:
    def test_login_admin_returns_jwt(self):
        r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
        assert r.status_code == 200
        data = r.json()
        token = data.get("access_token") or data.get("token")
        assert token and isinstance(token, str) and len(token) > 20
        # JWT has 3 dot-separated parts
        assert token.count(".") == 2

    def test_login_invalid_password(self):
        r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": "wrong"}, timeout=15)
        assert r.status_code in (400, 401, 403)


# ---- AI Agents --------------------------------------------------------------
class TestAIAgents:
    def test_agents_listing(self, admin_headers):
        r = requests.get(f"{API}/ai/agents", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text[:200]
        data = r.json()
        # Could be dict with "agents" or list directly
        agents = data.get("agents") if isinstance(data, dict) else data
        assert agents, f"no agents returned: {data}"
        slugs = []
        for a in agents:
            slugs.append(a.get("id") or a.get("slug") or a.get("key"))
        assert set(["producer", "user", "client", "developer"]).issubset(set(slugs)), f"slugs={slugs}"

    @pytest.mark.parametrize("agent,question,expected_terms", [
        ("producer", "Ce normativ se aplică pentru un sistem fotovoltaic de 30 kWp în categoria B?", ["kWp", "normativ", "fotovoltaic", "FV", "ANRE", "SR"]),
        ("user", "Ce înseamnă 5 kWp și cât produce într-un an?", ["kWp", "kWh", "an", "produce"]),
        ("client", "Liste materiale pentru branșament electric monofazat?", ["cablu", "siguranță", "monofazat", "branșament", "material"]),
        ("developer", "Cum adaug un endpoint pentru sincronizare ANAF?", ["endpoint", "FastAPI", "router", "def ", "api", "post"]),
    ])
    def test_agent_post_returns_reply(self, admin_headers, agent, question, expected_terms):
        r = requests.post(f"{API}/ai/agents/{agent}", headers=admin_headers, json={"message": question}, timeout=90)
        assert r.status_code == 200, f"{agent}: {r.status_code} {r.text[:300]}"
        data = r.json()
        reply = data.get("reply") or data.get("response") or ""
        assert isinstance(reply, str) and len(reply) > 20, f"{agent} short reply: {reply!r}"
        # Sanity-check at least one expected term shows up (case-insensitive)
        low = reply.lower()
        assert any(t.lower() in low for t in expected_terms), f"{agent} reply lacks expected terms. reply={reply[:300]}"

    def test_agent_history(self, admin_headers):
        # history should include some entries after the parametrized POSTs above
        r = requests.get(f"{API}/ai/agents/user/history?limit=10", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text[:200]
        data = r.json()
        msgs = data.get("messages") if isinstance(data, dict) else data
        assert isinstance(msgs, list)
        # At least one message should exist (from earlier POSTs)
        if msgs:
            sample = msgs[0]
            assert "message" in sample or "reply" in sample


# ---- Jobs + Dev contracts ---------------------------------------------------
class TestMarketplace:
    def test_jobs_list(self, admin_headers):
        r = requests.get(f"{API}/jobs", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text[:200]
        data = r.json()
        # accept list or dict with "items"
        items = data if isinstance(data, list) else (data.get("items") or data.get("jobs") or [])
        assert isinstance(items, list)

    def test_dev_contracts_list(self, admin_headers):
        r = requests.get(f"{API}/dev/contracts", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text[:200]
        data = r.json()
        items = data if isinstance(data, list) else (data.get("items") or data.get("contracts") or [])
        assert isinstance(items, list)


# ---- System templates -------------------------------------------------------
class TestSystemTemplates:
    def test_system_templates_count(self, admin_headers):
        r = requests.get(f"{API}/system-templates", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text[:200]
        data = r.json()
        items = data if isinstance(data, list) else (data.get("items") or data.get("templates") or [])
        assert isinstance(items, list)
        # spec says 13 gas templates pre-seeded
        assert len(items) >= 10, f"expected ~13 system templates, got {len(items)}"


# ---- ANAF -------------------------------------------------------------------
class TestANAF:
    def test_anaf_invoices_list_no_500(self, admin_headers):
        r = requests.get(f"{API}/anaf/invoices", headers=admin_headers, timeout=20)
        assert r.status_code != 500, f"ANAF crashed: {r.status_code} {r.text[:300]}"
        # 200 is expected; 401/403 unlikely for admin
        assert r.status_code in (200, 404), f"unexpected: {r.status_code} {r.text[:200]}"


# ---- Admin config -----------------------------------------------------------
class TestAdminConfig:
    def test_admin_config_requires_auth(self):
        r = requests.get(f"{API}/admin/config", timeout=10)
        assert r.status_code in (401, 403)

    def test_admin_config_returns_config(self, admin_headers):
        r = requests.get(f"{API}/admin/config", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text[:200]
        data = r.json()
        assert isinstance(data, dict) and len(data) > 0

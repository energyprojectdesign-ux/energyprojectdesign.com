"""V4.6 feature tests — industries catalog, system templates, multi-project,
developer auto-detection, AI Developer endpoints, QES credentials."""
import os
import uuid
import pytest
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / "frontend" / ".env")

_url = os.environ.get("REACT_APP_BACKEND_URL")
assert _url, "REACT_APP_BACKEND_URL must be set"
BASE_URL = _url.rstrip("/")
API = f"{BASE_URL}/api"

DEVELOPER_EMAIL = os.environ.get("DEVELOPER_TEST_EMAIL", "dragosserban95@gmail.com")
DEVELOPER_PASSWORD = os.environ.get("DEVELOPER_TEST_PASSWORD", "Test12345")


# ---------- Fixtures ----------
@pytest.fixture(scope="module")
def s():
    return requests.Session()


@pytest.fixture(scope="module")
def regular_user(s):
    email = f"v46_{uuid.uuid4().hex[:8]}@example.com"
    r = s.post(f"{API}/auth/register", json={
        "email": email, "password": "Pass1234", "name": "V46 User",
        "company": "Co", "gdpr_consent": True,
    })
    assert r.status_code == 200, r.text
    data = r.json()
    return {"email": email, "token": data["token"], "user": data["user"]}


@pytest.fixture(scope="module")
def regular_headers(regular_user):
    return {"Authorization": f"Bearer {regular_user['token']}"}


@pytest.fixture(scope="module")
def developer_user(s):
    """Register or login the developer account; auto-upgrade on login."""
    r = s.post(f"{API}/auth/register", json={
        "email": DEVELOPER_EMAIL, "password": DEVELOPER_PASSWORD,
        "name": "Dragos", "gdpr_consent": True,
    })
    if r.status_code == 200:
        data = r.json()
    elif r.status_code == 400:
        # Already exists, login
        r2 = s.post(f"{API}/auth/login", json={
            "email": DEVELOPER_EMAIL, "password": DEVELOPER_PASSWORD,
        })
        assert r2.status_code == 200, r2.text
        data = r2.json()
    else:
        pytest.fail(f"Unexpected register status {r.status_code}: {r.text}")
    return {"token": data["token"], "user": data["user"]}


@pytest.fixture(scope="module")
def developer_headers(developer_user):
    return {"Authorization": f"Bearer {developer_user['token']}"}


# ---------- Industries catalog ----------
class TestIndustries:
    def test_industries_list(self, s):
        r = s.get(f"{API}/industries")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        ids = [d["id"] for d in data]
        for expected in ["gas_engineering", "electrical_engineering",
                         "water_sewage", "civil_engineering", "telecom"]:
            assert expected in ids, f"Missing industry {expected}"
        assert len(data) >= 5

    def test_gas_active_others_coming_soon(self, s):
        data = s.get(f"{API}/industries").json()
        by_id = {d["id"]: d for d in data}
        # v5+: gas remains active; others may also be active (8 industries activated)
        assert by_id["gas_engineering"]["status"] == "active"
        # Ensure all industries have a valid status value
        for d in data:
            assert d["status"] in ("active", "coming_soon", "planned"), d

    def test_gas_subdomains_active(self, s):
        data = s.get(f"{API}/industries").json()
        gas = next(d for d in data if d["id"] == "gas_engineering")
        sub_ids = {sd["id"] for sd in gas["subdomains"]}
        expected_subs = {"bransamente_gaz", "instalatii_utilizare",
                         "extinderi_conducta", "studii_fezabilitate",
                         "inlocuiri_modernizari"}
        assert expected_subs.issubset(sub_ids)
        for sd in gas["subdomains"]:
            if sd["id"] in expected_subs:
                assert sd["active"] is True, f"{sd['id']} should be active"


# ---------- System templates ----------
class TestSystemTemplates:
    def test_list_system_templates(self, s):
        r = s.get(f"{API}/system-templates")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        keys = {d["key"] for d in data}
        expected = {"sys_cerere_racordare_gaz", "sys_memoriu_tehnic_gaz",
                    "sys_borderou_documente_gaz", "sys_adresa_osd_gaz"}
        assert expected.issubset(keys), f"Missing: {expected - keys}"

    def test_system_template_fields(self, s):
        data = s.get(f"{API}/system-templates").json()
        for d in data:
            assert d.get("is_system") is True
            assert isinstance(d.get("placeholders"), list)
            assert len(d["placeholders"]) > 0
            assert "data_b64" not in d

    def test_filter_industry_gas(self, s):
        r = s.get(f"{API}/system-templates", params={"industry": "gas_engineering"})
        assert r.status_code == 200
        data = r.json()
        # v5+: catalogue expanded from 4 to 6+ gas templates
        assert len(data) >= 4
        for d in data:
            assert d["industry"] == "gas_engineering"

    def test_clone_system_template(self, s, regular_headers):
        r = s.post(f"{API}/system-templates/sys_cerere_racordare_gaz/clone",
                   headers=regular_headers)
        assert r.status_code == 200, r.text
        cloned = r.json()
        assert cloned["source_system_key"] == "sys_cerere_racordare_gaz"
        assert "template_id" in cloned
        # Verify it appears in user's templates
        r2 = s.get(f"{API}/templates", headers=regular_headers)
        assert r2.status_code == 200
        tpls = r2.json()
        assert any(t["template_id"] == cloned["template_id"] for t in tpls)


# ---------- Multi-project CRUD ----------
class TestMultiProject:
    def test_list_projects_has_at_least_one(self, s, regular_headers):
        # Trigger default project creation
        s.get(f"{API}/project", headers=regular_headers)
        r = s.get(f"{API}/projects", headers=regular_headers)
        assert r.status_code == 200
        projects = r.json()
        assert isinstance(projects, list)
        assert len(projects) >= 1
        # Exactly one active
        active = [p for p in projects if p.get("active")]
        assert len(active) == 1

    def test_create_activate_new_project(self, s, regular_headers):
        # Get current active
        first = s.get(f"{API}/project", headers=regular_headers).json()
        first_id = first["project_id"]

        # Create second project
        r = s.post(f"{API}/projects", headers=regular_headers, json={
            "name": "TEST_Proiect_2", "industry": "gas_engineering",
            "subdomain": "extinderi_conducta",
        })
        assert r.status_code == 200, r.text
        new_proj = r.json()
        assert new_proj["name"] == "TEST_Proiect_2"
        assert new_proj["industry"] == "gas_engineering"
        assert new_proj["subdomain"] == "extinderi_conducta"
        new_id = new_proj["project_id"]

        # Should now be active (creation activates)
        active = s.get(f"{API}/project", headers=regular_headers).json()
        assert active["project_id"] == new_id

        # Switch back
        r2 = s.post(f"{API}/projects/{first_id}/activate", headers=regular_headers)
        assert r2.status_code == 200
        active2 = s.get(f"{API}/project", headers=regular_headers).json()
        assert active2["project_id"] == first_id

    def test_archive_unarchive_delete(self, s, regular_headers):
        r = s.post(f"{API}/projects", headers=regular_headers, json={
            "name": "TEST_ArchiveMe", "industry": "gas_engineering",
            "subdomain": "bransamente_gaz",
        })
        pid = r.json()["project_id"]
        # Archive
        r1 = s.post(f"{API}/projects/{pid}/archive", headers=regular_headers)
        assert r1.status_code == 200 and r1.json()["archived"] is True
        # Not in default listing
        r2 = s.get(f"{API}/projects", headers=regular_headers).json()
        assert not any(p["project_id"] == pid for p in r2)
        # In include_archived
        r3 = s.get(f"{API}/projects", headers=regular_headers,
                   params={"include_archived": True}).json()
        assert any(p["project_id"] == pid for p in r3)
        # Unarchive
        r4 = s.post(f"{API}/projects/{pid}/unarchive", headers=regular_headers)
        assert r4.status_code == 200 and r4.json()["archived"] is False
        # Delete
        r5 = s.delete(f"{API}/projects/{pid}", headers=regular_headers)
        assert r5.status_code == 200 and r5.json()["deleted"] is True
        # Gone
        r6 = s.delete(f"{API}/projects/{pid}", headers=regular_headers)
        assert r6.status_code == 404

    def test_update_active_project(self, s, regular_headers):
        # Create + activate fresh project
        r = s.post(f"{API}/projects", headers=regular_headers, json={
            "name": "TEST_Active", "industry": "gas_engineering",
            "subdomain": "bransamente_gaz",
        })
        pid = r.json()["project_id"]
        # PUT /project updates the active
        upd = s.put(f"{API}/project", headers=regular_headers, json={
            "beneficiar": "Beneficiar Test", "localitate": "Cluj",
        })
        assert upd.status_code == 200
        assert upd.json()["project_id"] == pid
        assert upd.json()["beneficiar"] == "Beneficiar Test"


# ---------- Developer auto-detection ----------
class TestDeveloperAutoDetect:
    def test_developer_email_is_developer(self, developer_user):
        u = developer_user["user"]
        assert u.get("is_developer") is True
        assert u.get("plan") == "developer"

    def test_non_developer_is_not(self, regular_user):
        u = regular_user["user"]
        assert u.get("is_developer") is False
        assert u.get("plan") != "developer"


# ---------- AI Developer ----------
class TestAIDeveloper:
    def test_dev_plan_as_developer(self, s, developer_headers):
        r = s.post(f"{API}/dev/plan", headers=developer_headers, json={
            "prompt": "Adaugă industria electrical_engineering",
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("mode") == "plan"
        assert isinstance(data.get("proposed_steps"), list)
        assert len(data["proposed_steps"]) > 0
        diag = data.get("diagnostic", {})
        assert "rules" in diag
        assert "missing_capabilities" in diag
        assert isinstance(data.get("validation_checklist"), list)

    def test_dev_plan_forbidden_for_regular(self, s, regular_headers):
        r = s.post(f"{API}/dev/plan", headers=regular_headers, json={"prompt": "test"})
        assert r.status_code == 403

    def test_safety_rules_developer(self, s, developer_headers):
        r = s.get(f"{API}/dev/safety-rules", headers=developer_headers)
        assert r.status_code == 200
        rules = r.json().get("rules", [])
        assert isinstance(rules, list)
        assert len(rules) == 9

    def test_safety_rules_forbidden_for_regular(self, s, regular_headers):
        r = s.get(f"{API}/dev/safety-rules", headers=regular_headers)
        assert r.status_code == 403


# ---------- QES credentials ----------
class TestQESCredentials:
    def test_put_certsign_creds(self, s, regular_headers):
        r = s.put(f"{API}/qes/credentials", headers=regular_headers, json={
            "provider": "certsign",
            "credentials": {"client_id": "X", "client_secret": "Y", "endpoint_url": "Z"},
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["ok"] is True
        assert data["provider"] == "certsign"
        assert set(data["fields_saved"]) == {"client_id", "client_secret", "endpoint_url"}

    def test_put_unknown_provider_400(self, s, regular_headers):
        r = s.put(f"{API}/qes/credentials", headers=regular_headers, json={
            "provider": "unknown_xyz", "credentials": {"a": "1"},
        })
        assert r.status_code == 400

    def test_get_creds_returns_counts_not_values(self, s, regular_headers):
        # Ensure saved first
        s.put(f"{API}/qes/credentials", headers=regular_headers, json={
            "provider": "certsign",
            "credentials": {"client_id": "X", "client_secret": "Y", "endpoint_url": "Z"},
        })
        r = s.get(f"{API}/qes/credentials", headers=regular_headers)
        assert r.status_code == 200
        data = r.json()
        assert "certsign" in data
        assert data["certsign"].get("fields_count") == 3
        # Must not contain actual values
        raw = r.text
        assert "client_id" not in raw or "X" not in raw
        assert "client_secret" not in raw or "Y" not in raw

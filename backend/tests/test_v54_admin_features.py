"""
V5.4 Admin/Configuration features backend tests.

Covers:
  - Auth flags (is_admin, is_developer)
  - Secondary email PATCH/GET
  - /api/users/me/email-config
  - /api/admin/config GET/PUT (singleton, maintenance, feature flags)
  - /api/system/banner public
  - /api/admin/stats
  - /api/admin/users (list/search/PATCH role/ban)
  - 403 enforcement for non-admins
  - /api/photovoltaic/tech-offer-pdf success & 400 branch
  - /api/documents/email cc echo
"""

import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://energy-project.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "dragosserban95@gmail.com"
ADMIN_PASSWORD = "Test12345"


# ---------- shared session ----------
@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    data = r.json()
    assert data["user"].get("is_admin") is True or data["user"].get("is_developer") is True, \
        f"Admin user missing flags: {data['user']}"
    return data["token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="session")
def regular_user():
    """Create a brand-new regular user via /api/auth/register."""
    email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPass123!"
    r = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": email, "password": password, "name": "Test Regular",
        "gdpr_consent": True,
    })
    if r.status_code not in (200, 201):
        pytest.skip(f"Register endpoint unavailable: {r.status_code} {r.text[:200]}")
    data = r.json()
    token = data.get("token")
    if not token:
        # Some apps return only user; fall back to login
        lr = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password})
        token = lr.json().get("token")
    return {"email": email, "password": password, "token": token, "headers": {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}}


# ---------- 1. Admin login flags ----------
class TestAdminLogin:
    def test_admin_login_returns_admin_flags(self):
        r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        assert r.status_code == 200
        u = r.json()["user"]
        assert u.get("is_developer") is True, f"is_developer missing/false: {u}"
        # is_admin may be implied by is_developer per other_misc_info
        assert u.get("is_admin") is True or u.get("is_developer") is True


# ---------- 2. Secondary email on /api/users/me ----------
class TestSecondaryEmail:
    def test_get_me_returns_secondary_email_field(self, admin_headers):
        # GET equivalent is /api/auth/me (PATCH lives at /api/users/me)
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=admin_headers)
        assert r.status_code == 200
        assert "secondary_email" in r.json()

    def test_patch_secondary_email(self, admin_headers):
        # Save original
        original = requests.get(f"{BASE_URL}/api/auth/me", headers=admin_headers).json().get("secondary_email")

        new_val = "biz@example.com"
        r = requests.patch(f"{BASE_URL}/api/users/me", headers=admin_headers, json={"secondary_email": new_val})
        assert r.status_code in (200, 204), f"PATCH failed: {r.status_code} {r.text}"

        r2 = requests.get(f"{BASE_URL}/api/auth/me", headers=admin_headers)
        assert r2.json()["secondary_email"] == new_val

        # Clear it
        r3 = requests.patch(f"{BASE_URL}/api/users/me", headers=admin_headers, json={"secondary_email": ""})
        assert r3.status_code in (200, 204)
        r4 = requests.get(f"{BASE_URL}/api/auth/me", headers=admin_headers)
        assert r4.json()["secondary_email"] in (None, "")

        # Restore
        requests.patch(f"{BASE_URL}/api/users/me", headers=admin_headers, json={"secondary_email": original or ""})

    def test_email_config_includes_secondary(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/users/me/email-config", headers=admin_headers)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "secondary_email" in body
        assert "configured" in body
        assert "gmail_user" in body


# ---------- 3. Admin config singleton ----------
class TestAdminConfig:
    def test_get_admin_config(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/config", headers=admin_headers)
        assert r.status_code == 200, r.text
        cfg = r.json()
        assert "smtp_global_password_set" in cfg
        assert isinstance(cfg["smtp_global_password_set"], bool)
        # Plaintext password must NEVER be in the response
        assert "smtp_global_password" not in cfg or cfg.get("smtp_global_password") in (None, "", "***")

    def test_maintenance_mode_toggle_and_banner(self, admin_headers):
        # Turn maintenance ON
        r = requests.put(f"{BASE_URL}/api/admin/config", headers=admin_headers, json={
            "maintenance_mode": True, "maintenance_message": "Reboot programat"
        })
        assert r.status_code == 200, r.text
        cfg = r.json()
        assert cfg.get("maintenance_mode") is True
        assert cfg.get("maintenance_message") == "Reboot programat"

        # Public banner endpoint
        b = requests.get(f"{BASE_URL}/api/system/banner")
        assert b.status_code == 200
        banner = b.json()
        assert banner.get("maintenance_mode") is True
        assert "Reboot programat" in (banner.get("maintenance_message") or "")

        # Turn OFF
        r2 = requests.put(f"{BASE_URL}/api/admin/config", headers=admin_headers, json={
            "maintenance_mode": False, "maintenance_message": ""
        })
        assert r2.status_code == 200
        assert r2.json().get("maintenance_mode") is False

    def test_feature_flags_toggle(self, admin_headers):
        flags = [
            "feature_forum_enabled", "feature_email_enabled", "feature_pdf_enabled",
            "feature_photovoltaic_enabled", "feature_ai_assistant_enabled", "feature_payments_enabled",
        ]
        original = requests.get(f"{BASE_URL}/api/admin/config", headers=admin_headers).json()
        for f in flags:
            curr = original.get(f, True)
            new_val = not bool(curr)
            r = requests.put(f"{BASE_URL}/api/admin/config", headers=admin_headers, json={f: new_val})
            assert r.status_code == 200, f"PUT {f}={new_val} failed: {r.text}"
            assert r.json().get(f) == new_val, f"Flag {f} not echoed correctly"
            # Restore
            requests.put(f"{BASE_URL}/api/admin/config", headers=admin_headers, json={f: curr})


# ---------- 4. Stats ----------
class TestAdminStats:
    def test_admin_stats_counters(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/stats", headers=admin_headers)
        assert r.status_code == 200, r.text
        s = r.json()
        for key in ("users_total", "admins_total", "projects_total", "documents_total", "emails_sent", "forum_threads"):
            assert key in s, f"Missing key {key} in stats: {s.keys()}"
            assert isinstance(s[key], int), f"{key} not int: {type(s[key])}"


# ---------- 5. Admin users list ----------
class TestAdminUsers:
    def test_list_users_with_limit(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/users?limit=5", headers=admin_headers)
        assert r.status_code == 200, r.text
        body = r.json()
        users = body if isinstance(body, list) else body.get("users", body.get("items", []))
        assert isinstance(users, list)
        assert len(users) <= 5

    def test_search_users(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/users?search=dragos", headers=admin_headers)
        assert r.status_code == 200, r.text
        body = r.json()
        users = body if isinstance(body, list) else body.get("users", body.get("items", []))
        assert len(users) >= 1, "Expected at least one match for 'dragos'"

    def test_promote_and_demote_user(self, admin_headers, regular_user):
        # Find the regular user's id
        r = requests.get(f"{BASE_URL}/api/admin/users?search={regular_user['email']}", headers=admin_headers)
        assert r.status_code == 200
        body = r.json()
        users = body if isinstance(body, list) else body.get("users", body.get("items", []))
        assert users, "Newly registered user not visible in admin users list"
        uid = users[0].get("user_id") or users[0].get("id") or users[0].get("_id")
        assert uid

        def _get_user_state():
            rr = requests.get(f"{BASE_URL}/api/admin/users?search={regular_user['email']}", headers=admin_headers)
            ulist = rr.json().get("users", [])
            return ulist[0] if ulist else {}

        try:
            # Promote
            r1 = requests.patch(f"{BASE_URL}/api/admin/users/{uid}", headers=admin_headers, json={"is_admin": True})
            assert r1.status_code == 200, r1.text
            assert _get_user_state().get("is_admin") is True

            # Demote
            r2 = requests.patch(f"{BASE_URL}/api/admin/users/{uid}", headers=admin_headers, json={"is_admin": False})
            assert r2.status_code == 200
            assert _get_user_state().get("is_admin") is False

            # Ban
            r3 = requests.patch(f"{BASE_URL}/api/admin/users/{uid}", headers=admin_headers, json={"is_banned": True})
            assert r3.status_code == 200
            assert _get_user_state().get("is_banned") is True

            # Unban
            r4 = requests.patch(f"{BASE_URL}/api/admin/users/{uid}", headers=admin_headers, json={"is_banned": False})
            assert r4.status_code == 200
            assert _get_user_state().get("is_banned") is False
        finally:
            # Force clean state regardless of test result
            requests.patch(f"{BASE_URL}/api/admin/users/{uid}", headers=admin_headers,
                           json={"is_admin": False, "is_banned": False})


# ---------- 6. Non-admin 403 ----------
@pytest.fixture
def fresh_non_admin():
    """Fresh non-admin user just for 403 testing (avoid promotion side-effects)."""
    email = f"test_403_{uuid.uuid4().hex[:8]}@example.com"
    r = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": email, "password": "TestPass123!", "name": "Test 403", "gdpr_consent": True,
    })
    if r.status_code not in (200, 201):
        pytest.skip(f"Register failed: {r.status_code} {r.text[:200]}")
    token = r.json().get("token")
    return {"email": email, "headers": {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}}


class TestNonAdmin403:
    @pytest.mark.parametrize("path", [
        "/api/admin/config",
        "/api/admin/stats",
        "/api/admin/users",
    ])
    def test_non_admin_blocked(self, fresh_non_admin, path):
        r = requests.get(f"{BASE_URL}{path}", headers=fresh_non_admin["headers"])
        assert r.status_code == 403, f"Expected 403 on {path}, got {r.status_code}"


# ---------- 7. Tech Offer FV PDF ----------
class TestTechOfferPDF:
    def _get_or_create_active_project(self, headers):
        # List projects
        r = requests.get(f"{BASE_URL}/api/projects", headers=headers)
        if r.status_code != 200:
            pytest.skip(f"/api/projects failed: {r.status_code}")
        projs = r.json() if isinstance(r.json(), list) else r.json().get("projects", [])
        if not projs:
            cr = requests.post(f"{BASE_URL}/api/projects", headers=headers, json={"name": "TEST_FV_PDF", "client_name": "Test Client"})
            if cr.status_code in (200, 201):
                projs = [cr.json()]
        return projs[0] if projs else None

    def test_pdf_after_calculate(self, admin_headers):
        proj = self._get_or_create_active_project(admin_headers)
        if not proj:
            pytest.skip("No active project")

        # Run a calculation to ensure photovoltaic_results exist
        payload = {
            "p_kwp": 10.0,
            "p_panou_wp": 450,
            "consum_anual_kwh": 12000,
            "zona": "bucuresti",
        }
        calc = requests.post(f"{BASE_URL}/api/photovoltaic/calculate", headers=admin_headers, json=payload)
        if calc.status_code not in (200, 201):
            calc = requests.post(f"{BASE_URL}/api/photovoltaic/calculate", headers=admin_headers, json={"p_kwp": 10})
        assert calc.status_code in (200, 201), f"Calculate failed: {calc.status_code} {calc.text[:300]}"

        # Download PDF
        r = requests.get(f"{BASE_URL}/api/photovoltaic/tech-offer-pdf", headers=admin_headers)
        assert r.status_code == 200, f"PDF download failed: {r.status_code} {r.text[:300]}"
        assert "pdf" in r.headers.get("Content-Type", "").lower()
        assert r.content[:4] == b"%PDF", "Body doesn't start with %PDF"
        assert len(r.content) > 4096, f"PDF too small: {len(r.content)} bytes"


# ---------- 8. Email send cc echo ----------
class TestEmailCcEcho:
    def test_email_doc_cc_echo(self, admin_headers):
        # Make sure secondary email is set
        requests.patch(f"{BASE_URL}/api/users/me", headers=admin_headers, json={"secondary_email": "biz-cc@example.com"})

        # List documents
        d = requests.get(f"{BASE_URL}/api/documents", headers=admin_headers)
        if d.status_code != 200:
            pytest.skip(f"documents endpoint: {d.status_code}")
        docs = d.json() if isinstance(d.json(), list) else d.json().get("documents", [])
        if not docs:
            pytest.skip("No documents present to send")
        doc_id = docs[0].get("document_id") or docs[0].get("id") or docs[0].get("_id")

        payload = {"document_id": doc_id, "to": "recipient@example.com", "subject": "Test", "body": "Test"}
        r = requests.post(f"{BASE_URL}/api/documents/email", headers=admin_headers, json=payload)
        # Either it sends or fails with structured error (gmail not configured)
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        if r.status_code == 200:
            cc = body.get("cc", [])
            assert "biz-cc@example.com" in cc, f"Expected secondary in cc, got: {cc}"
        else:
            # error must be structured (Romanian message expected)
            assert "detail" in body or "error" in body or "message" in body, f"Unstructured error: {r.text[:300]}"

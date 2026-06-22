"""
tests/ui/test_login.py
======================
UI and API authentication tests.
"""

from __future__ import annotations

import requests
from requests import Session

from fixtures import assert_ok


class TestLoginPage:
    """Login UI — no credentials required."""

    def test_login_page_returns_200(self, base_url: str, verify_tls: bool) -> None:
        r = requests.get(f"{base_url}/login", verify=verify_tls, timeout=15,
                         allow_redirects=True)
        assert r.status_code == 200

    def test_login_page_contains_form(self, base_url: str, verify_tls: bool) -> None:
        r = requests.get(f"{base_url}/login", verify=verify_tls, timeout=15,
                         allow_redirects=True)
        body = r.text.lower()
        assert "email" in body or "username" in body or "login" in body

    def test_logout_does_not_crash(self, base_url: str, verify_tls: bool) -> None:
        r = requests.get(f"{base_url}/logout", verify=verify_tls, timeout=10,
                         allow_redirects=True)
        assert r.status_code < 500

    def test_account_page_accessible(self, base_url: str, verify_tls: bool) -> None:
        """Redirects to login if unauthenticated — still should not 5xx."""
        r = requests.get(f"{base_url}/account", verify=verify_tls, timeout=10,
                         allow_redirects=True)
        assert r.status_code < 500


class TestTokenAuthentication:
    """API token acceptance and rejection."""

    def test_valid_token_accepted(self, http: Session, base_url: str) -> None:
        r = http.get(f"{base_url}/api/user/packages", params={"size": 1})
        assert_ok(r, 200)

    def test_valid_token_returns_hits(self, http: Session, base_url: str) -> None:
        r = http.get(f"{base_url}/api/user/packages", params={"size": 1})
        assert "hits" in r.json()

    def test_missing_token_rejected(self, anon_http: Session, base_url: str) -> None:
        r = anon_http.get(f"{base_url}/api/user/packages")
        assert r.status_code in (401, 403)

    def test_invalid_token_rejected(self, base_url: str, verify_tls: bool) -> None:
        s = requests.Session()
        s.headers["Authorization"] = "Bearer totally-invalid-token-xyz"
        s.verify = verify_tls
        r = s.get(f"{base_url}/api/user/packages")
        assert r.status_code in (401, 403)

    def test_token_can_read_packages(self, http: Session, base_url: str) -> None:
        r = http.get(f"{base_url}/api/packages", params={"size": 1})
        assert_ok(r, 200)

    def test_token_can_read_records(self, http: Session, base_url: str) -> None:
        r = http.get(f"{base_url}/api/records", params={"size": 1})
        assert_ok(r, 200)


class TestUserProfile:
    """User-scoped API endpoints."""

    def test_user_records_endpoint(self, http: Session, base_url: str) -> None:
        r = http.get(f"{base_url}/api/user/records", params={"size": 1})
        assert_ok(r, 200)
        assert "hits" in r.json()

    def test_user_packages_endpoint(self, http: Session, base_url: str) -> None:
        r = http.get(f"{base_url}/api/user/packages", params={"size": 1})
        assert_ok(r, 200)
        assert "hits" in r.json()

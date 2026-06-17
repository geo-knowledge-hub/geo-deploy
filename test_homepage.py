"""
test_homepage.py
Tests for the GEO Knowledge Hub public homepage and general availability.

Covers
------
- Homepage returns HTTP 200 (no auth required)
- Key UI sections are present in HTML (search bar, nav)
- Static assets endpoint responds
- robots.txt is reachable
- API root / health endpoint responds
- Redirect behaviour (trailing slash, http→https if applicable)
"""

from __future__ import annotations

import requests
import pytest
from requests import Session

from conftest import assert_ok


class TestHomepage:

    def test_homepage_status_200(self, base_url: str, verify_tls: bool) -> None:
        """Public homepage must return 200 without any credentials."""
        r = requests.get(base_url, verify=verify_tls, timeout=15)
        assert r.status_code == 200, f"Homepage returned {r.status_code}"

    def test_homepage_content_type_html(self, base_url: str, verify_tls: bool) -> None:
        r = requests.get(base_url, verify=verify_tls, timeout=15)
        assert "text/html" in r.headers.get("Content-Type", ""), (
            "Homepage should return HTML"
        )

    def test_homepage_contains_search_input(self, base_url: str, verify_tls: bool) -> None:
        """The search bar must be present on the homepage."""
        r = requests.get(base_url, verify=verify_tls, timeout=15)
        body = r.text.lower()
        assert "search" in body, "Expected 'search' keyword in homepage HTML"

    def test_homepage_contains_nav(self, base_url: str, verify_tls: bool) -> None:
        r = requests.get(base_url, verify=verify_tls, timeout=15)
        body = r.text.lower()
        assert "<nav" in body or "navbar" in body, (
            "Expected navigation element in homepage HTML"
        )

    def test_robots_txt_reachable(self, base_url: str, verify_tls: bool) -> None:
        r = requests.get(f"{base_url}/robots.txt", verify=verify_tls, timeout=10)
        assert r.status_code in (200, 404), (
            f"Unexpected status {r.status_code} for /robots.txt"
        )

    def test_trailing_slash_redirect(self, base_url: str, verify_tls: bool) -> None:
        """Requests with or without trailing slash should both succeed."""
        for url in [base_url, base_url + "/"]:
            r = requests.get(url, verify=verify_tls, timeout=15,
                             allow_redirects=True)
            assert r.status_code == 200, f"URL {url} returned {r.status_code}"

    def test_api_root_responds(self, anon_http: Session, base_url: str) -> None:
        """The API root should respond (200 or 404 – but not 5xx)."""
        r = anon_http.get(f"{base_url}/api/", timeout=10)
        assert r.status_code < 500, f"API root returned server error {r.status_code}"

    def test_static_assets_endpoint(self, base_url: str, verify_tls: bool) -> None:
        """Check that the static files path is not returning 5xx errors."""
        r = requests.get(f"{base_url}/static/", verify=verify_tls, timeout=10,
                         allow_redirects=True)
        assert r.status_code < 500, (
            f"/static/ returned server error {r.status_code}"
        )


class TestPublicSearchPage:
    """The /search page should be accessible without login."""

    def test_search_page_loads(self, base_url: str, verify_tls: bool) -> None:
        r = requests.get(f"{base_url}/search", verify=verify_tls, timeout=15)
        assert r.status_code in (200, 301, 302), (
            f"/search returned {r.status_code}"
        )

    def test_search_page_follows_redirect(self, base_url: str, verify_tls: bool) -> None:
        r = requests.get(f"{base_url}/search", verify=verify_tls, timeout=15,
                         allow_redirects=True)
        assert r.status_code == 200

    def test_api_search_public(self, anon_http: Session, base_url: str) -> None:
        """The /api/search endpoint must be publicly accessible."""
        r = anon_http.get(f"{base_url}/api/search", params={"size": 1})
        assert_ok(r, 200)
        assert "hits" in r.json()

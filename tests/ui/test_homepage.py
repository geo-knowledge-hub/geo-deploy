#
# This file is part of GEO Knowledge Hub.
# Copyright 2020-2021 GEO Secretariat.
#
# GEO Knowledge Hub is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Module UI/homepage test"""

from __future__ import annotations

import requests
from requests import Session

from tests.fixtures import assert_ok


class TestHomepage:
    """Public homepage availability and content."""

    def test_homepage_returns_200(self, base_url: str, verify_tls: bool) -> None:
        """Homepage must be reachable without any credentials."""
        r = requests.get(base_url, verify=verify_tls, timeout=15)
        assert r.status_code == 200, f"Homepage returned {r.status_code}"

    def test_homepage_is_html(self, base_url: str, verify_tls: bool) -> None:
        r = requests.get(base_url, verify=verify_tls, timeout=15)
        assert "text/html" in r.headers.get("Content-Type", "")

    def test_homepage_contains_search(self, base_url: str, verify_tls: bool) -> None:
        r = requests.get(base_url, verify=verify_tls, timeout=15)
        assert "search" in r.text.lower(), "Expected search element in homepage"

    def test_homepage_contains_nav(self, base_url: str, verify_tls: bool) -> None:
        r = requests.get(base_url, verify=verify_tls, timeout=15)
        body = r.text.lower()
        assert "<nav" in body or "navbar" in body

    def test_trailing_slash_redirect(self, base_url: str, verify_tls: bool) -> None:
        for url in [base_url, base_url + "/"]:
            r = requests.get(url, verify=verify_tls, timeout=15, allow_redirects=True)
            assert r.status_code == 200, f"{url} returned {r.status_code}"

    def test_robots_txt_reachable(self, base_url: str, verify_tls: bool) -> None:
        """
        robots.txt instructs search engine crawlers which pages to index.
        We only check that the server handles the URL without crashing.
        200 = file exists, 404 = no file — both are acceptable.
        """
        r = requests.get(f"{base_url}/robots.txt", verify=verify_tls, timeout=10)
        assert r.status_code in (200, 404), f"/robots.txt returned {r.status_code}"

    def test_static_assets_no_server_error(
        self, base_url: str, verify_tls: bool
    ) -> None:
        r = requests.get(
            f"{base_url}/static/",
            verify=verify_tls,
            timeout=10,
            allow_redirects=True,
        )
        assert r.status_code < 500

    def test_api_root_no_server_error(self, anon_http: Session, base_url: str) -> None:
        r = anon_http.get(f"{base_url}/api/", timeout=10)
        assert r.status_code < 500


class TestPublicSearchPage:
    """Public /search page — no login needed."""

    def test_search_page_loads(self, base_url: str, verify_tls: bool) -> None:
        r = requests.get(
            f"{base_url}/search", verify=verify_tls, timeout=15, allow_redirects=True
        )
        assert r.status_code == 200

    def test_api_search_public(self, anon_http: Session, base_url: str) -> None:
        r = anon_http.get(f"{base_url}/api/search", params={"size": 1})
        assert_ok(r, 200)
        assert "hits" in r.json()

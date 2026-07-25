#
# This file is part of GEO Knowledge Hub.
# Copyright 2020-2021 GEO Secretariat.
#
# GEO Knowledge Hub is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Module UI/login test"""

from __future__ import annotations

import pytest
import requests
from requests import Session

from geodeploy.packages import PackagesClient
from geodeploy.resources import ResourcesClient
from tests.fixtures import assert_ok


@pytest.fixture()
def packages(http: Session, base_url: str) -> PackagesClient:
    return PackagesClient(http, base_url)


@pytest.fixture()
def resources(http: Session, base_url: str) -> ResourcesClient:
    return ResourcesClient(http, base_url)


class TestLoginPage:
    """Login UI — no credentials required."""

    def test_login_page_returns_200(self, base_url: str, verify_tls: bool) -> None:
        r = requests.get(
            f"{base_url}/login", verify=verify_tls, timeout=15, allow_redirects=True
        )
        assert r.status_code == 200

    def test_login_page_contains_form(self, base_url: str, verify_tls: bool) -> None:
        r = requests.get(
            f"{base_url}/login", verify=verify_tls, timeout=15, allow_redirects=True
        )
        body = r.text.lower()
        assert "email" in body or "username" in body or "login" in body

    def test_logout_does_not_crash(self, base_url: str, verify_tls: bool) -> None:
        r = requests.get(
            f"{base_url}/logout", verify=verify_tls, timeout=10, allow_redirects=True
        )
        assert r.status_code < 500

    def test_account_page_accessible(self, base_url: str, verify_tls: bool) -> None:
        """Redirects to login if unauthenticated — still should not 5xx."""
        r = requests.get(
            f"{base_url}/account", verify=verify_tls, timeout=10, allow_redirects=True
        )
        assert r.status_code < 500


class TestTokenAuthentication:
    """API token acceptance and rejection."""

    def test_valid_token_accepted(self, packages: PackagesClient) -> None:
        r = packages.list_user_packages(size=1)
        assert_ok(r, 200)

    def test_valid_token_returns_hits(self, packages: PackagesClient) -> None:
        r = packages.list_user_packages(size=1)
        assert "hits" in r.json()

    def test_missing_token_rejected(self, anon_http: Session, base_url: str) -> None:
        r = PackagesClient(anon_http, base_url).list_user_packages()
        assert r.status_code in (401, 403)

    def test_invalid_token_rejected(self, base_url: str, verify_tls: bool) -> None:
        s = requests.Session()
        s.headers["Authorization"] = "Bearer totally-invalid-token-xyz"
        s.verify = verify_tls
        r = PackagesClient(s, base_url).list_user_packages()
        assert r.status_code in (401, 403)

    def test_token_can_read_packages(self, packages: PackagesClient) -> None:
        r = packages.list_published(size=1)
        assert_ok(r, 200)

    def test_token_can_read_records(self, resources: ResourcesClient) -> None:
        r = resources.list_published(size=1)
        assert_ok(r, 200)


class TestUserProfile:
    """User-scoped API endpoints."""

    def test_user_records_endpoint(self, resources: ResourcesClient) -> None:
        r = resources.list_user_records(size=1)
        assert_ok(r, 200)
        assert "hits" in r.json()

    def test_user_packages_endpoint(self, packages: PackagesClient) -> None:
        r = packages.list_user_packages(size=1)
        assert_ok(r, 200)
        assert "hits" in r.json()

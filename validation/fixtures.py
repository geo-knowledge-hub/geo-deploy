#
# This file is part of GEO Knowledge Hub.
# Copyright 2020-2021 GEO Secretariat.
#
# GEO Knowledge Hub is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Module fixtures"""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from requests import Session

from validation.client.base import BaseClient
from validation.client.communities import CommunitiesClient
from validation.client.doi import DOIClient, doi_configured
from validation.client.packages import PackagesClient
from validation.client.resources import ResourcesClient
from validation.factories import (
    make_community_payload,
    make_package_payload,
    make_package_payload_with_files,
    make_resource_payload,
    make_resource_payload_with_files,
)

# ---------------------------------------------------------------------------
# Core session fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def base_url(request: pytest.FixtureRequest) -> str:
    """Base URL of the GEO Knowledge Hub instance (no trailing slash)."""
    return request.config.getoption("--base-url").rstrip("/")


@pytest.fixture(scope="session")
def api_token(request: pytest.FixtureRequest) -> str:
    """Bearer token — from --api-token flag or GKH_API_TOKEN env var."""
    token = request.config.getoption("--api-token") or os.getenv("GKH_API_TOKEN", "")
    if not token:
        pytest.skip("No API token provided. Use --api-token or set GKH_API_TOKEN.")
    return token


@pytest.fixture(scope="session")
def verify_tls(request: pytest.FixtureRequest) -> bool:
    """False when --no-verify-tls is passed (self-signed / IP-based certs)."""
    return not request.config.getoption("--no-verify-tls")

    """
    Authenticated requests.Session.
    Shared across the entire test run for performance.

    Headers included:
      - Authorization: Bearer token
      - Content-Type:  application/json
      - Referer:       base_url  (required by InvenioRDM CSRF protection)
      - Origin:        base_url  (companion to Referer for CSRF checks)

    Without Referer/Origin, the server returns:
      400 {"message": "Referer checking failed - no Referer."}
    """


@pytest.fixture(scope="session")
def http(base_url: str, api_token: str, verify_tls: bool) -> Session:
    s = Session()
    s.verify = verify_tls

    # Step 1: hit the homepage to establish a session cookie
    s.get(base_url)

    # Step 2: this instance uses session-based CSRF, not csrftoken cookie.
    # Fetch the CSRF token from the API endpoint instead.
    r_csrf = s.get(f"{base_url}/api/")
    csrf = (
        s.cookies.get("csrftoken")
        or s.cookies.get("csrf_token")
        or r_csrf.headers.get("X-CSRFToken")
        or ""
    )

    s.headers.update(
        {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Referer": base_url,
            "Origin": base_url,
            "X-CSRFToken": csrf,
        }
    )

    return s


@pytest.fixture(scope="session")
def anon_http(verify_tls: bool) -> Session:
    """
    Unauthenticated requests.Session.
    Used to verify that public endpoints are accessible and
    protected endpoints correctly reject anonymous requests.
    """
    s = Session()
    s.verify = verify_tls
    return s


# ---------------------------------------------------------------------------
# Resource fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def resource_draft(http: Session, base_url: str) -> Generator[dict, None, None]:
    """
    Create a fresh metadata-only Resource draft before the test,
    delete it after the test completes (pass or fail).
    """
    resources = ResourcesClient(http, base_url)
    r = resources.create_draft(make_resource_payload())
    assert r.status_code == 201, f"Failed to create resource draft: {r.text}"
    data = r.json()
    yield data
    resources.delete_draft(data["id"])


@pytest.fixture()
def resource_draft_with_files(
    http: Session, base_url: str
) -> Generator[dict, None, None]:
    """
    Resource draft with file uploads enabled.
    Use this fixture in upload tests.
    """
    resources = ResourcesClient(http, base_url)
    r = resources.create_draft(make_resource_payload_with_files())
    assert r.status_code == 201, f"Failed to create resource draft (files): {r.text}"
    data = r.json()
    yield data
    resources.delete_draft(data["id"])


@pytest.fixture(scope="session")
def published_resource(http: Session, base_url: str) -> Generator[dict, None, None]:
    """
    Create, reserve DOI, and publish ONE Resource for the entire test run.
    DOI is required on this instance (marked * in the UI).
    """
    resources = ResourcesClient(http, base_url)
    doi = DOIClient(http, base_url)

    r = resources.create_draft(make_resource_payload())
    assert r.status_code == 201, f"Failed to create resource draft: {r.text}"
    rid = r.json()["id"]

    # Reserve DOI before publishing
    r_doi = doi.reserve_doi_for_record(rid)

    if not doi_configured(r_doi):
        pytest.skip(
            f"DOI provider not configured on this instance ({r_doi.status_code}); "
            "publishing here requires a reserved DOI."
        )

    assert r_doi.status_code in (200, 201), (
        f"Failed to reserve DOI: {r_doi.status_code} {r_doi.text}"
    )

    r_pub = resources.publish(rid)
    assert r_pub.status_code == 202, (
        f"Failed to publish resource: {r_pub.status_code} {r_pub.text}"
    )
    yield r_pub.json()


# ---------------------------------------------------------------------------
# Package fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def package_draft(http: Session, base_url: str) -> Generator[dict, None, None]:
    """
    Fresh metadata-only Package draft, deleted after each test.
    """
    packages = PackagesClient(http, base_url)
    r = packages.create_draft(make_package_payload())
    assert r.status_code == 201, f"Failed to create package draft: {r.text}"
    data = r.json()
    yield data
    packages.delete_draft(data["id"])


@pytest.fixture()
def package_draft_with_files(
    http: Session, base_url: str
) -> Generator[dict, None, None]:
    """
    Package draft with file uploads enabled.
    Use this fixture in upload tests.
    """
    packages = PackagesClient(http, base_url)
    r = packages.create_draft(make_package_payload_with_files())
    assert r.status_code == 201, f"Failed to create package draft (files): {r.text}"
    data = r.json()
    yield data
    packages.delete_draft(data["id"])


@pytest.fixture(scope="session")
def published_package(http: Session, base_url: str) -> Generator[dict, None, None]:
    """
    Create, reserve DOI, and publish ONE Package for the entire test run.
    DOI is required on this instance (marked * in the UI).
    """
    packages = PackagesClient(http, base_url)
    doi = DOIClient(http, base_url)

    r = packages.create_draft(make_package_payload())
    assert r.status_code == 201, f"Failed to create package draft: {r.text}"
    pid = r.json()["id"]

    # Reserve DOI before publishing
    r_doi = doi.reserve_doi_for_package(pid)

    if not doi_configured(r_doi):
        pytest.skip(
            f"DOI provider not configured on this instance ({r_doi.status_code}); "
            "publishing here requires a reserved DOI."
        )

    assert r_doi.status_code in (200, 201), (
        f"Failed to reserve DOI: {r_doi.status_code} {r_doi.text}"
    )

    r_pub = packages.publish(pid)
    assert r_pub.status_code == 202, (
        f"Failed to publish package: {r_pub.status_code} {r_pub.text}"
    )
    yield r_pub.json()


# ---------------------------------------------------------------------------
# Community fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def community(http: Session, base_url: str) -> Generator[dict, None, None]:
    """
    Create a Community before the test, delete it after.
    """
    communities = CommunitiesClient(http, base_url)
    r = communities.create(make_community_payload())
    assert r.status_code == 201, f"Failed to create community: {r.text}"
    data = r.json()
    yield data
    communities.delete(data["id"])


# ---------------------------------------------------------------------------
# Shared helper (importable by test files)
# ---------------------------------------------------------------------------

# Re-exported so test files can `from validation.fixtures import assert_ok` without
# needing to know it actually lives on BaseClient — single source of truth,
# no duplicated status-code-check logic.
assert_ok = BaseClient.assert_ok

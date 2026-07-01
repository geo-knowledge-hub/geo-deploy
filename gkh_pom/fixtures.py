"""
fixtures.py
===========
All pytest fixtures for the GEO Knowledge Hub test suite.

Fixture scopes:
  session  → created once per pytest run  (http session, base_url, token)
  function → created fresh for each test  (draft records, communities)

Fixtures are re-exported via conftest.py so pytest finds them automatically
in all subdirectories (tests/api/, tests/ui/).
"""

from __future__ import annotations

import os
from typing import Generator

import pytest
from requests import Response, Session

from factories import (
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
    """Bearer token — from --api-token flag or GEO_API_TOKEN env var."""
    token = request.config.getoption("--api-token") or os.getenv("GEO_API_TOKEN", "")
    if not token:
        pytest.skip("No API token provided. Use --api-token or set GEO_API_TOKEN.")
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
    r = http.post(f"{base_url}/api/records", json=make_resource_payload())
    assert r.status_code == 201, f"Failed to create resource draft: {r.text}"
    data = r.json()
    yield data
    http.delete(f"{base_url}/api/records/{data['id']}/draft")


@pytest.fixture()
def resource_draft_with_files(
    http: Session, base_url: str
) -> Generator[dict, None, None]:
    """
    Resource draft with file uploads enabled.
    Use this fixture in upload tests.
    """
    r = http.post(
        f"{base_url}/api/records",
        json=make_resource_payload_with_files(),
    )
    assert r.status_code == 201, f"Failed to create resource draft (files): {r.text}"
    data = r.json()
    yield data
    http.delete(f"{base_url}/api/records/{data['id']}/draft")


@pytest.fixture(scope="session")
def published_resource(http: Session, base_url: str) -> Generator[dict, None, None]:
    """
    Create, reserve DOI, and publish ONE Resource for the entire test run.
    DOI is required on this instance (marked * in the UI).
    """
    r = http.post(f"{base_url}/api/records", json=make_resource_payload())
    assert r.status_code == 201, f"Failed to create resource draft: {r.text}"
    rid = r.json()["id"]

    # Reserve DOI before publishing
    r_doi = http.post(f"{base_url}/api/records/{rid}/draft/pids/doi")
    assert r_doi.status_code in (200, 201), (
        f"Failed to reserve DOI: {r_doi.status_code} {r_doi.text}"
    )

    r_pub = http.post(f"{base_url}/api/records/{rid}/draft/actions/publish")
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
    r = http.post(f"{base_url}/api/packages", json=make_package_payload())
    assert r.status_code == 201, f"Failed to create package draft: {r.text}"
    data = r.json()
    yield data
    http.delete(f"{base_url}/api/packages/{data['id']}/draft")


@pytest.fixture()
def package_draft_with_files(
    http: Session, base_url: str
) -> Generator[dict, None, None]:
    """
    Package draft with file uploads enabled.
    Use this fixture in upload tests.
    """
    r = http.post(
        f"{base_url}/api/packages",
        json=make_package_payload_with_files(),
    )
    assert r.status_code == 201, f"Failed to create package draft (files): {r.text}"
    data = r.json()
    yield data
    http.delete(f"{base_url}/api/packages/{data['id']}/draft")


@pytest.fixture(scope="session")
def published_package(http: Session, base_url: str) -> Generator[dict, None, None]:
    """
    Create, reserve DOI, and publish ONE Package for the entire test run.
    DOI is required on this instance (marked * in the UI).
    """
    r = http.post(f"{base_url}/api/packages", json=make_package_payload())
    assert r.status_code == 201, f"Failed to create package draft: {r.text}"
    pid = r.json()["id"]

    # Reserve DOI before publishing
    r_doi = http.post(f"{base_url}/api/packages/{pid}/draft/pids/doi")
    assert r_doi.status_code in (200, 201), (
        f"Failed to reserve DOI: {r_doi.status_code} {r_doi.text}"
    )

    r_pub = http.post(f"{base_url}/api/packages/{pid}/draft/actions/publish")
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
    r = http.post(f"{base_url}/api/communities", json=make_community_payload())
    assert r.status_code == 201, f"Failed to create community: {r.text}"
    data = r.json()
    yield data
    http.delete(f"{base_url}/api/communities/{data['id']}")


# ---------------------------------------------------------------------------
# Shared helper (importable by test files)
# ---------------------------------------------------------------------------


def assert_ok(r: Response, *expected: int) -> None:
    """
    Assert the response status code is one of the expected codes.
    Prints the response body on failure to aid debugging.

    Usage:
        assert_ok(r, 200)
        assert_ok(r, 200, 201, 204)
    """
    codes = expected or (200,)
    assert r.status_code in codes, (
        f"Expected {codes}, got {r.status_code}\n{r.text[:600]}"
    )

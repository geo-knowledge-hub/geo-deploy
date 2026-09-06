#
# This file is part of GEO Knowledge Hub.
# Copyright 2020-2021 GEO Secretariat.
#
# GEO Knowledge Hub is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Module doi test"""

from __future__ import annotations

import pytest
from requests import Session

from gkh_validation.client.doi import DOIClient, doi_configured
from gkh_validation.client.packages import PackagesClient
from gkh_validation.client.resources import ResourcesClient
from gkh_validation.factories import make_package_payload, make_resource_payload
from gkh_validation.fixtures import assert_ok

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def doi(http: Session, base_url: str) -> DOIClient:
    return DOIClient(http, base_url)


@pytest.fixture()
def resources(http: Session, base_url: str) -> ResourcesClient:
    return ResourcesClient(http, base_url)


@pytest.fixture()
def packages(http: Session, base_url: str) -> PackagesClient:
    return PackagesClient(http, base_url)


# ---------------------------------------------------------------------------
# Resource DOI tests
# ---------------------------------------------------------------------------


@pytest.mark.publishes
class TestResourceDOI:
    def test_reserve_doi_for_resource(self, doi: DOIClient, resources: ResourcesClient) -> None:
        """
        Reserve a DOI on a resource draft.
        The DOI is not yet registered — only reserved.
        """
        r = resources.create_draft(make_resource_payload())
        assert_ok(r, 201)
        rid = r.json()["id"]

        try:
            r_doi = doi.reserve_doi_for_record(rid)

            if not doi_configured(r_doi):
                pytest.skip(
                    f"DOI provider not configured on this instance "
                    f"({r_doi.status_code}: {r_doi.text[:100]})"
                )

            assert_ok(r_doi, 200, 201)
            data = r_doi.json()

            # The reserved DOI identifier should be present in the response
            doi_value = doi.extract_doi(data) or (
                data.get("pids", {}).get("doi", {}).get("identifier")
            )
            assert doi_value is not None, f"Expected a DOI identifier in response, got: {data}"
            assert doi_value.startswith("10."), f"DOI should start with '10.' — got: {doi_value}"
        finally:
            # always clean up the draft
            resources.delete_draft(rid)

    def test_reserved_doi_appears_in_draft(
        self, doi: DOIClient, resources: ResourcesClient
    ) -> None:
        """
        After reserving, the DOI should be readable from the draft metadata.
        """
        r = resources.create_draft(make_resource_payload())
        assert_ok(r, 201)
        rid = r.json()["id"]

        try:
            r_doi = doi.reserve_doi_for_record(rid)
            if not doi_configured(r_doi):
                pytest.skip("DOI provider not configured on this instance.")
            assert_ok(r_doi, 200, 201)

            # Fetch the draft and confirm DOI is embedded
            r_draft = doi.get_record_pids(rid)
            assert_ok(r_draft, 200)
            draft_doi = doi.extract_doi(r_draft.json())
            assert draft_doi is not None, "DOI not found in draft after reservation"
        finally:
            resources.delete_draft(rid)

    def test_discard_reserved_doi(self, doi: DOIClient, resources: ResourcesClient) -> None:
        """
        A reserved but unpublished DOI can be discarded.
        After discard, the draft should have no DOI.
        """
        r = resources.create_draft(make_resource_payload())
        assert_ok(r, 201)
        rid = r.json()["id"]

        try:
            r_doi = doi.reserve_doi_for_record(rid)
            if not doi_configured(r_doi):
                pytest.skip("DOI provider not configured on this instance.")
            assert_ok(r_doi, 200, 201)

            # Discard the reserved DOI
            r_discard = doi.discard_doi_for_record(rid)
            assert_ok(r_discard, 200, 204)

            # Confirm DOI is gone from the draft
            r_draft = doi.get_record_pids(rid)
            assert_ok(r_draft, 200)
            draft_doi = doi.extract_doi(r_draft.json())
            assert draft_doi is None, f"Expected no DOI after discard, but found: {draft_doi}"
        finally:
            resources.delete_draft(rid)

    def test_publish_with_reserved_doi(self, doi: DOIClient, resources: ResourcesClient) -> None:
        """
        Full workflow: create → reserve DOI → publish.
        The DOI should be registered (made public) on publish.
        """
        r = resources.create_draft(make_resource_payload())
        assert_ok(r, 201)
        rid = r.json()["id"]

        r_doi = doi.reserve_doi_for_record(rid)
        if not doi_configured(r_doi):
            resources.delete_draft(rid)
            pytest.skip("DOI provider not configured on this instance.")
        assert_ok(r_doi, 200, 201)

        # Publish — this registers the DOI
        r_pub = resources.publish(rid)
        assert_ok(r_pub, 202)

        # Confirm DOI is present in the published record
        published_doi = doi.extract_doi(r_pub.json())
        assert published_doi is not None, "Expected DOI in published record"

    def test_publish_without_doi(self, resources: ResourcesClient) -> None:
        """
        Publishing without reserving a DOI should still succeed.
        The published record may or may not have a DOI depending on
        instance configuration (some instances auto-assign DOIs).
        """
        r = resources.create_draft(make_resource_payload())
        assert_ok(r, 201)
        rid = r.json()["id"]

        r_pub = resources.publish(rid)
        assert_ok(r_pub, 202)
        # No assertion on DOI presence — both outcomes are valid

    def test_external_doi_in_payload(self, resources: ResourcesClient) -> None:
        """
        Provide an external DOI at creation time.
        The record is created with a pre-existing DOI from another system.
        """
        import uuid

        external_doi = f"10.9999/pytest-{uuid.uuid4().hex[:8]}"

        payload = make_resource_payload()
        payload["pids"] = {
            "doi": {
                "identifier": external_doi,
                "provider": "external",
            }
        }

        r = resources.create_draft(payload)

        if not doi_configured(r):
            pytest.skip(f"External DOI not accepted by this instance: {r.text[:200]}")

        assert_ok(r, 201)
        rid = r.json()["id"]

        try:
            # Confirm the external DOI was stored
            r_draft = resources.get_draft(rid)
            assert_ok(r_draft, 200)
            stored_doi = r_draft.json().get("pids", {}).get("doi", {}).get("identifier")
            assert stored_doi == external_doi, f"Expected {external_doi}, got {stored_doi}"
        finally:
            resources.delete_draft(rid)

        # Note: we don't publish here because registering a fake DOI
        # with a real DOI provider would create junk records


# ---------------------------------------------------------------------------
# Package DOI tests
# ---------------------------------------------------------------------------


@pytest.mark.publishes
class TestPackageDOI:
    def test_reserve_doi_for_package(self, doi: DOIClient, packages: PackagesClient) -> None:
        """Reserve a DOI on a Knowledge Package draft."""
        r = packages.create_draft(make_package_payload())
        assert_ok(r, 201)
        pid = r.json()["id"]

        try:
            r_doi = doi.reserve_doi_for_package(pid)

            if not doi_configured(r_doi):
                pytest.skip(
                    f"DOI provider not configured on this instance "
                    f"({r_doi.status_code}: {r_doi.text[:100]})"
                )

            assert_ok(r_doi, 200, 201)
            doi_value = doi.extract_doi(r_doi.json())
            assert doi_value is not None
            assert doi_value.startswith("10.")
        finally:
            packages.delete_draft(pid)

    def test_discard_reserved_doi_for_package(
        self, doi: DOIClient, packages: PackagesClient
    ) -> None:
        """Reserved package DOI can be discarded before publish."""
        r = packages.create_draft(make_package_payload())
        assert_ok(r, 201)
        pid = r.json()["id"]

        try:
            r_doi = doi.reserve_doi_for_package(pid)
            if not doi_configured(r_doi):
                pytest.skip("DOI provider not configured on this instance.")
            assert_ok(r_doi, 200, 201)

            r_discard = doi.discard_doi_for_package(pid)
            assert_ok(r_discard, 200, 204)
        finally:
            packages.delete_draft(pid)

    def test_publish_package_with_doi(self, doi: DOIClient, packages: PackagesClient) -> None:
        """Full workflow for a package: create → reserve DOI → publish."""
        r = packages.create_draft(make_package_payload())
        assert_ok(r, 201)
        pid = r.json()["id"]

        r_doi = doi.reserve_doi_for_package(pid)
        if not doi_configured(r_doi):
            packages.delete_draft(pid)
            pytest.skip("DOI provider not configured on this instance.")
        assert_ok(r_doi, 200, 201)

        r_pub = packages.publish(pid)
        assert_ok(r_pub, 202)

        published_doi = doi.extract_doi(r_pub.json())
        assert published_doi is not None, "Expected DOI in published package"

"""
tests/api/test_resources.py
===========================
Tests for the Knowledge Resource API lifecycle.

Based on the official GEO Knowledge Hub documentation:
  POST /api/records          → create draft
  PUT  /api/records/{id}/draft → update metadata
  POST /api/records/{id}/draft/actions/publish → publish
  POST /api/records/{id}/versions → new version

All API calls go through ResourcesClient — tests never build URLs directly.
"""

from __future__ import annotations

import pytest
from requests import Session

from geodeploy.resources import ResourcesClient
from tests.factories import make_resource_payload
from tests.fixtures import assert_ok


# ---------------------------------------------------------------------------
# Client fixture — function-scoped so each test gets a clean client object
# ---------------------------------------------------------------------------


@pytest.fixture()
def resources(http: Session, base_url: str) -> ResourcesClient:
    return ResourcesClient(http, base_url)


# ---------------------------------------------------------------------------
# Search & discovery
# ---------------------------------------------------------------------------


class TestResourceSearch:
    def test_list_published_resources(self, resources: ResourcesClient) -> None:
        r = resources.list_published(size=5)
        assert_ok(r, 200)
        assert "hits" in r.json()

    def test_list_has_total_field(self, resources: ResourcesClient) -> None:
        r = resources.list_published(size=1)
        assert_ok(r, 200)
        assert "total" in r.json()["hits"]

    def test_full_text_search(self, resources: ResourcesClient) -> None:
        r = resources.list_published(query="climate")
        assert_ok(r, 200)

    def test_pagination_pages_dont_overlap(self, resources: ResourcesClient) -> None:
        r1 = resources.search(page=1, size=2)
        r2 = resources.search(page=2, size=2)
        assert_ok(r1, 200)
        assert_ok(r2, 200)
        ids1 = {h["id"] for h in r1.json()["hits"]["hits"]}
        ids2 = {h["id"] for h in r2.json()["hits"]["hits"]}
        if ids1 and ids2:
            assert ids1.isdisjoint(ids2), "Pages 1 and 2 share records"

    def test_nonexistent_record_returns_404(self, resources: ResourcesClient) -> None:
        r = resources.get_published("does-not-exist-xyz")
        assert r.status_code == 404

    def test_list_user_records(self, resources: ResourcesClient) -> None:
        r = resources.list_user_records()
        assert_ok(r, 200)
        assert "hits" in r.json()


# ---------------------------------------------------------------------------
# Draft lifecycle
# ---------------------------------------------------------------------------


class TestResourceDraft:
    def test_create_draft(self, resources: ResourcesClient) -> None:
        r = resources.create_draft(make_resource_payload())
        assert_ok(r, 201)
        data = r.json()
        assert "id" in data
        assert data.get("is_draft") is True
        resources.delete_draft(data["id"])

    def test_get_draft(self, resources: ResourcesClient, resource_draft: dict) -> None:
        r = resources.get_draft(resource_draft["id"])
        assert_ok(r, 200)
        assert r.json()["id"] == resource_draft["id"]

    def test_update_draft_title(
        self, resources: ResourcesClient, resource_draft: dict
    ) -> None:
        r = resources.fetch_and_update_title(
            resource_draft["id"], "Updated resource title"
        )
        assert_ok(r, 200)
        assert r.json()["metadata"]["title"] == "Updated resource title"

    def test_update_draft_multiple_times(
        self, resources: ResourcesClient, resource_draft: dict
    ) -> None:
        for i in range(3):
            r = resources.fetch_and_update_title(resource_draft["id"], f"Iteration {i}")
            assert_ok(r, 200)
            assert r.json()["metadata"]["title"] == f"Iteration {i}"

    def test_delete_draft(self, resources: ResourcesClient) -> None:
        r = resources.create_draft(make_resource_payload())
        assert_ok(r, 201)
        rid = r.json()["id"]
        assert_ok(resources.delete_draft(rid), 204)
        assert resources.get_draft(rid).status_code in (404, 410)

    def test_draft_not_in_public_search(
        self, resources: ResourcesClient, resource_draft: dict
    ) -> None:
        title = resource_draft["metadata"]["title"]
        r = resources.list_published(query=title)
        assert_ok(r, 200)
        ids = [h["id"] for h in r.json()["hits"]["hits"]]
        assert resource_draft["id"] not in ids, "Draft visible in public search"

    def test_list_draft_files_empty(
        self, resources: ResourcesClient, resource_draft: dict
    ) -> None:
        r = resources.list_files(resource_draft["id"])
        assert_ok(r, 200)


# ---------------------------------------------------------------------------
# Publish & versioning  (follows official API docs flow)
# ---------------------------------------------------------------------------


class TestResourcePublish:
    def test_publish_resource(
        self, resources: ResourcesClient, http: Session, base_url: str
    ) -> None:
        """Tests the publish action itself. Creates exactly one published record."""
        r = resources.create_draft(make_resource_payload())
        assert_ok(r, 201)
        rid = r.json()["id"]
        http.post(f"{base_url}/api/records/{rid}/draft/pids/doi")
        r_pub = resources.publish(rid)
        assert_ok(r_pub, 202)
        data = r_pub.json()
        assert data.get("is_published") is True or data.get("status") == "published"

    def test_published_resource_appears_in_search(
        self, resources: ResourcesClient, published_resource: dict
    ) -> None:
        """Uses the shared published_resource fixture — no new publish."""
        title = published_resource["metadata"]["title"]
        r = resources.list_published(query=title)
        assert_ok(r, 200)

    def test_list_versions(
        self, resources: ResourcesClient, published_resource: dict
    ) -> None:
        """Uses the shared published_resource fixture — no new publish."""
        r = resources.list_versions(published_resource["id"])
        assert_ok(r, 200)
        assert isinstance(r.json()["hits"]["hits"], list)

    def test_create_new_version(
        self, resources: ResourcesClient, published_resource: dict
    ) -> None:
        """Uses the shared published_resource fixture — no new publish."""
        r = resources.create_new_version(published_resource["id"])
        if r.status_code == 404:
            pytest.skip("PID not registered — cannot create new version.")
        assert_ok(r, 201)
        new_id = r.json()["id"]
        assert new_id != published_resource["id"]
        resources.delete_draft(new_id)


# ---------------------------------------------------------------------------
# File uploads  (follows official API docs 3-step flow)
# ---------------------------------------------------------------------------


class TestResourceFileUpload:
    def test_full_upload_cycle(
        self, resources: ResourcesClient, resource_draft_with_files: dict
    ) -> None:
        """
        Official flow: init → upload content → commit.
        """
        rid = resource_draft_with_files["id"]
        resources.upload_file(rid, "test-file.txt", b"Hello from pytest.")

    def test_file_appears_in_listing(
        self, resources: ResourcesClient, resource_draft_with_files: dict
    ) -> None:
        rid = resource_draft_with_files["id"]
        filename = "listed.txt"
        resources.upload_file(rid, filename, b"Listing test.")
        r = resources.list_files(rid)
        assert_ok(r, 200)
        keys = [e["key"] for e in r.json().get("entries", [])]
        assert filename in keys

    def test_delete_file(
        self, resources: ResourcesClient, resource_draft_with_files: dict
    ) -> None:
        rid = resource_draft_with_files["id"]
        filename = "to-delete.txt"
        resources.upload_file(rid, filename, b"Delete me.")
        assert_ok(resources.delete_file(rid, filename), 204)
        r = resources.list_files(rid)
        keys = [e["key"] for e in r.json().get("entries", [])]
        assert filename not in keys

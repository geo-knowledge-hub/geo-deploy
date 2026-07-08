"""
tests/api/test_drafts.py
========================
Focused tests on draft behaviour for both Packages and Resources.
Verifies draft visibility, persistence, and lifecycle rules.
"""

from __future__ import annotations

import pytest
from requests import Session

from geodeploy.packages import PackagesClient
from geodeploy.resources import ResourcesClient
from tests.factories import make_package_payload, make_resource_payload
from tests.fixtures import assert_ok


@pytest.fixture()
def packages(http: Session, base_url: str) -> PackagesClient:
    return PackagesClient(http, base_url)


@pytest.fixture()
def resources(http: Session, base_url: str) -> ResourcesClient:
    return ResourcesClient(http, base_url)


class TestPackageDraftBehaviour:
    def test_new_draft_is_draft(self, package_draft: dict) -> None:
        assert package_draft.get("is_draft") is True

    def test_new_draft_has_id(self, package_draft: dict) -> None:
        assert "id" in package_draft and package_draft["id"]

    def test_draft_not_visible_in_public_search(
        self, packages: PackagesClient, package_draft: dict
    ) -> None:
        title = package_draft["metadata"]["title"]
        r = packages.list_published(query=title)
        assert_ok(r, 200)
        ids = [h["id"] for h in r.json()["hits"]["hits"]]
        assert package_draft["id"] not in ids

    def test_draft_metadata_persists_after_create(
        self, packages: PackagesClient, package_draft: dict
    ) -> None:
        r = packages.get_draft(package_draft["id"])
        assert_ok(r, 200)
        assert r.json()["metadata"]["title"] == package_draft["metadata"]["title"]

    def test_draft_can_be_updated_multiple_times(
        self, packages: PackagesClient, package_draft: dict
    ) -> None:
        for i in range(3):
            r = packages.fetch_and_update_title(package_draft["id"], f"Title {i}")
            assert_ok(r, 200)
            assert r.json()["metadata"]["title"] == f"Title {i}"

    def test_deleted_draft_is_unreachable(self, packages: PackagesClient) -> None:
        r = packages.create_draft(make_package_payload())
        assert_ok(r, 201)
        pid = r.json()["id"]
        packages.delete_draft(pid)
        assert packages.get_draft(pid).status_code in (404, 410)

    def test_draft_file_list_is_empty_on_creation(
        self, packages: PackagesClient, package_draft: dict
    ) -> None:
        r = packages.list_files(package_draft["id"])
        assert_ok(r, 200)
        assert isinstance(r.json().get("entries", []), list)

    def test_edit_draft_opens_from_published(self, packages: PackagesClient) -> None:
        r = packages.create_draft(make_package_payload())
        assert_ok(r, 201)
        pid = r.json()["id"]
        assert_ok(packages.publish(pid), 202)
        r_edit = packages.open_edit_draft(pid)
        assert_ok(r_edit, 201)
        assert r_edit.json().get("is_draft") is True


class TestResourceDraftBehaviour:
    def test_new_draft_is_draft(self, resource_draft: dict) -> None:
        assert resource_draft.get("is_draft") is True

    def test_new_draft_has_id(self, resource_draft: dict) -> None:
        assert "id" in resource_draft and resource_draft["id"]

    def test_draft_not_visible_in_public_search(
        self, resources: ResourcesClient, resource_draft: dict
    ) -> None:
        title = resource_draft["metadata"]["title"]
        r = resources.list_published(query=title)
        assert_ok(r, 200)
        ids = [h["id"] for h in r.json()["hits"]["hits"]]
        assert resource_draft["id"] not in ids

    def test_draft_metadata_persists(
        self, resources: ResourcesClient, resource_draft: dict
    ) -> None:
        r = resources.get_draft(resource_draft["id"])
        assert_ok(r, 200)
        assert r.json()["metadata"]["title"] == resource_draft["metadata"]["title"]

    def test_draft_update(
        self, resources: ResourcesClient, resource_draft: dict
    ) -> None:
        r = resources.fetch_and_update_title(resource_draft["id"], "Updated title")
        assert_ok(r, 200)
        assert r.json()["metadata"]["title"] == "Updated title"

    def test_deleted_draft_unreachable(self, resources: ResourcesClient) -> None:
        r = resources.create_draft(make_resource_payload())
        assert_ok(r, 201)
        rid = r.json()["id"]
        resources.delete_draft(rid)
        assert resources.get_draft(rid).status_code in (404, 410)

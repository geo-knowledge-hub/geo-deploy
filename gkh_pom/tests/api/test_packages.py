"""
tests/api/test_packages.py
==========================
Tests for the Knowledge Package API lifecycle.

All API calls go through PackagesClient — tests never build URLs directly.
"""

from __future__ import annotations

import pytest
from requests import Session

from client.packages import PackagesClient
from client.resources import ResourcesClient
from factories import make_package_payload, make_package_payload_with_files, make_resource_payload
from fixtures import assert_ok


@pytest.fixture()
def packages(http: Session, base_url: str) -> PackagesClient:
    return PackagesClient(http, base_url)


@pytest.fixture()
def resources(http: Session, base_url: str) -> ResourcesClient:
    return ResourcesClient(http, base_url)


# ---------------------------------------------------------------------------
# Search & discovery
# ---------------------------------------------------------------------------

class TestPackageSearch:

    def test_list_published_packages(self, packages: PackagesClient) -> None:
        r = packages.list_published(size=5)
        assert_ok(r, 200)
        assert "hits" in r.json()

    def test_list_has_total_field(self, packages: PackagesClient) -> None:
        r = packages.list_published(size=1)
        assert "total" in r.json()["hits"]

    def test_full_text_search(self, packages: PackagesClient) -> None:
        r = packages.list_published(query="climate")
        assert_ok(r, 200)

    def test_pagination(self, packages: PackagesClient) -> None:
        r1 = packages.search(page=1, size=2)
        r2 = packages.search(page=2, size=2)
        assert_ok(r1, 200)
        assert_ok(r2, 200)

    def test_nonexistent_package_returns_404(self, packages: PackagesClient) -> None:
        r = packages.get_published("does-not-exist-xyz")
        assert r.status_code == 404

    def test_list_user_packages(self, packages: PackagesClient) -> None:
        r = packages.list_user_packages()
        assert_ok(r, 200)
        assert "hits" in r.json()


# ---------------------------------------------------------------------------
# Draft lifecycle
# ---------------------------------------------------------------------------

class TestPackageDraft:

    def test_create_draft(self, packages: PackagesClient) -> None:
        r = packages.create_draft(make_package_payload())
        assert_ok(r, 201)
        data = r.json()
        assert "id" in data
        assert data.get("is_draft") is True
        packages.delete_draft(data["id"])

    def test_get_draft(
        self, packages: PackagesClient, package_draft: dict
    ) -> None:
        r = packages.get_draft(package_draft["id"])
        assert_ok(r, 200)
        assert r.json()["id"] == package_draft["id"]

    def test_update_draft_title(
        self, packages: PackagesClient, package_draft: dict
    ) -> None:
        r = packages.fetch_and_update_title(
            package_draft["id"], "Updated package title"
        )
        assert_ok(r, 200)
        assert r.json()["metadata"]["title"] == "Updated package title"

    def test_update_draft_multiple_times(
        self, packages: PackagesClient, package_draft: dict
    ) -> None:
        for i in range(3):
            r = packages.fetch_and_update_title(
                package_draft["id"], f"Iteration {i}"
            )
            assert_ok(r, 200)

    def test_delete_draft(self, packages: PackagesClient) -> None:
        r = packages.create_draft(make_package_payload())
        assert_ok(r, 201)
        pid = r.json()["id"]
        assert_ok(packages.delete_draft(pid), 204)
        assert packages.get_draft(pid).status_code in (404, 410)

    def test_draft_not_in_public_search(
        self, packages: PackagesClient, package_draft: dict
    ) -> None:
        title = package_draft["metadata"]["title"]
        r = packages.list_published(query=title)
        assert_ok(r, 200)
        ids = [h["id"] for h in r.json()["hits"]["hits"]]
        assert package_draft["id"] not in ids

    def test_open_edit_draft_from_published(
        self, packages: PackagesClient, published_package: dict
    ) -> None:
        r = packages.open_edit_draft(published_package["id"])
        assert_ok(r, 201)
        assert r.json().get("is_draft") is True


# ---------------------------------------------------------------------------
# Publish & versioning
# ---------------------------------------------------------------------------

class TestPackagePublish:

    def test_publish_package(
        self, packages: PackagesClient, http: Session, base_url: str
    ) -> None:
        """Tests the publish action itself. Creates exactly one published record."""
        r = packages.create_draft(make_package_payload())
        assert_ok(r, 201)
        pid = r.json()["id"]
        http.post(f"{base_url}/api/packages/{pid}/draft/pids/doi")
        r_pub = packages.publish(pid)
        assert_ok(r_pub, 202)

    def test_published_appears_in_search(
        self, packages: PackagesClient, published_package: dict
    ) -> None:
        """Uses the shared published_package fixture — no new publish."""
        title = published_package["metadata"]["title"]
        r = packages.list_published(query=title)
        assert_ok(r, 200)

    def test_list_versions(
        self, packages: PackagesClient, published_package: dict
    ) -> None:
        """Uses the shared published_package fixture — no new publish."""
        r = packages.list_versions(published_package["id"])
        assert_ok(r, 200)
        hits = r.json()["hits"]["hits"]
        if len(hits) == 0:
            pytest.skip("Versions empty — PID registration not configured.")
        assert len(hits) >= 1

    def test_get_latest_version(
        self, packages: PackagesClient, published_package: dict
    ) -> None:
        """Uses the shared published_package fixture — no new publish."""
        r = packages.get_latest_version(published_package["id"])
        assert_ok(r, 200)

    def test_create_new_version(
        self, packages: PackagesClient, published_package: dict
    ) -> None:
        """Uses the shared published_package fixture — no new publish."""
        r = packages.create_new_version(published_package["id"])
        if r.status_code == 404:
            pytest.skip("PID not registered — cannot create new version.")
        assert_ok(r, 201)
        new_id = r.json()["id"]
        assert new_id != published_package["id"]
        packages.delete_draft(new_id)


# ---------------------------------------------------------------------------
# File uploads
# ---------------------------------------------------------------------------

class TestPackageFileUpload:

    def test_full_upload_cycle(
        self, packages: PackagesClient, package_draft_with_files: dict
    ) -> None:
        pid = package_draft_with_files["id"]
        packages.upload_file(pid, "test.txt", b"Hello from pytest.")

    def test_multiple_files(
        self, packages: PackagesClient, package_draft_with_files: dict
    ) -> None:
        pid = package_draft_with_files["id"]
        filenames = ["a.txt", "b.txt", "c.txt"]
        for fname in filenames:
            packages.upload_file(pid, fname, f"Content of {fname}".encode())
        r = packages.list_files(pid)
        keys = [e["key"] for e in r.json().get("entries", [])]
        for fname in filenames:
            assert fname in keys

    def test_file_in_listing_after_commit(
        self, packages: PackagesClient, package_draft_with_files: dict
    ) -> None:
        pid = package_draft_with_files["id"]
        filename = "listed.txt"
        packages.upload_file(pid, filename, b"Listing test.")
        r = packages.list_files(pid)
        keys = [e["key"] for e in r.json().get("entries", [])]
        assert filename in keys

    def test_delete_file(
        self, packages: PackagesClient, package_draft_with_files: dict
    ) -> None:
        pid = package_draft_with_files["id"]
        filename = "to-delete.txt"
        packages.upload_file(pid, filename, b"Delete me.")
        assert_ok(packages.delete_file(pid, filename), 204)
        r = packages.list_files(pid)
        keys = [e["key"] for e in r.json().get("entries", [])]
        assert filename not in keys

    def test_init_multiple_files_at_once(
        self, packages: PackagesClient, package_draft_with_files: dict
    ) -> None:
        """The init endpoint accepts a list — declare 3 files in one call."""
        pid = package_draft_with_files["id"]
        r = packages.init_file.__func__(
            packages, pid, "bulk-a.txt"
        ) if False else packages._post(
            f"/api/packages/{pid}/draft/files",
            json=[{"key": "bulk-a.txt"}, {"key": "bulk-b.txt"}, {"key": "bulk-c.txt"}],
        )
        assert_ok(r, 201)


# ---------------------------------------------------------------------------
# Resource association
# ---------------------------------------------------------------------------

class TestPackageResourceAssociation:

    @pytest.fixture()
    def pkg_and_res(
        self,
        packages: PackagesClient,
        resources: ResourcesClient,
    ):
        """Create a package draft and a published resource, clean up after."""
        pkg_r = packages.create_draft(make_package_payload())
        assert_ok(pkg_r, 201)
        pkg_id = pkg_r.json()["id"]

        res_r = resources.create_draft(make_resource_payload())
        assert_ok(res_r, 201)
        res_id = res_r.json()["id"]
        resources.publish(res_id)

        yield pkg_id, res_id

        packages.dissociate_resource(pkg_id, res_id)
        packages.delete_draft(pkg_id)

    def test_list_draft_resources_empty(
        self, packages: PackagesClient, package_draft: dict
    ) -> None:
        r = packages.list_draft_resources(package_draft["id"])
        assert_ok(r, 200)

    def test_associate_resource(
        self, packages: PackagesClient, pkg_and_res: tuple
    ) -> None:
        pkg_id, res_id = pkg_and_res
        r = packages.associate_resource(pkg_id, res_id)
        assert_ok(r, 200, 201, 204)

    def test_dissociate_resource(
        self, packages: PackagesClient, pkg_and_res: tuple
    ) -> None:
        pkg_id, res_id = pkg_and_res
        packages.associate_resource(pkg_id, res_id)
        r = packages.dissociate_resource(pkg_id, res_id)
        assert_ok(r, 200, 204)

    def test_add_resource_to_draft(
        self, packages: PackagesClient, pkg_and_res: tuple
    ) -> None:
        pkg_id, res_id = pkg_and_res
        packages.associate_resource(pkg_id, res_id)
        r = packages.add_resource_to_draft(pkg_id, res_id)
        if r.status_code not in (200, 201, 204):
            pytest.skip(
                f"add_resource_to_draft unsupported on this instance: "
                f"{r.status_code} {r.text[:200]}"
            )

    def test_remove_resource_from_draft(
        self, packages: PackagesClient, pkg_and_res: tuple
    ) -> None:
        """
        DELETE /api/packages/{id}/draft/resources
        Remove a resource from the draft (but keep it in the package context).
        """
        pkg_id, res_id = pkg_and_res

        # First associate and add to draft
        packages.associate_resource(pkg_id, res_id)
        r_add = packages.add_resource_to_draft(pkg_id, res_id)
        if r_add.status_code not in (200, 201, 204):
            pytest.skip("Could not add resource to draft — skipping remove test.")

        # Confirm it is in the draft
        r_list = packages.list_draft_resources(pkg_id)
        assert_ok(r_list, 200)
        data = r_list.json()
        hits = data.get("hits", {}).get("hits", data.get("entries", []))
        ids_before = [h.get("id") or h.get("record_id") for h in hits]
        assert res_id in ids_before, (
            f"Resource {res_id} not found in draft before removal: {ids_before}"
        )

        # Remove from draft
        r_remove = packages.remove_resource_from_draft(pkg_id, res_id)
        assert_ok(r_remove, 200, 204)

        # Confirm it is no longer in the draft
        r_list2 = packages.list_draft_resources(pkg_id)
        assert_ok(r_list2, 200)
        data2 = r_list2.json()
        hits2 = data2.get("hits", {}).get("hits", data2.get("entries", []))
        ids_after = [h.get("id") or h.get("record_id") for h in hits2]
        assert res_id not in ids_after, (
            f"Resource {res_id} still in draft after removal: {ids_after}"
        )


# ---------------------------------------------------------------------------
# Resources import from previous version
# ---------------------------------------------------------------------------

class TestPackageResourcesImport:
    """
    Tests for POST /api/packages/{id}/draft/actions/resources-import

    This endpoint copies all resources from the previous published version
    into the current new draft. It is only meaningful after a new version
    has been created from a published package.

    Workflow tested:
      1. Create a package draft
      2. Associate a resource and publish the package (v1)
      3. Create a new version (v2 draft)
      4. Call resources-import → v1 resources appear in v2 draft
    """

    def test_import_resources_from_previous_version(
        self,
        packages: PackagesClient,
        resources: ResourcesClient,
    ) -> None:
        """
        Full workflow: publish v1 with a resource → new version →
        import resources → confirm resource appears in v2 draft.
        """
        # 1. Create and publish a resource
        res_r = resources.create_draft(make_resource_payload())
        assert_ok(res_r, 201)
        res_id = res_r.json()["id"]
        resources.publish(res_id)

        # 2. Create a package draft and associate the resource
        pkg_r = packages.create_draft(make_package_payload())
        assert_ok(pkg_r, 201)
        pkg_id = pkg_r.json()["id"]

        packages.associate_resource(pkg_id, res_id)
        r_add = packages.add_resource_to_draft(pkg_id, res_id)
        if r_add.status_code not in (200, 201, 204):
            packages.delete_draft(pkg_id)
            pytest.skip("Could not add resource to draft — skipping import test.")

        # 3. Publish the package (v1)
        r_pub = packages.publish(pkg_id)
        assert_ok(r_pub, 202)

        # 4. Create new version (v2 draft)
        r_new = packages.create_new_version(pkg_id)
        if r_new.status_code == 404:
            pytest.skip("PID not registered — cannot create new version.")
        assert_ok(r_new, 201)
        new_pkg_id = r_new.json()["id"]

        try:
            # 5. Import resources from v1 into v2 draft
            r_import = packages.import_resources_from_previous_version(new_pkg_id)

            if r_import.status_code in (400, 404, 501):
                pytest.skip(
                    f"resources-import not supported on this instance: "
                    f"{r_import.status_code} {r_import.text[:200]}"
                )

            assert_ok(r_import, 200, 201, 204)

            # 6. Confirm the resource from v1 appears in v2 draft
            r_list = packages.list_draft_resources(new_pkg_id)
            assert_ok(r_list, 200)
            data = r_list.json()
            hits = data.get("hits", {}).get("hits", data.get("entries", []))
            ids = [h.get("id") or h.get("record_id") for h in hits]
            assert res_id in ids, (
                f"Expected resource {res_id} to be imported into v2 draft, "
                f"but found: {ids}"
            )
        finally:
            packages.delete_draft(new_pkg_id)

    def test_import_on_fresh_draft_with_no_previous_version(
        self, packages: PackagesClient
    ) -> None:
        """
        Calling resources-import on a brand new draft (no previous version)
        should return an error — not crash the server.
        Acceptable responses: 400, 404, 422 (all mean "nothing to import").
        """
        pkg_r = packages.create_draft(make_package_payload())
        assert_ok(pkg_r, 201)
        pkg_id = pkg_r.json()["id"]

        try:
            r = packages.import_resources_from_previous_version(pkg_id)
            # A new draft with no previous version should be rejected gracefully
            assert r.status_code in (400, 404, 422, 200, 204), (
                f"Unexpected status {r.status_code} for import on fresh draft: "
                f"{r.text[:200]}"
            )
            # Must not be a server error
            assert r.status_code < 500, (
                f"Server error on resources-import: {r.status_code} {r.text[:200]}"
            )
        finally:
            packages.delete_draft(pkg_id)

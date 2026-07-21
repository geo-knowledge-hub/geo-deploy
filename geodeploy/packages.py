# -*- coding: utf-8 -*-
#
# This file is part of GEO Knowledge Hub.
# Copyright 2020-2021 GEO Secretariat.
#
# GEO Knowledge Hub is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Module PackagesClient"""



from __future__ import annotations

from requests import Response

from geodeploy.base import BaseClient


class PackagesClient(BaseClient):
    """Page Object for the Knowledge Packages API."""

    # ------------------------------------------------------------------
    # Search & discovery
    # ------------------------------------------------------------------

    def list_published(self, size: int = 5, query: str = "") -> Response:
        """GET /api/packages — list published packages."""
        params = {"size": size}
        if query:
            params["q"] = query
        return self._get("/api/packages", params=params)

    def get_published(self, package_id: str) -> Response:
        """GET /api/packages/{id} — get a single published package."""
        return self._get(f"/api/packages/{package_id}")

    def list_user_packages(self, size: int = 5) -> Response:
        """GET /api/user/packages — current user's packages."""
        return self._get("/api/user/packages", params={"size": size})

    def search(self, query: str = "", page: int = 1, size: int = 5) -> Response:
        """GET /api/packages with full pagination support."""
        return self._get(
            "/api/packages", params={"q": query, "page": page, "size": size}
        )

    # ------------------------------------------------------------------
    # Draft management
    # ------------------------------------------------------------------

    def create_draft(self, payload: dict) -> Response:
        """POST /api/packages — create a new package draft."""
        return self._post("/api/packages", json=payload)

    def get_draft(self, package_id: str) -> Response:
        """GET /api/packages/{id}/draft — retrieve a draft."""
        return self._get(f"/api/packages/{package_id}/draft")

    def update_draft(self, package_id: str, payload: dict) -> Response:
        """PUT /api/packages/{id}/draft — update draft metadata."""
        return self._put(f"/api/packages/{package_id}/draft", json=payload)

    def delete_draft(self, package_id: str) -> Response:
        """DELETE /api/packages/{id}/draft — discard a draft."""
        return self._delete(f"/api/packages/{package_id}/draft")

    def open_edit_draft(self, package_id: str) -> Response:
        """POST /api/packages/{id}/draft — open an edit draft from a published package."""
        return self._post(f"/api/packages/{package_id}/draft")

    def fetch_and_update_title(self, package_id: str, new_title: str) -> Response:
        """
        Convenience method: GET current draft, change title, PUT back.
        Avoids 500 errors from sending incomplete payloads.
        """
        r = self.get_draft(package_id)
        self.assert_ok(r, 200)
        current = r.json()
        current["metadata"]["title"] = new_title
        return self.update_draft(package_id, current)

    # ------------------------------------------------------------------
    # File uploads (3-step: init → content → commit)
    # ------------------------------------------------------------------

    def init_file(self, package_id: str, filename: str) -> Response:
        """POST /api/packages/{id}/draft/files — declare a file upload."""
        return self._post(
            f"/api/packages/{package_id}/draft/files",
            json=[{"key": filename}],
        )

    def upload_file_content(
        self, package_id: str, filename: str, content: bytes
    ) -> Response:
        """PUT /api/packages/{id}/draft/files/{filename}/content — upload bytes."""
        return self._put_binary(
            f"/api/packages/{package_id}/draft/files/{filename}/content",
            content,
        )

    def commit_file(self, package_id: str, filename: str) -> Response:
        """POST /api/packages/{id}/draft/files/{filename}/commit."""
        return self._post(f"/api/packages/{package_id}/draft/files/{filename}/commit")

    def upload_file(self, package_id: str, filename: str, content: bytes) -> None:
        """Full 3-step upload: init → content → commit."""
        self.assert_ok(self.init_file(package_id, filename), 201)
        self.assert_ok(self.upload_file_content(package_id, filename, content), 200)
        self.assert_ok(self.commit_file(package_id, filename), 200)

    def list_files(self, package_id: str) -> Response:
        """GET /api/packages/{id}/draft/files."""
        return self._get(f"/api/packages/{package_id}/draft/files")

    def delete_file(self, package_id: str, filename: str) -> Response:
        """DELETE /api/packages/{id}/draft/files/{filename}."""
        return self._delete(f"/api/packages/{package_id}/draft/files/{filename}")

    # ------------------------------------------------------------------
    # Publish & versions
    # ------------------------------------------------------------------

    def publish(self, package_id: str) -> Response:
        """POST /api/packages/{id}/draft/actions/publish."""
        return self._post(f"/api/packages/{package_id}/draft/actions/publish")

    def list_versions(self, package_id: str) -> Response:
        """GET /api/packages/{id}/versions."""
        return self._get(f"/api/packages/{package_id}/versions")

    def get_latest_version(self, package_id: str) -> Response:
        """GET /api/packages/{id}/versions/latest."""
        return self._get(f"/api/packages/{package_id}/versions/latest")

    def create_new_version(self, package_id: str) -> Response:
        """POST /api/packages/{id}/versions — open a new version draft."""
        return self._post(f"/api/packages/{package_id}/versions")

    # ------------------------------------------------------------------
    # Resource association
    # ------------------------------------------------------------------

    def associate_resource(self, package_id: str, resource_id: str) -> Response:
        """POST /api/packages/{id}/context/actions/associate."""
        return self._post(
            f"/api/packages/{package_id}/context/actions/associate",
            json={"records": [{"id": resource_id}]},
        )

    def dissociate_resource(self, package_id: str, resource_id: str) -> Response:
        """POST /api/packages/{id}/context/actions/dissociate."""
        return self._post(
            f"/api/packages/{package_id}/context/actions/dissociate",
            json={"records": [{"id": resource_id}]},
        )

    def add_resource_to_draft(self, package_id: str, resource_id: str) -> Response:
        """
        POST /api/packages/{id}/draft/resources.
        Tries multiple body shapes across GKH versions.
        """
        for body in [
            {"records": [{"id": resource_id}]},
            {"ids": [resource_id]},
            {"record_ids": [resource_id]},
            [{"id": resource_id}],
        ]:
            r = self._post(f"/api/packages/{package_id}/draft/resources", json=body)
            if r.status_code in (200, 201, 204):
                return r
        return r  # return last response for caller to inspect

    def list_draft_resources(self, package_id: str) -> Response:
        """GET /api/packages/{id}/draft/resources."""
        return self._get(f"/api/packages/{package_id}/draft/resources")

    def remove_resource_from_draft(self, package_id: str, resource_id: str) -> Response:
        """
        DELETE /api/packages/{id}/draft/resources
        Remove a specific resource from the current draft.
        The resource remains associated with the package context —
        use dissociate_resource() to fully remove it from the package.
        """
        return self._delete(
            f"/api/packages/{package_id}/draft/resources",
            json={"records": [{"id": resource_id}]},
        )

    def import_resources_from_previous_version(self, package_id: str) -> Response:
        """
        POST /api/packages/{id}/draft/actions/resources-import
        Import all Resources from the previous published version into
        the current new draft. Used when creating a new version of a
        package to carry forward existing resources automatically.

        Workflow:
          1. publish package (v1)
          2. create new version → POST /api/packages/{id}/versions
          3. call this method on the new draft to import v1 resources
          4. edit / add more resources
          5. publish (v2)
        """
        return self._post(f"/api/packages/{package_id}/draft/actions/resources-import")

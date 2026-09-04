#
# This file is part of GEO Knowledge Hub.
# Copyright 2020-2021 GEO Secretariat.
#
# GEO Knowledge Hub is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Module ResourcesClient"""

from __future__ import annotations

from requests import Response

from validation.client.base import BaseClient


class ResourcesClient(BaseClient):
    """
    Page Object for the Knowledge Resources API.

    Usage in tests:
        resources = ResourcesClient(http, base_url)
        r = resources.create_draft(payload)
    """

    base_path = "/api/records"

    # ------------------------------------------------------------------
    # Search & discovery
    # ------------------------------------------------------------------

    def list_published(self, size: int = 5, query: str = "") -> Response:
        """GET /api/records — list published resources."""
        params = {"size": size}
        if query:
            params["q"] = query
        return self._get(self._resource_path(), params=params)

    def get_published(self, record_id: str) -> Response:
        """GET /api/records/{id} — get a single published resource."""
        return self._get(self._resource_path(record_id))

    def list_user_records(self, size: int = 5) -> Response:
        """GET /api/user/records — current user's records."""
        return self._get(self._path("api", "user", "records"), params={"size": size})

    def search(self, query: str = "", page: int = 1, size: int = 5) -> Response:
        """GET /api/records with full pagination support."""
        return self._get(
            self._resource_path(), params={"q": query, "page": page, "size": size}
        )

    # ------------------------------------------------------------------
    # Draft management
    # ------------------------------------------------------------------

    def create_draft(self, payload: dict) -> Response:
        """POST /api/records — create a new resource draft."""
        return self._post(self._resource_path(), json=payload)

    def get_draft(self, record_id: str) -> Response:
        """GET /api/records/{id}/draft — retrieve a draft."""
        return self._get(self._resource_path(record_id, "draft"))

    def update_draft(self, record_id: str, payload: dict) -> Response:
        """
        PUT /api/records/{id}/draft — update draft metadata.
        Best practice: fetch the current draft first, mutate, then PUT.
        """
        return self._put(self._resource_path(record_id, "draft"), json=payload)

    def delete_draft(self, record_id: str) -> Response:
        """DELETE /api/records/{id}/draft — discard a draft."""
        return self._delete(self._resource_path(record_id, "draft"))

    def fetch_and_update_title(self, record_id: str, new_title: str) -> Response:
        """
        Convenience method: GET current draft, change title, PUT back.
        Avoids 500 errors caused by sending incomplete payloads.
        """
        r = self.get_draft(record_id)
        self.assert_ok(r, 200)
        current = r.json()
        current["metadata"]["title"] = new_title
        return self.update_draft(record_id, current)

    # ------------------------------------------------------------------
    # File uploads (3-step: init → content → commit)
    # ------------------------------------------------------------------

    def init_file(self, record_id: str, filename: str) -> Response:
        """POST /api/records/{id}/draft/files — declare a file upload."""
        return self._post(
            self._resource_path(record_id, "draft", "files"),
            json=[{"key": filename}],
        )

    def upload_file_content(
        self, record_id: str, filename: str, content: bytes
    ) -> Response:
        """PUT /api/records/{id}/draft/files/{filename}/content — upload bytes."""
        return self._put_binary(
            self._resource_path(record_id, "draft", "files", filename, "content"),
            content,
        )

    def commit_file(self, record_id: str, filename: str) -> Response:
        """POST /api/records/{id}/draft/files/{filename}/commit — finalise upload."""
        return self._post(
            self._resource_path(record_id, "draft", "files", filename, "commit")
        )

    def upload_file(self, record_id: str, filename: str, content: bytes) -> None:
        """
        Full 3-step upload: init → content → commit.
        Raises AssertionError at the first failing step.
        """
        self.assert_ok(self.init_file(record_id, filename), 201)
        self.assert_ok(self.upload_file_content(record_id, filename, content), 200)
        self.assert_ok(self.commit_file(record_id, filename), 200)

    def list_files(self, record_id: str) -> Response:
        """GET /api/records/{id}/draft/files — list files on a draft."""
        return self._get(self._resource_path(record_id, "draft", "files"))

    def delete_file(self, record_id: str, filename: str) -> Response:
        """DELETE /api/records/{id}/draft/files/{filename} — remove a file."""
        return self._delete(self._resource_path(record_id, "draft", "files", filename))

    # ------------------------------------------------------------------
    # Publish & versions
    # ------------------------------------------------------------------

    def publish(self, record_id: str) -> Response:
        """POST /api/records/{id}/draft/actions/publish — publish a draft."""
        return self._post(self._resource_path(record_id, "draft", "actions", "publish"))

    def list_versions(self, record_id: str) -> Response:
        """GET /api/records/{id}/versions — list all versions."""
        return self._get(self._resource_path(record_id, "versions"))

    def create_new_version(self, record_id: str) -> Response:
        """POST /api/records/{id}/versions — open a new version draft."""
        return self._post(self._resource_path(record_id, "versions"))

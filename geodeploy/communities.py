# -*- coding: utf-8 -*-
#
# This file is part of GEO Knowledge Hub.
# Copyright 2020-2021 GEO Secretariat.
#
# GEO Knowledge Hub is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Module CommunitiesClient"""



from __future__ import annotations

from requests import Response

from geodeploy.base import BaseClient


class CommunitiesClient(BaseClient):
    """Page Object for the Communities API."""

    def list(self, size: int = 5, query: str = "") -> Response:
        """GET /api/communities — list communities."""
        params = {"size": size}
        if query:
            params["q"] = query
        return self._get("/api/communities", params=params)

    def get(self, community_id: str) -> Response:
        """GET /api/communities/{id} — get by ID or slug."""
        return self._get(f"/api/communities/{community_id}")

    def create(self, payload: dict) -> Response:
        """POST /api/communities — create a community."""
        return self._post("/api/communities", json=payload)

    def update(self, community_id: str, payload: dict) -> Response:
        """
        PUT /api/communities/{id} — update community.
        Sends the full fetched payload including slug — this instance
        requires slug to be present (unlike older versions that rejected it).
        """
        return self._put(f"/api/communities/{community_id}", json=payload)

    def fetch_and_update_title(self, community_id: str, new_title: str) -> Response:
        """
        Fetch the current community state, update the title, PUT back.
        Uses the full response body (including slug) to satisfy validation.
        """
        r = self.get(community_id)
        self.assert_ok(r, 200)
        current = r.json()
        current["metadata"]["title"] = new_title
        return self.update(community_id, current)

    def delete(self, community_id: str) -> Response:
        """DELETE /api/communities/{id}."""
        return self._delete(f"/api/communities/{community_id}")

    def list_members(self, community_id: str) -> Response:
        """GET /api/communities/{id}/members."""
        return self._get(f"/api/communities/{community_id}/members")

    def list_public_members(self, community_id: str) -> Response:
        """GET /api/communities/{id}/members/public."""
        return self._get(f"/api/communities/{community_id}/members/public")

    def search(self, query: str = "", page: int = 1, size: int = 5) -> Response:
        """GET /api/communities with pagination."""
        return self._get(
            "/api/communities",
            params={"q": query, "page": page, "size": size},
        )

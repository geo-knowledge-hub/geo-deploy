# -*- coding: utf-8 -*-
#
# This file is part of GEO Knowledge Hub.
# Copyright 2020-2021 GEO Secretariat.
#
# GEO Knowledge Hub is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Module DOIClient"""




from __future__ import annotations

from requests import Response

from geodeploy.base import BaseClient


class DOIClient(BaseClient):
    """Page Object for DOI reservation and management."""

    # ------------------------------------------------------------------
    # Records (Knowledge Resources)
    # ------------------------------------------------------------------

    def reserve_doi_for_record(self, record_id: str) -> Response:
        """
        POST /api/records/{id}/draft/pids/doi
        Reserves a DOI so it can be included in files before upload.
        The DOI is only registered (made public) when the record is published.
        Returns the reserved DOI identifier in the response.
        """
        return self._post(f"/api/records/{record_id}/draft/pids/doi")

    def discard_doi_for_record(self, record_id: str) -> Response:
        """
        DELETE /api/records/{id}/draft/pids/doi
        Releases a reserved DOI that has not yet been published.
        """
        return self._delete(f"/api/records/{record_id}/draft/pids/doi")

    def get_record_pids(self, record_id: str) -> Response:
        """
        GET /api/records/{id}/draft
        Returns full draft including pids block where DOI lives.
        """
        return self._get(f"/api/records/{record_id}/draft")

    # ------------------------------------------------------------------
    # Packages (Knowledge Packages)
    # ------------------------------------------------------------------

    def reserve_doi_for_package(self, package_id: str) -> Response:
        """
        POST /api/packages/{id}/draft/pids/doi
        Reserves a DOI for a Knowledge Package draft.
        """
        return self._post(f"/api/packages/{package_id}/draft/pids/doi")

    def discard_doi_for_package(self, package_id: str) -> Response:
        """
        DELETE /api/packages/{id}/draft/pids/doi
        Releases a reserved DOI for a Knowledge Package.
        """
        return self._delete(f"/api/packages/{package_id}/draft/pids/doi")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def extract_doi(self, draft: dict) -> str | None:
        """
        Extract the DOI identifier string from a draft response dict.
        Returns None if no DOI is present.

        InvenioRDM stores it at: draft["pids"]["doi"]["identifier"]
        """
        return draft.get("pids", {}).get("doi", {}).get("identifier")

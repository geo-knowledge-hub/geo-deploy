#
# This file is part of GEO Knowledge Hub.
# Copyright 2020-2021 GEO Secretariat.
#
# GEO Knowledge Hub is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Module SearchClient"""

from __future__ import annotations

from requests import Response

from gkh_validation.client.base import BaseClient

# The confirmed working spatial parameter for this GKH instance.
# Change this constant if the instance is upgraded and the parameter changes.
_SPATIAL_PARAM = "bounds"


class SearchClient(BaseClient):
    """Page Object for the unified /api/search endpoint."""

    base_path = "/api/search"

    # ------------------------------------------------------------------
    # Core search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str = "",
        page: int = 1,
        size: int = 5,
    ) -> Response:
        """
        GET /api/search — full-text search across Packages and Resources.

        Args:
            query: Free-text search string (e.g. "climate NDVI").
            page:  Page number (1-based).
            size:  Number of results per page.
        """
        return self._get(
            self._resource_path(),
            params={"q": query, "page": page, "size": size},
        )

    # ------------------------------------------------------------------
    # Spatial search
    # ------------------------------------------------------------------

    def search_by_bbox(
        self,
        west: float,
        south: float,
        east: float,
        north: float,
        query: str = "",
        page: int = 1,
        size: int = 5,
    ) -> Response:
        """
        Spatial bounding box search.

        Returns records whose geographic coverage intersects the given box.
        Uses the "bounds" parameter (confirmed working on this instance).
        Note: "bbox" causes 500 on this instance and must not be used.

        Args:
            west:  Western longitude boundary  (e.g. -3.26 for Ghana)
            south: Southern latitude boundary  (e.g.  4.74 for Ghana)
            east:  Eastern longitude boundary  (e.g.  1.19 for Ghana)
            north: Northern latitude boundary  (e.g. 11.17 for Ghana)
            query: Optional additional full-text filter.
            page:  Page number.
            size:  Results per page.

        Bounding box format sent to API: "west,south,east,north"
        Example: "-3.26,4.74,1.19,11.17"
        """
        params = {
            _SPATIAL_PARAM: f"{west},{south},{east},{north}",
            "page": page,
            "size": size,
        }
        if query:
            params["q"] = query
        return self._get(self._resource_path(), params=params)

    def search_by_point(
        self,
        longitude: float,
        latitude: float,
        query: str = "",
        size: int = 5,
    ) -> Response:
        """
        Search records that cover a specific point location.
        Internally creates a small bounding box (~1 km buffer) around the point.

        Args:
            longitude: Point longitude in decimal degrees.
            latitude:  Point latitude in decimal degrees.
            query:     Optional full-text filter.
            size:      Results per page.

        Examples:
            search_by_point(longitude=-0.839, latitude=9.403)  # Tamale, Ghana
            search_by_point(longitude=-0.187, latitude=5.603)  # Accra, Ghana
        """
        delta = 0.01  # ~1 km buffer
        return self.search_by_bbox(
            west=longitude - delta,
            south=latitude - delta,
            east=longitude + delta,
            north=latitude + delta,
            query=query,
            size=size,
        )

    # ------------------------------------------------------------------
    # Filtered search
    # ------------------------------------------------------------------

    def search_by_resource_type(
        self,
        resource_type: str,
        query: str = "",
        page: int = 1,
        size: int = 5,
    ) -> Response:
        """
        Filter results by resource type.

        Args:
            resource_type: InvenioRDM type id — "dataset", "software",
                           "publication", "knowledge", "image".
            query:         Optional additional full-text filter.

        Example:
            search_by_resource_type("dataset", query="NDVI")
        """
        q = f'metadata.resource_type.id:"{resource_type}"'
        if query:
            q += f" AND {query}"
        return self._get(
            self._resource_path(),
            params={"q": q, "page": page, "size": size},
        )

    # ------------------------------------------------------------------
    # Combined search (text + spatial + type filter)
    # ------------------------------------------------------------------

    def search_combined(
        self,
        query: str = "",
        west: float | None = None,
        south: float | None = None,
        east: float | None = None,
        north: float | None = None,
        resource_type: str | None = None,
        page: int = 1,
        size: int = 5,
    ) -> Response:
        """
        Combined search — any combination of text, spatial bbox, and type filter.
        All parameters are optional; pass only what you need.

        Args:
            query:              Full-text search string.
            west/south/east/north: Bounding box corners. All four must be
                                provided together to activate spatial filtering.
            resource_type:      Filter by resource type id.
            page:               Page number.
            size:               Results per page.

        Examples:
            # Text only
            search_combined(query="rainfall")

            # Spatial only — all records covering Ghana
            search_combined(west=-3.26, south=4.74, east=1.19, north=11.17)

            # Datasets about rainfall covering Northern Ghana
            search_combined(
                query="rainfall",
                west=-2.5, south=8.5, east=0.2, north=11.2,
                resource_type="dataset",
            )
        """
        params: dict = {"page": page, "size": size}

        # Build query string parts
        q_parts = []
        if query:
            q_parts.append(query)
        if resource_type:
            q_parts.append(f'metadata.resource_type.id:"{resource_type}"')
        if q_parts:
            params["q"] = " AND ".join(q_parts)

        # Add spatial filter only when all four corners are supplied
        if all(v is not None for v in (west, south, east, north)):
            params[_SPATIAL_PARAM] = f"{west},{south},{east},{north}"

        return self._get(self._resource_path(), params=params)

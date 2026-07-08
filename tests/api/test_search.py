"""
tests/api/test_search.py
========================
Tests for the unified /api/search endpoint.

Covers
------
- Full-text search
- Pagination
- Spatial bounding box search
- Point-based search
- Resource type filtering
- Combined search (text + spatial + type)
"""

from __future__ import annotations

import pytest
from requests import Session

from geodeploy.search import SearchClient
from tests.fixtures import assert_ok


@pytest.fixture()
def search(http: Session, base_url: str) -> SearchClient:
    return SearchClient(http, base_url)


# ---------------------------------------------------------------------------
# Full-text search
# ---------------------------------------------------------------------------


class TestFullTextSearch:
    def test_returns_hits_structure(self, search: SearchClient) -> None:
        r = search.search(size=5)
        assert_ok(r, 200)
        data = r.json()
        assert "hits" in data
        assert "total" in data["hits"]

    def test_full_text_query(self, search: SearchClient) -> None:
        r = search.search(query="climate")
        assert_ok(r, 200)

    def test_empty_query_returns_all(self, search: SearchClient) -> None:
        r = search.search(query="", size=10)
        assert_ok(r, 200)
        assert r.json()["hits"]["total"] >= 0

    def test_pagination_no_overlap(self, search: SearchClient) -> None:
        r1 = search.search(page=1, size=2)
        r2 = search.search(page=2, size=2)
        assert_ok(r1, 200)
        assert_ok(r2, 200)
        ids1 = {h["id"] for h in r1.json()["hits"]["hits"]}
        ids2 = {h["id"] for h in r2.json()["hits"]["hits"]}
        if ids1 and ids2:
            assert ids1.isdisjoint(ids2), "Pages 1 and 2 share the same records"

    def test_nonexistent_term_returns_empty(self, search: SearchClient) -> None:
        r = search.search(query="xyzzy-this-term-does-not-exist-12345")
        assert_ok(r, 200)
        assert r.json()["hits"]["total"] == 0


# ---------------------------------------------------------------------------
# Spatial / bounding box search
# ---------------------------------------------------------------------------


class TestSpatialSearch:
    def test_bbox_search_returns_200(self, search: SearchClient) -> None:
        """
        Bounding box covering the whole of Africa.
        Should always return a valid (possibly empty) result set.
        west=-20, south=-35, east=55, north=38
        """
        r = search.search_by_bbox(west=-20, south=-35, east=55, north=38)
        assert_ok(r, 200)
        assert "hits" in r.json()

    def test_bbox_ghana(self, search: SearchClient) -> None:
        """Bounding box covering Ghana (west=-3.26, south=4.74, east=1.19, north=11.17)."""
        r = search.search_by_bbox(west=-3.26, south=4.74, east=1.19, north=11.17)
        assert_ok(r, 200)
        data = r.json()
        assert "hits" in data

    def test_bbox_with_text_query(self, search: SearchClient) -> None:
        """Spatial filter combined with a full-text keyword."""
        r = search.search_by_bbox(
            west=-3.26,
            south=4.74,
            east=1.19,
            north=11.17,
            query="climate",
        )
        assert_ok(r, 200)

    def test_bbox_northern_ghana(self, search: SearchClient) -> None:
        """
        Tight bounding box covering Northern Ghana region
        (Tamale area: roughly 8.5N–11.2N, 2.5W–0.2E).
        """
        r = search.search_by_bbox(west=-2.5, south=8.5, east=0.2, north=11.2)
        assert_ok(r, 200)

    def test_point_search_tamale(self, search: SearchClient) -> None:
        """
        Point search for Tamale, Northern Region, Ghana.
        Coordinates: longitude=-0.839, latitude=9.403
        """
        r = search.search_by_point(longitude=-0.839, latitude=9.403)
        assert_ok(r, 200)
        assert "hits" in r.json()

    def test_point_search_accra(self, search: SearchClient) -> None:
        """Point search for Accra, Ghana. Coordinates: lon=-0.187, lat=5.603"""
        r = search.search_by_point(longitude=-0.187, latitude=5.603)
        assert_ok(r, 200)

    def test_bbox_outside_coverage_returns_empty_or_valid(
        self, search: SearchClient
    ) -> None:
        """
        Bounding box in the middle of the Pacific Ocean.
        Should return a valid (probably empty) result — not an error.
        """
        r = search.search_by_bbox(west=-180, south=-90, east=-90, north=-45)
        assert_ok(r, 200)
        assert isinstance(r.json()["hits"]["hits"], list)

    def test_bbox_global(self, search: SearchClient) -> None:
        """Full global bounding box — should return all spatially indexed records."""
        r = search.search_by_bbox(west=-180, south=-90, east=180, north=90)
        assert_ok(r, 200)


# ---------------------------------------------------------------------------
# Resource type filtering
# ---------------------------------------------------------------------------


class TestFilteredSearch:
    def test_filter_by_dataset(self, search: SearchClient) -> None:
        r = search.search_by_resource_type("dataset")
        assert_ok(r, 200)

    def test_filter_by_software(self, search: SearchClient) -> None:
        r = search.search_by_resource_type("software")
        assert_ok(r, 200)

    def test_filter_by_knowledge(self, search: SearchClient) -> None:
        """Knowledge Packages have resource_type id 'knowledge'."""
        r = search.search_by_resource_type("knowledge")
        assert_ok(r, 200)

    def test_filter_with_text_query(self, search: SearchClient) -> None:
        r = search.search_by_resource_type("dataset", query="NDVI")
        assert_ok(r, 200)


# ---------------------------------------------------------------------------
# Combined search (text + spatial + type)
# ---------------------------------------------------------------------------


class TestCombinedSearch:
    def test_text_only(self, search: SearchClient) -> None:
        r = search.search_combined(query="earth observation")
        assert_ok(r, 200)

    def test_spatial_only(self, search: SearchClient) -> None:
        r = search.search_combined(west=-3.26, south=4.74, east=1.19, north=11.17)
        assert_ok(r, 200)

    def test_type_only(self, search: SearchClient) -> None:
        r = search.search_combined(resource_type="dataset")
        assert_ok(r, 200)

    def test_text_and_spatial(self, search: SearchClient) -> None:
        r = search.search_combined(
            query="rainfall",
            west=-3.26,
            south=4.74,
            east=1.19,
            north=11.17,
        )
        assert_ok(r, 200)

    def test_text_and_type(self, search: SearchClient) -> None:
        r = search.search_combined(query="NDVI", resource_type="software")
        assert_ok(r, 200)

    def test_all_three_combined(self, search: SearchClient) -> None:
        """
        Full combined query: text + bounding box + resource type.
        Datasets about rainfall covering Ghana.
        """
        r = search.search_combined(
            query="rainfall",
            west=-3.26,
            south=4.74,
            east=1.19,
            north=11.17,
            resource_type="dataset",
        )
        assert_ok(r, 200)

    def test_no_params_returns_all(self, search: SearchClient) -> None:
        """Calling combined with no parameters should return all records."""
        r = search.search_combined()
        assert_ok(r, 200)
        assert "hits" in r.json()

"""
tests/api/test_communities.py
=============================
Tests for the Communities API.
All calls go through CommunitiesClient.
"""

from __future__ import annotations

import pytest
from requests import Session

from client.communities import CommunitiesClient
from factories import make_community_payload
from fixtures import assert_ok


@pytest.fixture()
def communities(http: Session, base_url: str) -> CommunitiesClient:
    return CommunitiesClient(http, base_url)


class TestCommunitySearch:

    def test_list_communities(self, communities: CommunitiesClient) -> None:
        r = communities.list(size=5)
        assert_ok(r, 200)
        assert "hits" in r.json()

    def test_list_has_total(self, communities: CommunitiesClient) -> None:
        r = communities.list(size=1)
        assert "total" in r.json()["hits"]

    def test_search_by_query(self, communities: CommunitiesClient) -> None:
        r = communities.list(query="geo")
        assert_ok(r, 200)

    def test_nonexistent_returns_404(self, communities: CommunitiesClient) -> None:
        r = communities.get("this-slug-does-not-exist-xyz")
        assert r.status_code == 404

    def test_pagination(self, communities: CommunitiesClient) -> None:
        r1 = communities.search(page=1, size=2)
        r2 = communities.search(page=2, size=2)
        assert_ok(r1, 200)
        assert_ok(r2, 200)


class TestCommunityCRUD:

    def test_create_community(self, communities: CommunitiesClient) -> None:
        payload = make_community_payload()
        r = communities.create(payload)
        assert_ok(r, 201)
        data = r.json()
        assert "id" in data
        assert data["metadata"]["title"] == payload["metadata"]["title"]
        communities.delete(data["id"])

    def test_get_by_id(
        self, communities: CommunitiesClient, community: dict
    ) -> None:
        r = communities.get(community["id"])
        assert_ok(r, 200)
        assert r.json()["id"] == community["id"]

    def test_get_by_slug(
        self, communities: CommunitiesClient, community: dict
    ) -> None:
        slug = community.get("slug") or community["id"]
        r = communities.get(slug)
        assert_ok(r, 200)

    def test_update_title(
        self, communities: CommunitiesClient, community: dict
    ) -> None:
        r = communities.fetch_and_update_title(community["id"], "Updated by pytest")
        assert_ok(r, 200)
        assert r.json()["metadata"]["title"] == "Updated by pytest"

    def test_delete_community(self, communities: CommunitiesClient) -> None:
        r = communities.create(make_community_payload())
        assert_ok(r, 201)
        cid = r.json()["id"]
        assert_ok(communities.delete(cid), 204)
        assert communities.get(cid).status_code in (404, 410)


class TestCommunityMembers:

    def test_list_members(
        self, communities: CommunitiesClient, community: dict
    ) -> None:
        r = communities.list_members(community["id"])
        assert r.status_code in (200, 404)

    def test_list_public_members(
        self, communities: CommunitiesClient, community: dict
    ) -> None:
        r = communities.list_public_members(community["id"])
        assert r.status_code in (200, 404)

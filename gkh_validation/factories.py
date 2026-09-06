#
# This file is part of GEO Knowledge Hub.
# Copyright 2020-2021 GEO Secretariat.
#
# GEO Knowledge Hub is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Module factories"""

from __future__ import annotations

import uuid

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _uid() -> str:
    """Short unique suffix for generated titles / slugs."""
    return uuid.uuid4().hex[:8]


# ---------------------------------------------------------------------------
# Knowledge Resource factories
# (POST /api/records)
# ---------------------------------------------------------------------------


def make_resource_payload(
    title: str | None = None,
    resource_type: str = "dataset",
    with_files: bool = False,
) -> dict:
    """
    Minimal valid payload for a Knowledge Resource draft.

    Args:
        title:         Override the auto-generated title.
        resource_type: InvenioRDM resource_type id (e.g. "dataset", "software",
                       "publication", "image").
        with_files:    True  → files enabled (required before uploading files).
                       False → metadata-only record (can publish without files).
    """
    return {
        "access": {
            "record": "public",
            "files": "public",
        },
        "files": {"enabled": with_files},
        "metadata": {
            "title": title or f"pytest-resource-{_uid()}",
            "description": "Automated test resource – safe to delete.",
            "publication_date": "2024-01-15",
            "publisher": "GEO Knowledge Hub",
            "resource_type": {"id": resource_type},
            "creators": [
                {
                    "person_or_org": {
                        "type": "personal",
                        "family_name": "Mr GEO",
                        "given_name": "Tester",
                    }
                }
            ],
        },
    }


def make_resource_payload_with_files(title: str | None = None) -> dict:
    """Convenience wrapper — resource draft with file uploads enabled."""
    return make_resource_payload(title=title, with_files=True)


def make_resource_full_metadata(title: str | None = None) -> dict:
    """
    Extended metadata payload matching the official 'Update metadata' example.
    Use this when testing richer metadata fields (rights, subjects, languages).
    """
    return {
        "access": {
            "record": "public",
            "files": "public",
        },
        "files": {"enabled": True},
        "metadata": {
            "title": title or f"pytest-resource-full-{_uid()}",
            "description": "Full metadata test resource.",
            "publication_date": "2024-01-15",
            "resource_type": {"id": "software"},
            "rights": [{"id": "mit"}],
            "subjects": [
                {"subject": "GEO"},
                {"subject": "Earth Observation"},
            ],
            "languages": [{"id": "eng"}],
            "creators": [
                {
                    "person_or_org": {
                        "type": "personal",
                        "family_name": "Mr GEO",
                        "given_name": "Tester",
                    }
                }
            ],
        },
    }


# ---------------------------------------------------------------------------
# Knowledge Package factories
# (POST /api/packages)
# ---------------------------------------------------------------------------


def make_package_payload(
    title: str | None = None,
    with_files: bool = False,
) -> dict:
    """
    Minimal valid payload for a Knowledge Package draft.

    Args:
        title:      Override the auto-generated title.
        with_files: True → files enabled on the package itself.
                    False → metadata-only (default; allows publish without files).
    """
    return {
        "access": {
            "record": "public",
            "files": "public",
        },
        "files": {"enabled": with_files},
        "metadata": {
            "title": title or f"pytest-package-{_uid()}",
            "description": "Automated test package – safe to delete.",
            "publication_date": "2024-01-15",
            "publisher": "GEO Knowledge Hub",
            "resource_type": {"id": "knowledge"},
            "creators": [
                {
                    "person_or_org": {
                        "type": "personal",
                        "family_name": "Mr GEO",
                        "given_name": "Tester",
                    }
                }
            ],
        },
    }


def make_package_payload_with_files(title: str | None = None) -> dict:
    """Convenience wrapper — package draft with file uploads enabled."""
    return make_package_payload(title=title, with_files=True)


# ---------------------------------------------------------------------------
# Community factories
# (POST /api/communities)
# ---------------------------------------------------------------------------


def make_community_payload(title: str | None = None) -> dict:
    """
    Minimal valid payload for a Community.
    Includes the required 'access' block.
    """
    uid = _uid()
    return {
        "slug": f"pytest-comm-{uid}",
        "access": {
            "visibility": "public",
            "member_policy": "open",
            "record_policy": "open",
        },
        "metadata": {
            "title": title or f"pytest-community-{uid}",
            "description": "Automated test community – safe to delete.",
            "type": {"id": "topic"},
        },
    }

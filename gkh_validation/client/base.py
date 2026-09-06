#
# This file is part of GEO Knowledge Hub.
# Copyright 2020-2021 GEO Secretariat.
#
# GEO Knowledge Hub is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Module BaseClient"""

from __future__ import annotations

import io

import requests
from requests import Response, Session


class BaseClient:
    """
    Wraps a requests.Session with the base URL and common helpers.

    Args:
        http:     Authenticated requests.Session (from the http fixture).
        base_url: Root URL of the GEO Knowledge Hub instance.
    """

    base_path: str = ""
    """API prefix for this resource, e.g. "/api/packages". Set once per
    subclass; individual methods should never hand-type it again."""

    def __init__(self, http: Session, base_url: str) -> None:
        self._http = http
        self._base_url = base_url

    # ------------------------------------------------------------------
    # Path building
    # ------------------------------------------------------------------

    def _path(self, *parts: object) -> str:
        """
        Join arbitrary segments into a clean "/"-prefixed path.

        Empty/None segments are dropped and stray slashes are stripped,
        so callers never need to worry about "//" or missing leading "/".

            self._path("api", "records", record_id, "draft")
            -> "/api/records/abc123/draft"
        """
        segments = [str(p).strip("/") for p in parts if p not in (None, "")]
        return "/" + "/".join(segments)

    def _resource_path(self, *parts: object) -> str:
        """
        Join this client's `base_path` with additional segments.

            # inside a class with base_path = "/api/packages"
            self._resource_path(package_id, "draft")
            -> "/api/packages/abc123/draft"
            self._resource_path()
            -> "/api/packages"
        """
        return self._path(self.base_path, *parts)

    # ------------------------------------------------------------------
    # Internal HTTP wrappers
    # ------------------------------------------------------------------

    def _get(self, path: str, **kwargs) -> Response:
        return self._http.get(f"{self._base_url}{path}", **kwargs)

    def _post(self, path: str, **kwargs) -> Response:
        return self._http.post(f"{self._base_url}{path}", **kwargs)

    def _put(self, path: str, **kwargs) -> Response:
        return self._http.put(f"{self._base_url}{path}", **kwargs)

    def _delete(self, path: str, **kwargs) -> Response:
        return self._http.delete(f"{self._base_url}{path}", **kwargs)

    def _put_binary(self, path: str, content: bytes) -> Response:
        """
        PUT raw binary content (file upload).
        Must NOT use JSON Content-Type — overrides the session header.
        """
        return requests.put(
            f"{self._base_url}{path}",
            data=io.BytesIO(content),
            headers={
                "Content-Type": "application/octet-stream",
                "Authorization": self._http.headers["Authorization"],
            },
            verify=self._http.verify,
        )

    # ------------------------------------------------------------------
    # Shared assertion helper
    # ------------------------------------------------------------------

    @staticmethod
    def assert_ok(r: Response, *expected: int) -> None:
        codes = expected or (200,)
        assert r.status_code in codes, f"Expected {codes}, got {r.status_code}\n{r.text[:600]}"

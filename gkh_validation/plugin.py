#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""GEO Knowledge Hub validation - Pytest plugin."""

import pytest

from gkh_validation import HERE

#
# Constants
#
PUBLISHES = "publishes"
SKIP_PUBLISH = "publishes irreversibly; pass --allow-publish to run it"


#
# Hooks
#
def pytest_addoption(parser: pytest.Parser) -> None:
    """Register the suite's options.

    Defaults stay None. What they fallback to is resolved when a fixture asks,
    in `settings.py`, so registering this plugin reads no environment and touches
    no disk.

    Args:
        parser (pytest.Parser): The parser to register the options with.
    """
    group = parser.getgroup("gkh validation")

    group.addoption(
        "--base-url",
        default=None,
        help="Base URL of the instance (or set GKH_BASE_URL).",
    )
    group.addoption(
        "--api-token",
        default=None,
        help="Personal access token (or set GKH_API_TOKEN).",
    )
    group.addoption(
        "--no-verify-tls",
        action="store_true",
        default=False,
        help="Skip TLS verification (or set GKH_NO_VERIFY_TLS=true).",
    )
    group.addoption(
        "--allow-publish",
        action="store_true",
        default=False,
        help="Run the tests that publish. A published record cannot be deleted.",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip this suite's tests that publish unless the caller opted in.

    The entry point registers this plugin in every pytest run of the environment, so the
    gate is confined to items collected from this package. A project that installs the
    `validation` extra keeps its own `publishes` tests.

    Args:
        config (pytest.Config): The session configuration.

        items (list[pytest.Item]): The collected tests.
    """
    if config.getoption("--allow-publish"):
        return

    skip = pytest.mark.skip(reason=SKIP_PUBLISH)

    for item in items:
        if PUBLISHES in item.keywords and item.path.is_relative_to(HERE):
            item.add_marker(skip)

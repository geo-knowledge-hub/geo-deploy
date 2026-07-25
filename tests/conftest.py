#
# This file is part of GEO Knowledge Hub.
# Copyright 2020-2021 GEO Secretariat.
#
# GEO Knowledge Hub is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Module conftest"""

from __future__ import annotations

import os
import ssl
import warnings
from pathlib import Path

import pytest
import urllib3

from tests.factories import *
from tests.fixtures import *


# ---------------------------------------------------------------------------
# Load .env file from the project root before anything else runs.
# This makes GEO_API_TOKEN and GEO_BASE_URL available as environment
# variables so you don't have to pass --api-token on every run.
#
# Priority order (highest to lowest):
#   1. CLI flag         --api-token "xyz"   (always wins)
#   2. Shell env var    $env:GEO_API_TOKEN  (already set in the shell)
#   3. .env file        GEO_API_TOKEN=xyz   (loaded here)
#
# Search is upward from this file's directory so conftest.py can live at
# any depth (project root, tests/, tests/ui/, etc.) without breaking the
# .env lookup if it's ever moved again.
# ---------------------------------------------------------------------------
def _find_env_file(start: Path) -> Path | None:
    """Walk upward from `start` looking for a .env file."""
    for parent in [start, *start.parents]:
        candidate = parent / ".env"
        if candidate.exists():
            return candidate
    return None


try:
    from dotenv import load_dotenv

    _env_file = _find_env_file(Path(__file__).parent)
    if _env_file is not None:
        load_dotenv(_env_file)
        print(f"\n[conftest] Loaded environment from {_env_file}")
    else:
        print(
            "\n[conftest] No .env file found in any parent directory of "
            f"{Path(__file__).parent}. Create one to avoid passing "
            "--api-token on every run."
        )
except ImportError:
    print(
        "\n[conftest] python-dotenv not installed. "
        "Run: pip install python-dotenv\n"
        "Or pass --api-token on the command line."
    )

# Re-export everything so pytest auto-discovers fixtures in tests/api/ and tests/ui/

# ---------------------------------------------------------------------------
# Suppress SSL warnings at import time (self-signed cert on site/host address)
# ---------------------------------------------------------------------------
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

_orig_ssl_ctx = ssl.create_default_context


def _no_verify_ctx(*args, **kwargs):
    ctx = _orig_ssl_ctx(*args, **kwargs)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


# ---------------------------------------------------------------------------
# CLI options
# ---------------------------------------------------------------------------


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--base-url",
        default=os.getenv("GEO_BASE_URL", ""),
        help="Base URL of the GEO Knowledge Hub instance (or set GEO_BASE_URL in .env)",
    )
    parser.addoption(
        "--api-token",
        default=None,
        help="Bearer token (or set GEO_API_TOKEN in .env)",
    )
    parser.addoption(
        "--no-verify-tls",
        action="store_true",
        default=os.getenv("GEO_NO_VERIFY_TLS", "false").lower() == "true",
        help="Disable TLS verification (or set GEO_NO_VERIFY_TLS=true in .env)",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Called before fixtures or tests — patches SSL process-wide."""
    if config.getoption("--no-verify-tls", default=False):
        ssl.create_default_context = _no_verify_ctx
        os.environ["PYTHONHTTPSVERIFY"] = "0"
        os.environ["REQUESTS_CA_BUNDLE"] = ""
        os.environ["CURL_CA_BUNDLE"] = ""

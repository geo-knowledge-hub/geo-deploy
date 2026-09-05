#
# This file is part of GEO Knowledge Hub.
# Copyright 2020-2021 GEO Secretariat.
#
# GEO Knowledge Hub is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Module conftest.

Fixtures for the validation suite. They live here rather than in the plugin so
they reach this suite's tests and nothing else in the environment.

The options themselves are registered in plugin.py:
- `pytest_addoption` in a conftest collected with `--pyargs` is never called.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import urllib3

from gkh_validation.factories import *
from gkh_validation.fixtures import *
from gkh_validation.settings import load_env_file

# instances with a self-signed certificate are checked with `verify=False`, which
# is exactly what this warning reports
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@pytest.fixture(scope="session", autouse=True)
def dotenv() -> Path | None:
    """Load the nearest .env once, when the suite actually runs.

    Everything that reads a setting depends on this, so a `.env` is never read
    by a pytest session that is not running this suite.
    """
    return load_env_file()

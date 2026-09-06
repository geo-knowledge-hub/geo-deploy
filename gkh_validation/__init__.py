#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""GEO Knowledge Hub validation suite."""

from pathlib import Path

#
# Constants
#
HERE = Path(__file__).parent

# The suite's own pytest configuration. Passed with -c so the working directory
# a run starts from can never redirect it.
CONFIG = HERE / "pytest.ini"

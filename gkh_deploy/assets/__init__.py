#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""GEO Knowledge Hub deploy assets."""

from pathlib import Path

#
# Constants.
#
HERE = Path(__file__).parent

# Chart values file
CHART_VALUES = HERE / "chart" / "values.yaml"

# Profiles directory files
PROFILES = HERE / "profiles"

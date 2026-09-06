#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""GEO Knowledge Hub deploy - CLI profiles."""

import yaml

from gkh_deploy.assets import PROFILES


#
# Functions
#
def names() -> list[str]:
    """Get the names of the available profiles.

    Returns:
        list[str]: The names of the available profiles.
    """
    return sorted(p.stem for p in PROFILES.glob("*.yaml"))


def load(name: str) -> dict:
    """Read a profile.

    Args:
        name (str): The name of the profile to load.

    Returns:
        dict: The profile data.

    Raises:
        FileNotFoundError: when no profile of that name is shipped.
    """
    path = PROFILES / f"{name}.yaml"

    if not path.is_file():
        # get the available profiles
        available = ", ".join(names())

        raise FileNotFoundError(f"unknown profile '{name}'; available: {available}")

    # load the profile
    return yaml.safe_load(path.read_text()) or {}

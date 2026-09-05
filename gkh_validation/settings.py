#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""GEO Knowledge Hub validation - Settings."""

import os
from pathlib import Path

from dotenv import load_dotenv

#
# Constants
#
ENV_FILE = ".env"


#
# Auxiliary functions
#
def load_env_file(base_path: Path | None = None) -> Path | None:
    """Load the nearest `.env` at or above a directory.

    Args:
        base_path (Path | None): Directory to search from. Defaults to the working directory.

    Returns:
        Path | None: The file that was loaded, or None when there is none.
    """
    base_path = base_path or Path.cwd()

    for parent in [base_path, *base_path.parents]:
        candidate = parent / ENV_FILE

        if candidate.is_file():
            # the environment a caller already set always wins
            load_dotenv(candidate, override=False)

            return candidate

    return None


def load_config_value(name: str, flag: str | None, default: str = "") -> str:
    """Resolve config value.

    This functions tries to resolve settings value. If provided it
    resolved from the CLI flag. Otherwise, tries to get from the env
    variable.

    Args:
        name (str): Environment variable to fall back to.

        flag (str | None): Value given on the command line, if any.

        default (str): Value to use when neither is set.

    Returns:
        str: The resolved value.
    """
    if flag:
        return flag

    return os.getenv(name, default)


def load_config_bool_from_env(name: str) -> bool:
    """Read a boolean setting from the environment.

    Args:
        name (str): Environment variable to read.

    Returns:
        bool: True when the variable is set to 'true'.
    """
    return os.getenv(name, "false").lower() == "true"

#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""GEO Knowledge Hub deploy - Settings."""

from pathlib import Path
from typing import Any

import pydash
import yaml

#
# Constants - Settings version
#
SETTINGS_VERSION = 1

#
# Constants - Required settings
#
REQUIRED = ("hostname", "admin.email")


#
# Functions
#
def _coerce(value: str) -> Any:
    """Convert string to a proper type.

    Args:
        value (str): The value to coerce.

    Returns:
        Any: The converted value.
    """
    if value.lower() in ("true", "false"):
        return value.lower() == "true"

    if value.isdigit():
        return int(value)

    return value


def load(path: Path) -> dict:
    """Read the settings file.

    Args:
        path (Path): The path to the settings file.

    Returns:
        dict: The settings.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when the file does not parse as a YAML mapping.
    """
    if not path.is_file():
        raise FileNotFoundError(f"no such configuration file: {path}")

    parsed = yaml.safe_load(path.read_text())

    if not isinstance(parsed, dict):
        raise ValueError(f"{path} does not contain a YAML mapping")

    return parsed


def apply_overrides(settings: dict, overrides: list[str]) -> dict:
    """Override settings values.

    Args:
        settings (dict): The settings.

        overrides (list[str]): The overrides.

    Returns:
        dict: The overridden settings.

    Raises:
        ValueError: when an override is not in KEY=VALUE form.
    """
    result = pydash.clone_deep(settings)

    for override in overrides:
        key, separator, value = override.partition("=")

        if not separator or not key:
            raise ValueError(f"override '{override}' is not in KEY=VALUE form")

        pydash.set_(result, key.strip(), _coerce(value.strip()))

    return result


def dump(settings: dict) -> str:
    """Serialize settings for writing.

    Args:
        settings (dict): The settings.

    Returns:
        str: The serialized settings.
    """
    return yaml.safe_dump(settings, sort_keys=False)


def validate(settings: dict) -> list[str]:
    """Report everything wrong with a settings file.

    Args:
        settings (dict): The settings.

    Returns:
        list[str]: The validation problems.
    """
    problems = []
    version = settings.get("version")

    # check the version
    if version != SETTINGS_VERSION:
        problems.append(f"version must be {SETTINGS_VERSION}, got {version!r}")

    # check the target
    if settings.get("target") != "k8s":
        problems.append(f"target must be 'k8s', got {settings.get('target')!r}")

    # check the required settings
    for key in REQUIRED:
        if not pydash.get(settings, key):
            problems.append(f"{key} is required and has no default")

    # check the datacite settings
    if pydash.get(settings, "datacite.enabled") and not pydash.get(settings, "datacite.prefix"):
        problems.append("datacite.prefix is required when datacite.enabled is true")

    return problems

#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""GEO Knowledge Hub deploy - Bundle rendering environment."""

import shlex
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

#
# Constants - Templates
#
TEMPLATES = Path(__file__).parent / "templates"


#
# Functions
#
def environment() -> Environment:
    """Build the Jinja environment used for every template.

    Returns:
        Environment: The Jinja environment.
    """
    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        trim_blocks=False,
        autoescape=False,
    )

    # add filters to the environment
    env.filters["shell"] = shlex.quote
    env.filters["yaml"] = _yaml_scalar

    return env


def _yaml_scalar(value: object) -> str:
    """Render one value as YAML, safe to place after a key.

    Args:
        value (object): The value to render as YAML.

    Returns:
        str: The rendered YAML.
    """
    dumped = yaml.safe_dump(
        data=value,
        default_flow_style=True,
        width=10**9,
    ).strip()

    # remove the trailing ellipsis
    return dumped.removesuffix("...").strip()

#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""GEO Knowledge Hub deploy - Bundle rendering files."""

import yaml

from gkh_deploy.render import context as context_module
from gkh_deploy.render.environment import environment

#
# Constants - Templated files
#
TEMPLATED = {
    "values.yaml": "k8s/values.yaml.j2",
    "secrets.sh": "k8s/secrets.sh.j2",
    "bootstrap.sh": "k8s/bootstrap.sh.j2",
    "README.md": "k8s/README.md.j2",
}


#
# Functions
#
def bundle(settings: dict) -> dict[str, str]:
    """Render the bundle files.

    Args:
        settings (dict): The settings object.

    Returns:
        dict: The rendered bundle files.
    """
    env = environment()
    context = context_module.build(settings)

    files = {
        "gkh-deploy.yaml": yaml.safe_dump(
            data=settings,
            sort_keys=False,
        ),
    }

    for name, template in TEMPLATED.items():
        files[name] = env.get_template(template).render(context)

    return {name: _ensure_newline(body) for name, body in files.items()}


def values(settings: dict) -> dict:
    """Render the Helm values.

    Args:
        settings (dict): The settings object.

    Returns:
        dict: The rendered Helm values.
    """
    return yaml.safe_load(bundle(settings)["values.yaml"])


def _ensure_newline(body: str) -> str:
    return body if body.endswith("\n") else body + "\n"

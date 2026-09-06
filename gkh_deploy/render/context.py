#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""GEO Knowledge Hub deploy - Bundle rendering context."""

import pydash
import yaml

from gkh_deploy import APP_VERSION, CHART_NAME, CHART_VERSION, DOCS_URL
from gkh_deploy import steps as steps_module
from gkh_deploy.render.k8s import WORKER_CONTAINER, worker_selector

#
# Constants - Rate limit storage
# > A Helm expression, resolved by the chart, so it follows redis.enabled and
# > redisExternal rather than naming a service this project would have to track.
#
RATELIMIT_STORAGE_URL = 'redis://{{ include "invenio.redis.hostname" . }}:6379/3'

#
# Constants - Extra configuration entries
#
BASE_EXTRA_CONFIG = {
    "INVENIO_APP_ALLOWED_HOSTS": None,
    "INVENIO_LOGGING_CONSOLE_LEVEL": "WARNING",
    # The chart injects RATELIMIT_STORAGE_URI, which the flask-limiter the application
    # image ships is too old to read. Without the _URL spelling it falls back to
    # redis://localhost:6379 and every request answers 500. The chart runs extraConfig
    # through `tpl`, so this resolves to the same Redis it uses for the URI.
    "INVENIO_RATELIMIT_STORAGE_URL": RATELIMIT_STORAGE_URL,
}


#
# Functions
#
def extra_config(settings: dict) -> dict:
    """Update settings with extra configuration entries.

    Args:
        settings (dict): The settings object.

    Returns:
        dict: The updated settings object.
    """
    hostname = settings["hostname"]

    # get extra config entries
    entries = dict(BASE_EXTRA_CONFIG)
    entries["INVENIO_APP_ALLOWED_HOSTS"] = f'["{hostname}"]'

    # update settings object with extra config entries
    return pydash.merge(entries, settings.get("extra_config") or {})


def extra_values(settings: dict) -> str:
    """Update settings with extra values.

    Args:
        settings (dict): The settings object.

    Returns:
        str: The updated settings object.
    """
    extra = settings.get("extra_values") or {}

    if not extra:
        return ""

    return yaml.safe_dump(extra, sort_keys=False).strip()


def build(settings: dict) -> dict:
    """Build the rendering context object.

    Args:
        settings (dict): The settings object.

    Returns:
        dict: The rendering context object.
    """
    return {
        "settings": settings,
        "extra_config": extra_config(settings),
        "extra_values": extra_values(settings),
        "steps": steps_module.sequence_configuration_steps(
            admin_email=settings["admin"]["email"],
            admin_password=steps_module.PLACEHOLDER_PASSWORD,
        ),
        "selector": worker_selector(settings.get("release")),
        "container": WORKER_CONTAINER,
        "chart_name": CHART_NAME,
        "chart_version": CHART_VERSION,
        "app_version": APP_VERSION,
        "docs_url": DOCS_URL,
    }

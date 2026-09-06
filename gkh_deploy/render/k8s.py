#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""GEO Knowledge Hub deploy - Bundle rendering Kubernetes facts."""

#
# Constants - Kubernetes labels
#
CHART_LABEL = "app.kubernetes.io/name=invenio"
WORKER_LABEL = "app.kubernetes.io/component=worker"
INSTANCE_LABEL = "app.kubernetes.io/instance"

#
# Constants - Container names
#
WORKER_CONTAINER = "worker"


#
# Functions
#
def worker_selector(release: str | None = None) -> str:
    """Build the label selector."""
    parts = [CHART_LABEL, WORKER_LABEL]

    if release:
        parts.append(f"{INSTANCE_LABEL}={release}")

    return ",".join(parts)

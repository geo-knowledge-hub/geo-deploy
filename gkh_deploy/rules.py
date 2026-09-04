#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""GEO Knowledge Hub deploy - Rules."""

import enum
import re
from dataclasses import dataclass

import pydash
import yaml

from gkh_deploy.assets import CHART_VALUES

#
# Constants - Preset limits
# > common.resources.preset in bitnami/common: memory limits, in MiB.
#
PRESET_LIMITS = {
    "nano": 192,
    "micro": 384,
    "small": 768,
    "medium": 1536,
    "large": 3072,
    "xlarge": 6144,
    "2xlarge": 12288,
}

#
# Constants - OpenSearch pools
#
OPENSEARCH_POOLS = (
    "master",
    "data",
    "coordinating",
    "ingest",
)

#
# Constants - Free-form keys
# > Keys whose children are free-form and cannot be checked against the chart.
#
FREE_FORM = {
    "invenio.extraConfig",
    "invenio.extra_config",
    "invenio.default_users",
    "invenio.uwsgiExtraConfig",
    "opensearch",
    "postgresql",
    "redis",
    "rabbitmq",
}

#
# Constants - Derived URLs
#
DERIVED_URLS = (
    "INVENIO_SITE_UI_URL",
    "INVENIO_SITE_API_URL",
    "INVENIO_SITE_HOSTNAME",
    "INVENIO_TRUSTED_HOSTS",
)


#
# Classes
#
class Level(enum.StrEnum):
    """How much a finding matters."""

    error = "error"
    warning = "warning"


@dataclass(frozen=True)
class Finding:
    """Finding from a rule."""

    rule: str
    level: Level
    message: str
    basis: str


#
# Auxiliary functions
#
def _mib(value: object) -> int | None:
    """Parse a Kubernetes or JVM memory quantity into MiB.

    Args:
        value (object): The value to parse.

    Returns:
        int | None: The memory quantity in MiB.
    """
    if value is None:
        return None

    # parse the value
    text = str(value).strip()
    match = re.fullmatch(r"(\d+)\s*([a-zA-Z]*)", text)

    # if the value is not a valid memory quantity, return None
    if not match:
        return None

    # extract the amount and unit
    amount, unit = int(match.group(1)), match.group(2).lower()

    # define the factors
    factors = {
        "": 1 / (1024 * 1024),
        "m": 1,
        "mi": 1,
        "g": 1024,
        "gi": 1024,
        "k": 1 / 1024,
        "ki": 1 / 1024,
    }

    # if the unit is not a valid factor, return None
    if unit not in factors:
        return None

    # return the memory quantity in MiB
    return int(amount * factors[unit])


#
# Rules
#
def datacite_secret_unreachable(values: dict) -> list[Finding]:
    """Inline DataCite credentials are dropped when an existing Secret is named."""
    # get the datacite settings
    datacite = pydash.get(values, "invenio.datacite") or {}

    if not datacite.get("enabled"):
        return []

    # get the existing secret and inline credentials
    existing = datacite.get("existingSecret") or datacite.get("existing_secret")
    inline = datacite.get("username") or datacite.get("password")

    # if both the existing secret and inline credentials are set, return a finding
    if existing and inline:
        return [
            Finding(
                "datacite-secret-unreachable",
                Level.error,
                f"invenio.datacite names existingSecret '{existing}' and also sets "
                "username/password inline. The chart creates no Secret when either "
                "existingSecret or existing_secret is set, so the inline credentials are "
                f"discarded and every pod gets a secretKeyRef to '{existing}', which will "
                "not exist. Clear the inline credentials and create that Secret yourself.",
                "templates/datacite-secret.yaml renders only when both spellings are empty",
            )
        ]

    # if neither the existing secret nor inline credentials are
    # set, return a finding
    if not existing and not inline:
        return [
            Finding(
                "datacite-secret-unreachable",
                Level.warning,
                "invenio.datacite is enabled with neither existingSecret nor inline "
                "credentials. The chart will create a Secret holding empty values.",
                "templates/datacite-secret.yaml b64encs whatever username/password hold",
            )
        ]

    return []


def opensearch_heap_oversized(values: dict) -> list[Finding]:
    """A JVM heap above half the container limit is OOMKilled under indexing load."""
    findings = []
    opensearch = values.get("opensearch") or {}

    # check pools
    for pool in OPENSEARCH_POOLS:
        # get the node settings
        node = opensearch.get(pool) or {}

        # if the node is scaled to 0, skip
        if node.get("replicaCount") == 0:
            continue

        # get the heap size and limit
        heap = _mib(node.get("heapSize"))
        limit = _mib(pydash.get(node, "resources.limits.memory"))

        # if the limit is not set, use the preset limit
        if limit is None:
            limit = PRESET_LIMITS.get(node.get("resourcesPreset"))

        # if the heap size or limit is not set, skip
        if heap is None or limit is None:
            continue

        # if the heap size is more than twice the limit, return a finding
        if heap * 2 > limit:
            findings.append(
                Finding(
                    "opensearch-heap-oversized",
                    Level.error,
                    f"opensearch.{pool} sets heapSize {node.get('heapSize')} against a memory "
                    f"limit of {limit}Mi ({heap * 100 // limit}% of it). Keep the heap at or "
                    "below half the limit, or the JVM is OOMKilled while the vocabularies "
                    "are indexed, which surfaces as search timeouts.",
                    "bitnami common _resources.tpl presets. Bitnami's own guidance is half "
                    "the container memory",
                )
            )

    # return!
    return findings


def default_users_not_a_mapping(values: dict) -> list[Finding]:
    """The chart iterates default_users as a mapping, not a list."""
    users = pydash.get(values, "invenio.default_users")

    if users is None or isinstance(users, dict):
        return []

    return [
        Finding(
            "default-users-not-a-mapping",
            Level.error,
            f"invenio.default_users is a {type(users).__name__}. It must be a mapping of "
            "email to password. The chart's own values.yaml documents the default as [], "
            "but a list silently creates no users.",
            "templates/install-init-job.yaml iterates it with range $usr, $pass",
        )
    ]


def init_job_enabled(values: dict) -> list[Finding]:
    """The chart's init job overlaps with, and precedes, the bootstrap sequence."""
    if not pydash.get(values, "invenio.init"):
        return []

    return [
        Finding(
            "init-job-enabled",
            Level.error,
            "invenio.init is true. The chart's install job creates only the admin user and "
            "runs before the vocabularies exist, and everything it does is covered by the "
            "bootstrap sequence. Set it to false.",
            "templates/install-init-job.yaml is gated on .Values.invenio.init",
        )
    ]


def hostname_override_inconsistent(values: dict) -> list[Finding]:
    """Overriding the chart's derived URLs can make them disagree."""
    extra = pydash.get(values, "invenio.extraConfig") or {}

    # get the overridden URLs
    overridden = [key for key in DERIVED_URLS if key in extra]

    # if no URLs are overridden, return
    if not overridden:
        return []

    # get the overridden UI and API URLs
    ui, api = extra.get("INVENIO_SITE_UI_URL"), extra.get("INVENIO_SITE_API_URL")

    # if the UI and API URLs are not consistent, return a finding
    if ui and api and api.rstrip("/") != f"{ui.rstrip('/')}/api":
        return [
            Finding(
                "hostname-override-inconsistent",
                Level.error,
                f"invenio.extraConfig overrides the chart's derived URLs, but "
                f"INVENIO_SITE_API_URL ({api}) is not INVENIO_SITE_UI_URL ({ui}) plus '/api'. "
                "The application returns 400s when they disagree.",
                "chart values.yaml: invenio.hostname is templated into TRUSTED_HOSTS, "
                "SITE_HOSTNAME and SITE_URL",
            )
        ]

    # if the UI URL is set but the API URL is not, return a finding
    if ui and not api:
        return [
            Finding(
                "hostname-override-inconsistent",
                Level.warning,
                "invenio.extraConfig overrides INVENIO_SITE_UI_URL but not "
                "INVENIO_SITE_API_URL, so the two are derived from different hostnames.",
                "chart values.yaml: invenio.hostname is templated into TRUSTED_HOSTS, "
                "SITE_HOSTNAME and SITE_URL",
            )
        ]

    return []


def image_tag_not_pinned(values: dict) -> list[Finding]:
    """An unpinned image makes a deployment unreproducible."""
    tag = pydash.get(values, "image.tag")

    if tag and tag != "latest":
        return []

    return [
        Finding(
            "image-tag-not-pinned",
            Level.warning,
            f"image.tag is {tag!r}. Pin a known-good release tag so the same configuration "
            "always produces the same instance.",
            "the GEO Knowledge Hub chart overlay: never `latest`",
        )
    ]


def deprecated_extra_config(values: dict) -> list[Finding]:
    """invenio.extra_config still works, but is the deprecated spelling."""

    if not pydash.get(values, "invenio.extra_config"):
        return []

    return [
        Finding(
            "deprecated-extra-config",
            Level.warning,
            "invenio.extra_config is the deprecated spelling. It is still read, and "
            "invenio.extraConfig wins where both set the same key. Use extraConfig.",
            "chart values.yaml: 'invenio.extra_config DEPRECATED: invenio.extraConfig instead'",
        )
    ]


def redundant_ratelimit_storage_url(values: dict) -> list[Finding]:
    """RATELIMIT_STORAGE_URL is dead weight on this InvenioRDM version."""
    extra = pydash.get(values, "invenio.extraConfig") or {}

    if "INVENIO_RATELIMIT_STORAGE_URL" not in extra:
        return []

    return [
        Finding(
            "redundant-ratelimit-storage-url",
            Level.warning,
            "invenio.extraConfig sets INVENIO_RATELIMIT_STORAGE_URL. It has no effect: "
            "flask-limiter reads RATELIMIT_STORAGE_URI first and only falls back to "
            "_URL, and the chart already injects the URI. The _URL spelling is deprecated "
            "and was removed in flask-limiter 3.",
            "flask-limiter 2.9.2 extension.py: "
            "config.get(STORAGE_URI, config.get(STORAGE_URL, None))",
        )
    ]


def unknown_chart_key(values: dict) -> list[Finding]:
    """Keys the chart does not read are accepted by Helm and silently ignored."""
    known = yaml.safe_load(CHART_VALUES.read_text()) or {}
    findings = []

    for path in sorted(_unknown_paths(values, known, prefix="")):
        findings.append(
            Finding(
                "unknown-chart-key",
                Level.error,
                f"'{path}' is not a key this chart defines. Helm accepts unknown values "
                "and ignores them, so the setting has no effect and nothing reports it.",
                "the chart ships no values.schema.json, so Helm validates nothing",
            )
        )

    return findings


def _unknown_paths(given: dict, known: dict, prefix: str) -> list[str]:
    """Walk two mappings together, collecting paths absent from the known one."""
    unknown = []

    for key, value in given.items():
        path = f"{prefix}.{key}" if prefix else key

        if key not in known:
            unknown.append(path)
            continue

        # if the path is in the free-form keys or the value is not a dict, skip
        if path in FREE_FORM or not isinstance(value, dict):
            continue

        # if the value is a dict, walk it
        if isinstance(known[key], dict):
            unknown.extend(_unknown_paths(value, known[key], path))

    return unknown


#
# Define all rules
#
ALL = (
    datacite_secret_unreachable,
    opensearch_heap_oversized,
    default_users_not_a_mapping,
    init_job_enabled,
    hostname_override_inconsistent,
    unknown_chart_key,
    image_tag_not_pinned,
    deprecated_extra_config,
    redundant_ratelimit_storage_url,
)


def check(values: dict) -> list[Finding]:
    """Run every rule, errors first.

    Args:
        values (dict): The values.

    Returns:
        list[Finding]: The findings.
    """
    # run every rule
    findings = [finding for rule in ALL for finding in rule(values)]

    # sort the findings
    return sorted(findings, key=lambda f: (f.level != Level.error, f.rule))

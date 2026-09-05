#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

import pytest

from gkh_deploy import rules

#
# One row per rule:
#   values that must trip it, values that must not, and the
#   name it reports
#
CASES = [
    (
        rules.datacite_secret_unreachable,
        {
            "invenio": {
                "datacite": {
                    "enabled": True,
                    "username": "GKH.EXAMPLE",
                    "password": "secret",
                    "existingSecret": "datacite-secrets",
                }
            }
        },
        {
            "invenio": {
                "datacite": {"enabled": True, "existingSecret": "gkh-datacite"},
            },
        },
        "datacite-secret-unreachable",
    ),
    (
        rules.opensearch_heap_oversized,
        {
            "opensearch": {
                "data": {"resourcesPreset": "medium", "heapSize": "1024m"},
            },
        },
        {
            "opensearch": {
                "master": {
                    "heapSize": "1024m",
                    "resources": {
                        "limits": {"memory": "2Gi"},
                    },
                }
            }
        },
        "opensearch-heap-oversized",
    ),
    (
        rules.default_users_not_a_mapping,
        {
            "invenio": {
                "default_users": [],
            },
        },
        {
            "invenio": {
                "default_users": {
                    "admin@example.org": "pw",
                },
            },
        },
        "default-users-not-a-mapping",
    ),
    (
        rules.init_job_enabled,
        {
            "invenio": {
                "init": True,
            },
        },
        {
            "invenio": {
                "init": False,
            },
        },
        "init-job-enabled",
    ),
    (
        rules.hostname_override_inconsistent,
        {
            "invenio": {
                "extraConfig": {
                    "INVENIO_SITE_UI_URL": "https://a.example.org",
                    "INVENIO_SITE_API_URL": "https://b.example.org/api",
                }
            }
        },
        {
            "invenio": {
                "extraConfig": {
                    "INVENIO_SITE_UI_URL": "https://a.example.org:8080",
                    "INVENIO_SITE_API_URL": "https://a.example.org:8080/api",
                }
            }
        },
        "hostname-override-inconsistent",
    ),
    (
        rules.unknown_chart_key,
        {
            "madeUpTopLevelKey": True,
        },
        {
            "invenio": {
                "extraConfig": {
                    "ANYTHING_AT_ALL": "1",
                },
            },
        },
        "unknown-chart-key",
    ),
    (
        rules.unknown_chart_key,
        {
            "app": {
                "extraConfig": {
                    "INVENIO_X": "1",
                },
            },
        },
        {
            "invenio": {
                "init": False,
            },
        },
        "unknown-chart-key",
    ),
    (
        rules.image_tag_not_pinned,
        {
            "image": {
                "tag": "latest",
            },
        },
        {
            "image": {
                "tag": "v1.7.0.dev17",
            },
        },
        "image-tag-not-pinned",
    ),
    (
        rules.deprecated_extra_config,
        {
            "invenio": {
                "extra_config": {
                    "INVENIO_X": "1",
                },
            },
        },
        {"invenio": {"extra_config": {}}},
        "deprecated-extra-config",
    ),
    (
        rules.ratelimit_storage_url_missing,
        {
            "invenio": {
                "extraConfig": {
                    "INVENIO_RATELIMIT_STORAGE_URI": "redis://x:6379/3",
                },
            },
        },
        {
            "invenio": {
                "extraConfig": {
                    "INVENIO_RATELIMIT_STORAGE_URL": "redis://x:6379/3",
                },
            },
        },
        "ratelimit-storage-url-missing",
    ),
]


@pytest.mark.parametrize("rule, tripping, clean, name", CASES)
def test_each_rule_catches_what_it_is_for_and_stays_quiet_otherwise(rule, tripping, clean, name):
    assert [f.rule for f in rule(tripping)] == [name]
    assert rule(clean) == []


def test_a_clean_configuration_has_no_findings():
    values = {
        "image": {"tag": "v1.7.0.dev17"},
        "invenio": {
            "hostname": "gkhub.example.org",
            "init": False,
            "extraConfig": {"INVENIO_RATELIMIT_STORAGE_URL": "redis://x:6379/3"},
        },
    }

    assert rules.check(values) == []


def test_errors_are_reported_before_warnings_and_every_finding_carries_a_basis():
    values = {
        "image": {"tag": "latest"},
        "invenio": {
            "init": True,
            "default_users": [],
            "extraConfig": {
                "INVENIO_SITE_UI_URL": "https://a.example.org",
                "INVENIO_SITE_API_URL": "https://b.example.org/api",
            },
        },
    }

    # check the values
    findings = rules.check(values)
    levels = [f.level for f in findings]

    # assert
    assert levels == sorted(levels, key=lambda level: level is not rules.Level.error)
    assert rules.Level.error in levels and rules.Level.warning in levels
    assert all(f.basis for f in findings)

#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Test bootstrap."""

import json

from gkh_cli import Context, Output
from typer.testing import CliRunner

from gkh_deploy import DOCS_URL, steps
from gkh_deploy.cli import app
from gkh_deploy.render import k8s

#
# Constants - CliRunner
#
runner = CliRunner()

#
# Constants - NAMES
#
#
NAMES = [
    "db",
    "files",
    "roles",
    "access",
    "users",
    "index",
    "fixtures",
]


#
# Auxiliary functions
#
def bootstrap(config, *arguments, **kwargs):
    return runner.invoke(app, ["bootstrap", "-c", str(config), *arguments], **kwargs)


def test_bootstrap_says_the_pod_the_container_and_the_password(settings, config_file):
    result = bootstrap(config_file(settings))

    # assert
    assert k8s.worker_selector(settings["release"]) in result.stdout
    assert f"'{k8s.WORKER_CONTAINER}'" in result.stdout
    assert steps.PLACEHOLDER_PASSWORD in result.stdout
    assert DOCS_URL in result.stdout


def test_only_narrows_to_one_step_and_an_unknown_step_is_a_usage_error(settings, config_file):
    config = config_file(settings)
    narrowed = bootstrap(config, "--only", "db")

    assert "invenio db init" in narrowed.stdout
    assert "rdm-records fixtures" not in narrowed.stdout
    assert bootstrap(config, "--only", "nope").exit_code == 2


def test_bootstrap_emits_json_when_asked(settings, config_file):
    result = bootstrap(config_file(settings), obj=Context(output=Output.json))
    payload = json.loads(result.stdout)

    # assert
    assert [step["name"] for step in payload["steps"]] == NAMES
    assert payload["steps"][0]["commands"] == ["invenio db init", "invenio db create"]

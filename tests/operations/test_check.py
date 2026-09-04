#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Test check."""

import json

from gkh_cli import Context, Output
from typer.testing import CliRunner

from gkh_deploy.cli import app

#
# Constants - CliRunner
#
runner = CliRunner()


#
# Auxiliary functions
#
def bundle_with(tmp_path, values):
    directory = tmp_path / "bundle"
    directory.mkdir()

    (directory / "values.yaml").write_text(values)

    return directory


def test_check_reports_a_problem_in_a_rendered_bundle(tmp_path):
    directory = bundle_with(tmp_path, "invenio:\n  init: true\n")

    result = runner.invoke(app, ["check", "-d", str(directory)])

    # assert
    assert result.exit_code == 1
    assert "init-job-enabled" in result.stdout


def test_check_reports_a_missing_settings_file_or_a_bundle_without_values(tmp_path):
    missing = runner.invoke(app, ["check", "-c", str(tmp_path / "absent.yaml")])

    assert missing.exit_code == 1
    assert "no such configuration file" in missing.stderr

    empty = runner.invoke(app, ["check", "-d", str(tmp_path)])

    assert empty.exit_code == 1
    assert "no values.yaml" in empty.stderr


def test_strict_turns_warnings_into_a_failure(tmp_path):
    directory = bundle_with(tmp_path, "image:\n  tag: latest\n")

    assert runner.invoke(app, ["check", "-d", str(directory)]).exit_code == 0
    assert runner.invoke(app, ["check", "-d", str(directory), "--strict"]).exit_code == 1


def test_check_emits_json_when_asked(tmp_path):
    directory = bundle_with(tmp_path, "image:\n  tag: latest\n")

    result = runner.invoke(app, ["check", "-d", str(directory)], obj=Context(output=Output.json))
    payload = json.loads(result.stdout)

    # assert
    assert payload["findings"][0]["rule"] == "image-tag-not-pinned"

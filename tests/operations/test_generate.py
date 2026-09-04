#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Test generate."""

import yaml
from typer.testing import CliRunner

from gkh_deploy.cli import app

#
# Constants - CliRunner
#
runner = CliRunner()


#
# Auxiliary functions
#
def generate(config, out, *arguments):
    return runner.invoke(app, ["generate", "-c", str(config), "-o", str(out), *arguments])


def test_generate_writes_the_whole_bundle(tmp_path, settings, config_file):
    # generate the bundle
    out = tmp_path / "bundle"
    result = generate(config_file(settings), out)

    # assert
    assert result.exit_code == 0
    assert sorted(p.name for p in out.iterdir()) == [
        "README.md",
        "bootstrap.sh",
        "gkh-deploy.yaml",
        "secrets.sh",
        "values.yaml",
    ]


def test_generate_refuses_when_a_check_fails_unless_skip_check_is_passed(
    tmp_path, settings, config_file
):
    settings["extra_values"] = {"madeUpKey": True}
    config = config_file(settings)
    refused = tmp_path / "refused"

    result = generate(config, refused)

    assert result.exit_code == 1
    assert "refusing to render" in result.stderr
    assert not refused.exists()

    skipped = tmp_path / "skipped"

    assert generate(config, skipped, "--skip-check").exit_code == 0
    assert (skipped / "values.yaml").is_file()


def test_generate_refuses_a_non_empty_directory(tmp_path, settings, config_file):
    out = tmp_path / "bundle"
    out.mkdir()

    (out / "keep.txt").write_text("mine\n")

    result = generate(config_file(settings), out)

    assert result.exit_code == 1
    assert "not empty" in result.stderr


def test_set_overrides_reach_the_bundle_and_print_writes_nothing_to_disk(
    tmp_path, settings, config_file
):
    config = config_file(settings)
    written = tmp_path / "written"

    # generate the bundle
    generate(config, written, "--set", "scaling.web_replicas=5")

    # assert
    assert yaml.safe_load((written / "values.yaml").read_text())["web"]["replicas"] == 5

    # print the bundle
    printed = tmp_path / "printed"
    result = generate(config, printed, "--print")

    # assert
    assert result.exit_code == 0
    assert "values.yaml" in result.stdout
    assert not printed.exists()

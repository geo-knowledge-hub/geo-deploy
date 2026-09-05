#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

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
def init(*arguments):
    return runner.invoke(app, ["init", "--non-interactive", *arguments])


def test_init_writes_a_configuration_that_validates(tmp_path):
    out = tmp_path / "gkh-deploy.yaml"
    result = init(
        "--hostname", "a.example.org", "--admin-email", "admin@example.org", "-o", str(out)
    )

    assert result.exit_code == 0
    assert yaml.safe_load(out.read_text())["hostname"] == "a.example.org"


def test_standard_needs_a_datacite_prefix_and_set_supplies_it(tmp_path):
    """standard enables datacite, which has no default prefix to fall back on."""
    out = tmp_path / "gkh-deploy.yaml"
    arguments = ["--profile", "standard", "--hostname", "a.org", "--admin-email", "a@b.org"]

    # without a value defined, init refuses and writes nothing
    assert init(*arguments, "-o", str(out)).exit_code == 1
    assert not out.exists()

    # with a value set, it writes a configuration that validates
    assert init(*arguments, "--set", "datacite.prefix=10.1234", "-o", str(out)).exit_code == 0
    assert yaml.safe_load(out.read_text())["datacite"]["prefix"] == "10.1234"


def test_a_malformed_override_is_a_usage_error(tmp_path):
    result = init(
        "--set",
        "nonsense",
        "--hostname",
        "a.org",
        "--admin-email",
        "a@b.org",
        "-o",
        str(tmp_path / "c.yaml"),
    )

    assert result.exit_code == 2


def test_an_unknown_profile_is_a_usage_error(tmp_path):
    result = init(
        "--profile",
        "nope",
        "--hostname",
        "a.org",
        "--admin-email",
        "a@b.org",
        "-o",
        str(tmp_path / "c.yaml"),
    )

    assert result.exit_code == 2

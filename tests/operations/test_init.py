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

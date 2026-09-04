#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Test CLI."""

from typer.testing import CliRunner

from gkh_deploy.cli import app

#
# Constants - CliRunner
#
runner = CliRunner()


def test_the_group_registers_the_four_commands():
    result = runner.invoke(app, ["--help"])

    for command in ("init", "check", "generate", "bootstrap"):
        assert command in result.stdout

#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""GEO Knowledge Hub deploy - CLI check command."""

from pathlib import Path
from typing import Annotated

import typer
import yaml
from gkh_cli import context_of

from gkh_deploy import render, rules
from gkh_deploy.operations.common import DEFAULT_CONFIG, ConfigFile, load_settings, report


def check(
    ctx: typer.Context,
    config: ConfigFile = DEFAULT_CONFIG,
    directory: Annotated[
        Path | None, typer.Option("--dir", "-d", help="Check a rendered bundle instead.")
    ] = None,
    strict: Annotated[bool, typer.Option("--strict", help="Treat warnings as errors.")] = False,
) -> None:
    """Check configuration / bundle.

    This command checks the configuration / bundle against known failure modes.

    Args:
        ctx (typer.Context): The Typer context.

        config (ConfigFile): The configuration file.

        directory (Path | None): The directory to check.

        strict (bool): Whether to treat warnings as errors.

    Returns:
        None. This function is called for its side effects.

    Raises:
        typer.Exit: when the check fails.
    """
    # check the values
    findings = rules.check(
        _values_to_check(
            config=config,
            directory=directory,
        )
    )

    # get the errors and warnings
    errors = [f for f in findings if f.level is rules.Level.error]
    warnings = [f for f in findings if f.level is rules.Level.warning]

    # report the findings
    report(
        findings=findings,
        output=context_of(ctx).output,
    )

    # raise an error if there are errors or warnings and
    # strict is True
    if errors or (strict and warnings):
        raise typer.Exit(code=1)


def _values_to_check(config: Path, directory: Path | None) -> dict:
    """Define Helm values to check.

    Args:
        config (Path): The configuration file.

        directory (Path | None): The directory to check.

    Returns:
        dict: The Helm values to check.

    Raises:
        typer.Exit: when a directory holds no values.yaml.
    """
    # if no directory is provided, load the values from
    # the configuration
    if directory is None:
        return render.values(load_settings(config, []))

    # otherwise, get the path to the values.yaml file
    path = directory / "values.yaml"

    # if there is no dir or values available, raise an error
    if not path.is_file():
        typer.echo(f"gkh deploy: no values.yaml in {directory}", err=True)

        raise typer.Exit(code=1)

    # load the values
    return yaml.safe_load(path.read_text()) or {}

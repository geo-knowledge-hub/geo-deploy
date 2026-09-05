#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""GEO Knowledge Hub deploy - Common operations."""

import json
from pathlib import Path
from typing import Annotated

import typer
from gkh_cli import Output

from gkh_deploy import rules
from gkh_deploy import settings as settings_module

#
# Constants
#
DEFAULT_CONFIG = Path("gkh-deploy.yaml")
DEFAULT_OUTPUT = Path("deploy")

#
# Types
#
ConfigFile = Annotated[Path, typer.Option("--config", "-c", help="Configuration to read.")]
Profile = Annotated[str, typer.Option("--profile", help="Start from a shipped profile.")]
Force = Annotated[bool, typer.Option("--force", help="Overwrite what is already there.")]
Overrides = Annotated[
    list[str] | None,
    typer.Option("--set", help="Override one value, as KEY=VALUE. Repeatable."),
]


def load_settings(path: Path, overrides: list[str]) -> dict:
    """Read a settings file.

    Read settings file and replace values on-the-fly.

    Args:
        path (Path): The path to the settings file.

        overrides (list[str]): The overrides to apply.

    Returns:
        dict: The settings object.

    Raises:
        typer.Exit: when the settings file cannot be read, or does not validate.
    """
    # try to load the settings
    try:
        settings = settings_module.apply_overrides(
            settings=settings_module.load(path=path),
            overrides=overrides,
        )

    except (FileNotFoundError, ValueError) as exc:
        typer.echo(f"gkh deploy: {exc}", err=True)

        raise typer.Exit(code=1) from exc

    # validate the settings
    fail_on(
        problems=settings_module.validate(
            settings=settings,
        ),
    )

    # return!
    return settings


def fail_on(problems: list[str]) -> None:
    """Report errors and exit.

    If there are problems, report to user and exit.

    Args:
        problems (list[str]): The problems to report.

    Returns:
        None. This function is called for its side effects.

    Raises:
        typer.Exit: when there is at least one problem.
    """
    if not problems:
        return

    for problem in problems:
        typer.echo(f"gkh deploy: {problem}", err=True)

    raise typer.Exit(code=1)


def report(findings: list[rules.Finding], output: Output) -> None:
    """Report findings.

    If there are findings, report them in the requested output format.

    Args:
        findings (list[rules.Finding]): The findings to report.

        output (Output): The output format.

    Returns:
        None. This function is called for its side effects.
    """
    # if the output is JSON
    if output is Output.json:
        # print the findings as JSON
        typer.echo(
            json.dumps(
                {
                    "findings": [
                        {
                            "rule": f.rule,
                            "level": str(f.level),
                            "message": f.message,
                            "basis": f.basis,
                        }
                        for f in findings
                    ]
                },
                indent=2,
            )
        )

        return

    # if there are no findings, report a success message
    if not findings:
        typer.echo("No problems found.")

        return

    # print the findings
    for finding in findings:
        typer.echo(f"{finding.level}: [{finding.rule}] {finding.message}")
        typer.echo(f"  basis: {finding.basis}\n")

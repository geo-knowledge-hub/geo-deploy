#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""GEO Knowledge Hub validation - CLI main module."""

import enum
import importlib.util
from typing import Annotated

import typer
from gkh_cli import context_of

from gkh_validation import CONFIG
from gkh_validation.settings import load_config_bool_from_env, load_config_value, load_env_file

#
# Constants - CLI app
#
app = typer.Typer(help="Check a running GEO Knowledge Hub instance.", no_args_is_help=True)

#
# Constants - User messages
#
MESSAGE_NO_INSTANCE = "gkh: no instance. Pass --url or set GKH_BASE_URL."
MESSAGE_INSTALL_HINT = "gkh: the suite is not installed. Install it with the 'validation' extra:"
MESSAGE_INSTALL_COMMAND = "    uv tool install --with 'gkh-deploy[validation]' gkh-cli"

#
# Constants - What the suite needs to run
# > All three come from the `validation` extra. pytest alone is not enough to go on:
# > it is a development dependency too, so it can be present while the rest is not.
#
REQUIREMENTS = ("pytest", "requests", "dotenv")


#
# Classes
#
class Suite(enum.StrEnum):
    """Which part of the suite to run."""

    all = "all"
    api = "api"
    ui = "ui"


#
# Auxiliary functions
#
def _target(suite: Suite) -> str:
    """Resolve a suite to the import path pytest collects.

    Args:
        suite (Suite): The part of the suite to run.

    Returns:
        str: The import path.
    """
    if suite is Suite.all:
        return "gkh_validation"

    return f"gkh_validation.{suite}"


#
# CLI options
#
SuiteOption = Annotated[
    Suite,
    typer.Option("--suite", help="Which part of the suite to run."),
]

AllowPublish = Annotated[
    bool,
    typer.Option(
        "--allow-publish",
        help="Run the tests that publish. A published record cannot be deleted.",
    ),
]


#
# Commands
#
@app.callback()
def main() -> None:
    """Check a running GEO Knowledge Hub instance.

    Drives the instance over its API and UI and reports what does not hold. It
    reads, and only writes when you ask it to.
    """


@app.command()
def run(
    ctx: typer.Context,
    suite: SuiteOption = Suite.all,
    allow_publish: AllowPublish = False,
) -> None:
    """Run the validation suite against an instance.

    Args:
        ctx (typer.Context): The Typer context, carrying the shared gkh settings.

        suite (Suite): The part of the suite to run.

        allow_publish (bool): Whether to run the tests that publish.

    Raises:
        typer.Exit: with pytest's exit code, 2 when there is no instance.
    """
    if any(importlib.util.find_spec(name) is None for name in REQUIREMENTS):
        typer.echo(MESSAGE_INSTALL_HINT, err=True)
        typer.echo(MESSAGE_INSTALL_COMMAND, err=True)

        raise typer.Exit(code=2)

    import pytest

    # Get context
    gkh = context_of(ctx)

    # The suite reads a `.env` of its own once it starts, which is too late to answer
    # for the settings below. Read it here as well, so a flag still wins over the
    # environment, and the environment over the file, whichever side asks first.
    load_env_file()

    url = load_config_value("GKH_BASE_URL", gkh.url)
    token = load_config_value("GKH_API_TOKEN", gkh.token)
    verify_tls = gkh.verify_tls and not load_config_bool_from_env("GKH_NO_VERIFY_TLS")

    # without an instance there is nothing to check
    if not url:
        typer.echo(MESSAGE_NO_INSTANCE, err=True)

        raise typer.Exit(code=2)

    # Define arguments for the pytest execution
    # -c keeps the run anchored to the suite's own configuration
    args = ["-c", str(CONFIG), "--pyargs", _target(suite), "--base-url", url]

    # Append token if available
    if token:
        args += ["--api-token", token]

    # Validate SSL / TLS
    if not verify_tls:
        args.append("--no-verify-tls")

    # Ensure allow publication
    if allow_publish:
        args.append("--allow-publish")

    raise typer.Exit(code=int(pytest.main(args)))

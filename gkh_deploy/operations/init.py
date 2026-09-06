#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""GEO Knowledge Hub deploy - CLI init command."""

from pathlib import Path
from typing import Annotated

import typer
from gkh_cli import context_of

from gkh_deploy import profiles
from gkh_deploy import settings as settings_module
from gkh_deploy.operations.common import DEFAULT_CONFIG, Force, Overrides, Profile, fail_on


def init(
    ctx: typer.Context,
    output: Annotated[
        Path, typer.Option("--output", "-o", help="Where to write it.")
    ] = DEFAULT_CONFIG,
    profile: Profile = "minimal",
    hostname: Annotated[str, typer.Option("--hostname", help="Hostname users will reach.")] = "",
    admin_email: Annotated[str, typer.Option("--admin-email", help="Administrator email.")] = "",
    set_: Overrides = None,
    non_interactive: Annotated[
        bool, typer.Option("--non-interactive", help="Never prompt; fail if an answer is missing.")
    ] = False,
    force: Force = False,
) -> None:
    """Write a configuration, asking only what cannot be defaulted.

    Args:
        ctx (typer.Context): The Typer context.

        output (Path): The output directory.

        profile (Profile): The profile to use.

        hostname (str): The hostname users will reach the instance on.

        admin_email (str): The administrator email.

        set_ (list[str] | None): The overrides to apply to the profile.

        non_interactive (bool): Whether to run non-interactively.

        force (Force): Whether to force overwrite.

    Raises:
        typer.Exit: when the output directory already exists and force is False.
        typer.BadParameter: when the profile is not found, or an override is malformed.
    """
    if output.exists() and not force:
        typer.echo(f"gkh deploy: {output} already exists; pass --force to overwrite", err=True)

        raise typer.Exit(code=1)

    # load the profile
    try:
        answers = profiles.load(profile)

    except FileNotFoundError as exc:
        raise typer.BadParameter(str(exc), param_hint="--profile") from exc

    # get the shared context
    shared = context_of(ctx)

    # get the hostname from the URL
    hostname = hostname or _host_of(shared.url)

    # if not non-interactive, prompt for the hostname and admin email
    if not non_interactive:
        hostname = hostname or typer.prompt("Hostname users will reach the instance on")
        admin_email = admin_email or typer.prompt("Administrator email")

    # update the answers
    answers["hostname"] = hostname
    answers["admin"]["email"] = admin_email

    # apply the overrides
    try:
        answers = settings_module.apply_overrides(answers, set_ or [])

    except ValueError as exc:
        raise typer.BadParameter(str(exc), param_hint="--set") from exc

    # validate the answers
    fail_on(settings_module.validate(answers))

    # write the answers to the output directory
    output.write_text(settings_module.dump(answers))

    # show the next step
    typer.echo(f"Wrote {output}. Review it, then run: gkh deploy generate -c {output}")


def _host_of(url: str | None) -> str:
    """Get the hostname inside a URL, if there is one.

    Args:
        url (str | None): The URL to get the hostname from.

    Returns:
        str: The hostname inside the URL.
    """
    if not url:
        return ""

    return url.split("://")[-1].split("/")[0]

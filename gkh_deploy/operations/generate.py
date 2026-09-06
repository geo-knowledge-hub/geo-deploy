#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""GEO Knowledge Hub deploy - CLI generate command."""

from pathlib import Path
from typing import Annotated

import typer
from gkh_cli import context_of

from gkh_deploy import CHART_NAME, CHART_VERSION, render, rules
from gkh_deploy.operations.common import (
    DEFAULT_CONFIG,
    DEFAULT_OUTPUT,
    ConfigFile,
    Force,
    Overrides,
    load_settings,
    report,
)


def generate(
    ctx: typer.Context,
    config: ConfigFile = DEFAULT_CONFIG,
    output: Annotated[
        Path, typer.Option("--output", "-o", help="Where to write.")
    ] = DEFAULT_OUTPUT,
    set_: Overrides = None,
    skip_check: Annotated[
        bool, typer.Option("--skip-check", help="Render even when check reports an error.")
    ] = False,
    print_: Annotated[
        bool, typer.Option("--print", help="Write to stdout instead of disk.")
    ] = False,
    force: Force = False,
) -> None:
    """Generate a deployment bundle.

    This command generates a deployment bundle from a configuration file.

    Args:
        ctx (typer.Context): The Typer context.

        config (ConfigFile): The configuration file.

        output (Path): The output directory.

        set_ (list[str] | None): The overrides to apply.

        skip_check (bool): Whether to skip the check.

        print_ (bool): Whether to print the bundle to stdout.

        force (bool): Whether to overwrite the output directory.

    Returns:
        None. This function is called for its side effects.

    Raises:
        typer.Exit: when the check fails and skip_check is False.
    """
    settings = load_settings(config, set_ or [])

    # check for errors
    findings = rules.check(render.values(settings))
    errors = [f for f in findings if f.level is rules.Level.error]

    # if there are errors
    if errors and not skip_check:
        # report
        report(findings=findings, output=context_of(ctx).output)

        # print error message
        typer.echo(
            "gkh deploy: refusing to render; fix the errors above or pass --skip-check", err=True
        )

        # exit!
        raise typer.Exit(code=1)

    # render the bundle
    files = render.bundle(settings)

    # show that will be generated in the bundle
    if print_:
        for name in sorted(files):
            typer.echo(f"--- {name}\n{files[name]}")

        return

    if output.exists() and any(output.iterdir()) and not force:
        typer.echo(
            message=f"gkh deploy: {output} is not empty; pass --force to overwrite",
            err=True,
        )

        raise typer.Exit(code=1)

    # write files
    for path in render.write(files, output):
        typer.echo(f"wrote {path}")

    # close!
    typer.echo(f"\nTargets {CHART_NAME} {CHART_VERSION}. Next: {output}/README.md")

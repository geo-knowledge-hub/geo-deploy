#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""GEO Knowledge Hub deploy - CLI bootstrap command."""

import json
from typing import Annotated

import typer
from gkh_cli import Output, context_of

from gkh_deploy import DOCS_URL
from gkh_deploy import steps as steps_module
from gkh_deploy.operations.common import DEFAULT_CONFIG, ConfigFile, load_settings
from gkh_deploy.render.k8s import WORKER_CONTAINER, worker_selector


def bootstrap(
    ctx: typer.Context,
    config: ConfigFile = DEFAULT_CONFIG,
    only: Annotated[str, typer.Option("--only", help="Print a single step.")] = "",
) -> None:
    """Show the configuration steps for the GEO Knowledge Hub."""
    settings = load_settings(path=config, overrides=[])

    # define step sequence
    steps = steps_module.sequence_configuration_steps(
        admin_email=settings["admin"]["email"],
        admin_password=steps_module.PLACEHOLDER_PASSWORD,
    )

    # select the step
    sequence = steps_module.select_step(sequence=steps, only=only)

    # print the sequence as JSON
    if context_of(ctx).output is Output.json:
        # define steps
        steps = {"steps": [_as_dict(step) for step in sequence]}
        steps = json.dumps(steps, indent=2)

        # print the steps
        typer.echo(steps)

        return

    # or show sequence as text
    _print_sequence(sequence, settings)


def _print_sequence(sequence: list[steps_module.Step], settings: dict) -> None:
    """Print the sequence as a numbered, commented plan.

    Args:
        sequence (list[steps_module.Step]): The sequence of steps.

        settings (dict): The settings of the GEO Knowledge Hub.

    Returns:
        None. This function is called for its side effects.

    Raises:
        typer.Exit: when the sequence is empty.
    """
    # get the namespace
    namespace = settings.get("namespace", "invenio")

    # print the header
    typer.echo(f"# Post-install sequence for namespace '{namespace}'.")
    typer.echo("# Run each step inside the worker container, in order, once `helm install`")
    typer.echo("# has settled and the worker pod is Running. Nothing here is executed for you.")

    # print the steps
    for position, step in enumerate(sequence, start=1):
        typer.echo(f"\n{position}. {step.name} — {step.description}")

        # print the commands
        for command in step.commands:
            typer.echo(f"     {command}")

    # print the footer
    typer.echo(f"\n# Replace {steps_module.PLACEHOLDER_PASSWORD} with the administrator password.")
    typer.echo("#")
    typer.echo("# The worker is the pod labelled:")
    typer.echo(f"#   {worker_selector(settings.get('release'))}")
    typer.echo(f"# and the container to enter is '{WORKER_CONTAINER}'.")
    typer.echo("#")
    typer.echo("# `gkh deploy generate` writes these same steps as ./bootstrap.sh, which finds")
    typer.echo("# that pod and runs them for you.")
    typer.echo("#")
    typer.echo("# `fixtures` only queues its work: the vocabulary records are written by")
    typer.echo("# Celery after the command returns. Until that drains the instance rejects")
    typer.echo("# values it has not stored yet, so wait for the workers to fall idle.")
    typer.echo("#")
    typer.echo("# `fixtures` takes several minutes. When it reports search timeouts the")
    typer.echo("# OpenSearch container is being OOMKilled rather than losing connectivity:")
    typer.echo("# check for pod restarts, then run `gkh deploy check`.")
    typer.echo(f"# Reference: {DOCS_URL}")


def _as_dict(step: steps_module.Step) -> dict:
    """Convert a step to a dictionary.

    This is used to print the sequence as JSON.

    Args:
        step (steps_module.Step): The step to convert.

    Returns:
        dict: The dictionary representation of the step.
    """

    # return the dictionary
    return {
        "name": step.name,
        "description": step.description,
        "commands": list(step.commands),
    }

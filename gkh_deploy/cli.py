#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""GEO Knowledge Hub deploy - CLI main module."""

import typer

from gkh_deploy.operations import bootstrap, check, generate, init

#
# Constants - CLI app
#
app = typer.Typer(help="Produce and verify a GEO Knowledge Hub deployment.", no_args_is_help=True)


#
# Functions
#
@app.callback()
def main() -> None:
    """Produce and verify a GEO Knowledge Hub deployment.

    Renders a ready-to-apply Helm bundle from a small configuration file, checks
    it against known failure modes, and states the post-install sequence.
    """


app.command()(init.init)
app.command()(check.check)
app.command()(generate.generate)
app.command()(bootstrap.bootstrap)

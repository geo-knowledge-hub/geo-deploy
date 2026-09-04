#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Test steps."""

import shlex
import subprocess

from gkh_deploy import render, steps
from gkh_deploy.render import k8s


#
# Auxiliary functions
#
def sequence(email="a@b.org", password="pw"):
    return steps.sequence_configuration_steps(
        admin_email=email,
        admin_password=password,
    )


def scripted_steps(script):
    pairs = []

    for line in script.splitlines():
        if line.startswith("run "):
            # split the line
            _, name, command = shlex.split(line)

            # add the pair
            pairs.append((name, command))

    return pairs


def test_the_sequence_is_the_documented_order_and_every_step_is_complete():
    # assert the sequence is the documented order
    assert [step.name for step in sequence()] == [
        "db",
        "files",
        "roles",
        "access",
        "users",
        "index",
        "fixtures",
    ]

    # assert every step is complete
    for step in sequence():
        assert step.commands, step.name
        assert step.description.endswith("."), step.name


def test_the_generated_scripts_are_valid_bash_and_enter_the_worker_container(settings, tmp_path):
    # render the bundle
    files = render.bundle(settings)
    render.write(files, tmp_path)

    # assert the scripts are valid bash
    for name in ("bootstrap.sh", "secrets.sh"):
        result = subprocess.run(
            ["bash", "-n", str(tmp_path / name)], capture_output=True, text=True
        )

        # assert
        assert result.returncode == 0, f"{name}: {result.stderr}"

    assert f"-c {k8s.WORKER_CONTAINER}" in files["bootstrap.sh"]

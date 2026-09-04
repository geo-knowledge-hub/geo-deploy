#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""GEO Knowledge Hub deploy - Steps."""

from dataclasses import dataclass

import typer

#
# Constants - Roles
#
ROLES = ("admin", "geo-community", "geo-provider", "geo-secretariat")
GEO_ROLES = ("geo-community", "geo-provider", "geo-secretariat")

#
# Constants - Data path
#
DATA_PATH = "/opt/invenio/var/instance/data"

#
# Constants - Placeholder password
#
PLACEHOLDER_PASSWORD = "CHANGE_ME"


#
# Classes
#
@dataclass(frozen=True)
class Step:
    """Workflow step definition."""

    name: str
    """The step name."""

    description: str
    """The step description."""

    commands: tuple[str, ...]
    """The commands to execute in the step."""

    @property
    def shell(self) -> str:
        """The commands as a single line (for a shell inside the pod)."""

        return " && ".join(self.commands)


#
# Functions
#
def select_step(sequence: list[Step], only: str) -> list[Step]:
    """Select a single step from the sequence.

    Args:
        sequence (list[Step]): The sequence of steps.

        only (str): The name of the step to select.

    Returns:
        list[Step]: The selected step.

    Raises:
        typer.BadParameter: when a named step does not exist.
    """
    if not only:
        return sequence

    # get all step names
    names = [step.name for step in sequence]

    # check if the step name exists
    if only not in names:
        raise typer.BadParameter(f"unknown step '{only}'; steps are: {', '.join(names)}")

    # return!
    return [step for step in sequence if step.name == only]


#
# Sequences
#
def sequence_configuration_steps(
    admin_email: str, admin_password: str, data_path: str = DATA_PATH
) -> list[Step]:
    """Build the sequence of the steps to configure the GEO Knowledge Hub.

    Args:
        admin_email (str): The email of the administrator.

        admin_password (str): The password of the administrator.

        data_path (str): The path to the data directory.

    Returns:
        list[Step]: The sequence of steps.

    Raises:
        typer.BadParameter: when a role is not valid.
    """
    # command - create the roles
    roles = [f"invenio roles create {role}" for role in ROLES]

    # command - create the grants
    grants = [
        "invenio access allow superuser-access role admin",
        "invenio access allow geo-provider-access role geo-provider",
    ]

    # command - add the administrator to the GEO roles
    promotions = [f"invenio roles add {admin_email} {role}" for role in GEO_ROLES]

    # return the sequence of steps
    return [
        Step(
            "db",
            "Create the database schema.",
            ("invenio db init", "invenio db create"),
        ),
        Step(
            "files",
            "Register the default file storage location.",
            (f"invenio files location --default 'default-location' {data_path}",),
        ),
        Step(
            "roles",
            "Create the GEO-specific roles.",
            tuple(roles),
        ),
        Step(
            "access",
            "Grant the access policies those roles carry.",
            tuple(grants),
        ),
        Step(
            "users",
            "Create the administrator and give them the GEO roles.",
            tuple(
                [
                    f"invenio users create --active --password={admin_password} {admin_email}",
                    *promotions,
                ]
            ),
        ),
        Step(
            "index",
            "Create the search indices and reset the indexing queue.",
            ("invenio index init", "invenio index queue init purge"),
        ),
        Step(
            "fixtures",
            "Load the controlled vocabularies. This takes several minutes.",
            ("invenio rdm-records fixtures",),
        ),
    ]

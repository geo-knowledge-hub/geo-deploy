#
# This file is part of GEO Knowledge Hub CLI.
# Copyright (C) 2026 GEO Knowledge Hub contributors.
#
# GEO Knowledge Hub CLI is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""GEO Knowledge Hub deploy - Bundle rendering writer."""

from pathlib import Path

#
# Constants - Executable files
#
EXECUTABLE = ("secrets.sh", "bootstrap.sh")


#
# Functions
#
def write(files: dict[str, str], directory: Path) -> list[Path]:
    """Write the rendered bundle to disk.

    Args:
        files (dict[str, str]): The rendered files.

        directory (Path): The directory to write the files to.

    Returns:
        list[Path]: The paths of the written files.
    """
    written = []
    directory.mkdir(parents=True, exist_ok=True)

    for name in sorted(files):
        path = directory / name
        path.write_text(files[name])

        if name in EXECUTABLE:
            path.chmod(0o755)

        written.append(path)

    return written
